from datetime import date, timedelta
from flask import jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from models import Foods, TodayFoods, db
from utils import load_status


def get_today_foods():
    today = date.today()
    foods = (
        TodayFoods.query.filter_by(record_date=today)
        .filter_by(status=1)
        .options(joinedload(TodayFoods.food))  # ✅ 一次性加载 Foods
        .order_by(TodayFoods.id.desc())
        .all()
    )

    data = [f.to_dict() for f in foods]
    # 🔢 统计数量
    total = len(data)
    warning = sum(1 for f in data if f["remain"] == 1)
    critical = sum(1 for f in data if f["remain"] == 2)
    empty = sum(1 for f in data if f["remain"] == 3)

    # ✅ 定时任务状态（True = 运行中, False = 暂停中）
    decay_status = "running" if load_status() else "paused"

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
                "decay_status": decay_status,  # 👈 新增字段
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

    today_food = TodayFoods.query.filter_by(
        food_id=food_id, record_date=date.today()
    ).first()

    try:
        # 从 Foods 复制必要字段到 TodayFoods
        if today_food:
            # ✅ 已存在：只更新 status=1
            today_food.status = 1
            db.session.commit()
            msg = "菜品已存在，已重新激活"
        else:
            # ✅ 不存在：新增记录
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
            msg = "菜品已添加"

        return (
            jsonify({"code": 200, "msg": msg, "data": today_food.to_dict()}),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"数据库错误：{str(e)}"}), 500


def del_today_food():
    data = request.get_json(silent=True) or {}

    food_id = data.get("food_id", 0)

    if not food_id:
        return jsonify({"code": 400, "msg": "食品ID不存在"}), 400

    food = Foods.query.filter_by(id=food_id).first()
    if not food:
        return jsonify({"code": 400, "msg": "食品不存在"}), 400

    today_food = TodayFoods.query.filter_by(
        food_id=food_id, record_date=date.today()
    ).first()

    if not today_food:
        return jsonify({"code": 400, "msg": "今日食品不存在"}), 400

    try:
        today_food.status = 2

        db.session.commit()
        return (
            jsonify({"code": 200, "msg": "success", "data": today_food.to_dict()}),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"数据库错误：{str(e)}"}), 500


def append_food():
    data = request.get_json(silent=True) or {}

    today_id = data.get("today_id", 0)

    if not today_id:
        return jsonify({"code": 400, "msg": "今日食品ID不存在"}), 400

    today_food = TodayFoods.query.filter_by(id=today_id).first()

    if not today_food or not today_food.food:
        return jsonify({"code": 400, "msg": "今日食品不存在"}), 400

    try:
        # 从foods表取初始份量
        add_weight = today_food.food.weight or 0

        if add_weight <= 0:
            return jsonify({"code": 400, "msg": "该菜品未设置初始份量，无法累加"}), 400

        # 更新今日菜品重量
        today_food.total_weight += add_weight
        today_food.current_weight += add_weight

        db.session.commit()
        return (
            jsonify({"code": 200, "msg": "success", "data": today_food.to_dict()}),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"数据库错误：{str(e)}"}), 500


def stats():
    """获取近30天菜品重量统计"""
    today = date.today()
    start_date = today - timedelta(days=30)

    results = (
        db.session.query(
            TodayFoods.record_date,
            Foods.name,
            func.sum(TodayFoods.total_weight).label("total_weight"),
        )
        .join(Foods, TodayFoods.food_id == Foods.id)
        .filter(TodayFoods.record_date >= start_date)
        .group_by(TodayFoods.record_date, Foods.name)
        .order_by(TodayFoods.record_date)
        .all()
    )

    data = {}
    for r in results:
        date_str = r.record_date.strftime("%m-%d")
        if date_str not in data:
            data[date_str] = {}
        data[date_str][r.name] = r.total_weight

    food_names = sorted({r.name for r in results})
    return data, food_names
