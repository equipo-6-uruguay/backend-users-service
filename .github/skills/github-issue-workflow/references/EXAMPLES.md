# GitHub Issue Workflow — Examples Reference

## Full Workflow Example: Bug Fix

### Input
> "There's a bug where users can submit the login form with an empty email field."

---

### Step 1: Issue Created

**Title:** `[Bug] Corregir validación de campo email en formulario de login`

**Body:**
```markdown
## 📋 Description
Users can submit the login form without providing an email address, bypassing client-side validation.

## 🎯 Expected Behavior
The submit button should be disabled and an error message should appear when the email field is empty.

## 🐛 Current Behavior
Form submits successfully with an empty email, causing a 500 error from the API.

## ✅ Acceptance Criteria
- [ ] Email field cannot be empty on form submit
- [ ] Error message displays: "El email es requerido"
- [ ] API is never called with an empty email

## 🔗 Context / References
Reported by QA team. Affects login page only.
```

**Label:** `bug`
**Issue number returned:** `#23`

---

### Step 2: Branch Created

```
bug/23-validacion-email-login
```
Based off: `develop`

---

### Step 3: Commits

```
fix(login): agregar validación de campo email vacío en LoginForm
test(login): agregar test unitario para validación de email en LoginForm
```

---

### Step 4: Quality Gate

- ✅ Single Responsibility: `LoginForm` only handles form display, validation moved to `useLoginValidation` hook
- ✅ No magic strings: error messages extracted to constants
- ✅ No duplicate code: validation logic is reused
- ✅ All checks pass → proceed to push

---

### Step 5: Branch Pushed

`bug/23-validacion-email-login` pushed to remote ✅

---

### Step 6: Pull Request

**Title:** `[Bug] #23 — Corregir validación de campo email en formulario de login`

**Body:**
```markdown
## 📋 Summary
Adds client-side validation to prevent login form submission with empty email field.

## 🔗 Related Issue
Fixes #23

## 🔄 Changes
- Added `useLoginValidation` hook with email required rule
- Disabled submit button when email is empty
- Added error message display component

## ✅ Quality Gate
- [x] SOLID principles verified
- [x] No code smells detected
- [x] Atomic commits with Conventional Commits format
```

---

## Issue Type Detection — Quick Reference

| User says... | Detected type |
|---|---|
| "Add a new feature to..." | Feature |
| "There's a bug where..." | Bug |
| "I want to refactor..." | Refactor |
| "Update the CI pipeline..." | Chore |
| "Fix a performance issue..." | Bug or Refactor (use context) |

## Branch Name Examples

| Issue # | Type | Description | Branch |
|---|---|---|---|
| 12 | Feature | export reports to PDF | `feature/12-exportar-reportes-pdf` |
| 33 | Bug | fix null pointer on checkout | `bug/33-null-pointer-checkout` |
| 7 | Refactor | extract payment logic | `refactor/7-extraer-logica-pagos` |
| 44 | Chore | upgrade node to v20 | `chore/44-upgrade-node-v20` |