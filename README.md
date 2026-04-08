# ComfyUI Photoshop Bridge

Export images from Photoshop directly into ComfyUI running on RunPod — no cloud uploads, just local files synced over SSH.

## How It Works

```
Photoshop Plugin → saves PNG to exports/
                        ↓
              fswatch + rsync (SSH)
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

Install fswatch:

```bash
brew install fswatch rsync
```

Edit `sync-to-pod.sh` — set `POD_IP` and `POD_PORT` to match your pod's TCP SSH info.

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

### 5. Start Syncing

```bash
bash sync-to-pod.sh
```

Files in `this repo's `exports/` folder` will auto-sync to `/workspace/ComfyUI/input/photoshop_bridge/` on your pod.

## Usage

1. Export from Photoshop (layer or document)
2. Sync script pushes the file to RunPod automatically
3. In ComfyUI, select the file in the **Load from Photoshop** node and queue the workflow
