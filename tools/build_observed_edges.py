#!/usr/bin/env python3
"""Build raw observed narrator-to-narrator edge evidence from atomic sanad occurrences."""
import argparse, hashlib, sqlite3
from collections import defaultdict
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('db'); a=ap.parse_args()
 c=sqlite3.connect(a.db)
 c.executescript("""DROP TABLE IF EXISTS observed_edge_evidence_raw; DROP TABLE IF EXISTS observed_edges_raw;
 CREATE TABLE observed_edges_raw(edge_id TEXT PRIMARY KEY,from_normalized_name TEXT NOT NULL,to_normalized_name TEXT NOT NULL,from_type TEXT NOT NULL,to_type TEXT NOT NULL,transmission_term_to TEXT NOT NULL,evidence_count INTEGER NOT NULL,distinct_sanad_count INTEGER NOT NULL,distinct_source_file_count INTEGER NOT NULL,needs_review INTEGER NOT NULL DEFAULT 0,UNIQUE(from_normalized_name,to_normalized_name,from_type,to_type,transmission_term_to));
 CREATE TABLE observed_edge_evidence_raw(edge_id TEXT NOT NULL REFERENCES observed_edges_raw(edge_id),sanad_id TEXT NOT NULL REFERENCES sanad_candidates(sanad_id),source_file_id TEXT NOT NULL REFERENCES source_files(source_file_id),hadith_record_id TEXT,from_occurrence_id TEXT NOT NULL REFERENCES narrator_occurrences(occurrence_id),to_occurrence_id TEXT NOT NULL REFERENCES narrator_occurrences(occurrence_id),PRIMARY KEY(edge_id,sanad_id,from_occurrence_id,to_occurrence_id));
 CREATE INDEX idx_edge_from ON observed_edges_raw(from_normalized_name); CREATE INDEX idx_edge_to ON observed_edges_raw(to_normalized_name);""")
 rows=c.execute("""select o.occurrence_id,o.sanad_id,o.sequence_index,o.atomic_index,o.branch_hint,o.transmission_term,o.normalized_name,o.occurrence_type,s.source_file_id,s.hadith_record_id from narrator_occurrences o join sanad_candidates s on s.sanad_id=o.sanad_id order by o.sanad_id,o.branch_hint,o.sequence_index,o.atomic_index""")
 chains=defaultdict(lambda:defaultdict(list)); meta={}
 for oid,sid,seq,ai,branch,term,name,typ,sfid,hid in rows:
  chains[(sid,branch)][seq].append((oid,name,typ,term)); meta[sid]=(sfid,hid)
 agg={}; evidence=[]
 for (sid,branch),seqs in chains.items():
  ordered=sorted(seqs)
  for x,y in zip(ordered,ordered[1:]):
   if y!=x+1: continue
   for foid,fname,ftype,fterm in seqs[x]:
    for toid,tname,ttype,tterm in seqs[y]:
     if fname==tname and ftype=='named_candidate': continue
     key=(fname,tname,ftype,ttype,tterm)
     eid='E_'+hashlib.blake2b('\x1f'.join(key).encode(),digest_size=12).hexdigest()
     z=agg.setdefault(key,{'eid':eid,'sanads':set(),'files':set(),'n':0,'review':0})
     z['sanads'].add(sid); z['files'].add(meta[sid][0]); z['n']+=1
     if ftype!='named_candidate' or ttype!='named_candidate': z['review']=1
     evidence.append((eid,sid,meta[sid][0],meta[sid][1],foid,toid))
 for key,z in agg.items():
  c.execute('insert into observed_edges_raw values(?,?,?,?,?,?,?,?,?,?)',(z['eid'],*key,z['n'],len(z['sanads']),len(z['files']),z['review']))
 c.executemany('insert or ignore into observed_edge_evidence_raw values(?,?,?,?,?,?)',evidence); c.commit()
 print('raw edge patterns',len(agg)); print('evidence rows',c.execute('select count(*) from observed_edge_evidence_raw').fetchone()[0])
if __name__=='__main__': main()
