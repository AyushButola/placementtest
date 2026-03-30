from flask import Flask
from flask_cors import CORS
from database import db
from routes.notes import notes_bp


def create_app():
    app = Flask(__name__)

    # SQLite config — creates notes.db in the project root
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app)
    db.init_app(app)

    app.register_blueprint(notes_bp)

    # Create tables on first run if they don't exist
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
