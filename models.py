import datetime
from pathlib import Path

from flask_login import UserMixin
from peewee import (
    CharField,
    DateTimeField,
    ForeignKeyField,
    Model,
    SqliteDatabase,
    TextField,
)

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

db = SqliteDatabase(INSTANCE_DIR / "app.db", pragmas={"foreign_keys": 1})


class BaseModel(Model):
    class Meta:
        database = db


class User(UserMixin, BaseModel):
    username = CharField(max_length=30, unique=True, collation="NOCASE")
    email = CharField(max_length=254, unique=True, collation="NOCASE")
    password_hash = TextField()

    class Meta:
        table_name = "users"


class Post(BaseModel):
    user = ForeignKeyField(User, backref="posts", on_delete="RESTRICT")
    image_filename = CharField(max_length=255, unique=True)
    caption = TextField(default="")
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = "posts"


def init_db():
    db.connect(reuse_if_open=True)
    db.create_tables([User, Post])
    db.close()
