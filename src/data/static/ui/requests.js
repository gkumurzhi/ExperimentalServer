// ===== Отправка запросов =====
const responseAreaEl = document.getElementById('responseArea');

document.querySelectorAll('[data-request-method]').forEach(button => {
    button.addEventListener('click', () => {
        const method = button.dataset.requestMethod;
        if (method) {
            sendRequest(method);
        }
    });
});

if (responseAreaEl) {
    responseAreaEl.addEventListener('click', (e) => {
        const downloadBtn = e.target.closest('[data-download-path]');
        if (!downloadBtn) return;

        const encodedPath = downloadBtn.dataset.downloadPath;
        if (encodedPath) {
            downloadFile(decodeURIComponent(encodedPath));
        }
    });
}

async function sendRequest(method) {
    const path = document.getElementById('pathInput').value || '/';
    const responseArea = document.getElementById('responseArea');

    announceLiveRegion('responseAreaLive', `${t('sendingRequest')} ${method} ${t('requestTo')} ${path}`);
    responseArea.innerHTML = `<div class="response-header">${t('sendingRequest')} ${esc(method)} ${t('requestTo')} ${esc(path)}...</div>`;

    try {
        const startTime = performance.now();

        const response = await sendCustomRequest(method, SERVER_URL + path, null);

        const endTime = performance.now();
        const duration = (endTime - startTime).toFixed(2);

        const text = await response.text();
        const statusClass = response.status < 400 ? 'success' : 'error';

        let headersText = '';
        for (const [key, value] of Object.entries(response.headers)) {
            headersText += `${key}: ${value}\n`;
        }

        let bodyDisplay = text;
        try {
            const json = JSON.parse(text);
            bodyDisplay = JSON.stringify(json, null, 2);
        } catch (e) {
            if (text.length > 500) {
                bodyDisplay = text.substring(0, 500) + '\n... (truncated)';
            }
        }

        responseArea.innerHTML = `
<div class="response-header">
${esc(method)} ${esc(path)}
<span class="status ${statusClass}">${response.status} ${esc(response.statusText || '')}</span>
${t('time')}: ${duration}ms
</div>
<div class="response-body">--- ${t('headers')} ---
${esc(headersText || t('headersNA'))}
--- ${t('responseBody')} ---
${esc(bodyDisplay)}</div>`;
        announceLiveRegion('responseAreaLive', `${method} ${path} ${response.status} ${response.statusText || ''}`.trim());

        // Если это FETCH, предложим скачать файл
        if (method === 'FETCH' && response.status === 200) {
            const filename = response.headers['x-file-name'] || 'download';
            responseArea.innerHTML += `\n\n<button class="btn-download" data-download-path="${encodeURIComponent(path)}">${t('download')} ${esc(filename)}</button>`;
        }

    } catch (error) {
        announceLiveRegion('responseAreaLive', `${method} ${path} ${t('error')}: ${error.message}`);
        responseArea.innerHTML = `
<div class="response-header">
${esc(method)} ${esc(path)}
<span class="status error">${t('error')}</span>
</div>
<div class="response-body">${esc(error.message)}</div>`;
    }
}

// Универсальная функция для кастомных HTTP-методов
function sendCustomRequest(method, path, body, headers = {}, onUploadProgress = null) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open(method, path, true);
        xhr.timeout = 30000; // 30 секунд таймаут

        if (onUploadProgress && xhr.upload) {
            xhr.upload.onprogress = onUploadProgress;
        }

        for (const [key, value] of Object.entries(headers)) {
            xhr.setRequestHeader(key, value);
        }

        xhr.onload = () => {
            const responseHeaders = {};
            xhr.getAllResponseHeaders().split('\r\n').forEach(line => {
                const idx = line.indexOf(': ');
                if (idx > 0) {
                    const key = line.substring(0, idx);
                    const value = line.substring(idx + 2);
                    responseHeaders[key.toLowerCase()] = value;
                }
            });
            resolve({
                status: xhr.status,
                ok: xhr.status >= 200 && xhr.status < 300,
                statusText: xhr.statusText,
                headers: responseHeaders,
                text: () => Promise.resolve(xhr.responseText),
                blob: () => Promise.resolve(new Blob([xhr.response]))
            });
        };

        xhr.onerror = () => reject(new Error(t('networkError')));
        xhr.ontimeout = () => reject(new Error(t('timeoutError')));

        if (body) {
            xhr.send(body);
        } else if (method === 'POST') {
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify({ demo: true, timestamp: new Date().toISOString() }));
        } else {
            xhr.send();
        }
    });
}

// Format ETA in mm:ss
function formatEta(seconds) {
    if (!isFinite(seconds) || seconds < 0) return '--:--';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
}

