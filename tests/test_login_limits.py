"""Six-digit PINs retain server-side throttling and role permissions."""

from unittest.mock import patch
import unittest

from flask import Flask
from werkzeug.security import generate_password_hash

from skyswallow_tools.auth import auth_bp, permission_required


class LoginLimitTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SECRET_KEY="unit-test-only",
            PASSWORD_HASHES={
                role: generate_password_hash("048271", method="pbkdf2:sha256:1000")
                for role in ("admin", "finance", "followup")
            },
        )
        self.app.register_blueprint(auth_bp)

        @self.app.get("/test-profit")
        @permission_required("profit")
        def profit():
            return "ok"

        self.client = self.app.test_client()

    def login(self, password="wrong", role="admin", address="127.0.0.1"):
        return self.client.post(
            "/api/auth/login", json={"role": role, "password": password},
            environ_overrides={"REMOTE_ADDR": address},
        )

    def test_five_failures_then_block_and_expiry(self):
        with patch("skyswallow_tools.auth.monotonic", return_value=100):
            for _ in range(5):
                self.assertEqual(self.login().status_code, 401)
            response = self.login(password="048271")
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.headers["Retry-After"], "60")
        with patch("skyswallow_tools.auth.monotonic", return_value=160):
            self.assertEqual(self.login(password="048271").status_code, 200)

    def test_roles_share_attempt_limit_but_clients_do_not(self):
        for _ in range(5):
            self.login()
        self.assertEqual(self.login(password="048271", role="finance").status_code, 429)
        self.assertEqual(self.login(password="048271", address="192.0.2.10").status_code, 200)

    def test_success_clears_previous_failures(self):
        for _ in range(4):
            self.login()
        self.assertEqual(self.login(password="048271").status_code, 200)
        self.assertEqual(self.login().status_code, 401)

    def test_shared_pin_keeps_selected_role_permissions(self):
        for role, expected in (("admin", 200), ("finance", 200), ("followup", 403)):
            self.assertEqual(self.login(password="048271", role=role).status_code, 200)
            self.assertEqual(self.client.get("/test-profit").status_code, expected)

    def test_invalid_json_shape_is_an_authentication_failure(self):
        self.assertEqual(self.client.post("/api/auth/login", json=[1, 2]).status_code, 401)


if __name__ == "__main__":
    unittest.main()
