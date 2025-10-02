"""Extract project titles and URLs from the top-level README.md and write CSV/JSON.

Usage:
  python scripts/extract_links.py [--outdir scripts] [--preview N]

The script writes <outdir>/projects.csv and <outdir>/projects.json by default.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from pathlib import Path
from typing import List, Dict


TABLE_ROW_RE = re.compile(
    r"^\|\s*(?P<id>\d+)\s*\|\s*(?P<name>.*?)\s*\|\s*\[(?:[^\]]*)\]\((?P<url>https?://[^)]+)\)")
INLINE_LINK_RE = re.compile(r"\[(?:👆|[^\]]+)\]\((?P<url>https?://[^)]+)\)")


def parse_readme(readme_path: Path) -> List[Dict]:
    """Parse the README and return list of {id,name,url} dicts.

    This first tries to parse table rows like the current README. If none are
    found, it falls back to finding any Markdown links.
    """
    rows: List[Dict] = []
    text = readme_path.read_text(encoding="utf-8")

    for line in text.splitlines():
        m = TABLE_ROW_RE.match(line)
        if m:
            rows.append({"id": int(m.group("id")), "name": m.group("name").strip(), "url": m.group("url").strip()})

    if rows:
        logging.debug("Parsed %d table rows from README", len(rows))
        return rows

    # fallback: collect inline links
    found = [m.group("url") for m in INLINE_LINK_RE.finditer(text)]
    logging.debug("Found %d inline links as fallback", len(found))
    for i, u in enumerate(found, start=1):
        rows.append({"id": i, "name": f"link_{i}", "url": u})
    return rows


def write_outputs(rows: List[Dict], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / "projects.csv"
    json_path = outdir / "projects.json"

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "url"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    logging.info("Wrote %d links to %s and %s", len(rows), csv_path, json_path)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract links from README.md")
    parser.add_argument("--readme", type=Path, default=Path(__file__).resolve().parents[1] / "README.md", help="Path to README.md")
    parser.add_argument("--outdir", type=Path, default=Path(__file__).resolve().parents[0], help="Output directory")
    parser.add_argument("--preview", type=int, nargs="?", const=10, help="Print a preview of the first N entries and exit (no files written)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    if not args.readme.exists():
        logging.error("README not found at %s", args.readme)
        return 2

    rows = parse_readme(args.readme)

    if not rows:
        logging.warning("No links found in %s", args.readme)
        return 0

    if args.preview is not None:
        n = args.preview
        for r in rows[:n]:
            print(f"{r['id']}: {r['name']} -> {r['url']}")
        print(f"(previewed {min(n, len(rows))} of {len(rows)} entries)")
        return 0

    write_outputs(rows, args.outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
