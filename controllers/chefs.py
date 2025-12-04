from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from models import db, Chefs


def list():
    chefs = Chefs.query.order_by(Chefs.id.desc()).all()
    return [c.to_dict() for c in chefs]


def create():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    nickname = data.get("nickname", "").strip()
    status = data.get("status", 1)
    advice = data.get("advice", "").strip()

    if not username:
        return jsonify({"code": 400, "msg": "用户名不能为空"})
    if not password:
        return jsonify({"code": 400, "msg": "密码不能为空"})

    # 检查是否已存在
    if Chefs.query.filter_by(username=username).first():
        return jsonify({"code": 400, "msg": "用户名已存在"})

    try:
        chef = Chefs(username=username, nickname=nickname, status=status, advice=advice)
        chef.set_password(password)
        db.session.add(chef)
        db.session.commit()
        return jsonify({"code": 200, "msg": "success", "data": chef.to_dict()})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"数据库错误：{str(e)}"})
