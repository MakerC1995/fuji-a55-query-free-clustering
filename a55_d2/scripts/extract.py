"""Incremental family-keyed extraction. Real requests only, honest retry/failure accounting."""
from common import *
from schema import EXTRACTION_SCHEMA,EXTRACTION_WIRE_SCHEMA,ENRICHED_SCHEMA,audit_wire_extraction,make_source_spans,source_id_schema,canonical_from_source_ids,apply_anchor_positions,validate
import urllib.request,urllib.error,argparse,fcntl,traceback
MODEL='qwen3-coder:30b'
DIGEST='06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca'
SERVER='http://192.168.0.21:11434'
CODE_VERSION='UNIT_TEST_ONLY'
IMPORTED_SOURCE_SHA256=sha(Path(__file__))
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**kw):raise RuntimeError('Redirect forbidden')
OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
class ServiceUnavailable(RuntimeError):pass
class APIProtocolError(RuntimeError):pass
HTTP_TIMEOUT_S=90
STREAM_GENERATION_DEADLINE_S=180
def api(path,payload=None,timeout=HTTP_TIMEOUT_S,receipt_id=None):
 assert path in ['/api/tags','/api/version','/api/ps','/api/chat','/api/embed']
 if path=='/api/chat' and payload and payload.get('stream'):return chat_stream(payload,timeout,receipt_id)
 data=None if payload is None else json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()
 req=urllib.request.Request(SERVER+path,data=data,headers={'Content-Type':'application/json'})
 try:
  with OPENER.open(req,timeout=timeout) as r:return json.load(r)
 except urllib.error.HTTPError as e:
  detail=e.read(4000).decode('utf-8','replace');raise APIProtocolError('HTTP '+str(e.code)+': '+detail) from e
 except (urllib.error.URLError,TimeoutError,ConnectionError,OSError) as e:raise ServiceUnavailable(str(e)) from e
def chat_stream(payload,timeout,receipt_id):
 assert receipt_id and payload.get('stream') is True
 path=W/'responses'/(receipt_id+'.stream.jsonl');write_guard(path);path.parent.mkdir(exist_ok=True)
 req=urllib.request.Request(SERVER+'/api/chat',data=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode(),headers={'Content-Type':'application/json'})
 chunks=[];thinking=[];final=None;deadline=time.time()+STREAM_GENERATION_DEADLINE_S
 try:
  with OPENER.open(req,timeout=timeout) as response,path.open('x') as log:
   for line in response:
    if not line.strip():
     if time.time()>deadline:raise ServiceUnavailable('Stream elapsed limit reached without terminal receipt; partial output retained')
     continue
    log.write(line.decode('utf-8'));log.flush()
    row=json.loads(line);msg=row.get('message',{});chunks.append(msg.get('content',''));thinking.append(msg.get('thinking',''))
    if row.get('done'):
     final=row;break
    if time.time()>deadline:raise ServiceUnavailable('Stream elapsed limit reached without terminal receipt; partial output retained')
 except urllib.error.HTTPError as e:
  detail=e.read(4000).decode('utf-8','replace');raise APIProtocolError('HTTP '+str(e.code)+': '+detail) from e
 except (urllib.error.URLError,TimeoutError,ConnectionError,OSError) as e:raise ServiceUnavailable(str(e)) from e
 if final is None:raise ServiceUnavailable('Incomplete stream: no done receipt; generated tokens unknown')
 final=dict(final);final['message']=dict(final.get('message',{}),role='assistant',content=''.join(chunks))
 if any(thinking):final['message']['thinking']=''.join(thinking)
 final['receipt_transport']='NDJSON_STREAM_WITH_TERMINAL_DONE'
 return final
