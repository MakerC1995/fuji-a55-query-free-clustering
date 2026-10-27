"""Apply documented AI source diagnostics before naming/freeze; never alter raw receipts."""
from common import *
import merge,copy
REVIEWS=[
 ('google:97217650','google:83395703','Distinct','前者以表面电荷密度及高低温弹性模量比限定驻极膜，后者以钙钛矿压电膜扫压电流曲线的双极大值限定；对象及可辨别指标机制不同。'),
 ('google:18018956','google:17489025','Related','前者以给定导热率的石墨中间层传热，后者在内壁与中间层间为防裂保留的间隙内填充填充材传热；共同热传导目标不证明具体结构手段等价。'),
 ('google:15704676','google:13861312','Related','均有树状多级分流和横向喷嘴；后一摘要额外明确挡板碰撞散射气流。共同上位分流原理不足以把含关键挡板限定的完整贡献归为相同具体方案。'),
 ('google:55231366','google:56543376','Related','前者在保护层局部设置薄层以便电连接，后者在外围设置贯穿电极与保护层的沟槽以避免空气击穿等问题；不能由同一层叠压电膜对象推定机制相同。'),
 ('google:51840117','google:58050862','Related','前者将介电常数低于10且25摄氏度的粘弹性聚合物作为关键限定；后者以凸起几何及H/Ds范围为关键限定。共同颗粒/粘弹基体不够支持具体等价。'),
 ('google:50890710','google:47832311','Same','两侧Title和Abstract逐字相同：不锈钢固定面贴合基板背面、背侧加热及反应液温控。可归并来源叙述，但不同Family ID不能当成两份独立原文佐证。'),
 ('google:36601150','google:36961711','Same','两侧均明确卡匣架、废液/回收容器架与承载两者的可整体装卸托台；英译术语差异未显示不同工程结构。只支持摘要所述模块化托台方案。'),
 ('google:55217532','google:51623983','Related','前者关键为朝一侧凸出的凸起；后者关键为薄膜电极上层叠的引出金属箔及焊接连接。原Same理由把后一来源没有的凸起当成双方共有。'),
 ('google:56788369','google:98864925','Related','前者明确串联电容、并联电阻网络及反极性直流偏置；后者通过层叠膜中相反电场的单极波形与斜率比限定驱动。非对称滞回背景相同不代表电路与驱动手段相同。'),
 ('google:41346026','google:39774253','Related','前者强调无烧绿石相的单一钙钛矿相及a/b上限，后者为特定B位元素/组成和柱状晶粒结构；共同PZT/钙钛矿材料不够支持具体机制等价。')
]
REVIEWS += [
 ('google:48129838','google:47832311','Same','两侧均披露不锈钢贴合固定面、基板背侧加热及反应液独立温控，来源文字和术语略不同，核心构造对应。'),
 ('google:34467419','google:34101262','Same','两侧均披露交替电极在相反侧区露出第一电极材料端面，并在另一侧的第二电极材料端面形成绝缘膜；同一可辨别层叠互连结构。'),
 ('google:15782500','google:15782520','Same','两侧均由分析载片推出时顶开柔性盖，推出完成后自动复位封闭出片口；弹性/重力复位叙述差异可保留为来源实现变体。'),
 ('google:51624314','google:51623983','Related','前者以两对或更多电极划分有源区以产生多个互不干扰的声音信号；后者以引出金属箔及焊接处理电连接。共同颗粒复合压电体不构成具体机制等价。'),
 ('google:38813296','google:39377937','Same','中日摘要均以总容忍因子0.98至1.01及三个组分容忍因子的同组不等式约束组成；关键范围和排序一致，可支持摘要层面的同机制。'),
 ('google:35632644','google:35649145','Same','两侧均先在厚压电层切槽、将已切层附着到有蚀刻结构的主体，再磨薄至小于切槽深度形成独立压电岛；临时承载基板等实施细节保留于各来源。')
]
def apply_reviews(stage):
 guard();assert not (W/'evidence/CORE_FREEZE.json').exists()
 if (W/'evidence/PAIR_ASSISTANT_SOURCE_REVIEW_APPLIED.json').exists():return
 policy=load('evidence/SAME_CONFIRMATION_POLICY.json');assert policy['enabled']
 selection=load('evidence/PAIR_ASSISTANT_AUDIT_SELECTION.json')['sample']+load('evidence/DUAL_SAME_ASSISTANT_DIAGNOSTIC_SELECTION.json')['sample']
 records=merge.load_stage(stage);byid={c['contribution_id']:c for c in records};judge=merge.Judge(records,state_db())
 expected={frozenset((a,b)):(rel,note) for a,b,rel,note in REVIEWS};assert len(expected)==16
 rows=[];changed=0
 for item in selection:
  a,b=item['left'],item['right'];left,right=byid[a],byid[b]
  desired,note=expected[frozenset((left['family_id'],right['family_id']))]
  p=W/item['path'];saved=load(str(p));old=copy.deepcopy(saved['result']);new=copy.deepcopy(old)
  action='SOURCE_DIAGNOSTIC_AGREES_WITH_SAME' if desired=='Same' and old['relation']=='Same' else 'DIAGNOSTIC_ONLY_EXISTING_NON_SAME_RETAINED'
  if desired!='Same' and old['relation']=='Same':
   new.update(relation=desired,parent_id=None,rationale=note,evidence_ids_left=[e['id'] for e in left['evidence_spans'] if e['field']=='abstract'][:8],evidence_ids_right=[e['id'] for e in right['evidence_spans'] if e['field']=='abstract'][:8],judgment_origin='AI_ASSISTANT_SOURCE_DIAGNOSTIC_NOT_HUMAN_GOLD')
   merge.verify_judgment_evidence(new,byid);saved.setdefault('original_llm_result',copy.deepcopy(old))
   saved['pre_assistant_source_result']=old;saved['result']=new;saved['result_sha256']=object_hash(new);saved['equivalence_usable']=False
   saved['source_review']=dict(at=now(),reviewer='AI_ASSISTANT_NOT_HUMAN_GOLD',reason=note,original_cache_sha256=sha(p),evidence_selection='source abstracts read in full; quote IDs refer to own side',source_title_abstract_hashes=[object_hash(dict(title=c['source_title'],abstract=c['source_abstract'])) for c in [left,right]])
   save(str(p),saved);changed+=1;action='SAME_DOWNGRADED_BY_AI_SOURCE_REVIEW'
  rows.append(dict(pair_path=item['path'],left=a,right=b,left_family_id=left['family_id'],right_family_id=right['family_id'],assistant_source_assessment=desired,source_reason=note,second_pass_relation=old['relation'],effective_relation=new['relation'],action=action,human_gold=False))
 # Source-supported Same diagnostics never promote an LLM non-Same into equivalence.
 class ExistingOnly(merge.Judge):
  def ensure(self,pairs):return [self.existing(p['left'],p['right']) for p in pairs]
 prior=load('working/'+stage+'/CONTRIBUTION_GROUPS.json');x,keys=merge.embeddings(records,judge.conn)
 groups,audit=merge.conservative_groups(records,x,ExistingOnly(records,judge.conn))
 prior.update(at=now(),groups=groups,audit=audit,group_count=len(groups),assistant_pair_source_review='evidence/PAIR_ASSISTANT_SOURCE_REVIEW_APPLIED.json',final_rule='Dual Same, conservative clique/double-anchor consistency with all explicit non-Same vetoes, plus documented AI source diagnostic downgrades. Unjudged is not Distinct.')
 save('working/'+stage+'/CONTRIBUTION_GROUPS.json',prior)
 save('evidence/PAIR_ASSISTANT_SOURCE_REVIEW_APPLIED.json',dict(at=now(),selection='evidence/PAIR_ASSISTANT_AUDIT_SELECTION.json',rows=rows,same_downgrades=changed,fixed_original_sample_size=10,dual_same_followup_size=6,final_groups=len(groups),independent_human_gold=False,precision_estimate=None,interpretation='Ten sampled original Same proposals plus six already-confirmed follow-up pairs, AI diagnostic review. Do not report as human accuracy; Same assessments never promote a non-Same model result.'))
 event('assistant_pair_source_diagnostics_applied',pairs=16,same_downgrades=changed,groups=len(groups))
