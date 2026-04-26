// ===== Обзор файлов на сервере =====
const browseRootBtn = document.getElementById('browseRootBtn');
const browseUpBtn = document.getElementById('browseUpBtn');
const browseBtn = document.getElementById('browseBtn');
const clearUploadsBtn = document.getElementById('clearUploadsBtn');
const deleteSelectedUploadsBtn = document.getElementById('deleteSelectedUploadsBtn');
const browsePathInput = document.getElementById('browsePathInput');
const serverFilesEl = document.getElementById('serverFiles');
const selectedUploadPaths = new Set();

if (browseRootBtn) {
    browseRootBtn.addEventListener('click', goToRoot);
}

if (browseUpBtn) {
    browseUpBtn.addEventListener('click', goUp);
}

if (browseBtn) {
    browseBtn.addEventListener('click', browseDirectory);
}

if (clearUploadsBtn) {
    clearUploadsBtn.addEventListener('click', () => clearUploads(clearUploadsBtn));
}

if (deleteSelectedUploadsBtn) {
    deleteSelectedUploadsBtn.addEventListener('click', () => deleteSelectedUploadFiles(deleteSelectedUploadsBtn));
}

if (browsePathInput) {
    browsePathInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            browseDirectory();
        }
    });
}

if (serverFilesEl) {
    serverFilesEl.addEventListener('click', (e) => {
        const actionBtn = e.target.closest('[data-file-action][data-path]');
        if (!actionBtn) return;

        const action = actionBtn.dataset.fileAction;
        const encodedPath = actionBtn.dataset.path;
        if (!action || !encodedPath) return;

        const path = decodeURIComponent(encodedPath);

        if (action === 'info') {
            getFileInfo(path);
        } else if (action === 'download') {
            downloadFile(path);
        } else if (action === 'smuggle') {
            showSmuggleDialog(path, actionBtn);
        } else if (action === 'delete') {
            deleteFile(path, actionBtn);
        } else if (action === 'open-dir') {
            browsePathInput.value = path;
            browseDirectory();
        }
    });

    serverFilesEl.addEventListener('change', (e) => {
        const selectBox = e.target.closest('[data-file-select][data-path]');
        if (!selectBox) return;

        const path = decodeURIComponent(selectBox.dataset.path || '');
        if (!path) return;

        if (selectBox.checked) {
            selectedUploadPaths.add(path);
        } else {
            selectedUploadPaths.delete(path);
        }

        const row = selectBox.closest('.uploaded-file');
        if (row) {
            row.classList.toggle('is-selected', selectBox.checked);
        }
        updateSelectedUploadsButton();
    });
}

function goToRoot() {
    document.getElementById('browsePathInput').value = '/';
    browseDirectory();
}

function goUp() {
    const pathInput = document.getElementById('browsePathInput');
    let path = pathInput.value || '/';

    // Убираем trailing slash если есть
    if (path.endsWith('/') && path.length > 1) {
        path = path.slice(0, -1);
    }

    // Находим родительскую директорию
    const lastSlash = path.lastIndexOf('/');
    if (lastSlash > 0) {
        path = path.substring(0, lastSlash);
    } else {
        path = '/';
    }

    pathInput.value = path;
    browseDirectory();
}

function focusFilesBrowserAnchor() {
    if (browsePathInput && typeof browsePathInput.focus === 'function') {
        browsePathInput.focus();
    }
}

function updateSelectedUploadsButton() {
    if (deleteSelectedUploadsBtn) {
        deleteSelectedUploadsBtn.disabled = selectedUploadPaths.size === 0;
        deleteSelectedUploadsBtn.dataset.count = String(selectedUploadPaths.size);
    }
}

