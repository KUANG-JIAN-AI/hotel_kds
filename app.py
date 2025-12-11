import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, redirect, render_template, request, session
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv
from controllers.chefs import add_chef, delete_chef, login_act, update_chef
from controllers.foods import add_food, delete_food
from controllers.today_foods import (
    add_today_food,
    append_food,
    del_today_food,
    get_today_foods,
    stats,
)
from models import Foods, TodayFoods, db, Chefs
from utils import login_required

load_dotenv()  # ✅ 自动加载 .env 文件中的环境变量


app = Flask(__name__)

app.permanent_session_lifetime = timedelta(hours=6)  # 登录有效期6小时


# --- DATABASE ---
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# --- 初始化数据库 ---
db.init_app(app)

is_decay_enabled = True


# -----------------------
# 衰减逻辑
# -----------------------
def decay_today_foods():
    global is_decay_enabled
    if not is_decay_enabled:
        # 如果暂停标志为 False，直接跳过执行
        return

    with app.app_context():
        today = date.today()
        now = datetime.now(ZoneInfo("Asia/Tokyo"))
        today_foods = (
            TodayFoods.query.filter_by(record_date=today)
            .filter_by(status=1)
            .options(joinedload(TodayFoods.food))  # ✅ 一次性加载 Foods
            .all()
        )
        changed = False
        for tf in today_foods:
            f = tf.food
            if not f:
                continue
            decay = f.decay_rate or 0
            if decay <= 0:
                continue

            # 减少重量
            tf.current_weight = max(tf.current_weight - decay, 0)

            # 状态更新
            if tf.current_weight <= 0:
                tf.remain = 3  # 卖完
            elif tf.current_weight <= f.critical_threshold:
                tf.remain = 2  # 危险
            elif tf.current_weight <= f.warning_threshold:
                tf.remain = 1  # 警告
            else:
                tf.remain = 0  # 正常

            tf.updated_at = now
            changed = True

        if changed:
            db.session.commit()
            print(f"[{now:%H:%M:%S}] 更新菜品衰减信息")


# -----------------------
# APScheduler 启动
# ⏰ 启动定时任务：每 5 秒执行一次
# -----------------------
scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
scheduler.add_job(decay_today_foods, "interval", seconds=1, id="decay_task")
scheduler.start()


@app.route("/")
@login_required
def index():
    return render_template("index.html", request=request)


@app.route("/form")
def form():
    return render_template("form.html")


@app.route("/chefs", methods=["GET"])
@login_required
def chefs():
    chefs = Chefs.active().order_by(Chefs.id.desc()).all()
    return render_template("chefs.html", chefs=chefs, request=request)


@app.route("/chef", methods=["POST"])
@login_required
def create_chef():
    return add_chef()


@app.route("/chef/<int:id>", methods=["GET"])
@login_required
def get_chef(id):
    chef = Chefs.query.get(id)
    if not chef:
        return jsonify({"code": 404, "msg": "管理人が存在しません"}), 404

    return jsonify({"code": 200, "msg": "success", "data": chef.to_dict()}), 200


@app.route("/chef/<int:id>", methods=["PUT"])
@login_required
def put_chef(id):
    data = request.get_json()
    chef = Chefs.query.get(id)

    if not chef:
        return jsonify({"code": 404, "msg": "管理人が存在しません"}), 404

    # 更新字段
    chef.nickname = data.get("nickname", chef.nickname)
    chef.status = int(data.get("status", chef.status))
    chef.advice = data.get("advice", chef.advice)

    # 如果传入了新密码，就更新
    password = data.get("password", "").strip()
    if password:
        chef.set_password(password)

    db.session.commit()
    return jsonify({"code": 200, "msg": "管理人情報を更新しました"}), 200


@app.route("/set_chef", methods=["POST"])
@login_required
def set_chef():
    return update_chef()


@app.route("/del_chef", methods=["POST"])
@login_required
def del_chef():
    return delete_chef()


@app.route("/foods", methods=["GET", "POST"])
@login_required
def foods():
    today = date.today()

    # 获取当前页码（默认第1页）
    page = request.args.get("page", 1, type=int)
    per_page = 10  # 每页显示条数

    # 如果是 POST 搜索
    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
    else:
        keyword = request.args.get("keyword", "").strip()

    # 构建查询
    query = Foods.active()
    if keyword:
        query = query.filter(Foods.name.like(f"%{keyword}%"))

    # 分页查询
    pagination = query.order_by(Foods.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    foods = pagination.items

    # 1️⃣ 查出所有菜品
    # foods = Foods.query.order_by(Foods.id.desc()).all()

    # 2️⃣ 查出今天的菜品 id 集合
    today_food_ids = {
        tf.food_id
        for tf in TodayFoods.query.filter_by(status=1, record_date=today).all()
    }

    # 3️⃣ 遍历打标
    for food in foods:
        food.is_today = food.id in today_food_ids

    return render_template(
        "foods.html",
        foods=foods,
        pagination=pagination,
        request=request,
        keyword=keyword,  # ✅ 传到模板
    )


@app.route("/food", methods=["POST"])
@login_required
def create_food():
    return add_food()

@app.route("/del_food", methods=["POST"])
@login_required
def del_food():
    return delete_food()


@app.route("/add_today", methods=["POST"])
@login_required
def add_today():
    return add_today_food()


@app.route("/del_today", methods=["POST"])
@login_required
def del_today():
    return del_today_food()


@app.route("/today_foods", methods=["GET"])
@login_required
def today_foods():
    return get_today_foods()


@app.route("/append_today_food", methods=["POST"])
@login_required
def append_today_food():
    return append_food()


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def do_login():
    return login_act()


@app.route("/logout")
def logout():
    session.clear()  # 清除所有session数据
    return redirect("/login")


# 404 Not Found
@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@app.route("/totals")
def totals():
    data, food_names = stats()
    return render_template("/totals.html", data=data, foods=food_names)


@app.route("/toggle_decay", methods=["POST"])
def toggle_decay():
    """前端点击按钮时调用，暂停或恢复衰减任务"""

    print("当前任务：", scheduler.get_jobs())
    global is_decay_enabled

    job = scheduler.get_job("decay_task")
    if job.next_run_time:  # 正在运行中 → 暂停
        scheduler.pause_job("decay_task")
        is_decay_enabled = False  # 🧩 同步关闭任务执行
        status = "paused"
    else:
        scheduler.resume_job("decay_task")
        is_decay_enabled = True  # 🧩 同步开启任务执行
        status = "running"

    print(f"当前衰减状态: {status}, 启动标志: {is_decay_enabled}")
    return jsonify({"code": 200, "msg": "success", "status": status})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ✅ 建库 + 确保上下文绑定
    app.run(debug=True, port=9000, use_reloader=False)
