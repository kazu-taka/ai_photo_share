from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import PasswordField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp


def strip_value(value):
    if isinstance(value, str):
        return value.strip()
    return value


class RegisterForm(FlaskForm):
    username = StringField(
        "ユーザー名",
        filters=[strip_value],
        validators=[
            DataRequired(message="ユーザー名を入力してください"),
            Regexp(
                r"^[A-Za-z0-9_]{3,30}$",
                message="ユーザー名は英数字とアンダースコア3〜30文字にしてください",
            ),
        ],
    )
    email = StringField(
        "メールアドレス",
        filters=[strip_value],
        validators=[
            DataRequired(message="メールアドレスを入力してください"),
            Length(max=254, message="メールアドレスは254文字以下にしてください"),
            Email(message="メールアドレスの形式が正しくありません"),
        ],
    )
    password = PasswordField(
        "パスワード",
        validators=[
            DataRequired(message="パスワードを入力してください"),
            Length(
                min=8,
                max=128,
                message="パスワードは8文字以上128文字以下にしてください",
            ),
        ],
    )


class PostForm(FlaskForm):
    image = FileField(
        "写真",
        validators=[
            FileRequired(message="写真を選んでください"),
            FileAllowed(
                ["png", "jpg", "jpeg", "gif"],
                message="png、jpg、jpeg、gif の画像を選んでください",
            ),
        ],
    )
    caption = TextAreaField(
        "キャプション",
        filters=[strip_value],
        validators=[
            Optional(),
            Length(max=200, message="キャプションは200文字以下にしてください"),
        ],
    )


class LoginForm(FlaskForm):
    username = StringField(
        "ユーザー名",
        filters=[strip_value],
        validators=[DataRequired(message="ユーザー名を入力してください")],
    )
    password = PasswordField(
        "パスワード",
        validators=[DataRequired(message="パスワードを入力してください")],
    )
