"""Assemble real outputs into a many-to-many catalog and spreadsheet input tables."""
from experiment import *
import pandas as pd
from analyze import allruns,load
OUTREL='outputs/01a171fb-0dd6-7792-b36b-80e200aba942'
def col(key,label=None,width=22,typ=None,wrap=False,fmt=None):
 return dict(key=key,label=label or key,width=width,type=typ,wrap=wrap,format=fmt)
def main():
 completion=json.loads((W/'evidence/naming_completion.json').read_text());assert completion['phase1']==completion['phase2']==70
 evidence_audit=pd.read_csv(W/'technology_catalog/theme_evidence_audit.csv',keep_default_na=False)
 audit_map={(r['panel_id'],int(r['theme_index'])):r for r in evidence_audit.to_dict('records')}
 semantic=json.loads((W/'evidence/semantic_source_review.json').read_text())['rows'];semantic_map={(r['panel_id'],r['theme_index']):r for r in semantic}
 runs=allruns();panels=json.loads((W/'technology_catalog/cluster_panels.json').read_text())
 named=[]
 for p in (W/'technology_catalog/phase1').glob('*.json'):
  if any(k in p.name for k in ['.input.','.raw.','.error.']):continue
  named.append(json.loads(p.read_text()))
 technologies=[];links=[];patent_links=[];evidences=[]
 modelpath=W/'technology_catalog/catalog.sqlite'
 con=sqlite3.connect(modelpath)
 con.executescript("CREATE TABLE IF NOT EXISTS technologies(technology_id TEXT PRIMARY KEY,name TEXT,object TEXT,problem TEXT,means TEXT,effect TEXT,confidence TEXT,needs_validation TEXT);CREATE TABLE IF NOT EXISTS cluster_technology(technology_id TEXT,run_id TEXT,cluster_id INTEGER,PRIMARY KEY(technology_id,run_id,cluster_id));CREATE TABLE IF NOT EXISTS patent_technology(technology_id TEXT,family_id TEXT,PRIMARY KEY(technology_id,family_id));CREATE TABLE IF NOT EXISTS evidence(technology_id TEXT,run_id TEXT,cluster_id INTEGER,family_id TEXT,field TEXT,quote TEXT,PRIMARY KEY(technology_id,run_id,cluster_id,family_id,field,quote));")
 for table in ['technologies','cluster_technology','patent_technology','evidence']:con.execute('DELETE FROM '+table)
 panelsby={p['panel_id']:p for p in panels}
 for n in sorted(named,key=lambda r:r['panel_id']):
  panel=panelsby[n['panel_id']];result=n['analysis'];related=W/f"technology_catalog/phase2/{n['panel_id']}.json"
  rels=json.loads(related.read_text())['analysis'].get('relations',[]) if related.exists() else []
  for ti,t in enumerate(result.get('themes') or [dict(name='无法确定',confidence='insufficient',limitations='模型未提供候选主题；此为状态记录。',verified_evidence=[])]):
   ident=hashlib.sha256(json.dumps([t.get('name'),t.get('object'),t.get('means')],ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:12]
   if t.get('name')=='无法确定':ident=hashlib.sha256((n['panel_id']+str(ti)).encode()).hexdigest()[:12]
   tid='TC-'+ident
   matching=[r for r in rels if r.get('theme_name')==t.get('name')]
   relation=matching[0] if t.get('name')!='无法确定' and len(matching)==1 else dict(relation='未判定',reason='首轮无法确定或第二阶段名称不能唯一匹配；原始第二阶段输出完整保留。')
   ev=t.get('verified_evidence',[]);familyids=sorted({e['family_id'] for e in ev})
   record=dict(technology_id=tid,algorithm=n['algorithm'],embedding_model=n['embedding_model'],run_id=n['run_id'],cluster_id=n['cluster_id'],cluster_size=n['cluster_size'],clustering_scope_size=panel.get('clustering_scope_size',N),name=t.get('name','无法确定'),object=t.get('object',''),problem=t.get('problem',''),means=t.get('means',''),effect=t.get('effect',''),representative_families='; '.join(familyids or [d['family_id'] for d in panel['docs'][:3]]),evidence_text='\n'.join(e['family_id']+': '+e['quote'] for e in ev),multiple_mechanisms=result.get('heterogeneity',''),needs_split=result.get('needs_split',False),confidence=t.get('confidence','insufficient'),llm_reported_confidence=t.get('llm_reported_confidence','未报告'),evidence_validation=t.get('evidence_validation','REVIEW_REQUIRED'),verified_families=len(familyids),head_chip_relation=relation.get('relation','未判定'),relation_reason=relation.get('reason',''),needs_validation=str(result.get('limitations',''))+'；'+str(relation.get('uncertainties',''))+'；候选主题未经领域专家确认。',unique_representative_texts=panel.get('unique_representative_texts'),title_only_fraction=panel.get('title_only_fraction'))
   a=audit_map.get((n['panel_id'],ti),{})
   record.update(model_original_name=t.get('unverified_name',t.get('name')),theme_index=ti,quote_audit_status=a.get('quote_audit_status',record['evidence_validation']),unique_supporting_texts=a.get('unique_supporting_texts',0),supporting_families='; '.join(familyids),reviewed_cluster_families='; '.join(d['family_id'] for d in panel['docs']))
   record['evidence_validation']=record['quote_audit_status']
   sem=semantic_map.get((n['panel_id'],ti),dict(supported_level='无法确定',mechanism_notes='不足以形成可核验共同技术主题。',reviewed_confidence='insufficient'))
   record.update(supported_level=sem['supported_level'],mechanism_notes=sem['mechanism_notes'])
   if record['name']!='无法确定':record['confidence']=sem['reviewed_confidence']
   record['needs_validation']+='；'+record['mechanism_notes']
   if record['unique_supporting_texts']<3:
    record['needs_validation']+='；支持原文少于3份独立文本，重复族号不能当作独立机制证据。'
    if record['confidence'] in ['high','medium']:record['confidence']='low'
   technologies.append(record);links.append(dict(technology_id=tid,run_id=n['run_id'],cluster_id=n['cluster_id']))
   vals=[record[k] if isinstance(record[k],(str,int,float)) else json.dumps(record[k],ensure_ascii=False) for k in ['name','object','problem','means','effect','confidence','needs_validation']]
   con.execute('insert or ignore into technologies values(?,?,?,?,?,?,?,?)',(tid,*vals))
   con.execute('insert or ignore into cluster_technology values(?,?,?)',(tid,n['run_id'],n['cluster_id']))
   for fid in familyids:
    patent_links.append(dict(technology_id=tid,family_id=fid));con.execute('insert or ignore into patent_technology values(?,?)',(tid,fid))
   for e in ev:
    row=dict(technology_id=tid,run_id=n['run_id'],cluster_id=n['cluster_id'],**e);evidences.append(row)
    con.execute('insert or ignore into evidence values(?,?,?,?,?,?)',(tid,n['run_id'],n['cluster_id'],e['family_id'],e['field'],e['quote']))
 con.commit();con.close()
 technologies.sort(key=lambda r:(r['name']=='无法确定',r['algorithm'],r['run_id'],r['cluster_id'],r['technology_id']))
 pd.DataFrame(technologies).to_csv(W/'technology_catalog/technologies.csv',index=False)
 pd.DataFrame(links).drop_duplicates().to_csv(W/'technology_catalog/cluster_technology.csv',index=False)
 pd.DataFrame(patent_links).drop_duplicates().to_csv(W/'technology_catalog/patent_technology.csv',index=False)
 pd.DataFrame(evidences).to_csv(W/'technology_catalog/evidence.csv',index=False)
 # Catalog each cluster in the primary algorithms; name only panels actually sent to local LLM.
 primary=json.loads((W/'comparison/primary_runs.json').read_text())
 allcluster=[];representatives=[]
 for r in runs:
  if r['run_id'] not in primary:continue
  labels,ids=load(r);cs,cnt=np.unique(labels[labels>=0],return_counts=True);f=W/r['algorithm']/r['run_id']
  center_sim=np.load(f/'semantic_center_cosine.npy',mmap_mode='r')
  cc=db();cc.row_factory=sqlite3.Row
  for c,size in zip(cs,cnt):
   pos=np.flatnonzero(labels==c);top=pos[np.argsort(-center_sim[pos],kind='stable')[:3]]
   docs=[dict(cc.execute('select family_id,title,abstract,pub_id from docs where row_idx=?',(int(ids[i]),)).fetchone()) for i in top]
   named_here=[t['name'] for t in technologies if t['run_id']==r['run_id'] and t['cluster_id']==int(c)]
   allcluster.append(dict(run_id=r['run_id'],algorithm=r['algorithm'],model=r['model'],cluster_id=int(c),cluster_size=int(size),clustering_scope_size=r['n'],mean_center_cosine=float(np.mean(center_sim[pos])),hdbscan_persistence=(r['persistence'][int(c)] if r['algorithm']=='hdbscan' else None),persistence_usable=(False if r['run_id']=='bge_n238541_pca30_c30_s15' else None),candidate_names=' / '.join(named_here) or '未命名',representative_families='; '.join(d['family_id'] for d in docs),representative_titles='\n'.join(d['title'] for d in docs),center_file=str((f/('centers.npy' if r['algorithm']=='kmeans' else 'semantic_centers.npy')).relative_to(W))))
  cc.close()
 for p in panels:
  tech=[t for t in technologies if t['run_id']==p['run_id'] and t['cluster_id']==p['cluster_id']]
  for d in p['docs']:
   representatives.append(dict(panel_id=p['panel_id'],algorithm=p['algorithm'],model=p['model'],cluster_id=p['cluster_id'],cluster_size=p['cluster_size'],candidate_names=' / '.join(t['name'] for t in tech) or '无法确定',**d,abstract_excerpt=d['abstract'][:360],original_abstract_characters=len(d['abstract'])))
 pd.DataFrame(allcluster).to_csv(W/'comparison/cluster_catalog.csv',index=False)
 pd.DataFrame(representatives).to_csv(W/'comparison/cluster_representatives.csv',index=False)
 statsrows=[]
 for r in runs:
  row={k:v for k,v in r.items() if isinstance(v,(str,int,float,bool)) or v is None}
  q=W/r['algorithm']/r['run_id']/'quality.json'
  if q.exists():row.update({k:v for k,v in json.loads(q.read_text()).items() if isinstance(v,(str,int,float,bool)) or v is None})
  row['parameters']=json.dumps(r['parameters'],sort_keys=True,ensure_ascii=False)
  statsrows.append(row)
 pairs=pd.read_csv(W/'comparison/partition_comparison.csv').where(pd.notnull(pd.read_csv(W/'comparison/partition_comparison.csv')),None).to_dict('records')
 rare=pd.read_csv(W/'comparison/rare_candidates.csv',keep_default_na=False).to_dict('records')
 for r in rare:r['abstract_excerpt']=r['abstract'][:300]
 specs=[
 dict(file='CLUSTER_STATISTICS.xlsx',sheets=[
  dict(name='Graphs',title='kNN图结构实测；不把孤点当作技术群',columns=[col('model','模型',16),col('k','k',10,'integer'),col('rule','图规则',16),col('edges','无向边数',18,'integer'),col('components','连通分量',20,'integer'),col('isolated','孤立节点',20,'integer'),col('largest_component','最大连通分量族数',24,'integer'),col('degree_p99','P99度数',18,'number'),col('degree_max','最大度数',18,'integer'),col('density','图密度',20,'number',fmt='0.000000'),col('weight_quantiles','余弦权重分位数',55,wrap=True)],rows=[dict(model=p.name.split('_')[0],**json.loads(p.read_text())) for p in sorted((W/'leiden').glob('*_graph.json'))],rowHeight=44),
  dict(name='Experiments',title='全库与固定样本聚类实测',columns=[col('run_id','实验',44),col('n','样本族数',16,'integer'),col('clusters','非空群数',16,'integer'),col('noise_fraction','Noise比例',16,'percent'),col('size_median','中位群大小',16,'number'),col('size_max','最大群',16,'integer'),col('largest_fraction','最大群占比',16,'percent'),col('singleton_clusters','单点群数',18,'integer'),col('small_nontrivial_3_30','3–30族小群数',22,'integer'),col('clusters_ge3','≥3族群数',20,'integer'),col('fraction_in_clusters_ge3','≥3族群覆盖',22,'percent'),col('quality','RB目标值（同图同分辨率内比较）',38,'number'),col('modularity','Modularity',22,'number'),col('mean_pair_cosine_weighted','非Noise群内余弦',24,'number'),col('silhouette_cosine','Silhouette（非Noise抽样）',22,'number'),col('nearest_other_center_cosine_mean','最近他群中心余弦',24,'number'),col('language_nmi','语言NMI',18,'number'),col('wall_s','算法秒数',18,'number'),col('space','输入空间',58,wrap=True),col('parameters','完整参数',100,wrap=True)],rows=statsrows,rowHeight=72),
  dict(name='Stability',title='种子、参数、算法和模型分区对照',columns=[col('run_a','实验A',48),col('run_b','实验B',48),col('comparison','比较类型',18),col('scope_n','共同族数',16,'integer'),col('ari_noise_as_one_label','ARI 含Noise',20,'number'),col('nmi_noise_as_one_label','NMI 含Noise',20,'number'),col('nonnoise_n','共同非Noise族数',22,'integer'),col('ari_both_nonnoise','ARI 共同非Noise',22,'number')],rows=pairs,rowHeight=36)
 ]),
 dict(file='CLUSTER_CATALOG.xlsx',sheets=[
  dict(name='Clusters',title='主比较分区的全部聚类目录',columns=[col('run_id','实验',44),col('cluster_id','群ID',12,'integer'),col('cluster_size','族数',14,'integer'),col('clustering_scope_size','实验覆盖族数',22,'integer'),col('mean_center_cosine','中心平均余弦',20,'number'),col('hdbscan_persistence','原始HDBSCAN持久性',26,'number'),col('persistence_usable','持久性可解释',22),col('candidate_names','本地LLM候选名',44,wrap=True),col('representative_families','中心代表族',50,wrap=True),col('representative_titles','中心代表标题',85,wrap=True),col('center_file','中心文件（定义见方法）',70,wrap=True)],rows=allcluster,rowHeight=76),
  dict(name='Evidence panels',title='不同规模与异质性群的中心、随机、多样性、边缘代表',columns=[col('panel_id','证据组',50),col('cluster_size','群族数',14,'integer'),col('selection_role','抽样角色',20),col('family_id','Family ID',24),col('title','标题原文',70,wrap=True),col('abstract_excerpt','摘要前360字；全文见CSV/底座',110,wrap=True),col('language','摘要/代表语言',20),col('title_language','标题语言',18),col('text_quality','文本质量',20),col('center_cosine','中心余弦',16,'number'),col('candidate_names','候选技术名称',65,wrap=True)],rows=representatives,rowHeight=150)
 ]),
 dict(file='TECHNOLOGY_CATALOG.xlsx',sheets=[
  dict(name='Candidates',title='本地LLM初步技术候选；与Cluster保持多对多',columns=[col('technology_id','候选ID',28),col('name','保守技术候选名',48,wrap=True),col('model_original_name','LLM原始名称',48,wrap=True),col('supported_level','证据支持层级',32,wrap=True),col('mechanism_notes','共同手段核查说明',95,wrap=True),col('object','技术对象',50,wrap=True),col('problem','技术问题',60,wrap=True),col('means','技术手段（模型原始归纳）',85,wrap=True),col('effect','技术效果',60,wrap=True),col('confidence','引文核查后证据等级',25),col('llm_reported_confidence','原始LLM自评',22),col('verified_families','引文已验证族数',22,'integer'),col('unique_supporting_texts','独立支持原文数',22,'integer'),col('supporting_families','支持原文的族',58,wrap=True),col('evidence_validation','逐字引文核查',24),col('run_id','来源实验',44),col('cluster_id','群ID',12,'integer'),col('cluster_size','群族数',14,'integer'),col('clustering_scope_size','实验覆盖族数',22,'integer'),col('multiple_mechanisms','异质性说明',80,wrap=True),col('needs_split','建议细分',18),col('head_chip_relation','第二阶段喷头关系',24),col('needs_validation','待验证',85,wrap=True)],rows=technologies,rowHeight=160),
  dict(name='Patent evidence',title='逐字引文与专利族证据',columns=[col('technology_id','候选ID',28),col('family_id','Family ID',25),col('field','原文字段',18),col('quote','已通过逐字匹配的原文引文',120,wrap=True),col('run_id','来源实验',44),col('cluster_id','群ID',12,'integer')],rows=evidences,rowHeight=110)
 ]),
 dict(file='RARE_TECHNOLOGY_CANDIDATES.xlsx',sheets=[
  dict(name='Review queue',title='小群、Noise、边界及模型差异审计',columns=[col('candidate_type','候选区域类型',40),col('family_id','Family ID',26),col('title','标题原文',70,wrap=True),col('abstract_excerpt','摘要前300字；全文见CSV/底座',100,wrap=True),col('neighbor_overlap30','双模型近邻重合',22,'percent'),col('scope_size','实验覆盖族数',20,'integer'),col('bge_neighbor_families','BGE前5近邻',65,wrap=True),col('qwen_neighbor_families','Qwen前5近邻',65,wrap=True),col('run_id','来源实验',44),col('cluster_id','群ID',14,'integer'),col('language','摘要/代表语言',20),col('title_language','标题语言',18),col('text_quality','文本质量',20),col('data_issue_flags','数据质量标记，独立于技术价值',42,wrap=True)],rows=rare,rowHeight=130)
 ])]
 specs[0]['sheets']=specs[0]['sheets'][1:]+specs[0]['sheets'][:1]
 dump('reports/workbook_data.json',specs)
 md=['# 初步技术候选目录','',f'本地LLM实际处理 {len(named)} 个聚类证据组；产生 {len(technologies)} 条主题尝试记录，其中 {sum(t['name']!='无法确定' for t in technologies)} 条具名、{sum(t['name']=='无法确定' for t in technologies)} 条待定。具名不等于共同技术机制已成立，见逐条证据支持层级。命名是候选，未经领域专家确认。所有引文以给定原文逐字检查；第二阶段喷头关系独立保存。','']
 for t in technologies:
  md += [f"## {t['technology_id']}｜{t['name']}",'',f"- 来源：{t['run_id']} / Cluster {t['cluster_id']}，{t['cluster_size']}族",f"- 证据支持层级：{t['supported_level']}；{t['mechanism_notes']}",f"- 对象：{t['object']}",f"- 问题：{t['problem']}",f"- 手段：{t['means']}",f"- 效果：{t['effect']}",f"- 证据状态：{t['evidence_validation']}；核查后等级 {t['confidence']}，原始LLM自评 {t['llm_reported_confidence']}；已匹配 {t['verified_families']}族",f"- 异质性：{t['multiple_mechanisms']}",f"- 第二阶段喷头关系：{t['head_chip_relation']}，{t['relation_reason']}",f"- 待验证：{t['needs_validation']}",'',t['evidence_text'],'']
 (W/'TECHNOLOGY_CATALOG.md').write_text('\n'.join(md))
 dump('evidence/catalog_assembly.json',dict(technology_cluster_records=len(technologies),unique_technology_ids=len({t['technology_id'] for t in technologies}),panels=len(named),verified_quote_records=len(evidences),candidate_records=sum(t['name']!='无法确定' for t in technologies),unresolved_names=sum(t['name']=='无法确定' for t in technologies),cluster_records=len(allcluster),rare_review_rows=len(rare),output_dir=OUTREL))
 log('catalog_assembled',technologies=len(technologies))
if __name__=='__main__':main()
