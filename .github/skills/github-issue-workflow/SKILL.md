---
name: github-issue-workflow
description: Complete GitHub workflow to create issues, branches, commits, and pull requests. Use when asked to create a GitHub issue, open a PR, push a branch, report a bug, add a feature, or manage the full GitHub development lifecycle. Triggers on keywords: issue, PR, pull request, branch, bug report, feature request, push changes, open ticket.
metadata:
  author: custom
  version: "1.1"
  compatibility: Requires GitHub MCP server to be active
---

# GitHub Issue Workflow Skill

## ⚠️ PREREQUISITE: GitHub MCP Check

**Before doing ANYTHING else**, verify that the GitHub MCP server is active and available.

- Attempt to call any GitHub MCP tool (e.g., list repositories or get authenticated user).
- If the tool call fails or the GitHub MCP server is not listed as available:
  - **STOP immediately**.
  - Notify the user with this exact message:

  > ❌ **GitHub MCP server is not active.**
  > This skill requires the GitHub MCP server to function.
  > Please enable it in your MCP settings (VS Code → Settings → MCP Servers) and try again.

- Only proceed if the GitHub MCP server responds successfully.

---

## Overview

This skill automates the full GitHub development workflow in 7 ordered steps:

1. Create a structured GitHub Issue
2. Create a new branch from `develop` named after the issue number
3. Apply code changes with atomic commits following Conventional Commits
4. **Quality Gate** — validate SOLID principles and no code smells before pushing
5. Push the branch to the remote repository
6. Open a Pull Request from the branch toward `develop`, linking the issue
7. **CI Verification** — monitor GitHub Actions and confirm the PR passes all checks

---

## Step 1 — Create GitHub Issue

### Issue Type Detection Rules

Determine the type automatically from the task description:

| Condition | Type |
|---|---|
| Introduces a new capability | `Feature` |
| Fixes incorrect or unexpected behavior | `Bug` |
| Improves structure without behavior change | `Refactor` |
| Infrastructure, CI/CD, config, tooling | `Chore` |

### Issue Title Format

```
[{Type}] {short action description in imperative mood}
```

**Examples:**
- `[Feature] Permitir cambio de prioridad de ticket por administrador`
- `[Bug] Corregir error de validación en formulario de login`
- `[Refactor] Extraer lógica de cálculo de precios a servicio dedicado`
- `[Chore] Actualizar dependencias de seguridad en package.json`

### Issue Body Structure

Use the following Markdown template for the issue body:

```markdown
## 📋 Description
<!-- Clear summary of what needs to be done or what is broken -->

## 🎯 Goal / Expected Behavior
<!-- What should happen when this issue is resolved -->

## 🐛 Current Behavior (for Bugs only)
<!-- What is currently happening incorrectly -->

## ✅ Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## 🔗 Context / References
<!-- Links, related issues, screenshots, or any relevant context -->
```

### Labels to assign

- `feature` → for Feature type
- `bug` → for Bug type
- `refactor` → for Refactor type
- `chore` → for Chore type

### MCP Action

Use the GitHub MCP tool to create the issue. Capture the **issue number** returned (e.g., `#42`) — it will be used in subsequent steps.

---

## Step 2 — Create Branch from `develop`

### Branch Naming Convention

```
{type}/{issue-number}-{short-kebab-case-description}
```

**Examples:**
- `feature/42-cambio-prioridad-ticket`
- `bug/17-validacion-formulario-login`
- `refactor/31-extraccion-servicio-precios`
- `chore/55-actualizar-dependencias`

### Rules
- Always base the new branch off `develop` (not `main` or any other branch).
- Use lowercase and hyphens only.
- Keep the description under 5 words.

### MCP Action

1. Use the GitHub MCP tool to create the branch from the `develop` ref. Confirm the branch was created before continuing.
2. **Link the branch to the issue** — Use the GitHub MCP tool to associate the newly created branch with the issue created in Step 1 (e.g., `create_issue_development_link` or equivalent), passing the issue number and branch name.

### Branch Linking Fallback Strategy

> ⚠️ **Important:** The GitHub API does not expose a direct endpoint to link a branch to an issue's Development section. The GitHub MCP is therefore unlikely to support this action. Use the following strategy:

```
TRY:
  Link branch to issue via GitHub MCP tool
  (only if the MCP explicitly exposes this capability)

IF MCP tool not available OR linking fails:
  REQUIRED FALLBACK → run via terminal/console:
    gh issue develop {ISSUE_NUMBER} --name {BRANCH_NAME} --repo {OWNER}/{REPO}

IF terminal/console is also unavailable OR command fails:
  STOP the entire workflow.
  Notify the user:

  ❌ No fue posible vincular la rama al issue.
  El MCP de GitHub no expone esta herramienta y no hay acceso a consola.
  Por favor, vincula la rama manualmente desde GitHub:
  Issue → sección "Development" → "Link a branch" → selecciona `{BRANCH_NAME}`.
  Una vez vinculada, avísame para continuar con el resto del workflow.

  Wait for user confirmation before proceeding to Step 3.
```

