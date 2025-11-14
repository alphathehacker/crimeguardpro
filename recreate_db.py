"""Script to recreate database tables with the correct schema"""
from app import app
from models import db
from models.user_model import User
from models.case_model import Case

print("=" * 60)
print("RECREATING DATABASE TABLES")
print("=" * 60)

with app.app_context():
    try:
        # Drop all tables
        print("[INFO] Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("[INFO] Creating tables with updated schema...")
        db.create_all()
        
        print("[OK] Database tables recreated successfully!")
        print("\n" + "=" * 60)
        print("You can now restart your Flask server:")
        print("  1. Stop the current server (Ctrl+C)")
        print("  2. Run: python app.py")
        print("  3. Test your routes in Postman")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Failed to recreate tables: {e}")
        import traceback
        traceback.print_exc()

