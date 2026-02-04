// Scrivener to Obsidian Converter - Frontend

const scrivPathInput = document.getElementById('scriv-path');
const outputPathInput = document.getElementById('output-path');
const selectScrivBtn = document.getElementById('select-scriv');
const selectOutputBtn = document.getElementById('select-output');
const convertBtn = document.getElementById('convert-btn');
const statusDiv = document.getElementById('status');

// Update convert button state
function updateConvertButton() {
    convertBtn.disabled = !scrivPathInput.value || !outputPathInput.value;
}

// Show status message
function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
}

// Hide status
function hideStatus() {
    statusDiv.className = 'status hidden';
}

// Unfortunately, browsers can't give us folder paths directly.
// We need to prompt the user to enter the path manually.
// In a real desktop app (Electron/Tauri), we'd use native dialogs.

selectScrivBtn.addEventListener('click', () => {
    const path = prompt(
        'Enter the full path to your Scrivener project:\n\n' +
        'Example: /Users/yourname/Documents/My Novel.scriv\n\n' +
        'Tip: In Finder, right-click the .scriv file, hold Option, and click "Copy as Pathname"'
    );
    if (path) {
        scrivPathInput.value = path.trim();
        updateConvertButton();

        // Auto-suggest output path
        if (!outputPathInput.value) {
            const suggested = path.replace(/\.scriv\/?$/, ' Vault');
            outputPathInput.value = suggested;
            updateConvertButton();
        }
    }
});

selectOutputBtn.addEventListener('click', () => {
    const suggested = scrivPathInput.value
        ? scrivPathInput.value.replace(/\.scriv\/?$/, ' Vault')
        : '';

    const path = prompt(
        'Enter the path where you want to create the Obsidian vault:\n\n' +
        (suggested ? `Suggested: ${suggested}` : 'Example: /Users/yourname/Documents/My Novel Vault')
    );
    if (path) {
        outputPathInput.value = path.trim();
        updateConvertButton();
    }
});

// Convert button
convertBtn.addEventListener('click', async () => {
    const scrivPath = scrivPathInput.value;
    const outputPath = outputPathInput.value;

    if (!scrivPath || !outputPath) {
        showStatus('Please select both paths', 'error');
        return;
    }

    convertBtn.disabled = true;
    showStatus('Converting...', 'loading');

    try {
        const response = await fetch('/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                scriv_path: scrivPath,
                output_path: outputPath,
            }),
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showStatus(`${data.message}`, 'success');
        } else {
            const errorMsg = data.detail || data.message || 'Conversion failed';
            showStatus(errorMsg, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        updateConvertButton();
    }
});

// Initialize
updateConvertButton();
