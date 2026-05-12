#!/bin/bash
# serve.command — Double-click to start a local server.
# Phone (same WiFi) can then open the app via the printed URL.
#
# Stops the server with Ctrl+C in the Terminal window.

set -e
cd "$(dirname "$0")"

PORT=8080
APP_DIR="app"

# Get the Mac's primary LAN IP (works on macOS)
LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "127.0.0.1")

clear
echo "================================================================"
echo "  Powerball Predictor — Local Server"
echo "================================================================"
echo ""
echo "  On THIS Mac:  open http://localhost:$PORT/$APP_DIR/index.html"
echo ""
if [ "$LAN_IP" != "127.0.0.1" ]; then
  echo "  On your PHONE (same WiFi):"
  echo "    http://$LAN_IP:$PORT/$APP_DIR/index.html"
  echo ""
  echo "  Tip: in Safari on iPhone — tap Share → Add to Home Screen"
  echo "       to launch it like a native app."
else
  echo "  ! Could not detect LAN IP — make sure your Mac is on WiFi."
fi
echo ""
echo "================================================================"
echo "  Server is running. Press Ctrl+C in this window to stop it."
echo "================================================================"
echo ""

# Try to open the local URL in default browser after 1s
( sleep 1; open "http://localhost:$PORT/$APP_DIR/index.html" ) &

# Start server (Python 3 is preinstalled on every modern Mac)
python3 -m http.server $PORT --bind 0.0.0.0
