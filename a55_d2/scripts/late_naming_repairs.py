"""Last naming audit: bounded source corrections, no history inputs."""
from common import *
import concepts,merge,copy,fcntl
def main():
 guard();assert not (W/'evidence/CORE_FREEZE.json').exists()
 old=load('working/all_selected/contributions.json');oldrec={c['contribution_id']:c for c in old};oldfam={c['family_id']:c['contribution_id'] for c in old}
 oldjudge=merge.Judge(merge.load_stage('all_selected'),state_db());old_a,old_b=oldfam['google:40130510'],oldfam['google:40587181'];old_pair_path=W/'pairs'/(oldjudge.key(old_a,old_b)+'.json');prior=load(str(old_pair_path))
 if prior.get('prior_pair_cache_path'):
  old_b=prior.get('source_review',{}).get('old_contribution_id',old_b);old_pair_path=W/prior['prior_pair_cache_path'];prior=load(str(old_pair_path))
 prior_sha=sha(old_pair_path)
 old_a=next(c for c in old if c['family_id']=='google:40130510').get('source_model_contribution_id',old_a)
 import known_amendments,consolidate
 known_amendments.main();saved_args=sys.argv;sys.argv=['consolidate.py','--stage','all_selected'];consolidate.main();sys.argv=saved_args
 records=merge.load_stage('all_selected');byid={c['contribution_id']:c for c in records};fam={c['family_id']:c['contribution_id'] for c in records};judge=merge.Judge(records,state_db())
 a,b=sorted([fam['google:40130510'],fam['google:40587181']])
 note='40130510限定Bi/镧系元素的A位取代、B位为Zr/Ti；40587181另含特定B位元素共同取代及不同组成窗口。共同PZT/钙钛矿背景不足以判具体组成等价，保留Related。'
 result=dict(left=a,right=b,relation='Related',parent_id=None,rationale=note,evidence_ids_left=[e['id'] for e in byid[a]['evidence_spans'] if e['field']=='abstract'][:8],evidence_ids_right=[e['id'] for e in byid[b]['evidence_spans'] if e['field']=='abstract'][:8],judgment_origin='AI_ASSISTANT_SOURCE_REVIEW_WITH_CURATED_CID_LINEAGE_NOT_HUMAN_GOLD')
 merge.verify_judgment_evidence(result,byid)
 pk=judge.key(a,b);save('pairs/'+pk+'.json',dict(cache_key=pk,request_id=None,model_digest=None,result=result,result_sha256=object_hash(result),original_llm_result=prior.get('original_llm_result',prior['result']),prior_local_request_id=prior['request_id'],prior_pair_cache_path=str(old_pair_path.relative_to(W)),source_review=dict(at=now(),reviewer='AI_ASSISTANT_NOT_HUMAN_GOLD',reason=note,prior_pair_cache_sha256=prior_sha,old_contribution_id=old_b,new_contribution_id=fam['google:40587181']),equivalence_usable=False))
 edits={
 'google:40130510':dict(name_zh='Bi或镧系元素A位取代的PZT组成窗口',level_a='钙钛矿铁电材料组成',technical_object='A位取代PZT材料',core_mechanism='以Bi或镧系元素取代PZT的A位；摘要给出相应钙钛矿组成及掺杂窗口，目标是不加烧结助剂或受主离子时提高A位施主取代含量。',applicable_conditions='0.05≤x≤0.4；0<y≤0.7；δ=0、z=3为标准，保持钙钛矿结构范围内可偏离。',review_notes='助手按源文保留组成窗口；不将分数窗口自行转换为摘要未逐字出现的百分数上界，也不补制备工序。'),
 'google:40587181':dict(name_zh='A位与特定B位元素共同取代的PZT材料',level_a='钙钛矿铁电材料组成',technical_object='A/B位共同取代PZT材料',core_mechanism='以非Pb元素取代PZT的A位，并以Nb、Ta、V、Sb、Mo或W取代B位；摘要用共同取代组成及变量范围限定材料。',applicable_conditions='0.01<x≤0.4；0<y≤0.7；0.1≤z≤0.4；δ=0、w=3为标准值，保持钙钛矿结构范围内可偏离。',review_notes='助手按源文区分共同取代与仅A位取代，保持x的严格下界；来源目的与通式在B位边界的差异需全文核对。'),
 'google:34401873':dict(name_zh='主链液晶聚合物压电域分散基体的减振复合材料',level_a='压电减振复合材料',technical_object='压电换能复合材料',core_mechanism='在基体材料中分散含主链型液晶聚合物的压电域；摘要主张将外界振动的应变能转为电能并耗散为热。',applicable_conditions='基体内具有含主链型液晶聚合物的压电域。',review_notes='助手源文修订：4至30质量百分比仅见一个来源，未提升为共同条件；具体加工步骤仍保留于各贡献。'),
 'google:64105183':dict(name_zh='外缘与分隔支撑厚度限定的多振膜压电麦克风',level_a='压电声压传感结构',technical_object='多振膜压电麦克风',core_mechanism='以外缘和分隔支撑将单片薄板分成多个振膜，各设电极、压电膜、电极叠层及检测电路；厚度满足13.3×td<t2<t1 −20µm。',applicable_conditions='t1为外缘支撑厚度，t2为分隔支撑厚度，td为薄板厚度。',review_notes='助手源文修订：保留原始厚度不等式；二元减法中的20与有符号负数的表现不同，未凭此声称源文没有该量。')
 }
 groups=load('working/all_selected/CONTRIBUTION_GROUPS.json')['groups'];new_reviews=[]
 for fid,edit in edits.items():
  cid=fam[fid];group=([cid] if fid in ['google:40130510','google:40587181'] else next(g for g in groups if cid in g));card=concepts.group_card(group,byid);key=concepts.naming_key(card)
  problems={byid[x]['technical_problem']['text'] for x in group};n=dict(edit,group_key=card['group_key'],support_contribution_ids=group,technical_problem=next(iter(problems)) if len(problems)==1 else None,scope_limit='共同机制候选；各来源特有的问题、材料、定量参数和效果见贡献，不统一继承。')
  concepts.audit_common_scope(n,card,group,byid)
  review=dict(at=now(),review_id='D2_LAST_NAMING_SOURCE_AUDIT_V1',family_id=fid,group_key=card['group_key'],reason=edit['review_notes'],reviewer='AI_ASSISTANT_NOT_HUMAN_GOLD',after_sha256=object_hash(n),source_contribution_ids=group)
  save('concept_names/'+key+'.json',dict(cache_key=key,request_id=None,result=n,result_sha256=object_hash(n),at=now(),naming_origin='AI_ASSISTANT_SOURCE_CURATED_AFTER_LOCAL_NAMING_FAILURE',source_review=review,raw_local_failures_retained=True));new_reviews.append(review)
 ledger=load('evidence/NAMING_SOURCE_REVIEW.json');ledger['source_names_compared']=12;ledger['curated_names']=[r for r in ledger['curated_names'] if r['family_id'] not in edits]+new_reviews;ledger['contribution_corrections']=['google:44719320','google:14080699','google:40130510','google:40587181'];ledger['notes']='Twelve source name/group audits against complete source. Nine source-curated names; one additional A/B-site pair separated and strict x bound corrected. AI review, no human Gold.';save('evidence/NAMING_SOURCE_REVIEW.json',ledger)
 save('evidence/LATE_NAMING_AUDIT_REPAIRS.json',dict(at=now(),pair=dict(old_cids=[old_a,old_b],new_cids=[a,b],before=prior['result']['relation'],after='Related',reason=note,prior_cache_sha256=prior_sha,new_cache_key=pk),naming_reviews=new_reviews,source_amended_families=['google:40130510','google:40587181'],new_model_calls=0))
 print(stable(dict(amended_families=len(load('evidence/ASSISTANT_SOURCE_AMENDMENTS.json')['families']),source_curated_names=len(ledger['curated_names']),curated_pair_relation='Related')))
if __name__=='__main__':
 lock=(W/'state/worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
