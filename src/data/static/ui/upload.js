// ===== Загрузка файлов =====
let uploadMethod = 'POST';
const uploadMethodButtons = Array.from(document.querySelectorAll('.upload-method-btn[data-upload-method]'));

function setUploadMethod(method, btn, options = {}) {
    const { focusButton = false } = options;
    uploadMethod = method;

    let activeButton = btn || null;
    uploadMethodButtons.forEach(button => {
        const isActive = button.dataset.uploadMethod === method;
        button.classList.toggle('active', isActive);
        button.setAttribute('aria-checked', String(isActive));
        button.setAttribute('tabindex', isActive ? '0' : '-1');
        if (isActive) {
            activeButton = button;
        }
    });

    const hint = document.getElementById('uploadMethodHint');
    if (hint) hint.textContent = method;

    if (focusButton) {
        focusElementWithoutScroll(activeButton);
    }
}

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const uploadBtn = document.getElementById('uploadBtn');
const uploadResponseAreaEl = document.getElementById('uploadResponseArea');
const uploadSelectionState = document.getElementById('uploadSelectionState');

function bindDropZoneKeyboardTrigger(container, input) {
    container.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            input.click();
        }
    });
}

function getUploadSelectionText() {
    if (filesToUpload.length === 0) {
        return t('uploadSelectionIdle');
    }

    if (filesToUpload.length === 1) {
        const selectedFile = filesToUpload[0];
        return `${t('selectedLabel')}: ${selectedFile.name} (${formatSize(selectedFile.size)})`;
    }

    return `${t('selectedFilesCount')}: ${filesToUpload.length}`;
}

function refreshUploadSelectionLocale() {
    if (uploadSelectionState) {
        uploadSelectionState.hidden = filesToUpload.length === 0;
        uploadSelectionState.textContent = getUploadSelectionText();
    }

    if (dropZone) {
        dropZone.classList.toggle('has-selection', filesToUpload.length > 0);
    }
}

uploadMethodButtons.forEach(button => {
    button.addEventListener('click', () => {
        const method = button.dataset.uploadMethod;
        if (method) {
            setUploadMethod(method, button);
        }
    });

    button.addEventListener('keydown', (event) => {
        const currentIndex = uploadMethodButtons.indexOf(button);
        if (currentIndex === -1) {
            return;
        }

        let nextIndex;
        if (event.key === 'ArrowRight') {
            nextIndex = (currentIndex + 1) % uploadMethodButtons.length;
        } else if (event.key === 'ArrowLeft') {
            nextIndex = (currentIndex - 1 + uploadMethodButtons.length) % uploadMethodButtons.length;
        } else if (event.key === 'Home') {
            nextIndex = 0;
        } else if (event.key === 'End') {
            nextIndex = uploadMethodButtons.length - 1;
        } else {
            return;
        }

        event.preventDefault();
        const nextButton = uploadMethodButtons[nextIndex];
        const method = nextButton?.dataset.uploadMethod;
        if (method) {
            setUploadMethod(method, nextButton, { focusButton: true });
        }
    });
});

if (uploadBtn) {
    uploadBtn.addEventListener('click', uploadAllFiles);
}

if (fileList) {
    fileList.addEventListener('click', (e) => {
        const removeBtn = e.target.closest('[data-remove-index]');
        if (!removeBtn) return;

        const index = Number(removeBtn.dataset.removeIndex);
        if (!Number.isNaN(index)) {
            removeFile(index);
        }
    });
}

if (uploadResponseAreaEl) {
    uploadResponseAreaEl.addEventListener('click', (e) => {
        const actionBtn = e.target.closest('[data-upload-response-action]');
        if (!actionBtn) return;

        if (actionBtn.dataset.uploadResponseAction === 'view-files') {
            switchTab('files', document.getElementById('tab-files'));
        }
    });
}

// Drag & Drop
if (dropZone && fileInput) {
    bindDropZoneKeyboardTrigger(dropZone, fileInput);

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', () => {
        handleFiles(fileInput.files);
        fileInput.value = '';
    });
}

if (uploadMethodButtons.length > 0) {
    const initialButton = uploadMethodButtons.find(button => button.classList.contains('active')) || uploadMethodButtons[0];
    const initialMethod = initialButton?.dataset.uploadMethod;
    if (initialMethod) {
        setUploadMethod(initialMethod, initialButton);
    }
}

function handleFiles(files) {
    for (const file of files) {
        if (!filesToUpload.find(f => f.name === file.name && f.size === file.size)) {
            filesToUpload.push({
                file: file,
                name: file.name,
                size: file.size,
                status: 'pending',
                progress: 0
            });
        }
    }
    renderFileList();
    uploadBtn.disabled = filesToUpload.length === 0;
    refreshUploadSelectionLocale();
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
}

let renderFileListRAF = null;
function scheduleRenderFileList() {
    if (!renderFileListRAF) {
        renderFileListRAF = requestAnimationFrame(() => {
            renderFileListRAF = null;
            renderFileList();
        });
    }
}

