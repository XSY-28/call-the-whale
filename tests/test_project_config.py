"""Real CLI/filesystem checks in temporary directories; no dsh/model calls."""

import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(os.environ.get("DSH_DEV_TEST_SCRIPT") or (
    Path(__file__).resolve().parents[1] / "skills/dsh-dev/scripts/project_config.py"))
spec = importlib.util.spec_from_file_location("project_config", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProjectConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dsh-project-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.config = self.root / "private" / "config.json"
        self.a = self.root / "项目 A"
        self.b = self.root / "project B"
        self.cwd = self.root / "unrelated-codex-cwd"
        for path in (self.a, self.b, self.cwd):
            path.mkdir()
        self.file = self.a / "src" / "task.py"
        self.file.parent.mkdir()
        self.file.write_text("# task object\n")
        self.env = dict(os.environ, CODEX_HOME=str(self.root / "codex-home"), PYTHONDONTWRITEBYTECODE="1")

    def cli(self, *args, code=0, with_config=True):
        command = [sys.executable, str(SCRIPT)]
        if with_config:
            command += ["--config", str(self.config)]
        run = subprocess.run(command + list(map(str, args)), cwd=self.cwd,
                             env=self.env, capture_output=True, text=True)
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        return json.loads(run.stdout)

    def save(self, project=None):
        return self.cli("set", "--project", project or self.a, "--user-requested")

    def stored(self, value):
        self.config.parent.mkdir(exist_ok=True)
        self.config.write_text(value)

    def resolve(self, *args, mode="new", code=0):
        return self.cli("resolve", "--mode", mode, *args, code=code)

    def test_explicit_project_overrides_default_without_saving(self):
        self.save()
        before = self.config.read_bytes()
        result = self.resolve("--project", self.b, "--web-workspace", self.b)
        self.assertEqual((result["project"], result["source"]), (str(self.b), "explicit"))
        self.assertTrue(result["can_submit"])
        self.assertEqual(self.config.read_bytes(), before)

    def test_unspecified_new_task_uses_default_not_cwd(self):
        self.save()
        result = self.resolve("--web-workspace", self.a)
        self.assertEqual((result["project"], result["source"]), (str(self.a), "default"))
        self.assertTrue(result["can_submit"])

    def test_no_default_asks_even_if_web_workspace_and_cwd_exist(self):
        result = self.resolve("--web-workspace", self.cwd, code=2)
        self.assertEqual(result["reason"], "default_missing")
        self.assertFalse(result["can_submit"])
        self.assertFalse(self.config.exists())
        self.assertFalse(self.config.parent.exists())

    def test_unavailable_explicit_project_does_not_fall_back(self):
        self.save()
        result = self.resolve("--project", self.root / "missing", "--web-workspace", self.a, code=2)
        self.assertEqual(result["reason"], "path_missing")
        self.assertFalse(result["can_submit"])
        self.assertNotIn("project", result)

    def test_unavailable_default_does_not_use_selected_web_workspace(self):
        self.save(self.b)
        before = self.config.read_bytes()
        self.b.rmdir()
        result = self.resolve("--web-workspace", self.a, code=2)
        self.assertEqual((result["reason"], result["source"]), ("path_missing", "default"))
        self.assertEqual(result["candidate_project"], str(self.b))
        self.assertFalse(result["can_submit"])
        self.assertEqual(self.config.read_bytes(), before)

    def test_file_cannot_be_used_as_project_directory(self):
        result = self.resolve("--project", self.file, code=2)
        self.assertEqual(result["reason"], "not_a_directory")

    def test_file_without_confirmed_project_asks_and_preserves_task_object(self):
        self.save(self.b)
        result = self.resolve("--file", self.file, code=2)
        self.assertEqual(result["reason"], "file_project_required")
        self.assertEqual(result["task_file"], str(self.file))
        self.assertNotIn("project", result)
        self.assertFalse(result["can_submit"])

    def test_file_with_confirmed_root_retains_both_paths(self):
        result = self.resolve("--file", self.file, "--file-project", self.a, "--web-workspace", self.a)
        self.assertEqual((result["project"], result["task_file"]), (str(self.a), str(self.file)))
        self.assertEqual(result["source"], "file_confirmed")
        self.assertTrue(result["can_submit"])

    def test_file_outside_confirmed_project_needs_clarification(self):
        result = self.resolve("--file", self.file, "--project", self.b, code=2)
        self.assertEqual(result["reason"], "file_outside_project")

    def test_missing_task_file_is_not_replaced_by_default(self):
        self.save()
        result = self.resolve("--file", self.a / "missing.py", "--file-project", self.a, code=2)
        self.assertEqual(result["reason"], "path_missing")

    def test_resume_keeps_confirmed_session_project_despite_default(self):
        self.save(self.b)
        before = self.config.read_bytes()
        result = self.resolve("--session-project", self.a, "--web-workspace", self.a, mode="resume")
        self.assertEqual((result["project"], result["source"]), (str(self.a), "session"))
        self.assertTrue(result["can_submit"])
        self.assertEqual(self.config.read_bytes(), before)

    def test_resume_conflict_needs_clarification(self):
        result = self.resolve("--session-project", self.a, "--project", self.b,
                              "--web-workspace", self.a, mode="resume", code=2)
        self.assertEqual(result["reason"], "session_project_conflict")
        self.assertEqual(result["session_project"], str(self.a))
        self.assertFalse(result["can_submit"])

    def test_resume_same_explicit_project_is_allowed(self):
        result = self.resolve("--session-project", self.a, "--project", self.a,
                              "--web-workspace", self.a, mode="resume")
        self.assertTrue(result["can_submit"])

    def test_resume_unknown_project_never_uses_default(self):
        self.save()
        result = self.resolve("--web-workspace", self.a, mode="resume", code=2)
        self.assertEqual(result["reason"], "session_project_required")

    def test_resume_unavailable_project_never_uses_default(self):
        self.save()
        result = self.resolve("--session-project", self.root / "gone", mode="resume", code=2)
        self.assertEqual(result["reason"], "path_missing")
        self.assertEqual(result["source"], "session")
        self.assertNotIn("project", result)

    def test_open_only_needs_no_default_and_cannot_submit(self):
        result = self.resolve(mode="open")
        self.assertEqual(result["status"], "open_only")
        self.assertTrue(result["may_open"])
        self.assertFalse(result["can_submit"])
        self.assertFalse(self.config.exists())

    def test_invalid_explicit_project_still_allows_opening_page(self):
        result = self.resolve("--project", self.root / "missing", mode="open", code=2)
        self.assertTrue(result["may_open"])
        self.assertFalse(result["can_submit"])

    def test_open_with_confirmed_project_still_cannot_submit(self):
        result = self.resolve("--project", self.a, "--web-workspace", self.a, mode="open")
        self.assertEqual(result["status"], "ready")
        self.assertFalse(result["can_submit"])

    def test_web_path_is_required_and_must_match(self):
        self.save()
        unchecked = self.resolve(code=2)
        mismatch = self.resolve("--web-workspace", self.b, code=2)
        self.assertEqual(unchecked["reason"], "web_workspace_unconfirmed")
        self.assertEqual(mismatch["reason"], "web_workspace_mismatch")
        self.assertFalse(unchecked["can_submit"] or mismatch["can_submit"])

    def test_same_named_directories_are_not_equal(self):
        same_name = self.b / self.a.name
        same_name.mkdir()
        result = self.resolve("--project", self.a, "--web-workspace", same_name, code=2)
        self.assertEqual(result["reason"], "web_workspace_mismatch")

    def test_canonical_symlink_alias_is_same_project(self):
        alias = self.root / "alias"
        alias.symlink_to(self.a, target_is_directory=True)
        result = self.resolve("--project", alias, "--session-project", self.a,
                              "--web-workspace", self.a, mode="resume")
        self.assertTrue(result["can_submit"])
        self.assertEqual(result["project"], str(self.a))

    def test_relative_path_is_not_resolved_against_cwd(self):
        result = self.resolve("--project", ".", code=2)
        self.assertEqual(result["reason"], "absolute_path_required")

    def test_show_is_read_only_and_does_not_create_config(self):
        result = self.cli("show")
        self.assertEqual(result["status"], "unset")
        self.assertFalse(self.config.parent.exists())

    def test_set_update_and_clear_touch_only_dedicated_config(self):
        self.save()
        result = self.save(self.b)
        self.assertEqual(result["default_project"], str(self.b))
        sibling = self.config.parent / "session.json"
        sibling.write_text("keep")
        cleared = self.cli("clear", "--user-requested")
        self.assertTrue(cleared["existed"])
        self.assertFalse(self.config.exists())
        self.assertEqual(sibling.read_text(), "keep")
        self.assertTrue(self.a.is_dir() and self.b.is_dir())
        self.assertFalse(self.cli("clear", "--user-requested")["existed"])

    def test_set_validates_before_replacing_old_default(self):
        self.save()
        before = self.config.read_bytes()
        result = self.cli("set", "--project", self.root / "missing", "--user-requested", code=2)
        self.assertEqual(result["reason"], "path_missing")
        self.assertEqual(self.config.read_bytes(), before)

    def test_mutations_require_deliberate_flag(self):
        for args in (("set", "--project", self.a), ("clear",)):
            run = subprocess.run([sys.executable, str(SCRIPT), "--config", str(self.config), *map(str, args)],
                                 env=self.env, cwd=self.cwd, capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn("--user-requested", run.stderr)
        self.assertFalse(self.config.exists())

    def test_new_private_config_permissions(self):
        self.save()
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.config.parent.stat().st_mode), 0o700)

    def test_codex_home_override_keeps_default_location_outside_skill(self):
        result = self.cli("set", "--project", self.a, "--user-requested", with_config=False)
        expected = self.root / "codex-home" / "dsh-dev" / "config.json"
        self.assertEqual(result["config"], str(expected))
        self.assertTrue(expected.exists())
        self.assertFalse(self.config.exists())

    def test_unset_codex_home_path_calculation_is_read_only(self):
        with patch.dict(os.environ, {"CODEX_HOME": ""}), patch.object(Path, "home", return_value=self.root):
            self.assertEqual(module.config_path(), self.root / ".codex/dsh-dev/config.json")
        self.assertFalse((self.root / ".codex").exists())

    def test_corrupt_default_blocks_fallback_but_not_explicit_resume_or_open(self):
        self.stored('{"private":"DO_NOT_DISCLOSE", invalid')
        before = self.config.read_bytes()
        result = self.resolve("--web-workspace", self.a, code=2)
        self.assertEqual(result["reason"], "config_unreadable")
        self.assertNotIn("DO_NOT_DISCLOSE", json.dumps(result))
        self.resolve("--project", self.a, "--web-workspace", self.a)
        self.resolve("--session-project", self.a, "--web-workspace", self.a, mode="resume")
        self.resolve(mode="open")
        self.assertEqual(self.config.read_bytes(), before)

    def test_future_schema_is_not_overwritten_by_set(self):
        self.stored('{"schema":2,"default_project":"/future"}')
        before = self.config.read_bytes()
        result = self.cli("set", "--project", self.a, "--user-requested", code=2)
        self.assertEqual(result["reason"], "config_invalid")
        self.assertEqual(self.config.read_bytes(), before)
        self.cli("clear", "--user-requested")
        self.assertFalse(self.config.exists())

    def test_config_symlink_is_not_followed_or_deleted(self):
        self.config.parent.mkdir()
        target = self.root / "external.json"
        target.write_text("DO_NOT_DISCLOSE")
        self.config.symlink_to(target)
        for args in (("show",), ("set", "--project", self.a, "--user-requested"), ("clear", "--user-requested")):
            result = self.cli(*args, code=2)
            self.assertEqual(result["reason"], "config_symlink")
        self.assertTrue(self.config.is_symlink())
        self.assertEqual(target.read_text(), "DO_NOT_DISCLOSE")

    def test_config_cannot_be_placed_inside_shareable_skill(self):
        with self.assertRaises(module.SelectionError) as raised:
            module.config_path(str(module.SKILL_ROOT / "config.json"))
        self.assertEqual(raised.exception.reason, "config_inside_skill")

    def test_atomic_replace_failure_preserves_previous_value(self):
        self.save()
        before = self.config.read_bytes()
        with patch.object(module.os, "replace", side_effect=OSError("simulated disk failure")):
            with self.assertRaises(OSError):
                module.set_default(self.config, self.b)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual(list(self.config.parent.glob(".config-*.tmp")), [])

    @unittest.skipIf(os.geteuid() == 0, "root bypasses directory mode restrictions")
    def test_actual_inaccessible_directory_is_reported_without_fallback(self):
        self.save()
        old_mode = self.b.stat().st_mode
        self.b.chmod(0)
        try:
            result = self.resolve("--project", self.b, "--web-workspace", self.a, code=2)
            self.assertEqual(result["reason"], "path_inaccessible")
            self.assertFalse(result["can_submit"])
        finally:
            self.b.chmod(stat.S_IMODE(old_mode))


if __name__ == "__main__":
    unittest.main()
