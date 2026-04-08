const { app, core, constants } = require("photoshop");
const { storage } = require("uxp");
const { localFileSystem, formats } = storage;

const SETTINGS_FILE = "bridge_settings.json";
let outputFolder = null;

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
    await loadSettings();
    document.getElementById("set-folder-btn").addEventListener("click", setOutputFolder);
    document.getElementById("export-btn").addEventListener("click", exportImage);
});

// ── Settings ─────────────────────────────────────────────────────────────────
async function loadSettings() {
    try {
        const dataFolder = await localFileSystem.getDataFolder();
        const entry = await dataFolder.getEntry(SETTINGS_FILE);
        const text = await entry.read({ format: formats.utf8 });
        const settings = JSON.parse(text);

        if (settings.folderToken) {
            outputFolder = await localFileSystem.getEntryForPersistentToken(settings.folderToken);
            document.getElementById("folder-path").textContent = outputFolder.nativePath;
        }
    } catch (e) {
        // No settings yet or folder no longer accessible
        document.getElementById("folder-path").textContent = "Not set — click below to choose";
    }
}

async function saveSettings(folderToken) {
    try {
        const dataFolder = await localFileSystem.getDataFolder();
        const file = await dataFolder.createFile(SETTINGS_FILE, { overwrite: true });
        await file.write(JSON.stringify({ folderToken }), { format: formats.utf8 });
    } catch (e) {
        console.error("[Bridge] Could not save settings:", e);
    }
}

// ── Folder picker ────────────────────────────────────────────────────────────
async function setOutputFolder() {
    try {
        const folder = await localFileSystem.getFolder();
        if (!folder) return;

        const token = await localFileSystem.createPersistentToken(folder);
        outputFolder = folder;

        await saveSettings(token);
        document.getElementById("folder-path").textContent = folder.nativePath;
        showStatus("success", "Output folder set!");
    } catch (e) {
        showStatus("error", "Could not set folder: " + e.message);
    }
}

// ── Export ────────────────────────────────────────────────────────────────────
async function exportImage() {
    const doc = app.activeDocument;
    if (!doc) {
        showStatus("error", "No document open.");
        return;
    }
    if (!outputFolder) {
        showStatus("error", "Set an output folder first.");
        return;
    }

    const exportType = document.querySelector("input[name='export-type']:checked").value;
    const btn = document.getElementById("export-btn");
    btn.disabled = true;

    try {
        const filename = exportType === "layer" ? "ps_layer.png" : "ps_document.png";
        const file = await outputFolder.createFile(filename, { overwrite: true });

        showStatus("info", "Exporting...");

        const originalDocId = doc.id;

        await core.executeAsModal(async () => {
            const targetLayerName =
                exportType === "layer" && app.activeDocument.activeLayers.length > 0
                    ? app.activeDocument.activeLayers[0].name
                    : null;

            // Duplicate document
            await app.batchPlay(
                [{ _obj: "duplicate", _target: [{ _ref: "document", _id: originalDocId }] }],
                {}
            );

            const dupDoc = app.activeDocument;
            if (dupDoc.id === originalDocId) throw new Error("Duplicate failed.");

            // Isolate target layer if exporting a single layer
            if (targetLayerName) {
                try {
                    for (const layer of dupDoc.layers) layer.visible = false;
                    let found = false;
                    function showTarget(layers) {
                        for (const l of layers) {
                            if (l.name === targetLayerName) {
                                l.visible = true;
                                found = true;
                                return;
                            }
                            if (l.layers) showTarget(l.layers);
                        }
                    }
                    showTarget(dupDoc.layers);
                    if (!found) {
                        for (const layer of dupDoc.layers) layer.visible = true;
                    }
                } catch (e) {
                    console.log("[Bridge] Could not isolate layer:", e.message);
                }
            }

            // Flatten and save
            await app.batchPlay([{ _obj: "flattenImage" }], {});
            await dupDoc.saveAs.png(file, { compression: 6, interlaced: false }, true);
            await dupDoc.close(constants.SaveOptions.DONOTSAVECHANGES);

            // Return focus to original document
            await app.batchPlay(
                [{ _obj: "select", _target: [{ _ref: "document", _id: originalDocId }] }],
                {}
            );
        }, { commandName: "Export for ComfyUI" });

        showStatus("success", "Exported " + filename);
    } catch (e) {
        showStatus("error", e.message);
    } finally {
        btn.disabled = false;
    }
}

// ── UI helpers ───────────────────────────────────────────────────────────────
function showStatus(type, message) {
    const el = document.getElementById("status");
    el.className = "status " + type;
    el.textContent = message;
}
