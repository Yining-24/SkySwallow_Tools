from datetime import timedelta
from pathlib import Path

from flask import Flask, abort, send_from_directory

from .api import api_bp
from .auth import auth_bp


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


def create_app():
    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    app.config.from_pyfile("config.py")

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
        raise RuntimeError("instance/config.py 缺少 SECRET_KEY。")

    if missing_roles:
        missing = ", ".join(sorted(missing_roles))
        raise RuntimeError(
            f"instance/config.py 缺少角色口令：{missing}"
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