async function browseDirectory() {
    const path = document.getElementById('browsePathInput').value || '/';
    const filesResponseArea = document.getElementById('filesResponseArea');
    const serverFiles = document.getElementById('serverFiles');
    selectedUploadPaths.clear();
    updateSelectedUploadsButton();

    announceLiveRegion('filesResponseAreaLive', `${t('loadingInfo')} ${path}`);
    filesResponseArea.innerHTML = `<div class="response-header">${t('loadingInfo')} ${esc(path)}...</div>`;

    try {
        const response = await sendCustomRequest('INFO', SERVER_URL + path);
        const text = await response.text();
        const info = JSON.parse(text);

        if (info.is_directory && info.contents) {
            const basePath = path === '/' ? '' : path;
            serverFiles.innerHTML = info.contents.map(item => {
                const itemPath = basePath + '/' + item.name;
                const encodedItemPath = encodeURIComponent(itemPath);
                const itemIcon = item.is_dir ? '📁' : '📄';
                const openLabel = esc(`${t('open')}: ${item.name}`);
                const fetchLabel = esc(`${t('methodFetch')}: ${item.name}`);
                const infoLabel = esc(`${t('methodInfo')}: ${item.name}`);
                const smuggleLabel = esc(`${t('smuggleTitle')}: ${item.name}`);
                const deleteLabel = esc(`${t('deleteBtn')}: ${item.name}`);
                const selectLabel = esc(`${t('selectFileLabel')}: ${item.name}`);

                if (item.is_dir) {
                    return `
                <div class="uploaded-file uploaded-file--dir">
                    <div class="file-info">
                        <span class="file-icon" aria-hidden="true">${itemIcon}</span>
                        <div class="file-meta">
                            <span class="file-name">${esc(item.name)}</span>
                        </div>
                    </div>
                    <div class="file-row__actions">
                        <div class="file-row__actions-primary">
                            <button
                                class="btn-info btn--sm file-row__action-main file-row__action-icon"
                                data-file-action="open-dir"
                                data-path="${encodedItemPath}"
                                title="${openLabel}"
                                aria-label="${openLabel}"
                            >↗</button>
                        </div>
                    </div>
                </div>
            `;
                }

                return `
                <div class="uploaded-file uploaded-file--file">
                    <div class="file-info">
                        <label class="file-select" title="${selectLabel}" aria-label="${selectLabel}">
                            <input type="checkbox" data-file-select data-path="${encodedItemPath}">
                            <span aria-hidden="true"></span>
                        </label>
                        <span class="file-icon" aria-hidden="true">${itemIcon}</span>
                        <div class="file-meta">
                            <span class="file-name">${esc(item.name)}</span>
                        </div>
                    </div>
                    <div class="file-row__actions">
                        <div class="file-row__actions-primary">
                            <button
                                class="btn-fetch btn--sm file-row__action-main file-row__action-icon"
                                data-file-action="download"
                                data-path="${encodedItemPath}"
                                title="${fetchLabel}"
                                aria-label="${fetchLabel}"
                            >↓</button>
                        </div>
                        <div class="file-row__actions-secondary" aria-label="${esc(t('advancedLabel'))}">
                            <button
                                class="btn-ghost btn--sm file-row__action-muted file-row__action-icon"
                                data-file-action="info"
                                data-path="${encodedItemPath}"
                                title="${infoLabel}"
                                aria-label="${infoLabel}"
                            >i</button>
                            <button
                                class="btn-ghost btn--sm file-row__action-muted file-row__action-compact"
                                data-file-action="smuggle"
                                data-path="${encodedItemPath}"
                                title="${smuggleLabel}"
                                aria-label="${smuggleLabel}"
                            >HTML</button>
                            <button
                                class="btn-ghost btn--sm file-row__action-danger file-row__action-icon"
                                data-file-action="delete"
                                data-path="${encodedItemPath}"
                                title="${deleteLabel}"
                                aria-label="${deleteLabel}"
                            >×</button>
                        </div>
                    </div>
                </div>
            `;
            }).join('');
        } else {
            serverFiles.innerHTML = '';
        }

        const uploadsOnlyNote = info.access_scope === 'uploads' ? '\n--- ' + t('uploadsOnlyMode') + ' ---\n' : '';
        filesResponseArea.innerHTML = `
<div class="response-header">
INFO ${path}
<span class="status success">200 OK</span>${info.access_scope === 'uploads' ? ' <span class="response-flag response-flag--sandbox">[uploads/]</span>' : ''}
</div>
<div class="response-body">${esc(uploadsOnlyNote)}${esc(JSON.stringify(info, null, 2))}</div>`;
        announceLiveRegion('filesResponseAreaLive', `INFO ${path} 200 OK`);

    } catch (error) {
        announceLiveRegion('filesResponseAreaLive', `INFO ${path} ${t('error')}: ${error.message}`);
        filesResponseArea.innerHTML = `
<div class="response-header">
INFO ${path}
<span class="status error">${t('error')}</span>
</div>
<div class="response-body">${esc(error.message)}</div>`;
    }
}

async function getFileInfo(path) {
    document.getElementById('browsePathInput').value = path;
    await browseDirectory();
}

