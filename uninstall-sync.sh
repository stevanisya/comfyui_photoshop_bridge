#!/bin/bash

PLIST_NAME="com.comfyui.photoshop.sync"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

launchctl unload "$PLIST_PATH" 2>/dev/null
rm -f "$PLIST_PATH"
echo "Sync agent removed."
