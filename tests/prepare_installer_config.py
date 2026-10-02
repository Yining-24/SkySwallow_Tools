"""Exercise first-time setup before launching an installed build in CI."""

import os
from pathlib import Path
import sys
from unittest.mock import patch

from werkzeug.security import check_password_hash

from skyswallow_tools.configuration import configure_instance, set_shared_pin


PASSWORDS = {
    "admin": "048271",
    "finance": "048271",
    "followup": "048271",
}

RESET_PASSWORDS = {
    "admin": "593804",
    "finance": "593804",
    "followup": "593804",
}


def check_reset(instance_path):
    config_path = Path(instance_path) / "config.py"
    before = {}
    exec(compile(config_path.read_text(encoding="utf-8"), str(config_path), "exec"), before)
    answers = [RESET_PASSWORDS["admin"]] * 2
    with patch("builtins.input", return_value="PIN"), patch(
        "skyswallow_tools.configuration.getpass", side_effect=answers,
    ):
        assert set_shared_pin() == config_path
    after = {}
    config_text = config_path.read_text(encoding="utf-8")
    exec(compile(config_text, str(config_path), "exec"), after)
    for key in ("SECRET_KEY", "SERVER_HOST", "SERVER_PORT"):
        assert before[key] == after[key]
    for role, password in RESET_PASSWORDS.items():
        assert password not in config_text
        assert check_password_hash(after["PASSWORD_HASHES"][role], password)
        assert not check_password_hash(after["PASSWORD_HASHES"][role], PASSWORDS[role])
    print("Shared PIN updated for every role; all other settings preserved.")


def main():
    instance_path = os.environ.get("SKYSWALLOW_INSTANCE_PATH")

    if not instance_path:
        raise RuntimeError("SKYSWALLOW_INSTANCE_PATH is required for this test.")

    if sys.argv[1:] == ["--reset"]:
        check_reset(instance_path)
        return

    answers = [PASSWORDS["admin"]] * 2

    with patch(
        "skyswallow_tools.configuration._allow_network_access",
        return_value=False,
    ), patch(
        "skyswallow_tools.configuration.getpass",
        side_effect=answers,
    ):
        config_path = configure_instance()

    assert config_path == Path(instance_path) / "config.py"
    config_text = config_path.read_text(encoding="utf-8")
    assert all(password not in config_text for password in PASSWORDS.values())

    settings = {}
    exec(compile(config_text, str(config_path), "exec"), settings)
    assert settings["SERVER_HOST"] == "127.0.0.1"
    assert len(settings["SECRET_KEY"]) >= 64

    for role, password in PASSWORDS.items():
        assert check_password_hash(settings["PASSWORD_HASHES"][role], password)

    with patch("builtins.input", return_value="REUSE"):
        assert configure_instance() == config_path

    assert config_path.read_text(encoding="utf-8") == config_text

    print("First-time configuration passed the installed-app check.")


if __name__ == "__main__":
    main()
