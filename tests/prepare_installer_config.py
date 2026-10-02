"""Exercise first-time setup before launching an installed build in CI."""

import os
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import check_password_hash

from skyswallow_tools.configuration import configure_instance


PASSWORDS = {
    "admin": "AdminSmokeTest2026!",
    "finance": "FinanceSmokeTest2026!",
    "followup": "FollowupSmokeTest2026!",
}


def main():
    instance_path = os.environ.get("SKYSWALLOW_INSTANCE_PATH")

    if not instance_path:
        raise RuntimeError("SKYSWALLOW_INSTANCE_PATH is required for this test.")

    answers = []

    for role in ("admin", "finance", "followup"):
        answers.extend([PASSWORDS[role], PASSWORDS[role]])

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
