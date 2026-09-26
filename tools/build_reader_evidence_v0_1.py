#!/usr/bin/env python3
"""Build a compact reader-facing evidence database from the audited research DB.

No global narrator-card deduplication is performed. Cards are stored once and
sanad occurrences point to them.
"""
from __future__ import annotations
import argparse, os, sqlite3

SCHEMA = """
CREATE TABLE cards(card_ref TEXT PRIMARY KEY,card_type TEXT NOT NULL,display_name TEXT NOT NULL,source_title TEXT,source_locator TEXT,grade_category TEXT,exact_grade_text TEXT,tabaqa INTEGER,birth_year_h INTEGER,death_year_h INTEGER,biography_text TEXT,teachers_raw TEXT,students_raw TEXT,source_card_id TEXT,external_id TEXT,status TEXT NOT NULL);
CREATE TABLE critic_statements(statement_ref TEXT PRIMARY KEY,card_ref TEXT NOT NULL,critic_name TEXT,exact_statement TEXT NOT NULL,judgment_category TEXT,source_title TEXT,confidence REAL);
CREATE TABLE sanads(sanad_id TEXT PRIMARY KEY,hadith_record_id TEXT,source_file_id TEXT NOT NULL,book_title TEXT,volume INTEGER,marker_number INTEGER,page_label TEXT,sanad_raw TEXT NOT NULL,evidence_layer TEXT,boundary_method TEXT,extraction_confidence REAL,needs_review INTEGER NOT NULL);
CREATE TABLE sanad_nodes(node_ref TEXT PRIMARY KEY,sanad_id TEXT NOT NULL,branch_hint INTEGER NOT NULL,sequence_index INTEGER NOT NULL,atomic_index INTEGER NOT NULL,transmission_term TEXT,raw_name TEXT NOT NULL,normalized_name TEXT,occurrence_type TEXT NOT NULL,card_ref TEXT,resolution_status TEXT NOT NULL,needs_review INTEGER NOT NULL);
CREATE TABLE sanad_edges(edge_ref TEXT PRIMARY KEY,sanad_id TEXT NOT NULL,branch_hint INTEGER NOT NULL,from_node_ref TEXT NOT NULL,to_node_ref TEXT NOT NULL,student_card_ref TEXT,teacher_card_ref TEXT,transmission_term TEXT,relationship_support TEXT,edge_status TEXT,evidence_json TEXT);
CREATE TABLE branch_summary(sanad_id TEXT NOT NULL,branch_hint INTEGER NOT NULL,total_occurrences INTEGER,resolved_occurrences INTEGER,total_links INTEGER,resolved_links INTEGER,supported_links INTEGER,unsupported_links INTEGER,complete_card_resolution INTEGER,PRIMARY KEY(sanad_id,branch_hint));
CREATE TABLE terminal_repairs(occurrence_id TEXT PRIMARY KEY,repair_kind TEXT,hidden_narrator_text TEXT,hidden_narrator_card_ref TEXT,needs_prophet_terminal INTEGER,needs_review INTEGER,evidence_json TEXT);
CREATE INDEX idx_cards_name ON cards(display_name);
CREATE INDEX idx_crit_card ON critic_statements(card_ref);
CREATE INDEX idx_sanad_book ON sanads(book_title);
CREATE INDEX idx_nodes_sanad ON sanad_nodes(sanad_id,branch_hint,sequence_index,atomic_index);
CREATE INDEX idx_nodes_card ON sanad_nodes(card_ref);
CREATE INDEX idx_edges_sanad ON sanad_edges(sanad_id,branch_hint);
"""

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("source_db"); ap.add_argument("output_db"); a=ap.parse_args()
    if os.path.exists(a.output_db): os.remove(a.output_db)
    s=sqlite3.connect(a.source_db); d=sqlite3.connect(a.output_db)
    d.execute("PRAGMA journal_mode=OFF"); d.execute("PRAGMA synchronous=OFF"); d.executescript(SCHEMA)
    existing=s.execute("""SELECT a.anchor_id,a.canonical_name,c.tk_source_locator,c.biography_text,c.teachers_raw,c.students_raw,st.grade_category,st.ibn_hajar_summary_exact,st.tabaqa,st.best_birth_year_h,st.best_death_year_h FROM tk_identity_anchors a LEFT JOIN narrator_cards_stage1 c ON c.anchor_id=a.anchor_id LEFT JOIN narrator_card_structured_stage2 st ON st.anchor_id=a.anchor_id""").fetchall()
    d.executemany("INSERT INTO cards VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",[("A:"+aid,"existing_anchor",name,"تهذيب الكمال",loc,grade,exact,tabaqa,birth,death,bio,tr,stu,None,None,"anchored") for aid,name,loc,bio,tr,stu,grade,exact,tabaqa,birth,death in existing])
    prov=s.execute("""SELECT provisional_card_id,source_card_id,canonical_display_name,taqrib_entry_no,taqrib_page,taqrib_full_text,summary_grade_category,tabaqa,death_year_h,tahdhib_entry_id,tahdhib_biography_text,teachers_raw,students_raw,card_status FROM provisional_narrator_cards_stage5""").fetchall()
    d.executemany("INSERT INTO cards VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",[("P:"+pid,"provisional_source_card",name,"تقريب التهذيب",page,grade,full,tabaqa,None,death,bio,tr,stu,scid,None,status) for pid,scid,name,no,page,full,grade,tabaqa,death,teid,bio,tr,stu,status in prov])
    crit=[]
    for sid,aid,critic,attrib,stmt,cat,source,conf in s.execute("SELECT statement_id,anchor_id,critic_name,attribution_chain,exact_statement,judgment_category,source_title,confidence FROM narrator_critic_statements_stage2"): crit.append(("S2:"+sid,"A:"+aid,critic,stmt,cat,source,conf))
    for sid,aid,source,eid,critic,attrib,stmt,cat,conf in s.execute("SELECT statement_id,anchor_id,source_title,entry_id,critic_name,attribution_chain,exact_statement,judgment_category,confidence FROM secondary_critic_statements_stage4"): crit.append(("S4:"+sid,"A:"+aid,critic,stmt,cat,source,conf))
    d.executemany("INSERT OR IGNORE INTO critic_statements VALUES(?,?,?,?,?,?,?)",crit)
    d.executemany("INSERT INTO sanads VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",s.execute("""SELECT sc.sanad_id,sc.hadith_record_id,sc.source_file_id,sf.book_title,sf.volume,hr.marker_number,hr.page_label,sc.sanad_raw,sc.evidence_layer,sc.boundary_method,sc.confidence,sc.needs_review FROM sanad_candidates sc JOIN source_files sf ON sf.source_file_id=sc.source_file_id LEFT JOIN hadith_records hr ON hr.hadith_record_id=sc.hadith_record_id""").fetchall())
    omap={oid:(("A:" if ct=="existing_anchor" else "P:")+cid,status) for oid,ct,cid,display,grade,status in s.execute("SELECT occurrence_id,card_type,card_id,display_name,grade_category,resolution_status FROM occurrence_card_map_stage6 WHERE card_type IN ('existing_anchor','provisional_source_card')")}
    nodes=[]
    for oid,sid,seq,ai,branch,term,raw,norm,typ,review in s.execute("SELECT occurrence_id,sanad_id,sequence_index,atomic_index,branch_hint,transmission_term,raw_atomic_name,normalized_name,occurrence_type,needs_review FROM narrator_occurrences"):
        cref,status=omap.get(oid,(None,"unresolved")); nodes.append((oid,sid,branch,seq,ai,term,raw,norm,typ,cref,status,review))
    d.executemany("INSERT INTO sanad_nodes VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",nodes)
    edges=[]
    for eid,sid,branch,foid,toid,sct,scid,tct,tcid,term,support,status,ev in s.execute("SELECT edge_id,sanad_id,branch_hint,from_occurrence_id,to_occurrence_id,student_card_type,student_card_id,teacher_card_type,teacher_card_id,transmission_term,relationship_support,edge_status,evidence_json FROM card_first_edges_stage6"):
        scr=(("A:" if sct=="existing_anchor" else "P:")+scid) if scid else None; tcr=(("A:" if tct=="existing_anchor" else "P:")+tcid) if tcid else None
        edges.append((eid,sid,branch,foid,toid,scr,tcr,term,support,status,ev))
    d.executemany("INSERT INTO sanad_edges VALUES(?,?,?,?,?,?,?,?,?,?,?)",edges)
    d.executemany("INSERT INTO branch_summary VALUES(?,?,?,?,?,?,?,?,?)",s.execute("SELECT sanad_id,branch_hint,total_occurrences,resolved_occurrences,total_links,resolved_links,supported_links,unsupported_links,complete_card_resolution FROM card_first_branch_summary_stage6").fetchall())
    tr={r[0]:r for r in s.execute("SELECT terminal_occurrence_id,hidden_name_raw,hidden_name_clean,source_card_id,output_card_type,output_card_id,previous_card_type,previous_card_id,score,status,evidence_json FROM terminal_hidden_narrator_resolutions_stage6")}
    rep=[]
    for oid,raw,kind,hidden,hnorm,needp,review in s.execute("SELECT occurrence_id,raw_text,repair_kind,hidden_narrator_text,hidden_narrator_norm,needs_prophet_terminal,needs_review FROM prophet_terminal_repair_stage6"):
        x=tr.get(oid); cref=ev=None
        if x: cref=(("A:" if x[4]=="existing_anchor" else "P:")+x[5]); ev=x[10]
        rep.append((oid,kind,hidden,cref,needp,review,ev))
    d.executemany("INSERT INTO terminal_repairs VALUES(?,?,?,?,?,?,?)",rep)
    d.commit(); d.execute("ANALYZE"); d.execute("VACUUM"); d.commit()
    print("quick_check:",d.execute("PRAGMA quick_check").fetchone()[0])

if __name__=="__main__": main()
