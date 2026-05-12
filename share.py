#!/usr/bin/env python3
"""
share.py — One command to publish the app to a public URL.

What it does
------------
1. Starts a local HTTP server on port 8080 serving the app/ folder.
2. Starts a Cloudflare Quick Tunnel that exposes that server publicly
   via a URL like https://wandering-anchor-1234.trycloudflare.com.
3. Prints the public URL — you share that link with anyone, on any
   device, on any network. They open it in any browser, including
   iPhone Safari, where they can "Add to Home Screen" to install
   the PWA.
4. Press Ctrl+C to stop sharing — the URL goes offline.

No account, no signup, no payment. Cloudflare's Quick Tunnel is free
and anonymous. The URL is temporary (changes every run); for a
permanent URL, see the deploy section in README.md.

Auto-installs cloudflared if missing (via Homebrew on macOS, direct
binary download otherwise).
"""

import os
import sys
import shutil
import subprocess
import threading
import time
import socket
import socketserver
import http.server
import urllib.request
import re

PORT = 8080
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)


# ---------- HTTP server ----------
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("0.0.0.0", PORT), QuietHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


# ---------- cloudflared discovery / install ----------
def cloudflared_path():
    p = shutil.which("cloudflared")
    if p: return p
    # Common install locations
    for c in ["/opt/homebrew/bin/cloudflared",
              "/usr/local/bin/cloudflared",
              os.path.expanduser("~/.local/bin/cloudflared")]:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def install_cloudflared():
    print("→ cloudflared not found. Installing…")
    if shutil.which("brew"):
        print("  using Homebrew")
        try:
            subprocess.run(["brew", "install", "cloudflared"], check=True)
            return cloudflared_path()
        except subprocess.CalledProcessError:
            pass
    # Fallback: download binary directly
    print("  downloading binary…")
    import platform
    sys_name = platform.system().lower()
    arch = platform.machine().lower()
    if sys_name == "darwin":
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
    elif sys_name == "linux":
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    else:
        print("✗ Auto-install only supports macOS/Linux. Install cloudflared manually: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
        return None
    dest_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "cloudflared")
    if url.endswith(".tgz"):
        import tarfile, tempfile
        tmp = tempfile.mktemp(suffix=".tgz")
        urllib.request.urlretrieve(url, tmp)
        with tarfile.open(tmp) as tar:
            for m in tar.getmembers():
                if m.name.endswith("cloudflared"):
                    m.name = "cloudflared"
                    tar.extract(m, dest_dir)
                    break
        os.remove(tmp)
    else:
        urllib.request.urlretrieve(url, dest)
    os.chmod(dest, 0o755)
    print(f"  installed to {dest}")
    return dest


# ---------- LAN IP ----------
def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 53))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return "127.0.0.1"


# ---------- Main ----------
def main():
    cf = cloudflared_path()
    if not cf:
        cf = install_cloudflared()
    if not cf:
        sys.exit(1)

    print("=" * 68)
    print("  Powerball Predictor — Public Share")
    print("=" * 68)
    print(f"  Local:  http://localhost:{PORT}/app/index.html")
    print(f"  LAN:    http://{lan_ip()}:{PORT}/app/index.html  (same WiFi only)")
    print(f"  Public: starting Cloudflare tunnel…")
    print()

    httpd = start_server()

    # Start cloudflared
    proc = subprocess.Popen(
        [cf, "tunnel", "--no-autoupdate", "--url", f"http://localhost:{PORT}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )

    url_pattern = re.compile(r"(https://[a-zA-Z0-9-]+\.trycloudflare\.com)")
    public_url = None
    try:
        for line in proc.stdout:
            # Forward concise progress
            if "trycloudflare.com" in line and not public_url:
                m = url_pattern.search(line)
                if m:
                    public_url = m.group(1)
                    full = f"{public_url}/app/index.html"
                    print("=" * 68)
                    print(f"  🌍 PUBLIC URL — share this:")
                    print()
                    print(f"     {full}")
                    print()
                    print(f"     (Works on any device, any network. Open in any browser.)")
                    print(f"     On iPhone Safari: Share → Add to Home Screen for app icon.")
                    print()
                    print("=" * 68)
                    print("  Press Ctrl+C to stop sharing.")
                    print("=" * 68)
                    # QR code: render in terminal if qrcode is available
                    try:
                        import qrcode
                        qr = qrcode.QRCode(border=1)
                        qr.add_data(full)
                        qr.make()
                        qr.print_ascii(invert=True)
                    except ImportError:
                        print()
                        print("  Tip: pip3 install qrcode  →  next run prints a scannable QR code")
                        print()
            elif "ERR" in line or "failed" in line.lower():
                print(f"  ! {line.strip()}")
    except KeyboardInterrupt:
        print("\n\nStopping…")
    finally:
        proc.terminate()
        httpd.shutdown()
        print("Stopped.")


if __name__ == "__main__":
    main()
