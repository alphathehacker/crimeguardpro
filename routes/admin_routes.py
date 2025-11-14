from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from datetime import datetime
import jwt
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from models import db

load_dotenv()

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# -----------------------------
# Utility Functions
# -----------------------------
def serialize_doc(doc):
    """Convert MongoDB document to JSON-safe dict (recursively converts all ObjectId fields)"""
    if not doc:
        return None
    # Convert to dict if it's not already
    if not isinstance(doc, dict):
        doc = dict(doc)
    else:
        # Create a copy to avoid modifying the original
        doc = doc.copy()
    
    # Remove password_hash if present
    if "password_hash" in doc:
        doc.pop("password_hash")
    
    # Recursively convert all ObjectId fields to strings
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, datetime):
            # Convert datetime to ISO format string
            doc[k] = v.isoformat()
        elif isinstance(v, list):
            doc[k] = [serialize_doc(i) if isinstance(i, dict) else (str(i) if isinstance(i, ObjectId) else (i.isoformat() if isinstance(i, datetime) else i)) for i in v]
        elif isinstance(v, dict):
            doc[k] = serialize_doc(v)
    
    return doc


def verify_token():
    """Verify JWT token from Authorization header"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        secret_key = os.getenv("SECRET_KEY", "default_secret_key")
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_admin():
    """Check JWT and ensure user is admin"""
    user = verify_token()
    if not user or user.get("role") != "admin":
        return None
    return user


# =====================================================
# 👤 USER MANAGEMENT CRUD
# =====================================================

@admin_bp.route("/users", methods=["GET"])
def get_users():
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    role = request.args.get("role")
    q = request.args.get("q")

    query = {}
    if role:
        query["role"] = role
    if q:
        query["$or"] = [
            {"first_name": {"$regex": q, "$options": "i"}},
            {"last_name": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}}
        ]

    users = list(db["users"].find(query))
    return jsonify([serialize_doc(u) for u in users]), 200


@admin_bp.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        user = db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(serialize_doc(user)), 200
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400


@admin_bp.route("/users", methods=["POST"])
def create_user():
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    required = ["email", "role"]
    if not all(field in data and data[field] for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    new_user = {
        "first_name": data.get("first_name", ""),
        "last_name": data.get("last_name", ""),
        "email": data["email"],
        "role": data.get("role", "citizen"),
        "badge_number": data.get("badge_number", ""),
        "department": data.get("department", ""),
        "created_at": datetime.utcnow(),
        "last_login": None
    }

    if data.get("password"):
        new_user["password_hash"] = generate_password_hash(data["password"])
    else:
        # If no password provided, set a default or return error
        return jsonify({"error": "Password is required when creating a user"}), 400

    db["users"].insert_one(new_user)
    new_user["_id"] = str(new_user["_id"])
    new_user.pop("password_hash", None)
    return jsonify({"message": "User created successfully", "user": serialize_doc(new_user)}), 201


@admin_bp.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    update_fields = {}

    allowed = ["first_name", "last_name", "email", "role", "badge_number", "department", "password"]
    for field in allowed:
        if field in data and data[field] != "":
            if field == "password":
                # Hash the password before storing
                update_fields["password_hash"] = generate_password_hash(data[field])
            else:
                update_fields[field] = data[field]

    if not update_fields:
        return jsonify({"error": "No fields to update"}), 400

    try:
        db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
        updated_user = db["users"].find_one({"_id": ObjectId(user_id)})
        return jsonify({"message": "User updated", "user": serialize_doc(updated_user)}), 200
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400


@admin_bp.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        res = db["users"].delete_one({"_id": ObjectId(user_id)})
        if res.deleted_count == 0:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400


# =====================================================
# ⚖️ CASE MANAGEMENT CRUD
# =====================================================

@admin_bp.route("/cases", methods=["GET"])
def get_all_cases():
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        status = request.args.get("status")
        q = request.args.get("q")
        query = {}

        if status:
            query["status"] = status
        if q:
            query["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
                {"location": {"$regex": q, "$options": "i"}}
            ]

        cases = list(db["cases"].find(query))
        serialized_cases = [serialize_doc(c) for c in cases]
        return jsonify(serialized_cases), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching cases: {str(e)}"}), 500


@admin_bp.route("/cases/<case_id>", methods=["GET"])
def get_case(case_id):
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        case = db["cases"].find_one({"_id": ObjectId(case_id)})
        if not case:
            return jsonify({"error": "Case not found"}), 404
        return jsonify(serialize_doc(case)), 200
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400


@admin_bp.route("/cases", methods=["POST"])
def create_case():
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    required = ["title", "category", "location", "description"]
    if not all(field in data and data[field] for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    new_case = {
        "title": data["title"],
        "category": data["category"],
        "location": data["location"],
        "description": data["description"],
        "status": data.get("status", "Pending"),
        "created_by": data.get("created_by", "Admin"),
        "assigned_officer": data.get("assigned_officer", ""),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    db["cases"].insert_one(new_case)
    return jsonify({"message": "Case created successfully"}), 201


@admin_bp.route("/cases/<case_id>", methods=["PUT"])
def update_case(case_id):
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    allowed = ["title", "category", "location", "description", "status", "assigned_officer"]
    update_fields = {k: v for k, v in data.items() if k in allowed and v != ""}

    if not update_fields:
        return jsonify({"error": "No fields to update"}), 400

    update_fields["updated_at"] = datetime.utcnow()

    try:
        result = db["cases"].update_one({"_id": ObjectId(case_id)}, {"$set": update_fields})
        if result.matched_count == 0:
            return jsonify({"error": "Case not found"}), 404
        updated_case = db["cases"].find_one({"_id": ObjectId(case_id)})
        return jsonify({"message": "Case updated", "case": serialize_doc(updated_case)}), 200
    except Exception as e:
        return jsonify({"error": f"Invalid ID: {str(e)}"}), 400


@admin_bp.route("/cases/<case_id>", methods=["DELETE"])
def delete_case(case_id):
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        res = db["cases"].delete_one({"_id": ObjectId(case_id)})
        if res.deleted_count == 0:
            return jsonify({"error": "Case not found"}), 404
        return jsonify({"message": "Case deleted successfully"}), 200
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400


# =====================================================
# 📊 ANALYTICS / STATS (for dashboard charts)
# =====================================================

@admin_bp.route("/stats", methods=["GET"])
def admin_stats():
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    users_count = db["users"].count_documents({})
    cases_count = db["cases"].count_documents({})
    open_cases = db["cases"].count_documents({"status": "Pending"})
    closed_cases = db["cases"].count_documents({"status": "Closed"})
    officers = db["users"].count_documents({"role": "officer"})
    citizens = db["users"].count_documents({"role": "citizen"})

    return jsonify({
        "users_count": users_count,
        "cases_count": cases_count,
        "open_cases": open_cases,
        "closed_cases": closed_cases,
        "officers": officers,
        "citizens": citizens,
    }), 200


# =====================================================
# 📋 FIR MANAGEMENT (Admin can view all FIRs)
# =====================================================

@admin_bp.route("/firs", methods=["GET"])
def get_all_firs():
    """Get all FIRs (admin only)"""
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    status = request.args.get("status")
    q = request.args.get("q")
    query = {}

    if status:
        query["status"] = status
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"complainant_name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}}
        ]

    firs = list(db["officer_firs"].find(query).sort("created_at", -1))
    # Use serialize_doc to properly convert all ObjectIds and datetimes
    serialized_firs = [serialize_doc(fir) for fir in firs]
    # Format datetime fields for better readability
    for fir in serialized_firs:
        if fir.get("created_at"):
            try:
                # If it's already a string from isoformat, try to format it nicely
                if isinstance(fir["created_at"], str):
                    dt = datetime.fromisoformat(fir["created_at"].replace('Z', '+00:00'))
                    fir["created_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        if fir.get("updated_at"):
            try:
                if isinstance(fir["updated_at"], str):
                    dt = datetime.fromisoformat(fir["updated_at"].replace('Z', '+00:00'))
                    fir["updated_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass

    return jsonify(serialized_firs), 200


@admin_bp.route("/firs/<fir_id>", methods=["GET"])
def get_fir(fir_id):
    """Get a specific FIR (admin only)"""
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        fir = db["officer_firs"].find_one({"_id": ObjectId(fir_id)})
        if not fir:
            return jsonify({"error": "FIR not found"}), 404
        # Use serialize_doc to properly convert all ObjectIds and datetimes
        serialized_fir = serialize_doc(fir)
        # Format datetime fields for better readability
        if serialized_fir.get("created_at"):
            try:
                if isinstance(serialized_fir["created_at"], str):
                    dt = datetime.fromisoformat(serialized_fir["created_at"].replace('Z', '+00:00'))
                    serialized_fir["created_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        if serialized_fir.get("updated_at"):
            try:
                if isinstance(serialized_fir["updated_at"], str):
                    dt = datetime.fromisoformat(serialized_fir["updated_at"].replace('Z', '+00:00'))
                    serialized_fir["updated_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        return jsonify(serialized_fir), 200
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400


@admin_bp.route("/firs/<fir_id>", methods=["PUT"])
def update_fir(fir_id):
    """Update a FIR (admin only)"""
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    allowed = ["status", "priority", "officer_notes"]
    update_fields = {k: v for k, v in data.items() if k in allowed and v != ""}

    if not update_fields:
        return jsonify({"error": "No fields to update"}), 400

    update_fields["updated_at"] = datetime.utcnow()

    try:
        result = db["officer_firs"].update_one({"_id": ObjectId(fir_id)}, {"$set": update_fields})
        if result.matched_count == 0:
            return jsonify({"error": "FIR not found"}), 404
        updated_fir = db["officer_firs"].find_one({"_id": ObjectId(fir_id)})
        # Use serialize_doc to properly convert all ObjectIds and datetimes
        serialized_fir = serialize_doc(updated_fir)
        # Format datetime fields for better readability
        if serialized_fir.get("created_at"):
            try:
                if isinstance(serialized_fir["created_at"], str):
                    dt = datetime.fromisoformat(serialized_fir["created_at"].replace('Z', '+00:00'))
                    serialized_fir["created_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        if serialized_fir.get("updated_at"):
            try:
                if isinstance(serialized_fir["updated_at"], str):
                    dt = datetime.fromisoformat(serialized_fir["updated_at"].replace('Z', '+00:00'))
                    serialized_fir["updated_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        return jsonify({"message": "FIR updated", "fir": serialized_fir}), 200
    except Exception as e:
        return jsonify({"error": f"Invalid ID: {str(e)}"}), 400


@admin_bp.route("/firs/<fir_id>", methods=["DELETE"])
def delete_fir(fir_id):
    """Delete a FIR (admin only)"""
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        res = db["officer_firs"].delete_one({"_id": ObjectId(fir_id)})
        if res.deleted_count == 0:
            return jsonify({"error": "FIR not found"}), 404
        return jsonify({"message": "FIR deleted successfully"}), 200
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400


# =====================================================
# 🔔 ALERTS MANAGEMENT (Admin can view all alerts)
# =====================================================

@admin_bp.route("/alerts", methods=["GET"])
def get_all_alerts():
    """Get all alerts (admin only)"""
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    alerts = list(db["notifications"].find().sort("sent_at", -1).limit(50))
    # Use serialize_doc to properly convert all ObjectIds and datetimes
    serialized_alerts = [serialize_doc(alert) for alert in alerts]
    # Format datetime fields for better readability
    for alert in serialized_alerts:
        if alert.get("sent_at"):
            try:
                if isinstance(alert["sent_at"], str):
                    dt = datetime.fromisoformat(alert["sent_at"].replace('Z', '+00:00'))
                    alert["sent_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass

    return jsonify(serialized_alerts), 200


@admin_bp.route("/alerts", methods=["POST"])
def send_alert():
    """Send an alert (admin only)"""
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    title = data.get("title", "").strip()
    message = data.get("message", "").strip()

    if not title or not message:
        return jsonify({"error": "Both title and message are required"}), 400

    alert = {
        "title": title,
        "message": message,
        "sent_by": admin.get("email", "admin"),
        "sent_at": datetime.utcnow(),
        "read": False
    }

    db["notifications"].insert_one(alert)
    return jsonify({"success": True, "message": "Alert sent successfully"}), 201