#!/usr/bin/env python3
"""Read a sanitized observation from stdin and suggest one recovery action.

Read-only: no provider calls, retries, session creation, file edits, or credential
inspection. Observations must come from the current failed request and live state.
See references/recovery.md for the input contract and required human checks.
"""

import json
import math
from pathlib import Path
import sys
import time
from email.utils import parsedate_to_datetime


LIMIT = 32768
CODES = {"CONTEXT_WINDOW_EXCEEDED": "context", "QUOTA": "quota", "RATE_LIMIT": "rate"}
OTHER_CODES = {"AUTH", "INVALID_CREDENTIAL", "MISSING_CREDENTIAL", "SERVER", "TIMEOUT",
               "TRANSPORT", "INVALID_REQUEST", "EMPTY_RESPONSE", "ABORTED"}
HANDOFF_FIELDS = ("goal", "constraints", "project", "branch", "head", "changes", "done",
                  "remaining", "decisions", "validation", "error", "next_step",
                  "acceptance", "old_session", "uncertainties")


def classify(error):
    """Use verified machine evidence; never infer from the word 'token'."""
    code = error.get("code")
    category = CODES.get(code)
    deepseek_balance = error.get("provider") == "deepseek" and error.get("http_status") == 402
    if deepseek_balance and category not in (None, "quota"):
        return "unknown", "conflicting_evidence"
    if category:
        return category, "dsh_error_code"
    if code in OTHER_CODES:
        return "other", "non_token_failure"
    if deepseek_balance and code in (None, "", "HTTP_402"):
        return "quota", "deepseek_http_402"
    # Unknown codes can carry a meaning different from a partial finish marker.
    if code:
        return "unknown", "unrecognized_code"
    if error.get("provider") == "deepseek" and error.get("http_status") == 429:
        # A body may identify exhausted quota even when HTTP status is 429.
        if error.get("rate_limit_confirmed") is True:
            return "rate", "verified_provider_rate_limit"
        return "unknown", "rate_or_quota_unresolved"
    if error.get("http_status", 200) >= 400:
        return "unknown", "provider_error_requires_details"
    if error.get("finish_reason") in ("length", "max-tokens"):
        return "output", "response_finish_reason"
    return "unknown", "insufficient_evidence"


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("expected finite nonnegative number")
    return value


def retry_delay(rate, retries):
    """Keep the original receipt time; never shorten a server wait to 60 seconds."""
    now = number(rate.get("now", time.time()))
    received = rate.get("received_at")
    header = rate.get("retry_after")
    if header is not None:
        try:
            if isinstance(header, bool):
                raise ValueError()
            seconds = float(header)
            if not math.isfinite(seconds) or seconds < 0:
                raise ValueError()
            if received is None:
                return None, "receipt_time_required"
            try:
                received = number(received)
            except ValueError:
                return None, "receipt_time_invalid"
            if received > now:
                return None, "receipt_time_invalid"
            return max(0, received + seconds - now), "server_seconds"
        except (ValueError, TypeError):
            try:
                date = parsedate_to_datetime(str(header))
                if date.tzinfo is None:
                    raise ValueError()
                return max(0, date.timestamp() - now), "server_date"
            except (ValueError, TypeError, OverflowError):
                pass
    return min(60, 5 * 2 ** min(retries, 8)), "local_backoff"


