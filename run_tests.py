import os
import sys
import subprocess

if sys.platform.startswith('win'):
    print('Detected Windows: running run_test.bat')
    subprocess.check_call(['cmd', '/c', 'run_test.bat'])
else:
    print('Detected POSIX: running run_test.sh')
    subprocess.check_call(['bash', 'run_test.sh'])
