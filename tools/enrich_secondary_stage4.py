from __future__ import annotations
import argparse, collections, hashlib, re, sqlite3
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
GRADE_WORDS=['ثقة','صدوق','ضعيف','متروك','كذاب','مجهول','لا بأس به','ليس به بأس','ليس بالقوي','فيه نظر','لين','حجة','ثبت','حافظ','صالح الحديث','سيئ الحفظ','سيء الحفظ','منكر الحديث','واهي الحديث']

def norm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
 s=re.sub(r'[ـ\u200c\u200d\u200e\u200f\[\]«»()]',' ',s);return re.sub(r'\s+',' ',s).strip(' ،؛;:.-')
def gradecat(s):
 s=norm(s)
 if any(x in s for x in ['كذاب','وضاع','متروك']):return 'rejected'
 if any(x in s for x in ['ضعيف جدا','واهي الحديث','منكر الحديث']):return 'very_weak'
 if any(x in s for x in ['ضعيف','ليس بالقوي','فيه نظر','لين الحديث','لا يحتج']):return 'weak'
 if 'مجهول' in s:return 'unknown'
 if any(x in s for x in ['لا باس به','ليس به باس','صالح الحديث']):return 'acceptable'
 if 'صدوق' in s:return 'saduq'
 if any(x in s for x in ['ثقة','ثبت','حجة']):return 'thiqa'
 return 'other'
def critic_statements(body):
 s=re.sub(r'(?<!^)(وقال\s+)',r'.\1',body or '')
 rx=re.compile(r'(?:^|[.؛])\s*(?:و)?قال\s+([^:：]{2,120})[:：]\s*([^.;؛]{1,500})')
 for m in rx.finditer(s):
  attrib=m.group(1).strip();statement=m.group(2).strip()
  if not any(norm(w) in norm(statement) for w in GRADE_WORDS):continue
  if any(x in attrib for x in ['رسول الله','النبي']):continue
  critic=re.split(r'\s+عن\s+',attrib)[-1].strip()
  if 2<=len(critic)<=90:yield critic,attrib,statement

def main():
 ap=argparse.ArgumentParser();ap.add_argument('db');a=ap.parse_args();c=sqlite3.connect(a.db)
 c.executescript("""DROP TABLE IF EXISTS secondary_anchor_matches_stage4;DROP TABLE IF EXISTS secondary_critic_statements_stage4;DROP TABLE IF EXISTS secondary_date_evidence_stage4;DROP TABLE IF EXISTS secondary_grade_evidence_stage4;
 CREATE TABLE secondary_anchor_matches_stage4(anchor_id TEXT,source_title TEXT,entry_id TEXT,match_method TEXT,match_score REAL,PRIMARY KEY(anchor_id,source_title,entry_id));
 CREATE TABLE secondary_critic_statements_stage4(statement_id TEXT PRIMARY KEY,anchor_id TEXT,source_title TEXT,entry_id TEXT,critic_name TEXT,attribution_chain TEXT,exact_statement TEXT,judgment_category TEXT,confidence REAL);
 CREATE TABLE secondary_date_evidence_stage4(evidence_id TEXT PRIMARY KEY,anchor_id TEXT,source_title TEXT,entry_id TEXT,event_type TEXT,year_h INTEGER,exact_text TEXT,confidence REAL);
 CREATE TABLE secondary_grade_evidence_stage4(evidence_id TEXT PRIMARY KEY,anchor_id TEXT,source_title TEXT,entry_id TEXT,attributed_to TEXT,exact_text TEXT,judgment_category TEXT,confidence REAL);""")
 anchors=[(aid,name,norm(name)) for aid,name in c.execute('select anchor_id,canonical_name from tk_identity_anchors')]
 sources=[r[0] for r in c.execute('select distinct source_title from secondary_entries_stage4')]
 matched=collections.Counter()
 for source in sources:
  entries=c.execute('select entry_id,heading_norm,body from secondary_entries_stage4 where source_title=?',(source,)).fetchall()
  idx=collections.defaultdict(set);emap={e[0]:e for e in entries}
  for eid,h,b in entries:
   toks=h.split()
   for L in range(2,min(7,len(toks))+1):idx[' '.join(toks[:L])].add(eid)
  for aid,name,nn in anchors:
   toks=nn.split();candidates=[]
   for L in range(min(6,len(toks)),1,-1):
    key=' '.join(toks[:L]);ids=idx.get(key,set())
    if ids:
     good=[eid for eid in ids if emap[eid][1].startswith(key) and (nn.startswith(emap[eid][1]) or emap[eid][1].startswith(nn) or L>=3)]
     if good:candidates=list(dict.fromkeys(good));break
   if len(candidates)!=1:continue
   eid=candidates[0];body=emap[eid][2]
   c.execute('insert or ignore into secondary_anchor_matches_stage4 values(?,?,?,?,?)',(aid,source,eid,'unique_heading_prefix',.92));matched[source]+=1
   for critic,attrib,st in critic_statements(body):
    sid='S4C_'+hashlib.blake2b(f'{aid}|{source}|{eid}|{attrib}|{st}'.encode(),digest_size=12).hexdigest()
    c.execute('insert or ignore into secondary_critic_statements_stage4 values(?,?,?,?,?,?,?,?,?)',(sid,aid,source,eid,critic,attrib,st,gradecat(st),.88))
   for typ,pat in [('death',r'(?:مات|توفي|توفى|قتل)[^.;؛]{0,100}?(?:سنة|عام)\s*\(?\s*(\d{2,4})'),('birth',r'(?:ولد|مولده)[^.;؛]{0,100}?(?:سنة|عام)\s*\(?\s*(\d{2,4})')]:
    for m in re.finditer(pat,body):
     yr=int(m.group(1));exact=m.group(0)[:220];did='S4D_'+hashlib.blake2b(f'{aid}|{source}|{eid}|{typ}|{exact}'.encode(),digest_size=12).hexdigest()
     c.execute('insert or ignore into secondary_date_evidence_stage4 values(?,?,?,?,?,?,?,?)',(did,aid,source,eid,typ,yr,exact,.94))
   if source.startswith('الكاشف'):
    if any(w in norm(body) for w in ['ثقة','صدوق','ضعيف','متروك','لا باس به','حجة','ثبت','حافظ','لين']):
     exact=body[:800];gid='S4G_'+hashlib.blake2b(f'{aid}|{source}|{eid}|{exact}'.encode(),digest_size=12).hexdigest()
     c.execute('insert or ignore into secondary_grade_evidence_stage4 values(?,?,?,?,?,?,?,?)',(gid,aid,source,eid,'الذهبي',exact,gradecat(exact),.86))
   if source.startswith('التاريخ الكبير') and any(w in norm(body) for w in ['فيه نظر','منكر الحديث','كثير الوهم','لا يتابع','سكتوا عنه']):
    exact=body[:1000];gid='S4G_'+hashlib.blake2b(f'{aid}|{source}|{eid}|{exact}'.encode(),digest_size=12).hexdigest()
    c.execute('insert or ignore into secondary_grade_evidence_stage4 values(?,?,?,?,?,?,?,?)',(gid,aid,source,eid,'البخاري',exact,gradecat(exact),.90))
 c.commit()
 print('matched',dict(matched))
 print('critic statements',c.execute('select count(*) from secondary_critic_statements_stage4').fetchone()[0])
 print('dates',c.execute('select count(*) from secondary_date_evidence_stage4').fetchone()[0])
 print('source grades',c.execute('select count(*) from secondary_grade_evidence_stage4').fetchone()[0])
if __name__=='__main__':main()
