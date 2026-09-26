#!/usr/bin/env python3
"""Index selected secondary rijal books by page and attach conservative candidate page evidence to current narrator cards."""
from __future__ import annotations
import argparse,collections,hashlib,re,sqlite3
from pathlib import Path
from bs4 import BeautifulSoup
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]');ZW=re.compile(r'[\u200c\u200d\u200e\u200f]')
def norm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
 return re.sub(r'\s+',' ',ZW.sub('',s)).strip()
def key(name):
 t=[x for x in norm(name).split() if x not in {'ع','خ','م','د','ت','س','ق','بخ','4'}]
 if len(t)>=5:return ' '.join(t[:5])
 if len(t)>=4:return ' '.join(t[:4])
 if len(t)>=3:return ' '.join(t[:3])
 return None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('db');ap.add_argument('core_sources',type=Path);a=ap.parse_args();c=sqlite3.connect(a.db)
 mem=sqlite3.connect(':memory:');mem.executescript("""CREATE TABLE pages(page_id TEXT PRIMARY KEY,source_title TEXT,file_name TEXT,page_label TEXT,text_raw TEXT,text_norm TEXT);CREATE VIRTUAL TABLE page_fts USING fts5(page_id UNINDEXED,source_title UNINDEXED,text_norm,tokenize='unicode61');""")
 for folder in [p for p in a.core_sources.iterdir() if p.is_dir()]:
  for path in sorted(folder.glob('*.htm')):
   soup=BeautifulSoup(path.read_text('utf-8'),'lxml')
   for i,div in enumerate(soup.select('div.PageText'),1):
    ph=div.select_one('.PageHead');page=ph.get_text(' ',strip=True) if ph else str(i)
    if ph:ph.extract()
    for fn in div.select('.footnote'):fn.extract()
    raw=re.sub(r'\s+',' ',div.get_text(' ',strip=True));pid='P_'+hashlib.blake2b(f'{folder.name}|{path.name}|{page}|{i}'.encode(),digest_size=12).hexdigest()
    mem.execute('insert into pages values(?,?,?,?,?,?)',(pid,folder.name,path.name,page,raw,norm(raw)));mem.execute('insert into page_fts values(?,?,?)',(pid,folder.name,norm(raw)))
 mem.commit()
 c.executescript("""DROP TABLE IF EXISTS secondary_source_page_evidence_stage2;CREATE TABLE secondary_source_page_evidence_stage2(evidence_id TEXT PRIMARY KEY,anchor_id TEXT NOT NULL,source_title TEXT NOT NULL,file_name TEXT NOT NULL,page_label TEXT NOT NULL,matched_name_key TEXT NOT NULL,context_snippet TEXT NOT NULL,evidence_status TEXT NOT NULL,confidence REAL NOT NULL);CREATE INDEX idx_secondary_anchor ON secondary_source_page_evidence_stage2(anchor_id,source_title);""")
 for aid,name in c.execute('select anchor_id,canonical_name from narrator_cards_stage1').fetchall():
  k=key(name)
  if not k:continue
  rows=mem.execute('select p.source_title,p.file_name,p.page_label,p.text_raw,p.page_id from page_fts f join pages p on p.page_id=f.page_id where page_fts match ? limit 40',('"'+k+'"',)).fetchall()
  by=collections.defaultdict(list)
  for r in rows:by[r[0]].append(r)
  for st,arr in by.items():
   for r in arr[:2]:
    raw=r[3];first=name.split()[0].strip();pos=raw.find(first);pos=max(0,pos)
    snip=raw[max(0,pos-350):pos+1200];eid='SE2_'+hashlib.blake2b(f'{aid}|{st}|{r[4]}'.encode(),digest_size=12).hexdigest()
    c.execute('insert or ignore into secondary_source_page_evidence_stage2 values(?,?,?,?,?,?,?,?,?)',(eid,aid,st,r[1],r[2],k,snip,'candidate_page_match',.70))
 c.commit()
if __name__=='__main__':main()
