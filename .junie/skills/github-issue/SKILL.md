---
name: github-issue
description: Used for creating new issues for the repo.
---

# GitHub Issue Creation

Guidelines for creating and editing GitHub issues in the EDXD repository.

## When to Use

Use this skill when the user asks to create, edit, or manage GitHub issues.

## Issue Creation Rules

### 1. Title Prefix

Every new issue title **must** start with one of the following prefixes:

| Prefix | Type | Description |
|--------|------|-------------|
| `e:` | Enhancement | New features, improvements, UI changes |
| `x:` | Bug | Something broken or not working as expected |
| `r:` | Refactoring | Code restructuring without behavioral changes |

Example: `x: App crashes when loading journal files on Wayland`

### 2. User Story Format

Write the issue body as a **user story** with the following structure:

```markdown
**As a** [type of user],
**I want** [some goal],
**So that** [some reason/value].

## Acceptance Criteria

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Tests pass
- [ ] Code reviewed
```

Include a **checklist of tasks** leading to the Definition of Done (DOD).

### 3. No Labels or Assignees

- **Do not** set any labels on issue creation.
- **Do not** set assignees.
- A GitHub workflow automatically handles labeling based on the title prefix (`e:` / `x:` / `r:`) and adds the issue to the linked EDXD project.

### 4. Default Repository

- Default repository: **Kepas-Beleglorn/EDXD**
- If the user does not specify a repository, **ask** which repository the issue belongs to before creating.

### 5. Signature

At the end of every new issue body or comment, append a signature line:

```
YYYY-MM-dd, created with Junie Agent
```

Use the current date in `YYYY-MM-dd` format.

### 6. Issue Linking

When the user provides issue numbers and a relationship type, use GitHub's issue linking keywords in the body or a comment:

| Relationship | Keyword |
|--------------|---------|
| Blocks | `blocks #<issue>` |
| Blocked by | `blocked by #<issue>` |
| Related to | `relates to #<issue>` |
| Parent | `part of #<issue>` |
| Child | `blocks #<issue>` (from parent's perspective) |

Follow the user's explicit instructions for which relationship to use.

### 7. Attachments

If the user provides screenshots or files (e.g., log files), include them in the issue body. For files, upload them as attachments or paste relevant content inline.

## Editing Existing Issues

### Title Rules

- **Never** add a prefix to an existing issue's title when editing.
- The title should remain as-is unless the user explicitly requests a change.

### Body Updates

When editing an existing issue, follow the user's instructions for what to update. Maintain the existing structure unless asked to reformat.

## API Usage

Use the GitHub REST API with the `GH_TOKEN` environment variable for authentication:

```bash
# Create an issue
curl -s -X POST \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/Kepas-Beleglorn/EDXD/issues \
  -d '{"title":"<title>","body":"<body>"}'

# Update an issue
curl -s -X PATCH \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/Kepas-Beleglorn/EDXD/issues/<number> \
  -d '{"body":"<updated body>"}'

# Add a comment
curl -s -X POST \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/Kepas-Beleglorn/EDXD/issues/<number>/comments \
  -d '{"body":"<comment>"}'
```

## Workflow Summary

1. Determine issue type (`e:` / `x:` / `r:`) from the user's request.
2. If the repository is not specified, ask the user (default: EDXD).
3. Draft the issue as a user story with acceptance criteria and DOD checklist.
4. Add the signature line with the current date.
5. If linking to other issues, include the appropriate linking keywords.
6. Create the issue via the GitHub API without labels or assignees.
7. Report back the issue URL to the user.
