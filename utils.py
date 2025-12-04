from functools import wraps
from flask import session, redirect, url_for, request, jsonify


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
