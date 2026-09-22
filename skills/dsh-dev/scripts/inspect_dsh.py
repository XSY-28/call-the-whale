#!/usr/bin/env python3
"""Read package metadata only. Never boot dsh, import plugins, or read secrets."""
import argparse
import json
import re
import sys
from pathlib import Path

PACKAGE = re.compile(r"(?:@[a-z0-9._-]+/)?[a-z0-9][a-z0-9._-]*\Z")
VERSION = re.compile(r"[0-9][0-9A-Za-z.+_-]*\Z")
RELEVANT = re.compile(r"^@deepseek-ai/dsh(?:$|.*(?:subagent|workflow|agent-team|directory-picker))")
LIMIT = 1024 * 1024


def read_object(path):
    # Error messages deliberately omit source contents and exception details.
    try:
        if path.resolve().name != "package.json":
            return None, "manifest_unexpected_target"
        if path.exists() and not path.is_file():
            return None, "manifest_not_regular_file"
        with path.open("rb") as stream:
            raw = stream.read(LIMIT + 1)
        if len(raw) > LIMIT:
            return None, "manifest_too_large"
        value = json.loads(raw)
        if not isinstance(value, dict):
            return None, "manifest_not_object"
        return value, None
    except FileNotFoundError:
        return None, "manifest_missing"
    except (OSError, ValueError):
        return None, "manifest_unreadable_or_invalid"


def object_value(value):
    return value if isinstance(value, dict) else {}


def package_names(value):
    values = value.keys() if isinstance(value, dict) else value
    if not isinstance(values, (list, type({}.keys()))):
        return []
    return sorted({s for s in values if isinstance(s, str) and PACKAGE.fullmatch(s)})


def inspect(node_modules, profile=None):
    root = Path(node_modules).expanduser().resolve()
    report = {
        "schema": 1,
        "node_modules": str(root),
        "evidence": "package_metadata_only",
        "runtime_available": "not_checked",
        "task_verified": False,
        "packages": [],
        "warnings": [],
    }
    if not root.is_dir():
        report["warnings"].append("node_modules_missing")
        return report, 2
    names = set()
    namespace = root / "@deepseek-ai"
    if namespace.is_dir():
        try:
            names.update("@deepseek-ai/" + p.name for p in namespace.iterdir()
                         if PACKAGE.fullmatch("@deepseek-ai/" + p.name)
                         and RELEVANT.search("@deepseek-ai/" + p.name))
        except OSError:
            report["warnings"].append("namespace_unreadable")
    profile_root = None
    if profile:
        profile_root = Path(profile).expanduser().resolve()
        manifest, error = read_object(profile_root / "package.json")
        if error:
            report["warnings"].append("profile_" + error)
        else:
            deps = package_names(manifest.get("dependencies", {}))
            bundle_names = package_names(object_value(object_value(
                manifest.get("dsh")).get("profile")).get("bundles", []))
            names.update(deps + bundle_names)
            report["profile"] = {
                "path": str(profile_root),
                "dependencies": deps,
                "declared_bundles": bundle_names,
                "patch_exists": (profile_root / "cordis.patch.yml").is_file(),
                "note": "Bundle declarations do not prove activation; user patches are not read.",
            }
    names.add("@deepseek-ai/dsh")
    # List all observed locations: dsh's resolver may give bundled packages
    # different precedence from profile packages. Do not guess the winner.
    for name in sorted(names):
        locations = [root / name / "package.json"]
        if profile_root:
            locations.append(profile_root / "node_modules" / name / "package.json")
        observed = set()
        for path in locations:
            if not path.exists() and path != locations[0]:
                continue
            real = path.resolve()
            if real in observed:
                continue
            observed.add(real)
            manifest, error = read_object(path)
            item = {"name": name, "manifest": str(real)}
            if error:
                item["state"] = error
            elif manifest.get("name") != name:
                item["state"] = "name_mismatch"
            else:
                version = manifest.get("version")
                item.update(
                    state="installed_metadata",
                    version=version if isinstance(version, str) and VERSION.fullmatch(version) else "unknown",
                    declares_bundle=isinstance(object_value(manifest.get("dsh")).get("bundle"), dict),
                    peer_dependencies=package_names(manifest.get("peerDependencies", {})),
                    install_scripts_present=any(k in object_value(manifest.get("scripts"))
                                                for k in ("preinstall", "install", "postinstall", "prepare")),
                )
            report["packages"].append(item)
    partial = bool(report["warnings"]) or any(
        p["state"] not in ("installed_metadata", "manifest_missing") for p in report["packages"])
    return report, 2 if partial else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node-modules", required=True, type=Path)
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()
    report, code = inspect(args.node_modules, args.profile)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
