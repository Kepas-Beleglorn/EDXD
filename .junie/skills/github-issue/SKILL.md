---
name: github-issue
description: Creates well-structured GitHub issues via the `gh` CLI. Never implements solutions — issue first, refine later, implement only when explicitly asked.
---

# GitHub Issue Creation Skill

Creates well-structured GitHub issues via the `gh` CLI. **Never implements solutions** — issue first, refine later, implement only when explicitly asked.

## When to trigger

- The user asks to create, file, or open a GitHub issue.
- The user reports a bug, requests a feature, or identifies technical debt and wants it tracked.
- The phrase "create an issue" or "file an issue" appears in any form.

**DO NOT trigger** when the user asks to fix something directly without mentioning issues — that may be a direct implementation request.

## The golden rule

> **Issue first, never implement.** When the user asks for an issue, create only the issue. Do not propose code changes, do not edit files, do not write implementations. The user will ask for implementation separately when ready.

## Prerequisites

Before creating an issue, verify:

1. **`gh` CLI is available** — run `which gh && gh auth status` to confirm authentication.
2. **Git remote is configured** — run `git remote -v` to confirm the origin repository URL.
3. **Git user is configured** — run `git config user.name && git config user.email`.

If any prerequisite fails, inform the user and stop — do not attempt to fix the environment unless explicitly asked.

## Issue creation algorithm

### 1. Understand the problem

From the user's description, extract:

- **What is broken or desired** — the core problem statement.
- **Expected vs actual behavior** — what should happen vs what happens now.
- **Relevant files and code locations** — if the user mentions or you can identify specific files, methods, or line ranges.
- **Any suggested fix direction** — only if the user provides one; do not invent solutions.

If the description is vague, ask focused clarifying questions before proceeding. Do not guess at the root cause.

### 2. Craft the issue body

Structure every issue body as a **user story** with these Markdown sections (omit sections that don't apply):

```markdown
## As a ... I want to ... so that ...

One-sentence user story describing the role, desire, and benefit.

## Acceptance Criteria

- [ ] First actionable item or condition
- [ ] Second actionable item or condition
- [ ] Third actionable item or condition

## Current Behavior

What actually happens now. Bullet points if there are multiple symptoms.

## Hints

(Optional) Brief notes on where in the codebase the change should be made, based on code analysis.

- **File:** `path/to/file.ext`
- **Method/Function:** `methodName()` (around line N)
- Brief note about the code context.

Created by Junie - <yyyy-MM-dd hh:mm:ss>
```

Rules for the body:

- Use backticks for all code symbols, file paths, method names, and technical terms.
- Keep it concise — the issue should be scannable.
- Never include implementation-level code changes or patches.
- Write in the same language as the user's issue description.
- The **last line** must always be `Created by Junie - <yyyy-MM-dd hh:mm:ss>` with the current local date and time.
- The acceptance criteria should be a checklist of actionable items using `- [ ]` Markdown syntax.

### 3. Create the issue via `gh` CLI

Write the body to a temporary file, then create the issue:

    gh issue create --title "Short descriptive title" --body-file /tmp/issue-body.md

Using `--body-file` avoids shell escaping issues with backticks and special characters in the body.

**DO NOT assign labels or users.** Use no `--label` or `--assignee` flags. That is handled by a separate workflow.

### 4. Verify and report

After creation, verify the issue exists:

    gh issue view <NUMBER>

Report back to the user with:

- The issue number and URL.
- Confirmation that the body is properly formatted.
- Explicit statement: **No code changes made — issue only, as requested.**

## Issue title conventions

On **creating** a new issue, prefix the title with a short type identifier:

- **Bug:** Prefix with `x:` — e.g., "x: current_system not written to route JSON"
- **Enhancement:** Prefix with `e:` — e.g., "e: Add export to CSV"
- **Refactoring:** Prefix with `r:` — e.g., "r: Extract clipboard logic"

Keep the title under 70 characters when possible.

**When editing existing issues, NEVER add the prefix.** The prefix is for new issues only.

## Edge cases

- **Duplicate check:** Before creating, briefly scan open issues with `gh issue list --state open` to avoid obvious duplicates. If a similar issue exists, mention it to the user.
- **Multi-part issues:** If the user's request clearly describes multiple independent issues, create separate issues and report all numbers.
- **Blocking issues:** If the user mentions the issue blocks other work, add a note in the body. Do not assign labels or users — that is handled by a workflow.
