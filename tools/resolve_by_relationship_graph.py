#!/usr/bin/env python3
"""Resolve ambiguous occurrences only when both adjacent resolved narrators fit the reported relationship graph."""
import argparse,collections,json,sqlite3
def main():
    ap=argparse.ArgumentParser();ap.add_argument('db');a=ap.parse_args();c=sqlite3.connect(a.db)
    anchors={r[0]:(r[1],r[2].replace('ابن','بن')) for r in c.execute('select anchor_id,canonical_name,canonical_norm from tk_identity_anchors')}
    cand=collections.defaultdict(set)
    for aid,(_,nn) in anchors.items():
        t=nn.split()
        for L in range(1,min(5,len(t))+1):cand[' '.join(t[:L])].add(aid)
    rels={(s,t) for s,t in c.execute('select student_anchor_id,teacher_anchor_id from reported_relationships_stage1')}
    groups=collections.defaultdict(lambda:collections.defaultdict(list))
    for r in c.execute('select occurrence_id,sanad_id,branch_hint,sequence_index,atomic_index,normalized_name,occurrence_type from narrator_occurrences order by sanad_id,branch_hint,sequence_index,atomic_index'):
        groups[(r[1],r[2])][r[3]].append(r)
    for passno in range(1,8):
        resolved={r[0]:r[1] for r in c.execute("select occurrence_id,anchor_id from occurrence_resolution_stage1 where status in ('provisional_anchor','strong_context','strong_graph')")}
        changes=0
        for _,seqs in groups.items():
            order=sorted(seqs)
            for pos,seq in enumerate(order):
                if len(seqs[seq])!=1:continue
                r=seqs[seq][0];oid=r[0]
                if oid in resolved or r[6]!='named_candidate':continue
                candidates=cand.get(r[5].replace('ابن','بن'),set())
                if not candidates or len(candidates)>100:continue
                prev=nxt=None
                if pos>0 and order[pos-1]==seq-1 and len(seqs[order[pos-1]])==1:prev=resolved.get(seqs[order[pos-1]][0][0])
                if pos+1<len(order) and order[pos+1]==seq+1 and len(seqs[order[pos+1]])==1:nxt=resolved.get(seqs[order[pos+1]][0][0])
                if not(prev and nxt):continue
                hits=[x for x in candidates if (prev,x) in rels and (x,nxt) in rels]
                if len(hits)!=1:continue
                an=hits[0];ev=json.dumps({'raw_name':r[5],'previous_anchor':prev,'next_anchor':nxt,'candidate_count':len(candidates),'rule':'prev_is_student_and_next_is_teacher'},ensure_ascii=False)
                old=c.execute('select status from occurrence_resolution_stage1 where occurrence_id=?',(oid,)).fetchone()
                if old and old[0]=='candidate_only':
                    c.execute("update occurrence_resolution_stage1 set anchor_id=?,resolution_method='reported_graph_two_sided',score=7,evidence_json=?,status='strong_graph' where occurrence_id=?",(an,ev,oid));changes+=1
                elif not old:
                    c.execute('insert into occurrence_resolution_stage1 values(?,?,?,?,?,?)',(oid,an,'reported_graph_two_sided',7,ev,'strong_graph'));changes+=1
        c.commit();print('pass',passno,'changes',changes)
        if not changes:break
if __name__=='__main__':main()
