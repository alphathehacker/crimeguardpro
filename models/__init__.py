from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/crime_management_db"))
db = client.get_database()  # automatically selects db from URI

# Helper to convert ObjectId -> string
def to_str_id(doc):
    """Convert all ObjectId fields in a MongoDB document to strings recursively."""
    if not doc:
        return None
    doc = dict(doc)
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, list):
            doc[k] = [to_str_id(i) if isinstance(i, dict) else (str(i) if isinstance(i, ObjectId) else i) for i in v]
        elif isinstance(v, dict):
            doc[k] = to_str_id(v)
    return doc
