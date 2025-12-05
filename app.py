from datetime import timedelta
from flask import Flask, redirect, render_template, request, session
from controllers.chefs import add_chef, login_act
from controllers.foods import add_food
from models import Foods, db, Chefs
from utils import login_required


app = Flask(__name__)

app.permanent_session_lifetime = timedelta(hours=6)  # 登录有效期6小时


# --- DATABASE ---
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/hotel_kds"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "ai_f_group"

# --- 初始化数据库 ---
db.init_app(app)


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


@app.route("/foods", methods=["GET"])
@login_required
def foods():
    foods = Foods.query.order_by(Foods.id.desc()).all()
    return render_template("foods.html", foods=foods, request=request)

@app.route("/food", methods=["POST"])
@login_required
def create_food():
    return add_food()


@app.route("/chef", methods=["POST"])
@login_required
def create_chef():
    return add_chef()


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
