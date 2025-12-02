# EDXD/version_check.py
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional, Tuple


def _http_get(url: str, timeout: float = 5.0) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "EDXD-VersionCheck/1.0",
            # Optional: use a token if provided to raise the rate limit
            **({"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"} if "GITHUB_TOKEN" in os.environ else {})
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def _normalize(ver: str) -> str:
    # strip leading "v" or "V"
    if ver and (ver[0] in "vV"):
        ver = ver[1:]
    return ver.strip()

def _cmp_numeric(v1: str, v2: str) -> int:
    """Compare numeric dotted versions like 0.4.6.123. Returns -1/0/1."""
    def parts(v: str):
        out = []
        for p in _normalize(v).split("."):
            try:
                out.append(int(p))
            except ValueError:
                # handle non-numeric tails gracefully (e.g., 1.2.3-rc1 -> 1.2.3, rc as -1)
                num = "".join(ch for ch in p if ch.isdigit())
                out.append(int(num) if num else 0)
        return out
    a, b = parts(v1), parts(v2)
    # pad shorter
    L = max(len(a), len(b))
    a += [0] * (L - len(a))
    b += [0] * (L - len(b))
    return (a > b) - (a < b)

def fetch_latest_release_version(owner: str, repo: str, include_prereleases: bool = False) -> Optional[str]:
    """
    Returns the latest version string from GitHub Releases.
    If include_prereleases is False, uses /releases/latest.
    Otherwise scans /releases and picks the first non-draft (and prerelease if allowed).
    """
    base = f"https://api.github.com/repos/{owner}/{repo}/releases"

    try:
        if not include_prereleases:
            data = json.loads(_http_get(base + "/latest").decode("utf-8"))
            ver = data.get("tag_name") or data.get("name") or ""
            return _normalize(ver) or None
        else:
            arr = json.loads(_http_get(base).decode("utf-8"))
            for rel in arr:
                if rel.get("draft"):
                    continue
                if not include_prereleases and rel.get("prerelease"):
                    continue
                ver = rel.get("tag_name") or rel.get("name") or ""
                ver = _normalize(ver)
                if ver:
                    return ver
            return None
    except urllib.error.HTTPError as e:
        # e.g., no releases yet -> 404 on /latest
        return None
    except Exception:
        return None

def is_update_available(current_version: str, latest_version: str) -> bool:
    if not latest_version:
        return False
    return _cmp_numeric(latest_version, current_version) > 0

def check_github_for_update(current_version: str, owner: str, repo: str,
                            include_prereleases: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Returns (update_available, latest_version_or_None)
    """
    latest = fetch_latest_release_version(owner, repo, include_prereleases=include_prereleases)
    return (is_update_available(current_version, latest), latest)
