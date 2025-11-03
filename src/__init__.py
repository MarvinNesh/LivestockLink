from flask import Flask, render_template
from .extensions import db, login_manager
from .models import User
import os

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'a-very-secret-key'
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '../resources/users.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    @app.route('/')
    def dashboard():
        """lending page"""
        return render_template('index.html')

    with app.app_context():
        db.create_all()

    return app