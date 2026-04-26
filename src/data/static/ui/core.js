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
        subtitle: "Кастомные методы, загрузки и E2E-заметки.",
        statusLive: "Локальная консоль",
        statusLiveCompact: "Локально",
        uploadsOnlyMode: "Доступ ограничен папкой uploads/",
        uploadsOnlyModeCompact: "uploads/",
        opsecEnabled: "Продвинутая загрузка включена",
        opsecEnabledCompact: "Продвинутая",
        themeToggleLabel: "Переключить тему",
        quickRequestMethodsLabel: "Методы запроса",
        primaryWorkflowsLabel: "Основные сценарии",
        serverToolsLabel: "Инструменты сервера",
        browseRootLabel: "Перейти в корень",
        browseUpLabel: "На уровень выше",
        httpMethodLabel: "HTTP-метод",
        randomLabel: "Случайно",
        refreshLabel: "Обновить",
        requestPanelLabel: "Рабочая панель",
        requestPanelTitle: "Запрос",
        requestPanelHint: "Быстрый запрос, быстрый ответ и быстрый переход к загрузке или скачиванию.",
        requestMetaHint: "Попробуйте `/index.html`, `/uploads/` или любой NOTE/INFO-совместимый путь.",
        responsePanelLabel: "Ответ",
        responsePanelTitle: "Ответ",
        responsePanelHint: "Статус, заголовки и полезные данные появляются здесь без переключения вкладок.",
        capabilityUploadDesc: "Очередь файлов, выбор метода и быстрый обмен.",
        capabilityFilesDesc: "Найти файл, скачать, удалить или подготовить smuggle-страницу.",
        capabilityOpsecDesc: "Продвинутая загрузка через тело, заголовки или URL.",
        capabilityNotepadDesc: "Сквозные заметки через HTTP и WebSocket.",
        advancedLabel: "Расширенные инструменты",
        advancedToolsTitle: "Загрузка, продвинутая загрузка, скачивание и заметки",
        advancedToolsHint: "Основной сценарий сверху, продвинутые инструменты ниже.",
        uploadHelper: "Быстро загрузите файлы, выберите метод и сразу проверьте результат.",
        filesHelper: "Скачивание из текущей директории, быстрые действия и детали ответа под списком.",
        opsecHelper: "Отдельный сценарий для продвинутой загрузки и выбора транспорта.",
        sandboxMode: "Доступ ограничен папкой uploads/",
        sandboxModeCompact: "uploads/",
        methodGet: "Получение ресурсов",
        methodHead: "Проверка заголовков",
        methodPost: "Отправка данных",
        methodDelete: "Удаление ресурса",
        methodOptions: "Проверка доступных методов",
        methodFetch: "Скачивание файлов",
        methodInfo: "Метаданные файла",
        methodPing: "Проверка сервера",
        methodNone: "Загрузка файлов",
        methodPut: "Загрузка/замена",
        methodPatch: "Обновление файлов",
        methodNote: "Проверка ECDH-ключа блокнота",
        methodSmuggle: "Генерация HTML smuggling-страницы",
        tabRequests: "Запросы",
        tabUpload: "Загрузка",
        tabFiles: "Скачивание",
        tabOpsec: "Загрузка (продвинутая)",
        sendRequests: "Отправка запросов",
        labelFilePath: "Путь к файлу",
        labelDirPath: "Путь к директории",
        pathPlaceholder: "/index.html или /uploads/",
        uploadFiles: "Загрузка файлов",
        methodLabel: "Метод:",
        requestPreviewToggleLabel: "Показывать отправляемое",
        requestPreviewModeLabel: "Режим показа запроса и ответа",
        requestPreviewModeSummary: "Сводка",
        requestPreviewModeRaw: "Raw HTTP",
        requestRunAllBtn: "Прогнать все",
        requestBatchRerunIssuesBtn: "Повторить проблемы",
        requestBatchRerunIssuesLabel: "Повторить только проблемные методы",
        requestBatchRerunIssuesStarted: "Повтор проблемных методов начат",
        requestBatchRerunIssuesCompleted: "Повтор проблемных методов завершён, осталось проблем",
        requestBatchExportBtn: "Экспорт JSON",
        requestBatchExportLabel: "Скачать JSON-отчёт прогона",
        requestBatchExported: "JSON-отчёт прогона выгружен",
        requestBatchExportFailed: "Не удалось выгрузить JSON-отчёт прогона",
        requestBatchClearBtn: "Очистить",
        requestBatchClearLabel: "Очистить результат прогона",
        requestBatchCleared: "Результат прогона очищен",
        requestBatchSummaryTitle: "Сводка прогона",
        requestBatchIssuesOnlyLabel: "Только проблемы",
        requestBatchNoIssues: "Расхождений и ошибок нет.",
        requestBatchNoIssuesYet: "Пока без расхождений и ошибок.",
        requestBatchRerunLabel: "Повторить метод",
        requestBatchRerunCompleted: "Повторный запуск завершён",
        requestBatchAttempts: "Попыток",
        requestBatchAttempt: "Попытка",
        requestBatchAttemptHistory: "История попыток",
        requestBatchLastRerun: "Последний повтор",
        requestBatchRerunFixed: "Исправлено",
        requestBatchRerunStillFailing: "Проблема осталась",
        requestBatchRerunRegressed: "Стало проблемой",
        requestBatchRerunStillOk: "Снова OK",
        requestBatchLegendLabel: "Легенда статусов методов",
        requestBatchLegendMatch: "Совпало",
        requestBatchLegendIssue: "Проблема",
        requestBatchRunning: "Выполняется",
        requestBatchCompleted: "Готово",
        requestBatchTotal: "Всего",
        requestBatchMatches: "Совпало",
        requestBatchMismatches: "Расхождений",
        requestBatchFailed: "Ошибок",
        requestPreviewTitle: "Что отправляется",
        copyRaw: "Копировать raw",
        copyRawRequestLabel: "Скопировать raw-запрос",
        copyRawResponseLabel: "Скопировать raw-ответ",
        requestPreviewCopied: "Raw-запрос скопирован",
        responseCopied: "Raw-ответ скопирован",
        clipboardCopyFailed: "Не удалось скопировать в буфер обмена",
        requestPreviewEmpty: "Выберите метод, чтобы увидеть исходящий HTTP-запрос.",
        requestPreviewPreparing: "Подготовка demo-сценария перед отправкой основного запроса...",
        requestPreviewFieldMethod: "Метод",
        requestPreviewFieldPath: "Путь",
        requestPreviewFieldExpectedStatus: "Ожидаемый статус",
        requestPreviewFieldActualStatus: "Фактический статус",
        requestPreviewFieldCheck: "Проверка",
        requestPreviewFieldHost: "Host",
        requestPreviewFieldHeaderCount: "Заголовки",
        requestPreviewFieldBodySize: "Размер тела",
        responseSummaryFieldStatus: "Статус",
        responseSummaryFieldContentType: "Content-Type",
        requestBody: "Тело запроса",
        requestPreviewNoBody: "Без тела",
        requestPreviewCheckPending: "Ожидание ответа",
        requestPreviewCheckMatch: "Совпадает",
        requestPreviewCheckMismatch: "Не совпадает",
        requestPreviewCheckFailed: "Ошибка запроса",
        dropFilesHere: "Выберите файлы",
        uploadDropZoneLabel: "Выбрать файлы для загрузки",
        uploadMethodLabel: "Метод загрузки",
        uploadSelectionIdle: "Файлы не выбраны",
        selectedLabel: "Выбрано",
        selectedFilesCount: "Файлов выбрано",
        uploadAllBtn: "Загрузить",
        serverFiles: "Файлы для скачивания",
        dirPathPlaceholder: "Путь к директории",
        browseBtn: "Обзор",
        statusPending: "Ожидание",
        statusUploading: "Загрузка...",
        statusSuccess: "Загружен",
        statusError: "Ошибка",
        queueRemoveLabel: "Убрать из очереди",
        clickToSend: "Выберите метод...",
        selectFilesToUpload: "Выберите файлы...",
        clickBrowse: "Нажмите \"Обзор\"...",
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
        preparingDemoRequest: "Подготовка demo-сценария",
        requestTo: "запроса на",
        headers: "Заголовки",
        headersNA: "(не доступны)",
        responseBody: "Тело ответа",
        time: "Время",
        download: "Скачать",
        loadingInfo: "Загрузка информации о",
        open: "Открыть",
        opsecTitle: "Загрузка (продвинутая)",
        opsecDesc: "Загрузка файлов через тело JSON, заголовки или URL-параметры.",
        opsecMethodPlaceholder: "Метод (CHECKDATA)",
        opsecUploadText: "Имя скрыто",
        opsecUploadHint: "Base64, без имени",
        opsecDropZoneLabel: "Выбрать файл для продвинутой загрузки",
        opsecSelectionIdle: "Файл не выбран",
        opsecIncludeName: "Имя",
        opsecEncryptXor: "XOR",
        opsecPasswordPlaceholder: "Пароль XOR",
        opsecSendKey: "Ключ",
        opsecKeyBase64: "Base64",
        opsecUploadBtn: "Загрузить",
        opsecSelectFile: "Выберите файл...",
        opsecFileSelected: "Файл выбран",
        opsecPasswordRequired: "Ошибка: введите пароль для шифрования",
        opsecUploading: "Загрузка через метод",
        opsecXorEncryption: "XOR шифрование",
        opsecSuccess: "Продвинутая загрузка выполнена",
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
        smuggleProtect: "XOR",
        smuggleProtectHint: "Пароль задаст сервер",
        smuggleOpen: "Открыть",
        smuggleCancel: "Отмена",
        smuggleGenerated: "HTML сгенерирован",
        smuggleEncrypted: "Зашифрован",
        smuggleYes: "Да (XOR)",
        smuggleNo: "Нет",
        smuggleOpened: "Открыто в новой вкладке.",
        opsecWarning: "",
        opsecTransportLabel: "Транспорт:",
        opsecTransportBody: "Тело (JSON)",
        opsecTransportHeaders: "Заголовки",
        opsecTransportUrl: "URL параметры",
        opsecUrlSizeWarning: "Файл слишком большой для URL (~2 КБ макс). Используйте Body или Headers.",
        opsecHeaderSizeWarning: "Файл может быть слишком большой для заголовков (~32 КБ макс). Рекомендуется Body.",
        opsecTransportAutoSwitch: "Транспорт переключён на {0} (файл слишком большой для {1})",
        opsecTransportUsed: "Транспорт",
        viewInFiles: "Перейти к скачиванию →",
        tabNotepad: "Блокнот",
        notepadTitle: "Защищённый блокнот",
        notepadDesc: "Сквозное шифрование заметок. Ключи согласуются автоматически через ECDH — пароль не нужен.",
        notepadRequirements: "Требуется сервер с exphttp[crypto] и браузер с поддержкой Web Crypto.",
        notepadTitlePlaceholder: "Заголовок",
        notepadTextareaPlaceholder: "Текст... (шифруется)",
        notepadNewBtn: "Новая",
        notepadDeleteBtn: "Удалить",
        notepadNotes: "Заметки",
        notepadNoNotes: "Нет заметок",
        notepadConnecting: "Подключение...",
        notepadConnected: "Онлайн",
        notepadDisconnected: "Офлайн",
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
        notepadUnavailableServer: "Блокнот недоступен: нужен exphttp[crypto] на сервере.",
        notepadUnavailableBrowser: "Блокнот недоступен: нет Web Crypto.",
        notepadTransportHttp: "HTTP",
        notepadTransportWs: "WS",
        notepadEphemeralWarning: "Сессии не сохраняются при перезагрузке сервера",
        notepadUntitled: "Без названия",
        notepadDeleteConfirm: "Удалить эту заметку?",
        notepadDeleteSelectedBtn: "Удалить выбранные заметки",
        notepadDeleteSelectedConfirm: "Удалить выбранные заметки?",
        notepadSelectedDeleted: "Выбранные заметки удалены",
        selectNoteLabel: "Выбрать заметку",
        notepadClearBtn: "Очистить заметки",
        notepadClearConfirm: "Удалить все заметки из notes/? Файлы в uploads/ не будут затронуты.",
        notepadCleared: "Заметки очищены",
        notepadClearError: "Ошибка очистки заметок",
        notepadReconnecting: "Переподключение...",
        charCountSuffix: "симв.",
        deleteBtn: "Удалить",
        deleteConfirm: "Удалить этот файл?",
        deleteSuccess: "Файл удалён",
        deleteError: "Ошибка удаления",
        selectFileLabel: "Выбрать файл",
        deleteSelectedFilesBtn: "Удалить выбранные файлы",
        deleteSelectedFilesConfirm: "Удалить выбранные файлы из uploads/?",
        deleteSelectedFilesSuccess: "Выбранные файлы удалены",
        clearUploadsBtn: "Очистить uploads/",
        clearUploadsConfirm: "Удалить всё содержимое uploads/? Служебные скрытые файлы будут сохранены.",
        clearUploadsRunning: "Очистка uploads/...",
        clearUploadsSuccess: "uploads/ очищена",
        clearUploadsError: "Ошибка очистки uploads/",
        filesDeleted: "файлов удалено",
        dirsDeleted: "папок удалено",
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
        subtitle: "Custom methods, uploads, and E2E notes.",
        statusLive: "Local console",
        statusLiveCompact: "Local",
        uploadsOnlyMode: "Access limited to the uploads/ folder",
        uploadsOnlyModeCompact: "uploads/",
        opsecEnabled: "Advanced upload enabled",
        opsecEnabledCompact: "Advanced",
        themeToggleLabel: "Toggle theme",
        quickRequestMethodsLabel: "Request methods",
        primaryWorkflowsLabel: "Primary workflows",
        serverToolsLabel: "Server tools",
        browseRootLabel: "Go to root",
        browseUpLabel: "Go up",
        httpMethodLabel: "HTTP method",
        randomLabel: "Random",
        refreshLabel: "Refresh",
        requestPanelLabel: "Workbench",
        requestPanelTitle: "Request",
        requestPanelHint: "Fast requests, quick responses, and direct jumps into uploads or download.",
        requestMetaHint: "Try `/index.html`, `/uploads/`, or any NOTE/INFO-compatible path.",
        responsePanelLabel: "Response",
        responsePanelTitle: "Response",
        responsePanelHint: "Status, headers, and payload appear here without switching tabs.",
        capabilityUploadDesc: "Queue files, pick a method, and share fast.",
        capabilityFilesDesc: "Find, download, delete, or smuggle any served file.",
        capabilityOpsecDesc: "Advanced uploads through body, headers, or URL params.",
        capabilityNotepadDesc: "End-to-end notes over HTTP and WebSocket.",
        advancedLabel: "More actions",
        advancedToolsTitle: "Upload, advanced upload, download, and notes",
        advancedToolsHint: "Keep the core workflow upfront; advanced tools live below.",
        uploadHelper: "Queue files, choose a method, and inspect the result right away.",
        filesHelper: "Download from the current directory, run quick actions, and inspect response details below the list.",
        opsecHelper: "Dedicated flow for advanced uploads and transport tuning.",
        sandboxMode: "Access limited to the uploads/ folder",
        sandboxModeCompact: "uploads/",
        methodGet: "Get resources",
        methodHead: "Inspect headers",
        methodPost: "Send data",
        methodDelete: "Delete a resource",
        methodOptions: "Inspect allowed methods",
        methodFetch: "Download files",
        methodInfo: "File metadata",
        methodPing: "Server check",
        methodNone: "Upload files",
        methodPut: "Upload/replace",
        methodPatch: "Update files",
        methodNote: "Inspect notepad ECDH key",
        methodSmuggle: "Generate an HTML smuggling page",
        tabRequests: "Requests",
        tabUpload: "Uploads",
        tabFiles: "Download",
        tabOpsec: "Advanced upload",
        sendRequests: "Send Requests",
        labelFilePath: "File path",
        labelDirPath: "Directory path",
        pathPlaceholder: "/index.html or /uploads/",
        uploadFiles: "Uploads",
        methodLabel: "Method:",
        requestPreviewToggleLabel: "Show outgoing request",
        requestPreviewModeLabel: "Request and response view mode",
        requestPreviewModeSummary: "Summary",
        requestPreviewModeRaw: "Raw HTTP",
        requestRunAllBtn: "Run all",
        requestBatchRerunIssuesBtn: "Rerun issues",
        requestBatchRerunIssuesLabel: "Rerun only problematic methods",
        requestBatchRerunIssuesStarted: "Issue rerun started",
        requestBatchRerunIssuesCompleted: "Issue rerun completed, issues left",
        requestBatchExportBtn: "Export JSON",
        requestBatchExportLabel: "Download the JSON run report",
        requestBatchExported: "JSON run report exported",
        requestBatchExportFailed: "Could not export the JSON run report",
        requestBatchClearBtn: "Clear",
        requestBatchClearLabel: "Clear the run result",
        requestBatchCleared: "Run result cleared",
        requestBatchSummaryTitle: "Run summary",
        requestBatchIssuesOnlyLabel: "Only issues",
        requestBatchNoIssues: "No mismatches or failures.",
        requestBatchNoIssuesYet: "No mismatches or failures yet.",
        requestBatchRerunLabel: "Run again",
        requestBatchRerunCompleted: "Rerun completed",
        requestBatchAttempts: "Attempts",
        requestBatchAttempt: "Attempt",
        requestBatchAttemptHistory: "Attempt history",
        requestBatchLastRerun: "Last rerun",
        requestBatchRerunFixed: "Fixed",
        requestBatchRerunStillFailing: "Still failing",
        requestBatchRerunRegressed: "Regressed",
        requestBatchRerunStillOk: "Still OK",
        requestBatchLegendLabel: "Method status legend",
        requestBatchLegendMatch: "Match",
        requestBatchLegendIssue: "Issue",
        requestBatchRunning: "Running",
        requestBatchCompleted: "Completed",
        requestBatchTotal: "Total",
        requestBatchMatches: "Matches",
        requestBatchMismatches: "Mismatches",
        requestBatchFailed: "Failed",
        requestPreviewTitle: "Outgoing request",
        copyRaw: "Copy raw",
        copyRawRequestLabel: "Copy raw request",
        copyRawResponseLabel: "Copy raw response",
        requestPreviewCopied: "Raw request copied",
        responseCopied: "Raw response copied",
        clipboardCopyFailed: "Could not copy to clipboard",
        requestPreviewEmpty: "Choose a method to inspect the outbound HTTP request.",
        requestPreviewPreparing: "Preparing the demo scenario before sending the primary request...",
        requestPreviewFieldMethod: "Method",
        requestPreviewFieldPath: "Path",
        requestPreviewFieldExpectedStatus: "Expected status",
        requestPreviewFieldActualStatus: "Actual status",
        requestPreviewFieldCheck: "Check",
        requestPreviewFieldHost: "Host",
        requestPreviewFieldHeaderCount: "Headers",
        requestPreviewFieldBodySize: "Body size",
        responseSummaryFieldStatus: "Status",
        responseSummaryFieldContentType: "Content-Type",
        requestBody: "Request body",
        requestPreviewNoBody: "No body",
        requestPreviewCheckPending: "Waiting for response",
        requestPreviewCheckMatch: "Matches",
        requestPreviewCheckMismatch: "Mismatch",
        requestPreviewCheckFailed: "Request failed",
        dropFilesHere: "Choose files",
        uploadDropZoneLabel: "Choose files to upload",
        uploadMethodLabel: "Upload method",
        uploadSelectionIdle: "No files selected",
        selectedLabel: "Selected",
        selectedFilesCount: "Files selected",
        uploadAllBtn: "Upload",
        serverFiles: "Downloadable files",
        dirPathPlaceholder: "Directory path",
        browseBtn: "Browse",
        statusPending: "Pending",
        statusUploading: "Uploading...",
        statusSuccess: "Uploaded",
        statusError: "Error",
        queueRemoveLabel: "Remove from queue",
        clickToSend: "Choose a method...",
        selectFilesToUpload: "Select files...",
        clickBrowse: "Click \"Browse\"...",
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
        preparingDemoRequest: "Preparing demo scenario",
        requestTo: "request to",
        headers: "Headers",
        headersNA: "(not available)",
        responseBody: "Response body",
        time: "Time",
        download: "Download",
        loadingInfo: "Loading info for",
        open: "Open",
        opsecTitle: "Advanced upload",
        opsecDesc: "Upload files through a JSON body, headers, or URL parameters.",
        opsecMethodPlaceholder: "Method (CHECKDATA)",
        opsecUploadText: "Name hidden",
        opsecUploadHint: "Base64, no name",
        opsecDropZoneLabel: "Choose a file for advanced upload",
        opsecSelectionIdle: "No file selected",
        opsecIncludeName: "Name",
        opsecEncryptXor: "XOR",
        opsecPasswordPlaceholder: "XOR password",
        opsecSendKey: "Key",
        opsecKeyBase64: "Base64",
        opsecUploadBtn: "Upload",
        opsecSelectFile: "Select a file...",
        opsecFileSelected: "File selected",
        opsecPasswordRequired: "Error: enter a password for encryption",
        opsecUploading: "Uploading via method",
        opsecXorEncryption: "XOR encryption",
        opsecSuccess: "Advanced upload completed",
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
        smuggleProtect: "XOR",
        smuggleProtectHint: "Server sets password",
        smuggleOpen: "Open",
        smuggleCancel: "Cancel",
        smuggleGenerated: "HTML generated",
        smuggleEncrypted: "Encrypted",
        smuggleYes: "Yes (XOR)",
        smuggleNo: "No",
        smuggleOpened: "Opened in new tab.",
        opsecWarning: "",
        opsecTransportLabel: "Transport:",
        opsecTransportBody: "Body (JSON)",
        opsecTransportHeaders: "Headers",
        opsecTransportUrl: "URL Params",
        opsecUrlSizeWarning: "File too large for URL params (~2 KB max). Use Body or Headers.",
        opsecHeaderSizeWarning: "File may be too large for headers (~32 KB max). Body recommended.",
        opsecTransportAutoSwitch: "Transport switched to {0} (file too large for {1})",
        opsecTransportUsed: "Transport",
        viewInFiles: "Go to Download →",
        tabNotepad: "Notepad",
        notepadTitle: "Secure Notepad",
        notepadDesc: "End-to-end encrypted notes. Encryption keys are negotiated automatically via ECDH — no password needed.",
        notepadRequirements: "Requires server installation with exphttp[crypto] and a browser with Web Crypto support.",
        notepadTitlePlaceholder: "Title",
        notepadTextareaPlaceholder: "Text... (encrypted)",
        notepadNewBtn: "New",
        notepadDeleteBtn: "Delete",
        notepadNotes: "Notes",
        notepadNoNotes: "No notes",
        notepadConnecting: "Connecting...",
        notepadConnected: "Online",
        notepadDisconnected: "Offline",
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
        notepadUnavailableServer: "Notepad unavailable: exphttp[crypto] required on server.",
        notepadUnavailableBrowser: "Notepad unavailable: no Web Crypto.",
        notepadTransportHttp: "HTTP",
        notepadTransportWs: "WS",
        notepadEphemeralWarning: "Sessions are lost on server restart",
        notepadUntitled: "Untitled",
        notepadDeleteConfirm: "Delete this note?",
        notepadDeleteSelectedBtn: "Delete selected notes",
        notepadDeleteSelectedConfirm: "Delete selected notes?",
        notepadSelectedDeleted: "Selected notes deleted",
        selectNoteLabel: "Select note",
        notepadClearBtn: "Clear notes",
        notepadClearConfirm: "Delete all notes from notes/? Files in uploads/ will not be touched.",
        notepadCleared: "Notes cleared",
        notepadClearError: "Clear notes error",
        notepadReconnecting: "Reconnecting...",
        charCountSuffix: "chars",
        deleteBtn: "Delete",
        deleteConfirm: "Delete this file?",
        deleteSuccess: "File deleted",
        deleteError: "Delete error",
        selectFileLabel: "Select file",
        deleteSelectedFilesBtn: "Delete selected files",
        deleteSelectedFilesConfirm: "Delete selected files from uploads/?",
        deleteSelectedFilesSuccess: "Selected files deleted",
        clearUploadsBtn: "Clear uploads/",
        clearUploadsConfirm: "Delete all contents of uploads/? Hidden service files will be preserved.",
        clearUploadsRunning: "Clearing uploads/...",
        clearUploadsSuccess: "uploads/ cleared",
        clearUploadsError: "Clear uploads/ error",
        filesDeleted: "files deleted",
        dirsDeleted: "folders deleted",
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

    if (typeof renderRequestPreview === 'function') {
        renderRequestPreview();
    }

    if (typeof renderRequestBatchSummary === 'function') {
        renderRequestBatchSummary();
    }

    if (typeof renderResponseView === 'function') {
        renderResponseView();
    }
}

