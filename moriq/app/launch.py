"""Opens MORIQ AI like a desktop app: starts the local server if needed, then opens its window."""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORT = int(os.environ.get('MORIQ_PORT', '5180'))
URL = f'http://127.0.0.1:{PORT}'
EDGE = (r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', r'C:\Program Files\Microsoft\Edge\Application\msedge.exe')
CHROME = (r'C:\Program Files\Google\Chrome\Application\chrome.exe',)


def running():
    try:
        with urllib.request.urlopen(f'{URL}/api/status', timeout=2) as response:
            return json.load(response).get('release_allowed') is False
    except (OSError, ValueError):
        return False


def start_server():
    python = Path(sys.executable)
    quiet = python.with_name('pythonw.exe')
    flags = subprocess.DETACHED_PROCESS if os.name == 'nt' else 0
    subprocess.Popen([str(quiet if quiet.exists() else python), '-m', 'moriq.app'], cwd=ROOT, creationflags=flags,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        if running():
            return True
        time.sleep(0.25)
    return False


def open_window():
    for path in (*EDGE, *CHROME, shutil.which('msedge'), shutil.which('chrome')):
        if path and Path(path).exists():
            subprocess.Popen([path, f'--app={URL}/#workspace'])
            return
    import webbrowser
    webbrowser.open(f'{URL}/#workspace')


def main():
    if not running() and not start_server():
        sys.exit('MORIQ AI could not start. Run start-moriq.bat to see why.')
    if '--no-window' not in sys.argv:
        open_window()


if __name__ == '__main__':
    main()
