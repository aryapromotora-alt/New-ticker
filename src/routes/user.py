from flask import Blueprint, request, jsonify
from src.models.user import db, User

user_bp = Blueprint("user", __name__)

# Rota para listar usuários
@user_bp.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "username": u.username, "email": u.email} for u in users])

# Rota para adicionar usuário
@user_bp.route("/users", methods=["POST"])
def add_user():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("email"):
        return jsonify({"error": "username e email são obrigatórios"}), 400

    new_user = User(username=data["username"], email=data["email"])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Usuário criado com sucesso", "id": new_user.id}), 201
