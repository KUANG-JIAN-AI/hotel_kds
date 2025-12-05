from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from models import Foods, db


def add_food():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    category = data.get("category", "").strip()
    weight = data.get("weight", 0)
    decay_rate = data.get("decay_rate", 0)
    warning_threshold = data.get("warning_threshold", 0)
    critical_threshold = data.get("critical_threshold", 0)
    status = data.get("status", 1)

    if (
        not name
        or not category
        or not weight
        or not decay_rate
        or not warning_threshold
        or not critical_threshold
    ):
        return jsonify({"code": 400, "msg": "必填项不能为空"}), 400

    try:
        food = Foods(
            name=name,
            category=category,
            weight=weight,
            decay_rate=decay_rate,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            status=status,
        )
        db.session.add(food)
        db.session.commit()
        return jsonify({"code": 200, "msg": "success", "data": food.to_dict()}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"数据库错误：{str(e)}"}), 500
