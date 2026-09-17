import traceback
import sys

try:
    from app_core import app
except Exception as e:
    from flask import Flask
    app = Flask(__name__)
    err = traceback.format_exc()
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        # Return 200 so Vercel renders this instead of its own 500 error page
        return f"<h1>CRASH ON STARTUP</h1><pre>{err}</pre>", 200

if __name__ == '__main__':
    try:
        from app_core import init_db
        with app.app_context():
            init_db()
    except Exception:
        pass
    
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
