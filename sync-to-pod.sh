#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_DIR="$SCRIPT_DIR/exports/"
REMOTE_DIR="/workspace/ComfyUI/input/photoshop_bridge/"
POD_IP="CHANGE_ME"
POD_PORT="CHANGE_ME"
SSH_KEY="$HOME/.ssh/id_ed25519"

RSYNC_OPTS="-rltz --no-perms --no-owner --no-group"
SSH_CMD="ssh -p $POD_PORT -i $SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no"

mkdir -p "$LOCAL_DIR"

# Cleanup images older than 30 days
find "$LOCAL_DIR" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.webp" \) -mtime +30 -delete 2>/dev/null

# Sync to pod
rsync $RSYNC_OPTS -e "$SSH_CMD" "$LOCAL_DIR" "root@$POD_IP:$REMOTE_DIR"
