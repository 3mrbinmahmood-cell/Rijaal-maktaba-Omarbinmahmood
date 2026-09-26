#!/usr/bin/env python3
"""Stage-5 conservative card-first resolver. Resolve occurrences to cards; do not deduplicate cards."""
from __future__ import annotations
import argparse, collections, json, re, sqlite3

AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def norm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
 s=re.sub(r'[ـ\u200c\u200d\u200e\u200f\[\]«»()]',' ',s);s=re.sub(r'\s+',' ',s).strip(' ،؛;:.-')
 return ' '.join('ابو' if x in ('ابي','أبي','أبو') else x for x in s.split())

def extract(text,start,endings):
 m=re.search(start,text,re.I)
 if not m:return ''
 st=m.end();end=len(text)
 for pat in endings:
  x=re.search(pat,text[st:],re.I)
  if x:end=min(end,st+x.start())
 return text[st:end].strip()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('db');a=ap.parse_args();c=sqlite3.connect(a.db)
 # Link Taqrib cards to existing anchors using the previously audited Taqrib entry number.
 c.executescript("""DROP TABLE IF EXISTS source_card_anchor_links_stage5;DROP TABLE IF EXISTS source_card_secondary_links_stage5;DROP TABLE IF EXISTS source_card_relationship_text_stage5;
 CREATE TABLE source_card_anchor_links_stage5(card_id TEXT PRIMARY KEY,anchor_id TEXT,link_method TEXT,confidence REAL);
 CREATE TABLE source_card_secondary_links_stage5(card_id TEXT,source_title TEXT,entry_id TEXT,link_method TEXT,confidence REAL,PRIMARY KEY(card_id,source_title,entry_id));
 CREATE TABLE source_card_relationship_text_stage5(card_id TEXT PRIMARY KEY,teachers_raw TEXT,students_raw TEXT,relationship_source_entry_id TEXT);""")
 for aid,no in c.execute('select anchor_id,taqrib_entry_no from narrator_cards_stage1 where taqrib_entry_no is not null'):
  rows=c.execute('select card_id from source_cards_stage5 where source_entry_no=?',(no,)).fetchall()
  if len(rows)==1:c.execute('insert or ignore into source_card_anchor_links_stage5 values(?,?,?,?)',(rows[0][0],aid,'existing_stage1_taqrib_entry_no',1.0))
 # Link to Tahdhib al-Tahdhib by unique heading prefix.
 entries=c.execute("select entry_id,heading,body from secondary_entries_stage4 where source_title='تهذيب التهذيب - ط الرسالة'").fetchall();idx=collections.defaultdict(set);emap={e[0]:e for e in entries}
 for eid,h,b in entries:
  t=norm(h).split()
  for L in range(2,min(7,len(t))+1):idx[' '.join(t[:L])].add(eid)
 for card,ident in c.execute('select card_id,identity_text from source_cards_stage5').fetchall():
  t=norm(ident).split();found=[]
  for L in range(min(6,len(t)),1,-1):
   key=' '.join(t[:L]);good=[eid for eid in idx.get(key,set()) if norm(emap[eid][1]).startswith(key)]
   if good:found=list(dict.fromkeys(good));break
  if len(found)!=1:continue
  eid=found[0];c.execute('insert into source_card_secondary_links_stage5 values(?,?,?,?,?)',(card,'تهذيب التهذيب - ط الرسالة',eid,'unique_heading_prefix',.94))
  body=emap[eid][2];student=r'(?:روى\s+عنه|روى\s+عنها|وعنه|وعنها)\s*:?' 
  teachers=extract(body,r'(?:روى|رَوَى)\s+عن\s*:?',[student,r'(?:قال|وقال|قَال|وَقَال)\s'])
  students=extract(body,student,[r'(?:قال|وقال|قَال|وَقَال)\s',r'(?:ذكره|وذكره|روى له|وروى له)'])
  c.execute('insert or replace into source_card_relationship_text_stage5 values(?,?,?,?)',(card,teachers,students,eid))
 c.commit()
 print('anchor links',c.execute('select count(*) from source_card_anchor_links_stage5').fetchone()[0])
 print('Tahdhib links',c.execute('select count(*) from source_card_secondary_links_stage5').fetchone()[0])
 print('cards with teacher/student text',c.execute("select count(*) from source_card_relationship_text_stage5 where teachers_raw<>'' or students_raw<>''").fetchone()[0])
 print('Next: score unresolved occurrences against these cards using the exact previous/next resolved narrator. A card match alone is not sufficient.')
if __name__=='__main__':main()
