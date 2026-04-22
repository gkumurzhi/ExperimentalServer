// ===== UI bootstrap =====
checkServerMode();

window.addEventListener('beforeunload', (e) => {
    if (notepadIsDirty) {
        e.preventDefault();
    }
});

document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        const notepadTab = document.getElementById('notepad-tab');
        if (notepadTab && notepadTab.classList.contains('active')) {
            e.preventDefault();
            notepadSave();
        }
    }

    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const uploadTab = document.getElementById('upload-tab');
        if (uploadTab && uploadTab.classList.contains('active')) {
            e.preventDefault();
            uploadAllFiles();
        }
    }
});
