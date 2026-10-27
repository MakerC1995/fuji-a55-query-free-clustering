"""Build typed contribution tables from current-protocol, verified cached responses."""
from common import *
from extract import key_for
from schema import ENRICHED_SCHEMA,validate,literal_index
from curation import apply as apply_source_amendment
import pandas as pd,pyarrow as pa,pyarrow.parquet as pq,argparse,collections
def current_records(stage):
 docs={d['family_id']:d for d in pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet').to_dict('records')}
 ids=load('inputs/STAGES.json')[stage];prompt=(W/'prompts/extraction_v2.txt').read_text()
 conn=state_db();states={r[0]:r for r in conn.execute('select family_id,cache_key,status,result_path,attempts,error from extraction')};conn.close()
 rows=[];status=[];objects=[]
 for fid in ids:
  d=docs[fid];r=states.get(fid);expected=key_for(d,prompt)
  state='UNATTEMPTED' if not r else (r[2] if r[1]==expected else 'STALE_DIFFERENT_PROTOCOL')
  status.append(dict(family_id=fid,row_idx=d['row_idx'],source_text_hash=d['text_hash'],status=state,attempts=r[4] if r and r[1]==expected else 0,error=r[5] if r and r[1]==expected else None))
  if state!='VALID':continue
  saved=load(r[3]);assert saved['cache_key']==expected and saved['source_text_hash']==d['text_hash']
  refinement=W/'refinements'/(fid.replace(':','_')+'.json')
  if refinement.exists():
   ref=load(str(refinement));assert ref['cache_key']==expected and ref['source_text_hash']==d['text_hash'];assert ref['result_sha256']==object_hash(ref['result'])
   if ref.get('adoption_status')=='ADOPTED_AFTER_SOURCE_REVIEW':saved=dict(saved,**ref)
  assert object_hash(saved['result'])==saved['result_sha256'];validate(saved['result'],ENRICHED_SCHEMA)
  for original in saved['result']['contributions']:
   c=apply_source_amendment(original,d)
   for e in c['evidence_spans']:assert (d[e['field']] or '')[e['start']:e['end']]==e['quote']
   obj=dict(c);obj['source_title']=d['title'];obj['source_abstract']=d['abstract'];obj['language']=d['language'];obj['publication_id']=d['publication_id'];obj['row_idx']=d['row_idx']
   obj['cache_key']=expected;obj['request_id']=saved['request_id'];obj['model_digest']=saved['model_digest'];obj['prompt_sha256']=saved['prompt_sha256'];obj['code_version']=saved.get('code_version')
   objects.append(obj)
   row={k:c[k] for k in ['contribution_id','family_id','source_text_hash','evidence_level','mechanism_type','ambiguity_notes','semantic_validation_status','schema_version']}
   for k in ['technical_object','technical_problem','technical_mechanism','implementation','expected_effect','applicable_conditions']:row[k]=c[k]['text']
   for k in ['materials','process_methods','structures']:row[k]=[x['text'] for x in c[k]]
   for k in ['parameters','evidence_spans','field_evidence_gaps','numeric_citation_gaps']:row[k]=c[k]
   row['rejected_parameter_claims_json']=stable(c.get('rejected_parameter_claims',[]));row['parameter_extraction_status']=c.get('parameter_extraction_status','LEGACY_NOT_RECORDED')
   row['field_evidence_ids_json']=stable({k:c[k]['evidence_ids'] for k in ['technical_object','technical_problem','technical_mechanism','implementation','expected_effect','applicable_conditions']})
   row['evidence_alignment_provenance_json']=stable(c['evidence_alignment_provenance'])
   row.update({k:obj[k] for k in ['source_title','source_abstract','language','publication_id','row_idx','cache_key','request_id','model_digest','prompt_sha256','code_version']})
   row['refinement_provenance_json']=c.get('refinement_provenance_json')
   row['source_model_contribution_id']=c.get('source_model_contribution_id',c['contribution_id']);row['curation_provenance_json']=c.get('curation_provenance_json')
   row['quantitative_parameter_count']=len(c['parameters']);row['field_gap_count']=len(c['field_evidence_gaps'])
   rows.append(row)
 assert len({r['contribution_id'] for r in rows})==len(rows)
 return rows,status,objects
def table_schema():
 strs=['contribution_id','family_id','source_text_hash','evidence_level','mechanism_type','ambiguity_notes','semantic_validation_status','schema_version','technical_object','technical_problem','technical_mechanism','implementation','expected_effect','applicable_conditions','field_evidence_ids_json','evidence_alignment_provenance_json','source_title','source_abstract','language','publication_id','cache_key','request_id','model_digest','prompt_sha256','code_version','rejected_parameter_claims_json','parameter_extraction_status','source_model_contribution_id','curation_provenance_json','refinement_provenance_json']
 fields=[pa.field(k,pa.string()) for k in strs]+[pa.field(k,pa.int64()) for k in ['row_idx','quantitative_parameter_count','field_gap_count']]
 fields +=[pa.field(k,pa.list_(pa.string())) for k in ['materials','process_methods','structures','field_evidence_gaps','numeric_citation_gaps']]
 fields +=[pa.field('parameters',pa.list_(pa.struct([pa.field('name',pa.string()),pa.field('kind',pa.string()),pa.field('raw',pa.string()),pa.field('evidence_ids',pa.list_(pa.string()))])))]
 fields +=[pa.field('evidence_spans',pa.list_(pa.struct([pa.field('id',pa.string()),pa.field('field',pa.string()),pa.field('quote',pa.string()),pa.field('start',pa.int64()),pa.field('end',pa.int64())])))]
 return pa.schema(fields)
def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',default='pilot30',choices=['pilot30','trial100','primary384','all_selected']);a=p.parse_args();guard();require_unfrozen()
 rows,status,objects=current_records(a.stage)
 out=W/'working'/a.stage;out.mkdir(parents=True,exist_ok=True)
 pq.write_table(pa.Table.from_pylist(rows,schema=table_schema()),out/'PATENT_CONTRIBUTIONS.parquet',compression='zstd')
 pd.DataFrame(status).to_parquet(out/'PATENT_PROCESSING_STATUS.parquet',index=False)
 save(str(out.relative_to(W))+'/contributions.json',objects)
 counts=collections.Counter(r['status'] for r in status)
 summary=dict(at=now(),stage=a.stage,families=len(status),status_counts=dict(counts),contributions=len(rows),explicit_mechanisms=sum(r['evidence_level']=='EXPLICIT_MECHANISM' for r in rows),families_with_explicit_mechanisms=len({r['family_id'] for r in rows if r['evidence_level']=='EXPLICIT_MECHANISM'}),contributions_with_unlinked_fields=sum(r['field_gap_count']>0 for r in rows),source_quote_spans=sum(len(r['evidence_spans']) for r in rows),all_quotes_verified=True,not_human_gold=True,terminal_attempts=sum(v for k,v in counts.items() if k in ['VALID','FAILED_VALIDATION']),complete=sum(v for k,v in counts.items() if k in ['VALID','FAILED_VALIDATION'])==len(status))
 save(str(out.relative_to(W))+'/SUMMARY.json',summary)
 event('contributions_consolidated',**summary)
if __name__=='__main__':main()
