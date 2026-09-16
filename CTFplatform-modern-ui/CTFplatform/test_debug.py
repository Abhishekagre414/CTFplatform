import subprocess, sys, os

build_context = r'C:\Users\ABHI\Desktop\CTFplatform\data\uploaded_labs\lab_f86ab47e4621\techcorp-access-control-HACK THE AI'
host_port = 15555

wrapper = f"""
import sys
import os
sys.path.insert(0, sys.argv[1])
os.chdir(sys.argv[1])
import app
if not hasattr(app, 'DB_PATH') or not os.path.exists(app.DB_PATH):
    try:
        app.init_db()
    except Exception as e:
        print('DB Init error:', e)
print("Starting app...", flush=True)
app.app.run(host="127.0.0.1", port=int(sys.argv[2]), debug=False, use_reloader=False)
"""

p = subprocess.Popen([sys.executable, "-c", wrapper, build_context, str(host_port)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
print("Waiting for output...")
for i in range(10):
    line = p.stdout.readline()
    if not line: break
    print(line.strip())
p.terminate()
