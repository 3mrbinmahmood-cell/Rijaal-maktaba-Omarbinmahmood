import sqlite3,re,collections,json,hashlib
DB='data/rijaal_work.sqlite';c=sqlite3.connect(DB)
AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
def norm(s):
 s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
 s=re.sub(r'[ـ\u200c\u200d\u200e\u200f\[\]«»()]',' ',s);s=re.sub(r'\s+',' ',s).strip(' ،؛;:.-')
 return ' '.join('ابو' if x in ('ابي','أبي','أبو') else x for x in s.split())
def pname(seg):
 t=seg.split()
 if not t:return ''
 if t[0] in ('عبد','ابو','ام') and len(t)>1:return ' '.join(t[:2])
 return t[0]
def specific_keys(text):
 n=norm(text);out={n} if len(n)>=4 else set();segs=[x.strip() for x in re.split(r'\s+بن\s+',n) if x.strip()]
 if len(segs)>=2:
  a,b=pname(segs[0]),pname(segs[1])
  if a and b:out.add(a+' بن '+b)
 if len(segs)>=3:
  a,b,d=pname(segs[0]),pname(segs[1]),pname(segs[2])
  if a and b and d:out.add(a+' بن '+b+' بن '+d)
 if n.startswith(('ابو ','ام ')):
  t=n.split()
  if len(t)>=3:out.add(' '.join(t[:3]))
 return {x for x in out if len(x)>=4}
cards={}
for card,ident in c.execute('select card_id,identity_text from source_cards_stage5'):cards[card]={'ident':norm(ident),'sec':'','tr':'','st':'','anchor':None}
for card,t,s in c.execute('select card_id,teachers_raw,students_raw from source_card_relationship_text_stage5'):
 if card in cards:cards[card]['tr']=norm(t);cards[card]['st']=norm(s)
for card,a in c.execute('select card_id,anchor_id from source_card_anchor_links_stage5'):
 if card in cards:cards[card]['anchor']=a
for card,eid in c.execute("select card_id,entry_id from source_card_secondary_links_stage5 where source_title='تهذيب التهذيب - ط الرسالة'"):
 r=c.execute('select heading from secondary_entries_stage4 where entry_id=?',(eid,)).fetchone()
 if r and card in cards:cards[card]['sec']=norm(r[0])
anchor_card={d['anchor']:card for card,d in cards.items() if d['anchor']}
prov_source={p:s for p,s in c.execute('select provisional_card_id,source_card_id from provisional_narrator_cards_stage5')}
source_prov={s:p for p,s in prov_source.items()}
anchor_keys=collections.defaultdict(set);card_keys=collections.defaultdict(set)
for a,n in c.execute('select anchor_id,canonical_name from tk_identity_anchors'):anchor_keys[a]|=specific_keys(n)
for card,d in cards.items():
 card_keys[card]|=specific_keys(d['ident'])
 if d['sec']:card_keys[card]|=specific_keys(d['sec'])
for a,card in anchor_card.items():anchor_keys[a]|=card_keys[card]
def nodekeys(node):
 if not node:return set()
 return anchor_keys[node[1]] if node[0]=='A' else card_keys.get(prov_source.get(node[1],''),set())
first=collections.defaultdict(set);tok=collections.defaultdict(set);anchor_alias_cards=collections.defaultdict(set)
for card,d in cards.items():
 for text in (d['ident'],d['sec']):
  tt=text.split()
  if tt:first[tt[0]].add(card)
  for x in set(tt):
   if len(x)>=3:tok[x].add(card)
for a,x in c.execute('select anchor_id,alias_norm from narrator_aliases_stage4'):
 card=anchor_card.get(a);xx=norm(x)
 if card and len(xx.split())>=2:anchor_alias_cards[xx].add(card)
cache={}
def candidates(raw):
 if raw in cache:return cache[raw]
 rt=raw.split();pool=set(anchor_alias_cards.get(raw,set()))
 if not rt:return []
 if rt[0]=='بن' and len(rt)>1:pool|=tok.get(rt[1],set())
 else:
  pool|=first.get(rt[0],set())
  if rt[0]=='ابو' and len(rt)>1:pool|=tok.get(rt[1],set())
  if len(rt)==1:pool|=tok.get(rt[0],set())
 out=[]
 for card in pool:
  best=9 if card in anchor_alias_cards.get(raw,set()) else -1
  for text in (cards[card]['ident'],cards[card]['sec']):
   if not text:continue
   tt=text.split()
   if text==raw:s=10
   elif text.startswith(raw+' '):s=9
   else:
    pos=-1
    for i in range(len(tt)-len(rt)+1):
     if tt[i:i+len(rt)]==rt:pos=i;break
    if pos<0:continue
    if rt[0]=='بن' and pos==1:s=8
    elif pos<=1:s=7
    elif pos<=3:s=5
    else:s=2
   best=max(best,s)
  if best>=0:out.append((card,best))
 cache[raw]=out;return out
