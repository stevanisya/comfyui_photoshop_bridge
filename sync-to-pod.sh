#!/bin/bash

LOCAL_DIR="$HOME/comfyui-inputs/"
REMOTE_DIR="/workspace/ComfyUI/input/photoshop_bridge/"
POD_IP="CHANGE_ME"
POD_PORT="CHANGE_ME"
SSH_KEY="$HOME/.ssh/id_ed25519"

RSYNC_OPTS="-rltz --progress --no-perms --no-owner --no-group"
SSH_CMD="ssh -p $POD_PORT -i $SSH_KEY"

# Create local folder if it doesn't exist
mkdir -p "$LOCAL_DIR"

echo "Watching $LOCAL_DIR for changes..."
echo "Syncing to $POD_IP:$POD_PORT -> $REMOTE_DIR"

# Initial sync
rsync $RSYNC_OPTS -e "$SSH_CMD" "$LOCAL_DIR" "root@$POD_IP:$REMOTE_DIR"

# Watch and sync on changes
fswatch -o "$LOCAL_DIR" | while read; do
    rsync $RSYNC_OPTS -e "$SSH_CMD" "$LOCAL_DIR" "root@$POD_IP:$REMOTE_DIR"
done
