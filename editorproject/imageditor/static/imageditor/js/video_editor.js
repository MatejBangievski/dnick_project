/**
 * Video Editor JS - 2026 Pro Version
 * Handles: Stacking Logic, Async Polling, Coordinate Calculation, and Reverting
 */

// 1. STATE MANAGEMENT
let originalFile = null;
let workingFile = null;
let previewFile = null;
let currentToolKey = null;
let pollingInterval = null;

// 2. ELEMENT SELECTORS
const elements = {
    fileInput: document.getElementById('video-file-input'),
    videoPlayer: document.getElementById('preview-video'),
    uploadContainer: document.getElementById('upload-container'),
    overlay: document.getElementById('processing-overlay'),
    progressBar: document.getElementById('task-progress-bar'),
    statusText: document.getElementById('status-text'),
    applyBtn: document.getElementById('apply-btn'),
    commitBtn: document.getElementById('commit-btn'),
    resetBtn: document.getElementById('reset-btn'),
    downloadBtn: document.getElementById('download-btn'),
    settingsArea: document.getElementById('tool-settings-area')
};

// --- UTILS ---
const makeEven = (val) => {
    let intVal = Math.floor(val);
    return intVal % 2 === 0 ? intVal : intVal - 1;
};

// 3. TOOL SELECTION & UI GENERATION
document.querySelectorAll('.tool-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentToolKey = btn.getAttribute('data-tool-key');
        renderSettings(currentToolKey);
    });
});

function renderSettings(key) {
    const config = window.EditorConfig.tools[key];
    if (!config) return;

    const visualBox = document.getElementById('visual-crop-box');
    if (key === 'video_crop') {
        visualBox.style.display = 'block';
        // Wait for UI to render then sync
        setTimeout(() => window.calculateCrop('free'), 50);
    } else {
        if(visualBox) visualBox.style.display = 'none';
    }

    elements.settingsArea.innerHTML = `<h6 class="fw-bold border-bottom pb-2 mb-3">${config.name}</h6>`;

    config.options.forEach(opt => {
        const div = document.createElement('div');
        div.className = 'mb-3';

        let labelHtml = `<label class="form-label small fw-bold">${opt.label || ''}</label>`;
        let inputHtml = '';

        if (opt.type === 'slider') {
            labelHtml = `<div class="d-flex justify-content-between">
                            <label class="small fw-bold">${opt.label}</label>
                            <span id="val-${opt.id}" class="badge bg-primary">${opt.default}</span>
                         </div>`;
            inputHtml = `<input type="range" class="form-range" id="${opt.id}" min="${opt.min}" max="${opt.max}" step="${opt.step || 1}" value="${opt.default}" 
                         oninput="document.getElementById('val-${opt.id}').innerText = this.value">`;
        }
        else if (opt.type === 'button-group') {
            let buttonsHtml = opt.buttons.map(b =>
                `<button type="button" class="btn btn-outline-secondary btn-sm me-1 mb-1" 
                         onclick="const t=document.getElementById('${opt.id}'); if(t){t.value='${b.value}'; const bd=document.getElementById('val-${opt.id}'); if(bd)bd.innerText='${b.value}';}">${b.label}</button>`
            ).join('');
            inputHtml = `<div class="d-flex flex-wrap">${buttonsHtml}</div>`;
        }
        else if (opt.type === 'aspect-ratio-group') {
            let buttonsHtml = opt.buttons.map(b =>
                `<button type="button" class="btn btn-primary btn-sm me-1 mb-1" onclick="window.calculateCrop('${b.value}')">${b.label}</button>`
            ).join('');
            inputHtml = `<div class="d-flex flex-wrap">${buttonsHtml}</div>`;
        }
        else if (opt.type === 'color') {
            inputHtml = `<input type="color" class="form-control form-control-color w-100" id="${opt.id}" value="${opt.default}" style="height:45px;">`;
        }
        else if (opt.type === 'checkbox') {
            div.className = 'form-check form-switch mb-3 p-3 border rounded bg-white shadow-sm';
            labelHtml = `<label class="form-check-label fw-bold" for="${opt.id}">${opt.label}</label>`;
            inputHtml = `<input class="form-check-input float-end" type="checkbox" role="switch" id="${opt.id}" ${opt.default ? 'checked' : ''}>`;

            div.innerHTML = labelHtml + inputHtml;
            elements.settingsArea.appendChild(div);
            return; // Exit this loop iteration
        }
        else if (opt.type === 'hidden') {
            div.className = 'd-none';
            inputHtml = `<input type="hidden" id="${opt.id}" value="${opt.default}">`;
        }
        else {
            inputHtml = `<input type="${opt.type || 'number'}" class="form-control form-control-sm" id="${opt.id}" value="${opt.default}">`;
        }

        div.innerHTML = labelHtml + inputHtml;
        elements.settingsArea.appendChild(div);
    });
}

