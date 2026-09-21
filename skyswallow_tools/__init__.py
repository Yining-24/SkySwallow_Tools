from flask import Flask, render_template


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def home():
        return render_template("index.html")

    return app