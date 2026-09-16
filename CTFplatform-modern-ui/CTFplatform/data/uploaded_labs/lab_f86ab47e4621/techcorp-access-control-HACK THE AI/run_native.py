
import sys
import os
import importlib.util

build_context = sys.argv[1]
host_port = int(sys.argv[2])
entry_path = sys.argv[3]

sys.path.insert(0, build_context)
sys.path.insert(0, os.path.dirname(entry_path))
os.chdir(build_context)

# Load the entry script directly by file path (rather than "import app"),
# so this works whether the Flask app lives at a top-level app.py or nested
# inside a package-like subdirectory (e.g. app/app.py). Loading it under a
# distinct module name (not "__main__") means any "if __name__ == '__main__'"
# block in the lab's own code is skipped, since we drive startup ourselves.
spec = importlib.util.spec_from_file_location("lab_app_entry", entry_path)
mod = importlib.util.module_from_spec(spec)
# Register in sys.modules before executing: Flask's own root-path detection
# (used to find the templates/static folders next to app.py) looks the
# module up by name in sys.modules, so this must happen first.
sys.modules["lab_app_entry"] = mod
spec.loader.exec_module(mod)

if not hasattr(mod, 'DB_PATH') or not os.path.exists(mod.DB_PATH):
    try:
        mod.init_db()
    except Exception:
        pass

mod.app.run(host='127.0.0.1', port=host_port, debug=False, use_reloader=False)
