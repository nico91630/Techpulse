import json, urllib.request, xml.etree.ElementTree as ET, datetime, email.utils, html, re
from pathlib import Path
FEEDS={
'IA':['https://www.technologyreview.com/feed/','https://www.theverge.com/rss/ai-artificial-intelligence/index.xml'],
'Smartphones':['https://www.gsmarena.com/rss-news-reviews.php3','https://www.androidauthority.com/feed/'],
'Informatique':['https://www.tomshardware.com/feeds/all','https://www.techspot.com/backend.xml'],
'Gaming':['https://www.pcgamer.com/rss/','https://www.gamespot.com/feeds/mashup/'],
'Domotique':['https://www.home-assistant.io/atom.xml','https://www.theverge.com/rss/smart-home/index.xml'],
'Électricité':['https://www.electricalengineeringportal.com/feed','https://www.pv-magazine.com/feed/'],
'Énergie':['https://www.pv-magazine.com/feed/','https://electrek.co/feed/'],
'Automatisme':['https://www.automation.com/en-us/rss','https://www.controleng.com/feed/'],
'Mobilité':['https://electrek.co/feed/','https://insideevs.com/rss/news/all/'],
'Innovation':['https://techcrunch.com/feed/','https://www.sciencedaily.com/rss/computers_math/engineering.xml'],
'Électronique':['https://www.hackster.io/news.rss','https://www.cnx-software.com/feed/'],
'Cybersécurité':['https://www.bleepingcomputer.com/feed/','https://www.securityweek.com/feed/']}
def val(e,names):
 for n in names:
  t=e.find(n)
  if t is not None and t.text: return t.text.strip()
 return ''
def clean(s): return re.sub(r'<[^>]+>',' ',html.unescape(s or '')).strip()[:320]
def parse(raw,cat,source):
 root=ET.fromstring(raw); out=[]
 for e in root.findall('.//item')+root.findall('.//{http://www.w3.org/2005/Atom}entry'):
  title=clean(val(e,['title','{http://www.w3.org/2005/Atom}title']))
  link=val(e,['link'])
  if not link:
   a=e.find('{http://www.w3.org/2005/Atom}link');link=a.attrib.get('href','') if a is not None else ''
  if not title or not link.startswith('http'):continue
  dt=val(e,['pubDate','{http://www.w3.org/2005/Atom}published','{http://www.w3.org/2005/Atom}updated'])
  try: date=email.utils.parsedate_to_datetime(dt).isoformat()
  except Exception: date=dt or datetime.datetime.now(datetime.timezone.utc).isoformat()
  out.append({'title':title,'url':link,'category':cat,'source':source,'date':date,'description':clean(val(e,['description','{http://www.w3.org/2005/Atom}summary']))})
 return out
old=[]
p=Path('articles.json')
if p.exists():
 try:old=json.loads(p.read_text()).get('articles',[])
 except Exception:pass
items=[];ok=0
for cat,urls in FEEDS.items():
 for url in urls:
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; TechpulsePersonal/1.0)'})
   with urllib.request.urlopen(req,timeout=13) as r: raw=r.read(2_000_000)
   got=parse(raw,cat,url.split('/')[2]);items+=got[:20];ok+=1
   print(cat,len(got),url)
  except Exception as ex: print('FAIL',url,str(ex)[:100])
items+=old
seen=set(); unique=[]
for a in sorted(items,key=lambda x:x.get('date',''),reverse=True):
 k=a['url'].split('?')[0]
 if k not in seen:seen.add(k);unique.append(a)
p.write_text(json.dumps({'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'successful_feeds':ok,'articles':unique[:450]},ensure_ascii=False,indent=2))
print('Total',len(unique),'successful feeds',ok)
