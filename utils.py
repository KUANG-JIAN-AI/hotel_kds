from functools import wraps
import json, os
from flask import session, redirect, url_for, request, jsonify

STATUS_FILE = "task_status.json"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果用户未登录
        if "user_id" not in session:
            # 如果是 API 请求（比如 AJAX），返回 JSON 错误
            if (
                request.is_json
                or request.headers.get("X-Requested-With") == "XMLHttpRequest"
            ):
                return jsonify({"code": 401, "msg": "未登录或登录已过期"}), 401
            # 否则重定向到登录页面
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def save_status(enabled: bool):
    """保存状态到 JSON 文件"""
    with open(STATUS_FILE, "w") as f:
        json.dump({"is_decay_enabled": enabled}, f)


def load_status() -> bool:
    """读取状态，没有文件则默认 True"""
    if not os.path.exists(STATUS_FILE):
        return True
    with open(STATUS_FILE, "r") as f:
        return json.load(f).get("is_decay_enabled", True)
