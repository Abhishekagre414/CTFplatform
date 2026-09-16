import subprocess, sys
wrapper = '''
print("Hello world")
'''
try:
    p = subprocess.Popen([sys.executable, '-c', wrapper], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    print("SUCCESS", p.pid)
except Exception as e:
    print('Failed:', e)
