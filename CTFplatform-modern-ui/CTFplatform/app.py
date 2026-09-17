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
        return f"<h1>CRASH ON STARTUP</h1><pre>{err}</pre>", 500