def assess(observation):
    category, evidence = classify(observation.get("error", {}))
    result = dict(category=category, evidence=evidence, executes_actions=False, task_complete=False)

    def action(name, reason, **extra):
        return dict(result, action=name, reason=reason, **extra)

    if category == "quota":
        return action("stop_retry_and_record", "quota_requires_user_action")
    if category in ("unknown", "other"):
        return action("inspect_evidence", evidence)
    budget = observation.get("budget", {})
    if "remaining_seconds" not in budget or budget.get("calls_allowed") is not True:
        return action("stop_and_record", "budget_or_call_authorization_unconfirmed")
    remaining = number(budget["remaining_seconds"])
    if remaining <= 0:
        return action("stop_retry_and_record", "budget_exhausted")
    if "retries_used" not in budget or "no_progress_errors" not in budget:
        return action("inspect_evidence", "retry_history_unconfirmed")
    retries = number(budget.get("retries_used", 0))
    retry_limit = number(budget.get("retry_limit", 2))
    no_progress = number(budget.get("no_progress_errors", 0))
    if type(retries) is not int or type(retry_limit) is not int:
        raise ValueError("retry counts must be integers")
    if no_progress >= 2 or (category == "rate" and retries >= retry_limit):
        return action("stop_retry_and_record", "retry_or_no_progress_limit")
    if category == "rate":
        delay, basis = retry_delay(observation.get("rate", {}), retries)
        if delay is None:
            return action("inspect_evidence", basis)
        # Internal retrying must not hide a known wait exceeding the task budget.
        if delay >= remaining:
            return action("stop_retry_and_record", "wait_exceeds_budget")
    state = observation.get("state", {})
    if state.get("run") in ("running", "retrying", "compacting") or state.get("writers") == "active":
        return action("observe_existing", "existing_work_or_recovery_in_progress")
    if state.get("run") not in ("idle", "stopped") or state.get("writers") != "quiescent":
        return action("inspect_running_tasks", "quiescence_unconfirmed")
    if state.get("submission") not in ("accepted", "not_accepted", "completed"):
        return action("reconcile_submission", "acceptance_unknown_do_not_resend")
    if not all(state.get(key) is True for key in ("files_checked", "diff_checked", "jobs_checked")):
        return action("inspect_actual_state", "files_diff_and_jobs_required")
    recovery = observation.get("recovery", {})
    if category == "rate":
        return action("wait_then_recheck" if delay > 0 else "recheck_then_retry_failed_step_once",
                      basis, delay_seconds=math.ceil(delay), wait_chunk_seconds=min(60, math.ceil(delay)))
    if category == "output":
        if recovery.get("breakpoint_verified") is not True:
            return action("inspect_partial_output", "verify_files_and_exact_breakpoint")
        return action("continue_remaining_only", "do_not_replay_whole_task")
    compact = recovery.get("compaction", "unknown")
    if compact == "unknown":
        return action("verify_compaction_capability", "package_presence_is_not_runtime_evidence")
    if compact == "available":
        return action("compact_current_once", "verified_idle_command_only")
    if compact == "succeeded" and recovery.get("old_session_unusable") is not True:
        return action("continue_original_after_check", "compaction_is_not_task_completion")
    if recovery.get("old_session_unusable") is not True:
        return action("inspect_current_session", "migration_not_yet_justified")
    if compact not in ("succeeded", "failed", "no_history", "unavailable"):
        return action("inspect_current_session", "compaction_outcome_unknown")
    handoff = observation.get("handoff", {})
    if not all(key in handoff for key in HANDOFF_FIELDS) or recovery.get("handoff_saved") is not True:
        return action("save_handoff", "concise_sanitized_handoff_required")
    if (not all(isinstance(handoff[key], str) and handoff[key].strip()
                for key in ("goal", "project", "branch", "head", "old_session", "next_step"))
            or not handoff["acceptance"]):
        return action("save_handoff", "handoff_incomplete")
    if recovery.get("handoff_reviewed") is not True:
        return action("review_handoff", "check_omissions_secrets_and_uncertainties")
    project = Path(handoff["project"]).expanduser()
    target = Path(state.get("target_project", "")).expanduser()
    if not project.is_absolute() or not target.is_absolute():
        return action("clarify_project", "absolute_confirmed_project_required")
    if not project.is_dir() or not target.is_dir() or project.resolve() != target.resolve():
        return action("clarify_project", "same_original_project_required")
    if state.get("branch") != handoff["branch"] or state.get("head") != handoff["head"]:
        return action("reconcile_baseline", "branch_or_head_changed_do_not_checkout_automatically")
    if handoff.get("successor_session"):
        return action("restore_successor", "existing_successor_do_not_create_again")
    return action("create_successor_same_project", "recheck_workspace_permissions_reasoning_before_submit")


def main():
    try:
        raw = sys.stdin.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError("input too large")
        result = assess(json.loads(raw))
    except (ValueError, TypeError, KeyError, AttributeError, OSError, RuntimeError):
        # No original input, error body, credential, or traceback is echoed.
        result = dict(category="unknown", action="inspect_evidence", reason="invalid_observation",
                      executes_actions=False, task_complete=False)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
