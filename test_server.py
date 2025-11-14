"""Quick test script to verify the Flask server and routes are working"""
import sys

try:
    from app import app
    
    print("=" * 60)
    print("FLASK SERVER ROUTE TEST")
    print("=" * 60)
    print(f"\n[OK] App loaded successfully")
    
    # Test route registration
    rules = list(app.url_map.iter_rules())
    api_routes = [r for r in rules if r.rule == '/api/routes']
    
    if api_routes:
        route = api_routes[0]
        print(f"[OK] Route /api/routes is registered")
        print(f"  Methods: {list(route.methods)}")
    else:
        print("[ERROR] Route /api/routes NOT FOUND")
    
    print(f"\nTotal routes registered: {len([r for r in rules if r.endpoint != 'static'])}")
    
    print("\n" + "=" * 60)
    print("TO START THE SERVER:")
    print("=" * 60)
    print("Run: python app.py")
    print("Then test: http://127.0.0.1:5000/api/routes")
    print("=" * 60)
    
except Exception as e:
    print(f"[ERROR]: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

