import os
import sys
import subprocess

LOGS_DIR = 'logs'
LOG_FILE = os.path.join(LOGS_DIR, 'test_run.log')

os.makedirs(LOGS_DIR, exist_ok=True)

# Prefer virtualenv python if present
venv_python = os.path.join('.venv', 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join('.venv', 'bin', 'python')
if os.path.exists(venv_python):
    python = venv_python
else:
    python = sys.executable

print('Using python:', python)

cmd = [python, '-m', 'pytest', '-q']

# docker vs local: when running in container, python will be present; nothing special needed
with open(LOG_FILE, 'w') as f:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in process.stdout:
        sys.stdout.write(line)
        f.write(line)
    process.wait()

sys.exit(process.returncode)
