#!/usr/bin/env python3
"""Stage-2 card enrichment: structured Ibn Hajar grade/tabaqah, dates, traits, and critic statements."""
from __future__ import annotations
import argparse, collections, hashlib, re, sqlite3
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def nrm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
 return re.sub(r'\s+',' ',s).strip()
ONES={'صفر':0,'واحد':1,'واحدة':1,'احد':1,'احدى':1,'اثنان':2,'اثنين':2,'اثنتان':2,'اثنتين':2,'اثنتي':2,'اثنتا':2,'ثلاث':3,'ثلاثة':3,'اربع':4,'اربعة':4,'خمس':5,'خمسة':5,'ست':6,'ستة':6,'سبع':7,'سبعة':7,'ثمان':8,'ثماني':8,'ثمانية':8,'تسع':9,'تسعة':9}
TENS={'عشرون':20,'عشرين':20,'ثلاثون':30,'ثلاثين':30,'اربعون':40,'اربعين':40,'خمسون':50,'خمسين':50,'ستون':60,'ستين':60,'سبعون':70,'سبعين':70,'ثمانون':80,'ثمانين':80,'تسعون':90,'تسعين':90}
HUND={'مئة':100,'مائة':100,'مئه':100,'مائتين':200,'مئتين':200,'مائتان':200,'مئتان':200,'ثلاثمئة':300,'ثلاثمائة':300,'اربعمئة':400,'اربعمائة':400,'خمسمئة':500,'خمسمائة':500}
ORD={'الاولى':1,'الاول':1,'الثانية':2,'الثاني':2,'الثالثة':3,'الثالث':3,'الرابعة':4,'الرابع':4,'الخامسة':5,'الخامس':5,'السادسة':6,'السادس':6,'السابعة':7,'السابع':7,'الثامنة':8,'الثامن':8,'التاسعة':9,'التاسع':9,'العاشرة':10,'العاشر':10,'الحادية عشرة':11,'الحادي عشر':11,'الثانية عشرة':12,'الثاني عشر':12}
GRADE_TERMS=['ثقة','ضعيف','صدوق','حجة','ثبت','لا بأس به','ليس به بأس','متروك','كذاب','مجهول','لين','صالح الحديث','سيئ الحفظ','سيء الحفظ','ليس بالقوي','ليس بقوي','لا يحتج','حافظ','امام']
def arabic_num(p):
 toks=[]
 for t in nrm(p).replace('سنة','').strip(' ،؛.').split():
  if t.startswith('و') and len(t)>1 and t[1:] in set(ONES)|set(TENS)|set(HUND)|{'عشر','عشرة'}:t=t[1:]
  toks.append(t)
 total=rec=0
 for t in toks:
  if t in ONES:total+=ONES[t];rec+=1
  elif t in TENS:total+=TENS[t];rec+=1
  elif t in HUND:total+=HUND[t];rec+=1
  elif t in ('عشر','عشرة'):total+=10;rec+=1
 return total if rec and rec>=max(1,len(toks)-1) else None
def parse_tabaqa(s):
 s=nrm(s);pat='|'.join(map(re.escape,sorted(ORD,key=len,reverse=True)))
 m=re.search(r'(?:من\s+(?:رؤوس\s+)?(?:الطبقة\s+)?|الطبقة\s+)('+pat+r')',s)
 return ORD.get(m.group(1)) if m else None
def parse_summary(s):
 s=nrm(s);cat=None
 pats=[('matruk_kadhdhab',['كذاب','وضاع','متروك']),('very_weak',['ضعيف جدا','واهي الحديث','منكر الحديث','ساقط']),('weak',[' ضعيف ','لين الحديث',' لين ']),('unknown',['مجهول الحال',' مجهول ','مستور']),('acceptable',[' مقبول ']),('saduq',[' صدوق ']),('thiqa',[' ثقة ']),('companion',[' صحابي ','له صحبة'])]
 padded=' '+s+' '
 for c,ps in pats:
  if any(x in padded for x in ps):cat=c;break
 flags={'tadlis':int('دلس' in s or 'مدلس' in s),'ikhtilat':int('اختلط' in s or 'اختلاط' in s),'late_memory_change':int(any(x in s for x in ['تغير حفظه','تغير باخره','تغير باخرة'])),'poor_memory':int(any(x in s for x in ['سيء الحفظ','سئ الحفظ','سيئ الحفظ']))}
 return cat,parse_tabaqa(s),flags
def dates(bio):
 s=nrm(bio);out=[]
 for typ,pat in [('birth',r'(?:ولد(?:ت)?|مولده)[^،؛.]{0,120}?\sسنة\s+([^،؛.\]\[]+)'),('death',r'(?:مات|توفي|توفى)[^،؛.]{0,120}?\sسنة\s+([^،؛.\]\[]+)')]:
  for m in re.finditer(pat,s):
   phrase=re.split(r'\s+(?:وهو|وله|وكان|ودفن|عن|قال)\b',m.group(1).strip(),maxsplit=1)[0]
   val=arabic_num(phrase);out.append((typ,val,m.group(0)[:240],.92 if val is not None else .55))
 return out
