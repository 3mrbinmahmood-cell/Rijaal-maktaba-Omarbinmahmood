#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sqlite3
from pathlib import Path

AR_DIAC = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
SCHEMA = """
CREATE TABLE IF NOT EXISTS shamela_narrators(
  shamela_id INTEGER PRIMARY KEY,
  short_name TEXT NOT NULL,
  long_name TEXT NOT NULL,
  death_year INTEGER,
  biography TEXT,
  metadata TEXT,
  short_norm TEXT NOT NULL,
  long_norm TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_shamela_short_norm ON shamela_narrators(short_norm);
CREATE INDEX IF NOT EXISTS idx_shamela_long_norm ON shamela_narrators(long_norm);
CREATE TABLE IF NOT EXISTS mention_shamela_matches(
  mention_id TEXT NOT NULL REFERENCES narrator_mentions_raw(mention_id),
  shamela_id INTEGER NOT NULL REFERENCES shamela_narrators(shamela_id),
  match_method TEXT NOT NULL,
  score REAL NOT NULL,
  match_status TEXT NOT NULL,
  PRIMARY KEY(mention_id, shamela_id)
);
CREATE INDEX IF NOT EXISTS idx_match_status ON mention_shamela_matches(match_status);
"""

def normalize_name(s: str) -> str:
    s = AR_DIAC.sub("", s or "")
    s = s.replace("ٱ","ا").replace("أ","ا").replace("إ","ا").replace("آ","ا").replace("ى","ي")
    s = re.sub(r'[ـ\u200c\u200d\u200e\u200f]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip(" ،؛;:.()-")

def pick(row: dict, *names, default=None):
    for n in names:
        if n in row and row[n] is not None:
            return row[n]
    return default

def load_json_or_jsonl(path: Path):
    text = path.read_text("utf-8")
    if text.lstrip().startswith("["):
        yield from json.loads(text)
    else:
        for line in text.splitlines():
            if line.strip():
                yield json.loads(line)

def load_parquet(path: Path):
    import pandas as pd
    for row in pd.read_parquet(path).to_dict("records"):
        yield row

def load_seed(path: Path):
    if path.suffix.lower() == ".parquet":
        yield from load_parquet(path)
    else:
        yield from load_json_or_jsonl(path)

def import_shamela(con: sqlite3.Connection, seed: Path):
    con.executescript(SCHEMA)
    con.execute("DELETE FROM mention_shamela_matches")
    con.execute("DELETE FROM shamela_narrators")
    count = 0
    for row in load_seed(seed):
        sid = int(pick(row, "id", "narrator_id", "shamela_id"))
        short = str(pick(row, "shortName", "short_name", "short_name_ar", default="") or "")
        long = str(pick(row, "longName", "long_name", "long_name_ar", default="") or "")
        death = pick(row, "deathYear", "death_year", "death_hijri")
        bio = str(pick(row, "biography", "bio", default="") or "")
        meta = pick(row, "metadata", "meta", default="")
        if not isinstance(meta, str):
            meta = json.dumps(meta, ensure_ascii=False)
        con.execute("INSERT INTO shamela_narrators VALUES(?,?,?,?,?,?,?,?)",
                    (sid, short, long, death, bio, meta, normalize_name(short), normalize_name(long)))
        count += 1
    con.commit()
    return count

def exact_match(con: sqlite3.Connection):
    mentions = con.execute("""
      SELECT mention_id, normalized_name
      FROM narrator_mentions_raw
      WHERE mention_type='named_candidate'
    """).fetchall()
    unique = ambiguous = unmatched = 0
    for mention_id, norm in mentions:
        rows = con.execute("""
          SELECT shamela_id,
                 CASE WHEN short_norm=? THEN 'exact_short' ELSE 'exact_long' END AS method
          FROM shamela_narrators
          WHERE short_norm=? OR long_norm=?
        """, (norm, norm, norm)).fetchall()
        ids = {}
        for sid, method in rows:
            ids.setdefault(sid, method)
        if len(ids) == 1:
            sid, method = next(iter(ids.items()))
            con.execute("INSERT OR REPLACE INTO mention_shamela_matches VALUES(?,?,?,?,?)",
                        (mention_id, sid, method, 1.0, "unique_exact"))
            unique += 1
        elif len(ids) > 1:
            for sid, method in ids.items():
                con.execute("INSERT OR REPLACE INTO mention_shamela_matches VALUES(?,?,?,?,?)",
                            (mention_id, sid, method, 1.0, "ambiguous_exact"))
            ambiguous += 1
        else:
            unmatched += 1
    con.commit()
    return unique, ambiguous, unmatched

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db", type=Path)
    ap.add_argument("shamela_seed", type=Path,
                    help="Shamela narrators.parquet, narrators.jsonl, or narrators-export.json")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    con.execute("PRAGMA foreign_keys=ON")
    imported = import_shamela(con, args.shamela_seed)
    unique, ambiguous, unmatched = exact_match(con)
    print("Shamela narrators imported:", imported)
    print("Unique exact mention matches:", unique)
    print("Ambiguous exact mention matches:", ambiguous)
    print("Unmatched mentions:", unmatched)
    print("No fuzzy or context merge is performed by this script.")

if __name__ == "__main__":
    main()
