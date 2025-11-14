from flask import Blueprint, request, jsonify, current_app as app
from bson import ObjectId
from datetime import datetime
import jwt
from models import db, to_str_id

# -------------------------------------------------
# Blueprint Setup
# -------------------------------------------------
case_bp = Blueprint("case", __name__, url_prefix="/api/cases")

cases_col = db["cases"]
users_col = db["users"]


# -------------------------------------------------
# Helper: Verify JWT token
# -------------------------------------------------
def verify_token(req):
    """Extract and verify JWT token from Authorization header"""
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# -------------------------------------------------
# ✅ CREATE NEW CASE (Auto-fetch citizen_id from token)
# -------------------------------------------------
@case_bp.route("", methods=["POST"])
def create_new_case():
    try:
        payload = verify_token(request)
        if not payload:
            return jsonify({"error": "Unauthorized or invalid token"}), 401

        user_id = payload.get("user_id")
        user_email = payload.get("email")

        data = request.get_json() or {}
        title = data.get("title")
        category = data.get("category")
        location = data.get("location")
        description = data.get("description")

        # Validate required fields
        if not all([title, category, location, description]):
            return jsonify({"error": "Missing fields"}), 400

        # Verify citizen exists
        citizen = users_col.find_one({"_id": ObjectId(user_id), "role": "citizen"})
        if not citizen:
            return jsonify({"error": "Citizen not found"}), 404

        # Create case document
        case_doc = {
            "citizen_id": ObjectId(user_id),
            "citizen_name": f"{citizen.get('first_name', '')} {citizen.get('last_name', '')}".strip(),
            "citizen_email": user_email,
            "title": title,
            "description": description,
            "category": category,
            "location": location,
            "status": "Pending",
            "priority": "Normal",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        res = cases_col.insert_one(case_doc)
        case_doc["_id"] = res.inserted_id

        return jsonify({
            "message": "Crime report submitted successfully",
            "case": to_str_id(case_doc)
        }), 201

    except Exception as e:
        print("❌ Error creating new case:", e)
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------
# ✅ GET ALL CASES (For Admin/Debug)
# -------------------------------------------------
@case_bp.route("", methods=["GET"])
def get_cases():
    try:
        cases = list(cases_col.find().sort("created_at", -1))
        return jsonify([to_str_id(c) for c in cases]), 200
    except Exception as e:
        print("❌ Error fetching all cases:", e)
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------
# ✅ GET CASE BY ID
# -------------------------------------------------
@case_bp.route("/<case_id>", methods=["GET"])
def get_case(case_id):
    try:
        case = cases_col.find_one({"_id": ObjectId(case_id)})
        if not case:
            return jsonify({"error": "Case not found"}), 404
        return jsonify(to_str_id(case)), 200
    except Exception as e:
        print("❌ Error fetching case:", e)
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------
# ✅ GET ALL CASES BY CITIZEN ID
# -------------------------------------------------
@case_bp.route("/citizen/<citizen_id>", methods=["GET"])
def get_citizen_cases(citizen_id):
    try:
        cases_cursor = cases_col.find({"citizen_id": ObjectId(citizen_id)}).sort("created_at", -1)
        cases = [to_str_id(c) for c in cases_cursor]
        return jsonify({"cases": cases}), 200
    except Exception as e:
        print("❌ Error in get_citizen_cases:", e)
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------
# ✅ UPDATE CASE DETAILS OR STATUS
# -------------------------------------------------
@case_bp.route("/<case_id>", methods=["PUT"])
def update_case_route(case_id):
    try:
        updates = request.get_json() or {}
        if not updates:
            return jsonify({"error": "No update data provided"}), 400

        updates["updated_at"] = datetime.utcnow()
        res = cases_col.find_one_and_update(
            {"_id": ObjectId(case_id)},
            {"$set": updates},
            return_document=True
        )
        if not res:
            return jsonify({"error": "Case not found"}), 404

        return jsonify({
            "message": "Case updated successfully",
            "updated_case": to_str_id(res)
        }), 200

    except Exception as e:
        print("❌ Error updating case:", e)
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------
# ✅ DELETE A CASE
# -------------------------------------------------
@case_bp.route("/<case_id>", methods=["DELETE"])
def delete_case_route(case_id):
    try:
        res = cases_col.delete_one({"_id": ObjectId(case_id)})
        if res.deleted_count == 0:
            return jsonify({"error": "Case not found"}), 404
        return jsonify({"message": "Case deleted successfully"}), 200
    except Exception as e:
        print("❌ Error deleting case:", e)
        return jsonify({"error": str(e)}), 500
