const { app } = require("photoshop");
const { storage } = require("uxp");
const { localFileSystem, formats } = storage;

const KEY_FILENAME     = "fal_api_key.txt";
const SETTINGS_FILENAME = "bridge_settings.json";
const TEMP_FOLDER_NAME = "temp_exports";
const MAX_AGE_MS       = 30 * 24 * 60 * 60 * 1000; // 30 days

let _keySource = "manual";

// ── On launch ─────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
    await loadSettings();
    await cleanupTempFolder();

    document.getElementById("fal-api-key").addEventListener("change", () => {
        _keySource = "manual";
        updateKeyBadge();
    });
    document.getElementById("upload-btn").addEventListener("click", uploadToFal);
    document.getElementById("copy-btn").addEventListener("click", copyUrl);
    document.getElementById("save-key-btn").addEventListener("click", saveSettingsToFile);
    document.getElementById("test-btn").addEventListener("click", testNetwork);
});

// ── Settings load/save ────────────────────────────────────────────────────────
async function loadSettings() {
    // 1. Try settings JSON in data folder
    try {
        const dataFolder = await localFileSystem.getDataFolder();
        const entry = await dataFolder.getEntry(SETTINGS_FILENAME);
        const text  = await entry.read({ format: formats.utf8 });
        const s = JSON.parse(text);
        if (s.falApiKey) {
            document.getElementById("fal-api-key").value = s.falApiKey;
            _keySource = "file";
        }
        if (s.comfyuiUrl) document.getElementById("comfyui-url").value = s.comfyuiUrl;
        updateKeyBadge();
        return;
    } catch (e) {}

    // 2. Try legacy fal_api_key.txt
    try {
        const dataFolder = await localFileSystem.getDataFolder();
        const entry = await dataFolder.getEntry(KEY_FILENAME);
        const key = (await entry.read({ format: formats.utf8 })).trim();
        if (key) { document.getElementById("fal-api-key").value = key; _keySource = "file"; }
        updateKeyBadge();
        return;
    } catch (e) {}

    // 3. Try plugin folder
    try {
        const pluginFolder = await localFileSystem.getPluginFolder();
        const entry = await pluginFolder.getEntry(KEY_FILENAME);
        const key = (await entry.read({ format: formats.utf8 })).trim();
        if (key) { document.getElementById("fal-api-key").value = key; _keySource = "file"; }
        updateKeyBadge();
        return;
    } catch (e) {}

    // 4. localStorage fallback
    try {
        const stored = JSON.parse(localStorage.getItem("bridge-settings") || "{}");
        if (stored.falApiKey) { document.getElementById("fal-api-key").value = stored.falApiKey; _keySource = "storage"; }
        if (stored.comfyuiUrl) document.getElementById("comfyui-url").value = stored.comfyuiUrl;
    } catch (e) {}

    updateKeyBadge();
}

function updateKeyBadge() {
    const badge    = document.getElementById("key-source-badge");
    const helpText = document.getElementById("key-help-text");
    if (_keySource === "file") {
        badge.textContent = "loaded from file";
        badge.className = "key-source-badge file";
        badge.style.display = "inline-block";
        helpText.textContent = "Settings loaded from file automatically.";
    } else if (_keySource === "storage") {
        badge.textContent = "loaded from storage";
        badge.className = "key-source-badge storage";
        badge.style.display = "inline-block";
        helpText.textContent = "Loaded from local storage. Click Save Settings to persist to file.";
    } else {
        badge.style.display = "none";
        helpText.textContent = "Enter your FAL API key and ComfyUI URL, then click Save Settings.";
    }
}

async function saveSettingsToFile() {
    const key        = document.getElementById("fal-api-key").value.trim();
    const comfyuiUrl = document.getElementById("comfyui-url").value.trim();
    const statusEl   = document.getElementById("save-key-status");

    const settings = { falApiKey: key, comfyuiUrl };

    try {
        const dataFolder = await localFileSystem.getDataFolder();
        const file = await dataFolder.createFile(SETTINGS_FILENAME, { overwrite: true });
        await file.write(JSON.stringify(settings), { format: formats.utf8 });
        localStorage.setItem("bridge-settings", JSON.stringify(settings));
        if (key) _keySource = "file";
        updateKeyBadge();
        statusEl.style.display = "block";
        statusEl.className = "status success";
        statusEl.textContent = "Settings saved — will auto-load on next launch.";
        setTimeout(() => { statusEl.style.display = "none"; }, 3000);
    } catch (e) {
        localStorage.setItem("bridge-settings", JSON.stringify(settings));
        if (key) _keySource = "storage";
        updateKeyBadge();
        statusEl.style.display = "block";
        statusEl.className = "status warning";
        statusEl.textContent = "Could not write file — saved to local storage instead.";
        setTimeout(() => { statusEl.style.display = "none"; }, 3000);
    }
}

