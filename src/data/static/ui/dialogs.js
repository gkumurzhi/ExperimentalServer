// ===== Shared app dialogs =====
let activeDialogId = null;
let activeDialogKeyHandler = null;
let activeDialogReturnFocusEl = null;
let activeDialogResolve = null;
let activeDialogRestoreFocusOnConfirm = false;

function getDialogFocusable(modal) {
    return Array.from(
        modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
    ).filter(el => !el.disabled && el.offsetParent !== null);
}

function getActiveDialogElement() {
    return activeDialogId ? document.getElementById(activeDialogId) : null;
}

function finishActiveDialog(result) {
    const modal = getActiveDialogElement();
    const resolve = activeDialogResolve;
    const focusTarget = (!result || activeDialogRestoreFocusOnConfirm) ? activeDialogReturnFocusEl : null;

    if (activeDialogKeyHandler) {
        document.removeEventListener('keydown', activeDialogKeyHandler);
        activeDialogKeyHandler = null;
    }

    activeDialogId = null;
    activeDialogResolve = null;
    activeDialogReturnFocusEl = null;
    activeDialogRestoreFocusOnConfirm = false;

    if (modal) {
        modal.remove();
    }

    if (focusTarget && focusTarget.isConnected && !focusTarget.disabled && typeof focusTarget.focus === 'function') {
        focusTarget.focus();
    }

    if (resolve) {
        resolve(result);
    }
}

function closeActiveDialog() {
    finishActiveDialog(false);
}

function closeAppDialog() {
    closeActiveDialog();
}

function openManagedDialog({
    dialogId,
    markup,
    triggerEl = null,
    initialFocusSelector = '',
    restoreFocusOnConfirm = false,
    onAction = null,
}) {
    closeActiveDialog();

    const activeElement = document.activeElement;
    activeDialogId = dialogId;
    activeDialogReturnFocusEl = triggerEl || (activeElement instanceof HTMLElement ? activeElement : null);
    activeDialogRestoreFocusOnConfirm = restoreFocusOnConfirm;

    const modal = document.createElement('div');
    modal.id = dialogId;
    modal.innerHTML = markup;
    document.body.appendChild(modal);

    modal.addEventListener('click', async (event) => {
        if (event.target === modal.querySelector('.modal-overlay')) {
            finishActiveDialog(false);
            return;
        }

        const actionButton = event.target.closest('[data-dialog-action]');
        if (!actionButton) return;

        if (onAction) {
            const result = await onAction(actionButton.dataset.dialogAction || '', modal, actionButton);
            if (typeof result === 'boolean') {
                finishActiveDialog(result);
            }
            return;
        }

        finishActiveDialog(actionButton.dataset.dialogAction === 'confirm');
    });

    activeDialogKeyHandler = (event) => {
        if (event.key === 'Escape') {
            finishActiveDialog(false);
            return;
        }

        if (event.key !== 'Tab') {
            return;
        }

        const focusable = getDialogFocusable(modal);
        if (focusable.length === 0) {
            return;
        }

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    };
    document.addEventListener('keydown', activeDialogKeyHandler);

    const initialFocusEl = (initialFocusSelector && modal.querySelector(initialFocusSelector)) || getDialogFocusable(modal)[0];
    if (initialFocusEl) {
        initialFocusEl.focus();
    }

    return modal;
}

function showAppDialog({
    title,
    message,
    details = '',
    confirmLabel,
    cancelLabel = t('smuggleCancel'),
    confirmClassName = 'btn-info',
    triggerEl = null,
    showCancel = true,
    initialFocus = 'confirm',
    restoreFocusOnConfirm = false,
}) {
    openManagedDialog({
        dialogId: 'appDialog',
        triggerEl,
        initialFocusSelector: initialFocus === 'cancel' && showCancel
            ? '[data-dialog-action="cancel"]'
            : '[data-dialog-action="confirm"]',
        restoreFocusOnConfirm,
        markup: `
        <div class="modal-overlay">
            <div class="modal-content app-dialog" role="alertdialog" aria-modal="true" aria-labelledby="appDialogTitle" aria-describedby="appDialogMessage${details ? ' appDialogDetails' : ''}">
                <div class="app-dialog__header">
                    <h3 class="app-dialog__title" id="appDialogTitle">${esc(title)}</h3>
                </div>
                <div class="app-dialog__body">
                    <p class="app-dialog__message" id="appDialogMessage">${esc(message)}</p>
                    ${details ? `<div class="app-dialog__details" id="appDialogDetails">${esc(details)}</div>` : ''}
                </div>
                <div class="modal-actions app-dialog__actions">
                    ${showCancel ? `<button type="button" class="btn-ghost" data-dialog-action="cancel">${esc(cancelLabel)}</button>` : ''}
                    <button type="button" class="${esc(confirmClassName)}" data-dialog-action="confirm">${esc(confirmLabel)}</button>
                </div>
            </div>
        </div>
    `,
    });

    return new Promise(resolve => {
        activeDialogResolve = resolve;
    });
}

function showConfirmDialog(options) {
    return showAppDialog({
        title: options.title,
        message: options.message,
        details: options.details,
        confirmLabel: options.confirmLabel,
        cancelLabel: options.cancelLabel || t('smuggleCancel'),
        confirmClassName: options.confirmClassName || 'btn-danger',
        triggerEl: options.triggerEl,
        showCancel: true,
        initialFocus: options.initialFocus || 'cancel',
        restoreFocusOnConfirm: Boolean(options.restoreFocusOnConfirm),
    });
}

function showNoticeDialog(options) {
    return showAppDialog({
        title: options.title,
        message: options.message,
        details: options.details,
        confirmLabel: options.confirmLabel || t('okBtn'),
        confirmClassName: options.confirmClassName || 'btn-info',
        triggerEl: options.triggerEl,
        showCancel: false,
        initialFocus: 'confirm',
        restoreFocusOnConfirm: true,
    });
}
