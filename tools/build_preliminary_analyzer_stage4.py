from __future__ import annotations
import argparse, collections, hashlib, json, sqlite3

def main():
 ap=argparse.ArgumentParser();ap.add_argument('db');a=ap.parse_args();c=sqlite3.connect(a.db)
 c.executescript("""DROP TABLE IF EXISTS resolved_sanad_edges_stage4;DROP TABLE IF EXISTS resolved_sanad_branch_summary_stage4;
 CREATE TABLE resolved_sanad_edges_stage4(edge_id TEXT PRIMARY KEY,sanad_id TEXT,branch_hint INTEGER,from_occurrence_id TEXT,to_occurrence_id TEXT,student_anchor_id TEXT,teacher_anchor_id TEXT,transmission_term TEXT,reported_relationship_status TEXT,observed_pair_count INTEGER,chronology_status TEXT,tadlis_warning INTEGER,node_weakness_status TEXT,preliminary_continuity_status TEXT,evidence_json TEXT);
 CREATE INDEX idx_rse4_pair ON resolved_sanad_edges_stage4(student_anchor_id,teacher_anchor_id);
 CREATE TABLE resolved_sanad_branch_summary_stage4(sanad_id TEXT,branch_hint INTEGER,total_occurrences INTEGER,resolved_occurrences INTEGER,total_links INTEGER,resolved_links INTEGER,supported_links INTEGER,warning_links INTEGER,unresolved_links INTEGER,complete_identity_resolution INTEGER,PRIMARY KEY(sanad_id,branch_hint));""")
 good=('provisional_anchor','strong_context','strong_graph','strong_relational','strong_relational_named','strong_secondary_alias','strong_unique_prefix')
 res={o:a for o,a in c.execute("select occurrence_id,anchor_id from occurrence_resolution_stage1 where status in (%s)"%(','.join('?'*len(good))),good)}
 reported={(s,t):st for s,t,te,se,st in c.execute('select * from reported_relationships_stage1')}
 observed={(s,t):n for s,t,n,ds in c.execute('select student_anchor_id,teacher_anchor_id,evidence_count,distinct_sanad_count from resolved_observed_relationships_stage1')}
 cards={a:(g,t,b,d,td,ik,late,poor) for a,g,t,b,d,td,ik,late,poor in c.execute('select anchor_id,grade_category,tabaqa,best_birth_year_h,best_death_year_h,has_tadlis,has_ikhtilat,has_late_memory_change,has_poor_memory from narrator_card_structured_stage2')}
 groups=collections.defaultdict(lambda:collections.defaultdict(list))
 for r in c.execute('select occurrence_id,sanad_id,branch_hint,sequence_index,atomic_index,transmission_term,normalized_name,occurrence_type from narrator_occurrences order by sanad_id,branch_hint,sequence_index,atomic_index'):
  groups[(r[1],r[2])][r[3]].append(r)
 for (sid,branch),seqs in groups.items():
  order=sorted(seqs);total_occ=sum(len(seqs[x]) for x in order);resolved_occ=sum(1 for x in order for r in seqs[x] if r[0] in res)
  total_links=max(0,len(order)-1);resolved_links=supported=warnings=unresolved=0
  for x,y in zip(order,order[1:]):
   if y!=x+1 or len(seqs[x])!=1 or len(seqs[y])!=1: unresolved+=1;continue
   fr,tr=seqs[x][0],seqs[y][0];fa=res.get(fr[0]);ta=res.get(tr[0])
   if not(fa and ta): unresolved+=1;continue
   resolved_links+=1;rep=reported.get((fa,ta));obs=observed.get((fa,ta),0)
   fc=cards.get(fa,(None,None,None,None,0,0,0,0));tc=cards.get(ta,(None,None,None,None,0,0,0,0))
   chronology='unknown'
   if fc[2] and tc[3] and fc[2]>tc[3]: chronology='conflict_student_born_after_teacher_death'
   elif fc[1] and tc[1] and fc[1]+1 < tc[1]: chronology='possible_generation_reversal'
   elif (fc[2] or fc[3]) and (tc[2] or tc[3]): chronology='compatible_no_obvious_conflict'
   term=(tr[5] or '').replace('أ','ا').replace('إ','ا')
   tad=int(bool(fc[4]) and term.strip() in ('عن','عَن','عَنْ'))
   weak=[]
   if fc[0] in ('weak','very_weak','rejected','unknown'): weak.append('student:'+str(fc[0]))
   if tc[0] in ('weak','very_weak','rejected','unknown'): weak.append('teacher:'+str(tc[0]))
   if chronology.startswith('conflict'): status='chronology_conflict'
   elif rep and not tad: status='supported_reported_and_observed'
   elif rep and tad: status='reported_but_tadlis_review'
   elif obs>=2 and not tad: status='observed_repeated_needs_reported_source'
   elif tad: status='tadlis_review'
   else: status='observed_only_needs_review'
   if status=='supported_reported_and_observed': supported+=1
   else: warnings+=1
   ev={'reported_relationship':rep,'observed_pair_count':obs,'student_grade':fc[0],'teacher_grade':tc[0],'student_tabaqa':fc[1],'teacher_tabaqa':tc[1],'student_birth':fc[2],'student_death':fc[3],'teacher_birth':tc[2],'teacher_death':tc[3]}
   eid='AE4_'+hashlib.blake2b(f'{sid}|{branch}|{fr[0]}|{tr[0]}'.encode(),digest_size=12).hexdigest()
   c.execute('insert into resolved_sanad_edges_stage4 values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(eid,sid,branch,fr[0],tr[0],fa,ta,tr[5],rep,obs,chronology,tad,';'.join(weak) if weak else 'none',status,json.dumps(ev,ensure_ascii=False)))
  c.execute('insert into resolved_sanad_branch_summary_stage4 values(?,?,?,?,?,?,?,?,?,?)',(sid,branch,total_occ,resolved_occ,total_links,resolved_links,supported,warnings,unresolved,int(total_occ>0 and total_occ==resolved_occ)))
 c.commit()
 print('edges',c.execute('select count(*) from resolved_sanad_edges_stage4').fetchone()[0])
 print('statuses',c.execute('select preliminary_continuity_status,count(*) from resolved_sanad_edges_stage4 group by preliminary_continuity_status').fetchall())
 print('complete branches',c.execute('select count(*) from resolved_sanad_branch_summary_stage4 where complete_identity_resolution=1').fetchone()[0])
if __name__=='__main__':main()
