# Call the Whale 🐋

**English** | [简体中文](README.zh-CN.md)

**A Codex skill that delegates development to DeepSeek Harness, checks the results, and follows up on fixes.**

Describe the task in Codex. Let the whale get to work.

Call the Whale connects Codex's task planning and independent review with [DeepSeek Harness (dsh)](https://github.com/deepseek-ai/deepseek-harness) running in the Codex desktop app's embedded browser. Codex prepares the task, follows dsh's progress, inspects the actual changes, and requests corrections when the result does not meet the acceptance criteria.

> **Full access is the intended operating mode.** dsh may read and write local files, run terminal commands, and access the network. Its effective access depends on dsh settings, the operating-system account, and OS restrictions—not just the selected project directory. Use it only in an environment you trust and are willing to authorize.
>
> **Set up dsh first.** Before using this skill, run dsh yourself at least once, configure your API key, and successfully send a request and receive a model response.

Installing the skill does **not** change dsh's global permission settings or grant authorization. Before first enabling full access, Codex must explain its effects and check your authorization. Existing authorization is reused within its scope; required tool or UI confirmations still apply. Full access does not authorize work outside your task or bypass OS restrictions.

This is a **community project, not an official DeepSeek or OpenAI product**. You pay for dsh model API usage; Codex usage limits apply separately. Successful completion and unattended operation are not guaranteed.

## What it does

- **Opens or reuses dsh:** finds a ready service, starts one when needed, and opens its actual authenticated URL in Codex's embedded browser.
- **Prepares the work:** turns your request and project constraints into a task with explicit scope and acceptance criteria.
- **Chooses suitable capabilities:** considers plugins, GitHub research, workflows, Agent Teams, and independent reviews when useful and available.
- **Checks the result:** inspects files and diffs, runs relevant checks, and sends specific feedback to dsh for corrections.
- **Handles interruptions:** distinguishes context limits, truncated output, rate limits, and exhausted account credit; preserves progress and avoids duplicate work.

Ordinary development requests are not automatically sent to dsh. Invoke **`$dsh-dev`** or explicitly ask Codex to use dsh. Asking only to open dsh does not submit a development task.

## Requirements