// 4. CROP CALCULATION & SYNC
window.calculateCrop = function(ratio) {
    const v = elements.videoPlayer;
    const visualBox = document.getElementById('visual-crop-box');
    if(!visualBox) return;

    const vw = v.videoWidth;
    const vh = v.videoHeight;
    const displayW = v.clientWidth;
    const displayH = v.clientHeight;
    const scale = displayW / vw;

    let rx1 = 0, ry1 = 0, rw = vw, rh = vh;

    if (ratio !== 'free') {
        const parts = ratio.split(':');
        const targetRatio = parseFloat(parts[0]) / parseFloat(parts[1]);
        if ((vw / vh) > targetRatio) {
            rw = vh * targetRatio;
            rx1 = (vw - rw) / 2;
        } else {
            rh = vw / targetRatio;
            ry1 = (vh - rh) / 2;
        }
    }

    visualBox.style.left = (rx1 * scale) + "px";
    visualBox.style.top = (ry1 * scale) + "px";
    visualBox.style.width = (rw * scale) + "px";
    visualBox.style.height = (rh * scale) + "px";

    const badge = document.getElementById('crop-badge');
    if(badge) badge.innerText = ratio.toUpperCase();

    updateBackendCoords();
};

function updateBackendCoords() {
    const v = elements.videoPlayer;
    const box = document.getElementById('visual-crop-box');
    if(!box) return;

    const scale = v.videoWidth / v.clientWidth;

    const x1 = box.offsetLeft * scale;
    const y1 = box.offsetTop * scale;
    const x2 = (box.offsetLeft + box.offsetWidth) * scale;
    const y2 = (box.offsetTop + box.offsetHeight) * scale;

    if(document.getElementById('x1')) document.getElementById('x1').value = makeEven(x1);
    if(document.getElementById('y1')) document.getElementById('y1').value = makeEven(y1);
    if(document.getElementById('x2')) document.getElementById('x2').value = makeEven(x2);
    if(document.getElementById('y2')) document.getElementById('y2').value = makeEven(y2);
}

// 5. UPLOAD LOGIC
elements.fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('video', file);

    elements.uploadContainer.innerHTML = `<div class="spinner-border text-primary"></div><p class="mt-2">Uploading...</p>`;

    try {
        const response = await fetch(window.EditorConfig.endpoints.initialUpload, {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': window.EditorConfig.csrfToken }
        });

        const data = await response.json();
        if (data.success) {
            originalFile = data.original_file_path;
            workingFile = data.working_file_path;
            previewFile = data.preview_file_path;
            window.EditorConfig.originalVideoUrl = data.temp_video_url;

            elements.videoPlayer.src = data.temp_video_url;
            elements.videoPlayer.style.display = 'block';
            elements.uploadContainer.style.display = 'none';

            elements.applyBtn.disabled = false;
            elements.resetBtn.disabled = false;
        }
    } catch (err) {
        alert("Upload error.");
        console.error(err);
    }
});

// 6. PREVIEW & POLLING
elements.applyBtn.addEventListener('click', async () => {
    if (!currentToolKey) return alert("Select a tool first!");

    const options = {};
    window.EditorConfig.tools[currentToolKey].options.forEach(opt => {
        const el = document.getElementById(opt.id);
        if (el) {
            if (el.type === 'checkbox') {
                options[opt.id] = el.checked;
            }
            else if (el.type === 'color') {
                const hex = el.value;
                options['r'] = parseInt(hex.slice(1, 3), 16) / 255;
                options['g'] = parseInt(hex.slice(3, 5), 16) / 255;
                options['b'] = parseInt(hex.slice(5, 7), 16) / 255;
                options[opt.id] = hex;
            }
            else {
                options[opt.id] = isNaN(el.value) || el.value === "" ? el.value : parseFloat(el.value);
            }
        }
    });

    elements.overlay.style.display = 'flex';
    elements.progressBar.style.width = '0%';
    elements.statusText.innerText = "Applying Effect...";

    const formData = new FormData();
    formData.append('working_file_path', workingFile);
    formData.append('current_preview_path', previewFile);
    formData.append('tool_key', currentToolKey);
    formData.append('options', JSON.stringify(options));

    try {
        const res = await fetch(window.EditorConfig.endpoints.preview, {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': window.EditorConfig.csrfToken }
        });

        const data = await res.json();
        if (data.success) startPolling(data.task_id);
        else throw new Error(data.error);
    } catch (err) {
        elements.overlay.style.display = 'none';
        alert("Error: " + err.message);
    }
});

