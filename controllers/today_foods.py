from datetime import date, datetime, timedelta
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
        .options(joinedload(TodayFoods.food))  # ✅ Foods を一括ロード
        .order_by(TodayFoods.id.desc())
        .all()
    )

    data = [f.to_dict() for f in foods]

    # 🔢 件数集計
    total = len(data)
    warning = sum(1 for f in data if f["remain"] == 1)
    critical = sum(1 for f in data if f["remain"] == 2)
    empty = sum(1 for f in data if f["remain"] == 3)

    # ✅ 定期タスク状態（True = 実行中, False = 停止中）
    decay_status = "running" if load_status() else "paused"

    return (
        jsonify(
            {
                "code": 200,
                "msg": "取得に成功しました",
                "data": data,
                "stats": {
                    "total": total,
                    "warning": warning,
                    "critical": critical,
                    "empty": empty,
                },
                "decay_status": decay_status,  # 👈 追加項目
            }
        ),
        200,
    )


def add_today_food():
    data = request.get_json(silent=True) or {}

    food_id = data.get("food_id", 0)

    if not food_id:
        return jsonify({"code": 400, "msg": "食品IDが存在しません"}), 400

    food = Foods.query.filter_by(id=food_id).first()
    if not food:
        return jsonify({"code": 400, "msg": "食品が存在しません"}), 400

    today_food = TodayFoods.query.filter_by(
        food_id=food_id, record_date=date.today()
    ).first()

    try:
        # Foods から TodayFoods に必要な項目をコピー
        if today_food:
            # ✅ 既に存在する場合：status を 1 に更新
            today_food.status = 1
            db.session.commit()
            msg = "既存の食品を再有効化しました"
        else:
            # ✅ 存在しない場合：新規追加
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
            msg = "食品を追加しました"

        return (
            jsonify({"code": 200, "msg": msg, "data": today_food.to_dict()}),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"データベースエラー：{str(e)}"}), 500


def del_today_food():
    data = request.get_json(silent=True) or {}

    food_id = data.get("food_id", 0)

    if not food_id:
        return jsonify({"code": 400, "msg": "食品IDが存在しません"}), 400

    food = Foods.query.filter_by(id=food_id).first()
    if not food:
        return jsonify({"code": 400, "msg": "食品が存在しません"}), 400

    today_food = TodayFoods.query.filter_by(
        food_id=food_id, record_date=date.today()
    ).first()

    if not today_food:
        return jsonify({"code": 400, "msg": "本日の食品データが存在しません"}), 400

    try:
        today_food.status = 2
        db.session.commit()
        return (
            jsonify({"code": 200, "msg": "下架に成功しました", "data": today_food.to_dict()}),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"データベースエラー：{str(e)}"}), 500


def append_food():
    data = request.get_json(silent=True) or {}

    today_id = data.get("today_id", 0)

    if not today_id:
        return jsonify({"code": 400, "msg": "本日の食品IDが存在しません"}), 400

    today_food = TodayFoods.query.filter_by(id=today_id).first()

    if not today_food or not today_food.food:
        return jsonify({"code": 400, "msg": "本日の食品データが存在しません"}), 400

    try:
        # Foods テーブルから初期重量を取得
        add_weight = today_food.food.weight or 0

        if add_weight <= 0:
            return jsonify(
                {"code": 400, "msg": "初期重量が設定されていないため、追加できません"}
            ), 400

        # 本日の食品重量を更新
        today_food.total_weight += add_weight
        today_food.current_weight += add_weight

        db.session.commit()
        return (
            jsonify({"code": 200, "msg": "上架に成功しました", "data": today_food.to_dict()}),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"データベースエラー：{str(e)}"}), 500


def stats():
    """直近30日間の食品重量統計を取得"""
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


def get_days():
    # 現在のページ番号を取得（デフォルト：1）
    page = request.args.get("page", 1, type=int)
    per_page = 10  # 1ページあたりの表示件数

    # POST 検索の場合
    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
    else:
        keyword = request.args.get("keyword", "").strip()

    date_str = (
        request.form.get("date", "").strip()
        if request.method == "POST"
        else request.args.get("date", "").strip()
    )

    query = TodayFoods.active().join(TodayFoods.food)

    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            query = query.filter(TodayFoods.record_date == target_date)
        except ValueError:
            pass  # 無効な日付形式は無視

    # 検索条件の構築
    if keyword:
        query = query.filter(Foods.name.like(f"%{keyword}%"))

    # ページネーション
    pagination = (
        query.order_by(TodayFoods.id.desc())
        .options(joinedload(TodayFoods.food))  # ✅ Foods を一括ロード
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    foods = pagination.items
    return foods, pagination, request, keyword, date_str
