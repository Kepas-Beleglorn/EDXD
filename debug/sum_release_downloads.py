#!/usr/bin/env python3
"""
sum_release_downloads.py

Fetch GitHub releases for owner/repo and print totals and/or detailed asset rows.
Also can save a timestamped snapshot (JSON) of the current cumulative counts for later diffing.

Usage:
  python sum_release_downloads.py owner repo [--token TOKEN] [--detailed] [--per-release] [--json]
  python sum_release_downloads.py owner repo --save-snapshot snapshots/2025-11-06T00:00:00Z.json

Token can also be provided via the GITHUB_TOKEN environment variable.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests

API_ACCEPT = "application/vnd.github+json"


def get_releases(owner: str, repo: str, token: str | None = None):
    headers = {"Accept": API_ACCEPT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=100"
    releases = []
    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 404:
            raise SystemExit(f"Repository not found: {owner}/{repo}")
        if resp.status_code != 200:
            raise SystemExit(f"GitHub API error: {resp.status_code} {resp.text}")
        batch = resp.json()
        releases.extend(batch)
        url = resp.links.get("next", {}).get("url")
    return releases


def build_snapshot(owner: str, repo: str, releases: list):
    """
    Build a snapshot dict with top-level metadata and per-asset cumulative counts.
    Structure:
    {
      "owner": "...",
      "repo": "...",
      "snapshot_at": "<ISO8601 UTC>",
      "releases": [
         {
            "id": ...,
            "tag_name": "...",
            "name": "...",
            "published_at": "...",
            "assets": [
               {
                  "id": ...,
                  "name": "...",
                  "created_at": "...",
                  "browser_download_url": "...",
                  "download_count": N
               }, ...
            ]
         }, ...
      ]
    }
    """
    snap = {
        "owner": owner,
        "repo": repo,
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "releases": []
    }
    for r in releases:
        release_entry = {
            "id": r.get("id"),
            "tag_name": r.get("tag_name"),
            "name": r.get("name"),
            "published_at": r.get("published_at"),
            "assets": []
        }
        for a in r.get("assets", []):
            release_entry["assets"].append({
                "id": a.get("id"),
                "name": a.get("name"),
                "created_at": a.get("created_at"),
                "browser_download_url": a.get("browser_download_url"),
                "download_count": int(a.get("download_count", 0))
            })
        snap["releases"].append(release_entry)
    return snap


def summarize(snapshot: dict, include_per_release: bool = False):
    total = 0
    per_release = []
    for r in snapshot["releases"]:
        r_total = sum(a["download_count"] for a in r["assets"])
        total += r_total
        per_release.append({
            "id": r["id"],
            "tag_name": r["tag_name"],
            "name": r["name"],
            "published_at": r["published_at"],
            "total_downloads": r_total,
            "assets_count": len(r["assets"])
        })
    if include_per_release:
        return total, per_release
    return total, None


def print_detailed(snapshot: dict):
    # Print per-asset rows with release info and dates
    rows = []
    for r in snapshot["releases"]:
        release_id = r.get("id")
        tag = r.get("tag_name") or r.get("name") or str(release_id)
        published_at = r.get("published_at")
        for a in r["assets"]:
            rows.append({
                "release_tag": tag,
                "release_published_at": published_at,
                "asset_id": a["id"],
                "asset_name": a["name"],
                "asset_created_at": a.get("created_at"),
                "download_count": a["download_count"],
                "url": a.get("browser_download_url")
            })
    # sort most recent releases first by published_at (None last)
    rows.sort(key=lambda r: (r["release_published_at"] is None, r["release_published_at"] or ""), reverse=True)
    for r in rows:
        print(
            f"{r['release_tag']}\t{r['release_published_at']}\t{r['asset_name']}\t{r['asset_created_at']}\t{r['download_count']}\t{r['url']}")


def main():
    p = argparse.ArgumentParser(description="Sum GitHub release asset downloads for a repository.")
    p.add_argument("owner", help="Repo owner (user or org)")
    p.add_argument("repo", help="Repo name")
    p.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    p.add_argument("--per-release", action="store_true", help="Show per-release totals")
    p.add_argument("--detailed", action="store_true", help="Print per-asset rows including dates")
    p.add_argument("--json", action="store_true", help="Output machine-readable JSON summary")
    p.add_argument("--save-snapshot", help="Save snapshot JSON to the given path")
    args = p.parse_args()

    token = args.token or os.getenv("GITHUB_TOKEN")
    try:
        releases = get_releases(args.owner, args.repo, token)
    except SystemExit as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    snap = build_snapshot(args.owner, args.repo, releases)
    total, per_release = summarize(snap, include_per_release=args.per_release)

    if args.save_snapshot:
        os.makedirs(os.path.dirname(args.save_snapshot) or ".", exist_ok=True)
        with open(args.save_snapshot, "w", encoding="utf-8") as f:
            json.dump(snap, f, indent=2, ensure_ascii=False)
        print(f"Saved snapshot to {args.save_snapshot}")

    if args.json:
        out = {"owner": args.owner, "repo": args.repo, "total_downloads": total}
        if args.per_release:
            out["per_release"] = per_release
        print(json.dumps(out, indent=2))
    else:
        print(f"{args.owner}/{args.repo} total release downloads: {total}")
        if args.per_release:
            print("\nPer-release totals (most recent first):")
            for r in per_release:
                print(
                    f"- {r['tag_name'] or r['name'] or r['id']}: {r['total_downloads']} downloads ({r['assets_count']} assets)")
        if args.detailed:
            print(
                "\nPer-asset detail (release_tag, release_published_at, asset_name, asset_created_at, download_count, url):")
            print_detailed(snap)


if __name__ == "__main__":
    main()
