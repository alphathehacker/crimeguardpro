from flask import Blueprint, jsonify
from models import db

# Prefix for dashboard API
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

# -----------------------
# DASHBOARD STATISTICS
# -----------------------
@dashboard_bp.route("/stats", methods=["GET"])
def dashboard_stats():
    total_users = db["users"].count_documents({})
    total_cases = db["cases"].count_documents({})
    pending_cases = db["cases"].count_documents({"status": "Pending"})
    resolved_cases = db["cases"].count_documents({"status": "Resolved"})
    officers = db["users"].count_documents({"role": "officer"})

    return jsonify({
        "total_users": total_users,
        "total_cases": total_cases,
        "pending_cases": pending_cases,
        "resolved_cases": resolved_cases,
        "officers": officers
    })
