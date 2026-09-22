#!/usr/bin/env python3
"""Static package/link/privacy checks. Not a substitute for a history review."""

import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TOP = {"README.md", "LICENSE", "NOTICE.md", "SECURITY.md", "CONTRIBUTING.md",
               ".gitignore", ".github", "skills", "tests", "tools", "docs", "examples"}
SECRET_PATTERNS = (
    r"/(?:Users|home)/[A-Za-z0-9_. -]+/", r"[A-Z]:\\Users\\[^\\\s]+\\",
    r"\bgh[pousr]_[A-Za-z0-9]{30,}\b", r"\bsk-[A-Za-z0-9_-]{24,}\b",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"https?://[^\s<>]+[?&](?:token|auth|api_key)=[A-Za-z0-9._~-]{8,}",
)


def public_files(root=ROOT):
    return sorted(p for p in root.rglob("*") if p.is_file()
                  and not any(part in {".git", "__pycache__", ".venv"} for part in p.relative_to(root).parts))


def check(root=ROOT):
    errors = []
    skill = root / "skills/dsh-dev"
    text = (skill / "SKILL.md").read_text()
    if not text.startswith("---\n") or text.count("\n---\n") < 1:
        errors.append("Missing skill frontmatter")
    header = text.split("---", 2)[1]
    if not re.search(r"^name: dsh-dev$", header, re.M) or not re.search(r"^description: .+", header, re.M):
        errors.append("Skill technical name or description mismatch")
    metadata = (skill / "agents/openai.yaml").read_text()
    if 'display_name: "呼叫蓝色大肥鱼"' not in metadata or "$dsh-dev" not in metadata:
        errors.append("Skill display name or invocation mismatch")
    links = 0
    files = public_files(root)
    for file in files:
        relative = file.relative_to(root)
        if relative.parts[0] not in ALLOWED_TOP:
            errors.append(f"Unexpected publication path: {relative}")
        if file.is_symlink():
            errors.append(f"Symlink in public package: {relative}")
        if file.name in {"config.json", "observation.json", ".env"} or file.suffix in {".log", ".jsonl", ".har"}:
            errors.append(f"Runtime data in public package: {relative}")
        try:
            body = file.read_text(encoding="utf-8")
        except UnicodeError:
            errors.append(f"Unexpected binary file: {relative}")
            continue
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, body, re.I):
                errors.append(f"Potential private path/credential in {relative}; inspect locally")
                break
        if file.suffix != ".md":
            continue
        for target in re.findall(r"\]\(([^)]+)\)", body):
            if "://" in target or target.startswith("mailto:"):
                continue
            name, _, anchor = target.partition("#")
            dest = (file.parent / name).resolve() if name else file.resolve()
            if not dest.is_relative_to(root.resolve()) or not dest.is_file():
                errors.append(f"Broken/outside relative link in {relative}: {target}")
                continue
            if anchor:
                headings = re.findall(r"^#+ (.+)$", dest.read_text(), re.M)
                anchors = [re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings]
                if anchor not in anchors:
                    errors.append(f"Missing anchor in {relative}: {target}")
            links += 1
    return {"files": len(files), "relative_links": links, "errors": errors}


if __name__ == "__main__":
    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(bool(result["errors"]))
