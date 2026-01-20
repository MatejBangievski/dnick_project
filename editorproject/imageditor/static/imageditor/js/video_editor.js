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

    // 1. VISIBILITY & SYNC
    const visualBox = document.getElementById('visual-crop-box');
    const isWatermark = (key === 'video_watermark' ||key === 'video_image_watermark');
    const isCrop = (key === 'video_crop');

    if (visualBox) {
        if (isCrop || isWatermark) {
            visualBox.style.display = 'block';
            if (isWatermark) {
                visualBox.classList.add('text-box-overlay', 'active');
                visualBox.classList.remove('crop-box-overlay');
            } else {
                visualBox.classList.add('crop-box-overlay');
                visualBox.classList.remove('text-box-overlay', 'active');
            }
            if (isCrop) setTimeout(() => window.calculateCrop('free'), 50);
        } else {
            visualBox.style.display = 'none';
            const textTarget = document.getElementById('watermark-text-content');
            if (textTarget) textTarget.innerText = "";
        }
    }

    elements.settingsArea.innerHTML = `<h6 class="fw-bold border-bottom pb-2 mb-3">${config.name}</h6>`;

    config.options.forEach(opt => {
        const div = document.createElement('div');
        div.className = 'mb-3';
        let labelHtml = `<label class="form-label small fw-bold">${opt.label || ''}</label>`;
        let inputHtml = '';

        // --- SLIDER (Updated to show changes from presets) ---
        if (opt.type === 'slider' || opt.type === 'range') {
            labelHtml = `<div class="d-flex justify-content-between">
                            <label class="small fw-bold">${opt.label}</label>
                            <span id="val-${opt.id}" class="badge bg-primary">${opt.default}</span>
                         </div>`;
            inputHtml = `<input type="range" class="form-range" id="${opt.id}" min="${opt.min}" max="${opt.max}" step="${opt.step || 1}" value="${opt.default}" 
                         oninput="
                            document.getElementById('val-${opt.id}').innerText = this.value; 

                            if('${opt.id}' === 'opacity') {
                                const content = document.getElementById('watermark-text-content');
                                if(content) content.style.opacity = this.value;
                            }
        
                            // 3. Keep existing watermark text logic if applicable
                            if(window.updateTextBoxContent) window.updateTextBoxContent();
                         ">`;
        }

        // --- BUTTON GROUP (Updated to sync with slider/badge) ---
        else if (opt.type === 'button-group') {
            let buttonsHtml = opt.buttons.map(b =>
                `<button type="button" class="btn btn-outline-secondary btn-sm me-1 mb-1" 
                    onclick="
                        const t=document.getElementById('${opt.id}'); 
                        const slider=document.querySelector('input[type=range]');
                        if(t){ t.value='${b.value}'; }
                        if(slider){ slider.value='${b.value}'; }
                        const bd=document.getElementById('val-${opt.id}'); 
                        if(bd){ bd.innerText='${b.value}'; }
                    ">
                    ${b.label}
                </button>`
            ).join('');
            inputHtml = `<div class="d-flex flex-wrap">${buttonsHtml}</div>`;
        }

        // --- FONT CAROUSEL ---
        else if (opt.type === 'font-carousel') {
            const group = document.createElement('div');
            group.className = 'font-carousel-container mb-4';
            group.innerHTML = `${labelHtml}<input type="hidden" id="${opt.id}" name="${opt.id}" value="${opt.default}">`;
            const carousel = document.createElement('div');
            carousel.className = 'font-carousel';
            opt.fonts.forEach(font => {
                const fontOption = document.createElement('div');
                fontOption.className = `font-option ${font.value === opt.default ? 'selected' : ''}`;
                fontOption.innerHTML = `<div class="font-preview-box"><img src="/media/font_previews/${font.value}.png" onerror="this.style.display='none'; this.parentElement.innerHTML='Aa'"></div><div class="font-label">${font.label}</div>`;
                fontOption.addEventListener('click', () => {
                    group.querySelectorAll('.font-option').forEach(o => o.classList.remove('selected'));
                    fontOption.classList.add('selected');
                    document.getElementById(opt.id).value = font.value;
                    if (isWatermark) updateTextBoxContent();
                });
                carousel.appendChild(fontOption);
            });
            group.appendChild(carousel);
            elements.settingsArea.appendChild(group);
            return;
        }

        // --- ASPECT RATIO ---
        else if (opt.type === 'aspect-ratio-group') {
            let buttonsHtml = opt.buttons.map(b => `<button type="button" class="btn btn-primary btn-sm me-1 mb-1" onclick="window.calculateCrop('${b.value}')">${b.label}</button>`).join('');
            inputHtml = `<div class="d-flex flex-wrap">${buttonsHtml}</div>`;
        }

        // --- OTHERS ---
        else if (opt.type === 'color') {
            inputHtml = `<input type="color" class="form-control form-control-color w-100" id="${opt.id}" value="${opt.default}" style="height:45px;" oninput="if(window.updateTextBoxContent) window.updateTextBoxContent();">`;
        }
        // --- LOGO FILE UPLOAD ---
        else if (opt.type === 'file') {
            inputHtml = `
                <input type="file" class="form-control form-control-sm" id="${opt.id}" accept="${opt.accept}" 
                       onchange="window.handleWatermarkUpload(this, 'overlay_path')">
                <input type="hidden" id="overlay_path" value="">`;
        }

        // --- OPACITY PRESETS (Sync with Slider) ---
        else if (opt.type === 'opacity-button-group') {
            let buttonsHtml = opt.buttons.map(b =>
                `<button type="button" class="btn btn-outline-secondary btn-sm me-1 mb-1" 
                    onclick="
                        const slider = document.getElementById('opacity');
                        const badge = document.getElementById('val-opacity');
                        const content = document.getElementById('watermark-text-content');
                        if(slider) slider.value = ${b.value};
                        if(badge) badge.innerText = ${b.value};
                        if(content) content.style.opacity = ${b.value}; // Sync preview
                        if(window.updateTextBoxContent) window.updateTextBoxContent();
                    ">
                    ${b.label}
                </button>`
            ).join('');
            inputHtml = `<div class="d-flex flex-wrap">${buttonsHtml}</div>`;
        }

        // --- POSITION PRESETS (Snap Visual Box) ---
        else if (opt.type === 'position-button-group') {
            let buttonsHtml = opt.buttons.map(b =>
                `<button type="button" class="btn btn-outline-primary btn-sm me-1 mb-1" 
                    onclick="window.applyImagePreset('${b.value}')">
                    ${b.label}
                </button>`
            ).join('');
            inputHtml = `<div class="d-flex flex-wrap">${buttonsHtml}</div>`;
        }

        // --- HIDDEN FIELDS ---
        else if (opt.type === 'hidden') {
            inputHtml = `<input type="hidden" id="${opt.id}" value="${opt.default}">`;
            div.className = 'd-none'; // Hide the container
        }
        else if (opt.type === 'checkbox') {
            div.className = 'form-check form-switch mb-3 p-3 border rounded bg-white shadow-sm';
            div.innerHTML = `<label class="form-check-label fw-bold">${opt.label}</label><input class="form-check-input float-end" type="checkbox" role="switch" id="${opt.id}" ${opt.default ? 'checked' : ''} onchange="if(window.updateTextBoxContent) window.updateTextBoxContent();">`;
            elements.settingsArea.appendChild(div);
            return;
        }
        else {
            inputHtml = `<input type="${opt.type || 'number'}" class="form-control form-control-sm" id="${opt.id}" value="${opt.default}" oninput="if(window.updateTextBoxContent) window.updateTextBoxContent();">`;
        }

        div.innerHTML = labelHtml + inputHtml;
        elements.settingsArea.appendChild(div);
    });

    if (isWatermark) setTimeout(updateTextBoxContent, 50);
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

            // 2. Show the elements (Change display from none to their functional types)
            const videoWrapper = document.getElementById('video-wrapper');
            if (videoWrapper) videoWrapper.style.display = 'inline-block';

            elements.videoPlayer.style.display = 'block';
            // 3. Hide the upload UI
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

    // 1. Gather RAW values
    const options = {};
    window.EditorConfig.tools[currentToolKey].options.forEach(opt => {
        const el = document.getElementById(opt.id);
        if (el) {
            if (el.type === 'checkbox') {
                options[opt.id] = el.checked;
            } else if (el.type === 'color') {
                const hex = el.value;
                options['r'] = parseInt(hex.slice(1, 3), 16) / 255;
                options['g'] = parseInt(hex.slice(3, 5), 16) / 255;
                options['b'] = parseInt(hex.slice(5, 7), 16) / 255;
                options[opt.id] = hex;
            } else if (opt.id === 'text') {
                options[opt.id] = el.value;
            } else {
                options[opt.id] = isNaN(el.value) || el.value === "" ? el.value : parseFloat(el.value);
            }
        }
    });

    const hiddenPath = document.getElementById('overlay_path');
    if (hiddenPath && hiddenPath.value) {
        options['overlay_path'] = hiddenPath.value;
    }

    let finalOptions = JSON.parse(JSON.stringify(options));

    // 2. Precise Coordinate Mapping
    const coordinateTools = ['video_watermark', 'video_crop', 'video_image_watermark'];
    if (coordinateTools.includes(currentToolKey)) {
        const v = elements.videoPlayer;
        const box = document.getElementById('visual-crop-box');

        // Use getBoundingClientRect to get absolute screen positions
        const vRect = v.getBoundingClientRect();
        const bRect = box.getBoundingClientRect();

        // Calculate position relative ONLY to the video player edges
        const relativeX = bRect.left - vRect.left;
        const relativeY = bRect.top - vRect.top;

        if (!v.videoWidth || v.clientWidth === 0) {
            return alert("Video player not ready.");
        }

        // Conversion factors (Actual Resolution / Display Size)
        const scaleFactorX = v.videoWidth / v.clientWidth;
        const scaleFactorY = v.videoHeight / v.clientHeight;

        // Map browser pixels to real video pixels
        const x = Math.round(relativeX * scaleFactorX);
        const y = Math.round(relativeY * scaleFactorY);
        const w = Math.round(box.offsetWidth * scaleFactorX);
        const h = Math.round(box.offsetHeight * scaleFactorY);

        console.log(`[${currentToolKey}] Mapping: Browser(${relativeX}, ${relativeY}) -> Video(${x}, ${y})`);

        if (currentToolKey === 'video_image_watermark' || currentToolKey === 'video_watermark') {
            // This 'box' key triggers the custom positioning in Python
            finalOptions.box = [x, y, x + w, y + h];
        }

        if (currentToolKey === 'video_crop') {
            finalOptions.x = Math.max(0, makeEven(x));
            finalOptions.y = Math.max(0, makeEven(y));
            finalOptions.width = makeEven(w);
            finalOptions.height = makeEven(h);
        }
    }

    // 3. UI Feedback
    elements.overlay.style.display = 'flex';
    if (elements.progressBar) elements.progressBar.style.width = '0%';
    elements.statusText.innerText = "Processing Video...";

    // 4. Send Data
    const formData = new FormData();
    formData.append('working_file_path', workingFile);
    formData.append('current_preview_path', previewFile);
    formData.append('tool_key', currentToolKey);
    formData.append('options', JSON.stringify(finalOptions));

    try {
        const res = await fetch(window.EditorConfig.endpoints.preview, {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': window.EditorConfig.csrfToken }
        });

        const data = await res.json();
        if (data.success) {
            startPolling(data.task_id);
        } else {
            throw new Error(data.error || "Server error.");
        }
    } catch (err) {
        elements.overlay.style.display = 'none';
        alert(err.message);
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
        document.getElementById('save-to-profile-btn').disabled = false;
        // Optionally reset button text if it was changed to "Saved" previously
        const saveBtn = document.getElementById('save-to-profile-btn');
        saveBtn.innerHTML = `<i class="bi bi-cloud-upload-fill me-1"></i> Save to Profile`;
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

// Logic for Saving to Cloudinary/Profile
document.getElementById('save-to-profile-btn').addEventListener('click', async function() {
    const btn = this;
    const originalContent = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Saving...`;

    const formData = new FormData();
    // 'workingFile' is your state variable tracking the current video path
    formData.append('working_file_path', workingFile);
    formData.append('media_type', 'video');

    try {
        const res = await fetch(window.EditorConfig.endpoints.saveToProfile, {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': window.EditorConfig.csrfToken }
        });

        const data = await res.json();
        if (data.success) {
            btn.innerHTML = `<i class="bi bi-check-circle-fill"></i> Saved!`;
            btn.classList.replace('btn-save-profile', 'btn-success');
        } else {
            alert("Error: " + data.error);
            btn.disabled = false;
            btn.innerHTML = originalContent;
        }
    } catch (err) {
        btn.disabled = false;
        btn.innerHTML = originalContent;
        console.error(err);
    }
});

// 8. MOUSE EVENTS FOR CROP BOX
let isDragging = false;
let startMouseX, startMouseY, startBoxLeft, startBoxTop, startBoxWidth, startBoxHeight;
let activeHandle = null;

const visualCropBox = document.getElementById('visual-crop-box');

if (visualCropBox) {
    visualCropBox.addEventListener('mousedown', function(e) {
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

// 9. SUBTITLE VISUAL SYNC
function updateTextBoxContent() {
    const v = elements.videoPlayer;
    const box = document.getElementById('visual-crop-box');
    const textTarget = document.getElementById('watermark-text-content');

    if (!box || !textTarget || !v || !v.videoWidth) return;

    const originalFontSize = parseFloat(document.getElementById('font_size').value) || 40;

    const scaleFactor = v.clientWidth / v.videoWidth;

    textTarget.innerText = document.getElementById('text')?.value || "";
    textTarget.style.fontSize = (originalFontSize * scaleFactor) + "px";

    textTarget.style.color = document.getElementById('color')?.value || "#ffffff";
    textTarget.style.fontFamily = document.getElementById('font_name')?.value || "arial";

    const strokeWidth = parseFloat(document.getElementById('stroke_width')?.value) || 0;
    if (strokeWidth > 0) {
        const s = strokeWidth * scaleFactor;
        textTarget.style.textShadow = `-${s}px -${s}px 0 #000, ${s}px -${s}px 0 #000, -${s}px ${s}px 0 #000, ${s}px ${s}px 0 #000`;
    }
}

window.previewWatermarkImage = function(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('image-preview-container').classList.remove('d-none');
            document.getElementById('logo-preview-thumbnail').src = e.target.result;

            // Put image inside the visual overlay box
            const textTarget = document.getElementById('watermark-text-content');
            textTarget.innerHTML = `<img src="${e.target.result}" style="width:100%; height:100%; object-fit:contain; pointer-events:none;">`;
            textTarget.style.background = "transparent";
            textTarget.style.textShadow = "none";
        };
        reader.readAsDataURL(input.files[0]);
    }
};


