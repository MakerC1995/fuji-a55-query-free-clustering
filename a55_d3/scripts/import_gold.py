"""Explicit human-label import; never promote Silver or fill blanks."""
from common import *
from design import DIM,LABELS,A,B
import argparse,zipfile,xml.etree.ElementTree as ET,posixpath,re
import pyarrow as pa,pyarrow.parquet as pq
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def read_rows(p):
 with zipfile.ZipFile(p) as z:
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():ss=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml'))]
  wb=ET.fromstring(z.read('xl/workbook.xml'));rs=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'));paths={r.attrib['Id']:r.attrib['Target'] for r in rs};sid=next(s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'] for s in wb.find('s:sheets',NS) if s.attrib['name']=='Human review');target=paths[sid];target=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
  out=[]
  for r in ET.fromstring(z.read(target)).findall('.//s:sheetData/s:row',NS):
   if int(r.attrib['r'])<6:continue
   row={}
   for c in r:
    col=re.sub(r'\d','',c.attrib['r']);v=c.find('s:v',NS);t=c.attrib.get('t');value=v.text if v is not None else None
    if t=='s' and value is not None:value=ss[int(value)]
    elif t=='inlineStr':value=''.join(c.find('s:is',NS).itertext())
    row[col]=value
   out.append(row)
  return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--workbook',required=True);p.add_argument('--confirm-human-reviewed',action='store_true');p.add_argument('--dry-run',action='store_true');a=p.parse_args();guard();book=Path(a.workbook).resolve();rows=read_rows(book);sel={r['family_id']:r for r in load('inputs/EVALUATION_SELECTION.json')};labels=[];incomplete=0
 for r in rows:
  if not r.get('A'):continue
  f=r['A'];assert f in sel and r.get('B')==sel[f]['split'] and r.get('D')==sel[f]['source_text_hash'],'FID/split/hash mismatch'
  assert r.get('C') in ['D2_ARCHIVED','D3_FULL']
  cols=[chr(x) for x in range(ord('E'),ord('T')+1)]
  if not any(r.get(c) for c in cols):continue
  if not all(r.get(c) for c in cols):incomplete+=1;continue
  dimensions=DIM+['source_adequacy','axis_a','axis_b']
  for i,dim in enumerate(dimensions):
   v=r[chr(ord('H')+i)];assert v in (A if dim=='axis_a' else B if dim=='axis_b' else LABELS),'Invalid human label'
   labels.append(dict(family_id=f,split=r['B'],configuration=r['C'],dimension=dim,label=v,label_tier='Gold',human_reviewer=r['E'],human_reviewed_at=r['F'],human_reason=r['G'],source_text_hash=r['D'],source_workbook_sha256=sha(book)))
 if a.dry_run:print(stable(dict(complete_label_records=len(labels),incomplete_rows=incomplete,written=False)));return
 assert a.confirm_human_reviewed,'Require explicit --confirm-human-reviewed; never infer human review from populated cells'
 assert labels,'No complete human review rows; no fake Gold output created'
 target=W/'human_imports'/now().replace(':','_');target.mkdir(parents=True);pq.write_table(pa.Table.from_pylist(labels),target/'D3_HUMAN_GOLD.parquet',compression='zstd');save(target/'IMPORT_RECEIPT.json',dict(at=now(),source_workbook=str(book),source_sha256=sha(book),label_records=len(labels),incomplete_rows=incomplete,explicit_human_confirmation=True))
 print(str(target))
if __name__=='__main__':main()
