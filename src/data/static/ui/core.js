function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    if (next === 'light') {
        html.setAttribute('data-theme', 'light');
    } else {
        html.removeAttribute('data-theme');
    }
    localStorage.setItem('theme', next);
    const btn = document.getElementById('themeBtn');
    if (btn) btn.textContent = next === 'light' ? '☀️' : '🌙';
}

// Update theme button icon on load
document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('themeBtn');
    if (btn) btn.textContent = localStorage.getItem('theme') === 'light' ? '☀️' : '🌙';
});

// ===== Система локализации =====
const translations = {
    ru: {
        subtitle: "Кастомные методы, обмен файлами, OPSEC и E2E-заметки.",
        statusLive: "Локальная консоль",
        statusLiveCompact: "Локально",
        opsecEnabled: "OPSEC включён",
        opsecEnabledCompact: "OPSEC",
        themeToggleLabel: "Переключить тему",
        quickRequestMethodsLabel: "Быстрые методы запроса",
        primaryWorkflowsLabel: "Основные сценарии",
        serverToolsLabel: "Инструменты сервера",
        browseRootLabel: "Перейти в корень",
        browseUpLabel: "На уровень выше",
        httpMethodLabel: "HTTP-метод",
        randomLabel: "Случайно",
        refreshLabel: "Обновить",
        requestPanelLabel: "Рабочая панель",
        requestPanelTitle: "Проверяйте маршруты и методы без лишнего шума",
        requestPanelHint: "Быстрый запрос, быстрый ответ и быстрый переход к загрузке или файлам.",
        requestMetaHint: "Попробуйте `/index.html`, `/uploads/` или любой NOTE/INFO-совместимый путь.",
        responsePanelLabel: "Ответ",
        responsePanelTitle: "Живой вывод сервера",
        responsePanelHint: "Статус, заголовки и полезные данные появляются здесь без переключения вкладок.",
        capabilityUploadDesc: "Очередь файлов, выбор метода и быстрый обмен.",
        capabilityFilesDesc: "Открыть, скачать, удалить или подготовить smuggle-страницу.",
        capabilityOpsecDesc: "Скрытая загрузка без лишнего следа в URL и заголовках.",
        capabilityNotepadDesc: "Сквозные заметки через HTTP и WebSocket.",
        advancedLabel: "Расширенные инструменты",
        advancedToolsTitle: "Загрузка, обзор, OPSEC и заметки",
        advancedToolsHint: "Основной сценарий сверху, продвинутые инструменты ниже.",
        uploadHelper: "Быстро загрузите файлы, выберите метод и сразу проверьте результат.",
        filesHelper: "Обзор текущей директории, быстрые действия и детали ответа под списком.",
        opsecHelper: "Отдельный сценарий для скрытой загрузки и выбора транспорта.",
        sandboxMode: "🔒 Режим sandbox — доступ ограничен папкой uploads/",
        sandboxModeCompact: "🔒 Sandbox: uploads/",
        methodGet: "Получение ресурсов",
        methodPost: "Отправка данных",
        methodFetch: "Скачивание файлов",
        methodInfo: "Метаданные файла",
        methodPing: "Проверка сервера",
        methodNone: "Загрузка файлов",
        methodPut: "Загрузка/замена",
        methodPatch: "Обновление файлов",
        tabRequests: "Запросы",
        tabUpload: "Загрузка файлов",
        tabFiles: "Файлы на сервере",
        tabOpsec: "Режим OPSEC",
        sendRequests: "Отправка запросов",
        labelFilePath: "Путь к файлу",
        labelDirPath: "Путь к директории",
        pathPlaceholder: "Путь к файлу (например: /index.html)",
        uploadFiles: "Загрузка файлов",
        methodLabel: "Метод:",
        dropFilesHere: "Перетащите файлы сюда или нажмите для выбора",
        uploadDropZoneLabel: "Выбрать файлы для загрузки",
        uploadMethodLabel: "Метод загрузки",
        uploadSelectionIdle: "Файлы пока не выбраны",
        selectedLabel: "Выбрано",
        selectedFilesCount: "Файлов выбрано",
        uploadAllBtn: "Загрузить все файлы",
        serverFiles: "Файлы на сервере",
        dirPathPlaceholder: "Путь к директории",
        browseBtn: "Обзор (INFO)",
        statusPending: "Ожидание",
        statusUploading: "Загрузка...",
        statusSuccess: "Загружен",
        statusError: "Ошибка",
        queueRemoveLabel: "Убрать из очереди",
        clickToSend: "Нажмите на кнопку для отправки запроса...",
        selectFilesToUpload: "Выберите файлы для загрузки...",
        clickBrowse: "Нажмите \"Обзор\" для просмотра файлов...",
        uploadViaMethod: "Файлы будут загружены через метод",
        networkError: "Ошибка сети — сервер недоступен",
        timeoutError: "Тайм-аут — превышено время ожидания",
        parseError: "Ошибка парсинга",
        error: "Ошибка",
        uploadStarting: "Начинаем загрузку...",
        uploadComplete: "Загрузка завершена",
        successCount: "успешно",
        errorCount: "ошибок",
        sendingRequest: "Отправка",
        requestTo: "запроса на",
        headers: "Заголовки",
        headersNA: "(не доступны)",
        responseBody: "Тело ответа",
        time: "Время",
        download: "Скачать",
        loadingInfo: "Загрузка информации о",
        open: "Открыть",
        opsecTitle: "Режим OPSEC — скрытая загрузка",
        opsecDesc: "Загрузка файлов без раскрытия имени в URL/заголовках. Используются случайные HTTP методы.",
        opsecMethodPlaceholder: "HTTP метод (любой, например: CHECKDATA)",
        opsecUploadText: "Загрузка OPSEC — имя файла скрыто",
        opsecUploadHint: "Данные кодируются в Base64, путь не содержит имени файла",
        opsecDropZoneLabel: "Выбрать файл для OPSEC-загрузки",
        opsecSelectionIdle: "Файл пока не выбран",
        opsecIncludeName: "Включить имя файла (менее скрытно)",
        opsecEncryptXor: "Шифровать XOR",
        opsecPasswordPlaceholder: "Пароль для XOR-шифрования",
        opsecSendKey: "Отправить ключ на сервер (автоматическая расшифровка)",
        opsecKeyBase64: "Кодировать ключ в Base64",
        opsecUploadBtn: "Загрузить (OPSEC)",
        opsecSelectFile: "Выберите файл для скрытой загрузки...",
        opsecFileSelected: "Файл выбран",
        opsecPasswordRequired: "Ошибка: введите пароль для шифрования",
        opsecUploading: "Загрузка через метод",
        opsecXorEncryption: "XOR шифрование",
        opsecSuccess: "Загрузка через OPSEC выполнена",
        opsecUploaded: "Загружено",
        opsecId: "ID",
        opsecSize: "Размер",
        opsecBytes: "байт",
        opsecMethodRandom: "(случайный)",
        opsecPathNoName: "(не содержит имя файла)",
        opsecNameInReq: "Имя в запросе",
        opsecYes: "да",
        opsecNoHidden: "нет (скрыто)",
        opsecEncryption: "Шифрование",
        opsecNone: "нет",
        opsecXorDecrypted: "XOR (расшифровано на сервере",
        opsecKeyInBase64: ", ключ в base64",
        opsecXorEncrypted: "XOR (файл зашифрован)",
        smuggleTitle: "HTML Smuggling",
        smuggleFile: "Файл",
        smuggleProtect: "Защитить паролем (XOR)",
        smuggleProtectHint: "Пароль будет сгенерирован сервером",
        smuggleOpen: "Открыть",
        smuggleCancel: "Отмена",
        smuggleGenerated: "HTML сгенерирован",
        smuggleEncrypted: "Зашифрован",
        smuggleYes: "Да (XOR)",
        smuggleNo: "Нет",
        smuggleOpened: "HTML страница открыта в новой вкладке.",
        opsecWarning: "⚠ Сервер запущен без флага --opsec. OPSEC-загрузка может не работать.",
        opsecTransportLabel: "Транспорт:",
        opsecTransportBody: "Тело (JSON)",
        opsecTransportHeaders: "Заголовки",
        opsecTransportUrl: "URL параметры",
        opsecUrlSizeWarning: "Файл слишком большой для URL (~2 КБ макс). Используйте Body или Headers.",
        opsecHeaderSizeWarning: "Файл может быть слишком большой для заголовков (~32 КБ макс). Рекомендуется Body.",
        opsecTransportAutoSwitch: "Транспорт переключён на {0} (файл слишком большой для {1})",
        opsecTransportUsed: "Транспорт",
        viewInFiles: "Посмотреть в файлах →",
        tabNotepad: "Блокнот",
        notepadTitle: "Защищённый блокнот",
        notepadDesc: "Сквозное шифрование заметок. Ключи согласуются автоматически через ECDH — пароль не нужен.",
        notepadRequirements: "Требуется сервер с exphttp[crypto] и браузер с поддержкой Web Crypto.",
        notepadTitlePlaceholder: "Название заметки",
        notepadTextareaPlaceholder: "Введите текст... (шифруется перед сохранением)",
        notepadNewBtn: "Новая",
        notepadDeleteBtn: "Удалить",
        notepadNotes: "Заметки",
        notepadNoNotes: "Заметок пока нет",
        notepadConnecting: "Подключение...",
        notepadConnected: "Подключено (E2E)",
        notepadDisconnected: "Отключено",
        notepadReady: "Готово",
        notepadUnsaved: "Не сохранено",
        notepadSaving: "Сохранение...",
        notepadSaved: "Сохранено",
        notepadLoading: "Загрузка...",
        notepadLoaded: "Загружено",
        notepadSaveError: "Ошибка сохранения",
        notepadLoadError: "Ошибка загрузки",
        notepadDecryptError: "Ошибка расшифровки",
        notepadSessionFailed: "Ошибка инициализации сессии",
        notepadUnavailableServer: "Защищённый блокнот недоступен: установите exphttp[crypto] на сервере.",
        notepadUnavailableBrowser: "Защищённый блокнот недоступен: браузер не поддерживает Web Crypto.",
        notepadTransportHttp: "HTTP",
        notepadTransportWs: "WebSocket",
        notepadEphemeralWarning: "Сессии не сохраняются при перезагрузке сервера",
        notepadUntitled: "Без названия",
        notepadDeleteConfirm: "Удалить эту заметку?",
        notepadReconnecting: "Переподключение...",
        charCountSuffix: "симв.",
        deleteBtn: "Удалить",
        deleteConfirm: "Удалить этот файл?",
        deleteSuccess: "Файл удалён",
        deleteError: "Ошибка удаления",
        notepadDeleteError: "Ошибка удаления заметки",
        okBtn: "OK",
        downloadStarted: "Загрузка начата",
        downloadCompleted: "Загрузка завершена",
        downloadFailed: "Не удалось скачать файл",
        downloadProgress: "Загрузка",
        downloadSpeed: "Скорость",
        downloadEta: "Осталось"
    },
    en: {
        subtitle: "Custom methods, fast file sharing, OPSEC, and E2E notes.",
        statusLive: "Local console",
        statusLiveCompact: "Local",
        opsecEnabled: "OPSEC enabled",
        opsecEnabledCompact: "OPSEC",
        themeToggleLabel: "Toggle theme",
        quickRequestMethodsLabel: "Quick request methods",
        primaryWorkflowsLabel: "Primary workflows",
        serverToolsLabel: "Server tools",
        browseRootLabel: "Go to root",
        browseUpLabel: "Go up",
        httpMethodLabel: "HTTP method",
        randomLabel: "Random",
        refreshLabel: "Refresh",
        requestPanelLabel: "Workbench",
        requestPanelTitle: "Probe routes and methods without the noise",
        requestPanelHint: "Fast requests, quick responses, and direct jumps into uploads or files.",
        requestMetaHint: "Try `/index.html`, `/uploads/`, or any NOTE/INFO-compatible path.",
        responsePanelLabel: "Response",
        responsePanelTitle: "Live server output",
        responsePanelHint: "Status, headers, and payload appear here without switching tabs.",
        capabilityUploadDesc: "Queue files, pick a method, and share fast.",
        capabilityFilesDesc: "Open, fetch, delete, or smuggle any served file.",
        capabilityOpsecDesc: "Covert uploads without obvious traces in URLs or headers.",
        capabilityNotepadDesc: "End-to-end notes over HTTP and WebSocket.",
        advancedLabel: "Advanced tools",
        advancedToolsTitle: "Upload, browse, OPSEC, and notes",
        advancedToolsHint: "Keep the core workflow upfront; advanced tools live below.",
        uploadHelper: "Queue files, choose a method, and inspect the result right away.",
        filesHelper: "Browse the current directory, run quick actions, and inspect response details below the list.",
        opsecHelper: "Dedicated flow for covert uploads and transport tuning.",
        sandboxMode: "🔒 Sandbox mode - access limited to the uploads/ folder",
        sandboxModeCompact: "🔒 Sandbox: uploads/",
        methodGet: "Get resources",
        methodPost: "Send data",
        methodFetch: "Download files",
        methodInfo: "File metadata",
        methodPing: "Server check",
        methodNone: "Upload files",
        methodPut: "Upload/replace",
        methodPatch: "Update files",
        tabRequests: "Requests",
        tabUpload: "Uploads",
        tabFiles: "Files",
        tabOpsec: "OPSEC",
        sendRequests: "Send Requests",
        labelFilePath: "File path",
        labelDirPath: "Directory path",
        pathPlaceholder: "File path (e.g.: /index.html)",
        uploadFiles: "Uploads",
        methodLabel: "Method:",
        dropFilesHere: "Drag files here or click to select",
        uploadDropZoneLabel: "Choose files to upload",
        uploadMethodLabel: "Upload method",
        uploadSelectionIdle: "No files selected yet",
        selectedLabel: "Selected",
        selectedFilesCount: "Files selected",
        uploadAllBtn: "Upload all files",
        serverFiles: "Server Files",
        dirPathPlaceholder: "Directory path",
        browseBtn: "Browse (INFO)",
        statusPending: "Pending",
        statusUploading: "Uploading...",
        statusSuccess: "Uploaded",
        statusError: "Error",
        queueRemoveLabel: "Remove from queue",
        clickToSend: "Click a button to send a request...",
        selectFilesToUpload: "Select files to upload...",
        clickBrowse: "Click \"Browse\" to view files...",
        uploadViaMethod: "Files will be uploaded via method",
        networkError: "Network error — server unavailable",
        timeoutError: "Timeout — request took too long",
        parseError: "Parse error",
        error: "Error",
        uploadStarting: "Starting upload...",
        uploadComplete: "Upload complete",
        successCount: "successful",
        errorCount: "errors",
        sendingRequest: "Sending",
        requestTo: "request to",
        headers: "Headers",
        headersNA: "(not available)",
        responseBody: "Response body",
        time: "Time",
        download: "Download",
        loadingInfo: "Loading info for",
        open: "Open",
        opsecTitle: "OPSEC - Covert upload",
        opsecDesc: "Upload files without revealing names in URL/headers. Random HTTP methods are used.",
        opsecMethodPlaceholder: "HTTP method (any, e.g.: CHECKDATA)",
        opsecUploadText: "OPSEC upload - filename hidden",
        opsecUploadHint: "Data is base64-encoded, path does not contain filename",
        opsecDropZoneLabel: "Choose a file for OPSEC upload",
        opsecSelectionIdle: "No file selected yet",
        opsecIncludeName: "Include filename (less covert)",
        opsecEncryptXor: "Encrypt with XOR",
        opsecPasswordPlaceholder: "Password for XOR encryption",
        opsecSendKey: "Send key to server (auto-decrypt)",
        opsecKeyBase64: "Encode key in Base64",
        opsecUploadBtn: "Upload via OPSEC",
        opsecSelectFile: "Select a file for covert upload...",
        opsecFileSelected: "File selected",
        opsecPasswordRequired: "Error: enter a password for encryption",
        opsecUploading: "Uploading via method",
        opsecXorEncryption: "XOR encryption",
        opsecSuccess: "OPSEC upload completed",
        opsecUploaded: "Uploaded",
        opsecId: "ID",
        opsecSize: "Size",
        opsecBytes: "bytes",
        opsecMethodRandom: "(random)",
        opsecPathNoName: "(does not contain filename)",
        opsecNameInReq: "Name in request",
        opsecYes: "yes",
        opsecNoHidden: "no (hidden)",
        opsecEncryption: "Encryption",
        opsecNone: "none",
        opsecXorDecrypted: "XOR (decrypted on server",
        opsecKeyInBase64: ", key in base64",
        opsecXorEncrypted: "XOR (file encrypted)",
        smuggleTitle: "HTML Smuggling",
        smuggleFile: "File",
        smuggleProtect: "Protect with password (XOR)",
        smuggleProtectHint: "Password will be generated by server",
        smuggleOpen: "Open",
        smuggleCancel: "Cancel",
        smuggleGenerated: "HTML generated",
        smuggleEncrypted: "Encrypted",
        smuggleYes: "Yes (XOR)",
        smuggleNo: "No",
        smuggleOpened: "HTML page opened in new tab.",
        opsecWarning: "⚠ Server started without --opsec flag. OPSEC upload may not work.",
        opsecTransportLabel: "Transport:",
        opsecTransportBody: "Body (JSON)",
        opsecTransportHeaders: "Headers",
        opsecTransportUrl: "URL Params",
        opsecUrlSizeWarning: "File too large for URL params (~2 KB max). Use Body or Headers.",
        opsecHeaderSizeWarning: "File may be too large for headers (~32 KB max). Body recommended.",
        opsecTransportAutoSwitch: "Transport switched to {0} (file too large for {1})",
        opsecTransportUsed: "Transport",
        viewInFiles: "View in Files →",
        tabNotepad: "Notepad",
        notepadTitle: "Secure Notepad",
        notepadDesc: "End-to-end encrypted notes. Encryption keys are negotiated automatically via ECDH — no password needed.",
        notepadRequirements: "Requires server installation with exphttp[crypto] and a browser with Web Crypto support.",
        notepadTitlePlaceholder: "Note title",
        notepadTextareaPlaceholder: "Enter text here... (encrypted before saving)",
        notepadNewBtn: "New",
        notepadDeleteBtn: "Delete",
        notepadNotes: "Notes",
        notepadNoNotes: "No notes yet",
        notepadConnecting: "Connecting...",
        notepadConnected: "Connected (E2E)",
        notepadDisconnected: "Disconnected",
        notepadReady: "Ready",
        notepadUnsaved: "Unsaved",
        notepadSaving: "Saving...",
        notepadSaved: "Saved",
        notepadLoading: "Loading...",
        notepadLoaded: "Loaded",
        notepadSaveError: "Save error",
        notepadLoadError: "Load error",
        notepadDecryptError: "Decrypt error",
        notepadSessionFailed: "Session initialization failed",
        notepadUnavailableServer: "Secure Notepad unavailable: install exphttp[crypto] on the server.",
        notepadUnavailableBrowser: "Secure Notepad unavailable: this browser lacks Web Crypto support.",
        notepadTransportHttp: "HTTP",
        notepadTransportWs: "WebSocket",
        notepadEphemeralWarning: "Sessions are lost on server restart",
        notepadUntitled: "Untitled",
        notepadDeleteConfirm: "Delete this note?",
        notepadReconnecting: "Reconnecting...",
        charCountSuffix: "chars",
        deleteBtn: "Delete",
        deleteConfirm: "Delete this file?",
        deleteSuccess: "File deleted",
        deleteError: "Delete error",
        notepadDeleteError: "Note delete error",
        okBtn: "OK",
        downloadStarted: "Download started",
        downloadCompleted: "Download complete",
        downloadFailed: "Download failed",
        downloadProgress: "Downloading",
        downloadSpeed: "Speed",
        downloadEta: "ETA"
    }
};

