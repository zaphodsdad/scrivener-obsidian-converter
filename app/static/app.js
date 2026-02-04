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

// Select Scrivener project
selectScrivBtn.addEventListener('click', async () => {
    selectScrivBtn.disabled = true;
    selectScrivBtn.textContent = 'Opening...';

    try {
        const response = await fetch('/select-scriv', { method: 'POST' });
        const data = await response.json();

        if (data.success && data.path) {
            scrivPathInput.value = data.path;
            updateConvertButton();

            // Auto-suggest output path if empty
            if (!outputPathInput.value) {
                const suggested = data.path.replace(/\.scriv$/, ' Vault');
                outputPathInput.value = suggested;
                updateConvertButton();
            }

            hideStatus();
        } else if (data.error) {
            showStatus(data.error, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        selectScrivBtn.disabled = false;
        selectScrivBtn.textContent = 'Select .scriv';
    }
});

// Select output folder
selectOutputBtn.addEventListener('click', async () => {
    selectOutputBtn.disabled = true;
    selectOutputBtn.textContent = 'Opening...';

    try {
        const response = await fetch('/select-output', { method: 'POST' });
        const data = await response.json();

        if (data.success && data.path) {
            outputPathInput.value = data.path;
            updateConvertButton();
            hideStatus();
        } else if (data.error) {
            showStatus(data.error, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        selectOutputBtn.disabled = false;
        selectOutputBtn.textContent = 'Select folder';
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
            showStatus(data.message, 'success');
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
