from __future__ import annotations
import argparse, hashlib, re, sqlite3
from pathlib import Path
from bs4 import BeautifulSoup, Tag, NavigableString

AR=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
NUMHYPH=re.compile(r'^\s*[\u200c\u200d\u200e\u200f]*(\d{1,6})\s*-\s*$')
EXCLUDE=('باب','حرف','فصل','القسم','مقدمة','من اسمه','ذكر من','الكنى','النساء','دراسة','جوانب')

def norm(s):
    s=AR.sub('',s or '').replace('ٱ','ا').replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ابن','بن')
    s=re.sub(r'[ـ\u200c\u200d\u200e\u200f\[\]«»()]',' ',s)
    return re.sub(r'\s+',' ',s).strip(' ،؛;:.-')

def title_person(raw, source):
    t=re.sub(r'\s+',' ',raw).strip(' \u200c\u200f\u200e،؛;:.')
    if not t:return None
    if source.startswith('التاريخ الكبير'):
        m=re.match(r'^\[(\d+)\]\s*(.+)$',t)
        return (int(m.group(1)),m.group(2).strip()) if m else None
    if source.startswith('الإصابة'):
        m=re.match(r'^(\d+)\s*(?:ز\s*)?-?\s*(.+)$',t)
        return (int(m.group(1)),m.group(2).strip()) if m else None
    if source.startswith('تهذيب التهذيب'):
        nt=norm(t)
        if any(nt.startswith(norm(x)) for x in EXCLUDE):return None
        if len(nt)<5 or len(nt)>220:return None
        if ' بن ' not in ' '+nt+' ' and not nt.startswith(('ابو ','ابي ','ام ')):return None
        return None,t
    return None

def extract_title_entries(source_dir,source):
    entries=[];cur=None
    for path in sorted(source_dir.glob('*.htm')):
        soup=BeautifulSoup(path.read_text('utf-8'),'lxml')
        for div in soup.select('div.PageText'):
            page=div.select_one('.PageNumber');page=page.get_text(' ',strip=True) if page else ''
            for el in div.descendants:
                if isinstance(el,Tag) and (el.get('data-type')=='title' or 'title' in el.get('class',[])):
                    parsed=title_person(el.get_text(' ',strip=True),source)
                    if parsed:
                        if cur:cur['body']=' '.join(cur.pop('parts')).strip();entries.append(cur)
                        no,name=parsed;cur={'entry_no':no,'heading':name,'page':page,'file':path.name,'parts':[name]};continue
                if cur and isinstance(el,NavigableString):
                    if el.find_parent('div',class_='footnote') or el.find_parent('div',class_='PageHead'):continue
                    if el.find_parent('span',attrs={'data-type':'title'}) or el.find_parent('span',class_='title'):continue
                    x=str(el).strip()
                    if x:cur['parts'].append(x)
    if cur:cur['body']=' '.join(cur.pop('parts')).strip();entries.append(cur)
    return entries

def extract_numeric_entries(source_dir,source):
    entries=[];cur=None
    for path in sorted(source_dir.glob('*.htm')):
        soup=BeautifulSoup(path.read_text('utf-8'),'lxml')
        for div in soup.select('div.PageText'):
            page=div.select_one('.PageNumber');page=page.get_text(' ',strip=True) if page else ''
            for el in div.descendants:
                if isinstance(el,Tag) and el.name=='span' and 'punct' in el.get('class',[]):
                    if el.find_parent('div',class_='footnote') or el.find_parent('sup'):continue
                    m=NUMHYPH.match(el.get_text(' ',strip=True))
                    if m:
                        if cur:cur['body']=' '.join(cur.pop('parts')).strip();entries.append(cur)
                        cur={'entry_no':int(m.group(1)),'heading':'','page':page,'file':path.name,'parts':[]};continue
                if cur and isinstance(el,NavigableString):
                    if el.find_parent('div',class_='footnote') or el.find_parent('div',class_='PageHead') or el.find_parent('span',class_='punct'):continue
                    x=str(el).strip()
                    if x:cur['parts'].append(x)
    if cur:cur['body']=' '.join(cur.pop('parts')).strip();entries.append(cur)
    out=[]
    for e in entries:
        h=re.split(r'[،,:؛;.]',e['body'],maxsplit=1)[0].strip();nh=norm(h)
        if len(nh)<4 or len(nh)>220:continue
        if any(nh.startswith(norm(x)) for x in EXCLUDE):continue
        if not (' بن ' in ' '+nh+' ' or nh.startswith(('ابو ','ابي ','ام '))):continue
        e['heading']=h;out.append(e)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('db');ap.add_argument('root',type=Path);a=ap.parse_args();c=sqlite3.connect(a.db)
    c.executescript("""DROP TABLE IF EXISTS secondary_entries_stage4;
    CREATE TABLE secondary_entries_stage4(entry_id TEXT PRIMARY KEY,source_title TEXT,file_name TEXT,page_label TEXT,entry_no INTEGER,heading TEXT,heading_norm TEXT,body TEXT);
    CREATE INDEX idx_sec4_norm ON secondary_entries_stage4(source_title,heading_norm);""")
    specs=[('تهذيب التهذيب - ط الرسالة','title'),('التاريخ الكبير للبخاري - ت الدباسي والنحال','title'),('الإصابة في تمييز الصحابة','title'),('الكاشف في معرفة من له رواية في الكتب الستة','numeric'),('ميزان الاعتدال','numeric')]
    for source,kind in specs:
        es=extract_title_entries(a.root/source,source) if kind=='title' else extract_numeric_entries(a.root/source,source)
        for e in es:
            eid='SE4_'+hashlib.blake2b(f"{source}|{e['file']}|{e['page']}|{e['entry_no']}|{e['heading']}".encode(),digest_size=12).hexdigest()
            c.execute('insert or ignore into secondary_entries_stage4 values(?,?,?,?,?,?,?,?)',(eid,source,e['file'],e['page'],e['entry_no'],e['heading'],norm(e['heading']),e['body']))
        print(source,len(es));c.commit()
if __name__=='__main__':main()
