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
