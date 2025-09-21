# Dictionary Management and Distribution

This document evaluates options for distributing the large dictionary files
used by FurlanSpellChecker and describes the recommended workflow and
implementation details for downloading and unpacking them at install time
or on first use.

## Dictionaries to manage
- elisions
- errors
- frec
- word database
- word radix tree

Some of these dictionaries may be distributed as split zip archives.

## Options Overview

1) Include dictionaries inside the PyPI wheel
   - Pros: Simple for users (no downloads), works offline
   - Cons: Wheels have size limits; slows downloads; not suitable for very
     large or frequently updated data

2) Provide a separate data wheel / package (e.g. `furlanspellchecker-data`)
   - Pros: Keeps main package small; users can opt-in to install data package
   - Cons: Two packages to manage; still served via PyPI (size limits apply)

3) Post-install download from GitHub Releases / CDN
   - Pros: Keeps wheel small, allows hosting large files externally,
     independently versioned; fast CDN delivery possible
   - Cons: Requires network access during install or first run; requires
     storage of checksums and release URLs

4) On-demand runtime fetching
   - Pros: Downloads only what is needed when needed; best for minimal
     initial footprint
   - Cons: May introduce latency on first lookup; requires robust error
     handling and retry logic

5) Use Git LFS for repository hosting
   - Pros: Keeps repo light; versioned with repo
   - Cons: Git LFS objects aren't delivered via PyPI; still requires
     a separate distribution strategy for end users

6) Wheel extras or optional extras
   - Pros: Users opt-in via `pip install furlanspellchecker[words]`
   - Cons: Extras still publish via PyPI; large sizes are problematic

## Recommendation

For most users the best tradeoff is a hybrid approach:

- Keep the main package lightweight on PyPI (no large binary blobs).
- Publish dictionary artifacts via GitHub Releases (or CDN) and include
  cryptographic checksums (SHA256) and a small JSON manifest in the package
  that points to release URLs and checksums.
- Provide a runtime helper that downloads and atomically extracts the
  dictionaries into a cross-platform cache directory (see below) on first use.
- Offer an optional CLI command to prefetch dictionaries for offline use.

This approach keeps the PyPI package small while providing a robust,
auditable delivery mechanism for large data files.

## Storage location (where to store dictionaries locally)

Order of preference for storage location (cross-platform):

- Per-user cache directory (preferred):
  - Linux: `$XDG_CACHE_HOME` or `~/.cache/furlan_spellchecker`
  - macOS: `~/Library/Caches/furlan_spellchecker`
  - Windows: `%LOCALAPPDATA%\furlan_spellchecker` (or use `appdirs`)

- Per-user data directory (if persistence is desired):
  - Linux: `~/.local/share/furlan_spellchecker`

Permissions: prefer user-writable locations to avoid elevation or admin
rights.

## Unpacking strategy

- Use SHA256 checksums to verify downloaded files before extracting.
- Extraction must be atomic: download to a temporary directory, extract to
  a temporary location, then rename to the final location once verification
  and extraction succeed.
- For split archives: concatenate parts in order into a temporary file,
  verify checksum, then extract.

## Implementation notes

- Provide a `DictionaryManager` utility in the package that:
  - Resolves the storage path
  - Downloads artifacts with retries and backoff
  - Verifies checksums
  - Handles split archives by concatenation
  - Performs atomic extraction

- Keep a small manifest (JSON) in the package (or in the release page) with
  metadata: file names, checksums, file sizes, whether split, and URLs.

## CLI and integration

- Add a CLI command `furlanspellchecker download-dicts` that triggers the
  download and extraction process and prints a short status.
- The library API should expose `DictionaryManager.ensure_installed()` so
  applications can call it programmatically.

## Security

- Always verify checksums and prefer HTTPS endpoints.
- Optionally support signatures (OpenPGP) for extra assurance if available.

## Example manifest format

```json
{
  "version": "2025-09-18",
  "artifacts": [
    {
      "name": "words-db.zip",
      "url": "https://github.com/owner/repo/releases/download/v0.0.1/words-db.zip",
      "sha256": "...",
      "split": false
    }
  ]
}

Update workflow when dictionaries change

When any dictionary archive changes, follow this minimal flow:

1. Replace the updated `.zip` files in `data/databases/` locally.
2. Regenerate the manifest with checksums:
   ```pwsh
   python .\scripts\prepare_release.py --manifest-only
   ```
3. Commit the updated zip(s) (LFS) and the manifest, push to your branch:
   ```pwsh
   git add data/databases/*.zip data/dicts_manifest.json
   git commit -m "chore: update dictionaries for release"
   git push origin <branch>
   ```
4. Create the GitHub Release and upload assets (via `gh` or web UI). If you used the script with `--create-release`, it uploads assets and writes an updated manifest with `url` fields.
5. Commit the manifest that contains the populated `url` fields and push.

Guidelines:
- Keep filenames stable across releases to avoid extra manual mapping between assets and manifest entries.
- Use `git lfs` locally: `git lfs install` before adding `.zip` files so they are stored in LFS.
- For partially changed sets, you may upload only changed zips to the release and update the manifest accordingly.
```

---

See `src/furlan_spellchecker/services/dictionary_manager.py` for an implementation
of the download/unpack/checksum utilities used by the package.
