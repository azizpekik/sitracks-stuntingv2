#!/usr/bin/env python3
"""
Robust app wrapper for Railway deployment with comprehensive error handling
"""
import os
import sys
import traceback

def main():
    try:
        print("=== Railway App Starting ===")
        print(f"Python executable: {sys.executable}")
        print(f"Python version: {sys.version}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Environment variables:")
        for key, value in os.environ.items():
            if not key.startswith('_'):
                print(f"  {key}: {value}")

        print("\n=== Importing Flask app ===")
        from app import app
        print("✅ Flask app imported successfully")

        # Test app configuration
        print(f"App debug mode: {app.debug}")
        print(f"App secret key configured: {'SECRET_KEY' in app.config}")

        print("\n=== Starting Flask server ===")
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')

        print(f"Starting on {host}:{port}")

        # Run with explicit configuration
        app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Application Error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()