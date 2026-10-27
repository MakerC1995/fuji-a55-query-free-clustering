from pathlib import Path
import hashlib,json,ast
root=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*2**20),b''):h.update(b)
 return h.hexdigest()
d1=json.loads((root/'PUBLICATION_MANIFEST.json').read_text());d2=json.loads((root/'D2_PUBLICATION_MANIFEST.json').read_text())
updates={r['path']:r for r in d2['root_file_updates']}
for r in d1['files']:
 p=root/r['path']
 if r['path'] in updates:
  u=updates[r['path']];assert r['sha256']==u['previous_sha256'] and sha(p)==u['published_sha256'],r['path']
 else:assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],r['path']
for u in d2['root_file_updates']:assert sha(root/u['path'])==u['published_sha256'],u['path']
for r in d2['files']:
 p=root/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['published_sha256'],r['path']
for p in (root/'a55_d2/scripts').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
assert all((root/r['path']).stat().st_size<=80*2**20 for r in d2['files'])
print(json.dumps(dict(status='PASS',d1_files=len(d1['files']),d2_files=len(d2['files']),no_recomputation=True)))
