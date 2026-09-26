#!/usr/bin/env python3
"""Conservative occurrence-level identity resolver using Tahdhib al-Kamal context."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, sqlite3
from pathlib import Path
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def norm(s):
    s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
    return re.sub(r'\s+',' ',re.sub(r'[ـ\u200c\u200d\u200e\u200f]','',s)).strip(' ،؛;:.()-')
def aid(eid):return 'A_'+hashlib.blake2b(eid.encode(),digest_size=10).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase_db',type=Path);ap.add_argument('core_index',type=Path);a=ap.parse_args()
    p=sqlite3.connect(a.phase_db);k=sqlite3.connect(a.core_index)
    entries={};prefix=collections.defaultdict(list);candidate=collections.defaultdict(list)
    for eid,cn,nn,tr,st in k.execute('select entry_id,canonical_name,canonical_norm,teachers_raw,students_raw from entries where confidence>=.8'):
        entries[eid]=(cn,nn,norm(tr),norm(st)); toks=nn.split()
        for i in range(3,len(toks)+1):prefix[' '.join(toks[:i])].append(eid)
        for i in range(1,min(5,len(toks))+1):candidate[' '.join(toks[:i])].append(eid)
    p.executescript("""DROP TABLE IF EXISTS tk_identity_anchors;DROP TABLE IF EXISTS occurrence_resolution_stage1;
    CREATE TABLE tk_identity_anchors(anchor_id TEXT PRIMARY KEY,tk_entry_id TEXT NOT NULL,canonical_name TEXT NOT NULL,canonical_norm TEXT NOT NULL,anchor_method TEXT NOT NULL);
    CREATE TABLE occurrence_resolution_stage1(occurrence_id TEXT PRIMARY KEY,anchor_id TEXT NOT NULL,resolution_method TEXT NOT NULL,score REAL NOT NULL,evidence_json TEXT NOT NULL,status TEXT NOT NULL);
    CREATE INDEX idx_res_anchor ON occurrence_resolution_stage1(anchor_id);""")
    name_anchor={}
    for name,n in p.execute("select normalized_name,count(*) from narrator_occurrences where occurrence_type='named_candidate' group by normalized_name"):
        toks=name.split()
        if len(toks)<3 or toks[0] in {'ابن','ابو','ابي','ام'} or toks[1]!='بن':continue
        ids=list(dict.fromkeys(prefix.get(name,[])))
        if len(ids)==1:
            eid=ids[0];cn,nn,_,_=entries[eid];an=aid(eid);name_anchor[name]=(an,eid)
            p.execute('insert or ignore into tk_identity_anchors values(?,?,?,?,?)',(an,eid,cn,nn,'unique_full_name_prefix'))
    for oid,name in p.execute("select occurrence_id,normalized_name from narrator_occurrences where occurrence_type='named_candidate'"):
        if name in name_anchor:
            an,eid=name_anchor[name]
            p.execute('insert into occurrence_resolution_stage1 values(?,?,?,?,?,?)',(oid,an,'unique_full_name_prefix',1.0,json.dumps({'raw_name':name,'tk_entry_id':eid},ensure_ascii=False),'provisional_anchor'))
    p.commit()
    resmap={r[0]:r[1] for r in p.execute('select occurrence_id,anchor_id from occurrence_resolution_stage1')}
    an_to_eid={r[0]:r[1] for r in p.execute('select anchor_id,tk_entry_id from tk_identity_anchors')}
    groups=collections.defaultdict(lambda:collections.defaultdict(list))
    for row in p.execute('select occurrence_id,sanad_id,branch_hint,sequence_index,atomic_index,normalized_name,occurrence_type from narrator_occurrences order by sanad_id,branch_hint,sequence_index,atomic_index'):
        groups[(row[1],row[2])][row[3]].append(row)
    new=[]
    for (_,branch),seqs in groups.items():
        ordered=sorted(seqs)
        for pos,seq in enumerate(ordered):
            if len(seqs[seq])!=1:continue
            row=seqs[seq][0];oid=row[0]
            if oid in resmap or row[6]!='named_candidate':continue
            name=row[5];cids=list(dict.fromkeys(candidate.get(name,[])))
            if not(1<len(cids)<=80):continue
            prev=nxt=None
            if pos>0 and ordered[pos-1]==seq-1 and len(seqs[ordered[pos-1]])==1:
                poid=seqs[ordered[pos-1]][0][0]
                if poid in resmap:prev=(seqs[ordered[pos-1]][0][5],an_to_eid[resmap[poid]])
            if pos+1<len(ordered) and ordered[pos+1]==seq+1 and len(seqs[ordered[pos+1]])==1:
                noid=seqs[ordered[pos+1]][0][0]
                if noid in resmap:nxt=(seqs[ordered[pos+1]][0][5],an_to_eid[resmap[noid]])
            if not prev and not nxt:continue
            scored=[]
            for eid in cids:
                cn,nn,teachers,students=entries[eid];score=0;signals=[]
                if prev:
                    raw,peid=prev;pcn=entries[peid][1]
                    if raw in students:score+=3;signals.append('previous_raw_in_students')
                    elif ' '.join(pcn.split()[:3]) in students:score+=2;signals.append('previous_canonical_in_students')
                if nxt:
                    raw,neid=nxt;ncn=entries[neid][1]
                    if raw in teachers:score+=3;signals.append('next_raw_in_teachers')
                    elif ' '.join(ncn.split()[:3]) in teachers:score+=2;signals.append('next_canonical_in_teachers')
                if score:scored.append((score,eid,signals))
            scored.sort(reverse=True)
            if not scored:continue
            best=scored[0];second=scored[1][0] if len(scored)>1 else 0
            # Only two-sided / >=5 evidence is promoted automatically.
            if best[0]>=5 and best[0]>second:
                eid=best[1];cn,nn,_,_=entries[eid];an=aid(eid)
                p.execute('insert or ignore into tk_identity_anchors values(?,?,?,?,?)',(an,eid,cn,nn,'strong_context'))
                ev={'raw_name':name,'candidate_count':len(cids),'previous':prev[0] if prev else None,'next':nxt[0] if nxt else None,'signals':best[2],'runner_up_score':second}
                new.append((oid,an,'neighbor_teacher_student',best[0],json.dumps(ev,ensure_ascii=False),'strong_context'))
    p.executemany('insert or ignore into occurrence_resolution_stage1 values(?,?,?,?,?,?)',new);p.commit()
    print('identity anchors',p.execute('select count(*) from tk_identity_anchors').fetchone()[0])
    print('full-name occurrences',p.execute("select count(*) from occurrence_resolution_stage1 where status='provisional_anchor'").fetchone()[0])
    print('strong two-sided context occurrences',p.execute("select count(*) from occurrence_resolution_stage1 where status='strong_context'").fetchone()[0])
if __name__=='__main__':main()
