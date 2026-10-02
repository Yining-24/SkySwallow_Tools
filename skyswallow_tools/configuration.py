"""Create the private configuration for a packaged Windows installation."""

import csv
from getpass import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile

from . import find_instance_path


ROLE_NAMES = (
    ("admin", "Administrator"),
    ("finance", "Finance"),
    ("followup", "Follow-up staff"),
)
HASH_ITERATIONS = 1_000_000
SID_PATTERN = re.compile(r"S-\d+(?:-\d+)+")
ADMINISTRATORS_SID = "S-1-5-32-544"
SYSTEM_SID = "S-1-5-18"
TRUSTED_OWNERS = {ADMINISTRATORS_SID, SYSTEM_SID}


def _run_icacls(path, *arguments):
    result = subprocess.run(
        ["icacls", str(path), *arguments],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise OSError(f"Could not secure {path}: {detail}")


def _current_user_sid():
    identity = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"],
        capture_output=True,
        text=True,
        errors="replace",
        check=True,
    )
    rows = list(csv.reader(identity.stdout.splitlines()))
    sid = rows[0][-1].strip() if rows else ""

    if not SID_PATTERN.fullmatch(sid):
        raise OSError("Could not identify the Windows account for configuration.")

    return sid


def _assert_trusted_acl(path, allowed_sids):
    script = r"""
$ErrorActionPreference = 'Stop'
$acl = Get-Acl -LiteralPath $env:SKYSWALLOW_ACL_TARGET
$grants = @(
    foreach ($entry in $acl.Access) {
        if ($entry.AccessControlType -eq 'Allow') {
            $entry.IdentityReference.Translate(
                [System.Security.Principal.SecurityIdentifier]
            ).Value
        }
    }
)
[pscustomobject]@{
    Owner = $acl.GetOwner(
        [System.Security.Principal.SecurityIdentifier]
    ).Value
    Grants = $grants
} | ConvertTo-Json -Compress -Depth 3
"""
    # A Python child of PowerShell 7 inherits incompatible Windows PowerShell
    # module paths. Let powershell.exe rebuild its own module search path.
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper() != "PSMODULEPATH"
    }
    environment["SKYSWALLOW_ACL_TARGET"] = str(path)
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        env=environment,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise OSError(f"Could not inspect permissions on {path}: {detail}")

    try:
        acl = json.loads(result.stdout)
    except (TypeError, ValueError) as error:
        raise OSError(f"Could not inspect permissions on {path}.") from error

    if not isinstance(acl, dict):
        raise OSError(f"Could not inspect permissions on {path}.")
    owner = acl.get("Owner")
    grants = acl.get("Grants")

    if owner not in TRUSTED_OWNERS or not isinstance(grants, list):
        raise OSError(f"Untrusted owner or permissions on {path}.")

    if any(sid not in allowed_sids for sid in grants):
        raise OSError(f"Untrusted permissions on {path}.")


def _secure_instance_directory(instance_path, sid):
    if instance_path.is_symlink() or instance_path.is_junction():
        raise OSError("The configuration directory cannot be a link or junction.")

    _run_icacls(instance_path, "/reset")
    _run_icacls(
        instance_path,
        "/grant:r",
        f"*{sid}:(OI)(CI)F",
        f"*{ADMINISTRATORS_SID}:(OI)(CI)F",
        f"*{SYSTEM_SID}:(OI)(CI)F",
    )
    _run_icacls(instance_path, "/inheritance:r")
    _run_icacls(instance_path, "/setowner", f"*{ADMINISTRATORS_SID}")
    _assert_trusted_acl(instance_path, {sid, ADMINISTRATORS_SID, SYSTEM_SID})


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

    if instance_path.is_symlink() or instance_path.is_junction():
        raise OSError("The configuration directory cannot be a link or junction.")

    directory_existed = instance_path.exists()
    sid = _current_user_sid() if os.name == "nt" else None
    allowed_sids = {sid, ADMINISTRATORS_SID, SYSTEM_SID}

    if directory_existed and os.name == "nt":
        _assert_trusted_acl(instance_path, allowed_sids)

        if config_path.is_symlink():
            raise OSError("The configuration file cannot be a link.")

        if config_path.exists():
            if not config_path.is_file():
                raise OSError("The configuration path is not a file.")

            _assert_trusted_acl(config_path, allowed_sids)

    instance_path.mkdir(parents=True, exist_ok=True)

    if os.name == "nt":
        _secure_instance_directory(instance_path, sid)

    if config_path.is_symlink():
        raise OSError("The configuration file cannot be a link.")

    if config_path.exists():
        if not config_path.is_file():
            raise OSError("The configuration path is not a file.")

        # Also catches a file planted while a new directory was being secured.
        if os.name == "nt":
            _assert_trusted_acl(config_path, allowed_sids)

        answer = input(
            f"Existing configuration found at {config_path}. "
            "Type REUSE only if you recognize this file: "
        ).strip()

        if answer != "REUSE":
            raise OSError("Existing configuration was not approved for reuse.")

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

        if os.name == "nt":
            _run_icacls(config_path, "/reset")
            _run_icacls(config_path, "/setowner", f"*{ADMINISTRATORS_SID}")
            _assert_trusted_acl(config_path, allowed_sids)
    finally:
        Path(temporary_name).unlink(missing_ok=True)

    print(f"Configuration saved: {config_path}")

    if allow_network:
        print("Local-network access selected. A Windows Firewall rule is still required.")
    else:
        print("This installation is accessible only on this computer.")

    return config_path
