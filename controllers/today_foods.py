from datetime import date
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from models import Foods, TodayFoods, db


def get_today_foods():
    today = date.today()
    foods = (
        TodayFoods.query.filter_by(record_date=today)
        .join(Foods, TodayFoods.food_id == Foods.id)
        .order_by(TodayFoods.id.desc())
        .all()
    )

    data = [f.to_dict() for f in foods]
    # 🔢 统计数量
    total = len(data)
    warning = sum(1 for f in data if f["remain"] == 1)
    critical = sum(1 for f in data if f["remain"] == 2)
    empty = sum(1 for f in data if f["remain"] == 3)

    return (
        jsonify(
            {
                "code": 200,
                "msg": "success",
                "data": data,
                "stats": {
                    "total": total,
                    "warning": warning,
                    "critical": critical,
                    "empty": empty,
                },
            }
        ),
        200,
    )


def add_today_food():
    data = request.get_json(silent=True) or {}

    food_id = data.get("food_id", 0)

    if not food_id:
        return jsonify({"code": 400, "msg": "食品ID不存在"}), 400

    food = Foods.query.filter_by(id=food_id).first()
    if not food:
        return jsonify({"code": 400, "msg": "食品不存在"}), 400

    try:
        # 从 Foods 复制必要字段到 TodayFoods
        today_food = TodayFoods(
            food_id=food.id,
            total_weight=food.weight,
            current_weight=food.weight,
            record_date=date.today(),
            status=1,
            remain=0,
        )
        db.session.add(today_food)
        db.session.commit()
        return (
            jsonify({"code": 200, "msg": "success", "data": today_food.to_dict()}),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"数据库错误：{str(e)}"}), 500
