"""Restore exact delivered Parquet from SHA-256 checked chunks; no dependencies."""
from pathlib import Path
import json,hashlib,os,lzma
ROOT=Path(__file__).resolve().parents[1]
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(8*2**20),b""):h.update(b)
 return h.hexdigest()
def main():
 meta=json.loads((ROOT/"data/cluster_assignments/parts.json").read_text());out=ROOT/meta["file"]
 if out.exists():
  assert out.stat().st_size==meta["bytes"] and digest(out)==meta["sha256"],"Existing file differs; not overwritten"
  print("PASS: exact Parquet already present");return
 for rec in meta["parts"]:
  p=ROOT/rec["path"];assert p.stat().st_size==rec["bytes"] and digest(p)==rec["sha256"],rec["path"]
 tmp=out.with_suffix(".parquet.restoring");assert not tmp.exists(),"Interrupted temporary file exists"
 try:
  with tmp.open("xb") as f:
   for rec in meta["parts"]:
    with lzma.open(ROOT/rec["path"],"rb") as part:
     for b in iter(lambda:part.read(8*2**20),b""):f.write(b)
  assert tmp.stat().st_size==meta["bytes"] and digest(tmp)==meta["sha256"];os.replace(tmp,out)
 except Exception:
  if tmp.exists():tmp.unlink()
  raise
 print("PASS:",out.name,meta["bytes"],meta["sha256"])
if __name__=="__main__":main()
