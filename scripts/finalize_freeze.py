from analyze import allruns,choose
from experiment import *
runs=allruns()
for name in ['technology_catalog/cluster_panels.json','evidence/LLM_INPUT_FREEZE.json']:
 p=W/name
 (W/'evidence'/('preflight_'+p.name)).write_bytes(p.read_bytes())
panels=[]
design=[('bge_k300_s42',30),('bge_k30_mutual_r1.0_s42',10),('bge_k30_sym_r1.0_s42',5),('bge_n238541_pca30_c30_s15',10),('bge_n50000_pca30_c10_s5',5),('qwen_k300_s42',5),('qwen_k30_mutual_r1.0_s42',3),('qwen_k30_sym_r1.0_s42',2)]
for rid,n in design:panels+=choose(next(r for r in runs if r['run_id']==rid),n)
assert len(panels)==len({p['panel_id'] for p in panels})==70
dump('technology_catalog/cluster_panels.json',panels)
dump('evidence/LLM_INPUT_FREEZE.json',dict(panels=70,sha256=sha(W/'technology_catalog/cluster_panels.json'),unprompted_by_known_technologies=True,time=time.strftime('%Y-%m-%dT%H:%M:%S%z')))
f=json.loads((W/'evidence/ASSIGNMENTS_FROZEN.json').read_text())
for path,h in f['sha256'].items():assert sha(W/path)==h,path
paths=[p for a in ['kmeans','hdbscan','leiden'] for p in (W/a).glob('*/result.json')]+list((W/'leiden').glob('*/local_result.json'))+list((W/'configs').glob('*'))
f['parameters_sha256']={str(p.relative_to(W)):sha(p) for p in paths if p.is_file()}
f['code_sha256']={str(p.relative_to(W)):sha(p) for p in (W/'scripts').glob('*.py')}
f['parameter_freeze_time']=time.strftime('%Y-%m-%dT%H:%M:%S%z')
dump('evidence/ASSIGNMENTS_FROZEN.json',f)
g=json.loads((W/'evidence/D1-G3.json').read_text());g['panels']=70;dump('evidence/D1-G3.json',g)
dump('evidence/panel_selection_validation.json',dict(status='PASS',preflight_panels=80,preflight_unique=75,final_panels=70,final_unique=70,naming_requests_before_correction=0,labels_changed=False,reason='Pre-inference validation caught repeated append-list entries; corrected evidence-only budget to the intended 70 distinct panels.',design=design))
print('Labels/parameters frozen; 70 unique evidence panels verified')
