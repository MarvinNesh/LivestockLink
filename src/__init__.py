import os
import random
from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from .extensions import db, login_manager
from .models import User
from .facts import facts

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(app.root_path), 'resources', 'users.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def index():
        fact = random.choice(facts)
        return render_template('index.html', fact=fact)

    with app.app_context():
        db.create_all()

    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .scanner.routes import scanner_bp
    app.register_blueprint(scanner_bp)

    from .tips.routes import tips_bp
    app.register_blueprint(tips_bp)

    return app