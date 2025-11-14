from flask import Blueprint, request, jsonify
from models.user_model import get_user_by_id, update_user
from models.case_model import get_cases_by_citizen, create_case

# Prefix for citizens API
citizen_bp = Blueprint("citizen", __name__, url_prefix="/api/citizen")

# -----------------------
# VIEW CITIZEN PROFILE
# -----------------------
@citizen_bp.route("/<citizen_id>", methods=["GET"])
def get_citizen_profile(citizen_id):
    user = get_user_by_id(citizen_id)
    if not user or user.get("role") != "citizen":
        return jsonify({"error": "Citizen not found"}), 404
    user.pop("password_hash", None)
    return jsonify(user)

# -----------------------
# UPDATE CITIZEN PROFILE
# -----------------------
@citizen_bp.route("/<citizen_id>", methods=["PUT"])
def update_citizen_profile(citizen_id):
    data = request.get_json()
    updated = update_user(citizen_id, data)
    return jsonify(updated)

# -----------------------
# FILE A NEW COMPLAINT
# -----------------------
@citizen_bp.route("/<citizen_id>/cases", methods=["POST"])
def file_complaint(citizen_id):
    data = request.get_json()
    required = ["title", "description", "category", "location"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400
    case = create_case(citizen_id, data["title"], data["description"], data["category"], data["location"])
    return jsonify(case), 201

# -----------------------
# VIEW OWN COMPLAINTS
# -----------------------
@citizen_bp.route("/<citizen_id>/cases", methods=["GET"])
def view_complaints(citizen_id):
    cases = get_cases_by_citizen(citizen_id)
    return jsonify(cases)
