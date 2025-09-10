import os
import sys
from flask import Flask, send_from_directory
from src.models.user import db
from src.routes.news import news_bp
from src.routes.user import user_bp   # <-- Import do user_bp

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Cria a aplicação Flask
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Blueprints
app.register_blueprint(user_bp, url_prefix_
