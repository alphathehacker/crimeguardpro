import os
import datetime
import jwt
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import ObjectId

# --------------------------------------------------
# 1️⃣ Load Environment Variables
# --------------------------------------------------
load_dotenv()

# --------------------------------------------------
# 2️⃣ Flask Initialization
# --------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
CORS(app, supports_credentials=True)

# --------------------------------------------------
# 3️⃣ MongoDB Connection
# --------------------------------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/crime_management_db")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client.get_database()
    print(f"✅ Connected to MongoDB: {MONGO_URI}")
except ConnectionFailure as e:
    print("❌ MongoDB connection failed:", e)
    db = None

# --------------------------------------------------
# 4️⃣ JWT Token Management
# --------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")

def generate_token(user):
    """Generate JWT for user"""
    payload = {
        "user_id": str(user.get("_id")),
        "email": user.get("email"),
        "name": user.get("name", ""),
        "role": user.get("role"),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=6),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token():
    """Verify token from request header"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# --------------------------------------------------
# 5️⃣ Import Blueprints
# --------------------------------------------------
from routes.auth_routes import auth_bp
from routes.case_routes import case_bp
from routes.dashboard_routes import dashboard_bp
from routes.citizen_routes import citizen_bp
from routes.officer_routes import officer_bp
from routes.admin_routes import admin_bp

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(case_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(citizen_bp)
app.register_blueprint(officer_bp)
app.register_blueprint(admin_bp)

# --------------------------------------------------
# 6️⃣ Public Routes
# --------------------------------------------------
@app.route("/", methods=["GET"])
def default_home():
    return render_template("index.html")

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("authentication_gateway.html")

@app.route("/logout", methods=["GET"])
def logout_user():
    session.clear()
    return render_template("authentication_gateway.html")

@app.route("/home")
def home_page():
    return render_template("homepage_government_technology_platform.html")

@app.route("/homepage_government_technology_platform.html")
def homepage():
    return render_template("homepage_government_technology_platform.html")

# --------------------------------------------------
# 7️⃣ Role-Based Dashboards
# --------------------------------------------------
@app.route("/dashboard/citizen")
def citizen_dashboard():
    return render_template("unified_dashboard_citizen_only.html")

@app.route("/dashboard/officer")
def officer_dashboard():
    return render_template("unified_dashboard_officer_only.html")

@app.route("/dashboard/admin")
def admin_dashboard():
    return render_template("unified_dashboard_admin_command_center.html")

@app.route("/citizen-dashboard.html")
def citizen_dashboard_alias():
    return render_template("unified_dashboard_citizen_only.html")

@app.route("/officer-dashboard.html")
def officer_dashboard_alias():
    return render_template("unified_dashboard_officer_only.html")

@app.route("/admin-dashboard.html")
def admin_dashboard_alias():
    return render_template("unified_dashboard_admin_command_center.html")

# --------------------------------------------------
# 8️⃣ Static Info Pages
# --------------------------------------------------
@app.route("/resources")
def resources():
    return render_template("resources.html")

@app.route("/analytics")
def analytics():
    return render_template("analytics_reports_data_driven_insights.html")

@app.route("/help_center")
def help_center():
    return render_template("help_center.html")

@app.route("/profile/edit")
def profile_edit():
    return render_template("citizen_profile_edit.html")

@app.route("/officer/profile/edit")
def officer_profile_edit():
    return render_template("officer_profile_edit.html")

@app.route("/officer/preferences")
def officer_preferences():
    return render_template("officer_preferences.html")

@app.route("/system-status")
def system_status():
    return render_template("system_status.html")

@app.route("/account-assistance")
def account_assistance():
    return render_template("account_assistance.html")

@app.route("/password-recovery")
def password_recovery():
    return render_template("password_recovery.html")

@app.route("/contact")
def contact():
    return render_template("contact_us.html")

@app.route("/privacy_policy")
def privacy_policy():
    return render_template("privacy_policy.html")

@app.route("/terms_of_service")
def terms_of_service():
    return render_template("terms_of_service.html")

@app.route("/accessibility")
def accessibility():
    return render_template("accessibility.html")

@app.route("/incident_map")
def incident_map():
    return render_template("incident_map.html")

@app.route("/alerts")
def alerts_page():
    return render_template("alerts.html")

@app.route("/document_center_secure_file_management.html")
def document_center_secure_file_management():
    return render_template("document_center_secure_file_management.html")

# --------------------------------------------------
# 9️⃣ API: Current User Info (JWT or session)
# --------------------------------------------------
@app.route("/api/me", methods=["GET"])
def get_current_user():
    auth_header = request.headers.get("Authorization", "")
    email = None
    role = None

    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            email = payload.get("email")
            role = payload.get("role")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

    if not email and "email" in session:
        email = session.get("email")
        role = session.get("role", "citizen")

    if not email:
        return jsonify({"error": "Not logged in"}), 401

    user = db["users"].find_one({"email": email, "role": role})
    if not user:
        return jsonify({"error": "User not found"}), 404

    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)
    return jsonify({"user": user}), 200

# --------------------------------------------------
# 🔹 10️⃣ ADMIN CRUD API (Users + Cases + Stats)
# --------------------------------------------------
from flask import Blueprint

admin_api = Blueprint("admin_api", __name__, url_prefix="/api/admin")

def admin_required():
    token_data = verify_token()
    if not token_data or token_data.get("role") != "admin":
        return None
    return token_data

# ===== USERS =====
@admin_api.route("/users", methods=["GET"])
def admin_list_users():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 403
    users = []
    for user in db["users"].find():
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        users.append(user)
    return jsonify(users), 200

@admin_api.route("/users/<user_id>", methods=["GET"])
def admin_get_user(user_id):
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 403
    try:
        u = db["users"].find_one({"_id": ObjectId(user_id)})
        if not u:
            return jsonify({"error": "User not found"}), 404
        u["_id"] = str(u["_id"])
        u.pop("password_hash", None)
        return jsonify(u), 200
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400

@admin_api.route("/users", methods=["POST"])
def admin_create_user():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json() or {}
    if "email" not in data or "role" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    data["created_at"] = datetime.datetime.utcnow()
    data["updated_at"] = datetime.datetime.utcnow()
    res = db["users"].insert_one(data)
    data["_id"] = str(res.inserted_id)
    return jsonify(data), 201

@admin_api.route("/users/<user_id>", methods=["PUT"])
def admin_update_user(user_id):
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json() or {}
    data["updated_at"] = datetime.datetime.utcnow()
    db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": data})
    updated = db["users"].find_one({"_id": ObjectId(user_id)})
    updated["_id"] = str(updated["_id"])
    updated.pop("password_hash", None)
    return jsonify(updated), 200

@admin_api.route("/users/<user_id>", methods=["DELETE"])
def admin_delete_user(user_id):
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 403
    result = db["users"].delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "User deleted"}), 200

# ===== CASES =====
@admin_api.route("/cases", methods=["GET"])
def admin_list_cases():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 403
    cases = []
    for case in db["cases"].find():
        case["_id"] = str(case["_id"])
        cases.append(case)
    return jsonify(cases), 200

@admin_api.route("/cases", methods=["POST"])
def admin_create_case():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json() or {}
    if "title" not in data or "description" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    data["created_at"] = datetime.datetime.utcnow()
    data["updated_at"] = datetime.datetime.utcnow()
    res = db["cases"].insert_one(data)
    data["_id"] = str(res.inserted_id)
    return jsonify(data), 201

@admin_api.route("/cases/<case_id>", methods=["PUT"])
def admin_update_case(case_id):
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json() or {}
    data["updated_at"] = datetime.datetime.utcnow()
    db["cases"].update_one({"_id": ObjectId(case_id)}, {"$set": data})
    updated = db["cases"].find_one({"_id": ObjectId(case_id)})
    updated["_id"] = str(updated["_id"])
    return jsonify(updated), 200

@admin_api.route("/cases/<case_id>", methods=["DELETE"])
def admin_delete_case(case_id):
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 403
    res = db["cases"].delete_one({"_id": ObjectId(case_id)})
    if res.deleted_count == 0:
        return jsonify({"error": "Case not found"}), 404
    return jsonify({"message": "Case deleted"}), 200

# ===== STATS =====
@admin_api.route("/stats", methods=["GET"])
def admin_stats():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({
        "total_users": db["users"].count_documents({}),
        "total_cases": db["cases"].count_documents({}),
        "pending_cases": db["cases"].count_documents({"status": "Pending"}),
        "resolved_cases": db["cases"].count_documents({"status": "Resolved"}),
        "officers": db["users"].count_documents({"role": "officer"}),
        "citizens": db["users"].count_documents({"role": "citizen"})
    }), 200

app.register_blueprint(admin_api)

# --------------------------------------------------
# 11️⃣ Utility: List Routes
# --------------------------------------------------
@app.route("/api/routes", methods=["GET"])
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != "static":
            routes.append({
                "path": rule.rule,
                "methods": list(rule.methods - {"OPTIONS", "HEAD"}),
                "endpoint": rule.endpoint
            })
    return jsonify({
        "total_routes": len(routes),
        "routes": sorted(routes, key=lambda x: x["path"])
    })

# --------------------------------------------------
# 12️⃣ Error Handlers
# --------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(405)
def not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

# --------------------------------------------------
# 13️⃣ Run App
# --------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    print(f"🚀 Flask app running on http://127.0.0.1:{port}")
    app.run(debug=True, port=port)
