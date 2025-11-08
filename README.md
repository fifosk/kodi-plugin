# Local Subtitle Files Add-on

This repository contains the **Local Subtitle Files** Kodi subtitle service and a
matching repository add-on so everything can be hosted directly from GitHub.

## Repository layout
- `service.subtitles.localfiles/` – main add-on source.
- `repo.localfiles/` – static files served by Kodi (generated).
- `repository.localfiles/` – repository add-on that points to GitHub Raw.
- `repository.localfiles.zip` – install this in Kodi to add the repo.
- `tools/build_repo.py` – helper that (re)builds the zip + repo metadata.

## Publish workflow
1. Make the desired changes inside `service.subtitles.localfiles/`.
2. Run the packager to regenerate the add-on zip and `addons.xml` files:
   ```bash
   python3 tools/build_repo.py
   ```
3. Rebuild the repository add-on zip so Kodi can install it:
   ```bash
   zip -rq repository.localfiles.zip repository.localfiles
   ```
4. Commit and push everything (including `repo.localfiles/` and the two zip
   files) to `main` on GitHub.

GitHub now serves all repo assets from:
```
https://raw.githubusercontent.com/fifosk/kodi-plugin/main/repo.localfiles/
```

Kodi users can install `repository.localfiles.zip` and the repository will pull
the add-on directly from the GitHub-hosted files. When bumping versions, rerun
`tools/build_repo.py` to refresh the zip, manifest and checksum before pushing.
