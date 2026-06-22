# Dialog Accessibility Tail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separate non-urgent notice dialog semantics from destructive confirm dialog semantics without broad UI refactors.

**Architecture:** Keep the existing shared dialog renderer and add a narrow role selector so `showConfirmDialog()` continues to emit `alertdialog` while `showNoticeDialog()` emits `dialog`. Lock the behavior with browser smoke assertions that invoke both shared helpers directly and verify focus/role contracts independently of feature-specific flows.

**Tech Stack:** Static SPA JavaScript, Playwright browser smoke, Python smoke harness

---

### Task 1: Lock the shared dialog role contract

**Files:**
- Modify: `tools/browser_smoke.playwright.js`
- Modify: `src/data/static/ui/dialogs.js`
- Test: `tools/browser_smoke.playwright.js`

- [ ] **Step 1: Write the failing regression**

Add a helper in `tools/browser_smoke.playwright.js` that opens a notice dialog and a confirm dialog via `page.evaluate()`, then asserts the notice uses `role="dialog"` and the confirm flow uses `role="alertdialog"`.

- [ ] **Step 2: Run smoke to verify it fails**

Run: `python tools/browser_smoke.py --profile lab --mode full`
Expected: FAIL on the new notice-dialog role assertion because `showNoticeDialog()` currently renders `alertdialog`.

- [ ] **Step 3: Write the minimal implementation**

Adjust `showAppDialog()` in `src/data/static/ui/dialogs.js` to accept a role parameter and set it to `dialog` for `showNoticeDialog()` while leaving `showConfirmDialog()` on `alertdialog`.

- [ ] **Step 4: Run smoke to verify it passes**

Run: `python tools/browser_smoke.py --profile lab --mode full`
Expected: PASS with the new notice/confirm role contract covered in the happy path.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-06-22-dialog-a11y-tail.md \
  src/data/static/ui/dialogs.js \
  tools/browser_smoke.playwright.js
git commit -m "Split notice and confirm dialog roles"
```
