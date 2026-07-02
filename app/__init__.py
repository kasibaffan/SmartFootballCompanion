from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template
from sqlalchemy.exc import OperationalError

from .config import Config
from .extensions import csrf, db, login_manager, migrate

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app():
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    csrf.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth import auth_bp
    from .main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Self-healing: create any missing tables on startup. This is a no-op
    # if the schema already matches, but guards against the dev SQLite file
    # losing its tables between runs (seen on this machine even outside
    # OneDrive - likely antivirus/backup software touching the file).
    with app.app_context():
        db.create_all()

    @app.errorhandler(OperationalError)
    def handle_missing_schema(error):
        # The underlying SQLite file has been observed losing its tables
        # mid-session on this machine (external to the app). Recreate the
        # schema on the spot instead of surfacing a raw 500 to the user.
        db.session.rollback()
        db.create_all()
        return render_template(
            "error.html",
            title="One moment",
            message="We just repaired something in the background. Please try that again.",
        ), 503

    @app.errorhandler(404)
    def handle_not_found(error):
        return render_template(
            "error.html",
            title="Page not found",
            message="That page doesn't exist.",
        ), 404

    @app.errorhandler(500)
    def handle_server_error(error):
        return render_template(
            "error.html",
            title="Something went wrong",
            message="An unexpected error occurred. Please try again.",
        ), 500

    return app
