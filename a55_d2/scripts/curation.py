"""Explicit assistant source corrections. Raw model extractions remain immutable."""
from common import *
from schema import ENRICHED_SCHEMA,validate
import copy
def apply(c,doc):
 path=W/'evidence/ASSISTANT_SOURCE_AMENDMENTS.json'
 if not path.exists():return c
 patches=load(str(path)).get('families',{});patch=patches.get(c['family_id'])
 if not patch:return c
 if patch.get('only_original_cid') and c['contribution_id']!=patch['only_original_cid']:return c
 out=copy.deepcopy(c);old_id=c['contribution_id'];old_fields={}
 for name,edit in patch.get('facets',{}).items():
  old_fields[name]=out[name]
  if edit['text'] is None:out[name]=dict(text=None,evidence_ids=[]);continue
  ids=[]
  for quote in edit['quotes']:
   text=doc[quote['field']] or ''
   assert text[quote['start']:quote['end']]==quote['quote']
   existing=next((e for e in out['evidence_spans'] if e['field']==quote['field'] and e['start']==quote['start'] and e['end']==quote['end']),None)
   if not existing:
    existing=dict(id='E'+str(len(out['evidence_spans'])+1),**quote);out['evidence_spans'].append(existing)
   ids.append(existing['id'])
  assert ids
  out[name]=dict(text=edit['text'],evidence_ids=ids)
 for fix in patch.get('parameter_kind_fixes',[]):
  for par in out['parameters']:
   if par['name']==fix['name']:
    old_fields.setdefault('parameter_kind_fixes',[]).append(dict(name=par['name'],original_kind=par['kind']))
    par['kind']=fix['kind']
 if patch.get('ambiguity_notes_append'):
  old_fields['ambiguity_notes']=out['ambiguity_notes'];out['ambiguity_notes']=(out['ambiguity_notes']+' '+patch['ambiguity_notes_append']).strip()
 if 'mechanism_type' in patch:
  old_fields['mechanism_type']=out['mechanism_type'];out['mechanism_type']=patch['mechanism_type']
 drop=set(patch.get('drop_parameter_names',[]))
 if drop:
  kept=[]
  for par in out['parameters']:
   if par['name'] in drop:
    old_fields.setdefault('removed_parameters',[]).append(par)
    out.setdefault('rejected_parameter_claims',[]).append(dict(name=par['name'],model_type=par['kind'],model_claim=par['raw'],reason='Source review: this defines a variable or a measurement point, not a numeric value of the named quantity; withheld'))
   else:kept.append(par)
  out['parameters']=kept
  if old_fields.get('removed_parameters'):out['parameter_extraction_status']='SOME_MODEL_PARAMETERS_WITHHELD'
 out['source_model_contribution_id']=old_id
 out['contribution_id']='C_'+object_hash(dict(original_cid=old_id,patch=patch,version='assistant-source-amendment-v1'))[:20]
 out['curation_provenance_json']=stable(dict(reviewer='AI assistant, not human Gold',patch_sha256=object_hash(patch),reason=patch['reason'],original_fields=old_fields))
 out['semantic_validation_status']='AI_SOURCE_CORRECTED_PENDING_HUMAN_REVIEW'
 changed=set(patch.get('facets',{}))
 out['field_evidence_gaps']=[g for g in out['field_evidence_gaps'] if g.split(':')[0] not in changed]
 out['numeric_citation_gaps']=[g for g in out['numeric_citation_gaps'] if g not in changed]
 validate(out,ENRICHED_SCHEMA['properties']['contributions']['items'])
 return out
