#!/usr/bin/env python3
"""
heatmap_from_snapshots.py

Generate a downloads heatmap from GitHub release snapshot JSON files.

This is the same script as before but with:
- an asset-name -> friendly-group mapping used when --group-by asset is selected;
- an added total download count shown in the headline/title.

The mapper is embedded as DEFAULT_ASSET_MAP and can be overridden by a JSON mapping file passed with --map-file.

Usage examples:
  # group by mapped assets (uses built-in mapping)
  python heatmap_from_snapshots.py snapshots/ out_heatmap.png --group-by asset

  # use a custom mapping JSON file:
  python heatmap_from_snapshots.py snapshots/ out_heatmap.png --group-by asset --map-file asset_map.json

Custom map-file format (JSON):
{
  "edxd-dashboard-Windows.zip": "Windows",
  "edxd-dashboard-Linux.tar.gz": "Linux",
  ...
}

Dependencies:
  pandas, matplotlib, seaborn
  (install into a venv recommended)

This script uses the Agg backend so it runs headless (no X required).
"""
from __future__ import annotations

import argparse
import json
import os
from glob import glob

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Default mapping as requested by user
DEFAULT_ASSET_MAP: dict[str, str] = {
    "edxd-dashboard-Windows.zip": "Windows",
    "edxd-dashboard-Linux.tar.gz": "Linux",
    "edxd-dashboard-Linux_ubuntu_mint.tar.gz": "Linux",
    "edxd-dashboard-arch.tar.gz": "arch",
    "EDXD_0.3.1.tar.gz": "Linux",
    "edxd-dashboard-macOS.tar.gz": "macOS",
    "edxd-dashboard-debian.tar.gz": "debian",
    "edxd-dashboard-Linux.zip": "Linux",
    "edxd-dashboard-macOS.zip": "macOS",
    "EDXD-0.3.0.tar.gz": "Linux",
}


def load_snapshots_from_dir(dirpath: str):
    files = sorted(glob(os.path.join(dirpath, "*.json")))
    if not files:
        raise SystemExit(f"No JSON files found in directory: {dirpath}")
    snaps = []
    for p in files:
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        t = data.get("snapshot_at") or os.path.basename(p)
        snaps.append((t, data))
    snaps.sort(key=lambda x: x[0])
    return snaps


