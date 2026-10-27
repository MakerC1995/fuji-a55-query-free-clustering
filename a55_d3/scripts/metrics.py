from common import *
from experiments import active_comparison,active_main
from client import estimate
from design import DIM
import collections

def collect_comparisons():
 out=[];sel=load('inputs/EVALUATION_SELECTION.json');pilot=set(load('inputs/SPLIT_LOCK.json')['pilot30'])
 for s in sel:
  r=active_comparison(s['family_id'])
  if not r:continue
  scores={r['candidate_mapping'][x['candidate_id']]:x for x in r['result']['scores']}
  # Full D3 changes relevance only; contribution audit is identical to D3_EVIDENCE.
  if 'D3_EVIDENCE' in scores:scores['D3_FULL']=scores['D3_EVIDENCE']
  out.append(dict(selection=s,comparison=r,scores=scores,ablation=s['split']=='holdout' or s['family_id'] in pilot))
 return out

def make_metrics(comparisons):
 rows=[]
 old_counts=collections.Counter(c['family_id'] for c in json.loads((D2/'working/all_selected/contributions.json').read_text()) if c['evidence_level']=='EXPLICIT_MECHANISM')
 def add(scope,split,config,metric,num,den,n,unknown=0,tier='Silver',unit='rate',notes=''):
  rows.append(dict(scope=scope,split=split,configuration=config,metric=metric,numerator=num,denominator=den,value=num/den if num is not None and den else None,label_tier=tier,sample_n=n,unknown_n=unknown,unit=unit,notes=notes))
 allconfs=['D2_ARCHIVED','D2_DEEPSEEK_REPLAY','D3_EXTRACT_ONLY','D3_FIDELITY','D3_EVIDENCE','D3_FULL']
 for split in ['development','holdout']:
  for scope in ['paired_full','paired_ablation']:
   selected=[r for r in comparisons if r['selection']['split']==split and (scope!='paired_ablation' or r['ablation'])]
   required=['D2_ARCHIVED','D3_EVIDENCE'] if scope=='paired_full' else allconfs[:-1]
   common=[r for r in selected if all(c in r['scores'] for c in required)]
   confs=['D2_ARCHIVED','D3_FIDELITY','D3_EVIDENCE','D3_FULL'] if scope=='paired_full' else allconfs
   for conf in confs:
    data=[r['scores'][conf] for r in common if conf in r['scores']];n=len(data)
    for dim in DIM:
     cnt=collections.Counter(r['dimensions'][dim] for r in data);den=sum(cnt[k] for k in ['Correct','Partially Correct','Incorrect']);unknown=n-den
     add(scope,split,conf,dim+'_correct_rate',cnt['Correct'],den,n,unknown,notes='Correct / {Correct,Partially Correct,Incorrect}; insufficient and uncertain excluded; same-model Silver')
     add(scope,split,conf,dim+'_partially_correct_rate',cnt['Partially Correct'],den,n,unknown)
    for metric,numkey,denkey in [('contribution_coverage','correct_contribution_count','expected_contribution_count'),('material_retention','critical_material_retained','critical_material_expected'),('process_retention','critical_process_retained','critical_process_expected')]:
     evaluable=[]
     for rr in common:
      ss=rr['scores'][conf]
      # Shared source expectations must agree across all compared configurations.
      ds=[rr['scores'][c].get(denkey) for c in required]
      if len(set(ds))==1 and ds[0] is not None and ds[0]>0 and ss.get(numkey) is not None:evaluable.append(ss)
     add(scope,split,conf,metric,sum(r[numkey] for r in evaluable),sum(r[denkey] for r in evaluable),n,n-len(evaluable),notes='Source-reference denominators required consistent across matched configs; disagreements/zero applicability excluded')
    multi=[rr['scores'][conf] for rr in common if len({rr['scores'][c].get('expected_contribution_count') for c in required})==1 and (rr['scores'][conf].get('expected_contribution_count') or 0)>1 and rr['scores'][conf].get('missing_contribution_count') is not None]
    add(scope,split,conf,'multi_contribution_omission_rate',sum(r['missing_contribution_count']>0 for r in multi),len(multi),n,n-len(multi))
    add(scope,split,conf,'full_conclusion_support_rate',sum(r['full_conclusion_grade'] in ['Explicit','Supported Paraphrase'] for r in data),sum(r['full_conclusion_grade']!='Insufficient' for r in data),n,sum(r['full_conclusion_grade']=='Insufficient' for r in data))
    # Counts refer to output contribution units; abstention entries are excluded.
    output_n=0
    for rr in common:
     fid=rr['selection']['family_id'];m=active_main(fid)
     if conf=='D2_ARCHIVED':
      cs=rr['comparison'] # Actual count independently from archive, loaded below.
      output_n+=old_counts[fid]
     elif conf=='D2_DEEPSEEK_REPLAY':
      p=W/'working/d2_replay'/(fid.replace(':','_')+'.json');v=load(p)['result'];output_n+=sum(c['evidence_level']=='EXPLICIT_MECHANISM' for c in v['contributions'])
     elif conf=='D3_EXTRACT_ONLY':output_n+=len(load('working/extract_only/'+fid.replace(':','_')+'.json')['result']['contributions'])
     elif conf=='D3_FIDELITY':output_n+=len(m['original']['contributions'])
     else:output_n+=len(m['final']['contributions'])
    add(scope,split,conf,'mean_contributions_per_family',output_n,n,n,unit='contributions/family')
    add(scope,split,conf,'oversplit_contribution_rate',sum(r['oversplit_count'] for r in data),output_n,n,notes='Auditor oversplit units / actual explicit output units; not a human error rate')
    add(scope,split,conf,'hallucinated_contribution_rate',sum(r['hallucination_count'] for r in data),output_n,n)
    for dim in ['technical_mechanism','materials','process_method','parameters','multiple_contributions']:
     add(scope,split,conf,dim+'_gold_accuracy',None,None,0,tier='Gold',notes='N/A: zero independent human Gold labels; AI must not be promoted to human truth')
 return rows

