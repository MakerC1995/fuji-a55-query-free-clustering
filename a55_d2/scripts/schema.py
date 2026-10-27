"""Strict evaluator for the JSON-Schema keywords used by this project."""
import re,json,unicodedata
from common import object_hash
def s(maxlen=700):return dict(type='string',maxLength=maxlen)
def arr(item,maxn=12,minn=0):return dict(type='array',items=item,minItems=minn,maxItems=maxn)
def obj(props):return dict(type='object',properties=props,required=list(props),additionalProperties=False)
def enum(items):return dict(type='string',enum=items)
facet=obj(dict(text=dict(type=['string','null'],maxLength=700),evidence_ids=arr(s(16),12)))
evidence=obj(dict(id=dict(type='string',pattern='^E[1-9][0-9]*$'),field=enum(['title','abstract']),quote=dict(type='string',minLength=2,maxLength=280)))
list_facet=obj(dict(text=dict(type='string',minLength=1,maxLength=400),evidence_ids=arr(s(16),8)))
contribution=obj(dict(
 evidence_spans=arr(evidence,18,1),
 technical_object=facet,technical_problem=facet,technical_mechanism=facet,implementation=facet,expected_effect=facet,applicable_conditions=facet,
 materials=arr(list_facet,8),process_methods=arr(list_facet,8),structures=arr(list_facet,8),
 parameters=arr(obj(dict(name=s(120),kind=enum(['TEMPERATURE','PRESSURE','VOLTAGE','TIME','LENGTH','FREQUENCY','COMPOSITION_RATIO','COUNT','OTHER_QUANTITATIVE']),raw=dict(type='string',minLength=1,maxLength=120,pattern='^.*[0-9０-９].*$'),evidence_ids=arr(s(16),8,1))),8),
 mechanism_type=enum(['STRUCTURE','PROCESS','CONTROL','MATERIAL','CHEMICAL','COMPUTATIONAL','COMPOSITE','UNDISCLOSED']),
 evidence_level=enum(['EXPLICIT_MECHANISM','MECHANISM_UNDISCLOSED','INSUFFICIENT_EVIDENCE']),
 ambiguity_notes=s(1000)))
EXTRACTION_SCHEMA=obj(dict(family_id=dict(type='string',minLength=1),contributions=arr(contribution,4,1)))
EXTRACTION_SCHEMA['$schema']='https://json-schema.org/draft/2020-12/schema'
PAIR_SCHEMA=obj(dict(judgments=arr(obj(dict(left=s(80),right=s(80),relation=enum(['Same','Parent-Child','Alternative','Complementary','Related','Distinct','Uncertain']),parent_id=dict(type=['string','null']),rationale=s(1000),evidence_ids_left=arr(s(16),8),evidence_ids_right=arr(s(16),8))),20,1)))
SUPPORTED={'$schema','type','properties','required','additionalProperties','items','minItems','maxItems','enum','minLength','maxLength','pattern'}
def check_schema(schema):
 assert not set(schema)-SUPPORTED,'Unsupported schema keyword'
 for v in schema.get('properties',{}).values():check_schema(v)
 if 'items' in schema:check_schema(schema['items'])
def validate(value,schema,path='$'):
 typ=schema.get('type');types=typ if isinstance(typ,list) else [typ]
 def ok(t):
  return {'object':isinstance(value,dict),'array':isinstance(value,list),'string':isinstance(value,str),'null':value is None,'boolean':type(value) is bool,'integer':type(value) is int,'number':type(value) in [int,float]}.get(t,False)
 if typ is not None and not any(ok(t) for t in types):raise ValueError(path+': wrong type')
 if 'enum' in schema and value not in schema['enum']:raise ValueError(path+': invalid enum')
 if isinstance(value,dict):
  missing=set(schema.get('required',[]))-set(value)
  if missing:raise ValueError(path+': missing '+','.join(sorted(missing)))
  props=schema.get('properties',{})
  if schema.get('additionalProperties') is False and set(value)-set(props):raise ValueError(path+': extra properties')
  for k,v in value.items():
   if k in props:validate(v,props[k],path+'.'+k)
 if isinstance(value,list):
  if not schema.get('minItems',0)<=len(value)<=schema.get('maxItems',10**9):raise ValueError(path+': array length')
  for i,v in enumerate(value):validate(v,schema['items'],path+f'[{i}]')
 if isinstance(value,str):
  if not schema.get('minLength',0)<=len(value)<=schema.get('maxLength',10**9):raise ValueError(path+': string length')
  if schema.get('pattern') and not re.search(schema['pattern'],value):raise ValueError(path+': pattern')
