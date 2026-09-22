#!/usr/bin/env python3
"""Update/uninstall only dsh-dev, keeping a private backup and user config.

Initial installation uses Codex's bundled skill-installer. This local helper
does not install dsh, start services, change permissions, or access credentials.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile


SOURCE = Path(__file__).resolve().parents[1] / "skills" / "dsh-dev"


def absolute(value):
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError("Use an absolute installation/backup path.")
    return path


def inventory(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Skill must be a real directory, not a symlink.")
    paths = sorted(root.rglob("*"))
    if any(p.is_symlink() for p in paths):
        raise ValueError("Symlink inside skill; inspect manually before updating.")
    skill = root / "SKILL.md"
    if not skill.is_file() or not re.search(r"^name: dsh-dev\s*$", skill.read_text(), re.M):
        raise ValueError("Target is not an identifiable dsh-dev skill.")
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths if p.is_file()}


def maintain(action, skills_dir, backup_dir, source=SOURCE):
    if action not in ("update", "uninstall"):
        raise ValueError("Only update and uninstall are supported.")
    skills_dir = absolute(skills_dir).resolve()
    destination = skills_dir / "dsh-dev"
    backup_dir = absolute(backup_dir).resolve()
    source = source.resolve()
    if destination.resolve() == source:
        raise ValueError("Do not maintain the repository source as an installed copy.")
    if backup_dir.is_relative_to(skills_dir) or skills_dir.is_relative_to(backup_dir):
        raise ValueError("Backups must be separate from the skill search directory.")
    if not destination.exists() and not destination.is_symlink():
        raise ValueError("dsh-dev is not installed at this path; use skill-installer first.")
    old = inventory(destination)
    expected = inventory(source) if action == "update" else None
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    private = Path(tempfile.mkdtemp(prefix="copy-", dir=backup_dir))
    backup = private / "dsh-dev"
    shutil.copytree(destination, backup)
    if inventory(backup) != old:
        raise ValueError("Backup verification failed; installation was not changed.")
    with tempfile.TemporaryDirectory(prefix=".dsh-dev-stage-", dir=skills_dir.parent) as temp:
        stage = Path(temp) / "new"
        previous = Path(temp) / "previous"
        if action == "update":
            shutil.copytree(source, stage)
            if inventory(stage) != expected:
                raise ValueError("Staged copy differs from source.")
        if inventory(destination) != old:
            raise ValueError("Installed files changed during backup; retry after inspecting edits.")
        os.replace(destination, previous)
        try:
            if action == "update":
                os.replace(stage, destination)
                if inventory(destination) != expected:
                    raise ValueError("Updated copy verification failed.")
        except BaseException:
            if destination.exists():
                os.replace(destination, stage)
            os.replace(previous, destination)
            raise
    return {"action": action, "target": str(destination), "backup": str(backup),
            "user_config_changed": False, "dsh_settings_changed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("update", "uninstall"))
    parser.add_argument("--skills-dir", help="Actual Codex skill search directory (absolute).")
    parser.add_argument("--backup-dir", help="Private backup parent, outside skill search directories.")
    args = parser.parse_args()
    try:
        codex = absolute(os.environ.get("CODEX_HOME") or str(Path.home() / ".codex"))
        result = maintain(args.action, args.skills_dir or codex / "skills",
                          args.backup_dir or codex / "backups" / "dsh-dev")
    except (OSError, ValueError) as error:
        # OS errors may include a path but never read or print file contents.
        parser.exit(2, f"No successful {args.action}: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
