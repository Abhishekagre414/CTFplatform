
import sys
import os
sys.path.insert(0, r"C:\Users\ABHI\Desktop\CTFplatform\data\uploaded_labs\lab_f86ab47e4621\techcorp-access-control-HACK THE AI")
os.chdir(r"C:\Users\ABHI\Desktop\CTFplatform\data\uploaded_labs\lab_f86ab47e4621\techcorp-access-control-HACK THE AI")
import app
if not hasattr(app, "DB_PATH") or not os.path.exists(app.DB_PATH):
    try:
        app.init_db()
    except:
        pass
app.app.run(host="127.0.0.1", port=13768, debug=False, use_reloader=False)
