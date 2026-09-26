import sqlite3,re,collections,hashlib,json
DB='data/rijaal_work.sqlite';c=sqlite3.connect(DB)
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def norm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
 s=re.sub(r'[ـ\u200c\u200d\u200e\u200f\[\]«»()]',' ',s);s=re.sub(r'\s+',' ',s).strip(' ،؛;:.-')
 return ' '.join('ابو' if x in ('ابي','أبي','أبو') else x for x in s.split())
def grade(s):
 x=norm(s)
 if any(w in x for w in ['كذاب','وضاع','متروك']):return 'rejected'
 if any(w in x for w in ['ضعيف جدا','واهي الحديث','منكر الحديث']):return 'very_weak'
 if any(w in x for w in ['ضعيف','ليس بالقوي','فيه نظر','لين الحديث']):return 'weak'
 if 'مجهول' in x:return 'unknown'
 if 'مقبول' in x:return 'acceptable'
 if 'صدوق' in x:return 'saduq'
 if any(w in x for w in ['ثقة','ثبت','حجة']):return 'thiqa'
 if 'صحابي' in x or 'صحابية' in x:return 'companion'
 return None
c.executescript("""DROP TABLE IF EXISTS occurrence_card_map_stage6;
CREATE TABLE occurrence_card_map_stage6 AS SELECT * FROM occurrence_card_map_stage5;
CREATE UNIQUE INDEX idx_ocm6_oid ON occurrence_card_map_stage6(occurrence_id);
DROP TABLE IF EXISTS occurrence_direct_card_seed_stage6;
CREATE TABLE occurrence_direct_card_seed_stage6(occurrence_id TEXT PRIMARY KEY,card_id TEXT,existing_anchor_id TEXT,raw_name TEXT,resolution_method TEXT,evidence_json TEXT);""")
idx=collections.defaultdict(set);carddata={}
for card,no,page,ident,full in c.execute('select card_id,source_entry_no,source_page,identity_text,full_text from source_cards_stage5'):
 carddata[card]=(no,page,ident,full);t=norm(ident).split()
 for L in range(3,min(8,len(t))+1):idx[' '.join(t[:L])].add(card)
unique={k:next(iter(v)) for k,v in idx.items() if len(v)==1}
anchor={card:a for card,a in c.execute('select card_id,anchor_id from source_card_anchor_links_stage5')}
prov={s:p for p,s in c.execute('select provisional_card_id,source_card_id from provisional_narrator_cards_stage5')}
rel={card:(t,s,eid) for card,t,s,eid in c.execute('select card_id,teachers_raw,students_raw,relationship_source_entry_id from source_card_relationship_text_stage5')}
newcards={};added=0
for oid,raw in c.execute("""select o.occurrence_id,o.normalized_name from narrator_occurrences o left join occurrence_card_map_stage6 m on m.occurrence_id=o.occurrence_id where m.occurrence_id is null and o.occurrence_type='named_candidate'""").fetchall():
 rr=norm(raw)
 if len(rr.split())<3 or rr not in unique:continue
 card=unique[rr];ev=json.dumps({'raw':rr,'rule':'unique_3plus_token_prefix_across_all_taqrib_cards'},ensure_ascii=False)
 c.execute('insert into occurrence_direct_card_seed_stage6 values(?,?,?,?,?,?)',(oid,card,anchor.get(card),raw,'unique_source_card_prefix',ev))
 if card in anchor:
  aid=anchor[card];name=c.execute('select canonical_name from tk_identity_anchors where anchor_id=?',(aid,)).fetchone()[0]
  g=c.execute('select grade_category from narrator_card_structured_stage2 where anchor_id=?',(aid,)).fetchone();g=g[0] if g else None
  c.execute('insert into occurrence_card_map_stage6 values(?,?,?,?,?,?)',(oid,'existing_anchor',aid,name,g,'stage6_unique_source_prefix'))
 else:
  pid=prov.get(card)
  if not pid:
   pid='P6_'+hashlib.blake2b(card.encode(),digest_size=10).hexdigest();prov[card]=pid;newcards[card]=pid
  no,page,ident,full=carddata[card]
  c.execute('insert into occurrence_card_map_stage6 values(?,?,?,?,?,?)',(oid,'provisional_source_card',pid,ident,grade(full),'stage6_unique_source_prefix'))
 added+=1
for card,pid in newcards.items():
 no,page,ident,full=carddata[card];t,s,eid=rel.get(card,('','',None));bio=''
 if eid:
  r=c.execute('select body from secondary_entries_stage4 where entry_id=?',(eid,)).fetchone();bio=r[0] if r else ''
 c.execute('insert into provisional_narrator_cards_stage5 values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(pid,card,ident,no,page,full,grade(full),None,None,eid,bio,t,s,0,'stage6_source_card'))
c.commit()
print('direct source-card seeds',added)
