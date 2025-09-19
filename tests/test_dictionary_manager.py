import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest

from furlan_spellchecker.services.dictionary_manager import DictionaryManager, Artifact


CI = os.environ.get("GITHUB_ACTIONS", "false").lower() == "true"


@pytest.mark.skipif(CI, reason="Integration tests for downloads are skipped in CI")
def test_ensure_artifact_installed_local_copy(tmp_path, monkeypatch):
    """Test downloading (via local copy) and atomic extraction of a zip artifact."""
    # create a small zip fixture
    fixture_dir = tmp_path / "srcdata"
    fixture_dir.mkdir()
    (fixture_dir / "a.txt").write_text("hello")
    zip_path = tmp_path / "fixture.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(fixture_dir / "a.txt", arcname="a.txt")

    # create a manager with cache dir
    cache_dir = tmp_path / "cache"
    manager = DictionaryManager(cache_dir=cache_dir)

    # monkeypatch _download to copy from our local fixture
    def fake_download(url, target, retries=3):
        shutil.copy(str(zip_path), str(target))

    monkeypatch.setattr(manager, "_download", fake_download)

    art = Artifact(name="test-fix", url="file:///dummy/fixture.zip", sha256=manager._compute_sha256(zip_path), split=False)

    installed = manager.ensure_artifact_installed(art)
    assert installed.exists()
    assert (installed / "a.txt").read_text() == "hello"


@pytest.mark.skipif(CI, reason="Integration tests for downloads are skipped in CI")
def test_install_from_manifest_local(tmp_path, monkeypatch):
    # create two small zips
    zips = []
    for name in ("one", "two"):
        d = tmp_path / name
        d.mkdir()
        (d / "x.txt").write_text(name)
        p = tmp_path / f"{name}.zip"
        with zipfile.ZipFile(p, "w") as zf:
            zf.write(d / "x.txt", arcname="x.txt")
        zips.append(p)

    cache_dir = tmp_path / "cache"
    manager = DictionaryManager(cache_dir=cache_dir)

    # monkeypatch download
    def fake_download(url, target, retries=3):
        # url will be the path string we pass in manifest
        src = Path(url)
        shutil.copy(str(src), str(target))

    monkeypatch.setattr(manager, "_download", fake_download)

    manifest = {"artifacts": []}
    for p in zips:
        manifest["artifacts"].append({"name": p.stem, "url": str(p), "sha256": manager._compute_sha256(p), "split": False})

    installed = manager.install_from_manifest(manifest)
    assert len(installed) == 2
    for p in installed:
        assert (p / "x.txt").exists()
