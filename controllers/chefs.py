from datetime import datetime
from zoneinfo import ZoneInfo
from flask import jsonify, request, session
from sqlalchemy.exc import SQLAlchemyError

from models import db, Chefs


def login_act():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    # パラメータチェック
    if not username or not password:
        return jsonify({"code": 400, "msg": "ユーザー名とパスワードは必須です"}), 400

    chef = Chefs.active().filter_by(username=username).first()

    # エラーメッセージを統一（アカウント列挙防止）
    if not chef or not chef.check_password(password):
        return jsonify({"code": 401, "msg": "ユーザー名またはパスワードが正しくありません"}), 401

    if chef.status == 2:
        return jsonify({"code": 402, "msg": "このユーザーは退職済みです"}), 401

    # ✅ session に保存
    session.permanent = True
    session["user_id"] = chef.id
    session["username"] = chef.username
    session["nickname"] = chef.nickname

    return jsonify({"code": 200, "msg": "ログイン成功", "data": chef.to_dict()}), 200


def add_chef():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    nickname = data.get("nickname", "").strip()
    status = data.get("status", 1)
    advice = data.get("advice", "").strip()

    if not username:
        return jsonify({"code": 400, "msg": "ユーザー名を入力してください"}), 400
    if not password:
        return jsonify({"code": 400, "msg": "パスワードを入力してください"}), 400

    # 既存ユーザー確認
    if Chefs.query.filter_by(username=username).first():
        return jsonify({"code": 409, "msg": "このユーザー名は既に存在します"}), 409

    try:
        chef = Chefs(username=username, nickname=nickname, status=status, advice=advice)
        chef.set_password(password)
        db.session.add(chef)
        db.session.commit()
        return jsonify({"code": 200, "msg": "追加に成功しました", "data": chef.to_dict()}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"データベースエラー：{str(e)}"}), 500


def update_chef():
    data = request.get_json()
    nickname = data.get("nickname", "").strip()
    password = data.get("password", "").strip()       # 現在のパスワード
    new_password = data.get("new_password", "").strip()  # 新しいパスワード

    chef_id = session.get("user_id")
    if not chef_id:
        return jsonify({"code": 401, "msg": "ログインしてください"}), 401

    chef = Chefs.query.get(chef_id)
    if not chef:
        return jsonify({"code": 404, "msg": "ユーザーが存在しません"}), 404

    # ✅ ケース1：ニックネームのみ変更
    if nickname and not password and not new_password:
        chef.nickname = nickname
        db.session.commit()

        # session 更新
        session["nickname"] = chef.nickname
        return jsonify({"code": 200, "msg": "ニックネームを更新しました", "data": chef.to_dict()}), 200

    # ✅ ケース2：パスワード変更（現在のパスワード＋新しいパスワード）
    elif password and new_password:
        if not chef.check_password(password):
            return jsonify({"code": 400, "msg": "現在のパスワードが正しくありません"}), 400

        chef.set_password(new_password)
        db.session.commit()

        # session をクリアして再ログイン
        session.clear()
        return (
            jsonify(
                {"code": 200, "msg": "パスワードを更新しました。再度ログインしてください", "redirect": "/login"}
            ),
            200,
        )

    # 🚫 入力不完全
    else:
        return jsonify({"code": 400, "msg": "必要な情報をすべて入力してください"}), 400


def delete_chef():
    data = request.get_json()

    chef_id = data.get("chef_id", 0)
    if not chef_id:
        return jsonify({"code": 401, "msg": "ユーザーIDが存在しません"}), 401

    chef = Chefs.query.get(chef_id)
    if not chef:
        return jsonify({"code": 404, "msg": "ユーザーが存在しません"}), 404

    chef.deleted_at = datetime.now(ZoneInfo("Asia/Tokyo"))
    db.session.commit()

    chef_id = int(data.get("chef_id", 0))
    session_user_id = int(session.get("user_id") or 0)

    if session_user_id == chef_id:
        # 自分自身を削除 → 再ログイン
        session.clear()
        return (
            jsonify(
                {"code": 200, "msg": "アカウントを削除しました。再度ログインしてください", "redirect": "/login"}
            ),
            200,
        )

    return jsonify({"code": 200, "msg": "削除に成功しました"}), 200