def numbers(text):
 return set(re.findall(r'(?<![0-9])[-+]?\d+(?:[.,]\d+)*(?:[eE][-+]?\d+)?',unicodedata.normalize('NFKC',text).translate(str.maketrans({'−':'-','‐':'-','‑':'-','﹣':'-'}))))
def source_numbers(text):
 values=numbers(text)
 normalized=unicodedata.normalize('NFKC',text)
 # Retain original tokens and allow conventional grouped integer presentation.
 for grouped in re.findall(r'(?<![0-9])([0-9]{1,3}(?:,[0-9]{3})+)(?![0-9])',normalized):
  values.add(grouped.replace(',',''))
 # Japanese wari denotes one tenth, an exact language-level conversion.
 for raw in re.findall(r'(\d+(?:\.\d+)?)割',normalized):
  converted=float(raw)*10
  values.add(str(int(converted)) if converted.is_integer() else str(converted))
 return values
def audit_extraction(result,doc):
 validate(result,EXTRACTION_SCHEMA)
 if result['family_id']!=doc['family_id']:raise ValueError('Family ID mismatch')
 seen=set()
 for i,c in enumerate(result['contributions'],1):
  em={}
  for e in c['evidence_spans']:
   if e['id'] in em:raise ValueError('Duplicate evidence ID')
   text=doc[e['field']] or '';start=text.find(e['quote'])
   if start<0:raise ValueError('Non-verbatim quote '+e['id']+' in '+e['field'])
   em[e['id']]=e;e['start']=start;e['end']=start+len(e['quote'])
  facets=[c[k] for k in ['technical_object','technical_problem','technical_mechanism','implementation','expected_effect','applicable_conditions']]
  facets+=c['materials']+c['process_methods']+c['structures']
  for f in facets:
   ids=f['evidence_ids']
   if any(k not in em for k in ids):raise ValueError('Unknown evidence reference')
   if f['text'] is None:
    if ids:raise ValueError('Null facet cannot claim evidence')
   else:
    if not f['text'].strip():raise ValueError('Populated facet is empty')
    supported=' '.join(em[k]['quote'] for k in ids)
    if not numbers(f['text'])<=source_numbers((doc.get('title') or '')+' '+(doc.get('abstract') or '')):raise ValueError('NUMERIC_VALUE_NOT_IN_SOURCE: '+f['text'][:180])
  for p in c['parameters']:
   if any(k not in em for k in p['evidence_ids']):raise ValueError('Parameter evidence missing')
   if not any(p['raw'] in em[k]['quote'] for k in p['evidence_ids']):raise ValueError('Parameter is not literal source text')
  if c['evidence_level']=='EXPLICIT_MECHANISM' and (not c['technical_mechanism']['text'] or c['mechanism_type']=='UNDISCLOSED'):raise ValueError('Explicit mechanism is missing')
  if c['evidence_level']!='EXPLICIT_MECHANISM' and c['technical_mechanism']['text'] is not None:raise ValueError('Unrevealed mechanism must remain null')
  if not doc.get('abstract') and c['evidence_level']!='INSUFFICIENT_EVIDENCE':raise ValueError('Conservative title-only policy requires abstention')
  key=object_hash([c['technical_mechanism']['text'],c['implementation']['text']])
  if key in seen:raise ValueError('Duplicate contribution within family')
  seen.add(key)
  c['contribution_id']='C_'+object_hash([doc['family_id'],doc['text_hash'],i,c['technical_mechanism']['text'],c['implementation']['text']])[:20]
  c['family_id']=doc['family_id'];c['source_text_hash']=doc['text_hash'];c['effect_interpretation']='disclosed_or_claimed_not_independently_measured'
 return result