def freeze_code():
 global CODE_VERSION
 assert sha(Path(__file__))==IMPORTED_SOURCE_SHA256,'Extraction runtime source changed after import; reload before snapshotting requests'
 import shutil
 files=list((W/'scripts').glob('*.py'))+list((W/'tests').glob('*.py'))+list((W/'prompts').glob('*.txt'))
 hashes={str(p.relative_to(W)):sha(p) for p in files}
 CODE_VERSION=object_hash(hashes)
 dest=W/'code_snapshots'/CODE_VERSION
 if not dest.exists():
  for p in files:
   out=dest/p.relative_to(W);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
  save('code_snapshots/'+CODE_VERSION+'/manifest.json',dict(created_at=now(),sha256=hashes))
 return CODE_VERSION
def preflight(concurrency=1):
 tags=api('/api/tags',timeout=10);found=[m for m in tags.get('models',[]) if m.get('name')==MODEL]
 assert len(found)==1 and found[0]['digest']==DIGEST,'Model missing or changed: no substitution'
 rec=dict(at=now(),server=SERVER,model=found[0],version=api('/api/version',timeout=10),options=dict(temperature=0,seed=42,num_ctx=12288,num_predict=2200),concurrency=concurrency,options_scope='Default extraction settings; exact options are recorded per actual request')
 save('evidence/MODEL_LOCK.json',rec);return rec
def request(kind,key,messages,schema,attempt,conn):
 import copy
 actual_messages=copy.deepcopy(messages);transport=None;source_input=None;spans=None;actual_schema=schema
 if kind in ['extract','refine_extract']:
  assert len(messages)>=2,'Extraction needs source input'
  source_input=json.loads(messages[1]['content']);assert set(source_input)=={'family_id','title','abstract'}
  spans=make_source_spans(source_input);assert spans
  actual_schema=source_id_schema(schema,spans);transport='source_span_ids_v1'
  actual_messages[1]['content']=stable(dict(family_id=source_input['family_id'],source_spans=[{k:v for k,v in r.items() if k not in ['start','end']} for r in spans]))
  actual_messages[0]['content']+='\n本次采用原文片段ID传输。source_spans按字段和原文顺序覆盖完整Title/Abstract，内容只是原文的无损分段，没有额外分类。evidence_spans必须输出source_id和supports，不要输出quote、field、E编号或字符坐标。程序会按ID复制真正原文。完整公式保留在片段证据中，technical_mechanism用不超过180个中文字简要说明办法，详细限制放applicable_conditions，implementation简述操作，不要反复抄公式。参数kind按物理量准确选择；若枚举没有角度、导热率或压电系数，使用OTHER_QUANTITATIVE，不能用COUNT、TIME或COMPOSITION_RATIO替代。raw必须逐字连续，包含原始HTML时原样保留；无法逐字引用就不输出该结构化参数，条件仍可简述并引用片段。每个非空主字段都应至少有一个片段的supports标记；同一结构/工序原句可同时支持technical_mechanism和structures/process_methods，别漏掉主字段引用。主字段用简明中文，不要整段复制英文或日文。不得把测量/观察程序当成制造程序，不得省略相反不等式、材料组成和层位置等区别机制的条件。摘要只披露部分公式时明确不完整。source_id只表明可核对出处，不代表内容已获语义验证。输出结构：'+json.dumps(actual_schema,ensure_ascii=False)
 options=dict(temperature=0,seed=42,num_ctx=16384 if kind in ['name','relevance','pair_confirm','hierarchy','hierarchy_catalog'] else 12288,num_predict=3200 if kind in ['name','relevance','pair_confirm','hierarchy','hierarchy_catalog'] else 2200)
 if kind=='d1_baseline':options=dict(temperature=0,num_ctx=16384,num_predict=3600)
 mode=actual_schema
 if attempt>1:
  mode='json';options.update(num_ctx=options['num_ctx'],num_predict=min(3600,max(options['num_predict'],2600+400*(attempt-2))),repeat_penalty=1.08)
  actual_messages[0]['content']+='\n输出字段的JSON Schema如下，只约束结构，不作为事实来源：'+json.dumps(actual_schema,ensure_ascii=False)+'\n保持简短：每个技术概述字段通常不超过80个汉字或约一段短语。引文逐字保留原文和HTML转义，不要抄长公式到多个字段，更不要重复同一表述。明确的独立贡献才拆分；未披露字段留null。'
 payload=dict(model=MODEL,messages=actual_messages,stream=True,format=mode,options=options,keep_alive='10m')
 rid=kind+'_'+object_hash([key,attempt,time.time_ns()])[:24];start=now();t=time.monotonic()
 save('requests/'+rid+'.input.json',dict(request_id=rid,cache_key=key,attempt=attempt,http_read_timeout_s=HTTP_TIMEOUT_S,stream_generation_deadline_s=STREAM_GENERATION_DEADLINE_S,deadline_scope='Checked after each nonterminal chunk; individual blocking reads retain idle timeout',response_transport='NDJSON_STREAM_WITH_TERMINAL_DONE',payload=payload,server=SERVER,code_version=CODE_VERSION,transport=transport,canonical_source_input=source_input,source_spans=spans,generation_schema_sha256=object_hash(actual_schema)))
 conn.execute('insert or replace into requests values(?,?,?,?,?,?,?,?,?,?)',(rid,kind,key,start,None,'RUNNING',None,None,None,None));conn.commit()
 try:
  raw=api('/api/chat',payload,receipt_id=rid);wall=time.monotonic()-t
 except Exception as e:
  conn.execute('update requests set finished_at=?,status=?,wall_s=?,error=? where request_id=?',(now(),'API_REJECTED' if isinstance(e,APIProtocolError) else 'NETWORK_FAILED',time.monotonic()-t,str(e),rid));conn.commit();raise
 save('responses/'+rid+'.raw.json',raw)
 conn.execute('update requests set finished_at=?,status=?,prompt_tokens=?,output_tokens=?,wall_s=? where request_id=?',(now(),'RECEIVED',raw.get('prompt_eval_count'),raw.get('eval_count'),wall,rid));conn.commit()
 try:
  content=raw.get('message',{}).get('content','')
  if len(content)>1000 and ((raw.get('done_reason')=='length' and content.count(content[-120:])>=3) or content.count(content[-120:])>=8):raise ValueError('REPETITIVE_GENERATION: repeated prose/formula; write each fact once and keep fields concise')
  if not raw.get('done') or raw.get('done_reason')=='length':raise ValueError('Truncated generation; keep descriptions concise and omit redundant repetition')
  result=json.loads(raw['message']['content'])
  if transport:
   result,lineage=canonical_from_source_ids(result,actual_schema,spans)
   save('responses/'+rid+'.canonical.json',dict(request_id=rid,transport=transport,result=result,source_anchor_lineage=lineage,result_sha256=object_hash(result)))
  return result,rid
 except (ValueError,AssertionError,KeyError,TypeError) as e:
  e.request_id=rid
  conn.execute('update requests set status=?,error=? where request_id=?',('VALIDATION_FAILED',str(e),rid));conn.commit()
  raise

