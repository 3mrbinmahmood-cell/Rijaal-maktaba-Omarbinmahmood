#!/usr/bin/env python3
"""Refine raw sanad mentions into atomic narrator occurrences without identity merging."""
import argparse, hashlib, re, sqlite3
AR_DIAC=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
RELATIONAL={'ابي','ابيه','ابيها','ابوه','ابوها','عمه','عمهما','جده','امه','اخيه','رجل','شيخ'}
NAME_START=r'(?:أبو|أبي|ابو|ابي|ابن|عبد|محمد|احمد|أحمد|يحي|يحيى|زهير|قتيبة|اسحاق|إسحاق|عثمان|عمرو|سعيد|سفيان|شعبة|حماد|هشام|مالك|نافع|عروة|علقمة|عبيد|الحارث|سليمان|موسي|موسى|خالد|جرير|وكيع|الليث|يونس|ايوب|أيوب|ابراهيم|إبراهيم|منصور|عكرمة|عطاء|انس|أنس|عائشة|جابر|معمر|ثابت|سالم|يزيد|علي|على|الزهري|الاعمش|الأعمش|قتادة|الاوزاعي|الأوزاعي|الشعبي|الأعرج|الحسن|الضحاك|مجاهد|طاوس|مسروق)'
def norm(s):
 s=AR_DIAC.sub('',s).replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
 s=re.sub(r'[ـ\u200c\u200d\u200e\u200f]','',s); return re.sub(r'\s+',' ',s).strip(' ،؛;:.()-')
def strip_notes(s):
 s=s.strip()
 s=re.sub(r'\s*\((?:قال|قَالَ|واللفظ|وَاللَّفْظ|لفظه|قالا|قَالَا).*$', '', s)
 s=re.sub(r'\s*[\-–—]\s*(?:واللفظ|وَاللَّفْظ|اللفظ).*$', '', s)
 s=re.sub(r'\s+(?:واللفظ|وَاللَّفْظ|اللفظ)\s+.*$', '', s)
 s=re.sub(r'\s+(?:قالوا|قَالُوا|جميعا|جَمِيعًا|جميعهم)\.?\s*$', '', s)
 s=re.sub(r'\s+(?:قراءة عليه(?: وانا اسمع)?|قِرَاءَةً عَلَيْهِ(?: وَأَنَا أَسْمَعُ)?)\s*$', '', s)
 s=re.sub(r'\s+(?:وانا اسمع|وَأَنَا أَسْمَعُ|نحوه|نَحْوَهُ|قال|قَالَ|قالا|قَالَا)\s*$', '', s)
 return s.strip(' ،؛;:.()-')
def split_atomic(s):
 s=strip_notes(s); out=[]
 for ch in [x.strip() for x in re.split(r'[،,]',s) if x.strip()]:
  for p in re.split(r'\s+و(?='+NAME_START+r'\b)',ch):
   p=strip_notes(p); p=re.sub(r'^و(?=[اأإآء-ي])','',p).strip()
   if p: out.append(p)
 return out or ([s] if s else [])
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('db'); a=ap.parse_args()
 c=sqlite3.connect(a.db)
 c.executescript("""DROP TABLE IF EXISTS narrator_occurrences;
 CREATE TABLE narrator_occurrences(occurrence_id TEXT PRIMARY KEY,mention_id TEXT NOT NULL,sanad_id TEXT NOT NULL,sequence_index INTEGER NOT NULL,atomic_index INTEGER NOT NULL,branch_hint INTEGER NOT NULL,transmission_term TEXT NOT NULL,raw_atomic_name TEXT NOT NULL,normalized_name TEXT NOT NULL,occurrence_type TEXT NOT NULL,needs_review INTEGER NOT NULL DEFAULT 0);
 CREATE INDEX idx_occ_norm ON narrator_occurrences(normalized_name);
 CREATE INDEX idx_occ_sanad ON narrator_occurrences(sanad_id,sequence_index,atomic_index);""")
 rows=c.execute('select mention_id,sanad_id,sequence_index,branch_hint,transmission_term,raw_name,mention_type from narrator_mentions_raw order by sanad_id,sequence_index')
 ct=0
 for mid,sid,seq,branch,term,raw,mtype in rows:
  parts=split_atomic(raw) if mtype=='named_candidate' else [raw]
  for ai,p in enumerate(parts,1):
   n=norm(p)
   if not n: continue
   typ='relational_or_unknown' if n in RELATIONAL else mtype
   review=int(typ!='named_candidate' or len(n)<3 or len(n)>90 or '(' in p or ':' in p)
   oid='O_'+hashlib.blake2b(f'{mid}\x1f{ai}\x1f{p}'.encode(),digest_size=12).hexdigest()
   c.execute('insert into narrator_occurrences values(?,?,?,?,?,?,?,?,?,?,?)',(oid,mid,sid,seq,ai,branch,term,p,n,typ,review)); ct+=1
 c.commit()
 print('occurrences',ct)
 print('distinct named strings',c.execute("select count(distinct normalized_name) from narrator_occurrences where occurrence_type='named_candidate'").fetchone()[0])
if __name__=='__main__': main()
