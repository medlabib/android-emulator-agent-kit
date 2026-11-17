#!/usr/bin/env python3
"""Package an Android CLI Journey report and its local evidence into a ZIP bundle.

This tool deliberately does not control devices or execute tests. It packages
outputs produced by Android CLI (or another test runner) after a run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

LINK_RE = re.compile(r"!?(?:\[[^\]]*\])\(([^)\s]+)(?:\s+['\"][^)]*['\"])?\)")
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=3, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40,64}", value) else None


def load_metadata(path: Path | None) -> dict:
    if path is None:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read metadata JSON: {error}") from error
    if not isinstance(value, dict):
        raise ValueError("Metadata JSON must contain an object.")
    return value


def local_report_links(report_text: str) -> list[str]:
    found = []
    for match in LINK_RE.finditer(report_text):
        raw = match.group(1).strip().strip("<>")
        parsed = urlsplit(raw)
        if parsed.scheme or parsed.netloc or raw.startswith("#"):
            continue
        path = unquote(parsed.path)
        if path and path not in found:
            found.append(path)
    return found


def safe_link_path(report_dir: Path, raw_path: str) -> Path | None:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return None
    try:
        resolved = (report_dir / candidate).resolve(strict=True)
        resolved.relative_to(report_dir.resolve())
    except (OSError, ValueError):
        return None
    return resolved if resolved.is_file() else None


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=ZIP_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def build_bundle(report: Path, output: Path, metadata_path: Path | None = None,
                 extra_artifacts: list[Path] | None = None) -> dict:
    report = report.expanduser().resolve(strict=True)
    if not report.is_file():
        raise ValueError(f"Journey report is not a file: {report}")
    output = output.expanduser().resolve()
    if output == report:
        raise ValueError("Output archive cannot overwrite the Journey report.")
    if output.suffix.lower() != ".zip":
        raise ValueError("Output archive must have a .zip extension.")

    report_text = report.read_text(encoding="utf-8")
    entries: dict[str, Path] = {}
    missing_links = []
    for link in local_report_links(report_text):
        source = safe_link_path(report.parent, link)
        if source is None:
            missing_links.append(link)
            continue
        if source == report:
            continue
        relative = source.relative_to(report.parent.resolve()).as_posix()
        entries[relative] = source

    for index, artifact in enumerate(extra_artifacts or [], start=1):
        source = artifact.expanduser().resolve(strict=True)
        if not source.is_file():
            raise ValueError(f"Artifact is not a file: {source}")
        name = source.name
        archive_name = f"attachments/{name}"
        if archive_name in entries or archive_name == "journey.md":
            archive_name = f"attachments/{index:03d}-{name}"
        entries[archive_name] = source

    if output == report or output in entries.values():
        raise ValueError("Output archive cannot overwrite the report or an included evidence file.")

    metadata = load_metadata(metadata_path)
    manifest = {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": {"name": "android-emulator-agent-kit-evidence-pack", "version": "0.1.0"},
        "source": {
            "report_name": report.name,
            "report_sha256": sha256_file(report),
            "git_commit": metadata.pop("git_commit", None) or git_commit(report.parent),
        },
        "host": {
            "os": platform.platform(),
            "python": platform.python_version(),
        },
        "metadata": metadata,
        "artifacts": [],
        "warnings": [f"Referenced local artifact was not included: {item}" for item in missing_links],
    }

    report_bytes = report.read_bytes()
    manifest["artifacts"].append({
        "path": "journey.md", "size_bytes": len(report_bytes),
        "sha256": hashlib.sha256(report_bytes).hexdigest(), "role": "journey_report",
    })
    for archive_name, source in sorted(entries.items()):
        manifest["artifacts"].append({
            "path": archive_name, "size_bytes": source.stat().st_size,
            "sha256": sha256_file(source), "role": "referenced_evidence" if not archive_name.startswith("attachments/") else "additional_evidence",
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(zip_info("journey.md"), report_bytes)
        for archive_name, source in sorted(entries.items()):
            archive.writestr(zip_info(archive_name), source.read_bytes())
        archive.writestr(
            zip_info("manifest.json"),
            (json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"),
        )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, help="Android CLI Journey Markdown report")
    parser.add_argument("--output", required=True, help="Destination .zip evidence bundle")
    parser.add_argument("--metadata", help="Optional JSON object with app/build/device metadata")
    parser.add_argument("--artifact", action="append", default=[], help="Additional evidence file; may be repeated")
    args = parser.parse_args(argv)
    try:
        manifest = build_bundle(
            Path(args.report), Path(args.output),
            Path(args.metadata) if args.metadata else None,
            [Path(item) for item in args.artifact],
        )
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps({
        "output": str(Path(args.output).expanduser().resolve()),
        "artifact_count": len(manifest["artifacts"]),
        "warning_count": len(manifest["warnings"]),
        "manifest_schema": manifest["schema_version"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
