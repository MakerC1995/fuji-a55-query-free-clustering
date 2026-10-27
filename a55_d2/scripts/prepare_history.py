"""Normalize the existing historical mappings only after the complete core freeze."""
from common import *
from posthoc_relevance import verify_freeze
import pandas as pd,shutil,collections
def main():
 guard();freeze=verify_freeze();source=D1/'manifests/historical'
 mapping=pd.read_csv(source/'FAMILY_ID_MAPPING.csv',dtype=str).fillna('');nodes=pd.read_csv(source/'HISTORICAL_NODES.csv',dtype=str).fillna('')
 mapping=mapping[mapping.family_id!=''];assert mapping.family_id.nunique()==45
 assert mapping.groupby('tree').family_id.nunique().to_dict()=={'Equipment':18,'Recipe':27}
 bynode={r['historical_node_id']:r for r in nodes.to_dict('records')};selected=set(pd.read_parquet(W/'inputs/PATENT_TEXTS.parquet').family_id)
 cases=[]
 for fid,g in mapping.groupby('family_id',sort=True):
  trees=set(g.tree);assert len(trees)==1
  expected=sorted(set(g.historical_node_id));references=[]
  for nid in expected:
   n=bynode[nid];rows=g[g.historical_node_id==nid]
   references.append(dict(node_id=nid,branch=n['branch'],description=n['description'],historical_note=n['historical_note'],representative=n['representative'],source_reference=n['evidence'],owner_history=n['owner_history'],observed_publications=sorted(set(rows.publication)),mapping_relationships=sorted(set(rows.relationship_to_representative)),ownership_verified=sorted(set(rows.ownership_verified))))
  cases.append(dict(family_id=fid,history_group=next(iter(trees)),expected_node_ids=expected,history_reference=references,discovery_scope='CORE_DISCOVERY_COHORT' if fid in selected else 'POST_FREEZE_SUPPLEMENT_PROBE'))
 outside=[c['family_id'] for c in cases if c['family_id'] not in selected];db=source_db();docs=[]
 for fid in outside:
  d=dict(db.execute('SELECT row_idx,family_id,pub_id,publication_id,title,abstract,language,title_language,raw_text,text_hash,text_quality,source,bge_input_hash,qwen_input_hash FROM docs WHERE family_id=?',(fid,)).fetchone())
  assert digest_bytes(d['raw_text'].encode())==d['text_hash'];docs.append(d)
 db.close();assert len(docs)==6
 for name in ['FAMILY_ID_MAPPING.csv','HISTORICAL_NODES.csv','historical_sputter_tree_recipe_equipment.md']:
  target=W/'inputs/posthoc_history'/name;write_guard(target);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,target)
 save('working/HISTORY_CASES.json',dict(cases=cases,core_freeze_sha256=object_hash(freeze),phase='POST_FREEZE_ONLY'))
 save('inputs/HISTORY_SUPPLEMENT_TEXTS.json',dict(docs=docs,phase='POST_FREEZE_SOURCE_ONLY_PROBE',not_core_discovery=True))
 save('evidence/HISTORICAL_INPUT_PREPARED.json',dict(at=now(),core_freeze_at=freeze['at'],core_freeze_sha256=object_hash(freeze),historical_read_after_core_freeze=True,families=45,groups={'Recipe':27,'Equipment':18},core_discovery_families=39,supplement_families=outside,source_hashes={str(p.relative_to(W)):sha(p) for p in sorted((W/'inputs/posthoc_history').glob('*'))},unresolved_history_nodes=sorted(set(nodes.historical_node_id)-set(mapping.historical_node_id)),limits='Historical research-node labels are not independent legal families or verified current ownership; six probes selected post-freeze cannot be called first-pass discovery'))
 verify_freeze();print(stable(dict(cases=len(cases),core=39,postfreeze_probes=len(docs))))
if __name__=='__main__':main()
