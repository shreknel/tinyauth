#!/bin/bash
# Launch Chrome from host (not in container)
# This script should be run on your host machine

set -e

echo "Launching Chrome for OIDC test setup..."

# Detect Chrome
if command -v google-chrome &> /dev/null; then
    CHROME_CMD="google-chrome"
elif command -v chromium-browser &> /dev/null; then
    CHROME_CMD="chromium-browser"
elif command -v chromium &> /dev/null; then
    CHROME_CMD="chromium"
elif [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    CHROME_CMD="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else
    echo "Error: Chrome not found. Please install Google Chrome or Chromium."
    exit 1
fi

echo "Using: $CHROME_CMD"
echo "Opening: http://client.aande.top/ (OIDC test client)"
echo ""

$CHROME_CMD \
    --host-resolver-rules="MAP auth.aande.top 127.0.0.1, MAP client.aande.top 127.0.0.1" \
    --disable-features=HttpsOnlyMode \
    --unsafely-treat-insecure-origin-as-secure=http://auth.aande.top,http://client.aande.top \
    --user-data-dir=/tmp/chrome-test-profile-$(date +%s) \
    --new-window \
    http://client.aande.top/ \
    > /dev/null 2>&1 &

echo "Chrome launched!"
echo "OIDC test client: http://client.aande.top/"
echo "Tinyauth: http://auth.aande.top/"