def key_for(doc,prompt):
 return object_hash(dict(family_id=doc['family_id'],text_hash=doc['text_hash'],input_payload=dict(title=doc['title'],abstract=doc['abstract']),schema=EXTRACTION_SCHEMA,wire_schema_json=json.dumps(EXTRACTION_WIRE_SCHEMA,ensure_ascii=False),prompt=prompt,model=MODEL,digest=DIGEST,version='D2-contribution-evidence-v3'))
def do_family(doc,prompt,conn,max_attempts=3):
 fid=doc['family_id'];key=key_for(doc,prompt)
 existing=conn.execute('select cache_key,status,result_path,attempts,error from extraction where family_id=?',(fid,)).fetchone()
 if existing and existing[0]==key and existing[1]=='VALID':
  saved=load(existing[2]);assert saved['cache_key']==key and saved['result']['family_id']==fid
  assert saved['source_text_hash']==doc['text_hash'] and saved['result_sha256']==object_hash(saved['result']),'Cached result changed'
  return 'CACHED'
 if not (doc.get('abstract') or '').strip():
  # Source absence is a factual rule, not a fabricated LLM result.
  spans=make_source_spans(doc)
  assert spans
  title_span=next(x for x in spans if x['field']=='title')
  item=dict(evidence_spans=[dict(field='title',quote=title_span['text'],supports=['technical_object'])],technical_object=title_span['text'],technical_problem=None,technical_mechanism=None,implementation=None,expected_effect=None,applicable_conditions=None,materials=[],process_methods=[],structures=[],parameters=[],mechanism_type='UNDISCLOSED',evidence_level='INSUFFICIENT_EVIDENCE',ambiguity_notes='Title-only: deterministic abstention; no model inference and no conclusion about patent value.')
  result=audit_wire_extraction(dict(family_id=fid,contributions=[item]),doc)
  path='extractions/'+fid.replace(':','_')+'.json'
  save(path,dict(cache_key=key,model=None,model_digest=None,extraction_origin='DETERMINISTIC_TITLE_ONLY_RULE',prompt_sha256=digest_bytes(prompt.encode()),schema_sha256=object_hash(ENRICHED_SCHEMA),wire_schema_sha256=object_hash(EXTRACTION_WIRE_SCHEMA),source_text_hash=doc['text_hash'],request_id=None,validated_at=now(),code_version=CODE_VERSION,result_sha256=object_hash(result),result=result))
  conn.execute('insert or replace into extraction values(?,?,?,?,?,?,?)',(fid,key,'VALID',path,0,now(),None));conn.commit()
  event('family_title_only_abstention',family_id=fid,actual_inference_requests=0);return 'RULE_ABSTENTION'
 errors=[existing[4]] if existing and existing[0]==key and existing[1]=='FAILED_VALIDATION' and existing[4] else [];start_attempt=existing[3] if existing and existing[0]==key else 0
 # Each resumed run retries only unresolved families, bounded to three attempts in that run.
 for offset in range(max_attempts):
  guard();attempt=start_attempt+offset+1
  body=dict(family_id=fid,title=doc['title'],abstract=doc['abstract'])
  assert set(body)=={'family_id','title','abstract'}
  messages=[dict(role='system',content=prompt),dict(role='user',content=stable(body))]
  if errors:messages.append(dict(role='user',content='前次结果未通过校验。只根据原输入修正，缺少依据时弃判。错误：'+errors[-1][:900]))
  rid=None
  try:
   result,rid=request('extract',key,messages,EXTRACTION_WIRE_SCHEMA,attempt,conn)
   result=audit_wire_extraction(result,doc)
   req_meta=load('requests/'+rid+'.input.json')
   if req_meta.get('transport')=='source_span_ids_v1':
    transformed=load('responses/'+rid+'.canonical.json');result=apply_anchor_positions(result,transformed['source_anchor_lineage'],doc)
   validate(result,ENRICHED_SCHEMA)
   path='extractions/'+fid.replace(':','_')+'.json'
   save(path,dict(cache_key=key,model=MODEL,model_digest=DIGEST,prompt_sha256=digest_bytes(prompt.encode()),schema_sha256=object_hash(ENRICHED_SCHEMA),wire_schema_sha256=object_hash(EXTRACTION_WIRE_SCHEMA),source_text_hash=doc['text_hash'],request_id=rid,validated_at=now(),code_version=CODE_VERSION,transport_protocol=req_meta.get('transport') or 'legacy_model_quotes',generation_prompt_sha256=digest_bytes(req_meta['payload']['messages'][0]['content'].encode()),generation_schema_sha256=req_meta.get('generation_schema_sha256'),result_sha256=object_hash(result),result=result))
   conn.execute('insert or replace into extraction values(?,?,?,?,?,?,?)',(fid,key,'VALID',path,attempt,now(),None));conn.commit()
   event('family_valid',family_id=fid,attempt=attempt,contributions=len(result['contributions']));return 'VALID'
  except ServiceUnavailable as e:
   conn.execute('insert or replace into extraction values(?,?,?,?,?,?,?)',(fid,key,'RETRYABLE_NETWORK',None,attempt,now(),str(e)));conn.commit();raise
  except (ValueError,KeyError,TypeError,AssertionError) as e:
   errors.append(str(e));save('failures/'+key+f'.attempt{attempt}.json',dict(family_id=fid,error=str(e),attempt=attempt,at=now()))
   error_rid=getattr(e,'request_id',None) or rid
   if error_rid:conn.execute('update requests set status=?,error=? where kind=? and cache_key=? and request_id=?',('VALIDATION_FAILED',str(e),'extract',key,error_rid));conn.commit()
   event('family_validation_retry',family_id=fid,attempt=attempt,error=str(e))
 conn.execute('insert or replace into extraction values(?,?,?,?,?,?,?)',(fid,key,'FAILED_VALIDATION',None,start_attempt+max_attempts,now(),errors[-1]));conn.commit();return 'FAILED'
