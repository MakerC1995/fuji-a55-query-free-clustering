from pathlib import Path
import os,sys,json,hashlib,datetime,plistlib,subprocess,time,threading
W=Path(__file__).resolve().parents[1]
D2=W.parent/'a55_d2_technology_kb'
D1=W.parent/'a55_d1_query_free_clustering'
sys.path.insert(0,str(D1/'deps'))
os.environ['PYTHONDONTWRITEBYTECODE']='1'
UUID='534D9B75-27C9-49B5-89A0-4DF7E631107C'
_device=None
_lock=threading.RLock()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def stable(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def oh(x):return hashlib.sha256(stable(x).encode()).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*2**20),b''):h.update(b)
 return h.hexdigest()
def guard():
 global _device
 m=Path('/Volumes/Fuji_SSD_Work');assert m.is_mount(),'SSD lost; stop, no fallback'
 d=plistlib.loads(subprocess.check_output(['/usr/sbin/diskutil','info','-plist',str(m)]))
 assert d['VolumeUUID']==UUID and d['FilesystemType']=='apfs','Wrong SSD'
 v=os.statvfs(m);assert v.f_bavail*v.f_frsize>25*2**30,'SSD low space'
 _device=m.stat().st_dev
 return dict(uuid=UUID,free_gib=round(v.f_bavail*v.f_frsize/2**30,2))
def write_guard(p):
 m=Path('/Volumes/Fuji_SSD_Work');assert m.is_mount(),'SSD lost'
 if _device is None:guard()
 assert m.stat().st_dev==_device,'SSD replaced'
 assert Path(p).resolve().is_relative_to(W),'Outside D3'
def save(p,x):
 p=W/p;write_guard(p);p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_name(p.name+'.'+str(threading.get_ident())+'.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)
def load(p):return json.loads((W/p).read_text())
def event(name,**x):
 row=dict(at=now(),event=name,**x)
 with _lock:
  p=W/'logs/events.jsonl';write_guard(p)
  with p.open('a') as f:f.write(stable(row)+'\n')
 print(stable(row),flush=True)
def spans(doc,limit=300):
 out=[]
 for f in ['title','abstract']:
  text=doc.get(f) or '';s=0
  while s<len(text):
   e=min(s+limit,len(text))
   if e<len(text):
    k=max(text.rfind(' ',s+120,e),text.rfind('。',s+120,e),text.rfind('；',s+120,e))
    if k>=s+120:e=k+1
   out.append(dict(id='S'+str(len(out)+1).zfill(3),field=f,text=text[s:e],start=s,end=e));s=e
 return out
def source_input(doc):return dict(family_id=doc['family_id'],title=doc.get('title') or '',abstract=doc.get('abstract') or '',source_spans=spans(doc))
def snapshot():
 files=[p for sub in ['scripts','prompts','schemas','tests'] for p in (W/sub).glob('*') if p.is_file()]+[W/'AGENTS.md',W/'run-python']
 hashes={str(p.relative_to(W)):sha(p) for p in files};key=oh(hashes)
 import shutil
 dest=W/'code_snapshots'/key;write_guard(dest)
 if not dest.exists():
  for p in files:
   d=dest/p.relative_to(W);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
  save(dest/'manifest.json',dict(at=now(),hashes=hashes))
 return key
object_hash=oh