def load_snapshots_from_file(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # If it's an object with key "snapshots"
    if isinstance(data, dict) and "snapshots" in data and isinstance(data["snapshots"], list):
        snaps = []
        for s in data["snapshots"]:
            t = s.get("snapshot_at") or s.get("timestamp") or ""
            snaps.append((t, s))
        snaps.sort(key=lambda x: x[0])
        return snaps
    # If it's a list of snapshot objects
    if isinstance(data, list):
        snaps = []
        for s in data:
            t = s.get("snapshot_at") or s.get("timestamp") or ""
            snaps.append((t, s))
        snaps.sort(key=lambda x: x[0])
        return snaps
    # Single snapshot object
    if isinstance(data, dict):
        t = data.get("snapshot_at") or data.get("timestamp") or ""
        return [(t, data)]
    raise SystemExit("Input JSON not recognized. Expecting a snapshot object, list, or {'snapshots': [...]}")


def flatten_snapshot_counts(snap: dict):
    """
    Return dict mapping "release_tag :: asset_name" -> cumulative_download_count
    """
    out = {}
    for r in snap.get("releases", []):
        tag = r.get("tag_name") or r.get("name") or str(r.get("id") or "")
        for a in r.get("assets", []):
            key = f"{tag} :: {a.get('name')}"
            out[key] = int(a.get("download_count", 0))
    return out


def compute_delta_dataframe(snaps: list[tuple[str, dict]]):
    """
    snaps: chronological list of (timestamp, snapshot_dict)
    Returns: pandas DataFrame indexed by date with columns per "tag :: asset" and values = delta downloads since previous snapshot
    """
    rows = []
    prev_counts = None
    prev_time = None
    for snap_time, snap in snaps:
        counts = flatten_snapshot_counts(snap)
        ts = pd.to_datetime(snap_time)
        if prev_counts is None:
            prev_counts = counts
            prev_time = ts
            continue
        # union keys
        keys = set(prev_counts.keys()) | set(counts.keys())
        delta = {k: max(0, counts.get(k, 0) - prev_counts.get(k, 0)) for k in keys}
        row = {"to": ts}
        row.update(delta)
        rows.append(row)
        prev_counts = counts
        prev_time = ts
    if not rows:
        return pd.DataFrame()  # caller should handle
    df = pd.DataFrame(rows).set_index("to")
    # convert index to date for daily bins (keeps unique days)
    df.index = pd.to_datetime(df.index).date
    # replace NaN with 0
    df = df.fillna(0).astype(int)
    return df


def group_columns(df: pd.DataFrame, group_by: str, asset_map: dict[str, str]):
    """
    group_by in {"release","asset"}
    produce a new DataFrame grouped by release tag or mapped asset name (summing assets that belong to the same group)
    """
    if df.empty:
        return df
    groups: dict[str, list[str]] = {}
    for col in df.columns:
        release, _, asset = col.partition(" :: ")
        if group_by == "release":
            key = release
        else:
            # map exact asset filename to friendly group when available
            mapped = asset_map.get(asset, None)
            key = mapped if mapped is not None else asset
        groups.setdefault(key, []).append(col)
    df_grouped = pd.DataFrame(index=df.index)
    for k, cols in groups.items():
        df_grouped[k] = df[cols].sum(axis=1)
    return df_grouped


def plot_heatmap(df_grouped: pd.DataFrame, out_png: str, top_n: int = 30, title: str | None = None):
    if df_grouped.empty:
        raise SystemExit("No data to plot")
    # total downloads across the displayed table (all periods x groups)
    total_downloads = int(df_grouped.values.sum())
    total_fmt = f"{total_downloads:,}"
    title_with_total = (title + f" — total downloads: {total_fmt}") if title else f"total downloads: {total_fmt}"

    totals = df_grouped.sum(axis=0).sort_values(ascending=False)
    top = totals.head(top_n).index.tolist()
    df_top = df_grouped[top]
    # If there's only one column (single snapshot case converted), produce bar chart instead
    if df_top.shape[0] == 1:
        # bar chart across groups for that date
        date_label = str(df_top.index[0])
        vals = df_top.iloc[0].sort_values(ascending=False)
        plt.figure(figsize=(10, max(4, len(vals) * 0.15)))
        vals.plot(kind="bar")
        plt.ylabel("downloads")
        plt.title(title_with_total + f" — {date_label}")
        plt.tight_layout()
        plt.savefig(out_png, dpi=150)
        print(f"Saved bar chart to {out_png}")
        csv_out = os.path.splitext(out_png)[0] + ".csv"
        df_top.to_csv(csv_out)
        print(f"Wrote CSV to {csv_out}")
        return
    # heatmap: rows = groups, cols = dates
    plt.figure(figsize=(max(8, df_top.shape[1] * 0.5), max(4, df_top.shape[0] * 0.25)))
    sns.heatmap(df_top.T, cmap="YlGnBu", linewidths=0.3, cbar_kws={"label": "downloads"})
    plt.xlabel("date")
    plt.ylabel("group")
    plt.title(title_with_total)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    print(f"Saved heatmap to {out_png}")
    csv_out = os.path.splitext(out_png)[0] + ".csv"
    df_top.to_csv(csv_out)
    print(f"Wrote CSV to {csv_out}")


def main():
    p = argparse.ArgumentParser(description="Generate a downloads heatmap from snapshot JSON(s).")
    p.add_argument("input", help="Directory of snapshot JSONs or a single JSON file")
    p.add_argument("out_png", help="Output PNG path")
    p.add_argument("--group-by", choices=["release", "asset"], default="release",
                   help="Group heatmap rows by release tag or asset name")
    p.add_argument("--top", type=int, default=30, help="Number of top groups to show")
    p.add_argument("--map-file", help="Optional JSON file mapping asset filenames to friendly group names")
    args = p.parse_args()

    # load mapping (defaults merged with any user-provided map-file)
    asset_map = dict(DEFAULT_ASSET_MAP)
    if args.map_file:
        if not os.path.isfile(args.map_file):
            raise SystemExit(f"Map file not found: {args.map_file}")
        try:
            with open(args.map_file, "r", encoding="utf-8") as fh:
                custom = json.load(fh)
            if not isinstance(custom, dict):
                raise ValueError("map-file JSON must be an object mapping filenames to group names")
            # merge: custom overrides defaults
            asset_map.update({str(k): str(v) for k, v in custom.items()})
        except Exception as e:
            raise SystemExit(f"Failed to load map file: {e}")

    if os.path.isdir(args.input):
        snaps = load_snapshots_from_dir(args.input)
    elif os.path.isfile(args.input):
        snaps = load_snapshots_from_file(args.input)
    else:
        raise SystemExit(f"Input path not found: {args.input}")

    # Ensure chronological ordering by parsed timestamp
    def parse_key(x):
        k = x[0]
        try:
            return pd.to_datetime(k)
        except Exception:
            return pd.NaT

    snaps.sort(key=parse_key)

    if len(snaps) >= 2:
        df = compute_delta_dataframe(snaps)
        if df.empty:
            raise SystemExit(
                "Could not compute deltas — need at least two snapshots with recognizable snapshot_at timestamps")
        df_grouped = group_columns(df, args.group_by, asset_map)
        title = f"{os.path.basename(args.input)} — grouped by {args.group_by}"
        plot_heatmap(df_grouped, args.out_png, top_n=args.top, title=title)
    else:
        # only one snapshot present: render a single-date bar chart of cumulative counts
        snap = snaps[0][1]
        flat = flatten_snapshot_counts(snap)
        if not flat:
            raise SystemExit("Snapshot contains no assets/releases")
        # group according to the requested grouping, applying mapping if requested
        grouped: dict[str, int] = {}
        for k, v in flat.items():
            release, _, asset = k.partition(" :: ")
            key = release if args.group_by == "release" else asset_map.get(asset, asset)
            grouped.setdefault(key, 0)
            grouped[key] += v
        df_one = pd.DataFrame([grouped], index=[pd.to_datetime(snaps[0][0]).date() if snaps[0][0] else "snapshot"])
        title = f"{snaps[0][0]} — Downloads by {args.group_by}"
        plot_heatmap(df_one, args.out_png, top_n=args.top, title=title)


if __name__ == "__main__":
    main()
