console.log("Script loading...");

let app, storage, formats, localFileSystem;

try {
    app = require("photoshop").app;
    const uxpStorage = require("uxp").storage;
    storage = uxpStorage.storage;
    formats = uxpStorage.formats;
    localFileSystem = uxpStorage.localFileSystem;
    console.log("Modules loaded successfully");
} catch (error) {
    console.error("Error loading modules:", error);
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM ready - ComfyUI Bridge (RunPod) plugin loaded");
    try {
        setupEventListeners();
        loadSettings();
        console.log("Setup complete");
    } catch (error) {
        console.error("Setup error:", error);
        alert("Setup error: " + error.message);
    }
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

    const urlInput = document.getElementById("comfyui-url");
    if (urlInput) {
        urlInput.addEventListener("change", saveSettings);
        urlInput.addEventListener("blur", saveSettings);
    }
}

// Load settings
function loadSettings() {
    try {
        const settings = localStorage.getItem("comfyui-bridge-settings");
        if (settings) {
            const parsed = JSON.parse(settings);
            const urlInput = document.getElementById("comfyui-url");
            if (urlInput && parsed.comfyuiUrl) {
                urlInput.value = parsed.comfyuiUrl;
            }
        }
    } catch (e) {
        console.error("Error loading settings:", e);
    }
}

// Save settings
function saveSettings() {
    try {
        const urlInput = document.getElementById("comfyui-url");
        const settings = {
            comfyuiUrl: urlInput ? urlInput.value : "http://localhost:8190"
        };
        localStorage.setItem("comfyui-bridge-settings", JSON.stringify(settings));
    } catch (e) {
        console.error("Error saving settings:", e);
    }
}

// Get ComfyUI URL from input
function getComfyUIUrl() {
    const urlInput = document.getElementById("comfyui-url");
    let url = urlInput ? urlInput.value.trim() : "http://localhost:8190";

    // Remove trailing slash if present
    if (url.endsWith("/")) {
        url = url.slice(0, -1);
    }

    return url;
}

// Send image to ComfyUI
async function sendToComfyUI() {
    const sendBtn = document.getElementById("send-to-comfyui");

    try {
        sendBtn.disabled = true;
        showStatus("send-status", "info", "Checking document...");

        // Check if there's an active document
        if (!app.activeDocument) {
            throw new Error("No active document. Please open an image in Photoshop.");
        }

        const doc = app.activeDocument;
        const exportType = document.querySelector('input[name="export-type"]:checked')?.value || "layer";
        const layerName = exportType === "layer" && doc.activeLayers.length > 0
            ? doc.activeLayers[0].name
            : doc.name;

        showStatus("send-status", "info", "Exporting image...");

        // Get temp folder and create temp file
        const tempFolder = await localFileSystem.getTemporaryFolder();
        const tempFile = await tempFolder.createFile(`comfyui_export_${Date.now()}.png`, { overwrite: true });

        // Save as PNG to temp file
        await require("photoshop").action.batchPlay([
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

        // Get ComfyUI URL
        const comfyuiUrl = getComfyUIUrl();

        // Send to ComfyUI
        const response = await fetch(`${comfyuiUrl}/send_image`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                image_data: base64Data,
                layer_name: layerName,
                timestamp: new Date().toISOString()
            })
        });

        if (!response.ok) {
            const errorText = await response.text().catch(() => "Unknown error");
            throw new Error(`Server responded with ${response.status}: ${errorText}`);
        }

        const result = await response.json();
        showStatus("send-status", "success", `✓ Sent successfully! Image ID: ${result.image_id || "N/A"}`);

        // Clean up temp file
        await tempFile.delete();

    } catch (error) {
        console.error("Error sending to ComfyUI:", error);
        let errorMsg = error.message;

        // Provide helpful error messages
        if (errorMsg.includes("Failed to fetch") || errorMsg.includes("NetworkError")) {
            errorMsg = "Cannot connect to ComfyUI. Check:\n• URL is correct\n• ComfyUI is running\n• No firewall blocking";
        }

        showStatus("send-status", "error", `✗ Error: ${errorMsg}`);
    } finally {
        sendBtn.disabled = false;
    }
}

// Test connection to ComfyUI
async function testConnection() {
    const testBtn = document.getElementById("test-connection");
    const originalText = testBtn.textContent;

    try {
        testBtn.disabled = true;
        testBtn.textContent = "Testing...";
        showStatus("test-status", "info", "Connecting...");

        const comfyuiUrl = getComfyUIUrl();

        // Try to ping the status endpoint
        const response = await fetch(`${comfyuiUrl}/status`, {
            method: "GET",
            headers: {
                "Accept": "application/json"
            }
        });

        if (response.ok) {
            const data = await response.json().catch(() => ({}));
            showStatus("test-status", "success",
                `✓ Connected! Status: ${data.status || "running"}`);
            alert(`✓ Connection successful!\n\nComfyUI is reachable at:\n${comfyuiUrl}`);
        } else {
            throw new Error(`Server responded with status ${response.status}`);
        }
    } catch (error) {
        console.error("Connection test failed:", error);
        let errorMsg = error.message;

        if (errorMsg.includes("Failed to fetch") || errorMsg.includes("NetworkError")) {
            errorMsg = "Cannot reach ComfyUI server. Please check:\n\n" +
                "1. URL is correct\n" +
                "2. ComfyUI is running\n" +
                "3. RunPod instance is active\n" +
                "4. No firewall blocking the connection";
        }

        showStatus("test-status", "error", `✗ Connection failed`);
        alert(`✗ Connection Failed\n\n${errorMsg}`);
    } finally {
        testBtn.disabled = false;
        testBtn.textContent = originalText;
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
