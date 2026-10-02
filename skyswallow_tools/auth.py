from functools import wraps
from math import ceil
from threading import Lock
from time import monotonic

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

LOGIN_ATTEMPT_LIMIT = 5
LOGIN_WINDOW_SECONDS = 60
LOGIN_CLIENT_LIMIT = 1024


@auth_bp.record_once
def initialize_login_limits(state):
    state.app.extensions["skyswallow_login_limits"] = {"lock": Lock(), "clients": {}}


def reserve_login_attempt():
    state = current_app.extensions["skyswallow_login_limits"]
    now = monotonic()
    client = request.remote_addr or "unknown"
    with state["lock"]:
        clients = state["clients"]
        for address, (_, expires) in list(clients.items()):
            if expires <= now:
                del clients[address]
        attempts, expires = clients.get(client, (0, now + LOGIN_WINDOW_SECONDS))
        if attempts >= LOGIN_ATTEMPT_LIMIT:
            return max(1, ceil(expires - now))
        if client not in clients and len(clients) >= LOGIN_CLIENT_LIMIT:
            return LOGIN_WINDOW_SECONDS
        clients[client] = (attempts + 1, expires)
    return 0


def clear_login_attempts():
    state = current_app.extensions["skyswallow_login_limits"]
    with state["lock"]:
        state["clients"].pop(request.remote_addr or "unknown", None)


def role_information(role):
    return {
        "role": role,
        "role_label": ROLE_LABELS[role],
        "permissions": sorted(ROLE_PERMISSIONS[role]),
    }


@auth_bp.post("/login")
def login():
    retry_after = reserve_login_attempt()
    if retry_after:
        response = jsonify(error=f"登录尝试过多，请 {retry_after} 秒后重试。")
        response.status_code = 429
        response.headers["Retry-After"] = str(retry_after)
        return response

    data = request.get_json(silent=True) or {}

    if not isinstance(data, dict):
        return jsonify(error="角色或口令错误。"), 401

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

    clear_login_attempts()
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
