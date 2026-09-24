from functools import wraps

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.security import check_password_hash


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
)


ROLE_LABELS = {
    "admin": "管理员",
    "finance": "财务",
    "followup": "跟单员",
}


ROLE_PERMISSIONS = {
    "admin": {"profit", "summary"},
    "finance": {"profit", "summary"},
    "followup": set(),
}


def role_information(role):
    return {
        "role": role,
        "role_label": ROLE_LABELS[role],
        "permissions": sorted(ROLE_PERMISSIONS[role]),
    }


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    role = data.get("role")
    password = data.get("password")

    if role not in ROLE_LABELS or not isinstance(password, str):
        return jsonify(error="角色或口令错误。"), 401

    password_hashes = current_app.config["PASSWORD_HASHES"]
    stored_hash = password_hashes.get(role)

    if not stored_hash or not check_password_hash(
        stored_hash,
        password,
    ):
        return jsonify(error="角色或口令错误。"), 401

    session.clear()
    session.permanent = True
    session["role"] = role

    return jsonify(
        authenticated=True,
        **role_information(role),
    )


@auth_bp.get("/session")
def session_status():
    role = session.get("role")

    if role not in ROLE_LABELS:
        return jsonify(authenticated=False)

    return jsonify(
        authenticated=True,
        **role_information(role),
    )


@auth_bp.post("/logout")
def logout():
    session.clear()

    return jsonify(authenticated=False)


def permission_required(permission):
    def decorator(view_function):
        @wraps(view_function)
        def protected_view(*args, **kwargs):
            role = session.get("role")

            if role not in ROLE_LABELS:
                return jsonify(error="请先登录。"), 401

            if permission not in ROLE_PERMISSIONS[role]:
                return jsonify(error="当前角色没有此功能的权限。"), 403

            return view_function(*args, **kwargs)

        return protected_view

    return decorator