check_schema(EXTRACTION_SCHEMA);check_schema(PAIR_SCHEMA)


# Compact model-facing protocol: evidence supports fields, IDs are assigned by code.
CORE_FIELDS=['technical_object','technical_problem','technical_mechanism','implementation','expected_effect','applicable_conditions']
LIST_FIELDS=['materials','process_methods','structures']
WIRE_FIELDS=CORE_FIELDS+LIST_FIELDS+['parameters']
wire_props=dict(evidence_spans=arr(obj(dict(field=enum(['title','abstract']),quote=dict(type='string',minLength=2,maxLength=280),supports=arr(enum(WIRE_FIELDS),10,1))),12,1))
for name in CORE_FIELDS:wire_props[name]=dict(type=['string','null'],maxLength=700)
for name in LIST_FIELDS:wire_props[name]=arr(dict(type='string',minLength=1,maxLength=400),8)
wire_props['parameters']=arr(obj(dict(name=s(120),kind=enum(['TEMPERATURE','PRESSURE','VOLTAGE','TIME','LENGTH','FREQUENCY','COMPOSITION_RATIO','COUNT','OTHER_QUANTITATIVE']),raw=dict(type='string',minLength=1,maxLength=120,pattern='^.*[0-9０-９].*$'))),8)
wire_props['mechanism_type']=contribution['properties']['mechanism_type']
wire_props['evidence_level']=contribution['properties']['evidence_level']
wire_props['ambiguity_notes']=s(1000)
EXTRACTION_WIRE_SCHEMA=obj(dict(family_id=dict(type='string',minLength=1),contributions=arr(obj(wire_props),4,1)))
check_schema(EXTRACTION_WIRE_SCHEMA)

def literal_index(text,needle,quantity=False):
 start=0
 while needle:
  pos=text.find(needle,start)
  if pos<0:return -1
  if quantity:
   before=unicodedata.normalize("NFKC",text[pos-1:pos]) if pos else ""
   after=unicodedata.normalize("NFKC",text[pos+len(needle):pos+len(needle)+1])
   first=unicodedata.normalize("NFKC",needle[:1]);last=unicodedata.normalize("NFKC",needle[-1:])
   if (first.isdigit() and (before.isdigit() or before==".")) or (last.isdigit() and (after.isdigit() or (after=="." and text[pos+len(needle)+1:pos+len(needle)+2].isdigit()))):
    start=pos+1;continue
  return pos
 return -1

def normalize_long_verbatim_quotes(wire,doc):
 clean=copy.deepcopy(wire);changes=[];hints=[]
 if not isinstance(clean,dict) or not isinstance(clean.get("contributions"),list):return clean,[],[]
 for c in clean["contributions"]:
  changed=[];offsets=[];out=[]
  for e in c.get("evidence_spans",[]):
   if not isinstance(e,dict) or not isinstance(e.get("quote"),str) or e.get("field") not in ["title","abstract"]:
    out.append(e);continue
   quote=e["quote"];text=doc.get(e["field"]) or "";origin=text.find(quote)
   if len(quote)>280 and origin>=0:
    rest=quote;cursor=0;parts=[]
    while rest:
     if len(rest)<=260:part=rest;rest=""
     else:
      cut=rest.rfind(" ",0,260)
      if cut<80:cut=260
      if len(rest)-cut==1:cut-=1
      part=rest[:cut];rest=rest[cut:]
     parts.append(part);offsets.append(dict(field=e["field"],quote=part,start=origin+cursor));cursor+=len(part)
     out.append(dict(field=e["field"],quote=part,supports=e.get("supports",[])))
    assert "".join(parts)==quote
    changed.append(dict(kind="split_long_verbatim_quote",field=e["field"],original_length=len(quote),segments=len(parts)))
   else:out.append(e)
  # Deduplicate only identical source fragments, never paraphrase or fuzzy-match them.
  unique=[];seen={}
  for e in out:
   if not isinstance(e,dict):unique.append(e);continue
   key=(e.get("field"),e.get("quote"))
   if key in seen:
    old=unique[seen[key]]
    old["supports"]=list(dict.fromkeys(old.get("supports",[])+e.get("supports",[])))
   else:seen[key]=len(unique);unique.append(e)
  c["evidence_spans"]=unique;changes.append(changed);hints.append(offsets)
 return clean,changes,hints