let currentLang = localStorage.getItem('lang') || 'ru';

function setLang(lang) {
    currentLang = lang;
    localStorage.setItem('lang', lang);
    document.documentElement.lang = lang;
    applyTranslations();
    updateLangButtons();
}

function applyTranslations() {
    const t = translations[currentLang];

    // Обновляем все элементы с data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key]) {
            el.textContent = t[key];
        }
    });

    // Обновляем placeholder'ы
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (t[key]) {
            el.placeholder = t[key];
        }
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (t[key]) {
            el.title = t[key];
        }
    });

    document.querySelectorAll('[data-i18n-aria-label]').forEach(el => {
        const key = el.getAttribute('data-i18n-aria-label');
        if (t[key]) {
            el.setAttribute('aria-label', t[key]);
        }
    });

    // Обновляем хинт метода загрузки
    const hint = document.getElementById('uploadMethodHint');
    if (hint && t.uploadMethodLabel) {
        hint.textContent = t.uploadMethodLabel + ': ' + (typeof uploadMethod !== 'undefined' ? uploadMethod : 'POST');
    }

    if (typeof notepadRefreshLocale === 'function') {
        notepadRefreshLocale();
    }

    if (typeof refreshUploadSelectionLocale === 'function') {
        refreshUploadSelectionLocale();
    }

    if (typeof refreshOpsecSelectionLocale === 'function') {
        refreshOpsecSelectionLocale();
    }

    if (typeof refreshOpsecTransportWarningLocale === 'function') {
        refreshOpsecTransportWarningLocale();
    }
}

