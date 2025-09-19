"""Utilities for managing large dictionary artifacts: download, verify, and extract.

This module provides a `DictionaryManager` class to handle downloading
dictionary artifacts (including split archives), verifying checksums,
and performing atomic extraction into a user cache directory.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import urllib.request


@dataclass
class Artifact:
    name: str
    url: str
    sha256: str
    split: bool = False


class DictionaryManager:
    def __init__(
        self, cache_dir: Optional[Path] = None, manifest: Optional[dict] = None, manifest_path: Optional[Path] = None
    ) -> None:
        """Initialize the manager.

        - `cache_dir`: optional base path where dictionaries will be stored.
        - `manifest`: optional manifest dict (if not provided, the caller
          should provide artifact info directly).
        """
        self.cache_dir = cache_dir or self._resolve_default_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = manifest or {}
        self.manifest_path = Path(manifest_path) if manifest_path else None

    @staticmethod
    def _resolve_default_cache_dir() -> Path:
        """Return a cross-platform per-user cache directory for dictionaries."""
        from sys import platform

        home = Path.home()
        if platform == "win32":
            return Path.home() / "AppData" / "Local" / "furlan_spellchecker" / "cache"
        if platform == "darwin":
            return home / "Library" / "Caches" / "furlan_spellchecker"
        # assume linux-like
        xdg = os.environ.get("XDG_CACHE_HOME")
        if xdg:
            return Path(xdg) / "furlan_spellchecker"
        return home / ".cache" / "furlan_spellchecker"

    def _download(self, url: str, target: Path, retries: int = 3) -> None:
        """Download a file to target path with simple retry logic."""
        for attempt in range(1, retries + 1):
            try:
                with urllib.request.urlopen(url) as resp:
                    with open(target, "wb") as w:
                        shutil.copyfileobj(resp, w)
                return
            except Exception as e:
                if attempt == retries:
                    raise

    def _compute_sha256(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _concatenate_parts(self, parts: Iterable[Path], out_path: Path) -> None:
        with open(out_path, "wb") as w:
            for p in parts:
                with open(p, "rb") as r:
                    shutil.copyfileobj(r, w)

    def _atomic_extract_zip(self, zip_path: Path, dest_dir: Path) -> None:
        import zipfile

        tmpdir = dest_dir.with_suffix(".tmp")
        if tmpdir.exists():
            shutil.rmtree(tmpdir)
        tmpdir.mkdir(parents=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmpdir)
            # move tmpdir to final dest atomically
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            tmpdir.rename(dest_dir)
        finally:
            if tmpdir.exists():
                # if rename failed, try to cleanup
                try:
                    shutil.rmtree(tmpdir)
                except Exception:
                    pass

    def ensure_artifact_installed(self, artifact: Artifact) -> Path:
        """Ensure the given artifact is downloaded, verified and extracted.

        Returns the path to the extracted folder or file.
        """
        target_dir = self.cache_dir / artifact.name
        if target_dir.exists():
            return target_dir

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            # Download
            if artifact.split:
                # manifest should contain part URLs with predictable naming
                # For now assume URL is a pattern with {part} placeholder or
                # a single URL to an index; caller is responsible to provide
                # correct artifact.url when split=True.
                raise NotImplementedError("split archives require explicit part list in manifest")

            archive_path = td_path / artifact.name
            self._download(artifact.url, archive_path)

            # Verify checksum
            actual = self._compute_sha256(archive_path)
            if actual.lower() != artifact.sha256.lower():
                raise ValueError(f"Checksum mismatch for {artifact.name}: {actual} != {artifact.sha256}")

            # Extract
            extract_dir = td_path / (artifact.name + ".extract")
            self._atomic_extract_zip(archive_path, extract_dir)

            # Move into final cache location atomically
            final_dir = self.cache_dir / artifact.name
            if final_dir.exists():
                shutil.rmtree(final_dir)
            extract_dir.rename(final_dir)

            return final_dir

    def _load_manifest(self) -> dict:
        """Load manifest from provided dict, file path, or package data.

        Priority: explicit self.manifest dict -> manifest_path file -> package bundled manifest (data/dicts_manifest.json)
        """
        if self.manifest:
            return self.manifest
        if self.manifest_path and self.manifest_path.exists():
            with open(self.manifest_path, "r", encoding="utf-8") as fh:
                return json.load(fh)

        # fall back to package data manifest if available
        try:
            pkg_manifest = Path(__file__).parent.parent / "data" / "dicts_manifest.json"
            if pkg_manifest.exists():
                with pkg_manifest.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
        except Exception:
            pass

        return {"artifacts": []}

    def install_from_manifest(self, manifest: Optional[dict] = None) -> List[Path]:
        """Install all artifacts listed in a manifest.

        `manifest` may be provided directly or the manager will load the
        manifest using `_load_manifest()`.
        Returns a list of installed paths.
        """
        manifest = manifest or self._load_manifest()
        installed: List[Path] = []
        for entry in manifest.get("artifacts", []):
            art = Artifact(
                name=entry["name"], url=entry["url"], sha256=entry["sha256"], split=entry.get("split", False)
            )
            p = self.ensure_artifact_installed(art)
            installed.append(p)
        return installed
