from datetime import date, datetime
from zoneinfo import ZoneInfo
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from models import Foods, TodayFoods, db


def add_food():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    category = data.get("category", "").strip()
    weight = data.get("weight", 0)
    decay_rate = data.get("decay_rate", 0)
    warning_threshold = data.get("warning_threshold", 0)
    critical_threshold = data.get("critical_threshold", 0)
    status = data.get("status", 1)

    # 必須項目チェック
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
        return jsonify(
            {"code": 400, "msg": f"必須項目が不足しています：{', '.join(missing)}"}
        ), 400

    # 既存データチェック
    if Foods.query.filter_by(name=name).first():
        return jsonify({"code": 409, "msg": "この食品は既に登録されています"}), 409

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
        return jsonify({"code": 200, "msg": "追加に成功しました", "data": food.to_dict()}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"データベースエラー：{str(e)}"}), 500


def delete_food():
    data = request.get_json()

    food_id = data.get("food_id", 0)
    if not food_id:
        return jsonify({"code": 401, "msg": "食品IDが存在しません"}), 401

    food = Foods.query.get(food_id)
    if not food:
        return jsonify({"code": 404, "msg": "食品が存在しません"}), 404

    food.deleted_at = datetime.now(ZoneInfo("Asia/Tokyo"))

    today_food = TodayFoods.query.filter_by(
        food_id=food_id, record_date=date.today()
    ).first()

    if today_food:
        today_food.status = 2

    db.session.commit()

    return jsonify({"code": 200, "msg": "削除に成功しました"}), 200
