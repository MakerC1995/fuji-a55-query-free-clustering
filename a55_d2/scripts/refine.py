"""Source-only second look at audited possible multi-contribution omissions."""
from common import *
import extract
from schema import EXTRACTION_WIRE_SCHEMA,ENRICHED_SCHEMA,audit_wire_extraction,apply_anchor_positions,validate
import pandas as pd,argparse,fcntl
SUFFIX="""
这是一次多贡献完整性复核。只提供同一族完整原始Title/Abstract，不提供旧结果、技术树或聚类。
先判断是否存在可相对独立实施、分别解决不同问题的两到四种工程办法。若存在要分别提取，不因“通常1项”而合在一起；同一办法的材料、结构和多个效果不要机械拆开。若必须保留综合贡献而不能可靠拆分，在ambiguity_notes具体说明。不得为了数量捏造办法。仍执行逐字段来源、参数与效果限制。
"""
def main(fids):
 guard();require_unfrozen();extract.freeze_code();extract.preflight();conn=state_db()
 docs={r['family_id']:r for r in pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet').to_dict('records')}
 base_prompt=(W/'prompts/extraction_v2.txt').read_text();prompt=base_prompt+SUFFIX
 for fid in fids:
  doc=docs[fid];basekey=extract.key_for(doc,base_prompt)
  state=conn.execute('select cache_key,status,result_path from extraction where family_id=?',(fid,)).fetchone()
  assert state and state[0]==basekey and state[1]=='VALID','First complete ordinary extraction for '+fid
  original=load(state[2]);prior=[c['contribution_id'] for c in original['result']['contributions']]
  key=object_hash(dict(basekey=basekey,prompt=prompt,version='multi-contribution-source-review-v1'))
  path='refinements/'+fid.replace(':','_')+'.json'
  if (W/path).exists() and load(path).get('inference_cache_key')==key:continue
  errors=[]
  for attempt in range(1,4):
   messages=[dict(role='system',content=prompt),dict(role='user',content=stable(dict(family_id=fid,title=doc['title'],abstract=doc['abstract'])))]
   if errors:messages.append(dict(role='user',content='契约错误：'+errors[-1][:800]))
   try:
    result,rid=extract.request('refine_extract',key,messages,EXTRACTION_WIRE_SCHEMA,attempt,conn)
    result=audit_wire_extraction(result,doc)
    transformed=load('responses/'+rid+'.canonical.json');result=apply_anchor_positions(result,transformed['source_anchor_lineage'],doc)
    for c in result['contributions']:
     c['refinement_provenance_json']=stable(dict(reason='Possible independent mechanisms found during source review',prior_contribution_ids=prior,original_result_path=state[2],second_look_is_not_independent_human_gold=True))
     c['semantic_validation_status']='LLM_REFINED_PENDING_SOURCE_AUDIT'
    validate(result,ENRICHED_SCHEMA)
    save(path,dict(cache_key=basekey,inference_cache_key=key,source_text_hash=doc['text_hash'],model=extract.MODEL,model_digest=extract.DIGEST,request_id=rid,prompt_sha256=digest_bytes(prompt.encode()),code_version=extract.CODE_VERSION,result=result,result_sha256=object_hash(result),refinement_origin='SOURCE_ONLY_LLM_SECOND_LOOK',adoption_status='PENDING_SOURCE_REVIEW',prior_contribution_ids=prior))
    event('family_refined',family_id=fid,original_contributions=len(prior),refined_contributions=len(result['contributions']));break
   except (ValueError,AssertionError,KeyError,TypeError) as e:
    errors.append(str(e))
    if 'rid' in locals():conn.execute('update requests set status=?,error=? where request_id=?',('VALIDATION_FAILED',str(e),rid));conn.commit()
  else:save('refinement_failures/'+fid.replace(':','_')+'.json',dict(errors=errors,status='FAILED_VALIDATION'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--family',nargs='+',required=True);a=p.parse_args()
 lock=(W/'state/worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);main(a.family)