function startPolling(taskId) {
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(async () => {
        const res = await fetch(`${window.EditorConfig.endpoints.status}${taskId}/`);
        const data = await res.json();

        if (data.status === 'SUCCESS') {
            clearInterval(pollingInterval);
            finishTask(data);
        } else if (data.status === 'FAILURE') {
            clearInterval(pollingInterval);
            elements.overlay.style.display = 'none';
            alert("Processing failed.");
        } else {
            let cur = parseInt(elements.progressBar.style.width.replace('%', '')) || 0;
            if (cur < 90) elements.progressBar.style.width = (cur + 5) + '%';
        }
    }, 2000);
}

function finishTask(data) {
    previewFile = data.preview_file_path;
    const currentTime = elements.videoPlayer.currentTime;
    elements.videoPlayer.src = `${data.preview_url}?t=${new Date().getTime()}`;
    elements.videoPlayer.load();
    elements.videoPlayer.onloadeddata = () => {
        elements.videoPlayer.currentTime = currentTime;
        elements.overlay.style.display = 'none';
        elements.commitBtn.classList.remove('d-none');
        elements.downloadBtn.disabled = false;
    };
}

// 7. COMMIT & DOWNLOAD LOGIC
elements.commitBtn.addEventListener('click', async () => {
    const formData = new FormData();
    formData.append('working_file_path', workingFile);
    formData.append('preview_file_path', previewFile);

    const res = await fetch(window.EditorConfig.endpoints.process, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': window.EditorConfig.csrfToken }
    });

    const data = await res.json();
    if (data.success) {
        workingFile = data.working_file_path;
        elements.commitBtn.classList.add('d-none');
        alert("Effect stacked!");
    }
});

elements.resetBtn.addEventListener('click', function() {
    if (confirm("Reset to original?")) {
        if (window.EditorConfig.originalVideoUrl) {
            elements.videoPlayer.src = window.EditorConfig.originalVideoUrl;
            elements.videoPlayer.load();
        }
        workingFile = originalFile;
        previewFile = originalFile;
        elements.commitBtn.classList.add('d-none');
    }
});

elements.downloadBtn.addEventListener('click', () => {
    window.location.href = `${window.EditorConfig.endpoints.download}?file_path=${previewFile}`;
});

// 8. MOUSE EVENTS FOR CROP BOX
// 8. MOUSE EVENTS FOR CROP BOX
let isDragging = false;
let startMouseX, startMouseY, startBoxLeft, startBoxTop, startBoxWidth, startBoxHeight;
let activeHandle = null;

const visualCropBox = document.getElementById('visual-crop-box');

if (visualCropBox) {
    visualCropBox.addEventListener('mousedown', function(e) {
        // Only start dragging if user clicks the handle OR the very edge of the box
        const isHandle = e.target.classList.contains('resize-handle');
        const isEdge = e.target === visualCropBox;

        if (isHandle || isEdge) {
            isDragging = true;
            activeHandle = isHandle ? e.target : null;

            startMouseX = e.clientX;
            startMouseY = e.clientY;
            startBoxLeft = this.offsetLeft;
            startBoxTop = this.offsetTop;
            startBoxWidth = this.offsetWidth;
            startBoxHeight = this.offsetHeight;


            e.preventDefault();
            e.stopPropagation();
        }
    });
}

window.addEventListener('mousemove', function(e) {
    if (!isDragging) return;

    const box = document.getElementById('visual-crop-box');
    const wrapper = document.getElementById('video-wrapper');
    if(!box || !wrapper) return;

    const dx = e.clientX - startMouseX;
    const dy = e.clientY - startMouseY;

    if (!activeHandle) {
        box.style.left = Math.max(0, Math.min(wrapper.clientWidth - box.offsetWidth, startBoxLeft + dx)) + 'px';
        box.style.top = Math.max(0, Math.min(wrapper.clientHeight - box.offsetHeight, startBoxTop + dy)) + 'px';
    } else {
        if (activeHandle.classList.contains('se')) {
            box.style.width = Math.max(50, Math.min(wrapper.clientWidth - box.offsetLeft, startBoxWidth + dx)) + 'px';
            box.style.height = Math.max(50, Math.min(wrapper.clientHeight - box.offsetTop, startBoxHeight + dy)) + 'px';
        }
    }
    updateBackendCoords();
});

window.addEventListener('mouseup', () => {
    isDragging = false;
    activeHandle = null;
});