def has_quantitative_value(raw):
 normalized=unicodedata.normalize('NFKC',raw)
 # Do not count index digits in V1, T0, d33, etc. as quantitative values.
 without_identifiers=re.sub(r'(?<![A-Za-zΑ-ω])(?:[A-Za-zΑ-ω]{1,3}_?[0-9]+|[A-Za-zΑ-ω] [0-9]+)(?![0-9])','',normalized)
 return bool(re.search(r'[0-9]',without_identifiers))
def audit_wire_extraction(wire,doc):
 wire,normalizations,offset_hints=normalize_long_verbatim_quotes(wire,doc)
 normalized_schema=copy.deepcopy(EXTRACTION_WIRE_SCHEMA)
 normalized_schema["properties"]["contributions"]["items"]["properties"]["evidence_spans"]["maxItems"]=18
 validate(wire,normalized_schema)
 result=dict(family_id=wire["family_id"],contributions=[])
 for item_index,item in enumerate(wire["contributions"]):
  spans=[];support={name:[] for name in WIRE_FIELDS};alignment={}
  for j,e in enumerate(item["evidence_spans"],1):
   eid="E"+str(j);spans.append(dict(id=eid,field=e["field"],quote=e["quote"]))
   for name in set(e["supports"]):support[name].append(eid)
  def align(name,text,quantity=False):
   if text is None:return []
   marked=support[name]
   if quantity:marked=[eid for eid in marked if literal_index(next(e["quote"] for e in spans if e["id"]==eid),text,True)>=0]
   if marked:return marked
   for e in spans:
    if literal_index(e["quote"],text,quantity)>=0:
     alignment.setdefault(name,[]).append("exact_literal_in_existing_span")
     return [e["id"]]
   if 2<=len(text)<=280:
    for field in ["abstract","title"]:
     if literal_index(doc.get(field) or "",text,quantity)>=0:
      eid="E"+str(len(spans)+1);spans.append(dict(id=eid,field=field,quote=text))
      alignment.setdefault(name,[]).append("exact_literal_aligned_to_original_source")
      return [eid]
   return []
  c=dict(evidence_spans=spans);missing=[]
  for name in CORE_FIELDS:
   ids=align(name,item[name]);c[name]=dict(text=item[name],evidence_ids=ids)
   if item[name] is not None and not ids:missing.append(name+": "+item[name][:100])
  for name in LIST_FIELDS:
   rows=[]
   for text in item[name]:
    ids=align(name,text);rows.append(dict(text=text,evidence_ids=ids))
    if not ids:missing.append(name+": "+text[:100])
   c[name]=rows
  c["parameters"]=[];rejected_parameters=[]
  for par in item["parameters"]:
   if not has_quantitative_value(par["raw"]):
    rejected_parameters.append(dict(name=par["name"],model_type=par["kind"],model_claim=par["raw"],reason="Digits occur only in variable/part identifiers, not a source quantitative value; withheld"))
    missing.append("parameters: symbol/index-only proposed value withheld for "+par["name"])
    continue
   ids=align("parameters",par["raw"],True)
   if not ids:
    rejected_parameters.append(dict(name=par["name"],model_type=par["kind"],model_claim=par["raw"],reason="No exact bounded source span for the proposed value; claim withheld, not published as a source parameter"))
    missing.append("parameters: unverified model value withheld for "+par["name"])
   else:c["parameters"].append(dict(**par,evidence_ids=ids))
  # Missing facet links are explicit review items, not silently invented citations.
  # Reused literal evidence does not require re-generating or translating any source text.
  if len(spans)>18:raise ValueError("Too many evidence spans after exact alignment")
  for name in ["mechanism_type","evidence_level","ambiguity_notes"]:c[name]=item[name]
  result["contributions"].append(c)
  c["_literal_alignment_pending"]=(alignment,missing,normalizations[item_index],offset_hints[item_index],rejected_parameters)
 pending=[c.pop("_literal_alignment_pending") for c in result["contributions"]]
 out=audit_extraction(result,doc)
 for c,(a,gaps,norm,hints,rejected) in zip(out["contributions"],pending):
  c["evidence_alignment_provenance"]=a;c["field_evidence_gaps"]=gaps;c["semantic_validation_status"]="PENDING_SOURCE_AUDIT"
  c["schema_version"]="D2-contribution-v3";c["wire_canonicalization"]=norm
  c["rejected_parameter_claims"]=rejected;c["parameter_extraction_status"]="SOME_MODEL_PARAMETERS_WITHHELD" if rejected else ("LITERAL_PARAMETERS_RETAINED" if c["parameters"] else "NO_STRUCTURED_PARAMETER_VALUES")
  for e in c["evidence_spans"]:
   for h in hints:
    if e["field"]==h["field"] and e["quote"]==h["quote"]:
     e["start"]=h["start"];e["end"]=h["start"]+len(e["quote"]);break
  c["numeric_citation_gaps"]=[name for name in CORE_FIELDS if c[name]["text"] and not numbers(c[name]["text"])<=numbers(" ".join(e["quote"] for e in c["evidence_spans"] if e["id"] in c[name]["evidence_ids"]))]
 validate(out,ENRICHED_SCHEMA)
 return out


