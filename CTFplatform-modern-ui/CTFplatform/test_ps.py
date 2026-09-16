import psutil
found = False
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if p.info['cmdline'] and 'python' in p.info['cmdline'][0].lower():
            if any('13767' in arg or '13768' in arg for arg in p.info['cmdline']):
                print(f"Found running fallback process: PID {p.info['pid']} - {p.info['cmdline']}")
                found = True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
if not found:
    print('No native fallback processes running.')
