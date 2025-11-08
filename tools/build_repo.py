#!/usr/bin/env python3
"""Builds the add-on zip and repository metadata for GitHub hosting."""

import argparse
import hashlib
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package the add-on and refresh repo metadata."
    )
    parser.add_argument(
        "--addon-dir",
        default="service.subtitles.localfiles",
        help="Path to the add-on source directory (default: %(default)s).",
    )
    parser.add_argument(
        "--repo-dir",
        default="repo.localfiles",
        help="Path to the Kodi repo root (default: %(default)s).",
    )
    return parser.parse_args()


def compute_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_addon(addon_id: str, version: str, addon_dir: Path, repo_dir: Path) -> Path:
    package_dir = repo_dir / addon_id
    package_dir.mkdir(parents=True, exist_ok=True)
    zip_path = package_dir / f"{addon_id}-{version}.zip"

    if zip_path.exists():
        zip_path.unlink()

    base_dir = addon_dir.parent
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in addon_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(base_dir).as_posix())

    md5_path = zip_path.with_suffix(zip_path.suffix + ".md5")
    md5_path.write_text(compute_md5(zip_path), encoding="utf-8")
    return zip_path


def build_addons_xml(addon_xml: Path, repo_dir: Path) -> Path:
    raw = addon_xml.read_text(encoding="utf-8").strip()
    if raw.startswith("<?xml"):
        raw = raw.split("?>", 1)[1].strip()

    addons_xml = repo_dir / "addons.xml"
    addons_xml.write_text(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        "<addons>\n"
        f"{raw}\n"
        "</addons>\n",
        encoding="utf-8",
    )

    md5_path = repo_dir / "addons.xml.md5"
    md5_path.write_text(compute_md5(addons_xml), encoding="utf-8")
    return addons_xml


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    addon_dir = (root / args.addon_dir).resolve()
    repo_dir = (root / args.repo_dir).resolve()
    addon_xml = addon_dir / "addon.xml"

    if not addon_xml.exists():
        print(f"Could not find addon.xml at {addon_xml}", file=sys.stderr)
        return 1

    repo_dir.mkdir(parents=True, exist_ok=True)

    try:
        addon = ET.parse(addon_xml).getroot()
        addon_id = addon.attrib["id"]
        version = addon.attrib["version"]
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unable to parse add-on id/version: {exc}", file=sys.stderr)
        return 1

    zip_path = package_addon(addon_id, version, addon_dir, repo_dir)
    addons_xml = build_addons_xml(addon_xml, repo_dir)

    print(f"Packaged {addon_id} {version} -> {zip_path.relative_to(root)}")
    print(f"Updated repo manifest -> {addons_xml.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