function getComfyuiUrl() {
    let url = document.getElementById("comfyui-url").value.trim();
    return url.endsWith("/") ? url.slice(0, -1) : url;
}

// ── Temp folder helpers ────────────────────────────────────────────────────────
async function getTempFolder() {
    const dataFolder = await localFileSystem.getDataFolder();
    try {
        return await dataFolder.getEntry(TEMP_FOLDER_NAME);
    } catch (e) {
        return await dataFolder.createFolder(TEMP_FOLDER_NAME);
    }
}

async function cleanupTempFolder() {
    try {
        const tempFolder = await getTempFolder();
        const entries    = await tempFolder.getEntries();
        const now        = Date.now();
        for (const entry of entries) {
            const match = entry.name.match(/ps_export_(\d+)\.png$/);
            if (match && now - parseInt(match[1], 10) > MAX_AGE_MS) {
                try { await entry.delete(); } catch (e) {}
            }
        }
    } catch (e) {
        console.log("[Bridge] Temp folder cleanup skipped:", e.message);
    }
}

// ── UI helpers ─────────────────────────────────────────────────────────────────
function showStatus(type, message) {
    const el = document.getElementById("upload-status");
    el.className = "status " + type;
    el.textContent = message;
}

function copyUrl() {
    const url = document.getElementById("result-url").textContent;
    try {
        require("uxp").clipboard.copyText(url);
        const btn = document.getElementById("copy-btn");
        btn.textContent = "Copied!";
        btn.className = "button success";
        setTimeout(() => { btn.textContent = "Copy URL"; btn.className = "button secondary"; }, 2000);
    } catch (e) {
        console.log("Clipboard copy failed:", e);
    }
}

// ── Network test ──────────────────────────────────────────────────────────────
async function testNetwork() {
    const comfyUrl = getComfyuiUrl();
    if (!comfyUrl) {
        showStatus("error", "Enter a ComfyUI URL first.");
        return;
    }
    showStatus("info", "Testing connection to " + comfyUrl + "...");
    try {
        const xhr = new XMLHttpRequest();
        xhr.open("GET", comfyUrl + "/system_stats");
        xhr.onload = () => {
            showStatus("success", "ComfyUI reachable — HTTP " + xhr.status + ". Network is working.");
        };
        xhr.onerror = () => {
            showStatus("error", "Cannot reach ComfyUI at " + comfyUrl);
        };
        xhr.send();
    } catch (e) {
        showStatus("error", "Cannot reach ComfyUI at " + comfyUrl + ": " + e.message);
    }
}

// ── XHR helpers ────────────────────────────────────────────────────────────────
function xhrJson(method, url, body) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open(method, url);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                try { resolve(JSON.parse(xhr.responseText)); }
                catch (e) { resolve(xhr.responseText); }
            } else {
                reject(new Error("HTTP " + xhr.status + ": " + xhr.responseText));
            }
        };
        xhr.onerror = () => reject(new Error("Network request failed"));
        xhr.send(body ? JSON.stringify(body) : null);
    });
}

function xhrUploadImage(url, arrayBuffer, fileName) {
    return new Promise((resolve, reject) => {
        const blob = new Blob([arrayBuffer], { type: "image/png" });
        const form = new FormData();
        form.append("image", blob, fileName);
        form.append("overwrite", "true");

        const xhr = new XMLHttpRequest();
        xhr.open("POST", url);
        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                try { resolve(JSON.parse(xhr.responseText)); }
                catch (e) { resolve(xhr.responseText); }
            } else {
                reject(new Error("HTTP " + xhr.status + ": " + xhr.responseText));
            }
        };
        xhr.onerror = () => reject(new Error("Network request failed"));
        xhr.send(form);
    });
}

