#!/usr/bin/env python3
"""Build a compact biography/teacher/student index from Tahdhib al-Kamal HTML."""
from __future__ import annotations
import argparse, hashlib, re, sqlite3
from pathlib import Path
from bs4 import BeautifulSoup, Tag

AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
START=re.compile(r'^\s*[\u200c\u200d\u200e\u200f]*(\d{1,5})\s*-\s*$')
CODE=re.compile(r'^\s*(?:[خمدتسقعربك4]+(?:\s+[خمدتسقعربك4]+)*\s*:)?\s*')

def norm(s):
    s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
    s=re.sub(r'[ـ\u200c\u200d\u200e\u200f]','',s)
    return re.sub(r'\s+',' ',s).strip(' ،؛;:.()-')

def heading(text):
    return re.split(r'(?:رَوَى|روى)\s+عَن\s*:|(?:رَوَى|روى)\s+عَ?نه\s*:',text,maxsplit=1)[0][:900].strip()

def canonical_from_heading(h):
    x=CODE.sub('',h)
    x=re.split(r'\s*\(\d+\)\s*[,،]|[,،]\s*(?:أَبُو|أبو|ابو|ويقال|وهو|مولى|له صحبة|من أهل|الكوفي|البصري|المدني|المكي|الشامي|القرشي|الثقفي|الانصاري|الأنصاري)',x,maxsplit=1)[0]
    return re.sub(r'\s*\(\d+\)\s*$','',x).strip(' ،؛;:.()-')[:400]

def extract_list(text,label,next_labels):
    m=re.search(label,text,re.I)
    if not m:return ''
    st=m.end(); end=len(text)
    for pat in next_labels:
        mm=re.search(pat,text[st:],re.I)
        if mm:end=min(end,st+mm.start())
    return text[st:end].strip()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tahdhib_dir',type=Path)
    ap.add_argument('--db',type=Path,default=Path('data/core_rijal_index.sqlite'))
    a=ap.parse_args(); a.db.parent.mkdir(parents=True,exist_ok=True)
    if a.db.exists():a.db.unlink()
    con=sqlite3.connect(a.db)
    con.executescript("""CREATE TABLE entries(entry_id TEXT PRIMARY KEY,source_title TEXT,volume_file TEXT,start_page TEXT,printed_entry_no INTEGER,heading TEXT,canonical_name TEXT,canonical_norm TEXT,body TEXT,teachers_raw TEXT,students_raw TEXT,has_teacher_list INTEGER,has_student_list INTEGER,confidence REAL);
    CREATE INDEX idx_entry_norm ON entries(canonical_norm);
    CREATE VIRTUAL TABLE entry_fts USING fts5(entry_id UNINDEXED,canonical_name,heading,body,tokenize='unicode61');""")
    entries=[]; cur=None
    for path in sorted(a.tahdhib_dir.glob('*.htm')):
        soup=BeautifulSoup(path.read_text('utf-8'),'lxml')
        for div in soup.select('div.PageText'):
            ph=div.select_one('.PageHead'); page=ph.get_text(' ',strip=True) if ph else path.name
            for child in div.children:
                if isinstance(child,Tag) and ('footnote' in child.get('class',[]) or 'PageHead' in child.get('class',[])):continue
                if isinstance(child,Tag) and child.name=='span' and 'punct' in child.get('class',[]):
                    m=START.match(child.get_text(' ',strip=True))
                    if m:
                        if cur:
                            cur['body']=' '.join(cur.pop('parts')).strip(); entries.append(cur)
                        cur={'num':int(m.group(1)),'vol':path.name,'page':page,'parts':[]}
                        continue
                if cur:
                    txt=child.get_text(' ',strip=True) if isinstance(child,Tag) else str(child).strip()
                    if txt:cur['parts'].append(txt)
    if cur:
        cur['body']=' '.join(cur.pop('parts')).strip(); entries.append(cur)
    for e in entries:
        body=e['body']; h=heading(body); cn=canonical_from_heading(h)
        teachers=extract_list(body,r'(?:رَوَى|روى)\s+عَن\s*:',[r'(?:رَوَى|روى)\s+عَ?نه\s*:',r'(?:وقال|وَقَال|قال|قَال)\s'])
        students=extract_list(body,r'(?:رَوَى|روى)\s+عَ?نه\s*:',[r'(?:وقال|وَقَال|قال|قَال)\s',r'(?:ذكره|وذكره|روى له|رَوَى لَهُ)'])
        conf=.95 if teachers and students else .8 if teachers or students else .35
        eid='TK_'+hashlib.blake2b(f"{e['vol']}|{e['page']}|{e['num']}|{h}".encode(),digest_size=12).hexdigest()
        row=(eid,'تهذيب الكمال في أسماء الرجال',e['vol'],e['page'],e['num'],h,cn,norm(cn),body,teachers,students,int(bool(teachers)),int(bool(students)),conf)
        con.execute('insert into entries values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',row)
        con.execute('insert into entry_fts values(?,?,?,?)',(eid,cn,h,body))
    con.commit()
    print('entries',len(entries))
    print('high-confidence',con.execute('select count(*) from entries where confidence>=.8').fetchone()[0])

if __name__=='__main__':main()
