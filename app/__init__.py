
from flask import Flask
from .models import db
from .routes import tasks_bp  # Import the tasks blueprint
from .main import main  # Import the main blueprint

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Register the main and tasks blueprints
    app.register_blueprint(main)  # Register main blueprint
    app.register_blueprint(tasks_bp, url_prefix='/tasks')  # Register tasks blueprint with /tasks prefix

    return app
