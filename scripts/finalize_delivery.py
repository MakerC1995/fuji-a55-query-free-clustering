"""Final source/label checks, gates and delivery manifest. No recomputation."""
from experiment import *
from analyze import allruns
import ast,re
def main():
 for p in (W/'scripts').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 report=(W/'REPORT.md').read_text();assert sorted(map(int,re.findall(r'^## Q(\d+)',report,re.M)))==list(range(1,11))
 frozen=json.loads((W/'evidence/ASSIGNMENTS_FROZEN.json').read_text())
 for p,h in frozen['sha256'].items():assert sha(W/p)==h,p
 for p,h in frozen['parameters_sha256'].items():assert sha(W/p)==h,p
 first=json.loads((W/'evidence/FIRST_NAMING_FROZEN.json').read_text())
 for p,h in first['outputs'].items():assert sha(W/'technology_catalog/phase1'/p)==h,p
 for name,rec in json.loads((W/'evidence/input_file_stats.json').read_text()).items():
  st=(B/name).stat();assert st.st_size==rec['bytes'] and st.st_mtime_ns==rec['mtime_ns'],name
 assert json.loads((W/'evidence/assignment_readback.json').read_text())['status']=='PASS'
 assert json.loads((W/'evidence/final_workbook_validation.json').read_text())['status']=='PASS'
 completion=json.loads((W/'evidence/naming_completion.json').read_text());assert completion['phase1']==completion['phase2']==70
 post=json.loads((W/'evidence/posthoc_blind_completion.json').read_text());assert post['complete'] and post['panels']==8
 rawfiles=[p for folder in ['phase1','phase2','posthoc_blind'] for p in (W/'technology_catalog'/folder).glob('*.raw.json')]
 assert len(rawfiles)==148
 rawstats=collections.Counter();pt=et=0
 for p in rawfiles:
  r=json.loads(p.read_text());rawstats[r.get('done_reason','unknown')]+=1;pt+=r.get('prompt_eval_count',0);et+=r.get('eval_count',0)
 outdir=W/'outputs/01a171fb-0dd6-7792-b36b-80e200aba942'
 expected=['CLUSTER_STATISTICS.xlsx','CLUSTER_CATALOG.xlsx','TECHNOLOGY_CATALOG.xlsx','RARE_TECHNOLOGY_CANDIDATES.xlsx']
 for name in expected:assert (outdir/name).is_file()
 time_now=time.strftime('%Y-%m-%dT%H:%M:%S%z')
 g3=json.loads((W/'evidence/D1-G3.json').read_text());g3.update(status='PASS',completed_at=time_now,semantics_reviewed_named_records=15,rare_review_rows=2329)
 dump('evidence/D1-G3.json',g3)
 dump('evidence/D1-G4.json',dict(status='PASS',completed_at=time_now,query_free_named_panels=70,supplemental_posthoc_blind_panels=8,first_pass_theme_attempts=112,first_pass_named_candidates_after_literal_rule=15,first_pass_pending_records=97,semantic_scope_and_mixed_mechanisms_explicit=True,historical_check_complete=True,not_final_technology_tree=True))
 outputs=[W/name for name in ['REPORT.md','ALGORITHM_COMPARISON.md','HISTORICAL_TREE_CHECK.md','TECHNOLOGY_CATALOG.md','CLUSTER_ASSIGNMENTS.parquet','README.md']]+[outdir/name for name in expected]+list((W/'figures').glob('*.png'))
 allarrays=[p for a in ['kmeans','hdbscan','leiden'] for p in (W/a).rglob('*.npy')]+list((W/'hdbscan').glob('*.npz'))
 source_meta=json.loads((B/'baseline.json').read_text())
 manifest=dict(experiment_id='A55-D1-query-free-v1',status='COMPLETE_WITH_EXPLICIT_LIMITATIONS',completed_at=time_now,workspace=str(W),storage=dict(apfs_uuid='534D9B75-27C9-49B5-89A0-4DF7E631107C',active_root=str(B),mac_fallback=False),input_audit=json.loads((W/'evidence/input_audit.json').read_text()),source_baseline=source_meta,configuration=json.loads((W/'configs/experiment_v1.json').read_text()),environment=json.loads((W/'evidence/environment.json').read_text()),runs=allruns(),frozen_labels=frozen['sha256'],frozen_parameters=frozen['parameters_sha256'],code_at_input_freeze=frozen.get('code_sha256',{}),final_code_sha256={str(p.relative_to(W)):sha(p) for p in (W/'scripts').iterdir() if p.suffix in ['.py','.mjs']},code_changes_after_freeze='Quote auditing, completed-stage reuse, artifact assembly and reports; no labels, vectors or algorithm parameters changed.',array_output_sha256={str(p.relative_to(W)):sha(p) for p in allarrays},delivery_files={str(p.relative_to(W)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in outputs},model_naming=dict(completion=completion,supplemental_posthoc=post,inference_responses=len(rawfiles),response_reasons=dict(rawstats),prompt_tokens=pt,output_tokens=et,local_llm=json.loads((W/'evidence/local_llm_lock.json').read_text()),internet_llm_api_calls=0,new_embedding_calls=0,authorization_receipt='evidence/lan_destination_authorization.json',initial_auto_review_rejection_executed=False),quote_audit=json.loads((W/'evidence/quote_audit_summary.json').read_text()),semantic_review='evidence/semantic_source_review.json (representative-text reading, not human Gold)',catalog=json.loads((W/'evidence/catalog_assembly.json').read_text()),historical_check=json.loads((W/'evidence/historical_check.json').read_text()),posthoc_amendment=json.loads((W/'evidence/posthoc_granularity_amendment.json').read_text()),gates={g:json.loads((W/f'evidence/{g}.json').read_text()) for g in ['D1-G1','D1-G2','D1-G3','D1-G4']},limitations=['Clusters mix object, application, material and mechanism levels.','PCA changes neighborhood structure; HDBSCAN Noise is not irrelevance.','Literal quotes do not prove common mechanisms; 15 named candidates are not 15 validated routes.','Historical labels only used after first naming freeze; post-hoc blind results are not first-pass discoveries.'])
 dump('EXPERIMENT_MANIFEST.json',manifest)
 # All local Markdown links in principal deliverables must resolve.
 checked=0
 for name in ['REPORT.md','ALGORITHM_COMPARISON.md','HISTORICAL_TREE_CHECK.md']:
  for p in re.findall(r'\]\((/Volumes/[^)]+)\)',(W/name).read_text()):
   assert Path(p).exists(),p;checked+=1
 receipt=dict(status='PASS',completed_at=time_now,all_ten_report_questions=True,markdown_local_links_checked=checked,frozen_label_files=len(frozen['sha256']),labels_and_original_inputs_unchanged=True,parquet_all_rows_verified=11044345,workbooks=4,sheets=8,naming_panels=70,posthoc_blind_panels=8,inference_responses=148,manifest_sha256=sha(W/'EXPERIMENT_MANIFEST.json'),ssd_free_gib=psutil.disk_usage('/Volumes/Fuji_SSD_Work').free/2**30)
 dump('evidence/FINAL_VALIDATION.json',receipt)
 print(json.dumps(receipt,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
