#!/usr/bin/env python3
"""Assemble stage-1 narrator cards from Tahdhib al-Kamal + Taqrib al-Tahdhib."""
from __future__ import annotations
import argparse, collections, re, sqlite3
from pathlib import Path
from bs4 import BeautifulSoup, Tag
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
START=re.compile(r'^\s*[\u200c\u200d\u200e\u200f]*(\d{1,5})\s*-\s*$')
def norm(s):
    s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
    return re.sub(r'\s+',' ',re.sub(r'[ـ\u200c\u200d\u200e\u200f]','',s)).strip(' ،؛;:.()-')
def parse_taqrib(path):
    soup=BeautifulSoup(path.read_text('utf-8'),'lxml');entries=[];cur=None
    for div in soup.select('div.PageText'):
        ph=div.select_one('.PageHead');page=ph.get_text(' ',strip=True) if ph else ''
        for ch in div.children:
            if isinstance(ch,Tag) and ('footnote' in ch.get('class',[]) or 'PageHead' in ch.get('class',[])):continue
            if isinstance(ch,Tag) and ch.name=='span' and 'punct' in ch.get('class',[]):
                m=START.match(ch.get_text(' ',strip=True))
                if m:
                    if cur:cur['text']=' '.join(cur.pop('parts')).strip();entries.append(cur)
                    cur={'no':int(m.group(1)),'page':page,'parts':[]};continue
            if cur:
                x=ch.get_text(' ',strip=True) if isinstance(ch,Tag) else str(ch).strip()
                if x:cur['parts'].append(x)
    if cur:cur['text']=' '.join(cur.pop('parts')).strip();entries.append(cur)
    return entries
def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase_db',type=Path);ap.add_argument('core_index',type=Path);ap.add_argument('taqrib_html',type=Path);a=ap.parse_args()
    p=sqlite3.connect(a.phase_db);k=sqlite3.connect(a.core_index)
    tidx=collections.defaultdict(list)
    for e in parse_taqrib(a.taqrib_html):
        toks=norm(e['text']).split()
        for L in range(2,min(7,len(toks))+1):tidx[' '.join(toks[:L])].append(e)
    p.executescript("""DROP TABLE IF EXISTS narrator_cards_stage1;
    CREATE TABLE narrator_cards_stage1(anchor_id TEXT PRIMARY KEY,tk_entry_id TEXT NOT NULL,canonical_name TEXT NOT NULL,tk_source_locator TEXT NOT NULL,biography_text TEXT NOT NULL,teachers_raw TEXT,students_raw TEXT,taqrib_entry_no INTEGER,taqrib_page TEXT,ibn_hajar_summary_text TEXT,dates_evidence_text TEXT,card_status TEXT NOT NULL);""")
    matched=0
    for an,eid,cn in p.execute('select anchor_id,tk_entry_id,canonical_name from tk_identity_anchors'):
        row=k.execute('select volume_file,start_page,body,teachers_raw,students_raw from entries where entry_id=?',(eid,)).fetchone()
        if not row:continue
        vol,page,body,teachers,students=row;toks=norm(cn).split();found=None
        for L in range(min(6,len(toks)),1,-1):
            rr=tidx.get(' '.join(toks[:L]),[])
            if len(rr)==1:found=rr[0];break
        summary=found['text'] if found else None
        if found:matched+=1
        dates=[]
        if summary:
            for m in re.finditer(r'(?:مات|توفي|توفى|قتل)\s+.{0,180}',summary):
                piece=re.split(r'[.؛\[\]]',m.group(0),maxsplit=1)[0].strip()
                if piece and piece not in dates:dates.append(piece)
        p.execute('insert into narrator_cards_stage1 values(?,?,?,?,?,?,?,?,?,?,?,?)',
          (an,eid,cn,f'{vol} | {page}',body,teachers,students,found['no'] if found else None,found['page'] if found else None,summary,' | '.join(dates[:3]),'tk+taqrib' if found else 'tk_only'))
    p.commit()
    print('cards',p.execute('select count(*) from narrator_cards_stage1').fetchone()[0])
    print('with Taqrib summary',matched)
if __name__=='__main__':main()
