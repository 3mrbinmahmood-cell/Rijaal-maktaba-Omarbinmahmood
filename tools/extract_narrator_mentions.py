#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, re, sqlite3
from pathlib import Path

AR_DIAC = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
CONNECTOR_RE = re.compile(
    r'(?P<term>'
    r'حَدَّثَنَا|حدَّثنا|حَدَّثَنا|حدثنا|حَدَّثَنِي|حدَّثني|حدثني|'
    r'أَخْبَرَنَا|أخبرنا|اخبرنا|أَخْبَرَنِي|أخبرني|اخبرني|'
    r'أَنْبَأَنَا|أنبأنا|انبأنا|'
    r'عَنْ|عَنِ|عن|'
    r'سَمِعْتُ|سمعت|أَنَّهُ سَمِعَ|أنه سمع|أَنَّهَا سَمِعَتْ|أنها سمعت'
    r')\s+'
)
EMBEDDED_RE = re.compile(
    r'(?:أَنَّ|أنَّ|أن|أَنَّ)\s+(.{2,120}?)\s+'
    r'(أَخْبَرَهُ|أخبره|أَخْبَرَهَا|أخبرها|قَالَ|قال)(?=[،,:؛;]|$)'
)
ROUTE_RE = re.compile(r'(?:\(\s*ح\s*\)|(?:^|\s)ح\s+(?=و?(?:حَدَّث|حدث|أَخْبَر|أخبر)))')
HONORIFIC_RE = re.compile(r'\s+(?:رضي الله عنهما|رضي الله عنه|رضي الله عنها|رحمه الله|رحمها الله).*$')
RELATIONAL = {
    "ابيه","ابيها","ابوه","ابوها","عمه","عمهما","جده","امه","اخيه",
    "رجل","بعض اصحابه","من حدثه","شيخ","رجل من اصحابه"
}
SCHEMA = """
CREATE TABLE IF NOT EXISTS narrator_mentions_raw(
  mention_id TEXT PRIMARY KEY,
  sanad_id TEXT NOT NULL REFERENCES sanad_candidates(sanad_id),
  sequence_index INTEGER NOT NULL,
  branch_hint INTEGER NOT NULL DEFAULT 0,
  transmission_term TEXT NOT NULL,
  raw_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  mention_type TEXT NOT NULL,
  is_group INTEGER NOT NULL DEFAULT 0,
  needs_review INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_mentions_sanad ON narrator_mentions_raw(sanad_id, sequence_index);
CREATE INDEX IF NOT EXISTS idx_mentions_norm ON narrator_mentions_raw(normalized_name);
"""

def undiac(s: str) -> str:
    return AR_DIAC.sub("", s)

