from common import *
import urllib.request,urllib.error,re,uuid,ssl
MODEL='deepseek-flash';URL='https://api.deepseek.com/chat/completions'
MAX_ATTEMPTS=3;MAX_TOTAL_ATTEMPTS_PER_KEY=6;HTTP_TIMEOUT=150
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**kw):raise RuntimeError('Redirect forbidden')
# Standard verified TLS; operating-system VPN may route traffic; no custom endpoint.
OPENER=urllib.request.build_opener(NoRedirect())
_budget_lock=threading.Lock()
def read_key():
 key=os.environ.get('DEEPSEEK_API_KEY')
 if key:return key
 for p in [Path('/Volumes/Fuji_SSD_Work/runtime_secrets/deepseek.env')]:
  if not p.is_file():continue
  values={}
  for line in p.read_text().splitlines():
   m=re.fullmatch(r'\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*',line)
   if m:values[m[1].lower()]=m[2].strip().strip('\"\'')
  key=values.get('deepseek_api_key') or values.get('apikey') or values.get('api_key')
  if key:return key
 raise RuntimeError('DeepSeek credential unavailable; no values logged')
def validate(v,s,path='$'):
 types=s.get('type',[]);types=types if isinstance(types,list) else [types]
 valid={'object':isinstance(v,dict),'array':isinstance(v,list),'string':isinstance(v,str),'number':type(v) in [int,float],'integer':type(v) is int,'null':v is None,'boolean':type(v) is bool}
 if types and not any(valid.get(t,False) for t in types):raise ValueError(path+': wrong type')
 if 'enum' in s and v not in s['enum']:raise ValueError(path+': enum')
 if isinstance(v,dict):
  if set(s.get('required',[]))-set(v):raise ValueError(path+': missing '+str(sorted(set(s.get('required',[]))-set(v))))
  props=s.get('properties',{})
  if s.get('additionalProperties') is False and set(v)-set(props):raise ValueError(path+': extra '+str(sorted(set(v)-set(props))))
  for k,x in v.items():
   if k in props:validate(x,props[k],path+'.'+k)
 if isinstance(v,list):
  if not s.get('minItems',0)<=len(v)<=s.get('maxItems',100000):raise ValueError(path+': length')
  for i,x in enumerate(v):validate(x,s.get('items',{}),path+f'[{i}]')
 if isinstance(v,str) and not s.get('minLength',0)<=len(v)<=s.get('maxLength',100000):raise ValueError(path+': length')
def estimate(usage):
 if not usage:return None
 inp=usage.get('prompt_tokens');out=usage.get('completion_tokens')
 if inp is None or out is None:return None
 hit=usage.get('prompt_cache_hit_tokens',0);miss=usage.get('prompt_cache_miss_tokens',max(0,inp-hit))
 # Published peak USD rates form a conservative upper estimate; not billing receipt.
 return (hit*.006+miss*.30+out*1.2)/1e6

