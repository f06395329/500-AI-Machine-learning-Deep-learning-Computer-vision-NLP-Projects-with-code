"""Simple script to extract project titles and URLs from README.md and write CSV/JSON.

Usage: python scripts/extract_links.py

Creates: scripts/projects.csv and scripts/projects.json
"""
import re
import json
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
OUT_DIR = ROOT / "scripts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TABLE_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*\[(?:[^\]]*)\]\((https?://[^)]+)\)")
LINK_RE = re.compile(r"\[👆\]\((https?://[^)]+)\)")

rows = []
with README.open(encoding="utf-8") as f:
    for line in f:
        m = TABLE_ROW_RE.match(line)
        if m:
            idx = m.group(1)
            name = m.group(2).strip()
            url = m.group(3).strip()
            rows.append({"id": int(idx), "name": name, "url": url})

# Fallback: find any explicit [👆](url) occurrences in file
if not rows:
    with README.open(encoding="utf-8") as f:
        text = f.read()
    found = LINK_RE.findall(text)
    for i, u in enumerate(found, start=1):
        rows.append({"id": i, "name": f"link_{i}", "url": u})

# write CSV
csv_path = OUT_DIR / "projects.csv"
with csv_path.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "name", "url"])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

# write JSON
json_path = OUT_DIR / "projects.json"
with json_path.open("w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(rows)} links to {csv_path} and {json_path}")
