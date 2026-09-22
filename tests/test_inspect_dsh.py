import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/dsh-dev/scripts/inspect_dsh.py"
spec = importlib.util.spec_from_file_location("inspect_dsh", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.modules = self.root / "node_modules"
        self.modules.mkdir()

    def package(self, name, **extra):
        path = self.modules / name / "package.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(name=name, version="0.1.5-rc.2", **extra)))
        return path

    def test_install_is_not_runtime_evidence(self):
        self.package("@deepseek-ai/dsh")
        self.package("@deepseek-ai/dsh-tool-workflow")
        result, code = module.inspect(self.modules)
        self.assertEqual(code, 0)
        self.assertEqual(result["runtime_available"], "not_checked")
        self.assertFalse(result["task_verified"])
        self.assertEqual(len(result["packages"]), 2)

    def test_manifest_scripts_are_not_executed_or_disclosed(self):
        marker = self.root / "executed"
        self.package("@deepseek-ai/dsh", scripts={"install": f"touch {marker}; TOKEN_SECRET"})
        result, _ = module.inspect(self.modules)
        self.assertFalse(marker.exists())
        self.assertNotIn("TOKEN_SECRET", json.dumps(result))
        self.assertTrue(result["packages"][0]["install_scripts_present"])

    def test_profile_secrets_and_yaml_are_never_read(self):
        profile = self.root / "profile"
        profile.mkdir()
        (profile / "package.json").write_text(json.dumps({
            "dependencies": {"example-plugin": "SECRET_SPEC", "../../escape": "x"},
            "dsh": {"profile": {"bundles": ["example-plugin"]}},
            "apiKey": "SECRET_KEY"}))
        (profile / "cordis.patch.yml").write_text("!!js SECRET_PATCH")
        (profile / ".credentials.yaml").write_text("SECRET_CREDENTIAL")
        result, code = module.inspect(self.modules, profile)
        self.assertEqual(code, 0)
        self.assertNotIn("SECRET", json.dumps(result))
        self.assertEqual(result["profile"]["dependencies"], ["example-plugin"])

    def test_bad_manifest_does_not_leak_contents(self):
        path = self.package("@deepseek-ai/dsh")
        path.write_text('{"apiKey": "VERY_SECRET", invalid')
        result, code = module.inspect(self.modules)
        self.assertEqual(code, 2)
        self.assertNotIn("VERY_SECRET", json.dumps(result))

    def test_multiple_installations_do_not_guess_resolution(self):
        path = self.package("@deepseek-ai/dsh")
        profile = self.root / "profile"
        target = profile / "node_modules/@deepseek-ai/dsh/package.json"
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps({"name": "@deepseek-ai/dsh", "version": "9.0.0"}))
        (profile / "package.json").write_text('{}')
        result, _ = module.inspect(self.modules, profile)
        self.assertEqual({p["version"] for p in result["packages"]}, {"0.1.5-rc.2", "9.0.0"})

    def test_symlinked_package_is_read_without_import(self):
        target = self.root / "actual"
        target.mkdir()
        (target / "package.json").write_text('{"name":"@deepseek-ai/dsh","version":"1.2.3"}')
        (self.modules / "@deepseek-ai").mkdir()
        (self.modules / "@deepseek-ai/dsh").symlink_to(target, target_is_directory=True)
        result, _ = module.inspect(self.modules)
        self.assertEqual(result["packages"][0]["version"], "1.2.3")

    def test_missing_root_and_nonobject_manifest(self):
        self.assertEqual(module.inspect(self.root / "missing")[1], 2)
        path = self.package("@deepseek-ai/dsh")
        path.write_text('[]')
        self.assertEqual(module.inspect(self.modules)[1], 2)

    def test_oversized_manifest_is_bounded(self):
        path = self.package("@deepseek-ai/dsh")
        path.write_bytes(b"x" * (module.LIMIT + 1))
        result, code = module.inspect(self.modules)
        self.assertEqual(code, 2)
        self.assertEqual(result["packages"][0]["state"], "manifest_too_large")

    def test_manifest_symlink_cannot_redirect_to_credential_filename(self):
        path = self.package("@deepseek-ai/dsh")
        secret = self.root / ".credentials.json"
        secret.write_text('{"apiKey":"UNREAD_SECRET"}')
        path.unlink()
        path.symlink_to(secret)
        result, code = module.inspect(self.modules)
        self.assertEqual(code, 2)
        self.assertEqual(result["packages"][0]["state"], "manifest_unexpected_target")
        self.assertNotIn("UNREAD_SECRET", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