def call(kind,fid,prompt,payload,schema,validator=None,max_tokens=7500):
 fingerprint=dict(model=MODEL,prompt_sha=oh(prompt),schema_sha=oh(schema),input_sha=oh(payload),max_tokens=max_tokens,thinking='disabled',temperature=0)
 key=oh(fingerprint);cp=W/'cache'/kind/(key+'.json')
 if cp.exists():
  r=json.loads(cp.read_text());validate(r['result'],schema)
  if validator:validator(r['result'])
  return r
 messages=[dict(role='system',content=prompt+'\n只输出 JSON，结构如下：'+stable(schema)),dict(role='user',content=stable(payload))]
 previous=[p.stem for p in (W/'responses').glob(kind+'_'+key[:16]+'_*.receipt.json')]
 remaining=MAX_TOTAL_ATTEMPTS_PER_KEY-len(previous)
 if remaining<=0:raise RuntimeError('Terminal task: six total attempts already exhausted; no silent unbounded retry')
 for n in range(1,min(MAX_ATTEMPTS,remaining)+1):
  # Never loop indefinitely on service failures. A resumed run may explicitly retry terminal tasks.
  rid=kind+'_'+key[:16]+'_'+uuid.uuid4().hex[:8]
  body=dict(model=MODEL,messages=messages,thinking=dict(type='disabled'),temperature=0,response_format=dict(type='json_object'),stream=False,max_tokens=max_tokens)
  with _budget_lock:
   ledgers=list((W/'responses').glob('*.receipt.json'))
   if len(ledgers)>=12000:raise RuntimeError('Safety stop at 12000 response attempts; inspect scope')
   # Main bounded D3 plan; budget ledger is reconstructed from real receipts.
   if len(ledgers)%100==0:
    cost=sum(estimate(json.loads(p.read_text()).get('usage')) or 0 for p in ledgers)
    if cost>30:raise RuntimeError('Conservative USD30 safety stop; not user spend permission limit')
  save('requests/'+rid+'.json',dict(at=now(),request_id=rid,kind=kind,family_id=fid,cache_key=key,attempt=n,fingerprint=fingerprint,endpoint=URL,payload=body,code_snapshot=snapshot()))
  t=time.monotonic();receipt=dict(request_id=rid,kind=kind,family_id=fid,cache_key=key,attempt=n,started_at=now(),status='RUNNING',usage=None)
  try:
   req=urllib.request.Request(URL,data=stable(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+read_key()},method='POST')
   with OPENER.open(req,timeout=HTTP_TIMEOUT) as response:raw=json.load(response)
   save('responses/'+rid+'.raw.json',raw);receipt.update(actual_model=raw.get('model'),usage=raw.get('usage'),api_id=raw.get('id'))
   assert raw.get('choices'),'No choices'
   choice=raw['choices'][0]
   assert choice.get('finish_reason')=='stop','Incomplete finish_reason: '+str(choice.get('finish_reason'))
   content=choice.get('message',{}).get('content');assert content,'Empty JSON output'
   syntax_changes=[]
   try:value=json.loads(content)
   except json.JSONDecodeError:
    repaired=content
    # Exact whitelist paths from input only: insert a missing closing JSON quote.
    # No textual claims/grades/IDs are changed; raw remains immutable.
    for claim in payload.get('claims',[]):
     path=claim['path'];bad='"path":"'+path+',"grade":';good='"path":"'+path+'","grade":'
     if bad in repaired:
      repaired=repaired.replace(bad,good);syntax_changes.append(dict(rule='close_known_claim_path_quote',path=path))
    if not syntax_changes:raise
    value=json.loads(repaired)
    save('responses/'+rid+'.syntax_normalization.json',dict(rules=syntax_changes,raw_content_sha256=oh(content),normalized_content_sha256=oh(repaired),result=value,semantics_changed=False))
   validate(value,schema)
   if validator:validator(value)
   receipt.update(status='VALID',finished_at=now(),wall_s=round(time.monotonic()-t,3),peak_cost_usd_upper_estimate=estimate(receipt['usage']))
   save('responses/'+rid+'.receipt.json',receipt)
   result=dict(result=value,request_id=rid,cache_key=key,fingerprint=fingerprint,actual_model=raw.get('model'),usage=raw.get('usage'),prior_failed_requests=previous,syntax_normalization=syntax_changes,created_at=now())
   save(cp,result);return result
  except urllib.error.HTTPError as e:
   # Do not log potentially reflected authorization or unbounded server body.
   receipt.update(status='HTTP_ERROR',error='HTTP '+str(e.code),http_status=e.code)
   terminal=e.code in [400,401,402,403,404]
  except Exception as e:
   receipt.update(status='VALIDATION_OR_NETWORK_FAILURE',error=type(e).__name__+': '+str(e)[:1200]);terminal=False
  receipt.update(finished_at=now(),wall_s=round(time.monotonic()-t,3),peak_cost_usd_upper_estimate=estimate(receipt.get('usage')))
  save('responses/'+rid+'.receipt.json',receipt);previous.append(rid)
  if terminal:raise RuntimeError(receipt['error'])
  if n<MAX_ATTEMPTS:
   messages=[dict(role='system',content=prompt+'\n只输出 JSON，结构如下：'+stable(schema)+'\n上次未通过确定性验证：'+receipt['error']+'。修正结构/引用，勿添加来源没有的技术。'),dict(role='user',content=stable(payload))]
   time.sleep(min(2*n,6))
 raise RuntimeError('Model output failed after bounded attempts; '+str(previous))
