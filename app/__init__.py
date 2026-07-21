from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(test_config=None):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .models import models
    from .routes.auth import auth_bp
    from .main import main_bp
    from .routes.note import note_bp
    from .routes.topics import topic_bp
    from .routes.ai_assistant import ai_assistant_bp
    from .routes.flashcard import flashcard_bp
    from .routes.progress import progress_bp
    from .routes.study_mode import study_mode_bp
    from .routes.quiz_mode import quiz_mode_bp
    from .routes.study_plan import study_plan_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(note_bp)
    app.register_blueprint(topic_bp)
    app.register_blueprint(ai_assistant_bp)
    app.register_blueprint(flashcard_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(study_mode_bp)
    app.register_blueprint(quiz_mode_bp)
    app.register_blueprint(study_plan_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    return app