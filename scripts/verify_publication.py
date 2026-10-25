"""Offline integrity check; no analysis or model invocation."""
from pathlib import Path
import hashlib,json,ast,lzma
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(8*2**20),b""):h.update(b)
 return h.hexdigest()
def main():
 m=json.loads((ROOT/"PUBLICATION_MANIFEST.json").read_text())
 for rec in m["files"]:
  p=ROOT/rec["path"];assert p.stat().st_size==rec["bytes"] and sha(p)==rec["sha256"],rec["path"]
 for p in (ROOT/"scripts").glob("*.py"):ast.parse(p.read_text(),filename=str(p))
 frozen=json.loads((ROOT/"evidence/ASSIGNMENTS_FROZEN.json").read_text())
 for name,want in frozen["sha256"].items():assert sha(ROOT/name)==want,name
 for name,want in frozen["parameters_sha256"].items():assert sha(ROOT/name)==want,name
 meta=json.loads((ROOT/"data/cluster_assignments/parts.json").read_text());h=hashlib.sha256();n=0
 for rec in meta["parts"]:
  with lzma.open(ROOT/rec["path"],"rb") as f:
   for b in iter(lambda:f.read(8*2**20),b""):h.update(b);n+=len(b)
 assert h.hexdigest()==meta["sha256"] and n==meta["bytes"]
 print(json.dumps(dict(status="PASS",published_files=len(m["files"]),frozen_labels=len(frozen["sha256"]),parquet_bytes=n,parquet_sha256=h.hexdigest(),no_recomputation=True)))
if __name__=="__main__":main()