function updateLangButtons() {
    document.getElementById('langRu').classList.toggle('active', currentLang === 'ru');
    document.getElementById('langEn').classList.toggle('active', currentLang === 'en');
}

function t(key) {
    return translations[currentLang][key] || key;
}

// Применяем переводы при загрузке
document.addEventListener('DOMContentLoaded', () => {
    document.documentElement.lang = currentLang;
    applyTranslations();
    updateLangButtons();
    const serverAddressValue = document.getElementById('serverAddressValue');
    if (serverAddressValue) {
        serverAddressValue.textContent = location.host || '127.0.0.1';
    }
});

// HTML escape helper (XSS prevention)
function esc(str) {
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

// Базовый URL сервера (если страница открыта не с нашего сервера)
const SERVER_URL = '';
const liveRegionTimers = new Map();

// Файлы для загрузки
let filesToUpload = [];

// Sandbox mode flag
let isSandboxMode = false;
let isOpsecMode = false;

function announceLiveRegion(regionId, message) {
    const region = document.getElementById(regionId);
    if (!region) {
        return;
    }

    const nextMessage = String(message || '').trim();
    const pendingTimer = liveRegionTimers.get(regionId);
    if (pendingTimer) {
        clearTimeout(pendingTimer);
    }

    region.textContent = '';
    if (!nextMessage) {
        liveRegionTimers.delete(regionId);
        return;
    }

    const timer = setTimeout(() => {
        if (document.getElementById(regionId) === region) {
            region.textContent = nextMessage;
        }
        liveRegionTimers.delete(regionId);
    }, 20);

    liveRegionTimers.set(regionId, timer);
}

// Проверяем режим сервера при загрузке страницы
async function checkServerMode() {
    try {
        const response = await sendCustomRequest('PING', SERVER_URL + '/');
        const text = await response.text();
        const info = JSON.parse(text);

        if (info.sandbox_mode) {
            isSandboxMode = true;
            document.getElementById('sandboxIndicator').hidden = false;
            document.getElementById('browsePathInput').value = '/';
        }

        if (info.opsec_mode) {
            isOpsecMode = true;
            const opsecIndicator = document.getElementById('opsecIndicator');
            if (opsecIndicator) {
                opsecIndicator.hidden = false;
            }
        }

        // Show warning on OPSEC tab if server not in OPSEC mode
        if (!info.opsec_mode) {
            const opsecWarning = document.getElementById('opsecModeWarning');
            if (opsecWarning) opsecWarning.hidden = false;
        }
    } catch (e) {
        console.log('Could not check server mode:', e);
    }
}
// Переключение вкладок
function syncCapabilityChips(activeTabName) {
    document.querySelectorAll('.capability-chip[data-tab-target]').forEach(button => {
        const isActive = button.dataset.tabTarget === activeTabName;
        button.classList.toggle('active', isActive);
        button.setAttribute('aria-pressed', String(isActive));
    });
}

function focusElementWithoutScroll(element) {
    if (!element || typeof element.focus !== 'function') {
        return;
    }

    try {
        element.focus({ preventScroll: true });
    } catch (error) {
        element.focus();
    }
}

function switchTab(tabName, tabButton, options = {}) {
    const { focusTabButton = false } = options;

    document.querySelectorAll('.tab[role="tab"]').forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
        t.setAttribute('tabindex', '-1');
    });
    document.querySelectorAll('.tab-content[role="tabpanel"]').forEach(panel => {
        panel.classList.remove('active');
        panel.hidden = true;
    });

    const resolvedTabButton = tabButton || document.getElementById('tab-' + tabName);
    if (resolvedTabButton) {
        resolvedTabButton.classList.add('active');
        resolvedTabButton.setAttribute('aria-selected', 'true');
        resolvedTabButton.setAttribute('tabindex', '0');
    }

    const targetPanel = document.getElementById(tabName + '-tab');
    if (targetPanel) {
        targetPanel.classList.add('active');
        targetPanel.hidden = false;
    }

    syncCapabilityChips(tabName);

    // Update URL hash
    history.replaceState(null, '', '#' + tabName);

    if (focusTabButton && resolvedTabButton) {
        focusElementWithoutScroll(resolvedTabButton);
    }

    if (tabName === 'files') {
        setTimeout(browseDirectory, 100);
    }
    if (tabName === 'notepad') {
        notepadInit();
    }
}

