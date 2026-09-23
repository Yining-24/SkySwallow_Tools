from flask import Flask, render_template
from .api import api_bp


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
    app.register_blueprint(api_bp)

    @app.get("/")
    def home():
        return render_template("index.html")

    return app
