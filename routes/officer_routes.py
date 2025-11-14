from flask import Blueprint, request, jsonify, current_app
from models.case_model import get_case_by_id
from models import db, to_str_id
from bson import ObjectId
from datetime import datetime
import jwt
from gridfs import GridFS
from werkzeug.utils import secure_filename

# -----------------------
# BLUEPRINT CONFIG
# -----------------------
officer_bp = Blueprint("officer", __name__, url_prefix="/api/officer")

# MongoDB collections
officers_col = db["users"]
cases_col = db["cases"]
officer_firs_col = db["officer_firs"]  # ✅ NEW collection for Officer FIRs
evidence_col = db["evidence"]  # Evidence metadata collection

# GridFS for file storage
if db is not None:
    fs = GridFS(db)
else:
    fs = None

# -----------------------
# JWT AUTH HELPER
# -----------------------
def verify_token(req):
    """Extract and verify JWT from Authorization header."""
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, current_app.secret_key, algorithms=["HS256"])
        return payload
    except Exception:
        return None

# -----------------------
# GET LOGGED-IN OFFICER PROFILE
# -----------------------
@officer_bp.route("/me", methods=["GET"])
def get_logged_officer():
    """Return currently logged-in officer’s details."""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    officer_id = payload.get("user_id")
    if not officer_id:
        return jsonify({"error": "Invalid token"}), 400

    officer = officers_col.find_one({"_id": ObjectId(officer_id)})
    if not officer:
        return jsonify({"error": "Officer not found"}), 404

    return jsonify({
        "id": str(officer["_id"]),
        "name": officer.get("name", "Officer"),
        "first_name": officer.get("first_name", ""),
        "last_name": officer.get("last_name", ""),
        "badge": officer.get("badge", "—"),
        "department": officer.get("department", "—"),
        "email": officer.get("email", ""),
        "phone": officer.get("phone", ""),
        "photo": officer.get("photo", ""),
        "last_login": officer.get("last_login", ""),
        "address": officer.get("address", ""),
        "date_of_birth": officer.get("date_of_birth", ""),
        "gender": officer.get("gender", ""),
    }), 200


# -----------------------
# UPDATE OFFICER PROFILE
# -----------------------
@officer_bp.route("/me", methods=["PUT"])
def update_officer_profile():
    """Update currently logged-in officer's profile."""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    officer_id = payload.get("user_id")
    if not officer_id:
        return jsonify({"error": "Invalid token"}), 400

    officer = officers_col.find_one({"_id": ObjectId(officer_id)})
    if not officer:
        return jsonify({"error": "Officer not found"}), 404

    data = request.get_json() or {}
    
    # Allowed fields for update
    allowed_fields = {
        "first_name", "last_name", "email", "phone", "badge", 
        "department", "address", "date_of_birth", "gender", "password"
    }
    
    update_data = {}
    for field in allowed_fields:
        if field in data and data[field]:
            if field == "password":
                # Hash password if provided
                from werkzeug.security import generate_password_hash
                update_data["password_hash"] = generate_password_hash(data[field])
            else:
                update_data[field] = data[field]
    
    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    update_data["updated_at"] = datetime.utcnow()
    
    # Update name if first_name or last_name changed
    if "first_name" in update_data or "last_name" in update_data:
        first_name = update_data.get("first_name", officer.get("first_name", ""))
        last_name = update_data.get("last_name", officer.get("last_name", ""))
        update_data["name"] = f"{first_name} {last_name}".strip()

    officers_col.update_one({"_id": ObjectId(officer_id)}, {"$set": update_data})
    
    # Fetch updated officer
    updated_officer = officers_col.find_one({"_id": ObjectId(officer_id)})
    updated_officer.pop("password_hash", None)
    
    return jsonify({
        "message": "Profile updated successfully",
        "officer": to_str_id(updated_officer)
    }), 200


# -----------------------
# GET CASES ASSIGNED TO LOGGED-IN OFFICER
# -----------------------
@officer_bp.route("/cases", methods=["GET"])
def officer_cases():
    """Return cases assigned to the logged-in officer."""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    officer_id = payload.get("user_id")
    officer_name = payload.get("name", "")
    query = {
        "$or": [
            {"assigned_to": ObjectId(officer_id)},
            {"assigned_name": officer_name}
        ]
    }

    # Optional filters
    status = request.args.get("status")
    if status:
        query["status"] = status

    priority = request.args.get("priority")
    if priority:
        query["priority"] = priority.capitalize()

    cases = list(cases_col.find(query).sort("created_at", -1))
    for c in cases:
        c["_id"] = str(c["_id"])
    return jsonify(cases), 200