> **Note:** The `gh issue develop` command requires the [GitHub CLI](https://cli.github.com/) installed and authenticated.

---

## Step 3 — Apply Code Changes with Atomic Commits

### Commit Convention (Conventional Commits)

```
{type}({scope}): {short description in imperative mood}
```

**Allowed types:**

| Type | When to use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behavior change |
| `chore` | Build, config, dependencies |
| `test` | Adding or updating tests |
| `docs` | Documentation only |
| `style` | Formatting, missing semicolons, etc. |

**Examples:**
- `feat(auth): agregar validación de token JWT`
- `fix(form): corregir error de submit en campos opcionales`
- `refactor(pricing): extraer cálculo de descuentos a PricingService`

### Atomic Commit Rules
- Each commit must represent **one logical change**.
- Do NOT bundle unrelated changes in a single commit.
- If multiple files are changed for the same logical reason, they can be in one commit.
- Each commit message must clearly describe what changed and why.

---

## Step 4 — Quality Gate ✅

**This step is MANDATORY before pushing any code.**

Evaluate every file that was modified or created against the following criteria:

### SOLID Principles Checklist

| Principle | Check |
|---|---|
| **S** — Single Responsibility | Each class/module does ONE thing only |
| **O** — Open/Closed | Extendable without modifying existing code |
| **L** — Liskov Substitution | Subclasses/implementations are interchangeable with their base |
| **I** — Interface Segregation | No class is forced to depend on methods it doesn't use |
| **D** — Dependency Inversion | High-level modules depend on abstractions, not concretions |

### Code Smell Checklist

Detect and eliminate any of the following:

- Long Methods (> ~20 lines doing multiple things)
- Large Classes (too many responsibilities)
- Duplicate Code (copy-pasted logic)
- Magic Numbers / Strings (unexplained literals)
- Deep Nesting (> 3 levels of indentation)
- God Objects (a class that knows too much)
- Feature Envy (a method that uses another class's data more than its own)
- Dead Code (unreachable or unused code)
- Poor Naming (single-letter variables, misleading names)
- Missing Error Handling

### Quality Gate Decision

```
IF any SOLID violation found OR any code smell detected:
  → Fix the code automatically to comply
  → Re-evaluate until all checks pass
  → Only then proceed to Step 5

IF all checks pass:
  → Proceed to Step 5
```

**Do NOT push code that fails the Quality Gate. Fix it first.**

---

## Step 5 — Push Branch to Remote

Use the GitHub MCP tool to push all commits to the remote branch created in Step 2.

Confirm the push was successful before proceeding.

---

## Step 6 — Open Pull Request

### ⚠️ Strict Rule: One PR per Issue

**Each PR must address exactly one issue.** It is forbidden to include changes from multiple issues in a single PR, even if the changes are related. If the user requests this, stop and explain:

> ❌ No es posible incluir múltiples issues en un mismo PR.
> Cada issue debe tener su propia rama y su propio PR.
> Por favor, ejecuta el workflow por separado para cada issue.

### PR Title Format

```
[{Type}] #{issue-number} — {same description as issue title}
```

**Example:**
- `[Feature] #42 — Permitir cambio de prioridad de ticket por administrador`

### PR Body Structure

```markdown
## 📋 Summary
<!-- Brief description of what this PR does -->

## 🔗 Related Issue
Fixes #ISSUE_NUMBER

## 🔄 Changes
<!-- List of key changes introduced -->

## ✅ Quality Gate
- [x] SOLID principles verified
- [x] No code smells detected
- [x] Atomic commits with Conventional Commits format

## 📝 Notes
<!-- Optional: deployment notes, migration steps, or reviewer hints -->
```

### Key Requirement

The PR description **MUST** include one of the following to auto-close the issue:
- `Fixes #ISSUE_NUMBER`
- `Closes #ISSUE_NUMBER`

Replace `ISSUE_NUMBER` with the actual number captured in Step 1.

### PR Settings
- **Base branch:** `develop`
- **Head branch:** the branch created in Step 2
- **Draft:** only if work is incomplete

### MCP Action

Use the GitHub MCP tool to create the pull request with the above title and body. Capture the **PR number** returned — it will be used in Step 7.

---

## Step 7 — CI Verification (GitHub Actions)

**This is the final step.** After the PR is open, verify that all GitHub Actions workflows triggered by the PR pass successfully.

### 7.1 — Discover Workflow Runs

Use the GitHub MCP tool to list the check runs or workflow runs associated with the PR's head commit SHA.

```
GET /repos/{owner}/{repo}/commits/{head_sha}/check-runs
```

> If the MCP exposes a tool like `list_check_runs_for_ref` or `get_pull_request_checks`, use it directly.

**Wait up to 60 seconds** for GitHub Actions to register the triggered workflows before the first poll.

### 7.2 — Polling Strategy

CI pipelines may take time. Use the following polling loop:

```
MAX_ATTEMPTS = 20
POLL_INTERVAL = 30 seconds
TIMEOUT = 10 minutes

FOR attempt IN 1..MAX_ATTEMPTS:
  Fetch current status of all check runs for the PR

  IF all check runs have status = "completed":
    EXIT loop → proceed to 7.3

  IF any check run has status = "in_progress" OR "queued":
    Notify user: "⏳ CI still running... (attempt {attempt}/{MAX_ATTEMPTS})"
    Wait POLL_INTERVAL seconds
    Continue loop

IF loop ends without completion:
  → Notify user of timeout (see 7.4 — Timeout Handling)
```

> ⚠️ **Important:** Do not poll more frequently than every 30 seconds to avoid rate-limiting by the GitHub API.

### 7.3 — Evaluate Results

Once all check runs are completed, evaluate the conclusion of each one:

| Conclusion | Meaning |
|---|---|
| `success` | ✅ Check passed |
| `failure` | ❌ Check failed — requires attention |
| `cancelled` | ⚠️ Check was cancelled |
| `skipped` | ℹ️ Check was intentionally skipped |
| `timed_out` | ❌ Check exceeded its time limit |
| `action_required` | ⚠️ Manual action needed (e.g. approval gate) |
| `neutral` | ℹ️ Informational only, does not block |

#### All checks passed

If every required check has conclusion `success` (or `skipped` / `neutral` for non-blocking ones):

```
✅ CI passed — all GitHub Actions checks completed successfully.

PR #PR_NUMBER is ready for review.
```

#### One or more checks failed

If any required check has conclusion `failure` or `timed_out`:

```
❌ CI failed on PR #PR_NUMBER.

The following checks did not pass:
  - {check_name}: {conclusion} — {details_url}

Suggested next steps:
  1. Review the failed workflow logs at the URL above.
  2. Fix the root cause in the codebase.
  3. Commit the fix to branch {BRANCH_NAME} following Conventional Commits (Step 3).
  4. Push the fix (Step 5) — GitHub Actions will re-trigger automatically.
  5. Re-run Step 7 to verify CI passes.
```

> **Note:** If a fix is committed and pushed, re-execute this Step 7 from the beginning to re-verify CI on the new commit.

### 7.4 — Timeout Handling

If the polling loop exhausts all attempts without CI completing:

```
⚠️ CI verification timed out after 10 minutes.

The following checks are still running or pending:
  - {check_name}: {status}

The PR #PR_NUMBER has been created, but CI status could not be confirmed.

Please monitor the workflow runs manually at:
  https://github.com/{owner}/{repo}/pull/{PR_NUMBER}/checks

Once CI completes, verify all checks pass before requesting a review.
```

### 7.5 — Fallback: MCP Cannot Access Check Runs

If the GitHub MCP does not expose check run tools, fall back to the GitHub CLI:

```bash
# Poll check status via CLI
gh pr checks {PR_NUMBER} --repo {OWNER}/{REPO} --watch
```

If CLI is also unavailable:

```
⚠️ No fue posible verificar el CI automáticamente.
El MCP de GitHub no expone herramientas de check runs y no hay acceso a consola.

Por favor, verifica manualmente el estado del CI en:
  https://github.com/{owner}/{repo}/pull/{PR_NUMBER}/checks

Avísame si algún check falla para ayudarte a diagnosticar el problema.
```

---

## Summary Checklist

After completing all steps, confirm:

- [ ] ✅ GitHub MCP was verified active
- [ ] ✅ Issue created with correct title format `[Type] description`
- [ ] ✅ Issue body uses structured template
- [ ] ✅ Correct label assigned
- [ ] ✅ Issue added to GitHub Project (visible in backlog)
- [ ] ✅ Branch created from `develop` with issue number in name
- [ ] ✅ Branch linked to the issue via `gh issue develop` (Development section)
- [ ] ✅ All commits are atomic and follow Conventional Commits
- [ ] ✅ Quality Gate passed (SOLID + no code smells)
- [ ] ✅ Branch pushed to remote
- [ ] ✅ PR opened from feature branch → `develop`
- [ ] ✅ PR description contains `Fixes #ISSUE_NUMBER` or `Closes #ISSUE_NUMBER`
- [ ] ✅ CI verified — all GitHub Actions checks passed on PR

---

## Common Edge Cases

- **Multiple issues requested in one PR:** Stop and explain the 1 PR per issue rule. Run the workflow separately for each issue.
- **Branch `develop` doesn't exist:** Notify the user and ask which base branch to use instead.
- **Issue number not returned by MCP:** Abort and ask the user to provide it manually.
- **Quality Gate keeps failing:** Show the specific violations found, apply fixes, and re-evaluate. Limit auto-fix attempts to 3 before asking the user for input.
- **GitHub MCP not available:** Stop the entire workflow and show the prerequisite error message.
- **Merge conflicts on PR creation:** Notify the user that conflicts exist and suggest rebasing the branch onto `develop` before proceeding.
- **CI fails after fix commit:** Re-execute Step 7 from scratch against the new head SHA. Do not assume the previous results are still valid.
- **No workflows triggered on PR:** This may mean no GitHub Actions are configured in the repository. Notify the user and skip Step 7 gracefully — do not treat absence of workflows as a failure.
- **`action_required` conclusion:** This typically means a required approval gate (e.g. environment protection rule). Notify the user and do not treat it as a CI failure.