#!/usr/bin/env python3
"""Local dsh-dev project preferences and read-only task directory resolution.

No dsh API, browser interaction, cwd fallback, or automatic root discovery.
Only explicit `set/clear --user-requested` mutate the dedicated config file.
"""

import argparse
import json
import os
from pathlib import Path
import stat
import tempfile


SKILL_ROOT = Path(__file__).resolve().parents[1]
CONFIG_LIMIT = 16384


class SelectionError(Exception):
    def __init__(self, reason, detail):
        self.reason = reason
        self.detail = detail
        super().__init__(detail)


def absolute_path(value):
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise SelectionError("absolute_path_required", "请先按用户提供的上下文确认绝对路径；不使用当前目录补齐。")
    return path


def checked_path(value, *, file=False):
    path = absolute_path(value)
    try:
        path = path.resolve(strict=True)
        if file:
            if not path.is_file():
                raise SelectionError("not_a_file", "任务对象不是普通文件。")
            if not os.access(path, os.R_OK):
                raise PermissionError()
            with path.open("rb"):
                pass
        else:
            if not path.is_dir():
                raise SelectionError("not_a_directory", "项目路径不是目录。")
            if not os.access(path, os.R_OK | os.X_OK):
                raise PermissionError()
            with os.scandir(path):
                pass
    except FileNotFoundError as exc:
        raise SelectionError("path_missing", "路径不存在；请用户确认或提供可用路径，不自动创建或切换。") from exc
    except PermissionError as exc:
        raise SelectionError("path_inaccessible", "路径不可读取或进入；请说明访问限制并询问用户。") from exc
    except (OSError, RuntimeError) as exc:
        raise SelectionError("path_unavailable", "路径无法解析或访问；不自动切换目录。") from exc
    return path


def config_path(override=None):
    if override is not None:
        path = absolute_path(override)
    else:
        codex_home = os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
        path = absolute_path(codex_home) / "dsh-dev" / "config.json"
    if path.is_symlink():
        raise SelectionError("config_symlink", "配置文件是符号链接；不读取或修改链接目标。")
    path = path.resolve()
    if path.is_relative_to(SKILL_ROOT):
        raise SelectionError("config_inside_skill", "本机配置必须保存在可分享的 skill 目录之外。")
    return path


def read_default(path):
    try:
        if path.is_symlink():
            raise SelectionError("config_symlink", "配置文件是符号链接；不读取链接目标。")
        try:
            info = path.stat()
        except FileNotFoundError:
            return None
        if not stat.S_ISREG(info.st_mode) or info.st_size > CONFIG_LIMIT:
            raise SelectionError("config_invalid", "配置不是受支持的小型普通 JSON 文件。")
        data = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or set(data) != {"schema", "default_project"}
                or type(data["schema"]) is not int or data["schema"] != 1
                or not isinstance(data["default_project"], str)
                or not data["default_project"].strip()
                or not Path(data["default_project"]).is_absolute()):
            raise SelectionError("config_invalid", "配置格式或版本不受支持；不忽略、重置或输出原始内容。")
        return data["default_project"]
    except (OSError, ValueError, UnicodeError) as exc:
        raise SelectionError("config_unreadable", "无法读取默认项目配置；不忽略或输出原始内容。") from exc


