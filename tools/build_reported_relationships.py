#!/usr/bin/env python3
"""Convert Tahdhib al-Kamal teacher/student lists into conservative anchor-ID relationships."""
import argparse, collections, hashlib, re, sqlite3
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def norm(s):
    s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
    s=re.sub(r'\([^)]{0,30}\)',' ',s);s=re.sub(r'[ـ\u200c\u200d\u200e\u200f]','',s)
    return re.sub(r'\s+',' ',s).strip(' ،؛;:.()-')
def segments(s):
    out=[]
    for x in re.split(r'[،,؛;]',s or ''):
        x=norm(x);x=re.sub(r'^و(?=[اأإآء-ي])','',x).strip()
        if len(x)>=3:out.append(x)
    return out
def main():
    ap=argparse.ArgumentParser();ap.add_argument('db');a=ap.parse_args();c=sqlite3.connect(a.db)
    anchors={r[0]:(r[1],norm(r[1])) for r in c.execute('select anchor_id,canonical_name from tk_identity_anchors')}
    raw=collections.defaultdict(set)
    for aid,(_,nn) in anchors.items():
        t=nn.split()
        for L in range(2,min(6,len(t))+1):raw[' '.join(t[:L])].add(aid)
    unique={k:next(iter(v)) for k,v in raw.items() if len(v)==1};byfirst=collections.defaultdict(list)
    for key,aid in unique.items():byfirst[key.split()[0]].append((len(key.split()),key,aid))
    for arr in byfirst.values():arr.sort(reverse=True)
    def match(seg):
        t=seg.split();hits=[]
        for L,key,aid in byfirst.get(t[0] if t else '',[]):
            if seg==key or seg.startswith(key+' '):hits.append((L,aid))
        if not hits:return None
        best=max(x[0] for x in hits);ids={x[1] for x in hits if x[0]==best}
        return next(iter(ids)) if len(ids)==1 else None
    c.executescript("""DROP TABLE IF EXISTS reported_relationship_evidence_stage1;DROP TABLE IF EXISTS reported_relationships_stage1;
    CREATE TABLE reported_relationship_evidence_stage1(evidence_id TEXT PRIMARY KEY,student_anchor_id TEXT NOT NULL,teacher_anchor_id TEXT NOT NULL,direction_source TEXT NOT NULL,source_segment TEXT NOT NULL,source_title TEXT NOT NULL);
    CREATE TABLE reported_relationships_stage1(student_anchor_id TEXT NOT NULL,teacher_anchor_id TEXT NOT NULL,teacher_list_evidence INTEGER NOT NULL,student_list_evidence INTEGER NOT NULL,status TEXT NOT NULL,PRIMARY KEY(student_anchor_id,teacher_anchor_id));""")
    ev=[]
    for aid,tr,st in c.execute('select anchor_id,teachers_raw,students_raw from narrator_cards_stage1'):
        for x in segments(tr):
            tid=match(x)
            if tid and tid!=aid:
                eid='RE_'+hashlib.blake2b(f'{aid}|{tid}|teachers|{x}'.encode(),digest_size=12).hexdigest();ev.append((eid,aid,tid,'teacher_list',x,'تهذيب الكمال'))
        for x in segments(st):
            sid=match(x)
            if sid and sid!=aid:
                eid='RE_'+hashlib.blake2b(f'{sid}|{aid}|students|{x}'.encode(),digest_size=12).hexdigest();ev.append((eid,sid,aid,'student_list',x,'تهذيب الكمال'))
    c.executemany('insert or ignore into reported_relationship_evidence_stage1 values(?,?,?,?,?,?)',ev)
    pairs=collections.defaultdict(lambda:[0,0])
    for s,t,d in c.execute('select student_anchor_id,teacher_anchor_id,direction_source from reported_relationship_evidence_stage1'):
        pairs[(s,t)][0 if d=='teacher_list' else 1]=1
    for (s,t),(te,se) in pairs.items():
        status='bilateral_reported' if te and se else 'teacher_list_only' if te else 'student_list_only'
        c.execute('insert into reported_relationships_stage1 values(?,?,?,?,?)',(s,t,te,se,status))
    c.commit();print('relationships',len(pairs));print(list(c.execute('select status,count(*) from reported_relationships_stage1 group by status')))
if __name__=='__main__':main()
