"""Independent literal-source audit; preserves every first-pass local LLM output."""
from experiment import *
import pandas as pd
def main():
 assert (W/'evidence/FIRST_NAMING_FROZEN.json').exists(),'First naming not frozen yet'
 panels={p['panel_id']:p for p in json.loads((W/'technology_catalog/cluster_panels.json').read_text())}
 rows=[];summaries=[];records=[]
 for p in (W/'technology_catalog/phase1').glob('*.json'):
  if any(v in p.name for v in ['.input.','.raw.','.error.']):continue
  rec=json.loads(p.read_text());records.append(rec);full_docs={d['family_id']:d for d in panels[rec['panel_id']]['docs']}
  inputs=[f for f in (W/'technology_catalog/phase1').glob(rec['panel_id']+'.attempt*.input.json') if sha(f)==rec['input_sha256']];assert len(inputs)==1
  sent=json.loads(json.loads(inputs[0].read_text())['messages'][1]['content']);docs={d['family_id']:d for d in sent['docs']}
  for ti,t in enumerate(rec['analysis'].get('themes',[])):
   valid=[];bad=0
   for qi,e in enumerate(t.get('evidence',[])):
    fid=e.get('family_id');quote=e.get('quote','');field=e.get('field','abstract');matches=[]
    if fid not in docs:status='unknown_family'
    elif not quote:status='empty_quote'
    else:
     matches=[f for f in ['title','abstract'] if quote in docs[fid][f]]
     if field in matches:status='exact_declared_field';valid.append(fid)
     elif matches:status='exact_other_field'
     elif any(quote in full_docs[fid][f] for f in ['title','abstract']):status='full_source_outside_sent_excerpt'
     else:status='no_verbatim_match'
    if status!='exact_declared_field':bad+=1
    rows.append(dict(panel_id=rec['panel_id'],theme_index=ti,model_name=t.get('unverified_name',t.get('name')),catalog_name=t.get('name'),family_id=fid,declared_field=field,quote=quote,quote_status=status,exact_matching_fields=';'.join(matches)))
   unique_texts=len({hashlib.sha256((docs[fid]['title']+'\n'+docs[fid]['abstract']).encode()).hexdigest() for fid in set(valid)})
   s=dict(panel_id=rec['panel_id'],theme_index=ti,model_name=t.get('unverified_name',t.get('name')),catalog_name=t.get('name'),valid_family_count=len(set(valid)),unique_supporting_texts=unique_texts,invalid_quote_count=bad,quote_audit_status='PASS' if bad==0 and len(set(valid))>=3 else 'REVIEW_REQUIRED',title_only_supporting_families=sum(docs[fid]['text_quality']=='title_only' for fid in set(valid)),original_panel_derived_status=t.get('evidence_validation'))
   summaries.append(s)
 pd.DataFrame(rows).to_csv(W/'technology_catalog/quote_audit.csv',index=False)
 pd.DataFrame(summaries).to_csv(W/'technology_catalog/theme_evidence_audit.csv',index=False)
 statuses=collections.Counter(r['quote_status'] for r in rows)
 dump('evidence/quote_audit_summary.json',dict(status='COMPLETE',panels=len(records),themes=len(summaries),quotes=len(rows),quote_status_counts=dict(statuses),panels_with_invalid_quotes=len({r['panel_id'] for r in rows if r['quote_status']!='exact_declared_field'}),model_original_named_records=sum(r['model_name']!='无法确定' for r in summaries),model_original_abstentions=sum(r['model_name']=='无法确定' for r in summaries),names_below_three_family_rule=sum(r['model_name']!='无法确定' and r['valid_family_count']<3 for r in summaries),named_theme_records=sum(r['catalog_name']!='无法确定' for r in summaries),unknown_theme_records=sum(r['catalog_name']=='无法确定' for r in summaries),named_theme_records_with_3_valid_families=sum(r['catalog_name']!='无法确定' and r['valid_family_count']>=3 for r in summaries),named_theme_records_with_fewer_than_3_independent_texts=sum(r['catalog_name']!='无法确定' and r['unique_supporting_texts']<3 for r in summaries),per_theme_status_corrections=sum(r['original_panel_derived_status']!=r['quote_audit_status'] for r in summaries),no_first_pass_files_modified=True,note='Independent audit fixes only overly conservative cross-theme propagation of panel errors; it never promotes fewer than 3 valid families or changes any model name/cluster. Exact-source matching is not semantic entailment or expert validation.'))
 print(json.dumps(dict(quote_status_counts=dict(statuses),panels=len(records),themes=len(summaries)),ensure_ascii=False))
if __name__=='__main__':main()