function bindCoreControls() {
    document.querySelectorAll('[data-lang]').forEach(button => {
        button.addEventListener('click', () => {
            setLang(button.dataset.lang || 'ru');
        });
    });

    const themeBtn = document.getElementById('themeBtn');
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleTheme);
    }

    document.querySelectorAll('.capability-chip[data-tab-target]').forEach(button => {
        button.addEventListener('click', (event) => {
            const tabName = button.dataset.tabTarget;
            if (!tabName) return;

            const tabButton = document.getElementById('tab-' + tabName);
            const focusTabButton = event.detail === 0;
            switchTab(tabName, tabButton, { focusTabButton });

            const scrollTarget = button.dataset.scrollTarget;
            if (scrollTarget) {
                document.getElementById(scrollTarget)?.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    document.querySelectorAll('.tab[role="tab"][data-tab-target]').forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tabTarget;
            if (tabName) {
                switchTab(tabName, button);
            }
        });
    });
}

bindCoreControls();

// Restore tab from URL hash on load
window.addEventListener('DOMContentLoaded', () => {
    const hash = location.hash.replace('#', '');
    if (hash && document.getElementById(hash + '-tab')) {
        const tabBtn = document.getElementById('tab-' + hash);
        if (tabBtn) switchTab(hash, tabBtn);
    }
});

// Arrow key navigation for tabs (WAI-ARIA tab pattern)
const tabList = document.querySelector('[role="tablist"]');
if (tabList) {
    tabList.addEventListener('keydown', (e) => {
        const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
        const currentIndex = tabs.indexOf(document.activeElement);
        if (currentIndex === -1) return;

        let newIndex;
        if (e.key === 'ArrowRight') {
            newIndex = (currentIndex + 1) % tabs.length;
        } else if (e.key === 'ArrowLeft') {
            newIndex = (currentIndex - 1 + tabs.length) % tabs.length;
        } else if (e.key === 'Home') {
            newIndex = 0;
        } else if (e.key === 'End') {
            newIndex = tabs.length - 1;
        } else {
            return;
        }
        e.preventDefault();
        tabs[newIndex].focus();
        tabs[newIndex].click();
    });
}
