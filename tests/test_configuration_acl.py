"""Check that existing Windows configuration is accepted only when private."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from skyswallow_tools.configuration import (
    ADMINISTRATORS_SID,
    SYSTEM_SID,
    _assert_trusted_acl,
)


class ConfigurationAclTests(unittest.TestCase):
    def setUp(self):
        self.allowed = {"S-1-5-21-123-456-789-500", ADMINISTRATORS_SID, SYSTEM_SID}

    def check_acl(self, owner, grants):
        output = json.dumps({"Owner": owner, "Grants": grants})

        with patch(
            "skyswallow_tools.configuration.subprocess.run",
            return_value=SimpleNamespace(stdout=output, stderr="", returncode=0),
        ):
            _assert_trusted_acl(Path("example"), self.allowed)

    def test_accepts_private_admin_owned_file(self):
        self.check_acl(ADMINISTRATORS_SID, list(self.allowed))

    def test_rejects_file_owned_by_another_user(self):
        with self.assertRaises(OSError):
            self.check_acl("S-1-5-21-123-456-789-1001", list(self.allowed))

    def test_rejects_broad_access(self):
        with self.assertRaises(OSError):
            self.check_acl(ADMINISTRATORS_SID, [*self.allowed, "S-1-1-0"])

    def test_reports_windows_inspection_error(self):
        with patch(
            "skyswallow_tools.configuration.subprocess.run",
            return_value=SimpleNamespace(
                stdout="", stderr="Access is denied", returncode=1,
            ),
        ), self.assertRaisesRegex(OSError, "Access is denied"):
            _assert_trusted_acl(Path("example"), self.allowed)

    def test_does_not_inherit_powershell_7_module_paths(self):
        output = json.dumps({
            "Owner": ADMINISTRATORS_SID,
            "Grants": list(self.allowed),
        })

        with patch.dict(os.environ, {"PSModulePath": "PowerShell7Modules"}), patch(
            "skyswallow_tools.configuration.subprocess.run",
            return_value=SimpleNamespace(stdout=output, stderr="", returncode=0),
        ) as process:
            _assert_trusted_acl(Path("example"), self.allowed)
            environment = process.call_args.kwargs["env"]
            self.assertFalse(any(key.upper() == "PSMODULEPATH" for key in environment))
            self.assertEqual(os.environ["PSModulePath"], "PowerShell7Modules")


if __name__ == "__main__":
    unittest.main()
