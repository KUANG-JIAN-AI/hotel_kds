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

    chef = Chefs.query.filter_by(username=username).first()

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
