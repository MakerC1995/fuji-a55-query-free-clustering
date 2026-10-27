from common import *
from client import read_key
from pipeline import spans
from design import DIM
import collections,re,zipfile,xml.etree.ElementTree as ET,sqlite3
import pyarrow.parquet as pq

def main():
 guard();manifest=load('D3_MANIFEST.json');stats=load('evidence/FINAL_STATISTICS.json');docs={d['family_id']:d for d in load('inputs/ALL_DOCUMENTS.json')};status=pq.read_table(W/'D3_PROCESSING_STATUS.parquet').to_pylist();contrib=pq.read_table(W/'D3_PATENT_CONTRIBUTIONS.parquet').to_pylist();audits=pq.read_table(W/'D3_EVIDENCE_AUDIT.parquet').to_pylist();labels=pq.read_table(W/'D3_LABELS.parquet').to_pylist()
 assert len(status)==1117 and len({r['family_id'] for r in status})==1117
 assert len(contrib)==1065 and len({r['contribution_id'] for r in contrib})==1065
 assert not any(r.get('human_confirmed') for r in contrib+audits)
 assert not any(r['label_tier']=='Gold' for r in labels)
 for c in contrib:
  fs=json.loads(c['field_support_json']);assert all(fs[p]['grade'] in ['Explicit','Supported Paraphrase'] for p in c['supported_candidate_paths'])
  if c['silver_supported_candidate']:assert c['processing_status']=='VALID' and c['full_conclusion_grade'] in ['Explicit','Supported Paraphrase'] and all(a['grade'] in ['Explicit','Supported Paraphrase'] for a in fs.values())
 for a in audits:
  for s in json.loads(a['source_spans_json']):assert (docs[a['family_id']].get(s['field']) or '')[s['start']:s['end']]==s['text']
  if a['grade'] in ['Inferred','Unsupported']:assert not a['source_supported_silver']
 hist=[load(p) for p in (W/'working/history').glob('*.json')];assert len(hist)==45 and collections.Counter(r['scope'] for r in hist)=={'main_discovery39':39,'postfreeze_probe6':6}
 d4=pq.read_table(W/'D4_MERGE_TEST_CASES.parquet').to_pylist();assert len(d4)==39 and not any(r['human_confirmed'] for r in d4)
 for p in load('inputs/D4_PAIR_SELECTION.json')['pairs'][:2]:assert (W/'working/d4'/(p['pair_id']+'.json')).exists(),'Missing mandated D4 boundary case'
 for p,h in load('evidence/MODEL_FREEZE.json')['semantic_code_hashes'].items():assert sha(W/p)==h,p
 for p,h in load('inputs/D2_LOCK.json')['files'].items():assert sha(D2/p)==h,p
 dbpath=D2/'outputs/TECHNOLOGY_KNOWLEDGE_BASE.sqlite';assert dbpath.is_file();db=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON');tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")];counts={t:db.execute('SELECT count(*) FROM "'+t.replace('"','""')+'"').fetchone()[0] for t in tables};db.close()
 save('evidence/D2_SQLITE_READONLY_RECONCILIATION.json',dict(at=now(),path=str(dbpath),query_only=True,table_counts=counts))
 for n in ['D3_EVALUATION_SET','D3_QUALITY_METRICS','D3_PRINTHEAD_RELEVANCE']:
  p=W/(n+'.xlsx');assert p.is_file();checks=[]
  with zipfile.ZipFile(p) as z:
   tables=[x for x in z.namelist() if re.match(r'xl/tables/table\d+\.xml$',x)];worksheets=[x for x in z.namelist() if re.match(r'xl/worksheets/sheet\d+\.xml$',x)];assert len(tables)==len(worksheets)
   panes=0;validations=0;formulas=0
   for x in worksheets:
    data=z.read(x);root=ET.fromstring(data);panes+=len(root.findall('.//{*}pane'));validations+=len(root.findall('.//{*}dataValidation'));formulas+=len(root.findall('.//{*}f'))
   assert panes>0
   if n=='D3_EVALUATION_SET':assert validations==13 and formulas==len(load('working/WORKBOOK_DATA.json')['human'])+1
   if n=='D3_QUALITY_METRICS':assert formulas==len(load('working/WORKBOOK_DATA.json')['metrics'])+10
   checks=dict(file=n+'.xlsx',sheets=len(worksheets),native_tables=len(tables),panes=panes,validations=validations,formulas=formulas)
  save('evidence/'+n+'_NATIVE_QA.json',checks)
 # Exact credential scan, without ever printing the credential.
 key=read_key().encode();checked=0
 for dirname in ['requests','responses','cache','working/main','working/main_history','prompts','schemas','scripts','evidence','logs']:
  for p in (W/dirname).rglob('*'):
   if p.is_file() and p.suffix in ['.json','.jsonl','.txt','.py','.md','.mjs']:
    assert key not in p.read_bytes(),'Credential found in publication candidate';checked+=1
 save('evidence/FINAL_VERIFICATION.json',dict(at=now(),passed=True,source_spans_exact=True,source_files_unchanged=True,frozen_semantic_code_unchanged=True,primary_families=1117,contributions=len(contrib),audit_rows=len(audits),human_gold=0,history39_plus6=True,d4_cases=len(d4),credential_scan_files=checked,credential_found=False))
 print(stable(dict(result='PASS',family_count=1117,contributions=len(contrib),audit_rows=len(audits),history=len(hist),d4_cases=len(d4),credential_scan_files=checked)))
if __name__=='__main__':main()
