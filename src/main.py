import os
import sys
from flask import Flask, send_from_directory
from src.models.user import db
from src.routes.news import news_bp
from src.routes.user import user_bp   # importa o blueprint de usuários
from src.routes.ticker import ticker_bp

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Cria a aplicação Flask
app = Flask(__name__, static_folder="static", static_url_path="")
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# --- Garantir que a pasta database existe ---
db_folder = os.path.join(os.path.dirname(__file__), "database")
os.makedirs(db_folder, exist_ok=True)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(db_folder, 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Blueprints
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(news_bp, url_prefix='/api/news')
app.register_blueprint(ticker_bp, url_prefix='/api/ticker')

# Cria tabelas automaticamente se não existirem
with app.app_context():
    db.create_all()

# Rota para servir arquivos estáticos (ex: index.html)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)  # Debug desativado para produção
