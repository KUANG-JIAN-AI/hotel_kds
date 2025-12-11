from datetime import datetime
from zoneinfo import ZoneInfo
from flask import jsonify, request, session
from sqlalchemy.exc import SQLAlchemyError

from models import db, Chefs


def login_act():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    # 参数校验
    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名和密码不能为空"}), 400

    chef = Chefs.active().filter_by(username=username).first()

    # 统一模糊错误信息，避免账号枚举
    if not chef or not chef.check_password(password):
        return jsonify({"code": 401, "msg": "用户名或密码错误"}), 401

    if chef.status == 2:
        return jsonify({"code": 402, "msg": "用户已离职"}), 401

    # ✅ 写入 session
    session.permanent = True
    session["user_id"] = chef.id
    session["username"] = chef.username
    session["nickname"] = chef.nickname

    return jsonify({"code": 200, "msg": "success", "data": chef.to_dict()}), 200


def add_chef():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    nickname = data.get("nickname", "").strip()
    status = data.get("status", 1)
    advice = data.get("advice", "").strip()

    if not username:
        return jsonify({"code": 400, "msg": "用户名不能为空"}), 400
    if not password:
        return jsonify({"code": 400, "msg": "密码不能为空"}), 400

    # 检查是否已存在
    if Chefs.query.filter_by(username=username).first():
        return jsonify({"code": 409, "msg": "用户名已存在"}), 409

    try:
        chef = Chefs(username=username, nickname=nickname, status=status, advice=advice)
        chef.set_password(password)
        db.session.add(chef)
        db.session.commit()
        return jsonify({"code": 200, "msg": "success", "data": chef.to_dict()}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"数据库错误：{str(e)}"}), 500


def update_chef():
    data = request.get_json()
    nickname = data.get("nickname", "").strip()
    password = data.get("password", "").strip()  # 当前密码
    new_password = data.get("new_password", "").strip()  # 新密码

    chef_id = session.get("user_id")
    if not chef_id:
        return jsonify({"code": 401, "msg": "未登录"}), 401

    chef = Chefs.query.get(chef_id)
    if not chef:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404

    # ✅ 情况 1：只修改昵称
    if nickname and not password and not new_password:
        chef.nickname = nickname
        db.session.commit()

        # 更新 session
        session["nickname"] = chef.nickname
        return jsonify({"code": 200, "msg": "昵称已更新", "data": chef.to_dict()}), 200

    # ✅ 情况 2：修改密码（必须输入当前密码 + 新密码）
    elif password and new_password:
        # 验证当前密码是否正确
        if not chef.check_password(password):
            return jsonify({"code": 400, "msg": "当前密码错误"}), 400

        chef.set_password(new_password)
        db.session.commit()

        # 清除 session 并要求重新登录
        session.clear()
        return (
            jsonify(
                {"code": 200, "msg": "密码已更新，请重新登录", "redirect": "/login"}
            ),
            200,
        )

    # 🚫 情况 3：输入不完整
    else:
        return jsonify({"code": 400, "msg": "请输入完整的信息"}), 400


def delete_chef():
    data = request.get_json()

    chef_id = data.get("chef_id", 0)
    if not chef_id:
        return jsonify({"code": 401, "msg": "用户ID不存在"}), 401

    chef = Chefs.query.get(chef_id)
    if not chef:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404

    chef.deleted_at = datetime.now(ZoneInfo("Asia/Tokyo"))
    db.session.commit()

    chef_id = int(data.get("chef_id", 0))
    session_user_id = int(session.get("user_id") or 0)

    if session_user_id == chef_id:
        # 清除 session 并要求重新登录
        session.clear()
        return (
            jsonify(
                {"code": 200, "msg": "密码已更新，请重新登录", "redirect": "/login"}
            ),
            200,
        )

    return jsonify({"code": 200, "msg": "success"}), 200
