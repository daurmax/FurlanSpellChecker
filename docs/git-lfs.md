Git LFS (Large File Storage) — quick guide

This project recommends using Git LFS to manage large dictionary artifacts so
that the package distributed on PyPI remains small while the large data files
are versioned in the repository.

Windows (PowerShell) quick steps for developers:

1. Install Git LFS (if not installed):

```pwsh
# using the official installer or package manager
choco install git-lfs -y   # if you use Chocolatey
# or download installer: https://git-lfs.github.com/

# initialize git lfs for the repo (run once per machine)
git lfs install
```

2. Ensure the repository has the `.gitattributes` file (it is included in
   this repo and tracks `*.zip`, `*.dict`, etc.). If you change patterns,
   commit the `.gitattributes` file.

3. Add dictionary artifacts (example):

```pwsh
# Stage new artifact (example: large-dict-2025-09.zip)
git add data/large-dict-2025-09.zip
git commit -m "chore: add dictionary artifact large-dict-2025-09 (LFS)"
# Push to remote. LFS will upload the objects to the remote's LFS storage
git push origin develop
```

4. Verify LFS objects uploaded:

```pwsh
git lfs ls-files
```

Notes and cautions:
- GitHub enforces storage and bandwidth quotas for Git LFS on free plans.
  Check your organization or repo's LFS usage and consider hosting
  releases on GitHub Releases or a CDN if you expect high download volume.
- If large files are already in the repository history, use the migration tool
  to move them to LFS (this rewrites history):

```pwsh
# VERY IMPORTANT: coordinate with collaborators before rewriting history
git lfs migrate import --include="*.zip,*.dict"
git push --force
```

- For CI: ensure your CI runner has `git lfs install` in its setup steps so
  it can pull LFS objects during `git clone` / `git fetch`.

Publishing for end-users:
- Keep PyPI packages small. For end-users prefer one of:
  - Host zipped dictionaries on GitHub Releases or on a CDN; include a
    manifest with SHA256 sums in the package and download on first run.
  - Provide a separate data package (e.g. `furlan_spellchecker-data`) and
    instruct users to install it separately (not ideal for PyPI size limits).
