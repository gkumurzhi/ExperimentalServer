// ===== Обзор файлов на сервере =====
const browseRootBtn = document.getElementById('browseRootBtn');
const browseUpBtn = document.getElementById('browseUpBtn');
const browseBtn = document.getElementById('browseBtn');
const clearUploadsBtn = document.getElementById('clearUploadsBtn');
const deleteSelectedUploadsBtn = document.getElementById('deleteSelectedUploadsBtn');
const browsePathInput = document.getElementById('browsePathInput');
const serverFilesEl = document.getElementById('serverFiles');
const selectedUploadPaths = new Set();

function isFileDeleteEnabled() {
    return typeof isServerCapabilityEnabled !== 'function'
        || isServerCapabilityEnabled('file_delete');
}

function isUploadsClearEnabled() {
    return typeof isServerCapabilityEnabled !== 'function'
        || isServerCapabilityEnabled('clear_uploads');
}

function isSmuggleEnabled() {
    return typeof isServerCapabilityEnabled !== 'function'
        || isServerCapabilityEnabled('smuggle');
}

function refreshFilesCapability() {
    if (clearUploadsBtn) {
        clearUploadsBtn.disabled = !isUploadsClearEnabled();
    }
    updateSelectedUploadsButton();
}

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
        } else if (action === 'smuggle' && isSmuggleEnabled()) {
            showSmuggleDialog(path, actionBtn);
        } else if (action === 'delete' && isFileDeleteEnabled()) {
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

refreshFilesCapability();

function updateSelectedUploadsButton() {
    if (deleteSelectedUploadsBtn) {
        deleteSelectedUploadsBtn.disabled = !isFileDeleteEnabled() || selectedUploadPaths.size === 0;
        deleteSelectedUploadsBtn.dataset.count = String(selectedUploadPaths.size);
    }
}

async function browseDirectory() {
    const path = document.getElementById('browsePathInput').value || '/';
    const serverFiles = document.getElementById('serverFiles');
    selectedUploadPaths.clear();
    updateSelectedUploadsButton();

    announceLiveRegion('filesResponseAreaLive', `${t('loadingInfo')} ${path}`);
    setExchangeInspector('files', {
        phase: 'sending',
        request: {
            transport: 'http',
            method: 'INFO',
            path,
            headers: {},
            body: null,
        },
        response: {
            phase: 'sending',
            startLine: `${t('loadingInfo')} ${path}`,
            body: createExchangeTextBody(`${t('loadingInfo')} ${path}...`),
        },
    });

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
                const smuggleButton = isSmuggleEnabled() ? `
                            <button
                                class="btn-ghost btn--sm file-row__action-muted file-row__action-compact"
                                data-file-action="smuggle"
                                data-path="${encodedItemPath}"
                                title="${smuggleLabel}"
                                aria-label="${smuggleLabel}"
                            >${esc(t('smuggleButtonLabel'))}</button>
                ` : '';
                const deleteButton = isFileDeleteEnabled() ? `
                            <button
                                class="btn-ghost btn--sm file-row__action-danger file-row__action-icon"
                                data-file-action="delete"
                                data-path="${encodedItemPath}"
                                title="${deleteLabel}"
                                aria-label="${deleteLabel}"
                            >×</button>
                ` : '';
                const selectBox = isFileDeleteEnabled() ? `
                        <label class="file-select" title="${selectLabel}" aria-label="${selectLabel}">
                            <input type="checkbox" data-file-select data-path="${encodedItemPath}">
                            <span aria-hidden="true"></span>
                        </label>
                ` : '';

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
                        ${selectBox}
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
                            ${smuggleButton}
                            ${deleteButton}
                        </div>
                    </div>
                </div>
            `;
            }).join('');
        } else {
            serverFiles.innerHTML = '';
        }

        const uploadsOnlyNote = info.access_scope === 'uploads' ? '\n--- ' + t('uploadsOnlyMode') + ' ---\n' : '';
        setExchangeInspector('files', {
            phase: 'complete',
            request: {
                transport: 'http',
                method: 'INFO',
                path,
                headers: {},
                body: null,
            },
            response: {
                transport: 'http',
                method: 'INFO',
                path,
                phase: 'complete',
                startLine: `INFO ${path}\n200 OK${info.access_scope === 'uploads' ? ' [uploads/]' : ''}`,
                status: 200,
                statusText: 'OK',
                headers: response.headers,
                body: createExchangeTextBody(`${uploadsOnlyNote}${JSON.stringify(info, null, 2)}`, { contentType: 'application/json' }),
            },
        });
        announceLiveRegion('filesResponseAreaLive', `INFO ${path} 200 OK`);

    } catch (error) {
        announceLiveRegion('filesResponseAreaLive', `INFO ${path} ${t('error')}: ${error.message}`);
        setExchangeInspector('files', {
            phase: 'error',
            request: {
                transport: 'http',
                method: 'INFO',
                path,
                headers: {},
                body: null,
            },
            response: {
                transport: 'http',
                method: 'INFO',
                path,
                phase: 'error',
                startLine: `INFO ${path}\n${t('error')}`,
                body: createExchangeTextBody(error.message),
            },
        });
    }
}

async function getFileInfo(path) {
    document.getElementById('browsePathInput').value = path;
    await browseDirectory();
}

async function clearUploads(triggerEl = null) {
    if (!isUploadsClearEnabled()) {
        return;
    }

    const confirmed = await showConfirmDialog({
        title: t('clearUploadsBtn'),
        message: t('clearUploadsConfirm'),
        details: '/uploads',
        confirmLabel: t('clearUploadsBtn'),
        triggerEl,
        initialFocus: 'cancel',
    });
    if (!confirmed) return;

    announceLiveRegion('filesResponseAreaLive', t('clearUploadsRunning'));
    setExchangeInspector('files', {
        phase: 'sending',
        request: {
            transport: 'http',
            method: 'DELETE',
            path: '/uploads?clear=1',
            headers: {},
            body: null,
        },
        response: {
            phase: 'sending',
            startLine: t('clearUploadsRunning'),
            body: createExchangeTextBody(t('clearUploadsRunning')),
        },
    });

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
            setExchangeInspector('files', {
                phase: 'complete',
                request: {
                    transport: 'http',
                    method: 'DELETE',
                    path: '/uploads?clear=1',
                    headers: {},
                    body: null,
                },
                response: {
                    transport: 'http',
                    method: 'DELETE',
                    path: '/uploads?clear=1',
                    phase: 'complete',
                    startLine: 'DELETE /uploads?clear=1\n200 OK',
                    status: 200,
                    statusText: 'OK',
                    headers: response.headers,
                    body: createExchangeTextBody(`${summary}\n\n${JSON.stringify(result, null, 2)}`, { contentType: 'application/json' }),
                },
            });
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
    if (!isFileDeleteEnabled()) {
        return;
    }

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

    const deleted = [];
    const errors = [];
    setExchangeInspector('files', {
        phase: 'sending',
        request: {
            transport: 'http',
            method: 'DELETE',
            path: t('deleteSelectedFilesBtn'),
            headers: {},
            body: createExchangeTextBody(paths.join('\n')),
        },
        response: {
            phase: 'sending',
            startLine: t('statusPending'),
            body: createExchangeTextBody(t('statusPending')),
        },
    });

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
    setExchangeInspector('files', {
        phase: errors.length ? 'error' : 'complete',
        request: {
            transport: 'http',
            method: 'DELETE',
            path: t('deleteSelectedFilesBtn'),
            headers: {},
            body: createExchangeTextBody(paths.join('\n')),
        },
        response: {
            transport: 'http',
            method: 'DELETE',
            path: t('deleteSelectedFilesBtn'),
            phase: errors.length ? 'error' : 'complete',
            startLine: `DELETE ${t('deleteSelectedFilesBtn')}\n${errors.length ? t('error') : '200 OK'}`,
            status: errors.length ? 400 : 200,
            statusText: errors.length ? t('error') : 'OK',
            body: createExchangeTextBody(`${summary}${errors.length ? '\n\n' + errors.join('\n') : ''}`),
        },
    });

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
    if (!isFileDeleteEnabled()) {
        return;
    }

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
const SAFE_SMUGGLE_EXTENSIONS = ['txt', 'bin', 'dat', 'zip', 'pdf'];
const SAFE_SMUGGLE_PRESET_CONFIG = {
    direct: { supportsCta: false, supportsDelay: false },
    card_manual: { supportsCta: true, supportsDelay: false },
    card_auto: { supportsCta: true, supportsDelay: true },
};

function getSmuggleSourceName(filePath) {
    const parts = String(filePath || '').split('/');
    return parts[parts.length - 1] || 'artifact.bin';
}

function getSmuggleDefaultExtension(sourceName) {
    const dotIndex = sourceName.lastIndexOf('.');
    const inferredExt = dotIndex > 0 ? sourceName.slice(dotIndex + 1).toLowerCase() : '';
    return SAFE_SMUGGLE_EXTENSIONS.includes(inferredExt) ? inferredExt : 'bin';
}

function getDefaultSmuggleBuilderState(filePath) {
    const sourceName = getSmuggleSourceName(filePath);
    const dotIndex = sourceName.lastIndexOf('.');
    return {
        sourceName,
        downloadName: dotIndex > 0 ? sourceName.slice(0, dotIndex) : sourceName.replace(/\.[^.]*$/, ''),
        downloadExt: getSmuggleDefaultExtension(sourceName),
        preset: 'direct',
        title: t('smuggleBuilderDefaultTitle'),
        message: t('smuggleBuilderDefaultMessage'),
        ctaLabel: t('smuggleBuilderDefaultCta'),
        delayMs: 1200,
        showNotice: true,
        encrypt: false,
    };
}

function getSmugglePresetConfig(preset) {
    return SAFE_SMUGGLE_PRESET_CONFIG[preset] || SAFE_SMUGGLE_PRESET_CONFIG.direct;
}

function getSmugglePresetLabel(preset) {
    if (preset === 'card_manual') {
        return t('smuggleBuilderPresetManual');
    }
    if (preset === 'card_auto') {
        return t('smuggleBuilderPresetAuto');
    }
    return t('smuggleBuilderPresetDirect');
}

function clampSmuggleDelay(value) {
    const parsed = Number.parseInt(String(value || ''), 10);
    if (!Number.isFinite(parsed)) {
        return 1200;
    }
    return Math.max(0, Math.min(10000, parsed));
}

function resolveSmuggleDownloadName(state) {
    const name = String(state.downloadName || '').trim() || 'download';
    const ext = SAFE_SMUGGLE_EXTENSIONS.includes(state.downloadExt) ? state.downloadExt : 'bin';
    return `${name}.${ext}`;
}

function readSmuggleBuilderState(modal, filePath) {
    const defaults = getDefaultSmuggleBuilderState(filePath);
    const downloadExt = String(modal.querySelector('#smuggleDownloadExt')?.value || defaults.downloadExt).toLowerCase();
    const preset = String(modal.querySelector('#smugglePreset')?.value || defaults.preset);
    const supports = getSmugglePresetConfig(preset);
    return {
        sourceName: defaults.sourceName,
        downloadName: String(modal.querySelector('#smuggleDownloadName')?.value || '').trim() || defaults.downloadName,
        downloadExt: SAFE_SMUGGLE_EXTENSIONS.includes(downloadExt) ? downloadExt : defaults.downloadExt,
        preset,
        title: String(modal.querySelector('#smuggleTitleInput')?.value || '').trim(),
        message: String(modal.querySelector('#smuggleMessageInput')?.value || '').trim(),
        ctaLabel: supports.supportsCta
            ? String(modal.querySelector('#smuggleCtaLabelInput')?.value || '').trim()
            : '',
        delayMs: supports.supportsDelay ? clampSmuggleDelay(modal.querySelector('#smuggleDelayMs')?.value) : 0,
        showNotice: Boolean(modal.querySelector('#smuggleShowNotice')?.checked),
        encrypt: Boolean(modal.querySelector('#smuggleEncrypt')?.checked),
    };
}

function setSmuggleFieldState(modal, rowSelector, inputSelector, enabled) {
    const row = modal.querySelector(rowSelector);
    const input = modal.querySelector(inputSelector);
    if (row) {
        row.hidden = !enabled;
    }
    if (input) {
        input.disabled = !enabled;
    }
}

function buildSmugglePreviewMarkup(state) {
    const supports = getSmugglePresetConfig(state.preset);
    const title = state.title || t('smuggleBuilderDefaultTitle');
    const message = state.message || t('smuggleBuilderDefaultMessage');
    const ctaLabel = state.ctaLabel || t('smuggleBuilderDefaultCta');
    const delay = clampSmuggleDelay(state.delayMs);
    const downloadName = resolveSmuggleDownloadName(state);
    const notice = state.showNotice
        ? `<p class="smuggle-preview__notice">${esc(t('smuggleBuilderNoticePreview'))}</p>`
        : '';
    const cta = supports.supportsCta
        ? `<div class="smuggle-preview__button">${esc(ctaLabel)}</div>`
        : '';
    const countdown = supports.supportsDelay
        ? `<p class="smuggle-preview__meta">${esc(t('smuggleBuilderPreviewDelay'))}: ${delay} ms</p>`
        : '';
    const shield = state.encrypt ? esc(t('smuggleBuilderPreviewProtected')) : esc(t('smuggleBuilderLabBadge'));
    return `
        <div class="smuggle-preview__card">
            <p class="smuggle-preview__badge">${shield}</p>
            ${notice}
            <h4 class="smuggle-preview__title">${esc(title)}</h4>
            <p class="smuggle-preview__message">${esc(message)}</p>
            <p class="smuggle-preview__meta">${esc(t('smuggleBuilderPreviewPreset'))}: ${esc(getSmugglePresetLabel(state.preset))}</p>
            <p class="smuggle-preview__meta">${esc(t('smuggleDownloadName'))}: <strong>${esc(downloadName)}</strong></p>
            ${countdown}
            ${cta}
        </div>
    `;
}

function syncSmuggleBuilderUi(modal, filePath) {
    const state = readSmuggleBuilderState(modal, filePath);
    const supports = getSmugglePresetConfig(state.preset);
    const previewName = modal.querySelector('#smuggleDownloadNamePreview');
    if (previewName) {
        previewName.textContent = resolveSmuggleDownloadName(state);
    }
    setSmuggleFieldState(modal, '#smuggleCtaRow', '#smuggleCtaLabelInput', supports.supportsCta);
    setSmuggleFieldState(modal, '#smuggleDelayRow', '#smuggleDelayMs', supports.supportsDelay);
    const preview = modal.querySelector('#smugglePreview');
    if (preview) {
        preview.innerHTML = buildSmugglePreviewMarkup(state);
    }
}

function buildSmuggleRequestPath(filePath, state) {
    const params = new URLSearchParams();
    if (state.encrypt) {
        params.set('encrypt', '1');
    }
    if (state.downloadName) {
        params.set('download_name', state.downloadName);
    }
    params.set('download_ext', state.downloadExt);
    params.set('preset', state.preset);
    if (state.title) {
        params.set('title', state.title);
    }
    if (state.message) {
        params.set('message', state.message);
    }
    if (getSmugglePresetConfig(state.preset).supportsCta && state.ctaLabel) {
        params.set('cta_label', state.ctaLabel);
    }
    if (getSmugglePresetConfig(state.preset).supportsDelay) {
        params.set('delay_ms', String(clampSmuggleDelay(state.delayMs)));
    }
    params.set('show_notice', state.showNotice ? '1' : '0');
    return `${filePath}?${params.toString()}`;
}

function showSmuggleDialog(filePath, triggerEl = null, options = {}) {
    if (!isSmuggleEnabled()) {
        return;
    }

    const defaults = getDefaultSmuggleBuilderState(filePath);
    const sourceName = defaults.sourceName;
    const extensionOptions = SAFE_SMUGGLE_EXTENSIONS.map(ext => (
        `<option value="${esc(ext)}"${ext === defaults.downloadExt ? ' selected' : ''}>.${esc(ext)}</option>`
    )).join('');

    const modal = openManagedDialog({
        dialogId: 'smuggleModal',
        triggerEl,
        initialFocusSelector: '#smuggleDownloadName',
        restoreFocusOnConfirm: false,
        markup: `
        <div class="modal-overlay">
            <div class="modal-content smuggle-dialog" role="dialog" aria-modal="true" aria-labelledby="smuggleDialogTitle" aria-describedby="smuggleDialogHint">
                <div class="smuggle-dialog__header">
                    <h3 id="smuggleDialogTitle">${t('smuggleTitle')}</h3>
                    <p class="smuggle-dialog__file">
                        <span class="smuggle-dialog__path">${esc(filePath)}</span>
                    </p>
                </div>
                <div class="smuggle-dialog__section">
                    <p class="smuggle-dialog__section-title">${esc(t('smuggleBuilderSourceSection'))}</p>
                    <div class="smuggle-dialog__meta">
                        <p class="smuggle-dialog__badge">${esc(t('smuggleBuilderLabBadge'))}</p>
                        <p class="smuggle-dialog__hint">${esc(t('smuggleBuilderSourceName'))}: <span class="smuggle-dialog__path">${esc(sourceName)}</span></p>
                        <p class="smuggle-dialog__hint" id="smuggleDialogHint">${esc(t('smuggleBuilderSourcePath'))}: <span class="smuggle-dialog__path">${esc(filePath)}</span></p>
                    </div>
                </div>
                <div class="smuggle-dialog__section">
                    <p class="smuggle-dialog__section-title">${esc(t('smuggleBuilderDeliverySection'))}</p>
                    <div class="smuggle-dialog__grid">
                        <label class="smuggle-dialog__field" for="smuggleDownloadName">
                            <span>${esc(t('smuggleBuilderBaseName'))}</span>
                            <input type="text" id="smuggleDownloadName" maxlength="120" value="${esc(defaults.downloadName)}">
                        </label>
                        <label class="smuggle-dialog__field" for="smuggleDownloadExt">
                            <span>${esc(t('smuggleBuilderExtension'))}</span>
                            <select id="smuggleDownloadExt">${extensionOptions}</select>
                        </label>
                    </div>
                    <p class="smuggle-dialog__hint">${esc(t('smuggleBuilderPreviewName'))}: <strong id="smuggleDownloadNamePreview">${esc(resolveSmuggleDownloadName(defaults))}</strong></p>
                </div>
                <div class="smuggle-dialog__section">
                    <p class="smuggle-dialog__section-title">${esc(t('smuggleBuilderPresetSection'))}</p>
                    <label class="smuggle-dialog__field" for="smugglePreset">
                        <span>${esc(t('smuggleBuilderPresetLabel'))}</span>
                        <select id="smugglePreset">
                            <option value="direct">${esc(t('smuggleBuilderPresetDirect'))}</option>
                            <option value="card_manual">${esc(t('smuggleBuilderPresetManual'))}</option>
                            <option value="card_auto">${esc(t('smuggleBuilderPresetAuto'))}</option>
                        </select>
                    </label>
                </div>
                <div class="smuggle-dialog__section">
                    <p class="smuggle-dialog__section-title">${esc(t('smuggleBuilderAdvancedSection'))}</p>
                    <div class="smuggle-dialog__grid">
                        <label class="smuggle-dialog__field" for="smuggleTitleInput">
                            <span>${esc(t('smuggleBuilderTitleLabel'))}</span>
                            <input type="text" id="smuggleTitleInput" maxlength="120" value="${esc(defaults.title)}">
                        </label>
                        <label class="smuggle-dialog__field" for="smuggleCtaLabelInput" id="smuggleCtaRow">
                            <span>${esc(t('smuggleBuilderCtaLabel'))}</span>
                            <input type="text" id="smuggleCtaLabelInput" maxlength="80" value="${esc(defaults.ctaLabel)}">
                        </label>
                        <label class="smuggle-dialog__field smuggle-dialog__field--wide" for="smuggleMessageInput">
                            <span>${esc(t('smuggleBuilderMessageLabel'))}</span>
                            <textarea id="smuggleMessageInput" maxlength="280">${esc(defaults.message)}</textarea>
                        </label>
                        <label class="smuggle-dialog__field" for="smuggleDelayMs" id="smuggleDelayRow" hidden>
                            <span>${esc(t('smuggleBuilderDelayLabel'))}</span>
                            <input type="number" id="smuggleDelayMs" min="0" max="10000" step="100" value="${esc(String(defaults.delayMs))}">
                        </label>
                    </div>
                    <label class="checkbox-row smuggle-dialog__toggle" for="smuggleShowNotice">
                        <input type="checkbox" id="smuggleShowNotice" checked> <span>${esc(t('smuggleBuilderNoticeLabel'))}</span>
                    </label>
                    <label class="checkbox-row smuggle-dialog__toggle" for="smuggleEncrypt">
                        <input type="checkbox" id="smuggleEncrypt"> <span>${esc(t('smuggleProtect'))}</span>
                    </label>
                    <p class="smuggle-dialog__hint">${esc(t('smuggleProtectHint'))}</p>
                </div>
                <div class="smuggle-dialog__section">
                    <p class="smuggle-dialog__section-title">${esc(t('smuggleBuilderPreviewSection'))}</p>
                    <div class="smuggle-preview" id="smugglePreview"></div>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn-opsec" id="smuggleSubmitBtn" data-dialog-action="confirm">${t('smuggleGenerate')}</button>
                    <button type="button" class="btn-ghost" id="smuggleCancelBtn" data-dialog-action="cancel">${t('smuggleCancel')}</button>
                </div>
            </div>
        </div>
    `,
        onAction: (action, activeModal) => {
            if (action === 'cancel') {
                return false;
            }
            if (action === 'confirm') {
                const builderState = readSmuggleBuilderState(activeModal, filePath);
                if (typeof options.onConfirm === 'function') {
                    options.onConfirm(builderState, activeModal);
                } else {
                    executeSmuggle(filePath, builderState, triggerEl, options.executionOptions || {});
                }
                return true;
            }
            return undefined;
        },
    });

    if (!modal) {
        return;
    }

    modal.querySelectorAll('input, select, textarea').forEach(control => {
        const eventName = control.tagName === 'SELECT' ? 'change' : 'input';
        control.addEventListener(eventName, () => syncSmuggleBuilderUi(modal, filePath));
        if (control.type === 'checkbox') {
            control.addEventListener('change', () => syncSmuggleBuilderUi(modal, filePath));
        }
    });
    syncSmuggleBuilderUi(modal, filePath);
}

function buildSmuggleResponseSummary(result) {
    const lines = [
        result.file,
        `${t('smuggleEncrypted')}: ${result.encrypted ? t('smuggleYes') : t('smuggleNo')}`,
    ];
    if (result.downloadName) {
        lines.push(`${t('smuggleDownloadName')}: ${result.downloadName}`);
    }
    lines.push(`URL: ${result.url}`);
    if (result.password) {
        lines.push(`${t('smugglePassword')}: ${result.password}`);
    }
    lines.push('', t('smuggleReady'));
    return lines.join('\n');
}

function buildSmuggleResultA11ySummary(filePath, artifactUrl, result) {
    const parts = [
        `${t('smuggleFile')}: ${filePath}`,
        `${t('smuggleEncrypted')}: ${result.encrypted ? t('smuggleYes') : t('smuggleNo')}`,
    ];
    if (result.downloadName) {
        parts.push(`${t('smuggleDownloadName')}: ${result.downloadName}`);
    }
    parts.push(`URL: ${artifactUrl}`);
    if (result.password) {
        parts.push(`${t('smugglePassword')}: ${result.password}`);
    }
    return parts.join('. ');
}

function setSmuggleResultStatus(modal, message, tone = '') {
    const statusEl = modal.querySelector('#smuggleResultStatus');
    if (!statusEl) {
        return;
    }
    statusEl.textContent = message;
    statusEl.className = `smuggle-dialog__hint smuggle-result__status${tone ? ` smuggle-result__status--${tone}` : ''}`;
}

function triggerSmuggleArtifactDownload(artifactUrl, artifactName) {
    const link = document.createElement('a');
    link.href = artifactUrl;
    link.download = artifactName;
    document.body.appendChild(link);
    link.click();
    link.remove();
}

function showSmuggleResultDialog(filePath, result, triggerEl = null, options = {}) {
    const liveRegionId = options.liveRegionId || 'filesResponseAreaLive';
    const artifactUrl = new URL(result.url, window.location.href).toString();
    const artifactName = String(result.url || '').split('/').pop() || 'smuggle-artifact.html';
    const resultSummary = buildSmuggleResultA11ySummary(filePath, artifactUrl, result);
    const passwordRow = result.password ? `
                <div class="smuggle-result__row">
                    <span class="smuggle-result__label">${esc(t('smugglePassword'))}</span>
                    <code class="smuggle-result__value">${esc(result.password)}</code>
                </div>
    ` : '';
    const downloadNameRow = result.downloadName ? `
                <div class="smuggle-result__row">
                    <span class="smuggle-result__label">${esc(t('smuggleDownloadName'))}</span>
                    <div class="smuggle-result__value" id="smuggleResultDownloadName">${esc(result.downloadName)}</div>
                </div>
    ` : '';

    openManagedDialog({
        dialogId: 'smuggleResultModal',
        triggerEl,
        initialFocusSelector: '#smuggleCopyUrlBtn',
        restoreFocusOnConfirm: true,
        markup: `
        <div class="modal-overlay">
            <div class="modal-content smuggle-dialog" role="dialog" aria-modal="true" aria-labelledby="smuggleResultTitle" aria-describedby="smuggleResultSummary smuggleResultHint smuggleResultStatus">
                <div class="smuggle-dialog__header">
                    <h3 id="smuggleResultTitle">${t('smuggleTitle')}</h3>
                    <p class="smuggle-dialog__file">
                        <span class="smuggle-dialog__path">${esc(filePath)}</span>
                    </p>
                </div>
                <div class="smuggle-dialog__settings smuggle-result__body">
                    <p class="sr-only" id="smuggleResultSummary">${esc(resultSummary)}</p>
                    <div class="smuggle-result__row">
                        <span class="smuggle-result__label">${esc(t('smuggleEncrypted'))}</span>
                        <span class="smuggle-result__value">${esc(result.encrypted ? t('smuggleYes') : t('smuggleNo'))}</span>
                    </div>
                    ${downloadNameRow}
                    ${passwordRow}
                    <div class="smuggle-result__row">
                        <span class="smuggle-result__label">URL</span>
                        <div class="smuggle-result__value" id="smuggleResultValue">${esc(artifactUrl)}</div>
                    </div>
                    <p class="smuggle-dialog__hint" id="smuggleResultHint">${t('smuggleResultHint')}</p>
                    <p class="smuggle-dialog__hint smuggle-result__status" id="smuggleResultStatus" role="status" aria-live="polite" aria-atomic="true">${t('smuggleReady')}</p>
                </div>
                <div class="modal-actions smuggle-result__actions">
                    <button type="button" class="btn-info" id="smuggleCopyUrlBtn" data-dialog-action="copy-url">${t('smuggleCopyUrl')}</button>
                    <button type="button" class="btn-opsec" id="smuggleOpenBtn" data-dialog-action="open">${t('smuggleOpen')}</button>
                    <button type="button" class="btn-ghost" id="smuggleSaveBtn" data-dialog-action="save">${t('smuggleSave')}</button>
                    <button type="button" class="btn-ghost" id="smuggleCloseBtn" data-dialog-action="close">${t('smuggleClose')}</button>
                </div>
            </div>
        </div>
    `,
        onAction: async (action, modal) => {
            if (action === 'close') {
                return false;
            }
            if (action === 'copy-url') {
                try {
                    await writeTextToClipboard(artifactUrl, 'smuggle-url');
                    setSmuggleResultStatus(modal, t('smuggleCopied'), 'ok');
                    announceLiveRegion(liveRegionId, `SMUGGLE ${filePath} ${t('smuggleCopied')}`);
                } catch (error) {
                    const message = formatActionErrorMessage(t('clipboardCopyFailed'), error);
                    setSmuggleResultStatus(modal, message, 'error');
                    announceLiveRegion(liveRegionId, `SMUGGLE ${filePath} ${message}`);
                }
                return undefined;
            }
            if (action === 'open') {
                const popup = window.open(artifactUrl, '_blank');
                if (!popup) {
                    const message = formatActionErrorMessage(t('smuggleOpen'), new Error(t('error')));
                    setSmuggleResultStatus(modal, message, 'error');
                    announceLiveRegion(liveRegionId, `SMUGGLE ${filePath} ${message}`);
                    return undefined;
                }
                announceLiveRegion(liveRegionId, `SMUGGLE ${filePath} ${t('smuggleOpened')}`);
                return true;
            }
            if (action === 'save') {
                triggerSmuggleArtifactDownload(artifactUrl, artifactName);
                announceLiveRegion(liveRegionId, `${t('downloadStarted')}: ${artifactName}`);
                return true;
            }
            return undefined;
        },
    });
}

async function executeSmuggle(filePath, builderState, triggerEl = null, options = {}) {
    const liveRegionId = options.liveRegionId || 'filesResponseAreaLive';
    const requestPath = buildSmuggleRequestPath(filePath, builderState);
    const url = SERVER_URL + requestPath;
    try {
        setExchangeInspector('files', {
            phase: 'sending',
            request: {
                transport: 'http',
                method: 'SMUGGLE',
                path: requestPath,
                headers: {},
                body: null,
            },
            response: {
                phase: 'sending',
                startLine: `SMUGGLE ${requestPath}`,
                body: createExchangeTextBody(t('statusPending')),
            },
        });
        const response = await sendCustomRequest('SMUGGLE', url);
        const text = await response.text();

        if (response.status === 200) {
            const result = JSON.parse(text);
            result.downloadName = resolveSmuggleDownloadName(builderState);

            const responseSummary = buildSmuggleResponseSummary(result);
            setExchangeInspector('files', {
                phase: 'complete',
                request: {
                    transport: 'http',
                    method: 'SMUGGLE',
                    path: requestPath,
                    headers: {},
                    body: null,
                },
                response: {
                    transport: 'http',
                    method: 'SMUGGLE',
                    path: filePath,
                    phase: 'complete',
                    startLine: `SMUGGLE ${requestPath}\n${t('smuggleGenerated')}`,
                    status: 200,
                    statusText: 'OK',
                    headers: response.headers,
                    body: createExchangeTextBody(responseSummary, { contentType: 'text/plain' }),
                },
            });
            announceLiveRegion(liveRegionId, `SMUGGLE ${filePath} ${t('smuggleGenerated')}`);
            showSmuggleResultDialog(filePath, result, triggerEl, { liveRegionId });
        } else {
            announceLiveRegion(liveRegionId, `SMUGGLE ${filePath} ${t('error')}`);
            setExchangeInspector('files', {
                phase: 'error',
                request: {
                    transport: 'http',
                    method: 'SMUGGLE',
                    path: requestPath,
                    headers: {},
                    body: null,
                },
                response: {
                    transport: 'http',
                    method: 'SMUGGLE',
                    path: filePath,
                    phase: 'error',
                    startLine: `SMUGGLE ${requestPath}\n${t('error')}`,
                    status: response.status,
                    statusText: response.statusText || t('error'),
                    headers: response.headers,
                    body: createExchangeTextBody(text),
                },
            });
            if (triggerEl) {
                focusElementWithoutScroll(triggerEl);
            }
        }
    } catch (error) {
        announceLiveRegion(liveRegionId, `SMUGGLE ${filePath} ${t('error')}: ${error.message}`);
        setExchangeInspector('files', {
            phase: 'error',
            request: {
                transport: 'http',
                method: 'SMUGGLE',
                path: requestPath,
                headers: {},
                body: null,
            },
            response: {
                transport: 'http',
                method: 'SMUGGLE',
                path: filePath,
                phase: 'error',
                startLine: `SMUGGLE ${requestPath}\n${t('error')}`,
                body: createExchangeTextBody(error.message),
            },
        });
        if (triggerEl) {
            focusElementWithoutScroll(triggerEl);
        }
    }
}
