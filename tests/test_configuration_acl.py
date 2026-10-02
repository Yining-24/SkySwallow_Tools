"""Check that existing Windows configuration is accepted only when private."""

import json
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
            return_value=SimpleNamespace(stdout=output),
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


if __name__ == "__main__":
    unittest.main()
