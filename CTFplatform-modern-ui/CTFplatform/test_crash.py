import subprocess, sys, os

wrapper = """
import sys, traceback
try:
    build_context = sys.argv[1]
    host_port = int(sys.argv[2])
    sys.path.insert(0, build_context)
    import os
    os.chdir(build_context)
    import app
    if not hasattr(app, "DB_PATH") or not os.path.exists(app.DB_PATH):
        try: app.init_db()
        except Exception as e: pass
    app.app.run(host="127.0.0.1", port=host_port, debug=False, use_reloader=False)
except Exception as e:
    with open("crash.txt", "w") as f:
        traceback.print_exc(file=f)
"""

env = os.environ.copy()
env.pop('WERKZEUG_SERVER_FD', None)
env.pop('WERKZEUG_RUN_MAIN', None)
build_context = r'C:\Users\ABHI\Desktop\CTFplatform\data\uploaded_labs\lab_f86ab47e4621\techcorp-access-control-HACK THE AI'

p = subprocess.Popen([sys.executable, '-c', wrapper, build_context, '15555'], cwd=build_context, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
print('Started', p.pid)
