from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Flask, redirect, render_template, request, session
from apscheduler.schedulers.background import BackgroundScheduler
from controllers.chefs import add_chef, login_act
from controllers.foods import add_food
from controllers.today_foods import add_today_food, get_today_foods
from models import Foods, TodayFoods, db, Chefs
from utils import login_required


app = Flask(__name__)

app.permanent_session_lifetime = timedelta(hours=6)  # 登录有效期6小时


# --- DATABASE ---
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/hotel_kds"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "ai_f_group"

# --- 初始化数据库 ---
db.init_app(app)

scheduler = BackgroundScheduler(timezone="Asia/Tokyo")


# 🕒 定时任务逻辑
def decay_today_foods():
    with app.app_context():
        today = date.today()
        now = datetime.now(ZoneInfo("Asia/Tokyo"))

        today_foods = (
            TodayFoods.query.filter_by(record_date=today)
            .join(Foods, TodayFoods.food_id == Foods.id)
            .all()
        )

        changed = False
        for tf in today_foods:
            if not tf.food:
                continue
            decay = tf.food.decay_rate or 0
            if decay <= 0:
                continue

            # 🧮 计算衰减
            if tf.current_weight > 0:
                tf.current_weight = max(tf.current_weight - decay, 0)
                changed = True

            # 🚨 状态更新
            if tf.current_weight <= 0:
                tf.remain = 3  # 卖完
            elif tf.current_weight <= (tf.food.critical_threshold or 20):
                tf.remain = 2  # 危险
            elif tf.current_weight <= (tf.food.warning_threshold or 40):
                tf.remain = 1  # 警告
            else:
                tf.remain = 0  # 正常

            tf.updated_at = now

        if changed:
            db.session.commit()
            # print(f"[{now:%H:%M:%S}] 更新今日菜品衰减信息")


# ⏰ 启动定时任务：每 5 秒执行一次
scheduler.add_job(func=decay_today_foods, trigger="interval", seconds=5)
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
    chefs = Chefs.query.order_by(Chefs.id.desc()).all()
    return render_template("chefs.html", chefs=chefs, request=request)


@app.route("/chef", methods=["POST"])
@login_required
def create_chef():
    return add_chef()


@app.route("/foods", methods=["GET"])
@login_required
def foods():
    today = date.today()

    # 1️⃣ 查出所有菜品
    foods = Foods.query.order_by(Foods.id.desc()).all()

    # 2️⃣ 查出今天的菜品 id 集合
    today_food_ids = {
        tf.food_id for tf in TodayFoods.query.filter_by(record_date=today).all()
    }

    # 3️⃣ 遍历打标
    for food in foods:
        food.is_today = food.id in today_food_ids
    return render_template("foods.html", foods=foods, request=request)


@app.route("/food", methods=["POST"])
@login_required
def create_food():
    return add_food()


@app.route("/add_today", methods=["POST"])
@login_required
def add_today():
    return add_today_food()


@app.route("/today_foods", methods=["GET"])
@login_required
def today_foods():
    return get_today_foods()


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


if __name__ == "__main__":
    app.run(debug=True, port=9000)