async function clearUploads(triggerEl = null) {
    const confirmed = await showConfirmDialog({
        title: t('clearUploadsBtn'),
        message: t('clearUploadsConfirm'),
        details: '/uploads',
        confirmLabel: t('clearUploadsBtn'),
        triggerEl,
        initialFocus: 'cancel',
    });
    if (!confirmed) return;

    const filesResponseArea = document.getElementById('filesResponseArea');
    announceLiveRegion('filesResponseAreaLive', t('clearUploadsRunning'));
    filesResponseArea.innerHTML = `<div class="response-header">${esc(t('clearUploadsRunning'))}</div>`;

    try {
        const response = await sendCustomRequest('DELETE', `${SERVER_URL}/uploads?clear=1`);
        const text = await response.text();
        let result = null;
        try {
            result = JSON.parse(text);
        } catch (error) {
            result = null;
        }

        if (response.ok && result && result.success) {
            if (browsePathInput) {
                browsePathInput.value = '/';
            }
            await browseDirectory();
            const summary = `${t('clearUploadsSuccess')}: ${result.deleted_files || 0} ${t('filesDeleted')}, ${result.deleted_dirs || 0} ${t('dirsDeleted')}`;
            announceLiveRegion('filesResponseAreaLive', summary);
            filesResponseArea.innerHTML = `
<div class="response-header">
DELETE /uploads?clear=1
<span class="status success">200 OK</span>
</div>
<div class="response-body">${esc(summary)}

${esc(JSON.stringify(result, null, 2))}</div>`;
            focusFilesBrowserAnchor();
            return;
        }

        const message = (result && result.error) || text || `${response.status} ${response.statusText || t('error')}`.trim();
        await showNoticeDialog({
            title: t('clearUploadsError'),
            message,
            details: '/uploads',
            triggerEl,
        });
    } catch (e) {
        await showNoticeDialog({
            title: t('clearUploadsError'),
            message: e.message,
            details: '/uploads',
            triggerEl,
        });
    }
}

async function deleteSelectedUploadFiles(triggerEl = null) {
    const paths = Array.from(selectedUploadPaths);
    if (paths.length === 0) return;

    const confirmed = await showConfirmDialog({
        title: t('deleteSelectedFilesBtn'),
        message: t('deleteSelectedFilesConfirm'),
        details: paths.join('\n'),
        confirmLabel: t('deleteSelectedFilesBtn'),
        triggerEl,
        initialFocus: 'cancel',
    });
    if (!confirmed) return;

    const filesResponseArea = document.getElementById('filesResponseArea');
    const deleted = [];
    const errors = [];

    for (const path of paths) {
        try {
            const response = await sendCustomRequest('DELETE', SERVER_URL + path);
            const text = await response.text();
            let result = null;
            try {
                result = JSON.parse(text);
            } catch (error) {
                result = null;
            }

            if (response.ok && result && result.success) {
                deleted.push(path);
                selectedUploadPaths.delete(path);
            } else {
                const message = (result && result.error) || text || `${response.status} ${response.statusText || t('error')}`.trim();
                errors.push(`${path}: ${message}`);
            }
        } catch (e) {
            errors.push(`${path}: ${e.message}`);
        }
    }

    await browseDirectory();
    const summary = `${t('deleteSelectedFilesSuccess')}: ${deleted.length}`;
    announceLiveRegion('filesResponseAreaLive', summary);
    filesResponseArea.innerHTML = `
<div class="response-header">
DELETE ${esc(t('deleteSelectedFilesBtn'))}
<span class="status ${errors.length ? 'error' : 'success'}">${errors.length ? esc(t('error')) : '200 OK'}</span>
</div>
<div class="response-body">${esc(summary)}
${errors.length ? '\n\n' + esc(errors.join('\n')) : ''}</div>`;

    if (errors.length) {
        await showNoticeDialog({
            title: t('deleteError'),
            message: errors.join('\n'),
            details: t('deleteSelectedFilesBtn'),
            triggerEl,
        });
    }
    focusFilesBrowserAnchor();
}

