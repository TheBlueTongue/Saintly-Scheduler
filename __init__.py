from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students_todo.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with the app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Import blueprints for routes
    from .auth import auth as auth_blueprint
    from .routes import main as main_blueprint
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    
    with app.app_context():
        db.create_all()
    
    return app