from common import *
def main():
 guard();assert not (W/'evidence/MODEL_FREEZE.json').exists()
 dev=load('evidence/BATCH_development_full.json');comp=load('evidence/COMPARISON_development.json')
 semantic=['common.py','client.py','design.py','pipeline.py','experiments.py','related_audit.py','history.py','d4_cases.py']
 files=[W/'scripts'/p for p in semantic]+list((W/'prompts').glob('*.txt'))+list((W/'schemas').glob('*.json'))
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=W,text=True).strip()
 rec=dict(at=now(),version='D3.1',semantic_code_hashes={str(p.relative_to(W)):sha(p) for p in files},code_commit=commit,code_snapshot=snapshot(),split_lock_sha256=sha(W/'inputs/SPLIT_LOCK.json'),input_lock_sha256=sha(W/'inputs/D2_LOCK.json'),development_main_counts=dev['counts'],development_comparison_counts=comp['counts'],holdout_size=42,holdout_seen_for_prompt_tuning=False,allowed_after_freeze='Fixed same-model configs, bounded retries<=6 per fingerprint, cache recovery, reports/exports; no semantic prompt tuning based on holdout',human_gold_n=0,known_limitations=['2 development families failed after6 bounded attempts','4 development families have unresolved evidence issues and remain quarantined','Same-model Silver bias; no human accuracy proof'])
 save('evidence/MODEL_FREEZE.json',rec);event('model_frozen',code_commit=commit,semantic_files=len(files),holdout=42)
if __name__=='__main__':main()