def normalize_name(s: str) -> str:
    s = undiac(s)
    s = s.replace("ٱ","ا").replace("أ","ا").replace("إ","ا").replace("آ","ا")
    s = s.replace("ى","ي")
    s = re.sub(r'[ـ\u200c\u200d\u200e\u200f]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip(" ،؛;:.()-")

def clean_phrase(s: str) -> str:
    s = s.strip(" \u200c\u200f\u200e،؛;:.()-")
    s = re.split(r'[،,]\s*(?=أَنَّ|أنَّ|أن\s)', s, maxsplit=1)[0]
    s = HONORIFIC_RE.sub('', s)
    s = re.sub(r'\s+(?:عَلَى الْمِنْبَرِ|على المنبر).*$', '', s)
    s = re.sub(r'\s+(?:فِي قَوْلِهِ تَعَالَى|في قوله تعالى).*$', '', s)
    s = re.sub(r'\s+(?:رِوَايَةً|روايةً).*$', '', s)
    s = re.sub(r'\s+(?:أَنَّهَا قَالَتْ|أنها قالت|أَنَّهُ قَالَ|أنه قال)\s*$', '', s)
    s = re.sub(r'\s+(?:يَقُولُ|يقول)\s*$', '', s)
    s = re.sub(r'\s+(?:قَالَ|قال|قَالَا|قالا)\s*:?$', '', s)
    s = re.sub(r'\s*\(ح\)\.?\s*و?$', '', s)
    s = re.sub(r'\s+نَحْوَهُ$', '', s)
    return s.strip(" \u200c\u200f\u200e،؛;:.()-")

def mention_type(name: str) -> str:
    n = normalize_name(name)
    if n in RELATIONAL:
        return "relational_or_unknown"
    if "رسول الله" in n or "النبي" in n:
        return "prophet_terminal"
    return "named_candidate"

def stable_id(*parts: object) -> str:
    raw = "\x1f".join(str(x) for x in parts)
    return "M_" + hashlib.blake2b(raw.encode("utf-8"), digest_size=16).hexdigest()[:20]

def route_branch(sanad: str, pos: int) -> int:
    return len(list(ROUTE_RE.finditer(sanad[:pos])))

def extract_mentions(sanad: str):
    direct = list(CONNECTOR_RE.finditer(sanad))
    out = []
    for i, m in enumerate(direct):
        st = m.end()
        en = direct[i+1].start() if i+1 < len(direct) else len(sanad)
        phrase = sanad[st:en]
        phrase = re.split(r'\s+(?:قَالَ|قال|قَالَا|قالا)\s*:', phrase, maxsplit=1)[0]
        phrase = clean_phrase(phrase)
        if phrase:
            out.append({
                "start": m.start(),
                "term": undiac(m.group("term")),
                "raw_name": phrase,
                "mention_type": mention_type(phrase),
                "branch": route_branch(sanad, m.start())
            })
    for m in EMBEDDED_RE.finditer(sanad):
        name = clean_phrase(m.group(1))
        if not name:
            continue
        if any(abs(m.start() - x["start"]) < 8 and normalize_name(name) == normalize_name(x["raw_name"]) for x in out):
            continue
        out.append({
            "start": m.start(),
            "term": "embedded_" + undiac(m.group(2)),
            "raw_name": name,
            "mention_type": mention_type(name),
            "branch": route_branch(sanad, m.start())
        })
    out.sort(key=lambda x: (x["start"], x["term"]))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db", type=Path)
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(SCHEMA)
    con.execute("DELETE FROM narrator_mentions_raw")
    rows = con.execute("SELECT sanad_id, sanad_raw FROM sanad_candidates ORDER BY sanad_id").fetchall()
    count = 0
    for sanad_id, sanad in rows:
        for seq, m in enumerate(extract_mentions(sanad), 1):
            norm = normalize_name(m["raw_name"])
            # This is only a raw occurrence layer. Do not merge identities here.
            is_group = 0
            review = 1 if m["mention_type"] != "named_candidate" or len(norm) < 3 or len(norm) > 120 else 0
            mid = stable_id(sanad_id, seq, m["start"], m["raw_name"])
            con.execute(
                "INSERT INTO narrator_mentions_raw VALUES(?,?,?,?,?,?,?,?,?,?)",
                (mid, sanad_id, seq, m["branch"], m["term"], m["raw_name"], norm,
                 m["mention_type"], is_group, review)
            )
            count += 1
    con.commit()
    print("mentions", count)
    print("distinct normalized", con.execute(
        "SELECT count(DISTINCT normalized_name) FROM narrator_mentions_raw WHERE mention_type='named_candidate'"
    ).fetchone()[0])
    print("relational/unknown", con.execute(
        "SELECT count(*) FROM narrator_mentions_raw WHERE mention_type='relational_or_unknown'"
    ).fetchone()[0])
    print("prophet terminal", con.execute(
        "SELECT count(*) FROM narrator_mentions_raw WHERE mention_type='prophet_terminal'"
    ).fetchone()[0])

if __name__ == "__main__":
    main()
