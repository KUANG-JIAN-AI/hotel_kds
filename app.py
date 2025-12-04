from flask import Flask, jsonify, render_template
from controllers.chefs import create, list
from models import db, Chefs


app = Flask(__name__)

# --- DATABASE ---
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/hotel_kds"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "ai_f_group"

# --- 初始化数据库 ---
db.init_app(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/form")
def form():
    return render_template("form.html")


@app.route("/head_chef")
def head_chef():
    chefs = Chefs.query.order_by(Chefs.id.desc()).all()
    return render_template("head_chef.html", chefs=chefs)


@app.route("/head_chef", methods=["POST"])
def create_chef():
    return create()


@app.route("/head_chefs", methods=["GET"])
def list_chef():
    return list()


@app.route("/login")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True, port=9000)