window.applyImagePreset = function(preset) {
    const v = elements.videoPlayer;
    const box = document.getElementById('visual-crop-box');
    const wrapper = document.getElementById('video-wrapper');
    if (!box || !v) return;

    const padding = 20;
    let left = 0;
    let top = 0;

    // Horizontal
    if (preset.includes('left')) {
        left = padding;
    } else if (preset.includes('right')) {
        left = v.clientWidth - box.offsetWidth - padding;
    } else { // center
        left = (v.clientWidth - box.offsetWidth) / 2;
    }

    // Vertical
    if (preset.includes('top')) {
        top = padding;
    } else if (preset.includes('bottom')) {
        top = v.clientHeight - box.offsetHeight - padding;
    } else { // center
        top = (v.clientHeight - box.offsetHeight) / 2;
    }

    box.style.left = left + "px";
    box.style.top = top + "px";

    updateBackendCoords();
};

window.handleWatermarkUpload = async function(input, hiddenPathId) {
    if (!input.files || !input.files[0]) return;

    const formData = new FormData();
    formData.append('overlay_file', input.files[0]);

    try {
        const response = await fetch('/api/upload/overlay/', {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': window.EditorConfig.csrfToken }
        });

        const data = await response.json();
        if (data.success) {
            document.getElementById(hiddenPathId).value = data.overlay_path;

            const visualBox = document.getElementById('visual-crop-box');
            const contentArea = document.getElementById('watermark-text-content');

            contentArea.innerHTML = `<img src="${data.overlay_url}" style="width:100%; height:100%; object-fit:contain; opacity:inherit;">`;
            visualBox.style.display = 'block';

            const startWidth = elements.videoPlayer.clientWidth * 0.2;
            const aspectRatio = data.width / data.height;
            visualBox.style.width = startWidth + "px";
            visualBox.style.height = (startWidth / aspectRatio) + "px";

        } else {
            alert("Error: " + data.error);
        }
    } catch (err) {
        console.error("Upload failed", err);
    }
};

window.updateOpacityPreview = function() {
    const opacitySlider = document.getElementById('opacity');
    const visualBoxContent = document.getElementById('watermark-text-content');

    if (opacitySlider && visualBoxContent) {
        const val = opacitySlider.value;
        // Apply the opacity to the container holding the logo image
        visualBoxContent.style.opacity = val;

        // Optional: Update the badge text if it exists
        const badge = document.getElementById('val-opacity');
        if (badge) badge.innerText = val;
    }
};

// --- INITIALIZATION ---
window.addEventListener('DOMContentLoaded', () => {
    // Force everything hidden on fresh load
    if (elements.videoPlayer) elements.videoPlayer.style.display = 'none';
    const videoWrapper = document.getElementById('video-wrapper');
    if (videoWrapper) videoWrapper.style.display = 'none';

    // Ensure play buttons and download are locked until upload
    elements.applyBtn.disabled = true;
    elements.downloadBtn.disabled = true;
    elements.resetBtn.disabled = true;
    document.getElementById('save-to-profile-btn').disabled = true;
});