# -----------------------
# GET SPECIFIC CASE (ONLY IF ASSIGNED)
# -----------------------
@officer_bp.route("/cases/<case_id>", methods=["GET"])
def view_case_details(case_id):
    """View a case only if assigned to logged-in officer."""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    officer_id = payload.get("user_id")
    case = cases_col.find_one({"_id": ObjectId(case_id)})
    if not case:
        return jsonify({"error": "Case not found"}), 404

    # Security check
    assigned = case.get("assigned_to")
    if assigned and str(assigned) != officer_id:
        return jsonify({"error": "Access denied"}), 403

    case["_id"] = str(case["_id"])
    return jsonify(case), 200


# -----------------------
# UPDATE CASE STATUS / PRIORITY / NOTES (Officer Only)
# -----------------------
@officer_bp.route("/cases/<case_id>/update", methods=["PUT"])
def update_case_status(case_id):
    """Update a case status, priority, or notes if assigned to officer."""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    allowed_fields = {"status", "priority", "officer_notes"}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = payload.get("user_id")

    case = cases_col.find_one({"_id": ObjectId(case_id)})
    if not case:
        return jsonify({"error": "Case not found"}), 404

    # Security check
    assigned = case.get("assigned_to")
    if assigned and str(assigned) != payload.get("user_id"):
        return jsonify({"error": "Access denied"}), 403

    cases_col.update_one({"_id": ObjectId(case_id)}, {"$set": update_data})
    updated_case = get_case_by_id(case_id)
    return jsonify(updated_case), 200

@officer_bp.route("/team", methods=["GET"])
def get_team_officers():
    """Return list of all officers except the logged-in officer."""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = payload.get("user_id")

    officers = list(db["users"].find({"role": "officer"}))
    team = []
    for o in officers:
        if str(o["_id"]) == user_id:
            continue
        team.append({
            "id": str(o["_id"]),
            "name": o.get("name") or o.get("email", "").split("@")[0].capitalize() or "Officer",
            "email": o.get("email", "N/A"),
            "status": o.get("status", "Offline"),
            "photo": o.get("photo") or "https://cdn-icons-png.flaticon.com/512/149/149071.png"
        })
    return jsonify(team), 200
# -----------------------
# INCIDENT MAP DATA (FIRs + Cases)
# -----------------------
@officer_bp.route("/incidents", methods=["GET"])
def get_incident_map_data():
    """Return all FIRs and cases with location info for map plotting."""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    # Fetch officer FIRs
    officer_firs = list(db["officer_firs"].find({}, {
        "title": 1,
        "category": 1,
        "location": 1,
        "complainant_name": 1,
        "created_at": 1,
        "status": 1
    }))

    # Fetch citizen cases
    citizen_cases = list(db["cases"].find({}, {
        "title": 1,
        "category": 1,
        "location": 1,
        "complainant_name": 1,
        "created_at": 1,
        "status": 1
    }))

    # Combine and normalize data
    all_incidents = []
    for c in officer_firs + citizen_cases:
        all_incidents.append({
            "id": str(c.get("_id")),
            "title": c.get("title", "Untitled"),
            "category": c.get("category", "Unknown"),
            "complainant": c.get("complainant_name", "—"),
            "location": c.get("location", "Unknown"),
            "status": c.get("status", "Pending"),
            "created_at": c.get("created_at", ""),
        })

    return jsonify(all_incidents), 200

# -----------------------
# SEND ALERT / NOTIFICATION (Officer Broadcast)
# -----------------------
@officer_bp.route("/send_alert", methods=["POST"])
def send_alert():
    """Allows an officer to send an alert or message to all other officers."""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    title = data.get("title", "").strip()
    message = data.get("message", "").strip()

    if not title or not message:
        return jsonify({"error": "Both title and message are required"}), 400

    alert = {
        "title": title,
        "message": message,
        "sent_by": payload.get("email"),
        "sent_at": datetime.utcnow(),
        "read": False
    }

    db["notifications"].insert_one(alert)
    return jsonify({"success": True, "message": "Alert sent successfully"}), 201


