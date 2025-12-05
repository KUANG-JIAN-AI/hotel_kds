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

    # 必填项校验
    required_fields = [
        "name",
        "category",
        "weight",
        "decay_rate",
        "warning_threshold",
        "critical_threshold",
    ]
    missing = [f for f in required_fields if not str(data.get(f, "")).strip()]
    if missing:
        return jsonify({"code": 400, "msg": f"缺少必填项：{', '.join(missing)}"}), 400

        # 检查是否已存在
    if Foods.query.filter_by(name=name).first():
        return jsonify({"code": 409, "msg": "菜品已存在"}), 409

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
