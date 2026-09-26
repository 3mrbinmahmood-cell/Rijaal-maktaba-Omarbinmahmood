#!/usr/bin/env python3
"""Create a non-destructive candidate queue for unresolved narrator occurrences. Does not auto-merge."""
import argparse,collections,json,re,sqlite3
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def nrm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
 return re.sub(r'\s+',' ',s).strip()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('db');a=ap.parse_args();c=sqlite3.connect(a.db)
 c.executescript("""DROP TABLE IF EXISTS occurrence_identity_candidates_stage2;DROP TABLE IF EXISTS occurrence_candidate_summary_stage2;
 CREATE TABLE occurrence_identity_candidates_stage2(occurrence_id TEXT,candidate_anchor_id TEXT,name_match_score REAL,previous_relation_score REAL,next_relation_score REAL,chronology_penalty REAL,total_score REAL,evidence_json TEXT,candidate_status TEXT,PRIMARY KEY(occurrence_id,candidate_anchor_id));
 CREATE TABLE occurrence_candidate_summary_stage2(occurrence_id TEXT PRIMARY KEY,candidate_count INTEGER,top_anchor_id TEXT,top_score REAL,runner_up_score REAL,top_is_unique INTEGER,recommendation_status TEXT);""")
 anchors={};prefix=collections.defaultdict(set)
 for aid,name in c.execute('select anchor_id,canonical_name from tk_identity_anchors'):
  nn=nrm(name);anchors[aid]=nn;t=nn.split()
  for L in range(1,min(6,len(t))+1):prefix[' '.join(t[:L])].add(aid)
 rels={(s,t) for s,t in c.execute('select student_anchor_id,teacher_anchor_id from reported_relationships_stage1')}
 resolved={o:a for o,a in c.execute("select occurrence_id,anchor_id from occurrence_resolution_stage1 where status in ('provisional_anchor','strong_context','strong_graph')")}
 dates={aid:(b,d) for aid,b,d in c.execute('select anchor_id,best_birth_year_h,best_death_year_h from narrator_card_structured_stage2')}
 groups=collections.defaultdict(lambda:collections.defaultdict(list))
 for r in c.execute('select occurrence_id,sanad_id,branch_hint,sequence_index,atomic_index,normalized_name,occurrence_type from narrator_occurrences order by sanad_id,branch_hint,sequence_index,atomic_index'):groups[(r[1],r[2])][r[3]].append(r)
 for _,seqs in groups.items():
  order=sorted(seqs)
  for pos,seq in enumerate(order):
   if len(seqs[seq])!=1:continue
   r=seqs[seq][0];oid=r[0]
   if oid in resolved or r[6]!='named_candidate':continue
   raw=nrm(r[5]);cs=prefix.get(raw,set())
   if not cs or len(cs)>120:continue
   prev=nxt=None
   if pos>0 and order[pos-1]==seq-1 and len(seqs[order[pos-1]])==1:prev=resolved.get(seqs[order[pos-1]][0][0])
   if pos+1<len(order) and order[pos+1]==seq+1 and len(seqs[order[pos+1]])==1:nxt=resolved.get(seqs[order[pos+1]][0][0])
   for aid in cs:
    ns=min(3.0,.5+.5*len(raw.split()));ps=3.0 if prev and (prev,aid) in rels else 0;xs=3.0 if nxt and (aid,nxt) in rels else 0;pen=0
    cb,cd=dates.get(aid,(None,None))
    if prev:
     pb,pd=dates.get(prev,(None,None))
     if cb and pd and cb>pd:pen-=4
    if nxt:
     nb,nd=dates.get(nxt,(None,None))
     if nb and cd and nb>cd:pen-=4
    total=ns+ps+xs+pen;ev=json.dumps({'raw_name':raw,'candidate_count':len(cs),'previous_anchor':prev,'next_anchor':nxt,'prev_reported_relation':bool(ps),'next_reported_relation':bool(xs)},ensure_ascii=False)
    c.execute('insert or ignore into occurrence_identity_candidates_stage2 values(?,?,?,?,?,?,?,?,?)',(oid,aid,ns,ps,xs,pen,total,ev,'candidate'))
 c.commit()
 for (oid,) in c.execute('select distinct occurrence_id from occurrence_identity_candidates_stage2').fetchall():
  rows=c.execute('select candidate_anchor_id,total_score from occurrence_identity_candidates_stage2 where occurrence_id=? order by total_score desc,candidate_anchor_id',(oid,)).fetchall();top=rows[0];runner=rows[1][1] if len(rows)>1 else None
  if len(rows)==1 and top[1]>=5:status='unique_candidate_high'
  elif top[1]>=6 and (runner is None or top[1]>=runner+2):status='unique_top_strong'
  elif top[1]>=4 and (runner is None or top[1]>runner):status='unique_top_review'
  else:status='ambiguous'
  c.execute('insert into occurrence_candidate_summary_stage2 values(?,?,?,?,?,?,?)',(oid,len(rows),top[0],top[1],runner,int(len(rows)==1 or (runner is not None and top[1]>runner)),status))
 c.commit()
if __name__=='__main__':main()
