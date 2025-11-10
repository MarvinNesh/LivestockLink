import os
import random
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from .extensions import db
from .models import User
from .facts import facts as livestock_facts
import google.generativeai as genai

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)

    
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'users.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    

    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        print("WARNING: SECRET_KEY environment variable not set. Using a default, insecure key for development.")
        secret_key = '91df1453195d837ad743d920' # Default for development only
    app.config['SECRET_KEY'] = secret_key
    
    # Configure Gemini API
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
    else:
        print("WARNING: GEMINI_API_KEY environment variable not set. The chatbot feature will not work.")

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/')

    from .scanner.routes import scanner_bp
    app.register_blueprint(scanner_bp, url_prefix='/')

    from .tips.routes import tips_bp
    app.register_blueprint(tips_bp, url_prefix='/')

    from .outbreaks.routes import outbreaks_bp
    app.register_blueprint(outbreaks_bp, url_prefix='/')

    from .chatbot.routes import chatbot_bp
    app.register_blueprint(chatbot_bp, url_prefix='/')

    from .admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route('/')
    def index():
        fact = random.choice(livestock_facts)
        return render_template('index.html', fact=fact)

    return app