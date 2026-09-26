#!/usr/bin/env python3
"""
Resolve kinship expressions in isnads per occurrence.

Hard rule: أبيه / أبي / جده / عمه / أخيه / أمه are relationship pointers,
never narrator names. Resolution requires the governing narrator in that
specific chain plus lineage/biography evidence. Ambiguity remains unresolved.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, sqlite3

DIAC = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
TOKENS = ("ابيه","ابي","ابيها","جده","عمه","اخيه","امه")

def norm(s):
    s = DIAC.sub("", s or "").replace("ٱ","ا").replace("أ","ا").replace("إ","ا").replace("آ","ا").replace("ى","ي").replace("ابن","بن")
    s = re.sub(r'\([^)]{0,40}\)', ' ', s)
    s = re.sub(r'[ـ\u200c\u200d\u200e\u200f]', '', s)
    return re.sub(r'\s+', ' ', s).strip(' ،؛;:.()-')

def knorm(s):
    return re.sub(r'\bابي\b', 'ابو', norm(s))

def stable_anchor(entry_id):
    return "A_" + hashlib.blake2b(entry_id.encode(), digest_size=10).hexdigest()

def trim_explicit_relative(text):
    text = text.strip(' ،؛;:.()-')
    text = re.split(
        r'\b(?:انه|انها|ان|قال|قالت|حدثه|حدثها|اخبره|اخبرها|سمع|سمعت|وكان|وكانت|فانه|ومن طريق|اخرجه|ذكره|فذكره|يروي|روى)\b',
        text, maxsplit=1
    )[0]
    return re.split(r'[.؛;:\[]', text, maxsplit=1)[0].strip(' ،؛;:.()-')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase_db")
    ap.add_argument("tk_db")
    args = ap.parse_args()
    db = sqlite3.connect(args.phase_db)
    tk = sqlite3.connect(args.tk_db)

    entries = {}
    prefix = collections.defaultdict(set)
    kunyah = collections.defaultdict(set)
    for row in tk.execute("""
        SELECT entry_id,
               coalesce(canonical_name_v2,canonical_name),
               heading,
               coalesce(teachers_raw_v2,teachers_raw),
               coalesce(students_raw_v2,students_raw),
               body
        FROM entries
    """):
        eid, name, heading, teachers, students, body = row
        nn, hn = norm(name), norm(heading)
        entries[eid] = (name, nn, hn, norm(teachers), norm(students), body)
        toks = nn.split()
        for L in range(2, min(8, len(toks)) + 1):
            prefix[" ".join(toks[:L])].add(eid)

        # Only own kunyah: in canonical identity or introduced after a comma.
        aliases = []
        m = re.search(r'\bابو\s+[ء-ي]+(?:\s+[ء-ي]+){0,2}', nn)
        if m:
            aliases.append(m.group(0))
        intro = re.split(r'(?:روى|يروي)\s+عن', hn, maxsplit=1)[0]
        for m in re.finditer(r'(?:^|،)\s*(?:ويقال:?\s*)?(ابو\s+[ء-ي]+(?:\s+[ء-ي]+){0,2})', intro):
            aliases.append(m.group(1))
        for alias in aliases:
            at = knorm(alias).split()
            for L in range(2, len(at) + 1):
                kunyah[" ".join(at[:L])].add(eid)

    anchor_by_entry = {e:a for a,e in db.execute("SELECT anchor_id,tk_entry_id FROM tk_identity_anchors")}
    anchor_name = {a:n for a,n in db.execute("SELECT anchor_id,canonical_name FROM tk_identity_anchors")}
    resolved = {o:a for o,a in db.execute("""
        SELECT occurrence_id,anchor_id FROM occurrence_resolution_stage1
        WHERE status IN ('provisional_anchor','strong_context','strong_graph','strong_relational','strong_relational_named')
    """)}

    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in db.execute("""
        SELECT occurrence_id,sanad_id,branch_hint,sequence_index,atomic_index,
               normalized_name,occurrence_type,raw_atomic_name
        FROM narrator_occurrences
        ORDER BY sanad_id,branch_hint,sequence_index,atomic_index
    """):
        groups[(r[1],r[2])][r[3]].append(r)

    db.executescript("""
    CREATE TABLE IF NOT EXISTS kinship_resolution_evidence(
      occurrence_id TEXT PRIMARY KEY,
      relation_token TEXT NOT NULL,
      governing_anchor_id TEXT,
      explicit_relative_name TEXT,
      resolved_anchor_id TEXT,
      score REAL NOT NULL,
      status TEXT NOT NULL,
      evidence_json TEXT NOT NULL
    );
    """)

    def match_label(label):
        scores = collections.Counter()
        reasons = collections.defaultdict(list)
        lab = norm(label)
        toks = lab.split()
        if not toks:
            return scores, reasons
        if toks[0] not in ("ابي","ابو"):
            for L in range(min(7,len(toks)), 1, -1):
                ids = prefix.get(" ".join(toks[:L]), set())
                if ids:
                    for eid in ids:
                        scores[eid] += 9 if L >= 3 else 6
                        reasons[eid].append("explicit_relative_name")
                    break
        else:
            kt = knorm(lab).split()
            key = " ".join(kt[:2])
            extras = [x for x in kt[2:] if len(x) > 2]
            for eid in kunyah.get(key, set()):
                intro = knorm(re.split(r'(?:روى|يروي)\s+عن', entries[eid][2], maxsplit=1)[0])
                if extras and not all(x in intro for x in extras):
                    continue
                scores[eid] += 9 if extras else 6
                reasons[eid].append("explicit_relative_kunyah")
        return scores, reasons

    promoted = 0
    for _, seqs in groups.items():
        order = sorted(seqs)
        for i, seq in enumerate(order):
            for row in seqs[seq]:
                oid, _, _, _, _, raw_norm, occ_type, raw_text = row
                token = raw_norm if occ_type == "relational_or_unknown" and raw_norm in TOKENS else next(
                    (t for t in TOKENS if raw_norm.startswith(t + " ")), None
                )
                if not token:
                    continue
                if i == 0 or order[i-1] != seq-1 or len(seqs[order[i-1]]) != 1:
                    continue
                gov_oid = seqs[order[i-1]][0][0]
                gov = resolved.get(gov_oid)
                if not gov:
                    continue

                explicit = ""
                if raw_norm.startswith(token + " "):
                    explicit = trim_explicit_relative(raw_norm[len(token):])

                scores, reasons = match_label(explicit) if explicit else (collections.Counter(), collections.defaultdict(list))

                # Father: derive directly from resolved lineage if no explicit name.
                if token in ("ابيه","ابي","ابيها") and not explicit:
                    gn = norm(anchor_name.get(gov, ""))
                    m = re.search(r'\bبن\s+(.+)$', gn)
                    if m:
                        tail = m.group(1).split()
                        if tail and tail[0] not in ("ابي","ابو"):
                            for L in range(min(7,len(tail)), 2, -1):
                                ids = prefix.get(" ".join(tail[:L]), set())
                                if ids:
                                    for eid in ids:
                                        scores[eid] += 7
                                        reasons[eid].append("direct_father_lineage")
                                    break

                # Grandfather after a resolved father node: father of that father.
                if token == "جده" and not explicit:
                    prev_rel = db.execute(
                        "SELECT relation_token FROM kinship_resolution_evidence WHERE occurrence_id=?",
                        (gov_oid,)
                    ).fetchone()
                    if prev_rel and prev_rel[0] in ("ابيه","ابي","ابيها"):
                        gn = norm(anchor_name.get(gov, ""))
                        m = re.search(r'\bبن\s+(.+)$', gn)
                        if m:
                            tail = m.group(1).split()
                            for L in range(min(7,len(tail)), 2, -1):
                                ids = prefix.get(" ".join(tail[:L]), set())
                                if ids:
                                    for eid in ids:
                                        scores[eid] += 8
                                        reasons[eid].append("grandfather_after_resolved_father")
                                    break

                ranked = sorted(scores.items(), key=lambda x:(-x[1],x[0]))
                if not ranked or ranked[0][1] < 7 or (len(ranked)>1 and ranked[0][1] < ranked[1][1] + 2):
                    db.execute("INSERT OR REPLACE INTO kinship_resolution_evidence VALUES(?,?,?,?,?,?,?,?)",
                               (oid,token,gov,explicit,None,ranked[0][1] if ranked else 0,"unresolved",
                                json.dumps({"candidate_count":len(ranked),"top":ranked[:5]},ensure_ascii=False)))
                    continue

                eid, score = ranked[0]
                target = anchor_by_entry.get(eid)
                if not target:
                    target = stable_anchor(eid)
                    name = entries[eid][0]
                    db.execute("INSERT OR IGNORE INTO tk_identity_anchors VALUES(?,?,?,?,?)",
                               (target,eid,name,norm(name),"relational_context"))
                    anchor_by_entry[eid] = target
                    anchor_name[target] = name

                ev = {
                    "relation_token": token,
                    "raw": raw_text,
                    "governing_anchor": gov,
                    "governing_name": anchor_name.get(gov),
                    "explicit_relative_name": explicit or None,
                    "candidate_name": entries[eid][0],
                    "reasons": reasons[eid],
                    "runner_up_score": ranked[1][1] if len(ranked)>1 else None,
                }
                status = "strong_relational_named" if explicit else "strong_relational"
                db.execute("INSERT OR REPLACE INTO occurrence_resolution_stage1 VALUES(?,?,?,?,?,?)",
                           (oid,target,"direct_context_kinship",score,json.dumps(ev,ensure_ascii=False),status))
                db.execute("INSERT OR REPLACE INTO kinship_resolution_evidence VALUES(?,?,?,?,?,?,?,?)",
                           (oid,token,gov,explicit,target,score,"resolved",json.dumps(ev,ensure_ascii=False)))
                resolved[oid] = target
                promoted += 1

    db.commit()
    print("kinship occurrences promoted:", promoted)

if __name__ == "__main__":
    main()
