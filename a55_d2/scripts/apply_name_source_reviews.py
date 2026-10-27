"""Bounded naming corrections from eight actual source/name comparisons."""
from common import *
import copy
EDITS={
 'google:97217650':dict(level_a='驻极体振动发电薄膜',technical_object='驻极体用薄膜'),
 'google:53004031':dict(level_a='压电元件叠层结构',technical_object='多层压电元件',applicable_conditions='中间层材料不同于第二电极，厚度0.4至10µm；硅基板局部去除形成振膜或悬臂结构。'),
 'google:51840117':dict(name_zh='粘弹聚合物基体分散压电颗粒的复合膜',core_mechanism='将压电颗粒分散在室温呈粘弹性的聚合物基体内，并在复合体两侧设置薄膜电极。',applicable_conditions='聚合物基体在室温具有粘弹性。'),
 'google:12135974':dict(core_mechanism='在靶与基板间等离子空间的上下端设置形状和电位相同的导体，使空间电位对称，以抑制粒子分散的偏斜及分散空间扩大。',technical_object='溅射装置',applicable_conditions='靶与基板间形成等离子空间。'),
 'google:37647266':dict(name_zh='调夹角并绕近靶面法向旋转控制柱状晶倾角',core_mechanism='改变基材与靶材夹角，并使基材围绕近垂直于靶材的轴旋转，以控制柱状晶体相对基材的倾角。')
}
REASONS={
 'google:97217650':'驻极体膜的电荷与弹性模量指标不能改称压电膜机理；按原文校正对象/问题域。',
 'google:53004031':'共同条件应披露实际材料、厚度和基板结构；性能目标不充当必要条件，开放域及对象改用中文。',
 'google:51840117':'不得把一个来源的介电常数阈值推广到所有成员；来源披露复合膜结构而非具体制备工艺。',
 'google:12135974':'原文为粒子空间分散偏斜，不将其改写成材料组分析出/偏析；保留等电位导体的空间位置。',
 'google:37647266':'补明旋转轴近垂直于靶材这一原文方向限制，名称突出实际角度和旋转控制。'
}
def main():
 guard();assert not (W/'evidence/CORE_FREEZE.json').exists()
 cs={c['contribution_id']:c for c in load('working/all_selected/contributions.json')};rows=[]
 for p in sorted((W/'concept_names').glob('*.json')):
  saved=load(str(p));n=saved['result'];fids={cs[c]['family_id'] for c in n['support_contribution_ids'] if c in cs};found=fids&set(EDITS)
  if not found:continue
  fid=sorted(found)[0];old=copy.deepcopy(n)
  if saved.get('source_review',{}).get('review_id')=='first-eight-name-source-diagnostic-v1':rows.append(saved['source_review']);continue
  n.update(EDITS[fid]);n['review_notes']='助手按原文修订命名：'+REASONS[fid]
  saved.setdefault('original_naming_result',old);saved['result']=n;saved['result_sha256']=object_hash(n)
  saved['source_review']=dict(at=now(),review_id='first-eight-name-source-diagnostic-v1',family_id=fid,group_key=n['group_key'],reason=REASONS[fid],reviewer='AI_ASSISTANT_NOT_HUMAN_GOLD',before_sha256=object_hash(old),after_sha256=object_hash(n),source_contribution_ids=n['support_contribution_ids'])
  save(str(p),saved);rows.append(saved['source_review'])
 assert {r['family_id'] for r in rows}==set(EDITS)
 save('evidence/NAMING_SOURCE_REVIEW.json',dict(at=now(),source_names_compared=9,curated_names=rows,contribution_corrections=['google:44719320','google:14080699'],notes='Nine generated names read against complete source abstracts. Five naming corrections, two original contribution corrections. No independent human Gold; no semantic accuracy estimate.'))
 print(stable(dict(corrected_name_records=len(rows))))
if __name__=='__main__':main()
