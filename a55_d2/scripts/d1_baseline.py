"""D1-style control calls and fair structural comparison, after core freeze only."""
from common import *
from posthoc_relevance import verify_freeze
import extract,collections
def check(result,docs):
 assert isinstance(result,dict) and isinstance(result.get('themes'),list)
 by={d['family_id']:d for d in docs};bad=[]
 for i,t in enumerate(result['themes']):
  valid=[]
  for e in t.get('evidence',[]):
   if e.get('family_id') in by and e.get('field','abstract') in ['title','abstract'] and e.get('quote') and e['quote'] in by[e['family_id']][e.get('field','abstract')]:valid.append(e)
   else:bad.append(dict(theme=i,evidence=e))
  t['verified_evidence']=valid;t['verified_family_count']=len({e['family_id'] for e in valid});t['unique_supporting_texts']=len({object_hash(dict(title=by[e['family_id']]['title'],abstract=by[e['family_id']]['abstract'])) for e in valid})
  if t['verified_family_count']<3:t['unverified_name']=t.get('name');t['name']='无法确定';t['confidence']='insufficient'
  t['evidence_validation']='PASS' if t['verified_family_count']>=3 and not bad else 'REVIEW_REQUIRED'
 return result,bad
def main():
 guard();freeze=verify_freeze();extract.freeze_code();extract.preflight();conn=state_db();data=load('working/D1_BASELINE_PANELS.json');system=(W/'prompts/d1_baseline.txt').read_text().rstrip('\n');results=[]
 for p in data['panels']:
  key=object_hash(dict(panel=p,prompt=system,model=extract.DIGEST,options=dict(temperature=0,num_ctx=16384,num_predict=3600),phase='POST_FREEZE_D1_STYLE_REPLICATION'));path=W/'d1_baseline'/(key+'.json')
  if path.exists():
   saved=load(str(path));assert saved['result_sha256']==object_hash(saved['result']);results.append(saved);continue
  errors=[];success=False
  for attempt in range(1,4):
   messages=[dict(role='system',content=system),dict(role='user',content=stable(p))]
   if errors:messages.append(dict(role='user',content='仅修复JSON格式：'+errors[-1][:500]))
   rid=None
   try:
    raw,rid=extract.request('d1_baseline',key,messages,'json',attempt,conn);result,bad=check(raw,p['docs']);saved=dict(selection_id=p['selection_id'],result=result,result_sha256=object_hash(result),invalid_evidence=bad,request_id=rid,cache_key=key,phase='POST_FREEZE_D1_STYLE_REPLICATION');save(str(path),saved);results.append(saved);success=True;break
   except (ValueError,AssertionError,KeyError,TypeError,extract.ServiceUnavailable) as e:
    errors.append(str(e))
    if isinstance(e,extract.ServiceUnavailable):extract.preflight();continue
    error_rid=getattr(e,'request_id',None) or rid
    if error_rid:conn.execute('UPDATE requests SET status=?,error=? WHERE request_id=?',('VALIDATION_FAILED',str(e),error_rid));conn.commit()
  if not success:results.append(dict(selection_id=p['selection_id'],status='FAILED_VALIDATION',errors=errors,result=dict(themes=[]),request_id=None))
  event('d1_style_control_complete',selection_id=p['selection_id'],success=success)
 kb=load('working/all_selected/KB_RECORDS.json');cs=load('working/all_selected/contributions.json');mapping=kb['cluster_technology'];byselection={r['selection_id']:r for r in results};rows=[]
 import pandas as pd
 members=pd.read_parquet(W/'inputs/CLUSTER_MEMBERS.parquet')
 for p in data['panels']:
  r=byselection[p['selection_id']];themes=r['result'].get('themes',[]);fids=set(members[members.selection_id==p['selection_id']].family_id);contributions=[c for c in cs if c['family_id'] in fids];tech={m['technology_id'] for m in mapping if m['selection_id']==p['selection_id']}
  rows.append([p['selection_id'],p['cluster_population'],p['selected_pool'],len(p['docs']),' / '.join(t.get('name','未返回') for t in themes) or '调用失败/无主题',sum(t.get('name') not in ['无法确定',None] for t in themes),sum(t.get('evidence_validation')=='PASS' for t in themes),len(tech),len({c['family_id'] for c in contributions if c['evidence_level']=='EXPLICIT_MECHANISM'}),sum(c['evidence_level']!='EXPLICIT_MECHANISM' for c in contributions),'是' if r['result'].get('needs_split') else '否/未报告'])
 method="""实际D1代码不是每群只有一个名称：它允许1至3个主题，要求原文引句，允许无法确定，也已有独立于Cluster的Technology散列ID和Cluster/Patent多对多表。D1以名称、对象、手段的字符串散列合并记录，尚无D2的逐族贡献层、源文坐标及双侧机制等价审计。
本对照复刻的是D1群级命名与逐字引文检查阶段，未复制D1后来另做的助手语义审计，不能将它当作旧D1完整最终审定结果。
本表是核心冻结之后、同一30B模型上新做的D1式对照，复用原SYSTEM、最多8个中心/边缘/随机/多样代表、摘要前1200字符和原逐字引文检查。不是冒充D1历史结果。部分控制池仅为本轮抽样；Noise原方法不命名，这里采用冻结60族中的均匀8族作为明确适配。
D2阅读更多原文、允许单源机制候选并有助手修订；D1门槛至少3个Family ID，原文重复另计。两种不确定率和节点数单位不同，不能直接比较准确率。表中D1引文PASS仅为字面匹配，不是语义正确。D2多节点不等于真实技术拆分率；当前没有独立人类Gold、同成本精确率或全量机制Recall。D2的价值首先在可逐族追溯、保留不同限定及机制关系审计。实际调用成本含所有失败和重试，详见Manifest。
"""
 allthemes=[t for r in results for t in r['result'].get('themes',[])]
 named=[t for t in allthemes if t.get('name') not in [None,'无法确定']]
 identities=[hashlib.sha256(json.dumps([t.get('name'),t.get('object'),t.get('means')],ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:12] for t in named]
 mechanism_nodes=[t for t in kb['concepts'] if t['level']=='B']
 operational=dict(
  d1=dict(input_family_appearances=sum(len(p['docs']) for p in data['panels']),unique_input_families=len({d['family_id'] for p in data['panels'] for d in p['docs']}),theme_records=len(allthemes),named_theme_records=len(named),literal_evidence_references=sum(len(t.get('evidence',[])) for t in allthemes),literal_verified_references=sum(len(t.get('verified_evidence',[])) for t in allthemes),themes_with_nonempty_means=sum(bool(t.get('means')) for t in allthemes),insufficient_theme_records=sum(t.get('name')=='无法确定' for t in allthemes),exact_string_duplicate_named_records=len(identities)-len(set(identities)),panels_suggested_split=sum(bool(r['result'].get('needs_split')) for r in results)),
  d2=dict(input_families=1117,contribution_or_abstention_records=len(cs),explicit_mechanism_records=sum(c['evidence_level']=='EXPLICIT_MECHANISM' for c in cs),nonexplicit_records=sum(c['evidence_level']!='EXPLICIT_MECHANISM' for c in cs),candidate_mechanisms=len(mechanism_nodes),all_source_spans=sum(len(c['evidence_spans']) for c in cs),nodes_with_multiple_family_ids=sum(t['family_count']>1 for t in mechanism_nodes),nodes_with_distinct_source_texts=sum(t['distinct_source_text_count']>1 for t in mechanism_nodes),contribution_reduction_into_candidates=sum(c['evidence_level']=='EXPLICIT_MECHANISM' for c in cs)-len(mechanism_nodes)),
  mixed_mechanism_split_rate=None,independent_semantic_precision=None,reason='No gold mechanism inventory or matched-cost semantic audit. Nonempty means and literal quote matches are structural indicators only; uncertainty units differ.')
 same_input_rows=[]
 pt={r['contribution_id']:r['technology_id'] for r in kb['patent_technology']}
 for panel in data['panels']:
  fids={d['family_id'] for d in panel['docs']};rr=byselection[panel['selection_id']];themes=rr['result'].get('themes',[]);subset=[c for c in cs if c['family_id'] in fids]
  evidence=sum(len(t.get('evidence',[])) for t in themes);verified=sum(len(t.get('verified_evidence',[])) for t in themes)
  same_input_rows.append([panel['selection_id'],len(themes),sum(t.get('name') not in [None,'无法确定'] for t in themes),str(verified)+' / '+str(evidence),sum(bool(t.get('means')) for t in themes),len(fids),len({c['family_id'] for c in subset if c['evidence_level']=='EXPLICIT_MECHANISM'}),len({pt[c['contribution_id']] for c in subset if c['contribution_id'] in pt}),sum(c['evidence_level']!='EXPLICIT_MECHANISM' for c in subset)])
 save('outputs/D1_D2_COMPARISON.json',dict(at=now(),method_notes=method,headers=['选择','群总体','本轮池','D1式输入族','D1式主题名','具名主题','引文PASS主题','D2候选机制','D2明确手段族','D2弃判记录','D1建议拆分'],rows=rows,operational_metrics=operational,same_input_family_headers=['选择','D1主题记录','D1具名','D1逐字证据匹配/提议','D1手段非空主题','共同输入唯一族','D2明确手段族','D2涉及全局节点','D2弃判记录'],same_input_family_rows=same_input_rows,controls=results,source_method=data,core_freeze_sha256=object_hash(freeze)))
 verify_freeze()
if __name__=='__main__':main()
