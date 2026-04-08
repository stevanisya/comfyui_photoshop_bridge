# ComfyUI Photoshop Bridge

Export images from Photoshop directly into ComfyUI running on RunPod — no cloud uploads, just local files synced over SSH.

## How It Works

```
Photoshop Plugin → saves PNG to exports/
                        ↓
            macOS launchd + rsync (SSH)
          (auto-triggers on file change)
                        ↓
RunPod: /workspace/ComfyUI/input/photoshop_bridge/
                        ↓
         ComfyUI "Load from Photoshop" node
```

## Setup

### 1. SSH & Sync (one-time)

Generate an SSH key and add it to your RunPod account:

```bash
ssh-keygen -t ed25519 -C "runpod"
cat ~/.ssh/id_ed25519.pub
# Paste in RunPod → Settings → SSH Public Keys
```

Edit `sync-to-pod.sh` — set `POD_IP` and `POD_PORT` to match your pod's TCP SSH info.

Install the background sync agent:

```bash
bash install-sync.sh
```

This registers a macOS launchd agent that auto-runs rsync whenever files change in `exports/`. No terminal needed — it runs silently in the background.

To remove it later: `bash uninstall-sync.sh`

### 2. Pod Setup (each new pod)

Connect via proxied SSH and run:

```bash
ssh-keygen -A && service ssh start
mkdir -p ~/.ssh
echo "YOUR_PUBLIC_KEY" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
apt update && apt install -y rsync
```

### 3. ComfyUI Node

Clone this repo into your ComfyUI custom nodes on the pod:

```bash
cd /workspace/ComfyUI/custom_nodes
git clone https://github.com/stevanisya/comfyui_photoshop_bridge.git
```

Restart ComfyUI. The **"Load from Photoshop"** node will appear under the **PhotoshopBridge** category.

### 4. Photoshop Plugin

Load the `photoshop_plugin/` folder in Photoshop via **Plugins → Development → Load Plugin**.

1. Click **Set Output Folder** and select `this repo's `exports/` folder`
2. Choose **Active Layer** or **Full Document**
3. Click **Export to ComfyUI**

## Usage

1. Export from Photoshop (layer or document)
2. Sync triggers automatically in the background
3. In ComfyUI, select the file in the **Load from Photoshop** node and queue the workflow

Images older than 30 days are auto-cleaned from `exports/` on each sync.

Logs: `cat /tmp/comfyui-sync.log`
