"""Create the private configuration for a packaged Windows installation."""

from getpass import getpass
import hashlib
import os
from pathlib import Path
import secrets
import tempfile

from . import find_instance_path


ROLE_NAMES = (
    ("admin", "Administrator"),
    ("finance", "Finance"),
    ("followup", "Follow-up staff"),
)
HASH_ITERATIONS = 1_000_000


def _password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        HASH_ITERATIONS,
    ).hex()
    return f"pbkdf2:sha256:{HASH_ITERATIONS}${salt}${digest}"


def _ask_password(label, used_passwords):
    while True:
        password = getpass(f"{label} password (at least 12 characters): ")

        if len(password) < 12:
            print("Please use at least 12 characters.")
            continue

        if password in used_passwords:
            print("Use a different password for each role.")
            continue

        if getpass("Repeat password: ") != password:
            print("The passwords did not match. Try again.")
            continue

        return password


def _allow_network_access():
    while True:
        answer = input(
            "Allow access from other computers on the local network? "
            "[y/N]: "
        ).strip().lower()

        if answer in ("", "n", "no"):
            return False

        if answer in ("y", "yes"):
            return True

        print("Enter y or n.")


def configure_instance():
    instance_path = find_instance_path()
    config_path = Path(instance_path) / "config.py"

    if config_path.exists():
        print(f"Existing configuration preserved: {config_path}")
        return config_path

    print("SkySwallow Tools first-time setup")
    print("Passwords are entered privately and stored only as hashes.")
    allow_network = _allow_network_access()

    password_hashes = {}
    used_passwords = set()

    for role, label in ROLE_NAMES:
        password = _ask_password(label, used_passwords)
        used_passwords.add(password)
        password_hashes[role] = _password_hash(password)

    secret_key = secrets.token_hex(32)
    server_host = "0.0.0.0" if allow_network else "127.0.0.1"
    lines = [
        "# Private SkySwallow Tools configuration. Do not share this file.",
        f"SECRET_KEY = {secret_key!r}",
        "PASSWORD_HASHES = {",
    ]

    for role, _ in ROLE_NAMES:
        lines.append(f"    {role!r}: {password_hashes[role]!r},")

    lines.extend(
        [
            "}",
            f"SERVER_HOST = {server_host!r}",
            "SERVER_PORT = 5001",
            "",
        ]
    )

    instance_path.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".config-",
        suffix=".tmp",
        dir=instance_path,
    )

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write("\n".join(lines))

        if config_path.exists():
            print(f"Existing configuration preserved: {config_path}")
            return config_path

        os.replace(temporary_name, config_path)
    finally:
        Path(temporary_name).unlink(missing_ok=True)

    print(f"Configuration saved: {config_path}")

    if allow_network:
        print("Local-network access selected. A Windows Firewall rule is still required.")
    else:
        print("This installation is accessible only on this computer.")

    return config_path
