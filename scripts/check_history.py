"""Post-hoc historical checks: strict chronological gate, no clustering changes."""
from experiment import *
from analyze import allruns,load,panel,metric
import pandas as pd
def main():
 frozen=json.loads((W/'evidence/FIRST_NAMING_FROZEN.json').read_text());assert frozen['count']==70
 for name,h in frozen['outputs'].items():assert sha(W/'technology_catalog/phase1'/name)==h
 source=Path('/Volumes/Fuji_SSD_Work/patent/embedding_benchmark/e4_historical_family_regression')
 out=W/'manifests/historical';out.mkdir(exist_ok=True)
 files=['FAMILY_ID_MAPPING.csv','HISTORICAL_NODES.csv','inputs/historical_sputter_tree_recipe_equipment.md']
 copied={}
 for name in files:
  p=source/name;h=sha(p);dest=out/p.name;dest.write_bytes(p.read_bytes());assert sha(dest)==h and sha(p)==h;copied[name]=h
 m=pd.read_csv(out/'FAMILY_ID_MAPPING.csv',keep_default_na=False);nodes=pd.read_csv(out/'HISTORICAL_NODES.csv',keep_default_na=False)
 ok=m[m.local_simple_family_verified.astype(str).str.lower().eq('true') & m.searchable_present.astype(str).str.lower().eq('true')]
 core=ok[['historical_node_id','collection','tree','technology_branch','historical_representative','family_id','relationship_to_representative']].drop_duplicates()
 con=db();con.row_factory=sqlite3.Row;families={}
 for fid in sorted(core.family_id.unique()):
  doc=con.execute('select row_idx,family_id,pub_id,title,abstract,language,text_quality from docs where family_id=?',(fid,)).fetchone();assert doc is not None
  families[fid]=dict(doc)
 assert len(families)==45
 unresolved=nodes[~nodes.historical_node_id.isin(core.historical_node_id)]
 candidate_only=core[core.relationship_to_representative.str.contains('unresolved')].historical_node_id.unique().tolist()
 rows=[];summaries=[];mixrows=[];blind=[]
 runs=allruns();selected=json.loads((W/'comparison/primary_runs.json').read_text())
 named_panels=json.loads((W/'technology_catalog/cluster_panels.json').read_text());named_map={(p['run_id'],p['cluster_id']):p for p in named_panels}
 for r in runs:
  if r['run_id'] not in selected:continue
  labels,ids=load(r);assign={};sizes=dict(zip(*np.unique(labels[labels>=0],return_counts=True)))
  for fid,doc in families.items():
   ri=doc['row_idx'];pos=int(np.searchsorted(ids,ri));inside=pos<len(ids) and ids[pos]==ri
   cl=int(labels[pos]) if inside else None;assign[fid]=cl
   trees=sorted(core[core.family_id==fid].tree.unique().tolist())
   related=core[core.family_id==fid]
   p=named_map.get((r['run_id'],cl));names=[]
   if p:
    rec=json.loads((W/'technology_catalog/phase1'/f"{p['panel_id']}.json").read_text());names=[t.get('name') for t in rec['analysis']['themes']]
   rows.append(dict(run_id=r['run_id'],scope_n=r['n'],family_id=fid,row_idx=ri,historical_nodes=';'.join(sorted(related.historical_node_id.unique())),trees=';'.join(trees),branches=';'.join(sorted(related.technology_branch.unique())),in_experiment_scope=inside,cluster_id=cl,noise=(cl==-1 if inside else None),cluster_size=int(sizes[cl]) if cl is not None and cl>=0 else None,first_pass_cluster_named=bool(p),first_pass_candidate_names=' / '.join(names),representative_link_unresolved=all('unresolved' in x for x in related.relationship_to_representative),pub_id=doc['pub_id'],title=doc['title']))
  for tree in ['Recipe','Equipment','All']:
   fids=sorted(core[core.tree==tree].family_id.unique()) if tree!='All' else sorted(families)
   vals=[assign[f] for f in fids if assign[f] is not None];non=[v for v in vals if v>=0];counts=collections.Counter(non)
   summaries.append(dict(run_id=r['run_id'],tree=tree,known_unique_families=len(fids),in_experiment_scope=len(vals),not_in_sample=len(fids)-len(vals),noise=sum(v==-1 for v in vals),nonnoise_clusters=len(counts),largest_cluster_core_families=max(counts.values(),default=0),first_pass_named_core_clusters=len({(r['run_id'],c) for c in non if (r['run_id'],c) in named_map})))
  for c in sorted({v for v in assign.values() if v is not None and v>=0}):
   rc=len({f for f in core[core.tree=='Recipe'].family_id if assign[f]==c});ec=len({f for f in core[core.tree=='Equipment'].family_id if assign[f]==c})
   mixrows.append(dict(run_id=r['run_id'],cluster_id=c,cluster_size=int(sizes[c]),recipe_core_families=rc,equipment_core_families=ec,mixed_historical_types=bool(rc and ec)))
  # Blinded supplemental naming: select modal Recipe/Equipment cluster, then
  # represent it with the same generic centroid/random/diversity/edge protocol.
  # No core family is inserted as a representative; no historical names enter LLM.
  if r['run_id'] in ['bge_k300_s42','bge_k30_mutual_r1.0_s42','bge_k30_sym_r1.0_s42','bge_n238541_pca30_c30_s15']:
   chosen=[]
   for tree in ['Recipe','Equipment']:
    fids=sorted(core[core.tree==tree].family_id.unique());counts=collections.Counter(assign[f] for f in fids if assign[f] is not None and assign[f]>=0)
    if counts:
     c=sorted(counts,key=lambda c:(-counts[c],c))[0]
     if c not in chosen:chosen.append(c)
   for c in chosen:
    p=panel(r,c);p['selection_stage']='posthoc_blind_check';blind.append(p)
 pd.DataFrame(rows).to_csv(W/'comparison/historical_assignments.csv',index=False)
 pd.DataFrame(summaries).to_csv(W/'comparison/historical_summary.csv',index=False)
 pd.DataFrame(mixrows).to_csv(W/'comparison/historical_cluster_mixing.csv',index=False)
 core.to_csv(W/'comparison/historical_node_family_links.csv',index=False)
 unresolved.to_csv(W/'comparison/historical_unresolved_nodes.csv',index=False)
 fine=next(r for r in runs if r['run_id']=='bge_k800_s42')
 finer=collections.Counter(r['cluster_id'] for r in rows if r['run_id']=='bge_k800_s42' and 'Recipe' in r['trees'] and r['cluster_id'] is not None and r['cluster_id']>=0)
 for c in sorted(finer,key=lambda c:(-finer[c],c))[:2]:
  p=panel(fine,int(c));p['selection_stage']='posthoc_finer_granularity_comparison';blind.append(p)
 blind=list({p['panel_id']:p for p in blind}.values());assert len(blind)<=8
 dump('technology_catalog/posthoc_blind_panels.json',blind)
 dump('evidence/historical_check.json',dict(status='ASSIGNMENTS_CHECKED_POSTHOC',historical_source_root=str(source),source_hashes=copied,first_naming_freeze_sha256=sha(W/'evidence/FIRST_NAMING_FROZEN.json'),first_historical_read_after_naming_freeze=True,known_observed_unique_families=45,recipe_unique_families=27,equipment_unique_families=18,nodes_with_observed_family=core.historical_node_id.nunique(),all_nodes=len(nodes),unresolved_nodes=unresolved.historical_node_id.tolist(),candidate_member_only_representative_link_unresolved=candidate_only,all_45_present_in_baseline=True,no_new_family_mapping_inferred=True,supplemental_blind_panels=len(blind),supplemental_selection_uses_history=True,supplemental_prompt_has_no_historical_names=True,labels_unchanged=True))
 print(pd.DataFrame(summaries).to_csv(index=False));print('Supplemental blinded clusters',len(blind))
if __name__=='__main__':main()
