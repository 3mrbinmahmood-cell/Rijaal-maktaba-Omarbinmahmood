import sqlite3,re
DB='data/rijaal_work.sqlite';c=sqlite3.connect(DB)
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def norm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
 s=re.sub(r'[ـ\u200c\u200d\u200e\u200f]','',s);return re.sub(r'\s+',' ',s).strip(' ،؛;:.-')
PATS=[
 re.compile(r'\s+(?:قالت|قال|يقول|يقولون)\s*:?\s*(?:قال\s+)?(?:رسول الله|النبي)\b'),
 re.compile(r'\s+(?:سمعت|سمع)\s+(?:رسول الله|النبي)\b'),
 re.compile(r'\s+(?:ان|انه|انها)\s+(?:رسول الله|النبي)\b'),
 re.compile(r'\s+(?:يبلغ به|رفعه الي|رفعه إلى)\s+(?:رسول الله|النبي)\b'),
]
def classify(raw):
 n=norm(raw)
 if n.startswith(('رسول الله','النبي')):return 'pure_prophet',''
 for pat in PATS:
  m=pat.search(n)
  if m:
   pre=n[:m.start()].strip(' ،؛:.-')
   return ('narrator_plus_prophet',pre) if pre else ('pure_prophet','')
 if 'رسول الله' in n or 'النبي' in n:return 'narrator_descriptor_only',n
 return 'other',n
c.executescript('DROP TABLE IF EXISTS prophet_terminal_repair_stage6;CREATE TABLE prophet_terminal_repair_stage6(occurrence_id TEXT PRIMARY KEY,raw_text TEXT,repair_kind TEXT,hidden_narrator_text TEXT,hidden_narrator_norm TEXT,needs_prophet_terminal INTEGER,needs_review INTEGER);')
rows=[]
for oid,raw in c.execute("select occurrence_id,raw_atomic_name from narrator_occurrences where occurrence_type='prophet_terminal'"):
 kind,pre=classify(raw);rows.append((oid,raw,kind,pre,norm(pre),int(kind in ('pure_prophet','narrator_plus_prophet')),int(kind=='other')))
c.executemany('insert into prophet_terminal_repair_stage6 values(?,?,?,?,?,?,?)',rows);c.commit()
print(c.execute('select repair_kind,count(*) from prophet_terminal_repair_stage6 group by repair_kind').fetchall())