# -----------------------
# FETCH ALERTS / NOTIFICATIONS
# -----------------------
@officer_bp.route("/alerts", methods=["GET"])
def get_alerts():
    """Fetch the latest alerts for display in the notification dropdown."""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    alerts = list(db["notifications"].find().sort("sent_at", -1).limit(10))
    for a in alerts:
        a["_id"] = str(a["_id"])
        a["sent_at"] = a["sent_at"].strftime("%Y-%m-%d %H:%M:%S")

    return jsonify(alerts), 200



# =====================================================
# 🔹 NEW SECTION — OFFICER FIR MANAGEMENT
# =====================================================

# -----------------------
# CREATE FIR (Officer Only)
# -----------------------
@officer_bp.route("/fir", methods=["POST"])
def create_officer_fir():
    """Allow an officer to register a new FIR."""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    officer_id = payload.get("user_id")
    officer = db["users"].find_one({"_id": ObjectId(officer_id), "role": "officer"})
    if not officer:
        return jsonify({"error": "Officer not found"}), 404

    data = request.get_json() or {}
    required_fields = ["title", "category", "complainant_name", "contact", "location", "description"]
    if not all(data.get(f) for f in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    fir_doc = {
        "title": data["title"],
        "category": data["category"],
        "complainant_name": data["complainant_name"],
        "contact": data["contact"],
        "location": data["location"],
        "description": data["description"],
        "officer_id": officer_id,
        "officer_name": officer.get("name", "Unknown Officer"),
        "status": "Pending",
        "priority": data.get("priority", "Normal"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = officer_firs_col.insert_one(fir_doc)
    fir_doc["_id"] = str(result.inserted_id)

    return jsonify({
        "message": "FIR created successfully",
        "fir": fir_doc
    }), 201



   


# -----------------------
# GET ALL OFFICER FIRs
# -----------------------
@officer_bp.route("/fir", methods=["GET"])
def get_all_officer_firs():
    """
    Returns all FIRs created by the currently logged-in officer.
    Ensures JWT authentication and sorts FIRs in descending order of creation.
    """
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    officer_id = payload.get("user_id")
    if not officer_id:
        return jsonify({"error": "Invalid token"}), 400

    officer = officers_col.find_one({"_id": ObjectId(officer_id)})
    if not officer:
        return jsonify({"error": "Officer not found"}), 404

    # Fetch all FIRs created by this officer
    firs = list(
        officer_firs_col.find({"officer_id": officer_id}).sort("created_at", -1)
    )

    # Clean up MongoDB ObjectIds for JSON response
    for fir in firs:
        fir["_id"] = str(fir["_id"])
        fir["officer_id"] = str(fir.get("officer_id", ""))
        fir["created_at"] = fir.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if fir.get("created_at") else "—"

    # Add metadata to the response
    return jsonify({
        "count": len(firs),
        "officer": {
            "name": officer.get("name"),
            "badge": officer.get("badge"),
            "email": officer.get("email"),
        },
        "firs": firs
    }), 200


# -----------------------
# GET SPECIFIC OFFICER FIR
# -----------------------
@officer_bp.route("/fir/<fir_id>", methods=["GET"])
def get_officer_fir(fir_id):
    """
    Fetch details of a specific FIR created by the logged-in officer.
    Returns full FIR details only if the officer owns it.
    """
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    officer_id = payload.get("user_id")
    if not officer_id:
        return jsonify({"error": "Invalid token"}), 400

    try:
        fir = officer_firs_col.find_one({"_id": ObjectId(fir_id)})
    except Exception:
        return jsonify({"error": "Invalid FIR ID"}), 400

    if not fir:
        return jsonify({"error": "FIR not found"}), 404

    # Security check: Officer can only view their own FIRs
    if fir.get("officer_id") != officer_id:
        return jsonify({"error": "Access denied"}), 403

    # Format for frontend
    fir["_id"] = str(fir["_id"])
    fir["officer_id"] = str(fir.get("officer_id", ""))
    fir["created_at"] = fir.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if fir.get("created_at") else "—"
    if fir.get("updated_at"):
        fir["updated_at"] = fir["updated_at"].strftime("%Y-%m-%d %H:%M:%S")

    return jsonify(fir), 200


# -----------------------
# UPDATE OFFICER FIR
# -----------------------
@officer_bp.route("/fir/<fir_id>", methods=["PUT"])
def update_officer_fir(fir_id):
    """
    Allow a logged-in officer to update the status, priority, or notes
    of an FIR they created.
    """
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    officer_id = payload.get("user_id")
    if not officer_id:
        return jsonify({"error": "Invalid token"}), 400

    try:
        fir = officer_firs_col.find_one({"_id": ObjectId(fir_id)})
    except Exception:
        return jsonify({"error": "Invalid FIR ID"}), 400

    if not fir:
        return jsonify({"error": "FIR not found"}), 404

    # Security check
    if fir.get("officer_id") != officer_id:
        return jsonify({"error": "Access denied"}), 403

    # Collect fields to update
    data = request.get_json() or {}
    allowed_fields = {"status", "priority", "officer_notes"}
    update_fields = {k: v for k, v in data.items() if k in allowed_fields and v}

    if not update_fields:
        return jsonify({"error": "No valid fields to update"}), 400

    update_fields["updated_at"] = datetime.utcnow()

    # Update the FIR
    officer_firs_col.update_one({"_id": ObjectId(fir_id)}, {"$set": update_fields})

    # Fetch and return updated document
    updated_fir = officer_firs_col.find_one({"_id": ObjectId(fir_id)})
    updated_fir["_id"] = str(updated_fir["_id"])
    updated_fir["officer_id"] = str(updated_fir.get("officer_id", ""))
    if updated_fir.get("updated_at"):
        updated_fir["updated_at"] = updated_fir["updated_at"].strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({
        "message": "FIR updated successfully",
        "updated_fir": updated_fir
    }), 200

# -----------------------
# DELETE OFFICER FIR
# -----------------------
@officer_bp.route("/fir/<fir_id>", methods=["DELETE"])
def delete_officer_fir(fir_id):
    """Allow officer to delete their own FIR."""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    officer_id = payload.get("user_id")
    fir = officer_firs_col.find_one({"_id": ObjectId(fir_id)})

    if not fir:
        return jsonify({"error": "FIR not found"}), 404
    if fir.get("officer_id") != officer_id:
        return jsonify({"error": "Access denied"}), 403

    officer_firs_col.delete_one({"_id": ObjectId(fir_id)})
    return jsonify({"message": "FIR deleted successfully"}), 200


# =====================================================
# 📎 EVIDENCE UPLOAD & MANAGEMENT
# =====================================================

@officer_bp.route("/evidence", methods=["POST"])
def upload_evidence():
    """Upload evidence files for a case or FIR"""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    officer_id = payload.get("user_id")
    if not officer_id:
        return jsonify({"error": "Invalid token"}), 400

    # Get form data
    case_id = request.form.get("case_id", "").strip()
    fir_id = request.form.get("fir_id", "").strip()
    notes = request.form.get("notes", "").strip()
    files = request.files.getlist("files")

    if not case_id and not fir_id:
        return jsonify({"error": "Either case_id or fir_id is required"}), 400

    if not files or len(files) == 0:
        return jsonify({"error": "No files provided"}), 400

    # Verify case or FIR exists and officer has access
    if case_id:
        try:
            case = cases_col.find_one({"_id": ObjectId(case_id)})
            if not case:
                return jsonify({"error": "Case not found"}), 404
            # Check if officer is assigned to this case
            assigned_to = case.get("assigned_to")
            if assigned_to and str(assigned_to) != officer_id:
                # Allow if no assignment or if officer created it
                pass  # For now, allow any officer to upload evidence
        except Exception:
            return jsonify({"error": "Invalid case ID"}), 400

    if fir_id:
        try:
            fir = officer_firs_col.find_one({"_id": ObjectId(fir_id)})
            if not fir:
                return jsonify({"error": "FIR not found"}), 404
            # Check if officer owns this FIR
            if fir.get("officer_id") != officer_id:
                return jsonify({"error": "Access denied"}), 403
        except Exception:
            return jsonify({"error": "Invalid FIR ID"}), 400

    uploaded_files = []
    errors = []

    for file in files:
        if not file.filename:
            continue

        try:
            # Read file content
            file_content = file.read()
            file_size = len(file_content)

            # Validate file size (10MB limit)
            if file_size > 10 * 1024 * 1024:
                errors.append(f"{file.filename}: File too large (max 10MB)")
                continue

            # Check if GridFS is available
            if not fs:
                errors.append(f"{file.filename}: File storage not available")
                continue

            # Store file in GridFS
            file_id = fs.put(
                file_content,
                filename=secure_filename(file.filename),
                content_type=file.content_type or "application/octet-stream",
                upload_date=datetime.utcnow()
            )

            # Store metadata in evidence collection
            evidence_doc = {
                "file_id": file_id,
                "filename": secure_filename(file.filename),
                "original_filename": file.filename,
                "content_type": file.content_type or "application/octet-stream",
                "file_size": file_size,
                "case_id": ObjectId(case_id) if case_id else None,
                "fir_id": ObjectId(fir_id) if fir_id else None,
                "officer_id": officer_id,
                "officer_name": payload.get("name", ""),
                "notes": notes,
                "uploaded_at": datetime.utcnow(),
                "status": "active"
            }

            evidence_id = evidence_col.insert_one(evidence_doc).inserted_id

            uploaded_files.append({
                "evidence_id": str(evidence_id),
                "file_id": str(file_id),
                "filename": file.filename,
                "size": file_size
            })

        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
            continue

    if not uploaded_files:
        return jsonify({"error": "No files uploaded", "errors": errors}), 400

    return jsonify({
        "message": f"Successfully uploaded {len(uploaded_files)} file(s)",
        "uploaded_files": uploaded_files,
        "errors": errors if errors else None
    }), 201


@officer_bp.route("/evidence", methods=["GET"])
def get_evidence():
    """Get evidence for a case or FIR"""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    case_id = request.args.get("case_id")
    fir_id = request.args.get("fir_id")

    if not case_id and not fir_id:
        return jsonify({"error": "Either case_id or fir_id is required"}), 400

    query = {}
    if case_id:
        try:
            query["case_id"] = ObjectId(case_id)
        except Exception:
            return jsonify({"error": "Invalid case ID"}), 400

    if fir_id:
        try:
            query["fir_id"] = ObjectId(fir_id)
        except Exception:
            return jsonify({"error": "Invalid FIR ID"}), 400

    evidence_list = list(evidence_col.find(query).sort("uploaded_at", -1))
    for ev in evidence_list:
        ev["_id"] = str(ev["_id"])
        ev["file_id"] = str(ev.get("file_id", ""))
        if ev.get("case_id"):
            ev["case_id"] = str(ev["case_id"])
        if ev.get("fir_id"):
            ev["fir_id"] = str(ev["fir_id"])
        if ev.get("uploaded_at") and isinstance(ev["uploaded_at"], datetime):
            ev["uploaded_at"] = ev["uploaded_at"].isoformat()

    return jsonify(evidence_list), 200


@officer_bp.route("/evidence/<evidence_id>/file", methods=["GET"])
def download_evidence(evidence_id):
    """Download evidence file"""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        evidence = evidence_col.find_one({"_id": ObjectId(evidence_id)})
        if not evidence:
            return jsonify({"error": "Evidence not found"}), 404

        # Check access - officer must own the evidence or have access to the case/FIR
        officer_id = payload.get("user_id")
        if evidence.get("officer_id") != officer_id:
            # Check if officer has access to the case
            if evidence.get("case_id"):
                case = cases_col.find_one({"_id": evidence["case_id"]})
                if not case or str(case.get("assigned_to", "")) != officer_id:
                    return jsonify({"error": "Access denied"}), 403
            elif evidence.get("fir_id"):
                return jsonify({"error": "Access denied"}), 403

        # Retrieve file from GridFS
        file_id = evidence.get("file_id")
        if not file_id:
            return jsonify({"error": "File not found"}), 404

        if not fs:
            return jsonify({"error": "File storage not available"}), 500

        grid_file = fs.get(file_id)
        file_content = grid_file.read()

        from flask import Response
        return Response(
            file_content,
            mimetype=evidence.get("content_type", "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="{evidence.get("filename", "evidence")}"'
            }
        )

    except Exception as e:
        return jsonify({"error": f"Error retrieving file: {str(e)}"}), 500


@officer_bp.route("/evidence/<evidence_id>", methods=["DELETE"])
def delete_evidence(evidence_id):
    """Delete evidence"""
    payload = verify_token(request)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        evidence = evidence_col.find_one({"_id": ObjectId(evidence_id)})
        if not evidence:
            return jsonify({"error": "Evidence not found"}), 404

        # Check if officer owns the evidence
        officer_id = payload.get("user_id")
        if evidence.get("officer_id") != officer_id:
            return jsonify({"error": "Access denied"}), 403

        # Delete from GridFS
        file_id = evidence.get("file_id")
        if file_id and fs:
            try:
                fs.delete(file_id)
            except Exception:
                pass  # File might already be deleted

        # Delete metadata
        evidence_col.delete_one({"_id": ObjectId(evidence_id)})

        return jsonify({"message": "Evidence deleted successfully"}), 200

    except Exception:
        return jsonify({"error": "Invalid evidence ID"}), 400


