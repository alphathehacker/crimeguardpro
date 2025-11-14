"""Test script to verify database connection is working"""
import sys

try:
    from app import app
    from models import db
    from models.user_model import User
    
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    
    with app.app_context():
        print("[OK] App context created successfully")
        print(f"[OK] DB instance: {id(db)}")
        print(f"[OK] User model loaded: {User}")
        
        # Test that we can query
        try:
            count = User.query.count()
            print(f"[OK] Database query successful! Total users: {count}")
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("DATABASE SETUP IS CORRECT!")
    print("=" * 60)
    print("\nYou can now restart your Flask server:")
    print("  1. Stop the current server (Ctrl+C)")
    print("  2. Run: python app.py")
    print("  3. Test your routes in Postman")
    print("=" * 60)
    
except Exception as e:
    print(f"[ERROR]: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

