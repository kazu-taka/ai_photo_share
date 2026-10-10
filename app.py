from flask import Flask, render_template

from models import init_db

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("posts/index.html")


init_db()


if __name__ == "__main__":
    app.run(port=8000)
