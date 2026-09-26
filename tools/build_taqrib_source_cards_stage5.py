#!/usr/bin/env python3
"""Build the Stage-5 Taqrib source-card universe. This creates cards before identity deduplication."""
from __future__ import annotations
import argparse, hashlib, re, sqlite3
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
MARK=re.compile(r'^\s*[\u200c\u200d\u200e\u200f]*(\d{1,5})\s*-\s*$')
GRADE=re.compile(r'\s+(?=(?:ثقة|صدوق|ضعيف|مقبول|مجهول|متروك|كذاب|لين|صحابي|صحابية|مستور|لا بأس به|ليس به بأس|سيئ الحفظ|سيء الحفظ|حافظ|إمام|امام|فقيه|صالح الحديث|رمي ب|اتهم ب|من الطبقة|مات سنة))')

def norm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
 s=re.sub(r'[ـ\u200c\u200d\u200e\u200f\[\]«»()]',' ',s);s=re.sub(r'\s+',' ',s).strip(' ،؛;:.-')
 return ' '.join('ابو' if x in ('ابي','أبي','أبو') else x for x in s.split())

def parse(path:Path):
 soup=BeautifulSoup(path.read_text('utf-8'),'lxml');out=[];cur=None
 for div in soup.select('div.PageText'):
  ph=div.select_one('.PageHead');page=ph.get_text(' ',strip=True) if ph else ''
  for el in div.descendants:
   if isinstance(el,Tag) and el.name=='span' and 'punct' in el.get('class',[]):
    if el.find_parent('div',class_='footnote') or el.find_parent('sup'):continue
    m=MARK.match(el.get_text(' ',strip=True))
    if m:
     if cur:cur['text']=' '.join(cur.pop('parts')).strip();out.append(cur)
     cur={'no':int(m.group(1)),'page':page,'parts':[]};continue
   if cur and isinstance(el,NavigableString):
    if el.find_parent('div',class_='footnote') or el.find_parent('div',class_='PageHead') or el.find_parent('span',class_='punct'):continue
    x=str(el).strip()
    if x:cur['parts'].append(x)
 if cur:cur['text']=' '.join(cur.pop('parts')).strip();out.append(cur)
 return out

def identity(text):
 x=re.sub(r'^\s*\d+\s*-\s*','',text).strip();m=GRADE.search(x)
 return (x[:m.start()] if m else x)[:600].strip()

def aliases(identity_text):
 n=norm(identity_text);t=n.split();out={(n,'identity')}
 if t:out.add((t[0],'first_name'))
 for i,x in enumerate(t):
  if x in ('ابو','ام') and i+1<len(t):
   out.add((' '.join(t[i:i+2]),'embedded_kunya'))
   for L in range(3,min(6,len(t)-i+1)):
    seg=' '.join(t[i:i+L])
    if ' بن ' in ' '+seg+' ':out.add((seg,'embedded_kunya_lineage'))
  if x=='بن' and i+1<len(t):out.add(('بن '+t[i+1],'embedded_ibn_alias'))
 for L in range(2,min(6,len(t))+1):out.add((' '.join(t[:L]),'name_prefix'))
 return {(a,k) for a,k in out if len(a)>=2}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('db',type=Path);ap.add_argument('taqrib_html',type=Path);a=ap.parse_args()
 c=sqlite3.connect(a.db)
 c.executescript("""DROP TABLE IF EXISTS source_cards_stage5;DROP TABLE IF EXISTS source_card_aliases_stage5;
 CREATE TABLE source_cards_stage5(card_id TEXT PRIMARY KEY,source_title TEXT,source_entry_no INTEGER,source_page TEXT,identity_text TEXT,identity_norm TEXT,full_text TEXT,card_status TEXT);
 CREATE TABLE source_card_aliases_stage5(alias_id TEXT PRIMARY KEY,card_id TEXT,alias_norm TEXT,alias_type TEXT,source_title TEXT);
 CREATE INDEX idx_sc5_norm ON source_cards_stage5(identity_norm);CREATE INDEX idx_sca5_norm ON source_card_aliases_stage5(alias_norm);""")
 for e in parse(a.taqrib_html):
  ident=identity(e['text']);cid='TQ_'+hashlib.blake2b(f"{e['no']}|{e['page']}|{e['text'][:300]}".encode(),digest_size=12).hexdigest()
  c.execute('insert into source_cards_stage5 values(?,?,?,?,?,?,?,?)',(cid,'تقريب التهذيب',e['no'],e['page'],ident,norm(ident),e['text'],'source_card'))
  for al,typ in aliases(ident):
   aid='TQA_'+hashlib.blake2b(f'{cid}|{al}|{typ}'.encode(),digest_size=10).hexdigest();c.execute('insert or ignore into source_card_aliases_stage5 values(?,?,?,?,?)',(aid,cid,al,typ,'تقريب التهذيب'))
 c.commit();print('cards',c.execute('select count(*) from source_cards_stage5').fetchone()[0]);print('aliases',c.execute('select count(*) from source_card_aliases_stage5').fetchone()[0])
if __name__=='__main__':main()
