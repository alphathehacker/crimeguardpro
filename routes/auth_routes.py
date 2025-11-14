from flask import Blueprint, request, jsonify
from models.user_model import create_user, verify_user, get_user_by_id
from bson import ObjectId
import jwt, os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------
# Blueprint with unified /api prefix
# -------------------------------------------------
auth_bp = Blueprint("auth", __name__, url_prefix="/api")

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")


# -------------------------------------------------
# Generate JWT Token
# -------------------------------------------------
def create_token(user):
    payload = {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user.get("role", "citizen"),
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


# -------------------------------------------------
# Helper for Registration
# -------------------------------------------------
def handle_registration(data, role):
    required = ["first_name", "last_name", "email", "phone", "password"]
    missing = [field for field in required if field not in data or not data[field]]
    if missing:
        return jsonify({"error": "Missing required fields", "fields": missing}), 400

    # Create user with role (citizen/officer/admin)
    user = create_user(
        data["first_name"],
        data["last_name"],
        data["email"],
        data["phone"],
        data["password"],
        role
    )

    if "error" in user:
        return jsonify(user), 400

    user.pop("password_hash", None)
    token = create_token(user)
    return jsonify({
        "message": f"{role.capitalize()} registered successfully",
        "user": user,
        "token": token
    }), 201


# -------------------------------------------------
# REGISTER CITIZEN
# -------------------------------------------------
@auth_bp.route("/register/citizen", methods=["POST"])
def register_citizen():
    data = request.get_json() or {}
    return handle_registration(data, "citizen")


# -------------------------------------------------
# REGISTER OFFICER
# -------------------------------------------------
@auth_bp.route("/register/officer", methods=["POST"])
def register_officer():
    data = request.get_json() or {}
    return handle_registration(data, "officer")


# -------------------------------------------------
# REGISTER ADMIN
# -------------------------------------------------
@auth_bp.route("/register/admin", methods=["POST"])
def register_admin():
    data = request.get_json() or {}
    return handle_registration(data, "admin")


# -------------------------------------------------
# LOGIN USER (Role-based)
# -------------------------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")
    role = data.get("role")  # 👈 Frontend must send role: citizen/officer/admin

    if not email or not password or not role:
        return jsonify({"error": "Email, password, and role are required"}), 400

    # Check user by email and role
    from models.user_model import users_col  # direct collection reference
    user = users_col.find_one({"email": email, "role": role})
    if not user:
        return jsonify({"error": f"No {role} account found for this email"}), 404

    from werkzeug.security import check_password_hash
    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid password"}), 401

    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)
    token = create_token(user)

    return jsonify({
        "message": f"{role.capitalize()} login successful",
        "user": user,
        "token": token
    }), 200


# -------------------------------------------------
# GET USER PROFILE (JWT Protected)
# -------------------------------------------------
@auth_bp.route("/profile/<user_id>", methods=["GET"])
def get_profile(user_id):
    """Get user profile (requires valid JWT token in Authorization header)."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authorization header missing or invalid"}), 401

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    # ✅ Only allow self or admin to view
    if payload["user_id"] != user_id and payload["role"] != "admin":
        return jsonify({"error": "Unauthorized access"}), 403

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.pop("password_hash", None)
    return jsonify(user), 200