// ===== DELETE file =====
async function deleteFile(path, triggerEl = null) {
    const confirmed = await showConfirmDialog({
        title: t('deleteBtn'),
        message: t('deleteConfirm'),
        details: path,
        confirmLabel: t('deleteBtn'),
        triggerEl,
        initialFocus: 'cancel',
    });
    if (!confirmed) return;

    try {
        const response = await sendCustomRequest('DELETE', SERVER_URL + path);
        const text = await response.text();
        let result = null;
        try {
            result = JSON.parse(text);
        } catch (error) {
            result = null;
        }

        if (response.ok && result && result.success) {
            await browseDirectory();
            focusFilesBrowserAnchor();
            return;
        }

        const message = (result && result.error) || text || `${response.status} ${response.statusText || t('error')}`.trim();
        await showNoticeDialog({
            title: t('deleteError'),
            message,
            details: path,
            triggerEl,
        });
    } catch (e) {
        await showNoticeDialog({
            title: t('deleteError'),
            message: e.message,
            details: path,
            triggerEl,
        });
    }
}
// ===== HTML Smuggling =====
function showSmuggleDialog(filePath, triggerEl = null) {
    openManagedDialog({
        dialogId: 'smuggleModal',
        triggerEl,
        initialFocusSelector: '#smuggleSubmitBtn',
        restoreFocusOnConfirm: true,
        markup: `
        <div class="modal-overlay">
            <div class="modal-content smuggle-dialog" role="dialog" aria-modal="true" aria-labelledby="smuggleDialogTitle" aria-describedby="smuggleDialogHint">
                <div class="smuggle-dialog__header">
                    <h3 id="smuggleDialogTitle">${t('smuggleTitle')}</h3>
                    <p class="smuggle-dialog__file">
                        <span class="smuggle-dialog__path">${esc(filePath)}</span>
                    </p>
                </div>
                <div class="smuggle-dialog__settings">
                    <label class="checkbox-row smuggle-dialog__toggle" for="smuggleEncrypt">
                        <input type="checkbox" id="smuggleEncrypt"> <span>${t('smuggleProtect')}</span>
                    </label>
                    <p class="smuggle-dialog__hint" id="smuggleDialogHint">${t('smuggleProtectHint')}</p>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn-opsec" id="smuggleSubmitBtn" data-dialog-action="confirm">${t('smuggleOpen')}</button>
                    <button type="button" class="btn-ghost" id="smuggleCancelBtn" data-dialog-action="cancel">${t('smuggleCancel')}</button>
                </div>
            </div>
        </div>
    `,
        onAction: (action, modal) => {
            if (action === 'cancel') {
                return false;
            }
            if (action === 'confirm') {
                const usePassword = Boolean(modal.querySelector('#smuggleEncrypt')?.checked);
                executeSmuggle(filePath, usePassword);
                return true;
            }
            return undefined;
        },
    });
}

async function executeSmuggle(filePath, usePassword = false) {
    // Формируем URL
    let url = SERVER_URL + filePath;
    if (usePassword) {
        url += '?encrypt=1';  // Сервер сгенерирует пароль
    }

    // Запрашиваем создание HTML файла
    try {
        const response = await sendCustomRequest('SMUGGLE', url);
        const text = await response.text();

        if (response.status === 200) {
            const result = JSON.parse(text);

            // Открываем страницу напрямую с сервера
            window.open(SERVER_URL + result.url, '_blank');

            // Показываем результат
            const filesResponseArea = document.getElementById('filesResponseArea');
            filesResponseArea.innerHTML = `
<div class="response-header">
SMUGGLE ${esc(filePath)}
<span class="status success">${t('smuggleGenerated')}</span>
</div>
<div class="response-body">${esc(result.file)}
${t('smuggleEncrypted')}: ${result.encrypted ? t('smuggleYes') : t('smuggleNo')}
URL: ${esc(result.url)}

${t('smuggleOpened')}</div>`;
            announceLiveRegion('filesResponseAreaLive', `SMUGGLE ${filePath} ${t('smuggleGenerated')}`);
        } else {
            const filesResponseArea = document.getElementById('filesResponseArea');
            announceLiveRegion('filesResponseAreaLive', `SMUGGLE ${filePath} ${t('error')}`);
            filesResponseArea.innerHTML = `<div class="response-header">SMUGGLE ${esc(filePath)} <span class="status error">${t('error')}</span></div><div class="response-body">${esc(text)}</div>`;
        }
    } catch (error) {
        const filesResponseArea = document.getElementById('filesResponseArea');
        announceLiveRegion('filesResponseAreaLive', `SMUGGLE ${filePath} ${t('error')}: ${error.message}`);
        filesResponseArea.innerHTML = `<div class="response-header">SMUGGLE ${esc(filePath)} <span class="status error">${t('error')}</span></div><div class="response-body">${esc(error.message)}</div>`;
    }
}
