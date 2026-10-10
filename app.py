import os
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

from cachelib.file import FileSystemCache
from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from peewee import IntegrityError
from PIL import Image, UnidentifiedImageError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from forms import LoginForm, PostForm, RegisterForm
from models import INSTANCE_DIR, Post, User, db, init_db

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads" / "posts"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
IMAGE_FORMATS = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", "gif": "GIF"}
STORED_NAME = re.compile(r"^[0-9a-f]{32}\.(png|jpg|jpeg|gif)$")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY が設定されていません。.env に書いてください。")

session_dir = INSTANCE_DIR / "sessions"
session_dir.mkdir(parents=True, exist_ok=True)
app.config["SESSION_TYPE"] = "cachelib"
app.config["SESSION_CACHELIB"] = FileSystemCache(cache_dir=str(session_dir))
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_BYTES
Session(app)
CSRFProtect(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = None


@login_manager.user_loader
def load_user(user_id):
    return User.get_or_none(User.id == int(user_id))


@app.before_request
def open_db():
    if db.is_closed():
        db.connect()


login_manager.init_app(app)


@app.teardown_request
def close_db(error):
    if not db.is_closed():
        db.close()


@app.route("/")
def index():
    posts = Post.select(Post, User).join(User).order_by(Post.created_at.desc())
    return render_template("posts/index.html", posts=posts)


@app.route("/posts/new", methods=["GET", "POST"])
@login_required
def post_new():
    form = PostForm()
    if form.validate_on_submit():
        saved_name = _save_post_image(form)
        if saved_name is not None:
            return redirect(url_for("index"))
    return render_template("posts/new.html", form=form)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    safe_name = secure_filename(filename)
    if safe_name != filename or not STORED_NAME.fullmatch(safe_name):
        abort(404)
    return send_from_directory(UPLOAD_DIR, safe_name)


@app.errorhandler(RequestEntityTooLarge)
def image_too_large(error):
    if request.path != "/posts/new":
        abort(413)
    form = PostForm()
    form.image.errors.append("写真は5MB以下にしてください")
    return render_template("posts/new.html", form=form), 413


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegisterForm()
    if form.validate_on_submit() and not _username_or_email_taken(form):
        try:
            User.create(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
            )
        except IntegrityError:
            form.username.errors.append(
                "このユーザー名またはメールアドレスは使われています"
            )
        else:
            return redirect(url_for("login"))

    return render_template("auth/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    login_error = None
    if form.validate_on_submit():
        user = User.get_or_none(User.username == form.username.data)
        password_matches = user is not None and check_password_hash(
            user.password_hash, form.password.data
        )
        if password_matches:
            login_user(user)
            if _next_is_new_post():
                return redirect(url_for("post_new"))
            return redirect(url_for("index"))
        login_error = "ログインできません"

    return render_template("auth/login.html", form=form, login_error=login_error)


@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("index"))


def _next_is_new_post():
    raw = request.args.get("next") or ""
    parsed = urlparse(raw)
    if parsed.scheme or parsed.netloc:
        if parsed.netloc != request.host:
            return False
        path = parsed.path
    else:
        path = raw
    return path == "/posts/new"


def _save_post_image(form):
    upload = form.image.data
    extension = Path(upload.filename or "").suffix.lower().lstrip(".")
    if extension not in ALLOWED_EXTENSIONS or not _is_allowed_image(upload, extension):
        form.image.errors.append("png、jpg、jpeg、gif の画像を選んでください")
        return None

    filename = secure_filename(f"{uuid.uuid4().hex}.{extension}")
    path = UPLOAD_DIR / filename
    upload.save(path)
    try:
        Post.create(
            user=current_user.id,
            image_filename=filename,
            caption=form.caption.data or "",
        )
    except IntegrityError:
        path.unlink(missing_ok=True)
        form.image.errors.append("投稿を保存できませんでした。もう一度選んでください")
        return None
    return filename


def _is_allowed_image(upload, extension):
    try:
        upload.stream.seek(0)
        with Image.open(upload.stream) as image:
            image_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError):
        return False
    finally:
        upload.stream.seek(0)
    return image_format == IMAGE_FORMATS[extension]


def _username_or_email_taken(form):
    taken = False
    if User.select().where(User.username == form.username.data).exists():
        form.username.errors.append("このユーザー名は使われています")
        taken = True
    if User.select().where(User.email == form.email.data).exists():
        form.email.errors.append("このメールアドレスは使われています")
        taken = True
    return taken


init_db()


if __name__ == "__main__":
    app.run(port=8000)