def relevance_metrics(main,node_records):
 out=[];confusions=collections.Counter();cases=[]
 def add(config,metric,num,den,n,notes):out.append(dict(scope='targeted_relevance_nodes',split='postfreeze_audit',configuration=config,metric=metric,numerator=num,denominator=den,value=num/den if den else None,label_tier='Silver',sample_n=n,unknown_n=0,unit='rate',notes=notes))
 reference_positive=[r for r in node_records if r['result']['legacy_reference'] in ['Direct','Manufacturing','Transferable']]
 add('D2_FINAL_SINGLE_LABEL','unrelated_despite_engineering_reference',sum(r['selection']['d2_category']=='Unrelated' for r in reference_positive),len(reference_positive),len(node_records),'Node-level targeted sample; independent same-model Silver reference positive Direct/Manufacturing/Transferable; not full-corpus prevalence')
 directs=[r for r in node_records if r['selection']['d2_category']=='Direct' and r['result']['legacy_reference']!='Uncertain']
 add('D2_FINAL_SINGLE_LABEL','direct_false_discovery_rate',sum(r['result']['legacy_reference']!='Direct' for r in directs),len(directs),len(node_records),'Denominator predicted Direct with determinate Silver reference; includes category-scope disagreements')
 matched=[]
 for r in node_records:
  old=r['selection']['d2_category'];ref=r['result'];confusions[('D2_SINGLE',old,ref['legacy_reference'])]+=1
  fs=r['selection']['family_ids']
  if len(fs)==1 and fs[0] in main and len(main[fs[0]]['final']['contributions'])==1 and not ref['source_families_disagree']:
   fid=fs[0];pred=main[fid]['relevance'];matched.append((pred,ref));confusions[('D3_A',pred['axis_a'],ref['axis_a'])]+=1;confusions[('D3_B',pred['axis_b'],ref['axis_b'])]+=1
   if pred['axis_a']!=ref['axis_a'] or pred['axis_b']!=ref['axis_b']:cases.append(dict(family_id=fid,technology_id=r['selection']['technology_id'],d2_category=old,d3_a=pred['axis_a'],d3_b=pred['axis_b'],reference_a=ref['axis_a'],reference_b=ref['axis_b'],reason=ref['mechanism_rationale']))
 for axis,pos,uncertain in [('axis_a',{'A1','A2'},'AU'),('axis_b',{'B1','B2','B3'},'BU')]:
  valid=[(p,r) for p,r in matched if r[axis]!=uncertain];positive=[(p,r) for p,r in valid if r[axis] in pos];negative=[(p,r) for p,r in valid if r[axis] not in pos]
  add('D3_FROZEN_TWO_AXES',axis+'_false_negative_rate',sum(p[axis] not in pos for p,r in positive),len(positive),len(matched),'Single-family node and single D3 contribution only; frozen prediction vs separate node Silver audit; scopes can differ')
  add('D3_FROZEN_TWO_AXES',axis+'_false_positive_rate',sum(p[axis] in pos for p,r in negative),len(negative),len(matched),'Reference negatives form denominator; uncertain reference excluded; no human Gold')
 return out,[dict(system=k[0],predicted=k[1],reference=k[2],count=v) for k,v in confusions.items()],cases