import copy
enriched=copy.deepcopy(contribution)
enriched['properties']['evidence_spans']['items']['properties'].update(start=dict(type='integer'),end=dict(type='integer'))
enriched['properties']['evidence_spans']['items']['required']+=['start','end']
alignment_schema=dict(type='object',properties={name:arr(s(100),30) for name in WIRE_FIELDS},additionalProperties=False)
extra=dict(
 contribution_id=dict(type='string',pattern='^C_[a-f0-9]{20}$'),
 family_id=s(100),source_text_hash=dict(type='string',pattern='^[a-f0-9]{64}$'),
 effect_interpretation=enum(['disclosed_or_claimed_not_independently_measured']),
 evidence_alignment_provenance=alignment_schema,field_evidence_gaps=arr(s(2000),100),
 semantic_validation_status=enum(['PENDING_SOURCE_AUDIT']),
 numeric_citation_gaps=arr(enum(CORE_FIELDS),6),schema_version=enum(['D2-contribution-v3']))
enriched['properties'].update(extra);enriched['required']+=list(extra)
enriched['properties']['wire_canonicalization']=arr(obj(dict(kind=enum(['split_long_verbatim_quote']),field=enum(['title','abstract']),original_length=dict(type='integer'),segments=dict(type='integer'))),30)
enriched['properties']['rejected_parameter_claims']=arr(obj(dict(name=s(120),model_type=s(80),model_claim=s(4000),reason=s(500))),8)
enriched['properties']['parameter_extraction_status']=enum(['SOME_MODEL_PARAMETERS_WITHHELD','LITERAL_PARAMETERS_RETAINED','NO_STRUCTURED_PARAMETER_VALUES'])
ENRICHED_SCHEMA=copy.deepcopy(EXTRACTION_SCHEMA);ENRICHED_SCHEMA['properties']['contributions']['items']=enriched
check_schema(ENRICHED_SCHEMA)


