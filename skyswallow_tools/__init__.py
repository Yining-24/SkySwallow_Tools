from datetime import timedelta
import os
from pathlib import Path
import sys

from flask import Flask, abort, send_from_directory

from .api import api_bp
from .auth import auth_bp


def find_resource_root():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)

    return Path(__file__).resolve().parent.parent


def find_instance_path():
    configured_path = os.environ.get(
        "SKYSWALLOW_INSTANCE_PATH"
    )

    if configured_path:
        return Path(configured_path)

    if getattr(sys, "frozen", False):
        program_data = os.environ.get("PROGRAMDATA")

        if program_data:
            return Path(program_data) / "SkySwallowTools"

        return Path.home() / ".skyswallow_tools"

    return Path(__file__).resolve().parent.parent / "instance"


RESOURCE_ROOT = find_resource_root()
FRONTEND_DIST = RESOURCE_ROOT / "frontend" / "dist"
INSTANCE_PATH = find_instance_path()


def create_app():
    INSTANCE_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    app = Flask(
        __name__,
        instance_relative_config=True,
        instance_path=str(INSTANCE_PATH),
    )

    try:
        app.config.from_pyfile("config.py")
    except FileNotFoundError as error:
        config_path = INSTANCE_PATH / "config.py"

        raise RuntimeError(
            f"找不到配置文件：{config_path}"
        ) from error

    app.config.update(
        MAX_CONTENT_LENGTH=20 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    )

    password_hashes = app.config.get("PASSWORD_HASHES", {})
    required_roles = {"admin", "finance", "followup"}
    missing_roles = required_roles - password_hashes.keys()

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("config.py 缺少 SECRET_KEY。")

    if missing_roles:
        missing = ", ".join(sorted(missing_roles))

        raise RuntimeError(
            f"config.py 缺少角色口令：{missing}"
        )

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    @app.get("/")
    def frontend_index():
        return send_from_directory(
            str(FRONTEND_DIST),
            "index.html",
        )

    @app.get("/<path:filename>")
    def frontend_file(filename):
        if filename.startswith("api/"):
            abort(404)

        return send_from_directory(
            str(FRONTEND_DIST),
            filename,
        )

    return app