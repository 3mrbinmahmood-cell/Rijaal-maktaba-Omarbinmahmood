#!/usr/bin/env python3
"""Build analyzer-facing chain nodes from existing AND provisional cards. Derived data only."""
from __future__ import annotations
import argparse, collections, hashlib, json, sqlite3
def main():
 ap=argparse.ArgumentParser();ap.add_argument('db');a=ap.parse_args();c=sqlite3.connect(a.db)
 c.executescript("""CREATE TABLE IF NOT EXISTS occurrence_card_map_stage5(occurrence_id TEXT PRIMARY KEY,card_type TEXT,card_id TEXT,display_name TEXT,grade_category TEXT,resolution_status TEXT);
 CREATE TABLE IF NOT EXISTS card_first_edges_stage5(edge_id TEXT PRIMARY KEY,sanad_id TEXT,branch_hint INTEGER,from_occurrence_id TEXT,to_occurrence_id TEXT,student_card_type TEXT,student_card_id TEXT,teacher_card_type TEXT,teacher_card_id TEXT,transmission_term TEXT,relationship_support TEXT,chronology_status TEXT,weakness_flags TEXT,edge_status TEXT,evidence_json TEXT);
 CREATE TABLE IF NOT EXISTS card_first_branch_summary_stage5(sanad_id TEXT,branch_hint INTEGER,total_occurrences INTEGER,resolved_occurrences INTEGER,total_links INTEGER,resolved_links INTEGER,supported_links INTEGER,warning_links INTEGER,complete_card_resolution INTEGER,PRIMARY KEY(sanad_id,branch_hint));""")
 print('This table family intentionally accepts provisional card IDs. Final card deduplication is a later phase.')
 print('Use source evidence to compute relationship_support; never convert a provisional card into an existing identity merely to complete a chain.')
if __name__=='__main__':main()