function updateLangButtons() {
    document.getElementById('langRu').classList.toggle('active', currentLang === 'ru');
    document.getElementById('langEn').classList.toggle('active', currentLang === 'en');
}

function t(key) {
    return translations[currentLang][key] || key;
}

function formatServerAddressDisplay(host) {
    if (!host) {
        return '127.0.0.1';
    }

    const localMatch = host.match(/^(?:127\.0\.0\.1|localhost)(:\d+)$/i);
    if (localMatch) {
        return localMatch[1];
    }

    return host;
}

// Применяем переводы при загрузке
document.addEventListener('DOMContentLoaded', () => {
    document.documentElement.lang = currentLang;
    applyTranslations();
    updateLangButtons();
    const serverAddressValue = document.getElementById('serverAddressValue');
    if (serverAddressValue) {
        const fullHost = location.host || '127.0.0.1';
        serverAddressValue.textContent = formatServerAddressDisplay(fullHost);
        serverAddressValue.title = fullHost;
        serverAddressValue.setAttribute('aria-label', fullHost);
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

// Server access scope flag
let isUploadsOnlyMode = true;

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

        if (info.access_scope === 'uploads') {
            isUploadsOnlyMode = true;
            const uploadsOnlyIndicator = document.getElementById('uploadsOnlyIndicator');
            if (uploadsOnlyIndicator) {
                uploadsOnlyIndicator.hidden = false;
            }
            document.getElementById('browsePathInput').value = '/';
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
