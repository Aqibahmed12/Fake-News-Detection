"""
REST API — Authentication Endpoints
POST /api/v1/auth/token   — obtain JWT
POST /api/v1/auth/register
"""
from flask import request, jsonify
from flask_jwt_extended import create_access_token

from app.api import api_bp
from app.extensions import db
from app.models.user import User


@api_bp.route("/auth/token", methods=["POST"])
def get_token():
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "token_type": "Bearer",
        "user": user.to_dict(),
    }), 200


@api_bp.route("/auth/register", methods=["POST"])
def register_api():
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not email or not username or not password:
        return jsonify({"error": "email, username, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409

    user = User(email=email, username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "token_type": "Bearer",
        "user": user.to_dict(),
    }), 201
