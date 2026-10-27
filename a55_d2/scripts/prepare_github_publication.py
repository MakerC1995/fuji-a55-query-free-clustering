"""Publish a verified D2 snapshot into the existing SSD GitHub Desktop checkout."""
from common import *
import shutil
PUBLISH=Path('/Volumes/Fuji_SSD_Work/workspaces/fuji-a55-query-free-clustering')
def main():
 guard();assert load('evidence/FINAL_INTEGRITY_CHECKS.json')['status']=='INTEGRITY_CHECKS_PASSED'
 assert PUBLISH.is_dir() and (PUBLISH/'.git').exists()
 code=PUBLISH/'a55_d2';delivery=PUBLISH/'deliverables/A5.5-D2';records=[];root_updates=[]
 previous_manifest=json.loads((PUBLISH/'D2_PUBLICATION_MANIFEST.json').read_text()) if (PUBLISH/'D2_PUBLICATION_MANIFEST.json').exists() else {}
 previous_updates={r['path']:r for r in previous_manifest.get('root_file_updates',[])}
 def put(src,dest):
  assert dest.resolve().is_relative_to(PUBLISH.resolve());assert src.is_file()
  dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
  assert sha(src)==sha(dest)
  records.append(dict(source=str(src.relative_to(W)) if src.is_relative_to(W) else str(src),path=str(dest.relative_to(PUBLISH)),bytes=dest.stat().st_size,source_sha256=sha(src),published_sha256=sha(dest)))
 for folder in ['scripts','tests','prompts','configs']:
  for src in sorted((W/folder).rglob('*')):
   if src.is_file() and '__pycache__' not in src.parts:put(src,code/src.relative_to(W))
 for name in ['README.md','TASK_PACKAGE.md','run-python']:
  put(W/name,code/name)
 for src in sorted((W/'outputs').rglob('*')):
  if not src.is_file() or src.name=='D2_DELIVERY_BUNDLE.zip':continue
  if src.suffix not in ['.md','.parquet','.sqlite','.json','.xlsx','.png']:continue
  dest=delivery/('previews' if src.suffix=='.png' else '')/src.name
  put(src,dest)
 bundle=W/'outputs/D2_DELIVERY_BUNDLE.zip';assert bundle.is_file()
 if bundle.stat().st_size<=80*2**20:
  put(bundle,delivery/bundle.name);archive=dict(path=bundle.name,bytes=bundle.stat().st_size,sha256=sha(bundle),split=False)
 else:
  archive=dict(path=bundle.name,bytes=bundle.stat().st_size,sha256=sha(bundle),split=True,parts=[])
  with bundle.open('rb') as f:
   i=0
   while True:
    chunk=f.read(32*2**20)
    if not chunk:break
    i+=1;dest=delivery/'archive'/(bundle.name+'.part'+str(i).zfill(3));dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(chunk)
    item=dict(path=str(dest.relative_to(delivery)),bytes=len(chunk),sha256=digest_bytes(chunk));archive['parts'].append(item)
    records.append(dict(source='D2_DELIVERY_BUNDLE.zip lossless bytes',path=str(dest.relative_to(PUBLISH)),bytes=len(chunk),source_sha256=item['sha256'],published_sha256=item['sha256']))
  (delivery/'ARCHIVE_PARTS.json').write_text(json.dumps(archive,ensure_ascii=False,indent=2)+'\n')
  restore="""from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
meta=json.loads((root/'ARCHIVE_PARTS.json').read_text())
out=root/meta['path']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if out.exists():
 assert out.stat().st_size==meta['bytes'] and digest(out)==meta['sha256'],'Existing archive differs; do not overwrite'
else:
 tmp=out.with_suffix('.restoring')
 with tmp.open('xb') as target:
  for part in meta['parts']:
   p=root/part['path'];assert p.stat().st_size==part['bytes'] and digest(p)==part['sha256'];target.write(p.read_bytes())
 assert tmp.stat().st_size==meta['bytes'] and digest(tmp)==meta['sha256'];tmp.rename(out)
print(out)
"""
  (delivery/'restore_archive.py').write_text(restore)
  combined=hashlib.sha256()
  for r in archive['parts']:combined.update((delivery/r['path']).read_bytes())
  assert combined.hexdigest()==archive['sha256']
 archive_note='完整证据压缩包分块无损保存；运行 python3 restore_archive.py 后按ARCHIVE_PARTS.json核验还原。' if archive['split'] else 'D2_DELIVERY_BUNDLE.zip包含完整代码、冻结输入、请求/响应、失败和修订审计。'
 (delivery/'README.md').write_text('# A5.5-D2 交付件\n\n主入口：[D2_REPORT.md](D2_REPORT.md) 与 [TECHNOLOGY_KNOWLEDGE_BASE.xlsx](TECHNOLOGY_KNOWLEDGE_BASE.xlsx)。\n\n主试验1117族，1114有效、3失败；975条明确机制贡献，926候选机制、26对象/问题域。已知误并及字段疑点见质量报告，尚无独立人类Gold。\n\n'+archive_note+'\n\n代码快照在 [a55_d2](../../a55_d2/)。原数据库、全库原向量、私人审核库与凭据不在本交付中。\n')
 # Add a concise D2 entry while retaining D1's historical publication manifest unchanged.
 for name,addition in [
  ('README.md','# A5.5-D2 技术知识库原型\n\n[D2交付件](deliverables/A5.5-D2/) 单独存放；[D2报告](deliverables/A5.5-D2/D2_REPORT.md)、[主工作簿](deliverables/A5.5-D2/TECHNOLOGY_KNOWLEDGE_BASE.xlsx)、[代码快照](a55_d2/)。当前为1117族试验，含已知误并及源文疑点，不是全库穷尽或经人工验证的知识库。\n\n仓库完整性检查：python3 scripts/verify_repository.py。原D1发布清单保持历史版本；以下为D1入口。\n\n---\n\n'),
  ('AGENTS.md','# D2追加归档\n\n本库同时保存D1和D2实验。D2代码在a55_d2/，科学交付单独在deliverables/A5.5-D2/；均不授权重跑已完成的全库编码或聚类。D2核心先冻结、后历史揭盲，已知错误只记录，不在本冻结版本回写。以下D1规则继续约束D1原件。\n\n')
 ]:
  p=PUBLISH/name;before=p.read_bytes();oldhash=previous_updates.get(name,{}).get('previous_sha256',digest_bytes(before))
  if addition.encode() not in before:p.write_text(addition+before.decode())
  root_updates.append(dict(path=name,previous_sha256=oldhash,published_sha256=sha(p),reason='Add D2 archive and separated deliverables index; D1 frozen scientific files unchanged'))
 # Include all newly authored public index/restore files in the publication manifest.
 listed={r['path'] for r in records}
 for p in [delivery/'README.md',delivery/'ARCHIVE_PARTS.json',delivery/'restore_archive.py']:
  if p.exists() and str(p.relative_to(PUBLISH)) not in listed:records.append(dict(path=str(p.relative_to(PUBLISH)),bytes=p.stat().st_size,published_sha256=sha(p),source='Publication index or lossless archive restore utility'))
 checker="""from pathlib import Path
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
"""
 checkpath=PUBLISH/'scripts/verify_repository.py';checkpath.write_text(checker);records.append(dict(path=str(checkpath.relative_to(PUBLISH)),bytes=checkpath.stat().st_size,published_sha256=sha(checkpath),source='Repository integrity checker'))
 manifest=dict(at=now(),repository='MakerC1995/fuji-a55-query-free-clustering',source_workspace=str(W),publication_status='PREPARED_FOR_GITHUB_DESKTOP_COMMIT_AND_PUSH',core_freeze_sha256=object_hash(load('evidence/CORE_FREEZE.json')),files=records,root_file_updates=root_updates,archive=archive,contains_original_large_database_or_vectors=False,private_review_database_included=False,credentials_included=False)
 (PUBLISH/'D2_PUBLICATION_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 save('evidence/D2_PUBLICATION_PREPARED.json',dict(at=now(),repository=str(PUBLISH),files=len(records),archive_split=archive['split'],manifest_sha256=sha(PUBLISH/'D2_PUBLICATION_MANIFEST.json')))
 print(stable(dict(prepared_files=len(records),archive_bytes=archive['bytes'],archive_split=archive['split'])))
if __name__=='__main__':main()
