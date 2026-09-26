#!/usr/bin/env python3
"""Use the earlier 664k-entry source index only as candidate evidence; never auto-merge identities."""
import argparse, collections, re, sqlite3
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def norm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
 s=re.sub(r'[ـ\u200c\u200d\u200e\u200f]','',s); return re.sub(r'\s+',' ',s).strip(' ،؛;:.()-')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('phase_db'); ap.add_argument('legacy_full_name_index'); a=ap.parse_args()
 p=sqlite3.connect(a.phase_db); old=sqlite3.connect(a.legacy_full_name_index)
 idx=collections.defaultdict(list)
 for eid,label,cls,bid,sid,pid in old.execute('select entry_id,name_label,classification,book_id,source_id,opening_page_id from name_entries'):
  n=norm(label)
  if n: idx[n].append((eid,label,cls,bid,sid,pid))
 p.executescript("""DROP TABLE IF EXISTS legacy_exact_name_matches;
 CREATE TABLE legacy_exact_name_matches(normalized_name TEXT NOT NULL,legacy_entry_id TEXT NOT NULL,legacy_name_label TEXT NOT NULL,classification TEXT NOT NULL,legacy_book_id TEXT NOT NULL,legacy_source_id TEXT NOT NULL,legacy_opening_page_id TEXT NOT NULL,candidate_count_for_name INTEGER NOT NULL,PRIMARY KEY(normalized_name,legacy_entry_id));
 CREATE INDEX idx_legacy_exact_norm ON legacy_exact_name_matches(normalized_name);""")
 names=[r[0] for r in p.execute("select distinct normalized_name from narrator_occurrences where occurrence_type='named_candidate'")]
 matched=unique=amb=0
 for n in names:
  rows=idx.get(n,[])
  if not rows: continue
  matched+=1; unique+=len(rows)==1; amb+=len(rows)>1
  for row in rows: p.execute('insert into legacy_exact_name_matches values(?,?,?,?,?,?,?,?)',(n,*row,len(rows)))
 p.commit()
 print('distinct current strings',len(names)); print('matched',matched); print('single legacy entry',unique); print('ambiguous legacy labels',amb)
 print('These are candidates only; no identity merge is performed.')
if __name__=='__main__': main()
