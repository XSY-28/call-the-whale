"""Simulated provider errors plus a real isolated project, never a live model."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(os.environ.get("DSH_DEV_RECOVERY_SCRIPT") or (
    Path(__file__).resolve().parents[1] / "skills/dsh-dev/scripts/recovery_check.py"))
spec = importlib.util.spec_from_file_location("recovery_check", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def observation(code="CONTEXT_WINDOW_EXCEEDED"):
    return {
        "error": {"code": code},
        "budget": {"remaining_seconds": 600, "calls_allowed": True, "retries_used": 0,
                   "retry_limit": 2, "no_progress_errors": 0},
        "state": {"run": "idle", "writers": "quiescent", "submission": "accepted",
                  "files_checked": True, "diff_checked": True, "jobs_checked": True},
        "recovery": {"compaction": "available"},
    }


class ClassificationTests(unittest.TestCase):
    def test_normalized_classes(self):
        for code, category in [("CONTEXT_WINDOW_EXCEEDED", "context"), ("QUOTA", "quota"), ("RATE_LIMIT", "rate")]:
            with self.subTest(code=code):
                self.assertEqual(module.classify({"code": code})[0], category)

    def test_output_markers_are_not_context_errors(self):
        for finish in ("length", "max-tokens"):
            self.assertEqual(module.classify({"finish_reason": finish})[0], "output")

    def test_token_word_and_abrupt_ending_are_unknown(self):
        for error in ({"message": "token 用完了"}, {"message": "implementing..."}, {"finish_reason": "stop"}):
            self.assertEqual(module.classify(error)[0], "unknown")

    def test_http_429_is_not_enough_and_quota_code_wins(self):
        self.assertEqual(module.classify({"http_status": 429})[0], "unknown")
        self.assertEqual(module.classify({"provider": "deepseek", "http_status": 429})[0], "unknown")
        self.assertEqual(module.classify({"code": "QUOTA", "http_status": 429})[0], "quota")
        self.assertEqual(module.classify({"provider": "deepseek", "http_status": 429,
                                           "rate_limit_confirmed": True})[0], "rate")

    def test_balance_mapping_requires_verified_provider(self):
        self.assertEqual(module.classify({"provider": "deepseek", "http_status": 402})[0], "quota")
        self.assertEqual(module.classify({"provider": "some-proxy", "http_status": 402})[0], "unknown")

    def test_conflicting_evidence_stays_unknown(self):
        result = module.classify({"provider": "deepseek", "http_status": 402, "code": "RATE_LIMIT"})
        self.assertEqual(result, ("unknown", "conflicting_evidence"))

    def test_auth_transport_server_are_separate(self):
        for code in ("AUTH", "TRANSPORT", "SERVER", "INVALID_REQUEST"):
            self.assertEqual(module.classify({"code": code})[0], "other")

    def test_partial_finish_does_not_hide_http_error_or_unknown_code(self):
        for error in ({"http_status": 503, "finish_reason": "length"},
                      {"code": "FUTURE_FAILURE", "finish_reason": "length"}):
            self.assertEqual(module.classify(error)[0], "unknown")


class RecoveryTests(unittest.TestCase):
    def action(self, data):
        result = module.assess(data)
        self.assertFalse(result["executes_actions"])
        self.assertFalse(result["task_complete"])
        return result["action"]

    def test_quota_stops_even_internal_retry(self):
        data = observation("QUOTA")
        data["state"].update(run="retrying", writers="active")
        self.assertEqual(self.action(data), "stop_retry_and_record")

    def test_unknown_does_not_retry_or_compact(self):
        data = observation()
        data["error"] = {"message": "token 用完"}
        self.assertEqual(self.action(data), "inspect_evidence")

    def test_budget_or_authorization_missing_blocks_new_calls(self):
        for update in ({"remaining_seconds": 0}, {"calls_allowed": False}):
            data = observation()
            data["budget"].update(update)
            self.assertIn(self.action(data), ("stop_and_record", "stop_retry_and_record"))

    def test_retry_counts_must_be_observed(self):
        data = observation("RATE_LIMIT")
        del data["budget"]["retries_used"]
        self.assertEqual(self.action(data), "inspect_evidence")

    def test_internal_recovery_prevents_extra_submit(self):
        for run in ("running", "retrying", "compacting"):
            data = observation("RATE_LIMIT")
            data["state"]["run"] = run
            self.assertEqual(self.action(data), "observe_existing")

    def test_unknown_workers_and_submission_require_reconciliation(self):
        data = observation()
        data["state"]["writers"] = "unknown"
        self.assertEqual(self.action(data), "inspect_running_tasks")
        data["state"].update(writers="quiescent", submission="unknown")
        self.assertEqual(self.action(data), "reconcile_submission")

    def test_files_diff_jobs_must_all_be_rechecked(self):
        for field in ("files_checked", "diff_checked", "jobs_checked"):
            data = observation()
            data["state"][field] = False
            self.assertEqual(self.action(data), "inspect_actual_state")

    def test_compaction_availability_and_success_are_distinct(self):
        for status, expected in (("unknown", "verify_compaction_capability"),
                                 ("available", "compact_current_once"),
                                 ("succeeded", "continue_original_after_check")):
            data = observation()
            data["recovery"]["compaction"] = status
            self.assertEqual(self.action(data), expected)

    def test_failure_does_not_automatically_create_successor(self):
        data = observation()
        data["recovery"]["compaction"] = "failed"
        self.assertEqual(self.action(data), "inspect_current_session")
        data["recovery"]["old_session_unusable"] = True
        self.assertEqual(self.action(data), "save_handoff")

    def test_output_continues_only_at_verified_breakpoint(self):
        data = observation()
        data["error"] = {"finish_reason": "max-tokens"}
        self.assertEqual(self.action(data), "inspect_partial_output")
        data["recovery"]["breakpoint_verified"] = True
        self.assertEqual(self.action(data), "continue_remaining_only")

    def test_server_wait_not_truncated_to_chunk_limit(self):
        data = observation("RATE_LIMIT")
        data["rate"] = {"retry_after": "180", "received_at": 1000, "now": 1030}
        result = module.assess(data)
        self.assertEqual((result["delay_seconds"], result["wait_chunk_seconds"]), (150, 60))
        data["budget"]["remaining_seconds"] = 100
        self.assertEqual(self.action(data), "stop_retry_and_record")

    def test_http_date_and_elapsed_wait(self):
        data = observation("RATE_LIMIT")
        data["rate"] = {"retry_after": "Thu, 01 Jan 1970 00:20:00 GMT", "now": 1100}
        self.assertEqual(module.assess(data)["delay_seconds"], 100)
        data["rate"]["now"] = 1201
        self.assertEqual(self.action(data), "recheck_then_retry_failed_step_once")

    def test_internal_retry_cannot_hide_server_wait_exceeding_budget(self):
        data = observation("RATE_LIMIT")
        data["rate"] = {"retry_after": "180", "received_at": 1000, "now": 1000}
        data["budget"]["remaining_seconds"] = 100
        data["state"]["run"] = "retrying"
        self.assertEqual(self.action(data), "stop_retry_and_record")

    def test_numeric_wait_requires_valid_original_receipt_time(self):
        for rate in ({"retry_after": "10", "now": 20},
                     {"retry_after": "10", "received_at": 25, "now": 20}):
            data = observation("RATE_LIMIT")
            data["rate"] = rate
            self.assertEqual(self.action(data), "inspect_evidence")

    def test_invalid_header_uses_bounded_backoff(self):
        data = observation("RATE_LIMIT")
        data["rate"] = {"retry_after": "unparseable", "now": 100}
        self.assertEqual(module.assess(data)["delay_seconds"], 5)
        data["budget"]["retries_used"] = 1
        self.assertEqual(module.assess(data)["delay_seconds"], 10)

    def test_combined_retries_stop_at_budget_and_no_progress_bound(self):
        data = observation("RATE_LIMIT")
        data["budget"]["retries_used"] = 2
        data["state"]["run"] = "retrying"
        self.assertEqual(self.action(data), "stop_retry_and_record")
        data = observation()
        data["budget"]["no_progress_errors"] = 2
        self.assertEqual(self.action(data), "stop_retry_and_record")

    def test_cli_invalid_input_never_echoes_secret(self):
        for value in ('{"message":"SECRET_API_KEY",', '[]', '{"error":{"code":[]}}', 'x' * (module.LIMIT + 1)):
            run = subprocess.run([sys.executable, str(SCRIPT)], input=value, text=True, capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertNotIn("SECRET_API_KEY", run.stdout + run.stderr)
            self.assertEqual(json.loads(run.stdout)["action"], "inspect_evidence")


class IsolatedHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dsh-recovery-isolated-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / "project"
        self.project.mkdir()
        self.git = os.environ.get("DSH_DEV_TEST_GIT") or shutil.which("git")
        if not self.git:
            self.skipTest("Git unavailable for isolated repository test")
        self.g("init", "-b", "fixture")
        (self.project / "module.py").write_text("def add(a, b):\n    return a + b\n")
        self.g("add", "module.py")
        self.g("-c", "user.name=isolated-test", "-c", "user.email=isolated@example.invalid", "commit", "-m", "fixture")
        self.head = self.g("rev-parse", "HEAD").strip()
        (self.project / "user-note.txt").write_text("preserve user work\n")
        self.data = observation()
        self.data["state"].update(target_project=str(self.project), branch="fixture", head=self.head)
        self.data["recovery"].update(compaction="unavailable", old_session_unusable=True,
                                     handoff_saved=True, handoff_reviewed=True)
        self.data["handoff"] = dict(goal="add and multiply", constraints=["preserve user-note.txt"],
            project=str(self.project), branch="fixture", head=self.head, changes=[], done=["add"],
            remaining=["multiply"], decisions=["keep Python, no dependencies"], validation=["add(2,3)=5"],
            error="CONTEXT_WINDOW_EXCEEDED", next_step="verify files then implement only multiply",
            acceptance=["add(2,3)=5", "multiply(2,3)=6", "preserve original work"],
            old_session="simulated-old", uncertainties=["old conversation summary unavailable"])

    def g(self, *args):
        return subprocess.check_output([self.git, *args], cwd=self.project, text=True, stderr=subprocess.DEVNULL)

    def check(self, data=None):
        run = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps(data or self.data),
                             text=True, capture_output=True, cwd=self.root)
        self.assertEqual(run.returncode, 0, run.stderr)
        return json.loads(run.stdout)

    def test_incomplete_or_unreviewed_handoff_cannot_migrate(self):
        del self.data["handoff"]["acceptance"]
        self.assertEqual(self.check()["action"], "save_handoff")
        self.data["handoff"]["acceptance"] = ["keep original acceptance"]
        self.data["recovery"]["handoff_reviewed"] = False
        self.assertEqual(self.check()["action"], "review_handoff")

    def test_project_and_baseline_conflicts_block_migration(self):
        other = self.root / "other-default-project"
        other.mkdir()
        self.data["state"]["target_project"] = str(other)
        self.assertEqual(self.check()["action"], "clarify_project")
        self.data["state"].update(target_project=str(self.project), branch="other-branch")
        self.assertEqual(self.check()["action"], "reconcile_baseline")

    def test_existing_successor_is_reused_even_after_interrupt(self):
        self.data["handoff"]["successor_session"] = "simulated-new"
        self.assertEqual(self.check()["action"], "restore_successor")
        self.data["state"]["submission"] = "unknown"
        self.assertEqual(self.check()["action"], "reconcile_submission")

    def test_real_files_and_live_worker_handoff_then_independent_acceptance(self):
        # A local stand-in for a background dsh writer; it waits for an explicit
        # release. No provider call, browser, credential or production project.
        worker = subprocess.Popen([sys.executable, "-c",
            "import sys; from pathlib import Path; sys.stdin.readline(); "
            "p=Path('module.py'); p.write_text(p.read_text()+'\\n# completed old step\\n')"],
            cwd=self.project, stdin=subprocess.PIPE, text=True)
        try:
            self.assertIsNone(worker.poll())
            self.data["state"].update(run="idle", writers="active")
            self.assertEqual(self.check()["action"], "observe_existing")
            worker.communicate("finish\n", timeout=10)
            self.assertEqual(worker.returncode, 0)
        finally:
            if worker.poll() is None:
                worker.kill()
                worker.wait()
        self.data["state"].update(writers="quiescent", files_checked=False, diff_checked=False)
        self.assertEqual(self.check()["action"], "inspect_actual_state")
        before = (self.project / "module.py").read_text()
        self.assertIn("completed old step", before)
        self.assertIn("completed old step", self.g("diff"))
        self.assertIn("user-note.txt", self.g("status", "--porcelain"))
        self.data["handoff"]["changes"] = ["module.py: old step marker", "untracked user-note.txt preserved"]
        private = self.root / "handoff.json"
        with open(private, "w", opener=lambda path, flags: os.open(path, flags, 0o600)) as stream:
            json.dump(self.data["handoff"], stream)
        self.assertEqual(private.stat().st_mode & 0o777, 0o600)
        self.data["handoff"] = json.loads(private.read_text())
        self.data["state"].update(files_checked=True, diff_checked=True, jobs_checked=True)
        self.assertEqual(self.check()["action"], "create_successor_same_project")
        self.data["handoff"]["successor_session"] = "simulated-new"
        self.assertEqual(self.check()["action"], "restore_successor")
        # Recovery is possible but the original acceptance is still not met.
        ns = {}
        exec(compile(before, "module.py", "exec"), ns)
        self.assertNotIn("multiply", ns)
        self.assertFalse(self.check()["task_complete"])
        # Simulate only the successor's remaining, explicitly owned file edit.
        (self.project / "module.py").write_text(before + "\ndef multiply(a, b):\n    return a * b\n")
        subprocess.run([sys.executable, "-c", "from module import add,multiply; assert add(2,3)==5; assert multiply(2,3)==6"],
                       cwd=self.project, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), check=True)
        text = (self.project / "module.py").read_text()
        self.assertEqual(text.count("def add"), 1)
        self.assertEqual(text.count("def multiply"), 1)
        self.assertEqual(text.count("completed old step"), 1)
        self.assertEqual((self.project / "user-note.txt").read_text(), "preserve user work\n")
        self.assertEqual(self.g("rev-parse", "HEAD").strip(), self.head)


if __name__ == "__main__":
    unittest.main()
