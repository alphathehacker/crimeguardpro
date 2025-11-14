from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, to_str_id

# -----------------------------
# USERS COLLECTION
# -----------------------------
users_col = db["users"]

# Create a new user (citizen/officer/admin)
def create_user(first_name, last_name, email, phone, password, role="citizen"):
    if users_col.find_one({"email": email.lower()}):
        return {"error": "Email already registered"}

    hashed_password = generate_password_hash(password)
    user_doc = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email.lower(),
        "phone": phone,
        "password_hash": hashed_password,
        "role": role,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    res = users_col.insert_one(user_doc)
    user_doc["_id"] = res.inserted_id
    return to_str_id(user_doc)

# Verify login credentials
def verify_user(email, password):
    user = users_col.find_one({"email": email.lower()})
    if user and check_password_hash(user["password_hash"], password):
        return to_str_id(user)
    return None

# Find user by ID
def get_user_by_id(user_id):
    user = users_col.find_one({"_id": ObjectId(user_id)})
    return to_str_id(user)

# Update user details
def update_user(user_id, updates):
    updates["updated_at"] = datetime.utcnow()
    res = users_col.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": updates},
        return_document=True
    )
    return to_str_id(res)

# Delete a user
def delete_user(user_id):
    users_col.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User deleted successfully"}