- **Codex desktop with embedded-browser display and interaction tools.** A client that only loads skills or opens links cannot run the full workflow.
- Tools and permissions to read the target project, execute terminal commands, and follow running processes.
- A working dsh configuration, including **one successful model conversation before using this skill**. Follow the [official dsh instructions](https://github.com/deepseek-ai/deepseek-harness).
- The Node.js and npm/npx versions required by your dsh version.
- Python 3.9+ for the standard-library helper scripts. Git and project-specific build/test tools as needed.

The skill does not obtain API keys, add credit, or extract credentials from other apps. **Never paste API keys into Codex messages, repository files, issues, or screenshots.** If configuration or authentication is missing, complete it in dsh before delegating work. Opening the page alone does not send a model test request; a listed model name is not proof that its API works.

## Install

Ask Codex to use its bundled [skill-installer](https://github.com/openai/skills/tree/main/skills/.system/skill-installer):

```text
Use $skill-installer to install the skill from
https://github.com/XSY-28/call-the-whale/tree/main/skills/dsh-dev.
Keep the skill directory name dsh-dev.
```

The usual destination is `$CODEX_HOME/skills/dsh-dev`, or `~/.codex/skills/dsh-dev` when `CODEX_HOME` is unset. Use the location reported by your installer and avoid duplicate installations. Try `$dsh-dev` in the next conversation turn.

To pin a release, replace `main` in the URL with a published tag such as `v0.1.0`. Install **`skills/dsh-dev`**, not the repository root. The installer stops if the destination already exists; use the [update instructions](#update-and-uninstall) for an existing installation.

The public installation check used the official installer's Git method. If your Python runtime has a certificate error during download, fix its certificate setup or use the installer's `--method git` option. Do not disable HTTPS certificate verification.

## Quick start

After completing dsh's first-run setup and getting a successful model response, check browser access:

```text
Use $dsh-dev to open dsh only. Do not submit a development task.
```

Then delegate a scoped task. Replace the path below with your project's absolute path, and authorize full access only after reading the notice above:

```text
Use $dsh-dev in /absolute/path/to/project to fix duplicate submissions
in the login form. Preserve the existing API, add relevant regression
coverage, and run the tests. I understand and authorize dsh full access
for this task.
```

**Illustrative flow, not a recorded demo:** Codex confirms the workspace and prepares the task → dsh works on the fix → Codex checks the diff and behavior → failing acceptance checks become specific follow-up requests → Codex reports the verified outcome or a concrete blocker.

Continue the same task:

```text
Use $dsh-dev to continue the login-form fix, keeping the original
session's project and acceptance criteria.
```

An open-only request does not require a default project or submit work automatically. Continuing a task uses its original session and project; an ambiguous session or a conflicting new project requires clarification.

## Project selection and local settings

```text
Use $dsh-dev to set /absolute/path/to/project as my default project.
Use $dsh-dev to change my default project to /absolute/path/to/another-project.
Use $dsh-dev to clear my default project.
```

An explicitly selected project takes priority for the current task and does not overwrite your default. A new task without a project uses your saved default; if none exists, Codex asks before submitting work. It does not silently choose Codex's current directory, the dsh launch directory, or the workspace last shown in the browser.

If you specify a file, it remains the task's target while Codex determines its project root from project evidence. Unclear ownership or an unavailable directory requires clarification. Before submission, Codex checks the full workspace path actually selected in dsh.

| Location | Purpose |
|---|---|
| Skill installation | `SKILL.md`, references, and scripts; replaced during updates |
| Target project | Your explicitly selected or saved default project; changes remain within the task's scope |
| Local configuration | `$CODEX_HOME/dsh-dev/config.json`, otherwise `~/.codex/dsh-dev/config.json`; changed only when you request setting, changing, or clearing the default |
| Temporary files and handoffs | Temporary directories are created through OS APIs; durable handoffs belong in an authorized private location outside the project, not an automatically cleaned temporary directory |

The [configuration example](examples/project-config.example.json) documents the format. Do not store personal configuration in the skill installation or tracked repository files. Use the requests above or the installed `project_config.py`. Updates and uninstall preserve your configuration and handoffs.

## How Codex and dsh work together

Codex reads the requirements and project constraints, protects existing changes, chooses an execution approach, and prepares the prompt. dsh is the default code writer. Codex independently examines files, diffs, and execution evidence, then performs relevant tests, builds, or UI checks. dsh saying “done” starts the acceptance check; it does not complete it.

- **Services and sessions:** inspect terminal output first, then processes, listeners, and tabs as needed. Reuse only a confirmed ready dsh service. Otherwise start the current version's supported `npx @deepseek-ai/dsh web --no-open` command in the confirmed project. For an open-only request without a project, a private OS-created temporary directory may be used without saving it as the default. Use the actual authenticated URL; do not guess ports or start duplicate servers.
- **Plugins:** search installed capabilities and credible sources when a plugin has a concrete benefit. Check compatibility, maintenance, permissions, and usage. Distinguish a candidate from an installed, working, or task-tested plugin. Missing a suitable plugin should not block otherwise feasible work.
- **GitHub research:** compare a small set of relevant projects when a mature solution, unfamiliar integration, or complex design warrants research. Check real links and evidence, compatibility, maintenance, and licenses. Stop once there is enough evidence to implement. Stars alone do not establish quality or justify changing the stack.
- **Execution modes:** select a single agent, ordinary subagents, workflow, or Agent Teams based on the task. Consider independent multi-agent review separately. Verify available capabilities and define roles, file ownership, concurrency, and aggregation before delegation.
- **Permissions and reasoning:** check full access for each new session. Reasoning defaults to High unless you request otherwise; report unsupported settings without silently switching models. Installation and updates do not modify global dsh settings.
- **Shared files:** while dsh writes, Codex defaults to read-only inspection. Direct edits to the same files require a confirmed stop and handoff. Multiple agents need explicit file ownership or separate worktrees where appropriate.

## Token errors, budgets, and recovery

“Out of tokens” can mean different things. Recovery follows the available evidence:

| Condition | Response |
|---|---|
| Context window exhausted | Use a verified compaction capability first. If the original session cannot continue, save a concise handoff and create one successor session in the original project. |
| Output limit reached | Inspect the response, tool results, and files; continue only the unfinished part from a clear stopping point. |
| Rate limiting | Respect server retry information and the task budget. Do not stack new submissions on top of internal retries; stop when over budget or making no progress. |
| Account quota or credit exhausted | Stop ineffective retries and preserve progress. The user supplies credit or chooses an authorized fallback; do not purchase credit or switch keys/accounts. |
| Insufficient or conflicting evidence | Report the uncertainty and collect minimal redacted evidence instead of guessing. |

Handoffs record the goal, constraints, project/branch, existing changes, completed and remaining work, decisions, verification, errors, and next steps. They exclude full chat logs and credentials. Before resuming, recheck files, diffs, submission state, and background tasks to prevent duplicate execution and concurrent writes. Recovery does not relax the original acceptance criteria.

Your budget takes priority. Retries, compaction, and multiple agents can add API cost. Without an actual scheduled execution mechanism, the skill does not promise to continue automatically after the current Codex task ends. See the [recovery reference (Chinese)](skills/dsh-dev/references/recovery.md).

## Update and uninstall

The official skill-installer does not overwrite an existing destination. This repository includes a [local maintenance script](tools/manage_skill.py) that only manages skill files: it does not access the network, launch dsh, or change personal configuration or permissions.

Finish active dsh development and skill-maintenance tasks first, then get the source:

```sh
git clone https://github.com/XSY-28/call-the-whale.git
cd call-the-whale
# For an existing independent clone, run git pull --ff-only inside it.
python3 tools/manage_skill.py update
```

The default target is `$CODEX_HOME/skills/dsh-dev`, otherwise `~/.codex/skills/dsh-dev`. If your skill lives elsewhere, pass `--skills-dir '/absolute/path/to/skills'`. Update the copy Codex actually uses.

Before updating, the script backs up the entire old skill in a unique subdirectory under `$CODEX_HOME/backups/dsh-dev`, otherwise `~/.codex/backups/dsh-dev`. Local skill-code changes are preserved in the backup but are not automatically merged into the new version. A failed update restores the old copy.

To uninstall by moving the skill out of the search directory while keeping a backup:

```sh
python3 tools/manage_skill.py uninstall
```

Both operations report the actual target and backup paths. Check availability in the next conversation turn. They do not delete default-project settings, handoffs, dsh sessions, profiles, or previously granted permissions. Revoke dsh permissions in dsh itself if desired. To restore an older version, stop related tasks and ask Codex to replace the same installation directory with the reported backup, preserving personal configuration.

## Compatibility and verification

| Area | Evidence and limits |
|---|---|
| Full browser workflow | Historically tested with an isolated small task on **macOS**; this does not establish coverage of every advanced mode. |
| Public package | Helper scripts, installation/maintenance, and simulated decisions checked. |
| Linux | CI checks scripts and package structure, not the full desktop/browser workflow. |
| Windows | Unverified. Helpers relying on POSIX permissions are not guaranteed to work. |
| CLI-only or other skill clients | Cannot directly run the complete workflow without the required desktop browser tools. |

The previously checked dsh version is **`0.1.5-rc.2`**. Rediscover capabilities when versions or UI change. Workflow/Teams, plugin-install rollback, real token failures, and multi-provider switching have not all received end-to-end testing. See the [validation record (Chinese)](docs/validation.md) and [compatibility reference (Chinese)](skills/dsh-dev/references/compatibility.md).

The skill instructions and detailed supporting references currently remain in Chinese. This update adds an English entry point; it does not claim that every document or interface has been translated.

Developer checks:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 tools/check_package.py
node tests/acceptance.mjs tests/e2e-fixture
node --test tests/e2e-fixture/clamp.test.mjs
```

Git must work. If Git on `PATH` cannot run, set `DSH_DEV_TEST_GIT` to a verified Git executable. Tests use temporary configuration and projects, not real keys or default-project settings. See [CONTRIBUTING.md (Chinese)](CONTRIBUTING.md).

## FAQ

**Why do I invoke `$dsh-dev` rather than the repository name?**

Call the Whale (呼叫蓝色大肥鱼) is the project brand; `call-the-whale` is the repository. The installed directory and technical skill identifier remain **`dsh-dev`**. Its current Codex display name is Chinese. Check that `SKILL.md` is directly inside that directory and that you do not have duplicate installations.

**Can the skill configure my API key for me?**

No. First use dsh yourself and get a successful model response. Handle authentication in dsh, and never send keys through Codex messages or issues.

**Does full access mean a project-only sandbox?**

No. In the checked dsh version, Full access maps to `danger-full-access` with the `never` approval policy. Your OS and account still constrain actual access. Enabling it requires authorization. See the [official permission-preset documentation](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/interaction/permission-presets/README.md).

**Why might Codex ask before starting?**

It may lack a project directory, browser tools, first-run configuration, permission authorization, or a consequential requirement. It should identify the actual missing information. Routine development requests do not automatically activate dsh delegation.

**What if the page disconnects or a request is rate-limited?**

Continue the same task and let Codex check the old session and background work first. Do not repeatedly submit or open new sessions; a disconnected page does not prove that execution stopped.

**How do I report a problem?**

Include your OS, Codex/dsh versions, missing tool names, minimal reproduction, expected/actual behavior, redacted error codes, and test results. Replace private paths with placeholders. Do not attach keys, authenticated URLs, cookies, full chat logs, private code, or unredacted screenshots. For sensitive reports, consult [SECURITY.md (Chinese)](SECURITY.md) first.

## License and sources

Original code, skill instructions, and documentation are available under the [MIT License](LICENSE). The project references official dsh and Codex documentation by link; it does not bundle their source, runtimes, credentials, or models. Those products retain their own licenses and terms. See [NOTICE.md (Chinese)](NOTICE.md).
