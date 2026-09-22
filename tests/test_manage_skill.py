import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/manage_skill.py"
spec = importlib.util.spec_from_file_location("manage_skill", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="whale-maintenance-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.codex = self.root / "codex"
        self.skills = self.codex / "skills"
        self.destination = self.skills / "dsh-dev"
        self.backups = self.codex / "backups/dsh-dev"
        shutil.copytree(ROOT / "skills/dsh-dev", self.destination)
        self.config = self.codex / "dsh-dev/config.json"
        self.config.parent.mkdir()
        self.config.write_text('{"schema":1,"default_project":"/placeholder/project"}')
        self.config_before = self.config.read_bytes()
        self.handoff = self.codex / "dsh-dev/handoff.json"
        self.handoff.write_text('{"keep":"private progress"}')

    def cli(self, action):
        run = subprocess.run([sys.executable, str(SCRIPT), action],
            env=dict(os.environ, CODEX_HOME=str(self.codex), PYTHONDONTWRITEBYTECODE="1"),
            capture_output=True, text=True, cwd=self.root)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return json.loads(run.stdout)

    def test_update_backs_up_local_edits_and_preserves_user_config(self):
        (self.destination / "custom-note.md").write_text("local edits, not repository content")
        original = module.inventory(self.destination)
        result = self.cli("update")
        self.assertEqual(module.inventory(Path(result["backup"])), original)
        self.assertEqual(module.inventory(self.destination), module.inventory(ROOT / "skills/dsh-dev"))
        self.assertEqual(self.config.read_bytes(), self.config_before)
        self.assertTrue(self.handoff.exists())

    def test_uninstall_moves_only_skill_and_preserves_config(self):
        original = module.inventory(self.destination)
        result = self.cli("uninstall")
        self.assertFalse(self.destination.exists())
        self.assertEqual(module.inventory(Path(result["backup"])), original)
        self.assertEqual(self.config.read_bytes(), self.config_before)
        self.assertTrue(self.handoff.exists())

    def test_update_failure_rolls_back(self):
        original = module.inventory(self.destination)
        real_replace = module.os.replace
        def fail_new(source, target):
            if Path(source).name == "new":
                raise OSError("simulated replacement failure")
            return real_replace(source, target)
        with patch.object(module.os, "replace", side_effect=fail_new):
            with self.assertRaises(OSError):
                module.maintain("update", self.skills, self.backups)
        self.assertEqual(module.inventory(self.destination), original)
        self.assertEqual(self.config.read_bytes(), self.config_before)

    def test_missing_install_does_not_implicitly_install(self):
        shutil.rmtree(self.destination)
        with self.assertRaises(ValueError):
            module.maintain("update", self.skills, self.backups)
        self.assertFalse(self.destination.exists())

    def test_unrelated_skill_directory_is_not_replaced(self):
        (self.destination / "SKILL.md").write_text("---\nname: unrelated\n---\n")
        with self.assertRaises(ValueError):
            module.maintain("update", self.skills, self.backups)
        self.assertIn("unrelated", (self.destination / "SKILL.md").read_text())

    def test_symlinked_files_are_not_followed(self):
        target = self.root / "outside"
        target.write_text("private")
        (self.destination / "link").symlink_to(target)
        with self.assertRaises(ValueError):
            module.maintain("update", self.skills, self.backups)
        self.assertEqual(target.read_text(), "private")

    def test_backup_cannot_create_duplicate_discoverable_skill(self):
        with self.assertRaises(ValueError):
            module.maintain("update", self.skills, self.skills / "backup")

    def test_repository_source_is_not_an_installation(self):
        with self.assertRaises(ValueError):
            module.maintain("uninstall", ROOT / "skills", self.backups)


if __name__ == "__main__":
    unittest.main()
