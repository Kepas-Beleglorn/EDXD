# Pre-Release Checklist

Use this checklist before every release. Copy the table into your release notes or a new issue so each item is explicitly checked off.

## 1. Testing

- [ ] **Local test** — Run `./test_edxd.sh` (or `bash debug_build.sh`) and verify the app starts without errors on your local machine.
- [ ] **GitHub CI** — Push to a branch and confirm the `auto-release` workflow builds successfully on all OS runners in the matrix:
  - `ubuntu-22.04`
  - `ubuntu-24.04`
  - `ubuntu-26.04`
  - `windows-latest`
  - `macos-latest`
  - See `.github/workflows/auto-release.yml` → `strategy.matrix.os`.
- [ ] **Nix build** — Run `nix build` locally and/or confirm the `nix-build` GitHub workflow passes.
  - See `.github/workflows/nix-build.yml`.

## 2. Screenshots

- [ ] **Existing screenshots up to date?** — Review every image in `screenshots.md` and confirm the UI still matches.
- [ ] **New screenshots to add?** — If new features or UI changes were introduced, capture and upload new screenshots, then update `screenshots.md`.
- [ ] **Cloudflare cache** — After updating screenshots on img.edxd.app, clear the Cloudflare cache so new images propagate.

## 3. Documentation

- [ ] **README.md** — Verify features, installation instructions, and binary compatibility table reflect the current release.
- [ ] **edcodex.info** — Update the EDXD entry on [edcodex.info](https://edcodex.info/?m=tools&entry=608) with the latest version info and feature list.
- [ ] **screenshots.md** — Ensure the "SCREENSHOTS TO UPDATE" section is cleared or reflects any remaining pending updates.

## 4. Discord Integration

- [ ] **Discord API tokens** — Confirm the following GitHub secrets are valid and up to date:
  - `DISCORD_WEBHOOK_ANNOUNCE_URL`
  - `DISCORD_WEBHOOK_PINNED_URL`
  - `DISCORD_MESSAGE_ID`
  - See `.github/workflows/discord_release_info.yml`.
- [ ] **Test webhook** (optional) — Trigger the `discord_release_info` workflow manually on a draft release to verify the message posts correctly.

## 5. OS Matrix in Workflows

- [ ] **OS matrix valid?** — Review `.github/workflows/auto-release.yml` → `strategy.matrix.os` and confirm the listed runners still exist and are supported by GitHub Actions.
  - Check for deprecated runner names (e.g., `ubuntu-20.04` was deprecated in 2024).
  - Add new LTS runners as needed (e.g., `ubuntu-28.04` when available).

## 6. Version & Release

- [ ] **pyproject.toml** — Version string matches the intended release version.
- [ ] **Commit message** — Follows the version pattern `vMAJOR.MINOR.PATCH.HOTFIX` so the auto-release workflow triggers.
  - See `VERSIONING.md` for the 4-part versioning policy.
- [ ] **Release notes** — Draft a release body summarizing changes, referencing issues/PRs.

---

> **Tip:** For future releases, copy this file, check off each item as you go, and attach the completed checklist to the release issue or PR.
