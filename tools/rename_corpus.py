#!/usr/bin/env python3
"""
Rename the fixed hadith corpus files from numeric Shamela-style filenames
to human-readable book + volume filenames without changing file contents.

Usage:
    python tools/rename_corpus.py "/path/to/sample library v 6 (2).zip" --output corpus
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re, zipfile
from pathlib import Path

def clean(text: str) -> str:
    text = text.strip().replace("/", " - ").replace("\\", " - ")
    return re.sub(r"\s+", " ", text)

def renamed_filename(book: str, filename: str):
    stem, ext = os.path.splitext(filename)
    m = re.fullmatch(r"j?0*(\d+)", stem, re.I)
    if m:
        volume = int(m.group(1))
        return f"{book} - المجلد {volume:02d}{ext}", "volume", volume
    if stem in {"مقدمة", "المقدمة"}:
        return f"{book} - المقدمة{ext}", "intro", None
    m = re.fullmatch(r"م\s*(\d+)", stem)
    if m:
        return f"{book} - ملحق {int(m.group(1))}{ext}", "supplement", None
    if stem == book:
        return f"{stem}{ext}", "standalone", None
    return f"{book} - {clean(stem)}{ext}", "named", None

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("zipfile")
    p.add_argument("--output", default="corpus")
    args = p.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    manifest, seen_sha = [], {}
    with zipfile.ZipFile(args.zipfile) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            parts = info.filename.split("/")
            rel = parts[1:] if parts and parts[0].lower().startswith("sample library") else parts
            parent = rel[-2] if len(rel) >= 2 else ""
            filename = rel[-1]
            stem, _ = os.path.splitext(filename)
            book = clean(parent if parent else stem)
            new_name, kind, volume = renamed_filename(book, filename)
            data = zf.read(info)
            sha = hashlib.sha256(data).hexdigest()
            duplicate_of = seen_sha.get(sha)

            if duplicate_of is None:
                dest = out / new_name
                n = 2
                while dest.exists():
                    dest = out / f"{dest.stem} ({n}){dest.suffix}"
                    n += 1
                dest.write_bytes(data)
                seen_sha[sha] = dest.name
                canonical = dest.name
            elif kind == "standalone" and duplicate_of != new_name:
                # Prefer a true root-level standalone book title as the canonical
                # filename when the same bytes also appeared nested in another folder.
                old = out / duplicate_of
                target = out / new_name
                if old.exists() and not target.exists():
                    old.rename(target)
                seen_sha[sha] = new_name
                canonical = new_name
                for row in manifest:
                    if row["sha256"] == sha:
                        row["canonical_filename"] = new_name
                        row["duplicate_of"] = new_name
                duplicate_of = ""
            else:
                canonical = duplicate_of

            manifest.append({
                "old_path": info.filename,
                "book": book,
                "volume": volume,
                "type": kind,
                "canonical_filename": canonical,
                "duplicate_of": duplicate_of or "",
                "size_bytes": len(data),
                "sha256": sha,
            })

    (out / "rename_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (out / "rename_manifest.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=manifest[0].keys())
        w.writeheader()
        w.writerows(manifest)
    print(f"Processed {len(manifest)} source files.")
    print(f"Wrote {len(seen_sha)} unique files to {out}.")

if __name__ == "__main__":
    main()
