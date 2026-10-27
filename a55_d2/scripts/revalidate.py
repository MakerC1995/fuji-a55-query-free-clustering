"""Revalidate already generated responses without repeating model inference."""
from common import *
import extract
from schema import *
import pandas as pd
def main():
 guard();require_unfrozen();extract.freeze_code();conn=state_db();prompt=(W/'prompts/extraction_v2.txt').read_text()
 docs={d['family_id']:d for d in pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet').to_dict('records')}
 already=set();passed=[];rejected=[]
 conn.execute('create table if not exists validation_replays(request_id TEXT,validation_code_version TEXT,cache_key TEXT,status TEXT,error TEXT,at TEXT,PRIMARY KEY(request_id,validation_code_version))');conn.commit()
 for rid, in conn.execute("select request_id from requests where kind='extract' order by started_at").fetchall():
  rp=W/'responses'/f'{rid}.raw.json';ip=W/'requests'/f'{rid}.input.json'
  if not rp.exists():continue
  req=json.loads(ip.read_text());payload=req['payload']
  is_native=isinstance(payload['format'],dict) and object_hash(payload['format'])==object_hash(EXTRACTION_WIRE_SCHEMA) and payload['messages'][0]['content']==prompt
  is_fallback=payload['format']=='json' and payload['messages'][0]['content'].startswith(prompt) and json.dumps(EXTRACTION_WIRE_SCHEMA,ensure_ascii=False) in payload['messages'][0]['content']
  is_anchor=req.get('transport')=='source_span_ids_v1' and payload['messages'][0]['content'].startswith(prompt)
  if payload['model']!=extract.MODEL or not (is_native or is_fallback or is_anchor):continue
  body=req['canonical_source_input'] if is_anchor else json.loads(payload['messages'][1]['content']);fid=body['family_id']
  if fid in already:continue
  d=docs[fid];assert body==dict(family_id=fid,title=d['title'],abstract=d['abstract'])
  raw=json.loads(rp.read_text())
  try:
   assert raw.get('done') and raw.get('done_reason')!='length'
   if is_anchor:
    transformed_path=W/'responses'/f'{rid}.canonical.json'
    if transformed_path.exists():
     transformed=load(str(transformed_path));assert transformed['result_sha256']==object_hash(transformed['result'])
    else:
     model_result=json.loads(raw['message']['content'])
     rebuilt,lineage=canonical_from_source_ids(model_result,payload['format'] if isinstance(payload['format'],dict) else source_id_schema(EXTRACTION_WIRE_SCHEMA,req['source_spans']),req['source_spans'])
     transformed=dict(result=rebuilt,source_anchor_lineage=lineage,result_sha256=object_hash(rebuilt))
    result=audit_wire_extraction(transformed['result'],d);result=apply_anchor_positions(result,transformed['source_anchor_lineage'],d)
   else:result=audit_wire_extraction(json.loads(raw['message']['content']),d)
  except (ValueError,AssertionError,KeyError,TypeError) as e:
   rejected.append(dict(request_id=rid,family_id=fid,error=str(e)))
   conn.execute('insert or replace into validation_replays values(?,?,?,?,?,?)',(rid,extract.CODE_VERSION,extract.key_for(d,prompt),'FAILED',str(e),now()));conn.commit();continue
  key=extract.key_for(d,prompt);path='extractions/'+fid.replace(':','_')+'.json'
  attempts=conn.execute('select count(*) from requests where cache_key=?',(req['cache_key'],)).fetchone()[0]
  save(path,dict(cache_key=key,source_request_cache_key=req['cache_key'],model=extract.MODEL,model_digest=extract.DIGEST,prompt_sha256=digest_bytes(prompt.encode()),schema_sha256=object_hash(ENRICHED_SCHEMA),wire_schema_sha256=object_hash(EXTRACTION_WIRE_SCHEMA),source_text_hash=d['text_hash'],request_id=rid,validated_at=now(),code_version=extract.CODE_VERSION,generation_code_version=req.get('code_version','not_snapshotted_for_early_draft'),offline_validation_replay=True,transport_protocol=req.get('transport') or 'legacy_model_quotes',generation_prompt_sha256=digest_bytes(payload['messages'][0]['content'].encode()),result_sha256=object_hash(result),result=result))
  conn.execute('insert or replace into extraction values(?,?,?,?,?,?,?)',(fid,key,'VALID',path,attempts,now(),None))
  conn.execute('insert or replace into validation_replays values(?,?,?,?,?,?)',(rid,extract.CODE_VERSION,key,'PASS',None,now()));conn.commit();already.add(fid)
  passed.append(dict(family_id=fid,request_id=rid,contributions=len(result['contributions']),explicit_mechanisms=sum(c['evidence_level']=='EXPLICIT_MECHANISM' for c in result['contributions']),field_gap_count=sum(len(c['field_evidence_gaps']) for c in result['contributions'])))
 save('evidence/OFFLINE_VALIDATION_REPLAY.json',dict(at=now(),actual_new_inference_requests=0,lossless_long_quote_splitting=True,selection_policy='Earliest response passing current schema/literal rules for identical source, prompt, wire schema and locked model; no semantic cherry-picking',passed=passed,rejected=rejected))
 for name,sch in [('EXTRACTION_WIRE_SCHEMA.json',EXTRACTION_WIRE_SCHEMA),('PATENT_CONTRIBUTIONS_SCHEMA.json',ENRICHED_SCHEMA)]:save('configs/'+name,sch)
 event('offline_replay_completed',new_inferences=0,passed=passed,rejected=len(rejected))
if __name__=='__main__':main()
