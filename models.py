from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from zoneinfo import ZoneInfo

# 创建数据库对象（但不绑定 app）
db = SQLAlchemy()


class Chefs(db.Model):
    __tablename__ = "chefs"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    advice = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Integer)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")),
        onupdate=lambda: datetime.now(ZoneInfo("Asia/Tokyo")),
        nullable=False,
    )
    deleted_at = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def active():
        return Chefs.query.filter(Chefs.deleted_at.is_(None))

    def set_password(self, password: str):
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

    def status_text(self):
        """返回状态对应的文字"""
        mapping = {
            1: "正常",
            0: "停用",
            2: "离职",
        }
        return mapping.get(self.status, "未知")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "advice": self.advice,
            "status": self.status,
            "status_text": self.status_text(),  # ✅ 新增文字版
            "created_at": (
                self.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                if self.updated_at
                else None
            ),
        }

    def __repr__(self):
        return f"<Chefs {self.id}>"


class Foods(db.Model):
    __tablename__ = "foods"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.Integer)
    decay_rate = db.Column(db.Integer)
    warning_threshold = db.Column(db.Integer)
    critical_threshold = db.Column(db.Integer)
    status = db.Column(db.Integer)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")),
        onupdate=lambda: datetime.now(ZoneInfo("Asia/Tokyo")),
        nullable=False,
    )
    deleted_at = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def active():
        return Foods.query.filter(Foods.deleted_at.is_(None))

    def status_text(self):
        """返回状态对应的文字"""
        mapping = {
            1: "正常",
        }
        return mapping.get(self.status, "未知")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "weight": self.weight,
            "decay_rate": self.decay_rate,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "status": self.status,
            "status_text": self.status_text(),  # ✅ 新增文字版
            # ✅ 动态判断 is_today，如果没有设置则默认 False
            "is_today": getattr(self, "is_today", False),
            "created_at": (
                self.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                if self.updated_at
                else None
            ),
        }

    def __repr__(self):
        return f"<Foods {self.id}>"


class TodayFoods(db.Model):
    __tablename__ = "today_foods"
    id = db.Column(db.Integer, primary_key=True)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"))
    total_weight = db.Column(db.Integer)
    current_weight = db.Column(db.Integer)
    record_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Integer)
    remain = db.Column(db.Integer)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")),
        onupdate=lambda: datetime.now(ZoneInfo("Asia/Tokyo")),
        nullable=False,
    )
    deleted_at = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def active():
        return TodayFoods.query.filter(TodayFoods.deleted_at.is_(None))

    # 建立关联
    food = db.relationship("Foods", backref="today_foods")

    def status_text(self):
        """返回状态对应的文字"""
        mapping = {
            1: "上架",
        }
        return mapping.get(self.status, "未知")

    def remain_text(self):
        """返回状态对应的文字"""
        mapping = {
            0: "正常",
            1: "警告",
            2: "危险",
            3: "卖完",
        }
        return mapping.get(self.remain, "未知")

    def to_dict(self):
        return {
            "id": self.id,
            "food_id": self.food_id,
            "total_weight": self.total_weight,
            "current_weight": self.current_weight,
            "record_date": self.record_date,
            "status": self.status,
            "remain": self.remain,
            "status_text": self.status_text(),  # ✅ 新增文字版
            "remain_text": self.remain_text(),  # ✅ 新增文字版
            "record_date": (
                self.record_date.strftime("%Y-%m-%d") if self.record_date else None
            ),
            "created_at": (
                self.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                if self.updated_at
                else None
            ),
            # ✅ 仅提取 Foods 的基础信息，避免递归
            "food_info": (
                {
                    "id": self.food.id,
                    "name": self.food.name,
                    "category": self.food.category,
                    "weight": self.food.weight,
                    "decay_rate": self.food.decay_rate,
                    "warning_threshold": self.food.warning_threshold,
                    "critical_threshold": self.food.critical_threshold,
                    "status": self.food.status,
                }
                if self.food
                else None
            ),
        }

    def __repr__(self):
        return f"<TodayFoods {self.id}>"
