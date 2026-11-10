"""
LifeDrop BD - Unified Live Production Runner
Runs local Django WSGI server on port 8080 and establishes Cloudflare HTTPS Quick Tunnel.
"""

import subprocess
import sys
import re
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main():
    print("=" * 60)
    print("  Starting LifeDrop BD Live Server & Cloudflare Tunnel")
    print("=" * 60)

    # 1. Start Django Server on 127.0.0.1:8080
    django_cmd = [sys.executable, "manage.py", "runserver", "127.0.0.1:8080", "--noreload"]
    print(f"Launching Django: {' '.join(django_cmd)}")
    django_proc = subprocess.Popen(
        django_cmd,
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Give Django a couple seconds to bind
    time.sleep(2)

    # 2. Launch cloudflared tunnel
    cloudflared_exe = BASE_DIR / "cloudflared.exe"
    if not cloudflared_exe.exists():
        print(f"Error: {cloudflared_exe} not found!")
        sys.exit(1)

    cf_cmd = [str(cloudflared_exe), "tunnel", "--url", "http://127.0.0.1:8080"]
    print(f"Launching Cloudflare Tunnel: {' '.join(cf_cmd)}")
    cf_proc = subprocess.Popen(
        cf_cmd,
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Read output and detect the https://*.trycloudflare.com URL
    tunnel_url = None
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')

    start_time = time.time()
    while time.time() - start_time < 30:
        line = cf_proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        print(f"[cloudflared] {line.strip()}")
        match = url_pattern.search(line)
        if match:
            tunnel_url = match.group(0)
            break

    if tunnel_url:
        print("\n" + "=" * 60)
        print(f"  >>> SUCCESS: LIFEDROP BD IS LIVE ONLINE! <<<")
        print(f"  Public Live URL: {tunnel_url}")
        print("=" * 60 + "\n")
        with open(BASE_DIR / "LIVE_URL.txt", "w") as f:
            f.write(tunnel_url + "\n")
    else:
        print("Warning: Could not automatically parse Cloudflare tunnel URL within 30 seconds.")

    # Keep both running indefinitely
    try:
        while True:
            time.sleep(1)
            if django_proc.poll() is not None:
                print("Django process exited unexpectedly!")
                break
            if cf_proc.poll() is not None:
                print("Cloudflared process exited unexpectedly!")
                break
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        django_proc.terminate()
        cf_proc.terminate()

if __name__ == "__main__":
    main()