function renderFileList() {
    fileList.innerHTML = filesToUpload.map((f, i) => `
        <div class="file-item" data-testid="file-item-${i}">
            <div class="file-info">
                <span class="file-name">${esc(f.name)}</span>
                <span class="file-size">${formatSize(f.size)}</span>
            </div>
            <div class="queue-item__aside">
                <span class="file-status ${f.status}">${getStatusText(f.status)}</span>
                ${f.status === 'pending' ? `
                    <button
                        type="button"
                        class="btn-ghost btn--sm queue-item__remove"
                        data-remove-index="${i}"
                        title="${esc(t('queueRemoveLabel'))}"
                        aria-label="${esc(t('queueRemoveLabel'))}"
                    >✕</button>
                ` : ''}
            </div>
        </div>
        ${f.status === 'uploading' ? `<div class="progress-bar"><div class="progress-fill" style="width: ${f.progress || 0}%"></div></div>` : ''}
    `).join('');
}

function getStatusText(status) {
    const statusMap = {
        'pending': t('statusPending'),
        'uploading': t('statusUploading'),
        'success': t('statusSuccess'),
        'error': t('statusError')
    };
    return statusMap[status] || status;
}

function removeFile(index) {
    filesToUpload.splice(index, 1);
    renderFileList();
    uploadBtn.disabled = filesToUpload.length === 0;
    refreshUploadSelectionLocale();
}

async function uploadAllFiles() {
    const uploadResponseArea = document.getElementById('uploadResponseArea');
    announceLiveRegion('uploadResponseAreaLive', t('uploadStarting'));
    uploadResponseArea.innerHTML = `<div class="response-header">${t('uploadStarting')}</div>`;
    uploadBtn.disabled = true;

    const results = [];

    for (let i = 0; i < filesToUpload.length; i++) {
        const fileData = filesToUpload[i];
        if (fileData.status !== 'pending') continue;

        fileData.status = 'uploading';
        fileData.progress = 0;
        renderFileList();

        try {
            const arrayBuffer = await fileData.file.arrayBuffer();
            console.log(`Загрузка ${fileData.name}, размер: ${arrayBuffer.byteLength} байт`);

            // Кодируем имя файла для передачи в заголовке (поддержка кириллицы)
            const encodedFileName = encodeURIComponent(fileData.name);

            const response = await sendCustomRequest(
                uploadMethod,
                SERVER_URL + '/' + encodedFileName,
                arrayBuffer,
                {
                    'Content-Type': fileData.file.type || 'application/octet-stream',
                    'X-File-Name': encodedFileName
                },
                (event) => {
                    if (!event.lengthComputable) {
                        return;
                    }
                    fileData.progress = Math.round((event.loaded / event.total) * 100);
                    scheduleRenderFileList();
                }
            );

            console.log(`Ответ: ${response.status}`, response);

            const text = await response.text();
            console.log(`Тело ответа: ${text}`);

            let result;
            try {
                result = JSON.parse(text);
            } catch (parseError) {
                result = { success: false, error: t('parseError') + ': ' + text.substring(0, 100) };
            }

            if ((response.status === 200 || response.status === 201) && result.success) {
                fileData.status = 'success';
                fileData.progress = 100;
                fileData.serverPath = result.path;
                results.push({ name: fileData.name, success: true, path: result.path });
            } else {
                fileData.status = 'error';
                fileData.progress = 0;
                results.push({ name: fileData.name, success: false, error: result.error || `HTTP ${response.status}` });
            }
        } catch (error) {
            console.error(`Ошибка загрузки ${fileData.name}:`, error);
            fileData.status = 'error';
            fileData.progress = 0;
            results.push({ name: fileData.name, success: false, error: error.message });
        }

        renderFileList();
    }

    // Показываем результаты
    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;

    uploadResponseArea.innerHTML = `
<div class="response-header">
${t('uploadComplete')}
<span class="status ${failCount === 0 ? 'success' : 'error'}">${successCount} ${t('successCount')}, ${failCount} ${t('errorCount')}</span>
</div>
<div class="response-body">${results.map(r =>
    r.success
? `✓ ${esc(r.name)} -> ${esc(r.path)}`
: `✗ ${esc(r.name)}: ${esc(r.error)}`
).join('\n')}</div>
${successCount > 0 ? `<div class="upload-response-actions"><button class="btn-info btn--sm" data-upload-response-action="view-files">${t('viewInFiles')}</button></div>` : ''}`;
    announceLiveRegion('uploadResponseAreaLive', `${t('uploadComplete')}: ${successCount} ${t('successCount')}, ${failCount} ${t('errorCount')}`);

    // Очищаем успешно загруженные файлы
    filesToUpload = filesToUpload.filter(f => f.status !== 'success');
    renderFileList();
    uploadBtn.disabled = filesToUpload.length === 0;
    refreshUploadSelectionLocale();
}

refreshUploadSelectionLocale();
