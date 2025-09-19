#!/usr/bin/env python3
"""Prepare dicts manifest and optionally create a GitHub Release.

Usage:
  # generate manifest only
  python scripts/prepare_release.py --manifest-only

  # generate manifest and create release
  python scripts/prepare_release.py --tag dicts-2025-09-19 --create-release

This script computes SHA256 for each .zip in `data/databases`, writes
`data/dicts_manifest.json` and optionally creates a GitHub Release and
uploads assets using the `gh` CLI (must be installed and authenticated).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "databases"
MANIFEST_PATH = ROOT / "data" / "dicts_manifest.json"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest() -> dict:
    artifacts = []
    if not DATA_DIR.exists():
        raise SystemExit(f"Data directory not found: {DATA_DIR}")
    for p in sorted(DATA_DIR.glob("*.zip")):
        name = p.stem
        sha256 = compute_sha256(p)
        artifacts.append({"name": name, "url": "", "sha256": sha256, "split": False})

    return {"artifacts": artifacts}


def write_manifest(manifest: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print(f"Wrote manifest to {MANIFEST_PATH}")


def create_release(tag: str) -> None:
    if shutil.which("gh") is None:
        raise SystemExit("gh CLI not found. Install GitHub CLI to create releases from script.")

    # create annotated tag and push
    subprocess.run(["git", "tag", "-a", tag, "-m", f"Dictionary release {tag}"], check=True)
    subprocess.run(["git", "push", "origin", tag], check=True)

    # prepare asset list: all zips and manifest
    assets = [str(p) for p in sorted(DATA_DIR.glob("*.zip"))]
    assets.append(str(MANIFEST_PATH))

    cmd = ["gh", "release", "create", tag] + assets + ["--title", f"Dictionaries {tag}", "--notes", f"Dictionaries release {tag}"]
    subprocess.run(cmd, check=True)
    print(f"Created release {tag} with assets: {assets}")
    # populate manifest URLs from release assets
    try:
        res = subprocess.check_output(["gh", "release", "view", tag, "--json", "assets"])  # requires gh >= 1.0
        info = json.loads(res)
        assets_info = info.get("assets", [])
        if assets_info:
            manifest = json.load(MANIFEST_PATH.open("r", encoding="utf-8"))
            for art in manifest.get("artifacts", []):
                # find matching asset by name prefix
                matched = None
                for a in assets_info:
                    name = a.get("name")
                    if name and name.startswith(art["name"]):
                        matched = a
                        break
                if matched:
                    art["url"] = matched.get("browser_download_url", art.get("url", ""))
            # write updated manifest
            with MANIFEST_PATH.open("w", encoding="utf-8") as fh:
                json.dump(manifest, fh, ensure_ascii=False, indent=2)
            print(f"Populated manifest URLs in {MANIFEST_PATH}")
    except Exception:
        print("Warning: could not auto-populate manifest URLs. You may update them manually.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", type=str, help="Release tag to create, e.g. dicts-2025-09-19")
    parser.add_argument("--create-release", action="store_true", help="Create GitHub Release via gh")
    parser.add_argument("--manifest-only", action="store_true", help="Only generate manifest")
    args = parser.parse_args()

    manifest = build_manifest()
    write_manifest(manifest)

    if args.create_release:
        if not args.tag:
            raise SystemExit("--tag is required when --create-release is used")
        create_release(args.tag)


if __name__ == "__main__":
    main()
