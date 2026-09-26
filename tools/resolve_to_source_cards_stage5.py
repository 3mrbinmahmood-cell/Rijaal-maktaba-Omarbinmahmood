#!/usr/bin/env python3
"""Resolve unresolved sanad occurrences to source cards using exact chain context. No card deduplication."""
from __future__ import annotations
import argparse, collections, json, re, sqlite3
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def norm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
 s=re.sub(r'[ـ\u200c\u200d\u200e\u200f\[\]«»()]',' ',s);s=re.sub(r'\s+',' ',s).strip(' ،؛;:.-')
 return ' '.join('ابو' if x in ('ابي','أبي','أبو') else x for x in s.split())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('db');a=ap.parse_args();c=sqlite3.connect(a.db)
 good=('provisional_anchor','strong_context','strong_graph','strong_relational','strong_relational_named','strong_secondary_alias','strong_unique_prefix','strong_source_card')
 resolved={o:a for o,a in c.execute("select occurrence_id,anchor_id from occurrence_resolution_stage1 where status in (%s)"%(','.join('?'*len(good))),good)}
 names={a:norm(n) for a,n in c.execute('select anchor_id,canonical_name from tk_identity_anchors')};keys=collections.defaultdict(set)
 for a,n in names.items():
  t=n.split()
  for L in range(2,min(6,len(t))+1):keys[a].add(' '.join(t[:L]))
 for a,x in c.execute('select anchor_id,alias_norm from narrator_aliases_stage4'):keys[a].add(norm(x))
 aliases=collections.defaultdict(set)
 for card,x in c.execute('select card_id,alias_norm from source_card_aliases_stage5'):aliases[x].add(card)
 rel={card:(norm(t),norm(s)) for card,t,s in c.execute('select card_id,teachers_raw,students_raw from source_card_relationship_text_stage5')}
 card_anchor={card:a for card,a in c.execute('select card_id,anchor_id from source_card_anchor_links_stage5')}
 def has(a,text):return bool(a and text and any(k in text for k in keys.get(a,()) if len(k)>=3))
 groups=collections.defaultdict(lambda:collections.defaultdict(list))
 for r in c.execute('select occurrence_id,sanad_id,branch_hint,sequence_index,atomic_index,normalized_name,occurrence_type from narrator_occurrences order by sanad_id,branch_hint,sequence_index,atomic_index'):
  groups[(r[1],r[2])][r[3]].append(r)
 c.executescript("""DROP TABLE IF EXISTS occurrence_source_card_candidates_stage5;DROP TABLE IF EXISTS occurrence_source_card_resolutions_stage5;
 CREATE TABLE occurrence_source_card_candidates_stage5(occurrence_id TEXT,card_id TEXT,alias_norm TEXT,previous_anchor_id TEXT,next_anchor_id TEXT,previous_in_students INTEGER,next_in_teachers INTEGER,score REAL,status TEXT,evidence_json TEXT,PRIMARY KEY(occurrence_id,card_id));
 CREATE TABLE occurrence_source_card_resolutions_stage5(occurrence_id TEXT PRIMARY KEY,card_id TEXT,existing_anchor_id TEXT,resolution_method TEXT,score REAL,status TEXT,evidence_json TEXT);""")
 cand=[];out=[]
 for _,seqs in groups.items():
  order=sorted(seqs)
  for pos,seq in enumerate(order):
   if len(seqs[seq])!=1:continue
   r=seqs[seq][0];oid=r[0]
   if oid in resolved or r[6]!='named_candidate':continue
   alias=norm(r[5]);cards=aliases.get(alias,set())
   if not cards or len(cards)>80:continue
   prev=nxt=None
   if pos>0 and order[pos-1]==seq-1 and len(seqs[order[pos-1]])==1:prev=resolved.get(seqs[order[pos-1]][0][0])
   if pos+1<len(order) and order[pos+1]==seq+1 and len(seqs[order[pos+1]])==1:nxt=resolved.get(seqs[order[pos+1]][0][0])
   if not prev and not nxt:continue
   scored=[]
   for card in cards:
    tr,st=rel.get(card,('',''));ps=int(has(prev,st));ns=int(has(nxt,tr));score=2+3*ps+3*ns
    ev={'alias':alias,'candidate_count':len(cards),'previous_anchor':prev,'next_anchor':nxt,'previous_in_students':bool(ps),'next_in_teachers':bool(ns)}
    cand.append((oid,card,alias,prev,nxt,ps,ns,score,'two_sided' if ps and ns else 'one_sided' if ps or ns else 'alias_only',json.dumps(ev,ensure_ascii=False)));scored.append((score,ps+ns,card,ev))
   scored.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True);best=scored[0]
   if best[1]<1 or sum(x[0]==best[0] for x in scored)!=1:continue
   out.append((oid,best[2],card_anchor.get(best[2]),'source_card_context',best[0],'resolved_unique_best_context_card',json.dumps(best[3],ensure_ascii=False)))
 c.executemany('insert or ignore into occurrence_source_card_candidates_stage5 values(?,?,?,?,?,?,?,?,?,?)',cand);c.executemany('insert into occurrence_source_card_resolutions_stage5 values(?,?,?,?,?,?,?)',out);c.commit()
 print('candidate rows',len(cand));print('resolved occurrences',len(out));print('Do not merge cards here. Unlinked source cards remain provisional identities.')
if __name__=='__main__':main()