// Download file via FETCH with progress
async function downloadFile(path) {
    const xhr = new XMLHttpRequest();
    xhr.open('FETCH', SERVER_URL + path, true);
    xhr.responseType = 'blob';

    // Create/get progress container
    let progressEl = document.getElementById('downloadProgressArea');
    if (!progressEl) {
        progressEl = document.createElement('div');
        progressEl.id = 'downloadProgressArea';
        progressEl.className = 'panel download-progress-overlay';
        progressEl.hidden = true;
        document.body.appendChild(progressEl);
    }

    let progressLiveEl = document.getElementById('downloadProgressLive');
    if (!progressLiveEl) {
        progressLiveEl = document.createElement('div');
        progressLiveEl.id = 'downloadProgressLive';
        progressLiveEl.className = 'sr-only';
        progressLiveEl.setAttribute('role', 'status');
        progressLiveEl.setAttribute('aria-live', 'polite');
        progressLiveEl.setAttribute('aria-atomic', 'true');
        document.body.appendChild(progressLiveEl);
    }

    progressEl.removeAttribute('role');
    progressEl.removeAttribute('aria-live');
    progressEl.removeAttribute('aria-atomic');

    const startTime = Date.now();
    const fileName = path.split('/').pop() || 'download';
    progressEl.innerHTML = `
        <div class="download-progress-title">${t('downloadProgress')}: ${esc(fileName)}</div>
        <div class="progress-container">
            <div
                class="progress-bar-fill"
                id="dlProgressBar"
                role="progressbar"
                aria-label="${esc(t('downloadProgress'))}"
                aria-valuemin="0"
                aria-valuemax="100"
                aria-valuenow="0"
            ></div>
        </div>
        <div class="download-progress" id="dlProgressText" aria-hidden="true">0%</div>`;
    progressEl.hidden = false;

    const progressBarEl = document.getElementById('dlProgressBar');
    const progressTextEl = document.getElementById('dlProgressText');
    const progressTitleEl = progressEl.querySelector('.download-progress-title');
    let lastAnnouncedMilestone = 0;

    function setProgress(pct, text) {
        if (progressBarEl) {
            progressBarEl.style.width = pct + '%';
            progressBarEl.setAttribute('aria-valuenow', String(pct));
        }
        if (progressTextEl) {
            progressTextEl.classList.remove('download-progress--error');
            progressTextEl.textContent = text;
        }
    }

    function setLiveStatus(text) {
        announceLiveRegion('downloadProgressLive', text);
    }

    function showDownloadError(message) {
        progressEl.classList.add('download-progress-overlay--error');
        if (progressTitleEl) {
            progressTitleEl.textContent = `${t('downloadFailed')}: ${fileName}`;
        }
        if (progressBarEl) {
            progressBarEl.style.width = '100%';
            progressBarEl.setAttribute('aria-valuenow', '100');
            progressBarEl.setAttribute('aria-invalid', 'true');
        }
        if (progressTextEl) {
            progressTextEl.classList.add('download-progress--error');
            progressTextEl.textContent = message;
        }
        setLiveStatus(`${t('downloadFailed')}: ${fileName}. ${message}`);
    }
    progressEl.classList.remove('download-progress-overlay--error');
    if (progressBarEl) {
        progressBarEl.removeAttribute('aria-invalid');
    }
    setProgress(0, '0%');
    setLiveStatus(`${t('downloadStarted')}: ${fileName}`);

    xhr.onprogress = (e) => {
        if (e.lengthComputable) {
            const pct = Math.round((e.loaded / e.total) * 100);
            const elapsed = (Date.now() - startTime) / 1000;
            const speed = elapsed > 0 ? e.loaded / elapsed : 0;
            const remaining = speed > 0 ? (e.total - e.loaded) / speed : 0;
            setProgress(
                pct,
                `${pct}%  ${formatSize(e.loaded)}/${formatSize(e.total)}  ${t('downloadSpeed')}: ${formatSize(speed)}/s  ${t('downloadEta')}: ${formatEta(remaining)}`
            );

            const milestone = Math.floor(pct / 25) * 25;
            if (milestone > lastAnnouncedMilestone && milestone < 100) {
                lastAnnouncedMilestone = milestone;
                setLiveStatus(`${t('downloadProgress')}: ${fileName} ${milestone}%`);
            }
        }
    };

    xhr.onload = () => {
        if (xhr.status < 200 || xhr.status >= 300) {
            showDownloadError(`${xhr.status} ${xhr.statusText || t('error')}`.trim());
            return;
        }

        setLiveStatus(`${t('downloadCompleted')}: ${fileName}`);
        if (progressEl) progressEl.hidden = true;
        const filename = xhr.getResponseHeader('X-File-Name') || 'download';
        const blob = xhr.response;
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    };

    xhr.onerror = () => {
        showDownloadError(t('networkError'));
    };

    xhr.ontimeout = () => {
        showDownloadError(t('timeoutError'));
    };

    xhr.send();
}
