"""
LifeDrop BD - Unified Live Production Runner
Runs local Django WSGI server on 0.0.0.0:8000 (accessible at http://127.0.0.1:8000)
and establishes Cloudflare HTTPS Quick Tunnel for instant worldwide public access.
"""

import subprocess
import sys
import re
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main():
    print("=" * 65)
    print("  LifeDrop BD — Starting Local Server & Cloudflare Live Tunnel")
    print("=" * 65)

    # 1. Start Django Server on 0.0.0.0:8000 (so 127.0.0.1:8000 works in browser!)
    django_cmd = [sys.executable, "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]
    print(f"[*] Starting Django Server at http://127.0.0.1:8000/ ...")
    django_proc = subprocess.Popen(
        django_cmd,
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Allow server to bind
    time.sleep(2)

    # 2. Start Cloudflare Tunnel
    cloudflared_exe = BASE_DIR / "cloudflared.exe"
    if not cloudflared_exe.exists():
        print(f"[!] Error: cloudflared.exe not found in {BASE_DIR}")
        sys.exit(1)

    cf_cmd = [str(cloudflared_exe), "tunnel", "--url", "http://127.0.0.1:8000"]
    print(f"[*] Starting Cloudflare Public Tunnel for port 8000 ...")
    cf_proc = subprocess.Popen(
        cf_cmd,
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')

    start_time = time.time()
    while time.time() - start_time < 30:
        line = cf_proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        print(f"[tunnel] {line.strip()}")
        match = url_pattern.search(line)
        if match:
            tunnel_url = match.group(0)
            break

    if tunnel_url:
        print("\n" + "=" * 65)
        print("  >>> SUCCESS! APPLICATION IS LIVE BOTH LOCALLY & GLOBALLY <<<")
        print(f"  Local Browser URL : http://127.0.0.1:8000/")
        print(f"  Public Internet URL: {tunnel_url}")
        print("=" * 65 + "\n")
        with open(BASE_DIR / "LIVE_URL.txt", "w") as f:
            f.write(tunnel_url + "\n")
    else:
        print("[!] Warning: Could not detect tunnel URL automatically within 30s.")

    # Keep both running
    try:
        while True:
            time.sleep(1)
            if django_proc.poll() is not None:
                print("[!] Django process terminated!")
                break
            if cf_proc.poll() is not None:
                print("[!] Cloudflared process terminated!")
                break
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        django_proc.terminate()
        cf_proc.terminate()

if __name__ == "__main__":
    main()
