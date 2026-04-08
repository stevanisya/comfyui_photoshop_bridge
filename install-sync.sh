#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.comfyui.photoshop.sync"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
EXPORTS_DIR="$SCRIPT_DIR/exports"

mkdir -p "$EXPORTS_DIR"
mkdir -p "$HOME/Library/LaunchAgents"

# Unload if already running
launchctl unload "$PLIST_PATH" 2>/dev/null

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$SCRIPT_DIR/sync-to-pod.sh</string>
    </array>
    <key>WatchPaths</key>
    <array>
        <string>$EXPORTS_DIR</string>
    </array>
    <key>StandardOutPath</key>
    <string>/tmp/comfyui-sync.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/comfyui-sync.log</string>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH"
echo "Sync agent installed."
echo "It will auto-run rsync whenever files change in exports/"
echo "Logs: /tmp/comfyui-sync.log"
