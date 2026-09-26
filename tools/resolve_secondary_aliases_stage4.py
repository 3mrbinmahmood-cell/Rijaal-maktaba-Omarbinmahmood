from __future__ import annotations
import argparse, collections, hashlib, json, re, sqlite3
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def norm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
 s=re.sub(r'[ـ\u200c\u200d\u200e\u200f\[\]«»()]',' ',s);return re.sub(r'\s+',' ',s).strip(' ،؛;:.-')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('db');a=ap.parse_args();c=sqlite3.connect(a.db)
 c.executescript("""DROP TABLE IF EXISTS narrator_aliases_stage4;DROP TABLE IF EXISTS secondary_alias_resolution_stage4;
 CREATE TABLE narrator_aliases_stage4(alias_id TEXT PRIMARY KEY,anchor_id TEXT,alias_text TEXT,alias_norm TEXT,alias_type TEXT,source_title TEXT,source_entry_id TEXT);
 CREATE INDEX idx_alias4_norm ON narrator_aliases_stage4(alias_norm);
 CREATE TABLE secondary_alias_resolution_stage4(occurrence_id TEXT PRIMARY KEY,anchor_id TEXT,alias_norm TEXT,previous_anchor_id TEXT,next_anchor_id TEXT,relation_support_count INTEGER,status TEXT,evidence_json TEXT);""")
 for aid,name in c.execute('select anchor_id,canonical_name from tk_identity_anchors'):
  nn=norm(name);x='AL4_'+hashlib.blake2b(f'{aid}|canonical|{nn}'.encode(),digest_size=10).hexdigest();c.execute('insert or ignore into narrator_aliases_stage4 values(?,?,?,?,?,?,?)',(x,aid,name,nn,'canonical','تهذيب الكمال',None))
 for aid,source,eid in c.execute("select anchor_id,source_title,entry_id from secondary_anchor_matches_stage4 where source_title in ('تهذيب التهذيب - ط الرسالة','التاريخ الكبير للبخاري - ت الدباسي والنحال','الإصابة في تمييز الصحابة')"):
  row=c.execute('select heading from secondary_entries_stage4 where entry_id=?',(eid,)).fetchone()
  if not row:continue
  txt=row[0];nn=norm(txt)
  if len(nn.split())<2:continue
  x='AL4_'+hashlib.blake2b(f'{aid}|{source}|{eid}|{nn}'.encode(),digest_size=10).hexdigest();c.execute('insert or ignore into narrator_aliases_stage4 values(?,?,?,?,?,?,?)',(x,aid,txt,nn,'source_heading',source,eid))
 c.commit()
 unique={}
 for n,count,aid in c.execute('select alias_norm,count(distinct anchor_id),min(anchor_id) from narrator_aliases_stage4 group by alias_norm'):
  if count==1 and len(n.split())>=2:unique[n]=aid
 good=('provisional_anchor','strong_context','strong_graph','strong_relational','strong_relational_named')
 res={o:a for o,a in c.execute("select occurrence_id,anchor_id from occurrence_resolution_stage1 where status in (%s)"%(','.join('?'*len(good))),good)}
 rel={(s,t) for s,t in c.execute('select student_anchor_id,teacher_anchor_id from reported_relationships_stage1')}
 groups=collections.defaultdict(lambda:collections.defaultdict(list))
 for r in c.execute('select occurrence_id,sanad_id,branch_hint,sequence_index,atomic_index,normalized_name,occurrence_type from narrator_occurrences order by sanad_id,branch_hint,sequence_index,atomic_index'):
  groups[(r[1],r[2])][r[3]].append(r)
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
   ev={'alias':nn,'previous_anchor':prev,'next_anchor':nxt,'previous_relation':bool(prev and (prev,aid) in rel),'next_relation':bool(nxt and (aid,nxt) in rel)}
   status='strong_alias_two_sided' if support==2 else 'strong_alias_one_sided'
   c.execute('insert or replace into secondary_alias_resolution_stage4 values(?,?,?,?,?,?,?,?)',(oid,aid,nn,prev,nxt,support,status,json.dumps(ev,ensure_ascii=False)))
   promoted.append((oid,aid,'secondary_unique_alias_context',6 if support==2 else 5,json.dumps(ev,ensure_ascii=False),'strong_secondary_alias'))
 c.executemany('insert or ignore into occurrence_resolution_stage1 values(?,?,?,?,?,?)',promoted);c.commit()
 print('unique aliases',len(unique));print('new resolutions',len(promoted));print(c.execute('select status,count(*) from secondary_alias_resolution_stage4 group by status').fetchall())
if __name__=='__main__':main()
