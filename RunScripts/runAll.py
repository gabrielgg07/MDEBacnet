import subprocess
import os
import signal
import sys
import time

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

commands = [
    ["python3", os.path.join(BASE, "PPF/PPFServer.py")],
    ["python3", os.path.join(BASE, "padADriver/PadAListener.py")],
    ["python3", os.path.join(BASE, "padADriver/PadAServer.py")],
]

procs = []

def shutdown(signum, frame):
    print("\n🛑 Shutting down all subprocesses...")
    for p in procs:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGINT)
        except Exception:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

for cmd in commands:
    p = subprocess.Popen(
        cmd,
        preexec_fn=os.setsid   # 🔑 creates new process group
    )
    procs.append(p)

print("🚀 All services running. Press Ctrl-C to stop.")

# Keep parent alive
while True:
    time.sleep(1)