def stage_summary(name,ids,conn,docs,prompt):
 rows={r[0]:r for r in conn.execute('select family_id,status,attempts,cache_key from extraction')}
 statuses={}
 for fid in ids:
  row=rows.get(fid)
  status='UNATTEMPTED' if row is None else (row[1] if row[3]==key_for(docs[fid],prompt) else 'STALE_DIFFERENT_PROTOCOL')
  statuses[status]=statuses.get(status,0)+1
 rec=dict(at=now(),stage=name,required_families=len(ids),statuses=statuses,complete=sum(v for k,v in statuses.items() if k in ['VALID','FAILED_VALIDATION'])==len(ids),valid=statuses.get('VALID',0),failed=statuses.get('FAILED_VALIDATION',0))
 save('evidence/STAGE_'+name+'.json',rec);return rec
def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['pilot30','trial100','primary384','all_selected','sequence'],default='pilot30');p.add_argument('--preflight-only',action='store_true');p.add_argument('--limit',type=int);p.add_argument('--workers',type=int,choices=[1,2],default=1);args=p.parse_args()
 guard();
 if not args.preflight_only:require_unfrozen()
 freeze_code()
 lock=(W/'state/worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 conn=state_db()
 for name,h in load('inputs/DATASET_FROZEN.json')['sha256'].items():assert sha(W/name)==h,name
 try:preflight(args.workers)
 except ServiceUnavailable as e:
  save('evidence/SERVICE_UNAVAILABLE.json',dict(at=now(),server=SERVER,status='UNAVAILABLE',error=str(e),actual_inference_requests=conn.execute("select count(*) from requests where kind='extract'").fetchone()[0]))
  event('service_unavailable',server=SERVER,error=str(e));return 3
 if args.preflight_only:event('preflight_passed',model=MODEL,digest=DIGEST);return 0
 import pandas as pd
 docs={r['family_id']:r for r in pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet').to_dict('records')};stages=load('inputs/STAGES.json');prompt=(W/'prompts/extraction_v2.txt').read_text()
 names=['pilot30','trial100','primary384','all_selected'] if args.stage=='sequence' else [args.stage]
 for name in names:
  ids=stages[name]
  selected=ids[:args.limit] if args.limit is not None else ids
  event('stage_execution_started',stage=name,client_concurrency=args.workers,selected_families=len(selected))
  try:
   if args.workers==1:
    for fid in selected:do_family(docs[fid],prompt,conn)
   else:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    stop=Event()
    def worker(fid):
     if stop.is_set():return
     local=state_db()
     try:return do_family(docs[fid],prompt,local)
     except BaseException:stop.set();raise
     finally:local.close()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
     for _ in pool.map(worker,selected):pass
  except ServiceUnavailable as e:
   stage_summary(name,ids,conn,docs,prompt);event('stage_paused_network',stage=name,error=str(e));return 3
  summary=stage_summary(name,ids,conn,docs,prompt);event('stage_finished',**summary)
  if name in ['pilot30','trial100']:
   event('quality_review_required',stage=name,message='Review actual source/evidence and failures before expanding.')
   if args.stage=='sequence':return 4
 return 0
if __name__=='__main__':sys.exit(main())