def judgment_cat(s):
 s=nrm(s)
 if any(x in s for x in ['كذاب','وضاع','متروك']):return 'rejected'
 if any(x in s for x in ['ليس بثقة','ليس ثقة','لا يكتب حديثه','لا يحتج به','ليس بالقوي','ليس بقوي','منكر الحديث','واهي الحديث']):return 'weak'
 if 'ضعيف' in s or 'لين الحديث' in s:return 'weak'
 if 'مجهول' in s:return 'unknown'
 if 'لا بأس به' in s or 'ليس به بأس' in s:return 'acceptable'
 if 'صدوق' in s:return 'saduq'
 if 'ثقة' in s or 'ثبت' in s or 'حجة' in s:return 'thiqa'
 if 'صالح الحديث' in s:return 'acceptable'
 if 'حافظ' in s or 'امام' in s:return 'praise'
 return 'other'
def critic_statements(bio):
 s=re.sub(r'(?<!^)(وقال\s+)',r'.\1',nrm(bio))
 rx=re.compile(r'(?:^|[.؛])\s*(?:و)?قال\s+([^:：]{2,120})[:：]\s*([^.;؛]{1,500})')
 for m in rx.finditer(s):
  attrib=m.group(1).strip();statement=m.group(2).strip()
  if not any(t in statement for t in GRADE_TERMS):continue
  if any(x in attrib for x in ['رسول الله','النبي','الرجل','بعض الفقهاء','موضع اخر','موضع آخر']):continue
  critic=re.split(r'\s+عن\s+',attrib)[-1].strip()
  if 2<=len(critic)<=80:yield critic,attrib,statement
def main():
 ap=argparse.ArgumentParser();ap.add_argument('db');a=ap.parse_args();c=sqlite3.connect(a.db)
 c.executescript("""DROP TABLE IF EXISTS narrator_card_structured_stage2;DROP TABLE IF EXISTS narrator_date_evidence_stage2;DROP TABLE IF EXISTS narrator_trait_evidence_stage2;DROP TABLE IF EXISTS narrator_critic_statements_stage2;
 CREATE TABLE narrator_card_structured_stage2(anchor_id TEXT PRIMARY KEY,canonical_name TEXT NOT NULL,grade_category TEXT,ibn_hajar_summary_exact TEXT,tabaqa INTEGER,has_tadlis INTEGER NOT NULL,has_ikhtilat INTEGER NOT NULL,has_late_memory_change INTEGER NOT NULL,has_poor_memory INTEGER NOT NULL,best_birth_year_h INTEGER,best_death_year_h INTEGER,structured_status TEXT NOT NULL);
 CREATE TABLE narrator_date_evidence_stage2(date_evidence_id TEXT PRIMARY KEY,anchor_id TEXT,event_type TEXT,year_h INTEGER,exact_text TEXT,source_title TEXT,confidence REAL);
 CREATE TABLE narrator_trait_evidence_stage2(trait_evidence_id TEXT PRIMARY KEY,anchor_id TEXT,trait_type TEXT,exact_text TEXT,source_title TEXT,confidence REAL);
 CREATE TABLE narrator_critic_statements_stage2(statement_id TEXT PRIMARY KEY,anchor_id TEXT,critic_name TEXT,attribution_chain TEXT,exact_statement TEXT,judgment_category TEXT,source_title TEXT,confidence REAL);""")
 for aid,name,bio,summary in c.execute('select anchor_id,canonical_name,biography_text,ibn_hajar_summary_text from narrator_cards_stage1').fetchall():
  cat,tabaqa,flags=parse_summary(summary or '');ds=dates(bio or '')
  for typ,val,exact,conf in ds:
   did='D2_'+hashlib.blake2b(f'{aid}|{typ}|{exact}'.encode(),digest_size=12).hexdigest();c.execute('insert or ignore into narrator_date_evidence_stage2 values(?,?,?,?,?,?,?)',(did,aid,typ,val,exact,'تهذيب الكمال',conf))
  for trait in [k for k,v in flags.items() if v]:
   tid='T2_'+hashlib.blake2b(f'{aid}|{trait}|{summary}'.encode(),digest_size=12).hexdigest();c.execute('insert or ignore into narrator_trait_evidence_stage2 values(?,?,?,?,?,?)',(tid,aid,trait,summary or '','تقريب التهذيب',.95))
  births=[x[1] for x in ds if x[0]=='birth' and x[1] is not None];deaths=[x[1] for x in ds if x[0]=='death' and x[1] is not None]
  bb=collections.Counter(births).most_common(1)[0][0] if births else None;bd=deaths[-1] if deaths else None
  c.execute('insert into narrator_card_structured_stage2 values(?,?,?,?,?,?,?,?,?,?,?,?)',(aid,name,cat,summary,tabaqa,flags['tadlis'],flags['ikhtilat'],flags['late_memory_change'],flags['poor_memory'],bb,bd,'structured_taqrib' if summary else 'no_taqrib_summary'))
  for critic,attrib,statement in critic_statements(bio or ''):
   sid='CS2_'+hashlib.blake2b(f'{aid}|{attrib}|{statement}'.encode(),digest_size=12).hexdigest();c.execute('insert or ignore into narrator_critic_statements_stage2 values(?,?,?,?,?,?,?,?)',(sid,aid,critic,attrib,statement,judgment_cat(statement),'تهذيب الكمال',.82))
 c.commit()
if __name__=='__main__':main()