def make_source_spans(doc,limit=240):
 spans=[];seq=0
 for field in ['title','abstract']:
  text=doc.get(field) or '';start=0
  while start<len(text):
   end=min(len(text),start+limit)
   if end<len(text):
    found=max(text.rfind(' ',start+80,end),text.rfind('。',start+80,end),text.rfind('；',start+80,end))
    if found>=start+80:end=found+1
    if len(text)-end==1:end+=1
   seq+=1;spans.append(dict(source_id='S'+str(seq).zfill(3),field=field,text=text[start:end],start=start,end=end));start=end
  assert ''.join(r['text'] for r in spans if r['field']==field)==text
 return spans
def source_id_schema(canonical,spans):
 model_schema=copy.deepcopy(canonical)
 prop=model_schema['properties']['contributions']['items']['properties']
 prop['evidence_spans']['items']=obj(dict(source_id=enum([r['source_id'] for r in spans]),supports=arr(enum(WIRE_FIELDS),10,1)))
 prop['ambiguity_notes']=dict(type=['string','null'],maxLength=1000)
 return model_schema
def canonical_from_source_ids(result,model_schema,spans):
 # Invalid structured parameter strings must not erase a genuine disclosed mechanism.
 # Preserve the original raw response; withhold those values from factual parameters.
 relaxed=copy.deepcopy(model_schema)
 raw_schema=relaxed['properties']['contributions']['items']['properties']['parameters']['items']['properties']['raw']
 raw_schema.pop('pattern',None);raw_schema['maxLength']=2000;raw_schema['minLength']=0
 validate(result,relaxed);lookup={r['source_id']:r for r in spans};out=copy.deepcopy(result);lineage=[]
 for c in out['contributions']:
  origins=[];quotes=[]
  for e in c['evidence_spans']:
   original=lookup[e['source_id']]
   quotes.append(dict(field=original['field'],quote=original['text'],supports=e['supports']))
   origins.append(dict(**original,supports=e['supports']))
  c['evidence_spans']=quotes
  rejected=[];kept=[]
  parameter_schema=EXTRACTION_WIRE_SCHEMA['properties']['contributions']['items']['properties']['parameters']['items']
  for par in c['parameters']:
   try:validate(par,parameter_schema);kept.append(par)
   except ValueError as err:rejected.append(dict(name=par['name'],model_type=par['kind'],model_claim=par['raw'],reason='Model parameter violates quantitative literal contract; withheld: '+str(err)))
  c['parameters']=kept
  if origins and rejected:origins[0]['transport_rejected_parameters']=rejected
  if c['ambiguity_notes'] is None:c['ambiguity_notes']=''
  lineage.append(origins)
 validate(out,EXTRACTION_WIRE_SCHEMA)
 return out,lineage
def apply_anchor_positions(result,lineage,doc):
 for c,origins in zip(result['contributions'],lineage):
  rejected=[p for x in origins for p in x.get('transport_rejected_parameters',[])]
  if rejected:
   c.setdefault('rejected_parameter_claims',[]).extend(rejected)
   c['parameter_extraction_status']='SOME_MODEL_PARAMETERS_WITHHELD'
   c['field_evidence_gaps'].append('parameters: invalid model parameter strings withheld in source-ID transport')
  for e in c['evidence_spans']:
   match=next((x for x in origins if x['field']==e['field'] and x['text']==e['quote']),None)
   if match:
    assert (doc[e['field']] or '')[match['start']:match['end']]==e['quote']
    e['start']=match['start'];e['end']=match['end']
 return result

# Optional provenance for separately preserved source corrections.
enriched['properties']['source_model_contribution_id']=s(80)
enriched['properties']['curation_provenance_json']=s(15000)

enriched['properties']['semantic_validation_status']=enum(['PENDING_SOURCE_AUDIT','AI_SOURCE_CORRECTED_PENDING_HUMAN_REVIEW'])

enriched['properties']['refinement_provenance_json']=s(15000)
enriched['properties']['semantic_validation_status']=enum(['PENDING_SOURCE_AUDIT','AI_SOURCE_CORRECTED_PENDING_HUMAN_REVIEW','LLM_REFINED_PENDING_SOURCE_AUDIT'])
