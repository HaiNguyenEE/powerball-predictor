#!/usr/bin/env python3
"""
serve.py — Start a local HTTP server so the app works on phones (same WiFi).

Usage:
    python3 serve.py            # default port 8080
    python3 serve.py 9000       # custom port

The script:
  - Serves the entire PowerPoint folder over HTTP on 0.0.0.0
  - Prints the local IP so you can open it from your phone
  - Opens the app in your Mac's default browser
  - Stops when you press Ctrl+C

Tip: on iPhone Safari, after opening the URL, tap Share → Add to Home Screen
     to launch it like a native app (full-screen, app icon).
"""
import sys
import os
import socket
import threading
import time
import webbrowser
import http.server
import socketserver

PORT = 8080
if len(sys.argv) > 1:
    try: PORT = int(sys.argv[1])
    except: pass

APP_DIR = "app"
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)


def lan_ip():
    """Get the Mac's primary LAN IP without external calls."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 53))   # no traffic — just resolves which iface
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Suppress per-request noise — only show errors
        if "200" not in (args[1] if len(args)>1 else ""):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt%args))


def main():
    ip = lan_ip()
    url_local = f"http://localhost:{PORT}/{APP_DIR}/index.html"
    url_lan   = f"http://{ip}:{PORT}/{APP_DIR}/index.html"

    print("=" * 64)
    print("  Powerball Predictor — Local Server")
    print("=" * 64)
    print()
    print(f"  On THIS Mac:    {url_local}")
    if ip != "127.0.0.1":
        print(f"  On your PHONE:  {url_lan}")
        print(f"  (must be on the same WiFi as this Mac)")
        print()
        print(f"  Tip on iPhone: open in Safari, then Share → Add to Home Screen.")
    print()
    print("=" * 64)
    print("  Server running. Press Ctrl+C to stop.")
    print("=" * 64)
    print()

    # Open local URL after a brief delay
    def open_local():
        time.sleep(1)
        try: webbrowser.open(url_local)
        except: pass
    threading.Thread(target=open_local, daemon=True).start()

    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), QuietHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n✗ Port {PORT} already in use. Try: python3 serve.py 9000")
        else:
            raise


if __name__ == "__main__":
    main()