G=collections.defaultdict(lambda:collections.defaultdict(list))
for r in c.execute('select occurrence_id,sanad_id,branch_hint,sequence_index,atomic_index,normalized_name,occurrence_type from narrator_occurrences order by sanad_id,branch_hint,sequence_index,atomic_index'):
 G[(r[1],r[2])][r[3]].append(r)
occmap={oid:('A',cid) if ct=='existing_anchor' else ('P',cid) for oid,ct,cid in c.execute("select occurrence_id,card_type,card_id from occurrence_card_map_stage6 where card_type in ('existing_anchor','provisional_source_card')")}
supcache={}
def support(card,node,field):
 if not node:return 0
 k=(card,node,field)
 if k in supcache:return supcache[k]
 text=cards[card][field]
 if not text:supcache[k]=0;return 0
 v=int(any(x in text for x in nodekeys(node)));supcache[k]=v;return v
c.executescript('DROP TABLE IF EXISTS occurrence_context_resolutions_stage6_specific;CREATE TABLE occurrence_context_resolutions_stage6_specific(occurrence_id TEXT PRIMARY KEY,source_card_id TEXT,output_card_type TEXT,output_card_id TEXT,resolution_method TEXT,score REAL,pass_no INTEGER,evidence_json TEXT);')
allnew=[]
for pno in range(1,7):
 contexts=collections.defaultdict(list)
 for _,seqs in G.items():
  order=sorted(seqs)
  for pos,seq in enumerate(order):
   if len(seqs[seq])!=1:continue
   r=seqs[seq][0];oid=r[0]
   if oid in occmap or r[6]!='named_candidate':continue
   prev=nxt=None
   if pos>0 and order[pos-1]==seq-1 and len(seqs[order[pos-1]])==1:prev=occmap.get(seqs[order[pos-1]][0][0])
   if pos+1<len(order) and order[pos+1]==seq+1 and len(seqs[order[pos+1]])==1:nxt=occmap.get(seqs[order[pos+1]][0][0])
   if prev or nxt:contexts[(norm(r[5]),prev,nxt)].append(oid)
 new=[]
 for (raw,prev,nxt),oids in contexts.items():
  cs=candidates(raw)
  if not cs or len(cs)>300:continue
  scored=[]
  for card,ns in cs:
   ps=support(card,prev,'st');xs=support(card,nxt,'tr');total=ns+5*ps+5*xs
   scored.append((total,ps+xs,ns,card,ps,xs))
  scored.sort(reverse=True);best=scored[0];runner=scored[1][0] if len(scored)>1 else -99
  promote=False;method=''
  if best[1]>=2 and best[0]>=17 and best[0]>=runner+2:promote=True;method='two_sided_specific_context'
  elif best[1]>=1 and best[2]>=8 and best[0]>=13 and best[0]>=runner+3:promote=True;method='strong_name_specific_context'
  elif len(scored)==1 and best[2]>=9 and best[1]>=1:promote=True;method='unique_card_specific_context'
  if not promote:continue
  card=best[3];a=cards[card]['anchor'];pid=source_prov.get(card)
  if a:ct,cid,node='existing_anchor',a,('A',a)
  else:
   if not pid:pid='P6_'+hashlib.blake2b(card.encode(),digest_size=10).hexdigest();source_prov[card]=pid;prov_source[pid]=card
   ct,cid,node='provisional_source_card',pid,('P',pid)
  ev={'raw':raw,'candidate_count':len(cs),'previous':prev,'next':nxt,'name_score':best[2],'previous_in_students':bool(best[4]),'next_in_teachers':bool(best[5]),'runner_up_score':runner}
  for oid in oids:
   new.append((oid,card,ct,cid,method,best[0],pno,json.dumps(ev,ensure_ascii=False)));occmap[oid]=node
 if not new:break
 c.executemany('insert or ignore into occurrence_context_resolutions_stage6_specific values(?,?,?,?,?,?,?,?)',new);c.commit();allnew+=new
print('context resolutions',len(allnew))
