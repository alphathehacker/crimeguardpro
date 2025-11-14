from bson import ObjectId
from datetime import datetime
from models import db, to_str_id

# -----------------------------
# CASES COLLECTION
# -----------------------------
cases_col = db["cases"]

# Create a new case
def create_case(citizen_id, title, description, category, location, status="Pending"):
    case_doc = {
        "citizen_id": ObjectId(citizen_id),
        "title": title,
        "description": description,
        "category": category,
        "location": location,
        "status": status,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res = cases_col.insert_one(case_doc)
    case_doc["_id"] = res.inserted_id
    return to_str_id(case_doc)

# Get all cases (with optional filters)
def get_all_cases(filter_data=None):
    query = filter_data or {}
    cur = cases_col.find(query)
    return [to_str_id(c) for c in cur]

# Get cases for a specific citizen
def get_cases_by_citizen(citizen_id):
    cur = cases_col.find({"citizen_id": ObjectId(citizen_id)})
    return [to_str_id(c) for c in cur]

# Get case by ID
def get_case_by_id(case_id):
    case = cases_col.find_one({"_id": ObjectId(case_id)})
    return to_str_id(case)

# Update case status or details
def update_case(case_id, updates):
    updates["updated_at"] = datetime.utcnow()
    res = cases_col.find_one_and_update(
        {"_id": ObjectId(case_id)},
        {"$set": updates},
        return_document=True
    )
    return to_str_id(res)

# Delete a case
def delete_case(case_id):
    """Delete a case by ID"""
    cases_col.delete_one({"_id": ObjectId(case_id)})
    return {"message": "Case deleted successfully"}