// ── Main upload flow ───────────────────────────────────────────────────────────
async function uploadToFal() {
    const btn      = document.getElementById("upload-btn");
    const apiKey   = document.getElementById("fal-api-key").value.trim();
    const comfyUrl = getComfyuiUrl();

    if (!apiKey) {
        showStatus("error", "No FAL API key. Enter one in Settings.");
        return;
    }
    if (!comfyUrl) {
        showStatus("error", "No ComfyUI URL. Enter your RunPod ComfyUI URL in Settings.");
        return;
    }

    const doc = app.activeDocument;
    if (!doc) {
        showStatus("error", "No active document in Photoshop.");
        return;
    }

    const exportType = document.querySelector("input[name='export-type']:checked").value;
    btn.disabled = true;
    document.getElementById("url-result").style.display = "none";

    try {
        // ── 1. Export from Photoshop to temp folder ───────────────────────────
        const timestamp = Date.now();
        const fileName  = "ps_export_" + timestamp + ".png";

        const tempFolder = await getTempFolder();
        const tempFile   = await tempFolder.createFile(fileName, { overwrite: true });

        showStatus("info", "Exporting from Photoshop...");

        const originalDocId = doc.id;
        const core = require("photoshop").core;

        await core.executeAsModal(async () => {
            const targetLayerName = (exportType === "layer" && app.activeDocument.activeLayers.length > 0)
                ? app.activeDocument.activeLayers[0].name : null;

            await app.batchPlay([{
                _obj: "duplicate",
                _target: [{ _ref: "document", _id: originalDocId }]
            }], {});

            const duplicateDoc = app.activeDocument;
            if (duplicateDoc.id === originalDocId) throw new Error("Duplicate document was not created properly.");

            if (targetLayerName) {
                try {
                    for (let i = 0; i < duplicateDoc.layers.length; i++) duplicateDoc.layers[i].visible = false;
                    let found = false;
                    function showTarget(layers) {
                        for (const l of layers) {
                            if (l.name === targetLayerName) { l.visible = true; found = true; return; }
                            if (l.layers) showTarget(l.layers);
                        }
                    }
                    showTarget(duplicateDoc.layers);
                    if (!found) for (let i = 0; i < duplicateDoc.layers.length; i++) duplicateDoc.layers[i].visible = true;
                } catch (e) { console.log("Could not isolate layer:", e.message); }
            }

            await app.batchPlay([{ _obj: "flattenImage" }], {});
            await duplicateDoc.saveAs.png(tempFile, { compression: 1, interlaced: false }, true);
            await duplicateDoc.close(require("photoshop").constants.SaveOptions.DONOTSAVECHANGES);
            await app.batchPlay([{ _obj: "select", _target: [{ _ref: "document", _id: originalDocId }] }], {});

        }, { commandName: "Export for ComfyUI" });

        // ── 2. Read exported file ─────────────────────────────────────────────
        showStatus("info", "Reading exported file...");
        const arrayBuffer = await tempFile.read({ format: formats.binary });

        // ── 3. Upload image to ComfyUI input folder ───────────────────────────
        showStatus("info", "Sending image to ComfyUI...");
        let uploadResult;
        try {
            uploadResult = await xhrUploadImage(comfyUrl + "/upload/image", arrayBuffer, fileName);
        } catch (e) {
            throw new Error("Could not reach ComfyUI at " + comfyUrl + ": " + e.message);
        }

        const uploadedName = uploadResult.name || fileName;

        // ── 4. Ask ComfyUI to upload to fal.ai server-side ───────────────────
        showStatus("info", "Uploading to Fal.ai via ComfyUI...");
        let falResult;
        try {
            falResult = await xhrJson("POST", comfyUrl + "/photoshop_bridge/fal_upload", {
                filename: uploadedName,
                fal_key: apiKey,
            });
        } catch (e) {
            throw new Error("Fal upload via ComfyUI failed: " + e.message);
        }

        if (falResult.error) throw new Error("Fal upload error: " + falResult.error);

        const fileUrl = falResult.url;
        if (!fileUrl) throw new Error("No URL returned from fal upload. Response: " + JSON.stringify(falResult));

        // ── 5. Show result ────────────────────────────────────────────────────
        document.getElementById("result-url").textContent = fileUrl;
        document.getElementById("url-result").style.display = "block";
        showStatus("success", "Uploaded! Copy the URL and paste it into the LoadImageFromURL node in ComfyUI.");

    } catch (error) {
        console.error("Upload error:", error);
        showStatus("error", error.message);
    } finally {
        btn.disabled = false;
    }
}
