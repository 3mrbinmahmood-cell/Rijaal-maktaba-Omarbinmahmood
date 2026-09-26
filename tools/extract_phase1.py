#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, re, sqlite3
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

AR_DIAC = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
MARK_RE = re.compile(r'^\s*[\u200c\u200d\u200e\u200f]*\(?(\d{1,6})\)?\s*[-–—]\s*$')
TITLE_PREFIXES = ("باب","بَاب","كتاب","كِتَاب","أبواب","أَبْوَاب","فصل","فَصْل","المقدمة","مقدمة")
START_CHAIN = re.compile(
    r'(?:(?:و|ف)?حَدَّثَنَا|(?:و|ف)?حدثنا|(?:و|ف)?حَدَّثَنِي|(?:و|ف)?حدثني|'
    r'(?:و|ف)?أَخْبَرَنَا|(?:و|ف)?أخبرنا|(?:و|ف)?أَخْبَرَنِي|(?:و|ف)?أخبرني|'
    r'(?:و|ف)?أَنْبَأَنَا|(?:و|ف)?أنبأنا|(?:و|ف)?سَمِعْتُ|(?:و|ف)?سمعت)'
)
PROPHET_BOUNDARIES = [
    re.compile(r'\b(?:أَنَّ|أنَّ|أن|أَنَّهُ|أنه|أَنَّهَا|أنها)\s+(?:النَّبِيَّ|النبي|رَسُولَ اللَّهِ|رسول الله)'),
    re.compile(r'\b(?:قَالَ|قال)\s*:\s*(?:قَالَ|قال)\s+(?:رَسُولُ اللَّهِ|رسول الله|النَّبِيُّ|النبي)'),
    re.compile(r'\b(?:قَالَ|قال)\s+(?:رَسُولُ اللَّهِ|رسول الله|النَّبِيُّ|النبي)'),
    re.compile(r'\b(?:سَمِعْتُ|سمعت|رَأَيْتُ|رأيت)\s+(?:رَسُولَ اللَّهِ|رسول الله|النَّبِيَّ|النبي)'),
]
CHAIN_START_WORDS = (
    "حدثنا","وحدثنا","حدثني","وحدثني","اخبرنا","واخبرنا","اخبرني","واخبرني",
    "انبانا","وانبانا","سمعت","وسمعت","قالا","وقالا","قال","وقال","انه سمع",
    "انها سمعت","اخبره","اخبرها"
)

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS source_files(
  source_file_id TEXT PRIMARY KEY,
  book_title TEXT NOT NULL,
  volume INTEGER,
  file_kind TEXT NOT NULL,
  filename TEXT NOT NULL UNIQUE,
  sha256 TEXT NOT NULL UNIQUE,
  size_bytes INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS hadith_records(
  hadith_record_id TEXT PRIMARY KEY,
  source_file_id TEXT NOT NULL REFERENCES source_files(source_file_id),
  marker_number INTEGER,
  page_label TEXT,
  record_type TEXT NOT NULL,
  body_raw TEXT NOT NULL,
  body_sha256 TEXT NOT NULL,
  extraction_method TEXT NOT NULL,
  needs_review INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_hadith_source_num ON hadith_records(source_file_id, marker_number);
CREATE TABLE IF NOT EXISTS sanad_candidates(
  sanad_id TEXT PRIMARY KEY,
  hadith_record_id TEXT REFERENCES hadith_records(hadith_record_id),
  source_file_id TEXT NOT NULL REFERENCES source_files(source_file_id),
  evidence_layer TEXT NOT NULL,
  sanad_raw TEXT NOT NULL,
  boundary_method TEXT NOT NULL,
  confidence REAL NOT NULL,
  terminal_prophet_hint INTEGER NOT NULL DEFAULT 0,
  needs_extension_review INTEGER NOT NULL DEFAULT 0,
  needs_review INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sanad_record ON sanad_candidates(hadith_record_id);
CREATE TABLE IF NOT EXISTS page_footnotes(
  footnote_id TEXT PRIMARY KEY,
  source_file_id TEXT NOT NULL REFERENCES source_files(source_file_id),
  page_label TEXT,
  footnote_raw TEXT NOT NULL,
  footnote_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS extraction_runs(
  run_id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  extractor_version TEXT NOT NULL,
  source_dir TEXT NOT NULL,
  source_file_count INTEGER NOT NULL,
  record_count INTEGER NOT NULL,
  sanad_candidate_count INTEGER NOT NULL,
  footnote_count INTEGER NOT NULL
);
"""

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def stable_id(prefix: str, *parts: object, n: int = 20) -> str:
    s = "\x1f".join("" if p is None else str(p) for p in parts)
    return prefix + hashlib.blake2b(s.encode("utf-8"), digest_size=16).hexdigest()[:n]

def undiac(s: str) -> str:
    return AR_DIAC.sub("", s)

def has_ancestor_class(node, classes: set[str]) -> bool:
    p = node.parent if hasattr(node, "parent") else None
    while p is not None:
        cls = set(p.get("class", [])) if isinstance(p, Tag) else set()
        if cls & classes:
            return True
        p = p.parent if hasattr(p, "parent") else None
    return False

def parse_filename(path: Path):
    stem = path.stem
    m = re.search(r'\s*-\s*المجلد\s+(\d+)$', stem)
    if m:
        return stem[:m.start()].strip(), int(m.group(1)), "volume"
    m = re.search(r'\s*-\s*ملحق\s+(\d+)$', stem)
    if m:
        return stem[:m.start()].strip(), None, "supplement"
    if stem.endswith(" - المقدمة"):
        return stem[:-len(" - المقدمة")].strip(), None, "introduction"
    return stem, None, "standalone"

def page_segments_and_footnotes(path: Path):
    soup = BeautifulSoup(path.read_text("utf-8"), "lxml")
    for div in soup.select("div.PageText"):
        page_el = div.select_one(".PageNumber")
        page = page_el.get_text(" ", strip=True) if page_el else ""
        for fn in div.select(".footnote"):
            txt = re.sub(r'\s+', ' ', fn.get_text(" ", strip=True)).strip()
            if txt:
                yield ("footnote", page, None, txt)
        events = []
        for desc in div.descendants:
            if isinstance(desc, Tag) and desc.name == "span" and "punct" in desc.get("class", []):
                if has_ancestor_class(desc, {"footnote", "PageHead"}) or desc.find_parent("sup") is not None:
                    continue
                t = desc.get_text(" ", strip=True).replace("\u200c", "").replace("\u200f", "")
                m = MARK_RE.match(t)
                if m:
                    events.append(("marker", int(m.group(1))))
            elif isinstance(desc, NavigableString):
                if has_ancestor_class(desc, {"footnote", "PageHead"}):
                    continue
                if desc.find_parent("span", class_="punct") is not None:
                    continue
                txt = str(desc)
                if txt.strip():
                    events.append(("text", txt))
        cur = None
        for ev in events:
            if ev[0] == "marker":
                if cur is not None:
                    cur["text"] = re.sub(r'\s+', ' ', cur["text"]).strip()
                    yield ("segment", page, cur["num"], cur["text"])
                cur = {"num": ev[1], "text": ""}
            elif cur is not None:
                cur["text"] += " " + ev[1]
        if cur is not None:
            cur["text"] = re.sub(r'\s+', ' ', cur["text"]).strip()
            yield ("segment", page, cur["num"], cur["text"])

def classify_segment(text: str) -> str:
    t = text.lstrip(" \u200c\u200f\u200e")
    t = re.sub(r'^\(\d+\)\s*', '', t)
    if t.startswith(TITLE_PREFIXES):
        return "title"
    nt = undiac(t).replace("أ","ا").replace("إ","ا").replace("آ","ا")
    if START_CHAIN.search(t[:300]) or re.search(r'(?:^|\s)(?:و?حدثنا|و?حدثني|و?اخبرنا|و?اخبرني|و?انبانا|و?سمعت)\b', nt[:300]):
        return "hadith"
    if re.match(r'^(?:و?قال|و?قَالَ|و?عَنْ|و?عن)\s+', t) and len(t) > 80:
        return "report"
    if any(x in t[:500] for x in ("رسول الله","رَسُولُ اللَّهِ","النبي","النَّبِي")) and len(t) > 80:
        return "report"
    return "other"

def is_chain_continuation(after: str) -> bool:
    n = undiac(after).replace("أ","ا").replace("إ","ا").replace("آ","ا")
    n = n.strip(" \u200c\u200f\u200e.,،؛;:-")
    return any(n.startswith(w) for w in CHAIN_START_WORDS)

def extract_sanad_prefix(text: str):
    t = re.sub(r'^\(\d+\)\s*', '', text.strip())
    m = START_CHAIN.search(t[:350])
    if m:
        start = m.start()
    else:
        nt = undiac(t).replace("أ","ا").replace("إ","ا").replace("آ","ا")
        nm = re.search(r'(?:^|\s)(?:و?حدثنا|و?حدثني|و?اخبرنا|و?اخبرني|و?انبانا|و?سمعت)\b', nt[:350])
        if nm and nm.start() < 80:
            start = 0
        elif re.match(r'^(?:و?قال|و?قَالَ|و?عَنْ|و?عن)\s+', t):
            start = 0
        else:
            return None
    sub = t[start:]
    candidates = []
    for pat in PROPHET_BOUNDARIES:
        mm = pat.search(sub)
        if not mm or mm.start() <= 15:
            continue
        g = undiac(mm.group(0))
        terminal = 1
        if g.startswith(("سمعت", "رأيت")):
            end = mm.end()
            ext = re.match(r'(?:\s+صلى الله عليه وسلم)?(?:\s+(?:يقول|يَقُولُ|قال|قَالَ))?', sub[end:])
            if ext:
                end += ext.end()
        elif g.startswith(("قال رسول", "قال النبي")):
            end = mm.end()
            ext = re.match(r'(?:\s+صلى الله عليه وسلم)?', sub[end:])
            if ext:
                end += ext.end()
        else:
            end = mm.start()
        candidates.append((end, "prophet_boundary", 0.90, terminal))
    for mm in re.finditer(r'[:؛;]', sub):
        if mm.start() <= 30:
            continue
        after = sub[mm.end():mm.end()+140]
        if is_chain_continuation(after):
            continue
        before = undiac(sub[max(0, mm.start()-220):mm.start()])
        if re.search(r'(?:عن|اخبر|حدث|سمع|قال)', before) and len(re.findall(r'(?:عن|حدث|اخبر|سمع)', undiac(sub[:mm.start()]))) >= 2:
            candidates.append((mm.start()+1, "reporter_boundary", 0.78, 0))
            break
    if not candidates:
        raw = sub[:1400].strip()
        if len(raw) < 25:
            return None
        return raw, "open_ended", 0.40, 0, 1
    end, method, conf, terminal = min(candidates, key=lambda x: x[0])
    raw = sub[:end].strip()
    after = sub[end:end+1200]
    extension = 1 if method == "reporter_boundary" and re.search(
        r'(?:سَمِعْتُ|سمعت|قَالَ|قال).{0,50}(?:رَسُولُ اللَّهِ|رسول الله|النَّبِي|النبي)', after
    ) else 0
    return raw, method, conf, terminal, extension

def build_db(source_dir: Path, db_path: Path):
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    files = sorted(source_dir.glob("*.htm"), key=lambda p: p.name)
    record_count = sanad_count = foot_count = 0
    for path in files:
        data = path.read_bytes()
        fsha = sha256_bytes(data)
        book, volume, kind = parse_filename(path)
        sfid = stable_id("SF_", fsha)
        con.execute("INSERT INTO source_files VALUES(?,?,?,?,?,?,?)",
                    (sfid, book, volume, kind, path.name, fsha, len(data)))
        seg_seq = fn_seq = 0
        for typ, page, marker, text in page_segments_and_footnotes(path):
            if typ == "footnote":
                fn_seq += 1
                tsha = sha256_bytes(text.encode("utf-8"))
                fnid = stable_id("FN_", fsha, page, fn_seq, tsha)
                con.execute("INSERT INTO page_footnotes VALUES(?,?,?,?,?)",
                            (fnid, sfid, page, text, tsha))
                foot_count += 1
                continue
            seg_seq += 1
            rtype = classify_segment(text)
            if rtype == "title":
                continue
            bsha = sha256_bytes(text.encode("utf-8"))
            hid = stable_id("H_", fsha, page, marker, seg_seq, bsha)
            con.execute("INSERT INTO hadith_records VALUES(?,?,?,?,?,?,?,?,?)",
                        (hid, sfid, marker, page, rtype, text, bsha, "numeric_marker_v1", 1 if rtype == "other" else 0))
            record_count += 1
            if rtype in ("hadith", "report"):
                cand = extract_sanad_prefix(text)
                if cand:
                    raw, method, conf, terminal, extension = cand
                    sid = stable_id("S_", hid, raw)
                    con.execute("INSERT INTO sanad_candidates VALUES(?,?,?,?,?,?,?,?,?,?)",
                                (sid, hid, sfid, "primary_body", raw, method, conf, terminal, extension,
                                 1 if conf < 0.8 or extension else 0))
                    sanad_count += 1
        con.commit()
    con.execute(
        "INSERT INTO extraction_runs(extractor_version,source_dir,source_file_count,record_count,sanad_candidate_count,footnote_count) VALUES(?,?,?,?,?,?)",
        ("phase1-v1", str(source_dir), len(files), record_count, sanad_count, foot_count)
    )
    con.commit()
    return con

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source_dir", type=Path)
    ap.add_argument("--db", type=Path, default=Path("data/rijaal_phase1.sqlite"))
    args = ap.parse_args()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    con = build_db(args.source_dir, args.db)
    print(dict(con.execute("SELECT 'source_files',count(*) FROM source_files UNION ALL SELECT 'hadith_records',count(*) FROM hadith_records UNION ALL SELECT 'sanad_candidates',count(*) FROM sanad_candidates UNION ALL SELECT 'page_footnotes',count(*) FROM page_footnotes").fetchall()))
