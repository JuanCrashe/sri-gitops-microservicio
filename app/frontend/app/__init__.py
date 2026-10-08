import os
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default-dev-key')
    
    from app.routes import frontend_bp
    app.register_blueprint(frontend_bp)
    
    return app
