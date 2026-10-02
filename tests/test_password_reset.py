"""Shared-PIN migration must preserve configuration and support every role."""

import ast
from contextlib import ExitStack
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from werkzeug.security import check_password_hash, generate_password_hash

from skyswallow_tools import create_app
from skyswallow_tools.configuration import _ask_shared_pin, configure_instance, set_shared_pin


class PasswordResetTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.config = self.path / "config.py"
        self.old_passwords = {
            "admin": "OldAdministrator2026!",
            "finance": "OldFinancePassword2026!",
            "followup": "UnchangedFollowup2026!",
        }
        self.hashes = {
            role: generate_password_hash(password, method="pbkdf2:sha256:1000")
            for role, password in self.old_passwords.items()
        }
        self.original = (
            "# 私有配置：保留其他设置\r\n"
            "SECRET_KEY = 'keep-this-secret'\r\n"
            f"PASSWORD_HASHES = {self.hashes!r}\r\n"
            "SERVER_HOST = '0.0.0.0'\r\nSERVER_PORT = 5001\r\n"
            "EXTRA_SETTING = 'keep me'\r\n"
        ).encode("utf-8")
        self.config.write_bytes(self.original)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch(
            "skyswallow_tools.configuration.find_instance_path", return_value=self.path,
        ))
        # Real Windows ownership and ACLs are exercised by the installed-app CI test.
        self.stack.enter_context(patch("skyswallow_tools.configuration._check_reset_permissions"))
        self.stack.enter_context(patch("skyswallow_tools.configuration._secure_reset_file"))

    def run_reset(self, answers=None, confirmation="PIN"):
        answers = answers or ["048271", "048271"]
        with patch("builtins.input", return_value=confirmation), patch(
            "skyswallow_tools.configuration.getpass", side_effect=answers,
        ), patch("builtins.print"):
            return set_shared_pin()

    def settings(self):
        return {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in ast.parse(self.config.read_text(encoding="utf-8")).body
            if isinstance(node, ast.Assign)
        }

    def test_preserves_settings_and_private_backup(self):
        self.assertEqual(self.run_reset(), self.config)
        settings = self.settings()
        self.assertEqual(settings["SECRET_KEY"], "keep-this-secret")
        self.assertEqual(settings["SERVER_HOST"], "0.0.0.0")
        self.assertEqual(settings["SERVER_PORT"], 5001)
        self.assertEqual(settings["EXTRA_SETTING"], "keep me")
        for role in self.hashes:
            self.assertTrue(check_password_hash(settings["PASSWORD_HASHES"][role], "048271"))
        self.assertEqual(len(set(settings["PASSWORD_HASHES"].values())), 3)
        backups = list(self.path.glob("config-before-reset-*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), self.original)
        self.assertFalse(list(self.path.glob(".config-reset-*")))
        self.assertNotIn(b"048271", self.config.read_bytes())
        self.assertTrue(self.config.read_bytes().endswith(b"EXTRA_SETTING = 'keep me'\r\n"))

    def test_all_roles_can_log_in_and_old_reset_passwords_fail(self):
        self.run_reset()
        with patch("skyswallow_tools.INSTANCE_PATH", self.path):
            app = create_app()
        new_passwords = {role: "048271" for role in self.old_passwords}
        for role, password in new_passwords.items():
            with app.test_client() as client:
                response = client.post("/api/auth/login", json={"role": role, "password": password})
                self.assertEqual(response.status_code, 200, role)
                self.assertEqual(response.json["role"], role)
                response = client.post("/api/auth/login", json={"role": role, "password": self.old_passwords[role]})
                self.assertEqual(response.status_code, 401, role)

    def test_cancellation_preserves_original_without_backup(self):
        with self.assertRaisesRegex(OSError, "cancelled"):
            self.run_reset(confirmation="NO")
        self.assertEqual(self.config.read_bytes(), self.original)
        self.assertEqual(list(self.path.iterdir()), [self.config])

    def test_cancel_during_confirmation_does_not_save_pin(self):
        with self.assertRaises(KeyboardInterrupt):
            self.run_reset(["048271", KeyboardInterrupt()])
        self.assertEqual(self.config.read_bytes(), self.original)

    def test_pin_validation_and_confirmation(self):
        with patch("skyswallow_tools.configuration.getpass", side_effect=[
            "12345", "1234567", "abcdef", "１２３４５６", " 48271", "048271 ",
            "048271", "593804", "048271", "048271",
        ]) as prompt, patch("builtins.print"):
            self.assertEqual(_ask_shared_pin(), "048271")
            self.assertEqual(prompt.call_count, 10)

    def test_ambiguous_config_is_not_modified(self):
        content = self.original + b"PASSWORD_HASHES = {}\n"
        self.config.write_bytes(content)
        with self.assertRaisesRegex(OSError, "safely edited"):
            self.run_reset()
        self.assertEqual(self.config.read_bytes(), content)

    def test_private_file_failure_preserves_original(self):
        with patch("skyswallow_tools.configuration._secure_reset_file", side_effect=OSError("Access denied")):
            with self.assertRaisesRegex(OSError, "Access denied"):
                self.run_reset()
        self.assertEqual(self.config.read_bytes(), self.original)
        self.assertEqual(list(self.path.iterdir()), [self.config])

    def test_concurrent_config_change_is_not_overwritten(self):
        changed = self.original + b"# another update\n"
        calls = 0

        def verify(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                self.config.write_bytes(changed)

        with patch("skyswallow_tools.configuration._check_reset_permissions", side_effect=verify):
            with self.assertRaisesRegex(OSError, "changed during reset"):
                self.run_reset()
        self.assertEqual(self.config.read_bytes(), changed)

    def test_shared_pin_cli_does_not_start_server(self):
        from run_server import main

        with patch("run_server.set_shared_pin") as reset, patch("run_server._pause_reset_window"), patch("run_server.create_app") as app:
            self.assertEqual(main(["--set-shared-pin"]), 0)
            reset.assert_called_once_with()
            app.assert_not_called()

    def test_installer_pin_choice_updates_existing_config(self):
        with patch("skyswallow_tools.configuration._assert_trusted_acl"), patch(
            "skyswallow_tools.configuration._secure_instance_directory",
        ), patch("builtins.input", return_value="PIN"), patch(
            "skyswallow_tools.configuration.getpass", side_effect=["048271", "048271"],
        ), patch("builtins.print"):
            self.assertEqual(configure_instance(), self.config)
        for stored_hash in self.settings()["PASSWORD_HASHES"].values():
            self.assertTrue(check_password_hash(stored_hash, "048271"))


if __name__ == "__main__":
    unittest.main()
