from common import *
from client import estimate
from metrics import collect_comparisons
from pipeline import prompt
import collections
import pyarrow as pa,pyarrow.parquet as pq

def main():
 guard();rows=pq.read_table(W/'D3_METRICS.parquet').to_pylist();rows=[r for r in rows if not r['metric'].startswith(('mean_known_usage_cost','calls_per_family'))];comparisons=collect_comparisons()
 names={'facts':'facts','organize':'organize','extract_only':'extract_only','audit':'audit','revision_audit':'audit','revision_2_audit':'audit','revision':'revise','revision_2':'revise','relevance':'relevance'};allowed={k:oh(prompt(v)) for k,v in names.items()};index=collections.defaultdict(list);bykey=collections.defaultdict(list)
 for p in (W/'responses').glob('*.receipt.json'):
  r=load(p);bykey[(r['kind'],r['cache_key'])].append(r)
  if r['kind'] in allowed:
   q=load('requests/'+r['request_id']+'.json')
   if q['fingerprint']['prompt_sha']==allowed[r['kind']]:index[(r['family_id'],r['kind'])].append(r)
 kinds={'D3_EXTRACT_ONLY':['extract_only'],'D3_FIDELITY':['facts','organize'],'D3_EVIDENCE':['facts','organize','audit','revision','revision_audit','revision_2','revision_2_audit'],'D3_FULL':['facts','organize','audit','revision','revision_audit','revision_2','revision_2_audit','relevance']}
 for split in ['development','holdout']:
  for scope in ['paired_full','paired_ablation']:
   required=['D2_ARCHIVED','D3_EVIDENCE'] if scope=='paired_full' else ['D2_ARCHIVED','D2_DEEPSEEK_REPLAY','D3_EXTRACT_ONLY','D3_FIDELITY','D3_EVIDENCE'];common=[r for r in comparisons if r['selection']['split']==split and (scope!='paired_ablation' or r['ablation']) and all(c in r['scores'] for c in required)];confs=['D2_ARCHIVED','D3_FIDELITY','D3_EVIDENCE','D3_FULL'] if scope=='paired_full' else required+['D3_FULL']
   for conf in confs:
    receipts=[];unknown_families=0
    for r in common:
     fid=r['selection']['family_id'];rr=[]
     if conf=='D2_DEEPSEEK_REPLAY':
      actual=load('working/d2_replay/'+fid.replace(':','_')+'.json');key=load('requests/'+actual['request_id']+'.json')['cache_key'];rr=bykey[('d2_prompt_replay',key)]
     elif conf in kinds:
      for k in kinds[conf]:rr+=index[(fid,k)]
     if any(x.get('usage') is None for x in rr):unknown_families+=1
     receipts+=rr
    seen={r['request_id']:r for r in receipts};receipts=list(seen.values());have=[r for r in receipts if r.get('usage')];cost=sum(estimate(r['usage']) or 0 for r in have);n=len(common)
    for name,num,den,unit in [('mean_known_usage_cost_usd_per_family',cost,n,'USD/family'),('mean_known_usage_cost_usd_per_response',cost,len(have),'USD/response'),('calls_per_family',len(receipts),n,'attempts/family')]:
     if conf=='D2_ARCHIVED':num=den=None
     rows.append(dict(scope=scope,split=split,configuration=conf,metric=name,numerator=num,denominator=den,value=num/den if den else None,label_tier='Measured usage' if conf!='D2_ARCHIVED' else 'N/A local cost unknown',sample_n=n,unknown_n=unknown_families,unit=unit,notes='Actual current-fingerprint receipt usage at published peak prices. Shared stages are allocated to each config; rows are NOT additive billed spend. Comparator/posthoc costs excluded here and listed in Usage. Missing usage has unknown cost. D2 archived local compute cost unavailable.'))
 pq.write_table(pa.Table.from_pylist(rows),W/'D3_METRICS.parquet',compression='zstd');w=load('working/WORKBOOK_DATA.json');w['metrics']=rows;save('working/WORKBOOK_DATA.json',w)
 p=W/'D3_EXPERIMENT_COMPARISON.md';text=p.read_text();text+='\n## 同源配置的实测调用成本\n\n| 分集 | 配置 | 已有usage峰时估算USD/族 | 调用尝试/族 |\n|---|---|---:|---:|\n'
 for split in ['development','holdout']:
  for conf in ['D2_ARCHIVED','D2_DEEPSEEK_REPLAY','D3_EXTRACT_ONLY','D3_FIDELITY','D3_EVIDENCE','D3_FULL']:
   costs=[r for r in rows if r['scope']=='paired_ablation' and r['split']==split and r['configuration']==conf];a=next(r for r in costs if r['metric']=='mean_known_usage_cost_usd_per_family');b=next(r for r in costs if r['metric']=='calls_per_family');text+='| '+split+' | '+conf+' | '+(f"{a['value']:.6f}" if a['value'] is not None else 'N/A')+' | '+(f"{b['value']:.2f}" if b['value'] is not None else 'N/A')+' |\n'
 p.write_text(text+'\n共享阶段只实际调用一次，按配置展示成本不能求和当账单。无usage尝试不假设免费，D2本地算力成本未知。\n');print('Added measured per-config call/cost metrics',len(rows))
if __name__=='__main__':main()
