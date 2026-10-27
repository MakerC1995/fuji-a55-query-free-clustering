"""Final bounded source-based directory review before any historical inputs."""
from common import *
import fcntl,copy
def main():
 guard();assert not (W/'evidence/CORE_FREEZE.json').exists()
 data=load('working/all_selected/DOMAIN_ORGANIZATION.json');names=load('working/all_selected/CONCEPT_NAMES.json');cs={c['contribution_id']:c for c in load('working/all_selected/contributions.json')};bykey={n['group_key']:n for n in names['names']}
 old_catalog=copy.deepcopy(next(d for d in data['catalog'] if d['domain_id']=='P019'))
 new_name='振动与发电材料器件';new_scope='涵盖振动、发电及能量转换相关的材料结构、器件和驱动机制；各节点的具体物理机理分别保留。'
 for domain in data['catalog']:
  if domain['domain_id']=='P019':domain['name_zh']=new_name;domain['scope']=new_scope;domain['source_review_note']='助手据驻极体薄膜原文拓宽组织范围，非物理等价或实际采用结论。'
 changes=[]
 for r in data['mappings']:
  fids={cs[c]['family_id'] for c in bykey[r['group_key']]['support_contribution_ids']}
  if 'google:97217650' in fids:
   prior=copy.deepcopy(r);r.update(domain_id='P019',classification_origin='AI_ASSISTANT_SOURCE_OBJECT_REVIEW',original_classification_request_id=r['request_id'],request_id=None);changes.append(dict(family_id='google:97217650',group_key=r['group_key'],before=prior,reason='驻极膜的表面电荷与温度弹性指标服务于振动发电，不属于机械载具/承载结构；按原文对象调整组织域。'))
  if r['domain_id']=='P019':r['canonical_domain']=new_name;r['domain_scope']=new_scope
  r['unclassified_source_label_fallback']=r.pop('needs_human_review',False);r['human_validation_status']='NOT_INDEPENDENTLY_HUMAN_VALIDATED'
 assert len(changes)==1
 data['source_review']='evidence/DOMAIN_SOURCE_REVIEW.json';data['canonical_domains']=len({r['canonical_domain'] for r in data['mappings']});save('working/all_selected/DOMAIN_ORGANIZATION.json',data)
 save('evidence/DOMAIN_SOURCE_REVIEW.json',dict(at=now(),changes=changes,catalog_before=old_catalog,catalog_after=next(d for d in data['catalog'] if d['domain_id']=='P019'),human_gold=False,scope='Bounded object/domain diagnostic; other AI classifications may overlap and need expert review; no historical or printhead labels used'))
 print(stable(dict(domains=data['canonical_domains'],reviewed_object_correction=1,mechanisms=len(data['mappings']))))
if __name__=='__main__':
 lock=(W/'state/worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
