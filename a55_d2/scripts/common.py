"""D2 isolated runtime. Existing corpus and D1 artifacts are read only."""
from pathlib import Path
import os,sys,json,hashlib,sqlite3,time,datetime,plistlib,subprocess
W=Path(__file__).resolve().parents[1]
D1=Path('/Volumes/Fuji_SSD_Work/workspaces/a55_d1_query_free_clustering')
BASE=Path('/Volumes/Fuji_SSD_Work/patent/embedding_benchmark/vector_corpus/v1')
sys.path.insert(0,str(D1/'deps'))
os.environ.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',VECLIB_MAXIMUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
UUID='534D9B75-27C9-49B5-89A0-4DF7E631107C'
_VERIFIED_DEVICE=None
def now():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def guard():
 global _VERIFIED_DEVICE
 mount=Path('/Volumes/Fuji_SSD_Work')
 assert mount.is_mount(),'SSD unavailable; no fallback'
 info=plistlib.loads(subprocess.check_output(['/usr/sbin/diskutil','info','-plist',str(mount)]))
 assert info['VolumeUUID']==UUID and info['FilesystemType']=='apfs'
 st=os.statvfs(mount);assert st.f_bavail*st.f_frsize>25*2**30
 _VERIFIED_DEVICE=mount.stat().st_dev
def require_unfrozen():
 assert not (W/'evidence/CORE_FREEZE.json').exists(),'Core discovery is frozen. Use a separately authorized new blind run; post-hoc checks cannot revise discovery.'
def digest_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8*2**20),b''):h.update(b)
 return h.hexdigest()
def stable(obj):return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def object_hash(obj):return digest_bytes(stable(obj).encode())
def write_guard(destination):
 mount=Path('/Volumes/Fuji_SSD_Work')
 assert mount.is_mount(),'SSD unavailable at write; no fallback or directory creation'
 if _VERIFIED_DEVICE is None:guard()
 assert mount.stat().st_dev==_VERIFIED_DEVICE,'SSD device changed during active process; stop'
 assert Path(destination).resolve().is_relative_to(W.resolve()),'Write outside isolated D2 workspace'
def save(path,obj):
 p=W/path;write_guard(p);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def load(path):return json.loads((W/path).read_text())
def event(name,**kw):
 rec=dict(kw);rec.update(at=now(),event=name);p=W/'logs/events.jsonl';write_guard(p);p.parent.mkdir(exist_ok=True)
 with p.open('a') as f:f.write(stable(rec)+'\n')
 print(stable(rec),flush=True)
def source_db():
 c=sqlite3.connect((BASE/'corpus.sqlite').as_uri()+'?mode=ro',uri=True)
 c.execute('PRAGMA query_only=ON');c.row_factory=sqlite3.Row;return c
def state_db():
 write_guard(W/'state/d2.sqlite')
 c=sqlite3.connect(W/'state/d2.sqlite',timeout=30);c.execute('PRAGMA journal_mode=WAL')
 c.executescript("""
 CREATE TABLE IF NOT EXISTS requests(request_id TEXT PRIMARY KEY,kind TEXT,cache_key TEXT,started_at TEXT,finished_at TEXT,status TEXT,prompt_tokens INTEGER,output_tokens INTEGER,wall_s REAL,error TEXT);
 CREATE TABLE IF NOT EXISTS extraction(family_id TEXT PRIMARY KEY,cache_key TEXT,status TEXT,result_path TEXT,attempts INTEGER,updated_at TEXT,error TEXT);
 """);c.commit();return c
