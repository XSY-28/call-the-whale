# Call the Whale 🐋

**English** | [简体中文](README.zh-CN.md)

A Codex desktop skill for delegating project work to [DeepSeek Harness (dsh)](https://github.com/deepseek-ai/deepseek-harness). Codex prepares the task, follows execution in its embedded browser, and independently checks the changed files and behavior. When checks fail, it sends specific corrections to dsh.

The whale gets to work. Codex checks the result.

**Call the Whale / 呼叫蓝色大肥鱼** is the project brand, **`call-the-whale`** is the repository, and **`$dsh-dev`** is the invocation. The installed skill directory remains `dsh-dev`.

> **Development defaults to full access; your explicit task permission settings take priority.** dsh may read and write local files, run terminal commands, and access the network. Its effective access depends on dsh settings, the operating-system account, and OS restrictions. It is not confined to the selected project directory. Use it only in an environment you trust and are willing to authorize.

Installing the skill does not grant authorization or change global dsh permissions. Codex explains the effects before first enabling full access and checks your authorization; existing authorization is reused within its scope, while required tool/UI confirmations still apply. Open-only requests and pure chat do not automatically expand permissions. Chat is not a guaranteed sandbox. Every new session checks actual permissions and reasoning settings; reasoning defaults to **High**, unless you request another level. Full access does not expand the task's scope or bypass OS restrictions.

This is a community project, **not an official DeepSeek or OpenAI product**. You pay for dsh model API usage; Codex limits apply separately. Completion and unattended operation are not guaranteed.

[Start here](#start-here) · [Choose a request](#choose-a-request) · [Projects and defaults](#projects-and-defaults) · [Development and verification](#development-and-verification) · [Update and uninstall](#update-and-uninstall) · [Compatibility](#compatibility)

## Start here

### 1. Set up dsh and check your environment

**Before using this skill, run DeepSeek Harness yourself at least once, configure your API key, and successfully send a request and receive a model response.** Follow the [official dsh instructions](https://github.com/deepseek-ai/deepseek-harness).

You also need:

- Codex desktop with actual **embedded-browser display and interaction tools**, plus terminal execution and project-reading access. Loading skills or opening links alone is insufficient.
- The Node.js and npm/npx versions required by your dsh version.
- Python 3.9+ for the standard-library helpers. Git and project-specific build/test tools are needed where the task uses them.

The skill does not obtain keys, add credit, or extract credentials from other apps. Configure authentication in dsh; **never paste keys into Codex, repository files, issues, or screenshots**. A listed model name does not prove its API works. If configuration or authentication fails, finish setup in dsh before delegating work.

### 2. Install the skill

Send this to Codex:

```text
Use $skill-installer to install the skill from
https://github.com/XSY-28/call-the-whale/tree/main/skills/dsh-dev.
Keep the skill directory name dsh-dev.
```

The [official installer](https://github.com/openai/skills/tree/main/skills/.system/skill-installer) usually installs to `$CODEX_HOME/skills/dsh-dev`, or `~/.codex/skills/dsh-dev` when `CODEX_HOME` is unset. Use its reported location, avoid duplicate copies, and try `$dsh-dev` in the next conversation turn. Install the `skills/dsh-dev` subdirectory, not the repository root.

The installation was checked using the official installer's Git method. For a Python download certificate error, fix that runtime's certificate setup or use `--method git`; do not disable HTTPS verification. An existing destination is not overwritten: use [update](#update-and-uninstall) instead.

Use `main` for the current documented behavior. You can replace it with a published tag to pin a version, but **`v0.1.0` predates the newer message, acceptance, and development-mode rules**.

### 3. Open dsh, then give it a scoped task

First check browser access without submitting work:

```text
Use $dsh-dev to open dsh only. Do not submit a development task.
```

After reading the full-access notice above, replace the placeholder path and describe what must pass:

```text
Use $dsh-dev in /absolute/path/to/project to fix duplicate submissions
in the login form. Preserve the existing API. Verify that a double-click
makes only one request and that a failed request can be retried.
I understand and authorize dsh full access for this task.
```

Codex confirms the workspace and scope → dsh implements the fix → Codex inspects the diff and tests the behavior → failures become targeted corrections. The final report identifies changed files, passed/failed/unverified acceptance items, evidence, and any blocker. **This login example illustrates usage; it is not a recorded test result.**

## Choose a request

| Request in Codex | What happens |
|---|---|
| `Use $dsh-dev to open dsh only.` | Find or start a service and show it in the embedded browser. No message or development task is submitted. |
| `Use $dsh-dev to send “你好”.` | Send the exact text once, confirm acceptance, and obtain the complete reply. Non-project chat needs no default project and adds no development work or plugins. |
| `Use $dsh-dev in /absolute/project to fix …` | Confirm the project, prepare a task, delegate, independently check, and correct failures. |
| `Use $dsh-dev to continue the login-form fix.` | Locate the original session, keep its confirmed project and criteria, and check what is actually running or complete before continuing. |

Ordinary development requests and discussions about dsh do not activate delegation. A greeting is not appended to an active development task; an identifiable idle chat is used, or a new session is created. File, code-review, and editing requests still follow project and acceptance rules. Ambiguous sessions or conflicting project paths require clarification.

## Projects and defaults

Specify a project for one task, or explicitly save a default:

```text
Use $dsh-dev to set /absolute/path/to/project as my default project.
Use $dsh-dev to change my default project to /absolute/path/to/another-project.
Use $dsh-dev to clear my default project.
```

A current explicit project takes priority **without changing the default**. A new project task without a path uses your saved default; if none exists, Codex asks before submitting. It does not silently use its current directory, the dsh launch directory, or the last browser workspace. An unavailable directory is reported rather than replaced.

A specified file stays the task's target while Codex confirms its project root from project evidence; its parent directory is not automatically the root. Resuming uses the original session's project, even if your default has changed. Open-only requests and non-project messages need no default. Before project work is submitted, the full workspace path actually selected in dsh must match the target.

| Location | Contents |
|---|---|
| Skill installation | `SKILL.md`, references, and scripts; managed during updates/uninstall |
| Target project | Your project files; existing work is protected and changes follow the task scope |
| Local configuration | `$CODEX_HOME/dsh-dev/config.json`, otherwise `~/.codex/dsh-dev/config.json`; changed only by explicit default-project requests |
| Progress and handoffs | A private record outside the project and skill, resolved from the user directory or `CODEX_HOME`; separate from configuration, atomically replaced with private permissions where supported |

Personal settings and execution records are not published with the skill. Updates and uninstall preserve them. See the [format example](examples/project-config.example.json) and [project-selection rules (Chinese)](skills/dsh-dev/references/projects.md).

## Development and verification

**dsh is the default code writer; Codex is the coordinator and independent verifier.** Codex reads project constraints and existing changes before delegation. It checks actual files, diffs, untracked files, and relevant tests/builds/UI behavior after dsh finishes. If Codex needs to edit the same files, it first confirms that dsh and its writing subtasks have stopped and completes a handoff.

For multi-part tasks, acceptance IDs survive corrections and recovery. A report might look like this:

| Criterion | Status | Evidence |
|---|---|---|
| Double-click sends one request | Passed | Independently observed network requests |
| Retry works after failure | Failed | Reproduction and actual error |
| Required browser coverage | Unverified | Missing environment or check |

This table is illustrative. A failed or unverified key criterion prevents an overall completion claim. dsh's self-report is a lead, not verification. Corrections name the failed item and preserve passing behavior; small tasks need only a few sentences.

Long tasks use a few dependency-aware milestones with outputs, allowed scope, and checks. Progress summaries track confirmed work, next steps, writers, submission state, and remaining budget. Repeated status messages are not progress. Silence or a disconnected page does not prove that background execution stopped; Codex checks before restarting. Stored state and PIDs are not reliable locks.

### Capability selection

- **Services:** inspect terminal output first, then processes, listeners, and tabs as needed. Reuse a confirmed ready service; otherwise use the current version's supported `npx @deepseek-ai/dsh web --no-open`. Open the actual authenticated URL in the embedded browser without guessing ports, duplicating servers, or opening a system browser. A non-project request may use an OS-created private temporary launch directory without saving it as a default.
- **Plugins:** search when there is a concrete benefit. Check actual availability, compatibility, maintenance, permissions, and usage; install only what is needed. Candidate, installed, runtime-ready, and task-tested are different states. No suitable plugin is not itself a blocker.
- **GitHub research:** when useful for a mature feature, unfamiliar integration, or complex design, compare a few relevant projects with real links, compatibility, maintenance, and licenses. Distinguish ideas, dependencies, and copied code; stars are not a quality verdict. Enough evidence should lead to implementation, not endless research or an unsolicited stack change.
- **Execution:** choose a single agent, ordinary subagents, workflow, Agent Teams, and/or independent review according to dependencies, communication, cost, and verified capabilities. Define roles and file ownership; Teams does not automatically isolate files. Do not assume an unavailable mode was enabled.

See [capability selection (Chinese)](skills/dsh-dev/references/capabilities.md) and [submission and acceptance (Chinese)](skills/dsh-dev/references/task-loop.md).

### MVP and agile iteration

Ask for an **MVP (Minimum Viable Product)** to build the smallest runnable core flow. Non-core work can wait; placeholders or fake results cannot replace explicitly required behavior. Code acceptance does not prove market demand.

Ask for **agile delivery** when you want to review each increment: **dsh implements and self-reviews → Codex independently checks → you review**. The next round waits for your feedback; silence or an earlier approval is not approval of the current round. Ordinary tasks and milestones do not add this review gate.

```text
Use $dsh-dev in /absolute/project to build a course-registration MVP.
Core: save registrations and read them after restart. Defer payment and polish.

Use $dsh-dev in /absolute/project for agile delivery. Each round, have dsh
self-review, independently verify it, then show me the increment and wait
for my review before the next round.
```

Every development task also asks for maintainable code: follow the existing structure, centralize changing rules/configuration, and separate actual change boundaries without speculative frameworks. MVP and agile can be combined. They are delegation rules, **not additional dsh CLI modes or plugins**. See [development modes (Chinese)](skills/dsh-dev/references/development-modes.md).

### Token errors and recovery

Recovery follows evidence, not the phrase “out of tokens” alone:

| Evidence-supported condition | Response |
|---|---|
| Context window exhausted | Use verified compaction first; if the session cannot continue, save a concise handoff and create one successor in the original project. |
| Single-response output limit | Check the reply, tool results, and files; continue only the unfinished part from a clear breakpoint. |
| Rate limiting | Respect server wait information and bounded retries, including observed internal retries. Do not submit duplicates. |
| Account quota or credit exhausted | Stop ineffective retries and save progress. The user supplies credit or authorizes a suitable fallback; no purchases, new keys, or other accounts. |
| Insufficient or conflicting evidence | Report uncertainty and collect minimal redacted evidence. |

Handoffs keep goals, constraints, project/branch, changes, decisions, completed/remaining work, verification, errors, and next steps—not full chat logs or credentials. Before resuming, recheck files, diffs, submission state, and background writers. Recovery does not mean completion or relax acceptance criteria.

Your budget takes priority; compression, retries, and multiple agents can add API cost. Unreadable costs are reported as unknown, not claimed to be precisely controlled. Switching sessions does not reset the budget. Without an actual scheduled mechanism, the skill does not promise to continue after the current Codex task ends. See [recovery rules (Chinese)](skills/dsh-dev/references/recovery.md).

## Update and uninstall

Finish active dsh development and skill-maintenance work first. For a new independent source clone, run:

```sh
git clone https://github.com/XSY-28/call-the-whale.git
cd call-the-whale
python3 tools/manage_skill.py update
```

For an existing clone, inspect local changes, run `git pull --ff-only` inside it, then run the same update command. The [maintenance script](tools/manage_skill.py) only manages skill files; it does not access the network, launch dsh, or change configuration or permissions.

Its default target is `$CODEX_HOME/skills/dsh-dev`, otherwise `~/.codex/skills/dsh-dev`. For another installation, pass `--skills-dir '/absolute/path/to/skills'`. It backs up the old skill under `$CODEX_HOME/backups/dsh-dev` (otherwise `~/.codex/backups/dsh-dev`), preserves unknown personal files, and restores the old copy if replacement fails. Edits to known skill files remain in the backup, not automatically merged; inspect them before updating.

From the same source clone, uninstall with:

```sh
python3 tools/manage_skill.py uninstall
```

Both operations report target and backup paths. Check skill availability in the next turn. They preserve default-project settings, handoffs, dsh sessions/profiles, and previously granted permissions. Revoke permissions in dsh itself. To restore, stop related tasks and ask Codex to replace the same installation with the reported backup while preserving personal settings.

## Compatibility

| Area | Evidence and limits |
|---|---|
| macOS browser workflow | Historical isolated development/fix/recovery task, plus a later exact-message chat test. This does not cover every advanced mode. |
| Helpers and package | Isolated configuration, recovery decisions, maintenance, function-fixture tests, and static/link checks. |
| Linux | CI covers helpers and structure, not the full desktop/browser workflow. |
| Windows / other clients | Windows is unverified; POSIX permissions are not guaranteed. CLI-only clients cannot run the full workflow without the required browser tools. |
| MVP, agile, long-task milestones | Rule/scenario review; no complete live dsh MVP or multi-round agile test. |

The previously checked dsh version is **`0.1.5-rc.2`**, not a claim about the latest release. Rediscover capabilities after version/UI changes. Real token exhaustion, workflow/Teams, plugin rollback, provider switching, and all recovery transitions have not received complete end-to-end coverage. See [validation evidence (Chinese)](docs/validation.md), [CI runs](https://github.com/XSY-28/call-the-whale/actions), and [compatibility details (Chinese)](skills/dsh-dev/references/compatibility.md).

The skill and detailed references are currently in Chinese; the English README does not imply a full translation. For developer checks, see [CONTRIBUTING.md (Chinese)](CONTRIBUTING.md).

## When something blocks progress

- **Skill missing:** verify `SKILL.md` is directly inside `dsh-dev`, check the actual installation path, and remove duplicate installations only after inspecting them.
- **Setup/authentication missing:** complete dsh setup yourself and get a successful response. Do not send keys to Codex or an issue.
- **Project or browser unavailable:** Codex should identify the missing directory/tool or conflicting session instead of silently changing the target.
- **Disconnected or rate-limited:** continue the same task and check existing execution first; repeated submissions can duplicate work.
- **Full-access questions:** the checked preset maps to `danger-full-access` and the `never` approval policy; OS/account restrictions still apply. See the [official preset documentation](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/interaction/permission-presets/README.md).

For feedback, include OS and Codex/dsh versions, missing tools, minimal reproduction, expected/actual behavior, redacted error codes, and checks performed. Replace private paths with placeholders; omit keys, authenticated URLs, cookies, full chat logs, private code, and unredacted screenshots. Consult [SECURITY.md (Chinese)](SECURITY.md) for sensitive reports.

Original code, instructions, and documentation use the [MIT License](LICENSE). The project links to official documentation without bundling dsh/Codex source, runtimes, credentials, or models; their own terms still apply. See [NOTICE.md (Chinese)](NOTICE.md).
