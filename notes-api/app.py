from flask import Flask
from routes.notes import notes_bp, notes_store as bp_store

def create_app():
    app = Flask(__name__)

    # Register blueprint
    app.register_blueprint(notes_bp)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
