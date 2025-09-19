Publishing dictionary artifacts to GitHub Releases

This is a recommended workflow for hosting the large dictionary ZIPs that
your package will download at runtime. GitHub Releases provide stable URLs
and integrate with GitHub's UI/APIs.

Overview
- Build or prepare your dictionary ZIPs locally (e.g. `large-dict-2025-09.zip`).
- Create a release (tag) and upload the ZIP(s) as release assets.
- Include a manifest JSON (URLs + SHA256) as a release asset or in the
  package so the runtime can find and verify artifacts.

Manual steps (recommended for occasional uploads)
1. Create a release on GitHub:
   - Go to the repository Releases page → Draft a new release.
   - Choose a tag (e.g. `v0.0.1-dicts-2025-09-19`) and title.
2. Attach assets:
   - Drag & drop your `large-dict-2025-09.zip` and `dicts_manifest.json`.
   - Publish the release.
3. Use the release asset URL in your package manifest or manifest file.

Programmatic / CI-driven release (example with GitHub Actions)
- You can automate creation of a release and upload assets using GitHub Actions.
- Example workflow (place in `.github/workflows/publish-release.yml`):

```yaml
# Example: create a GitHub Release and upload dictionary zip + manifest
name: Publish dictionaries

on:
  workflow_dispatch:

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Prepare artifacts
        run: |
          # Assume dictionary ZIPs are prepared in repo under data/
          ls -la data || true

      - name: Create release
        id: create_release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: ${{ github.event.inputs.tag || 'dicts-' + github.run_id }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Upload assets
        uses: actions/upload-release-asset@v1
        with:
          upload_url: ${{ steps.create_release.outputs.upload_url }}
          asset_path: data/large-dict-2025-09.zip
          asset_name: large-dict-2025-09.zip
          asset_content_type: application/zip

      - name: Upload manifest
        uses: actions/upload-release-asset@v1
        with:
          upload_url: ${{ steps.create_release.outputs.upload_url }}
          asset_path: data/dicts_manifest.json
          asset_name: dicts_manifest.json
          asset_content_type: application/json

```

Creating a manifest (example `dicts_manifest.json`)
```json
{
  "artifacts": [
    {
      "name": "large-dict-2025-09",
      "url": "https://github.com/<owner>/<repo>/releases/download/<tag>/large-dict-2025-09.zip",
      "sha256": "<sha256sum>",
      "split": false
    }
  ]
}

Updating dictionaries for a new release (concise workflow)

When one or more dictionary ZIPs change and you need to publish a new release, follow this safe sequence:

1. Replace or update the ZIP files in `data/databases/` locally (keep the filename stable where possible).
2. Recompute checksums and update the local manifest:
  - Use the helper script to regenerate checksums:
    ```pwsh
    python .\scripts\prepare_release.py --manifest-only
    ```
  - This writes `data/dicts_manifest.json` with updated `sha256` fields and empty `url` fields.
3. Review the manifest and verify the checksum changes. To see what changed, diff the previous manifest with the generated one:
  ```pwsh
  git diff -- data/dicts_manifest.json
  ```
4. Commit the ZIP changes (these files should be LFS-tracked) and the updated manifest (manifest may still have empty URLs at this point):
  ```pwsh
  git add data/databases/*.zip data/dicts_manifest.json
  git commit -m "chore: update dictionaries and manifest for release"
  git push origin <branch>
  ```
5. Create the release (tag) and upload assets. You can use the same helper script to create the release and upload assets if you have `gh` installed and authenticated:
  ```pwsh
  python .\scripts\prepare_release.py --tag dicts-2025-09-19 --create-release
  ```
  The script will create the tag, push it, and upload all `.zip` files in `data/databases` plus the `data/dicts_manifest.json` manifest as release assets.
6. Populate the manifest `url` fields with the release asset download URLs:
  - If you used the script and `gh` is available, the script will also populate the `url` fields in `data/dicts_manifest.json` for you (it writes the updated manifest file but does not commit it). If you created the release manually, copy the asset URLs from the Release page and update the manifest.
7. Commit and push the updated manifest (now containing `url` values):
  ```pwsh
  git add data/dicts_manifest.json
  git commit -m "chore: populate manifest with release asset URLs"
  git push origin <branch>
  ```

Notes:
- If filenames change, the helper script matches manifest artifacts to release assets by prefix (artifact `name` → asset filename). Keep stable filenames if possible to avoid manual matching.
- The package runtime will read the manifest and use the `url` + `sha256` to download and verify artifacts.
- If you only want to publish changed files in a release, you can review which manifests entries changed (`git diff`) and upload only those assets when creating the release (or delete unchanged assets from the release UI). The helper script uploads all `.zip` files in `data/databases` by default — you can adapt it for partial uploads if needed.
```

Tips
- Use a stable tag naming scheme for dictionary releases so package code can
  reference the correct download URLs.
- Include SHA256 checksums in the manifest so runtime code can verify integrity.
- CI can compute checksums automatically (`sha256sum file.zip`) and insert
  them into the manifest before uploading.
- If you host large numbers of artifacts or expect heavy bandwidth, consider
  a CDN or cloud storage (S3, Azure Blob) and publish signed URLs.
