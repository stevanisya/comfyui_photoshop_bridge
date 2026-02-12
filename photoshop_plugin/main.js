const { app } = require("photoshop");
const { storage, formats } = require("uxp").storage;
const { localFileSystem } = storage;

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    console.log("ComfyUI Bridge plugin loaded");
    setupEventListeners();
    loadSettings();
});

// Setup event listeners
function setupEventListeners() {
    const sendBtn = document.getElementById("send-to-comfyui");
    if (sendBtn) {
        sendBtn.addEventListener("click", sendToComfyUI);
    }

    const testBtn = document.getElementById("test-connection");
    if (testBtn) {
        testBtn.addEventListener("click", testConnection);
    }

    const toggleServerBtn = document.getElementById("toggle-server");
    if (toggleServerBtn) {
        toggleServerBtn.addEventListener("click", () => {
            showStatus("receive-status", "info", "Server functionality coming soon!");
        });
    }
}

// Load settings
function loadSettings() {
    try {
        const settings = localStorage.getItem("comfyui-bridge-settings");
        if (settings) {
            const parsed = JSON.parse(settings);
            const portInput = document.getElementById("comfyui-port");
            if (portInput) portInput.value = parsed.comfyuiPort || 8190;
        }
    } catch (e) {
        console.error("Error loading settings:", e);
    }
}

// Save settings
function saveSettings() {
    try {
        const portInput = document.getElementById("comfyui-port");
        const settings = {
            comfyuiPort: portInput ? portInput.value : 8190
        };
        localStorage.setItem("comfyui-bridge-settings", JSON.stringify(settings));
    } catch (e) {
        console.error("Error saving settings:", e);
    }
}

// Send image to ComfyUI
async function sendToComfyUI() {
    const statusEl = document.getElementById("send-status");
    const sendBtn = document.getElementById("send-to-comfyui");

    try {
        sendBtn.disabled = true;
        showStatus("send-status", "info", "Checking document...");

        // Check if there's an active document
        if (!app.activeDocument) {
            throw new Error("No active document. Please open an image in Photoshop.");
        }

        const doc = app.activeDocument;
        const layerName = doc.activeLayers.length > 0 ? doc.activeLayers[0].name : "Document";

        showStatus("send-status", "info", "Exporting image...");

        // Get temp folder and create temp file
        const tempFolder = await localFileSystem.getTemporaryFolder();
        const tempFile = await tempFolder.createFile(`comfyui_export_${Date.now()}.png`, { overwrite: true });

        // Save document as PNG to temp file
        const saveResult = await require("photoshop").action.batchPlay([
            {
                _obj: "exportDocument",
                _target: [{ _ref: "document", _id: doc.id }],
                exportIn: { _path: tempFile.nativePath, _kind: "local" },
                exportAs: { _obj: "PNGFormat" },
                copy: true
            }
        ], {});

        showStatus("send-status", "info", "Reading file...");

        // Read the file as binary
        const fileData = await tempFile.read({ format: formats.binary });

        // Convert to base64
        const base64Data = arrayBufferToBase64(fileData);

        showStatus("send-status", "info", "Sending to ComfyUI...");

        // Send to ComfyUI
        const port = document.getElementById("comfyui-port").value || 8190;
        const response = await fetch(`http://localhost:${port}/send_image`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                image_data: base64Data,
                layer_name: layerName,
                timestamp: new Date().toISOString()
            })
        });

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }

        const result = await response.json();
        showStatus("send-status", "success", `✓ Sent successfully! Image ID: ${result.image_id}`);

        // Clean up temp file
        await tempFile.delete();

    } catch (error) {
        console.error("Error sending to ComfyUI:", error);
        showStatus("send-status", "error", `✗ Error: ${error.message}`);
    } finally {
        sendBtn.disabled = false;
    }
}

// Test connection to ComfyUI
async function testConnection() {
    const testBtn = document.getElementById("test-connection");

    try {
        testBtn.disabled = true;
        testBtn.textContent = "Testing...";

        const port = document.getElementById("comfyui-port").value || 8190;
        const response = await fetch(`http://localhost:${port}/status`, {
            method: "GET"
        });

        if (response.ok) {
            const data = await response.json();
            alert(`✓ Connection successful!\n\nComfyUI Bridge is ${data.status}\nReceived images: ${data.received_images_count}`);
        } else {
            alert(`✗ Connection failed!\n\nServer responded with status ${response.status}`);
        }
    } catch (error) {
        alert(`✗ Connection failed!\n\n${error.message}\n\nMake sure ComfyUI is running and the bridge node is loaded.`);
    } finally {
        testBtn.disabled = false;
        testBtn.textContent = "Test Connection";
    }
}

// Convert ArrayBuffer to base64
function arrayBufferToBase64(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

// Show status message
function showStatus(elementId, type, message) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.className = `status ${type}`;
    element.textContent = message;
    element.style.display = "block";

    if (type === "success") {
        setTimeout(() => {
            element.style.display = "none";
        }, 5000);
    }
}
