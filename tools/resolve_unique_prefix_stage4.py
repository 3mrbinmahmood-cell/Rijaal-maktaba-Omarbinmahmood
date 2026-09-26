from __future__ import annotations
import argparse,collections,hashlib,json,re,sqlite3
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def norm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
 return re.sub(r'\s+',' ',re.sub(r'[ـ\u200c\u200d\u200e\u200f]','',s)).strip(' ،؛;:.-')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('db');a=ap.parse_args();c=sqlite3.connect(a.db)
 c.executescript("""DROP TABLE IF EXISTS unique_prefix_resolution_stage4;CREATE TABLE unique_prefix_resolution_stage4(occurrence_id TEXT PRIMARY KEY,anchor_id TEXT,prefix_norm TEXT,previous_anchor_id TEXT,next_anchor_id TEXT,relation_support_count INTEGER,status TEXT,evidence_json TEXT);""")
 pref=collections.defaultdict(set)
 for aid,name in c.execute('select anchor_id,canonical_name from tk_identity_anchors'):
  t=norm(name).split()
  for L in range(3,min(7,len(t))+1):pref[' '.join(t[:L])].add(aid)
 unique={k:next(iter(v)) for k,v in pref.items() if len(v)==1}
 good=('provisional_anchor','strong_context','strong_graph','strong_relational','strong_relational_named','strong_secondary_alias')
 res={o:a for o,a in c.execute("select occurrence_id,anchor_id from occurrence_resolution_stage1 where status in (%s)"%(','.join('?'*len(good))),good)}
 rel={(s,t) for s,t in c.execute('select student_anchor_id,teacher_anchor_id from reported_relationships_stage1')}
 groups=collections.defaultdict(lambda:collections.defaultdict(list))
 for r in c.execute('select occurrence_id,sanad_id,branch_hint,sequence_index,atomic_index,normalized_name,occurrence_type from narrator_occurrences order by sanad_id,branch_hint,sequence_index,atomic_index'):groups[(r[1],r[2])][r[3]].append(r)
 promoted=[]
 for _,seqs in groups.items():
  order=sorted(seqs)
  for pos,seq in enumerate(order):
   if len(seqs[seq])!=1:continue
   r=seqs[seq][0];oid=r[0]
   if oid in res or r[6]!='named_candidate':continue
   nn=norm(r[5]);aid=unique.get(nn)
   if not aid:continue
   prev=nxt=None
   if pos>0 and order[pos-1]==seq-1 and len(seqs[order[pos-1]])==1:prev=res.get(seqs[order[pos-1]][0][0])
   if pos+1<len(order) and order[pos+1]==seq+1 and len(seqs[order[pos+1]])==1:nxt=res.get(seqs[order[pos+1]][0][0])
   support=int(bool(prev and (prev,aid) in rel))+int(bool(nxt and (aid,nxt) in rel))
   if support<1:continue
   ev={'prefix':nn,'previous_anchor':prev,'next_anchor':nxt,'previous_relation':bool(prev and (prev,aid) in rel),'next_relation':bool(nxt and (aid,nxt) in rel)}
   status='strong_prefix_two_sided' if support==2 else 'strong_prefix_one_sided'
   c.execute('insert into unique_prefix_resolution_stage4 values(?,?,?,?,?,?,?,?)',(oid,aid,nn,prev,nxt,support,status,json.dumps(ev,ensure_ascii=False)))
   promoted.append((oid,aid,'unique_canonical_prefix_context',6 if support==2 else 5,json.dumps(ev,ensure_ascii=False),'strong_unique_prefix'))
 c.executemany('insert or ignore into occurrence_resolution_stage1 values(?,?,?,?,?,?)',promoted);c.commit()
 print('unique prefixes',len(unique));print('new resolutions',len(promoted));print(c.execute('select status,count(*) from unique_prefix_resolution_stage4 group by status').fetchall())
if __name__=='__main__':main()
