import subprocess
import sys
import os

build_context = r'C:\Users\ABHI\Desktop\CTFplatform\data\uploaded_labs\lab_f86ab47e4621\techcorp-access-control-HACK THE AI'
host_port = 13769

wrapper = f"""
import sys
import os
sys.path.insert(0, r'{build_context}')
os.chdir(r'{build_context}')
import app
if not hasattr(app, 'DB_PATH') or not os.path.exists(app.DB_PATH):
    try:
        app.init_db()
    except:
        pass
app.app.run(host='127.0.0.1', port={host_port}, debug=False, use_reloader=False)
"""

p = subprocess.Popen([sys.executable, "-c", wrapper], cwd=build_context, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
stdout, stderr = p.communicate(timeout=5)
print('STDOUT:', stdout)
print('STDERR:', stderr)
print('RETURN CODE:', p.returncode)
