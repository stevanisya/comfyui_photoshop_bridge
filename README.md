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

### 1. SSH Key (one-time)

Generate an SSH key and add it to your RunPod account:

```bash
ssh-keygen -t ed25519 -C "runpod"
cat ~/.ssh/id_ed25519.pub
```

Paste the public key in **RunPod → Settings → SSH Public Keys**.

### 2. Pod Setup (each new pod)

Connect via proxied SSH:

```bash
ssh PODID@ssh.runpod.io -i ~/.ssh/id_ed25519
```

Then run:

```bash
ssh-keygen -A && service ssh start
mkdir -p ~/.ssh
echo "YOUR_PUBLIC_KEY" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
apt update && apt install -y rsync
```

### 3. Install ComfyUI Node (on the pod)

```bash
cd /workspace/ComfyUI/custom_nodes
git clone https://github.com/stevanisya/comfyui_photoshop_bridge.git
```

Restart ComfyUI. The **"Load from Photoshop"** node appears under **PhotoshopBridge**.

### 4. Install Sync Agent (on your Mac)

Edit `sync-to-pod.sh` — set `POD_IP` and `POD_PORT` from your pod's TCP SSH connection info.

Then install the background sync agent:

```bash
bash install-sync.sh
```

This registers a macOS launchd service that watches `exports/` and auto-syncs to RunPod whenever a file changes. No terminal needed.

To remove: `bash uninstall-sync.sh`

### 5. Photoshop Plugin

Load `photoshop_plugin/` in Photoshop via **Plugins → Development → Load Plugin**.

1. Click **Set Output Folder** → select the `exports/` folder in this repo
2. Choose **Active Layer** or **Full Document**
3. Click **Export to ComfyUI**

## Usage

1. Export from Photoshop (layer or document)
2. Sync triggers automatically in the background
3. In ComfyUI, select the file in the **Load from Photoshop** node and queue

Images older than 30 days are auto-cleaned from `exports/` on each sync.

## When You Start a New Pod

1. Run the pod setup commands (step 2)
2. Update `POD_IP` and `POD_PORT` in `sync-to-pod.sh`
3. Re-run `bash install-sync.sh`

## Logs

```bash
cat /tmp/comfyui-sync.log
```
