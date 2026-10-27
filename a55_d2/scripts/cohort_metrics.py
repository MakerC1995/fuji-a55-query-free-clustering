"""Observed cohort overlap and mechanism sharing, after core definitions freeze."""
from common import *
from posthoc_relevance import verify_freeze
import pandas as pd,collections,itertools
def main():
 guard();freeze=verify_freeze();kb=load('working/all_selected/KB_RECORDS.json');cs=load('working/all_selected/contributions.json')
 members=pd.read_parquet(W/'inputs/CLUSTER_MEMBERS.parquet');cohorts=pd.read_csv(W/'inputs/COHORTS.csv').to_dict('records')
 ct={r['contribution_id']:r['technology_id'] for r in kb['patent_technology']};text={c['family_id']:object_hash(dict(title=c['source_title'],abstract=c['source_abstract'])) for c in cs}
 fs={c['selection_id']:set(members[members.selection_id==c['selection_id']].family_id) for c in cohorts}
 tf={};metrics=[]
 for co in cohorts:
  sid=co['selection_id'];groups=collections.defaultdict(set)
  for c in cs:
   if c['family_id'] in fs[sid] and c['contribution_id'] in ct:groups[ct[c['contribution_id']]].add(c['family_id'])
  tf[sid]=dict(groups)
  cc=[c for c in cs if c['family_id'] in fs[sid]]
  metrics.append(dict(selection_id=sid,source_coverage='FULL_CLUSTER' if co['complete_cluster'] else 'SAMPLED_MEMBERS_ONLY',families=len(fs[sid]),contributions=len(cc),candidate_mechanisms=len(groups),mechanism_type_counts=dict(collections.Counter(c['mechanism_type'] for c in cc)),evidence_level_counts=dict(collections.Counter(c['evidence_level'] for c in cc)),different_mechanism_types=len({c['mechanism_type'] for c in cc if c['mechanism_type']!='UNDISCLOSED'})))
 rows=[]
 for a,b in itertools.combinations(cohorts,2):
  x,y=a['selection_id'],b['selection_id'];common_t=sorted(set(tf[x])&set(tf[y]))
  proven=[]
  for tid in common_t:
   witnesses=[(f,g) for f in sorted(tf[x][tid]) for g in sorted(tf[y][tid]) if f!=g and text[f]!=text[g]]
   if witnesses:proven.append(dict(technology_id=tid,left_family_id=witnesses[0][0],right_family_id=witnesses[0][1]))
  rows.append(dict(left=x,right=y,left_run=a['run_id'],right_run=b['run_id'],left_cluster_id=int(a['cluster_id']),right_cluster_id=int(b['cluster_id']),left_complete_cluster=bool(a['complete_cluster']),right_complete_cluster=bool(b['complete_cluster']),family_intersection=len(fs[x]&fs[y]),family_union=len(fs[x]|fs[y]),family_jaccard=len(fs[x]&fs[y])/len(fs[x]|fs[y]),shared_technology_ids=common_t,shared_concept_count=len(common_t),distinct_family_and_text_witness_count=len(proven),witnesses=proven))
 save('outputs/CROSS_MODEL_COMPARISON.json',dict(at=now(),core_freeze_sha256=object_hash(freeze),cohorts=metrics,pairs=rows,interpretation='Jointly built global concepts demonstrate reusable IDs, not independent rediscovery or accuracy across models. A repeated Family ID or identical title/abstract is excluded from independent mechanism witnesses. Membership comparisons are limited to selected cohorts; sampled cohorts do not represent full clusters.'))
 verify_freeze();print(stable(dict(cohorts=len(metrics),pairs=len(rows))))
if __name__=='__main__':main()