def set_default(path, project):
    project = checked_path(project)
    read_default(path)  # Refuse to silently replace malformed or future config.
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temp_path = None
    try:
        fd, name = tempfile.mkstemp(prefix=".config-", suffix=".tmp", dir=path.parent)
        temp_path = Path(name)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump({"schema": 1, "default_project": str(project)}, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    return {"status": "saved", "config": str(path), "default_project": str(project)}


def clear_default(path):
    # Explicit clear can remove a corrupt dedicated config, but never its symlink target.
    if path.is_symlink():
        raise SelectionError("config_symlink", "配置文件是符号链接；不修改链接目标。")
    existed = path.exists()
    path.unlink(missing_ok=True)
    return {"status": "cleared", "config": str(path), "existed": existed}


def resolve_project(args):
    result = {"mode": args.mode, "may_open": True, "can_submit": False}
    source = "explicit" if args.project else "file_confirmed" if args.file else None
    result["source"] = source
    try:
        if args.file_project and not args.file:
            raise SelectionError("file_required", "只有明确的文件任务才可传入已确认所属项目。")
        if args.session_project and args.mode != "resume":
            raise SelectionError("resume_required", "会话目录只适用于继续已有任务。")
        # Open-only must not depend on any default, even a damaged one.
        if args.mode == "open" and not args.project and not args.file:
            return dict(result, status="open_only", reason="project_not_required")
        task_file = checked_path(args.file, file=True) if args.file else None
        if task_file:
            result["task_file"] = str(task_file)
        explicit = args.project or args.file_project
        if task_file and not explicit:
            raise SelectionError("file_project_required", "先依据项目资料确认文件所属项目；不明确时询问，不使用文件父目录或默认项目猜测。")
        if explicit:
            result["candidate_project"] = explicit
        project = checked_path(explicit) if explicit else None
        if task_file and not task_file.is_relative_to(project):
            raise SelectionError("file_outside_project", "文件不在确认的项目目录中；请澄清归属。")
        if args.mode == "resume":
            if not args.session_project:
                raise SelectionError("session_project_required", "先核实原会话的项目目录；仍不明确时询问，不使用默认项目。")
            result["session_project"] = args.session_project
            if project is None:
                result.update(source="session", candidate_project=args.session_project)
            session = checked_path(args.session_project)
            result["session_project"] = str(session)
            if project and project != session:
                raise SelectionError("session_project_conflict", "当前指定目录与原会话冲突；先澄清，不直接切换或继续执行。")
            project, source = session, "session"
        elif project is None:
            source = "default"
            result["source"] = source
            path = config_path(args.config)
            result["config"] = str(path)
            default = read_default(path)
            if default is None:
                raise SelectionError("default_missing", "请询问本次开发的项目目录，得到答复后再提交；答复不自动保存为默认。")
            result["candidate_project"] = default
            project = checked_path(default)
        result.update(project=str(project), source=source)
        if not args.web_workspace:
            return dict(result, status="needs_workspace_check", reason="web_workspace_unconfirmed")
        web = checked_path(args.web_workspace)
        result["web_workspace"] = str(web)
        if web != project:
            return dict(result, status="needs_workspace_check", reason="web_workspace_mismatch")
        return dict(result, status="ready", can_submit=args.mode != "open")
    except SelectionError as exc:
        return dict(result, status="needs_input", reason=exc.reason, detail=exc.detail)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="独立配置绝对路径；测试必须指向临时目录。")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("show", help="只读默认项目，不创建配置。")
    setter = commands.add_parser("set", help="仅当用户明确设置/修改默认项目时调用。")
    setter.add_argument("--project", required=True)
    setter.add_argument("--user-requested", action="store_true", required=True)
    clearer = commands.add_parser("clear", help="仅当用户明确清除默认项目时调用。")
    clearer.add_argument("--user-requested", action="store_true", required=True)
    resolver = commands.add_parser("resolve", help="只读选择目录及核对所提供的网页路径。")
    resolver.add_argument("--mode", choices=("new", "resume", "open"), required=True)
    explicit = resolver.add_mutually_exclusive_group()
    explicit.add_argument("--project", help="当前请求明确指定的项目绝对路径。")
    explicit.add_argument("--file-project", help="经过 Codex 确认归属的文件项目根；必须同时有 --file。")
    resolver.add_argument("--file", help="用户明确指定的任务文件绝对路径。")
    resolver.add_argument("--session-project", help="已从原会话核实的项目路径；仅适用于 resume。")
    resolver.add_argument("--web-workspace", help="刚从目标 dsh 网页核实的完整路径；不得猜测。")
    args = parser.parse_args()
    try:
        if args.command == "resolve":
            result = resolve_project(args)
        else:
            path = config_path(args.config)
            if args.command == "show":
                default = read_default(path)
                result = {"status": "configured" if default else "unset", "config": str(path), "default_project": default}
            elif args.command == "set":
                result = set_default(path, args.project)
            else:
                result = clear_default(path)
    except SelectionError as exc:
        result = {"status": "needs_input", "reason": exc.reason, "detail": exc.detail, "can_submit": False}
    except (OSError, RuntimeError, ValueError) as exc:
        result = {"status": "needs_input", "reason": "filesystem_error", "detail": type(exc).__name__, "can_submit": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] in {"needs_input", "needs_workspace_check"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
