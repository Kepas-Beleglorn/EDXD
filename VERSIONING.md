# Versioning policy — MAJOR.MINOR.PATCH.HOTFIX

We use a 4-part numeric version format: MAJOR.MINOR.PATCH.HOTFIX

- Format: vMAJOR.MINOR.PATCH.HOTFIX (example: v2.4.1.0)
- Always four integers separated by dots. If there is no hotfix, set HOTFIX to 0.

Rules
- MAJOR
  - Increment for incompatible API changes or major redesigns.
  - When MAJOR is incremented, reset MINOR, PATCH, and HOTFIX to 0.
- MINOR
  - Increment for new, backwards-compatible features.
  - When MINOR is incremented, reset PATCH and HOTFIX to 0.
- PATCH
  - Increment for backwards-compatible bug fixes and small improvements.
  - When PATCH is incremented, reset HOTFIX to 0.
- HOTFIX
  - Increment for urgent, post-release fixes that must be released immediately without changing the intended PATCH semantics.
  - HOTFIX should be non-negative integer starting at 0.

Tagging
- Use annotated git tags prefixed with `v`: `vMAJOR.MINOR.PATCH.HOTFIX`
- Example: `git tag -a v1.2.3.1 -m "Release v1.2.3.1"`

Releases
- Release title: `Release vMAJOR.MINOR.PATCH.HOTFIX`
- Release body: summary of changes, reference to issues/PRs, and a short changelog.
- If a Hotfix release is made, indicate which release it patches (e.g., "Hotfix for v1.2.3.0 — fixes crash on startup").

VERSION file
- Keep a plain `VERSION` file at the repository root containing only the numeric version (e.g., `1.2.3.0`). Use this as the single source of truth for scripts and CI.

Notes
- If we later add automation for changelogs or releases, ensure the tooling reads and respects this 4-part format.
- For pre-releases, consider appending a suffix: `v1.2.3.0-rc.1` (optional — still keep the base four-part version).