"""Synthetic unit fixtures only. No real patent result or inference is fabricated."""
import sys,unittest,copy,tempfile,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import common,schema,extract
from unittest.mock import patch
def fixture():
 title='Test device';abstract='The test device uses a 5 nm porous layer to reduce drift.'
 doc=dict(family_id='test:synthetic',title=title,abstract=abstract,raw_text=title+'\n\n'+abstract)
 doc['text_hash']=common.digest_bytes(doc['raw_text'].encode())
 def f(text):return dict(text=text,evidence_ids=['E1'] if text is not None else [])
 c=dict(technical_object=f('测试器件'),technical_problem=f(None),technical_mechanism=f('采用5 nm多孔层'),implementation=f('在器件中使用多孔层'),expected_effect=f('降低漂移'),applicable_conditions=f(None),materials=[],process_methods=[],structures=[f('多孔层')],parameters=[dict(name='layer thickness',kind='LENGTH',raw='5 nm',evidence_ids=['E1'])],evidence_spans=[dict(id='E1',field='abstract',quote=abstract)],evidence_level='EXPLICIT_MECHANISM',mechanism_type='STRUCTURE',ambiguity_notes='')
 return doc,dict(family_id=doc['family_id'],contributions=[c])

def to_wire(result):
 wire=dict(family_id=result["family_id"],contributions=[])
 for c in result["contributions"]:
  item={}
  for e in c["evidence_spans"]:
   support=[]
   for name in schema.CORE_FIELDS:
    if e["id"] in c[name]["evidence_ids"]:support.append(name)
   for name in schema.LIST_FIELDS+["parameters"]:
    if any(e["id"] in row["evidence_ids"] for row in c[name]):support.append(name)
   item.setdefault("evidence_spans",[]).append(dict(field=e["field"],quote=e["quote"],supports=support))
  for name in schema.CORE_FIELDS:item[name]=c[name]["text"]
  for name in schema.LIST_FIELDS:item[name]=[row["text"] for row in c[name]]
  item["parameters"]=[{k:v for k,v in row.items() if k!="evidence_ids"} for row in c["parameters"]]
  for name in ["mechanism_type","evidence_level","ambiguity_notes"]:item[name]=c[name]
  wire["contributions"].append(item)
 return wire

class EvidenceTests(unittest.TestCase):
 def test_valid_and_stable_id(self):
  d,r=fixture();a=schema.audit_extraction(copy.deepcopy(r),d);b=schema.audit_extraction(copy.deepcopy(r),d)
  self.assertEqual(a['contributions'][0]['contribution_id'],b['contributions'][0]['contribution_id'])
  e=a['contributions'][0]['evidence_spans'][0];self.assertEqual(d[e['field']][e['start']:e['end']],e['quote'])
 def mutate_reject(self,fn):
  d,r=fixture();fn(r)
  with self.assertRaises((ValueError,AssertionError)):schema.audit_extraction(r,d)
 def test_nonverbatim(self):self.mutate_reject(lambda r:r['contributions'][0]['evidence_spans'][0].update(quote='The test device uses a 5  nm porous layer.'))
 def test_wrong_field(self):self.mutate_reject(lambda r:r['contributions'][0]['evidence_spans'][0].update(field='title'))
 def test_hallucinated_number(self):self.mutate_reject(lambda r:r['contributions'][0]['technical_mechanism'].update(text='采用10 nm多孔层'))
 def test_parameter_paraphrase(self):self.mutate_reject(lambda r:r['contributions'][0]['parameters'][0].update(raw='5纳米'))
 def test_family_mismatch(self):self.mutate_reject(lambda r:r.update(family_id='test:wrong'))
 def test_unknown_evidence(self):self.mutate_reject(lambda r:r['contributions'][0]['technical_mechanism'].update(evidence_ids=['E99']))
 def test_null_supported(self):self.mutate_reject(lambda r:r['contributions'][0]['technical_problem'].update(evidence_ids=['E1']))
 def test_missing_mechanism(self):self.mutate_reject(lambda r:r['contributions'][0]['technical_mechanism'].update(text=None,evidence_ids=[]))
 def test_duplicate_contribution(self):self.mutate_reject(lambda r:r['contributions'].append(copy.deepcopy(r['contributions'][0])))
 def test_extra_field(self):self.mutate_reject(lambda r:r['contributions'][0].update(guessed_claims='not supplied'))
 def test_unrevealed_is_valid(self):
  d,r=fixture();c=r['contributions'][0];c.update(evidence_level='MECHANISM_UNDISCLOSED',mechanism_type='UNDISCLOSED');c['technical_mechanism']=dict(text=None,evidence_ids=[])
  schema.audit_extraction(r,d)
 def test_title_only_abstention(self):
  d,r=fixture();d['abstract']='';c=r['contributions'][0];c['evidence_spans']=[dict(id='E1',field='title',quote=d['title'])]
  for k in ['technical_problem','technical_mechanism','implementation','expected_effect','applicable_conditions']:c[k]=dict(text=None,evidence_ids=[])
  c.update(structures=[],parameters=[],evidence_level='INSUFFICIENT_EVIDENCE',mechanism_type='UNDISCLOSED')
  schema.audit_extraction(r,d)
 def test_title_only_cannot_claim_mechanism(self):
  d,r=fixture();d['title']=d['abstract'];d['abstract']='';r['contributions'][0]['evidence_spans'][0]['field']='title'
  with self.assertRaises(ValueError):schema.audit_extraction(r,d)
 def test_schema_no_unsupported_keywords(self):schema.check_schema(schema.EXTRACTION_SCHEMA);schema.check_schema(schema.PAIR_SCHEMA)
 def test_wire_evidence_ids_are_program_assigned(self):
  d,r=fixture();out=schema.audit_wire_extraction(to_wire(r),d);self.assertEqual(out['contributions'][0]['evidence_spans'][0]['id'],'E1')
 def test_exact_alignment_can_repair_omitted_field_tags(self):
  d,r=fixture();wire=to_wire(r);c=wire['contributions'][0]
  c.update(technical_object='test device',technical_problem=None,technical_mechanism='uses a 5 nm porous layer',implementation=None,expected_effect='reduce drift',structures=['porous layer'])
  c['evidence_spans'][0]['supports']=['technical_mechanism']
  out=schema.audit_wire_extraction(wire,d)
  self.assertTrue(out['contributions'][0]['evidence_alignment_provenance'])
 def test_nonliteral_untagged_translation_stays_flagged(self):
  d,r=fixture();wire=to_wire(r);wire['contributions'][0]['evidence_spans'][0]['supports']=['technical_mechanism']
  out=schema.audit_wire_extraction(wire,d)
  self.assertTrue(out['contributions'][0]['field_evidence_gaps'])
 def test_long_original_quote_split_is_lossless(self):
  d,r=fixture();d['abstract']+=' '+'additional source words '*35
  wire=to_wire(r);wire['contributions'][0]['evidence_spans'][0]['quote']=d['abstract']
  out=schema.audit_wire_extraction(wire,d);c=out['contributions'][0]
  self.assertTrue(c['wire_canonicalization'])
  self.assertTrue(all(len(e['quote'])<=280 and d[e['field']][e['start']:e['end']]==e['quote'] for e in c['evidence_spans']))
  original_parts=[e['quote'] for e in c['evidence_spans']]
  self.assertEqual(''.join(original_parts),d['abstract'])
 def test_long_nonverbatim_quote_is_not_repaired(self):
  d,r=fixture();wire=to_wire(r);wire['contributions'][0]['evidence_spans'][0]['quote']='NOT THE SOURCE '*40
  with self.assertRaises(ValueError):schema.audit_wire_extraction(wire,d)
 def test_parameter_substring_cannot_change_50_to_5(self):
  self.assertEqual(schema.literal_index('50 nm','5',True),-1)
 def test_wire_nonquantitative_parameter_rejected(self):
  d,r=fixture();wire=to_wire(r);wire['contributions'][0]['parameters'][0]['raw']='porous layer'
  with self.assertRaises(ValueError):schema.audit_wire_extraction(wire,d)
 def test_grouped_integer_presentation_equivalence(self):
  self.assertIn('1000',schema.source_numbers('100-1,000 grain size'))
  self.assertNotIn('1000',schema.source_numbers('1,00 grain size'))
 def test_unicode_negative_sign_is_preserved(self):
  self.assertEqual(schema.numbers('Rsk为‑3.5～5'),{'-3.5','5'})
 def test_numeric_symbol_does_not_match_partial_suffix(self):
  self.assertEqual(schema.numbers('d33 与 ε33'),{'33'})
 def test_exact_japanese_wari_percentage_conversion(self):
  self.assertIn('10',schema.source_numbers('柱径差は１割以内'))
  self.assertNotIn('20',schema.source_numbers('柱径差は１割以内'))
 def test_decimal_at_sentence_end_is_not_partial_number(self):
  self.assertGreaterEqual(schema.literal_index('a ratio of 0.12 to 0.50. Next.','0.12 to 0.50',True),0)
  self.assertEqual(schema.literal_index('50.0 nm','50',True),-1)
 def test_variable_indices_are_not_parameter_values(self):
  self.assertFalse(schema.has_quantitative_value('最小電圧値Ｖ１［Ｖ］'))
  self.assertTrue(schema.has_quantitative_value('1/4 Curie temperature'))
  self.assertTrue(schema.has_quantitative_value('0.12 to 0.50'))
  self.assertTrue(schema.has_quantitative_value('not less than 20 nm and not more than 300 nm'))
  self.assertFalse(schema.has_quantitative_value('d 33'))
 def test_boolean_is_not_integer(self):
  with self.assertRaises(ValueError):schema.validate(True,dict(type='integer'))
class CacheTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=ROOT/'tests');self.w=Path(self.temp.name);(self.w/'state').mkdir();self.oldcommon=common.W;self.oldextract=extract.W;common.W=self.w;extract.W=self.w
  self.conn=common.state_db();self.calls=[]
 def tearDown(self):
  self.conn.close();common.W=self.oldcommon;extract.W=self.oldextract;self.temp.cleanup()
 def fake_request(self,kind,key,messages,sch,attempt,conn):
  self.calls.append(messages);common.save('requests/synthetic_unit_test_only.input.json',dict(payload=dict(messages=messages),transport=None));return to_wire(copy.deepcopy(fixture()[1])),'synthetic_unit_test_only'
 def test_cache_and_prompt_change(self):
  d,r=fixture();d['cluster_id']=999
  with patch.object(extract,'request',side_effect=self.fake_request):
   self.assertEqual(extract.do_family(d,'TEST-PROMPT',self.conn),'VALID')
   self.assertEqual(extract.do_family(d,'TEST-PROMPT',self.conn),'CACHED')
   self.assertEqual(len(self.calls),1)
   sent=json.loads(self.calls[0][1]['content']);self.assertEqual(set(sent),{'family_id','title','abstract'})
   self.assertEqual(extract.do_family(d,'TEST-PROMPT-V2',self.conn),'VALID')
   self.assertEqual(len(self.calls),2)
 def test_title_only_uses_honest_rule_without_inference(self):
  d,_=fixture();d['abstract']='';d['raw_text']=d['title'];d['text_hash']=common.digest_bytes(d['raw_text'].encode())
  with patch.object(extract,'request',side_effect=AssertionError('Must not infer from title')):
   self.assertEqual(extract.do_family(d,'TEST-PROMPT',self.conn),'RULE_ABSTENTION')
  saved=json.loads(next((self.w/'extractions').glob('*.json')).read_text())
  self.assertIsNone(saved['model']);self.assertIsNone(saved['request_id'])
  self.assertEqual(saved['result']['contributions'][0]['evidence_level'],'INSUFFICIENT_EVIDENCE')
  self.assertEqual(self.conn.execute('select count(*) from requests').fetchone()[0],0)
 def test_cache_corruption_detected(self):
  d,r=fixture()
  with patch.object(extract,'request',side_effect=self.fake_request):extract.do_family(d,'TEST-PROMPT',self.conn)
  p=next((self.w/'extractions').glob('*.json'));j=json.loads(p.read_text());j['result']['contributions'][0]['technical_mechanism']['text']='CHANGED';p.write_text(json.dumps(j))
  with self.assertRaises(AssertionError):extract.do_family(d,'TEST-PROMPT',self.conn)
 def test_unsupported_parameter_is_withheld_not_published(self):
  d,r=fixture()
  def bad(*a,**kw):
   j=copy.deepcopy(r);j['contributions'][0]['parameters'][0]['raw']='999 nm';common.save('requests/synthetic_bad.input.json',dict(payload=dict(messages=[dict(content='TEST')]),transport=None));return to_wire(j),'synthetic_bad'
  with patch.object(extract,'request',side_effect=bad):self.assertEqual(extract.do_family(d,'TEST-PROMPT',self.conn,max_attempts=2),'VALID')
  saved=json.loads(next((self.w/'extractions').glob('*.json')).read_text());c=saved['result']['contributions'][0]
  self.assertEqual(c['parameters'],[]);self.assertEqual(c['rejected_parameter_claims'][0]['model_claim'],'999 nm')
  self.assertEqual(c['parameter_extraction_status'],'SOME_MODEL_PARAMETERS_WITHHELD')

class RequestAccountingTests(unittest.TestCase):
 setUp=CacheTests.setUp
 tearDown=CacheTests.tearDown
 def test_real_request_path_with_mocked_transport(self):
  d,r=fixture();raw=dict(done=True,done_reason="stop",message=dict(content=json.dumps(r)),prompt_eval_count=10,eval_count=20)
  with patch.object(extract,"api",return_value=raw):
   out,rid=extract.request("unit_test","synthetic-test",[],schema.EXTRACTION_SCHEMA,1,self.conn)
  self.assertEqual(out["family_id"],d["family_id"])
  self.assertEqual(self.conn.execute("select status,prompt_tokens,output_tokens from requests").fetchone(),("RECEIVED",10,20))
  self.assertTrue((self.w/("responses/"+rid+".raw.json")).exists())
 def test_retry_uses_json_mode_with_schema_and_no_message_mutation(self):
  d,r=fixture();raw=dict(done=True,done_reason="stop",message=dict(content=json.dumps(to_wire(r))),prompt_eval_count=10,eval_count=20)
  messages=[dict(role="system",content="TEST"),dict(role="user",content="SOURCE")]
  with patch.object(extract,"api",return_value=raw) as mocked:
   extract.request("unit_test","synthetic-retry",messages,schema.EXTRACTION_WIRE_SCHEMA,2,self.conn)
  payload=mocked.call_args.args[1]
  self.assertEqual(payload["format"],"json")
  self.assertIn("properties",payload["messages"][0]["content"])
  self.assertEqual(messages[0]["content"],"TEST")
  self.assertEqual(payload["options"]["repeat_penalty"],1.08)
 def test_api_rejection_is_separate_from_network_failure(self):
  with patch.object(extract,"api",side_effect=extract.APIProtocolError("HTTP 400 TEST")):
   with self.assertRaises(extract.APIProtocolError):extract.request("unit_test","synthetic-400",[],schema.EXTRACTION_WIRE_SCHEMA,1,self.conn)
  self.assertEqual(self.conn.execute("select status from requests").fetchone()[0],"API_REJECTED")
 def test_source_span_transport_preserves_original_text(self):
  d,r=fixture();spans=schema.make_source_spans(d);wire=to_wire(r)
  abstract_sid=next(s['source_id'] for s in spans if s['field']=='abstract')
  for c in wire['contributions']:
   c['evidence_spans']=[dict(source_id=abstract_sid,supports=e['supports']) for e in c['evidence_spans']]
  raw=dict(done=True,done_reason='stop',message=dict(content=json.dumps(wire)),prompt_eval_count=10,eval_count=20)
  messages=[dict(role='system',content='TEST'),dict(role='user',content=common.stable({k:d[k] for k in ['family_id','title','abstract']}))]
  with patch.object(extract,'api',return_value=raw) as mocked:
   canonical,rid=extract.request('extract','source-span-test',messages,schema.EXTRACTION_WIRE_SCHEMA,1,self.conn)
  sent=json.loads(mocked.call_args.args[1]['messages'][1]['content'])
  self.assertEqual(set(sent),{'family_id','source_spans'})
  for field in ['title','abstract']:self.assertEqual(''.join(x['text'] for x in sent['source_spans'] if x['field']==field),d[field])
  self.assertEqual(canonical['contributions'][0]['evidence_spans'][0]['quote'],d['abstract'])
  self.assertTrue((self.w/('responses/'+rid+'.canonical.json')).exists())
 def test_source_transport_withholds_nonquantitative_parameter_without_faking_fact(self):
  d,r=fixture();wire=to_wire(r);spans=schema.make_source_spans(d);sid=next(x['source_id'] for x in spans if x['field']=='abstract')
  wire['contributions'][0]['evidence_spans']=[dict(source_id=sid,supports=['technical_mechanism','parameters'])]
  wire['contributions'][0]['parameters'][0]['raw']='VcF - VcR'
  canonical,lineage=schema.canonical_from_source_ids(wire,schema.source_id_schema(schema.EXTRACTION_WIRE_SCHEMA,spans),spans)
  self.assertEqual(canonical['contributions'][0]['parameters'],[])
  out=schema.apply_anchor_positions(schema.audit_wire_extraction(canonical,d),lineage,d)
  self.assertEqual(out['contributions'][0]['rejected_parameter_claims'][0]['model_claim'],'VcF - VcR')
  schema.validate(out,schema.ENRICHED_SCHEMA)
 def test_source_span_schema_rejects_unknown_id(self):
  d,r=fixture();spans=schema.make_source_spans(d);model_schema=schema.source_id_schema(schema.EXTRACTION_WIRE_SCHEMA,spans)
  wire=to_wire(r);wire['contributions'][0]['evidence_spans']=[dict(source_id='NOT_A_SOURCE_ID',supports=['technical_object'])]
  with self.assertRaises(ValueError):schema.canonical_from_source_ids(wire,model_schema,spans)
 def test_source_partition_is_lossless_for_long_html_source(self):
  d,r=fixture();d['abstract']+=' '+'a &lt;sup&gt;+&lt;/sup&gt; original segment. '*90
  spans=schema.make_source_spans(d)
  for field in ['title','abstract']:
   self.assertEqual(''.join(x['text'] for x in spans if x['field']==field),d[field])
  self.assertTrue(all(d[x['field']][x['start']:x['end']]==x['text'] and len(x['text'])<=241 for x in spans))
 def test_network_failure_is_recorded_without_tokens(self):
  with patch.object(extract,"api",side_effect=extract.ServiceUnavailable("TEST_ONLY")):
   with self.assertRaises(extract.ServiceUnavailable):extract.request("unit_test","synthetic-down",[],schema.EXTRACTION_SCHEMA,1,self.conn)
  self.assertEqual(self.conn.execute("select status,prompt_tokens,output_tokens from requests").fetchone(),("NETWORK_FAILED",None,None))


class GroupIntegrityTests(unittest.TestCase):
 def test_short_pair_id_transport_copies_cids_without_model_retyping(self):
  import confirm_same
  w=dict(pair_id='P001',relation='Parent-Child',parent_side='right',rationale='Synthetic test only',evidence_ids_left=['E1'],evidence_ids_right=['E2'])
  schema.validate(dict(judgments=[w]),confirm_same.schema(['P001']))
  result=confirm_same.canonical_judgment(w,dict(left='CID_original_left',right='CID_original_right'))
  self.assertEqual(result['parent_id'],'CID_original_right')
  self.assertEqual(result['left'],'CID_original_left')
  w['pair_id']='UNREQUESTED'
  with self.assertRaises(ValueError):schema.validate(dict(judgments=[w]),confirm_same.schema(['P001']))

 def test_title_cannot_prove_mechanism_equivalence(self):
  import merge
  ev=[dict(id='E1',field='title',quote='Synthetic title'),dict(id='E2',field='abstract',quote='Synthetic mechanism source phrase')]
  records={'a':dict(evidence_spans=ev),'b':dict(evidence_spans=ev)}
  row=dict(left='a',right='b',relation='Same',evidence_ids_left=['E1'],evidence_ids_right=['E2'])
  with self.assertRaises(AssertionError):merge.verify_judgment_evidence(row,records)
  row['evidence_ids_left']=['E2'];merge.verify_judgment_evidence(row,records)

 def test_related_edge_blocks_small_equivalence_group(self):
  import merge,numpy as np
  class ToyJudge:
   def relation(self,a,b):
    if a==b:return 'Same'
    return {('a','b'):'Same',('a','c'):'Same',('b','c'):'Related'}.get(tuple(sorted([a,b])))
   def ensure(self,pairs):return []
  records=[dict(contribution_id=x) for x in ['a','b','c']]
  def proposed(ids,judge):
   return [list(ids)] if len(ids)>1 else [list(ids)]
  with patch.object(merge,'connected_same',side_effect=proposed):
   groups,audit=merge.conservative_groups(records,np.eye(3,dtype=np.float32),ToyJudge())
  self.assertNotIn(['a','b','c'],groups)
  self.assertEqual(sorted(x for g in groups for x in g),['a','b','c'])
 def test_related_edge_also_blocks_large_equivalence_group(self):
  import merge,numpy as np
  class ToyJudge:
   def relation(self,a,b):
    return 'Related' if set([a,b])==set(['c','d']) else 'Same'
   def ensure(self,pairs):return []
  records=[dict(contribution_id=x) for x in 'abcdef']
  with patch.object(merge,'connected_same',side_effect=lambda ids,judge:[list(ids)]):
   groups,audit=merge.conservative_groups(records,np.eye(6,dtype=np.float32),ToyJudge())
  self.assertTrue(all(not ('c' in g and 'd' in g) for g in groups))
  self.assertEqual(sorted(x for g in groups for x in g),list('abcdef'))
 def test_registry_split_after_new_member_does_not_collide(self):
  from build_kb import Registry
  with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
   p=Path(tmp)/'registry.json';r=Registry(p);r.allocate('B','b',['b','c']);r.commit()
   joined=Registry(p);joined.allocate('B','a',['a','b','c']);joined.commit()
   split=Registry(p);left=split.allocate('B','a',['a']);right=split.allocate('B','b',['b','c'])
   self.assertNotEqual(left,right)
 def test_registry_merge_records_retired_alias(self):
  from build_kb import Registry
  with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
   p=Path(tmp)/'registry.json';r=Registry(p);a=r.allocate('B','a',['a']);b=r.allocate('B','b',['b']);r.commit()
   merged=Registry(p);tid=merged.allocate('B','a',['a','b'])
   self.assertEqual(merged.data['aliases'][next(x for x in [a,b] if x!=tid)],tid)
 def test_stable_registry_reuses_id_when_new_member_sorts_first(self):
  from build_kb import Registry
  with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
   p=Path(tmp)/'registry.json';r=Registry(p)
   tid=r.allocate('B','cid_b',['cid_b','cid_c']);r.commit()
   again=Registry(p);self.assertEqual(again.allocate('B','cid_a',['cid_a','cid_b','cid_c']),tid)
 def test_registry_split_does_not_reuse_one_id_for_two_nodes(self):
  from build_kb import Registry
  with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
   p=Path(tmp)/'registry.json';r=Registry(p)
   tid=r.allocate('B','a',['a','b']);r.commit()
   split=Registry(p);left=split.allocate('B','a',['a']);right=split.allocate('B','b',['b'])
   self.assertEqual(left,tid);self.assertNotEqual(left,right)


class CurationTests(unittest.TestCase):
 def test_source_amendment_preserves_original_and_records_link(self):
  import curation
  d,r=fixture();original=schema.audit_wire_extraction(to_wire(r),d)['contributions'][0]
  prior=common.object_hash(original)
  quote=dict(field='abstract',quote=d['abstract'],start=0,end=len(d['abstract']))
  patch_data=dict(families={d['family_id']:dict(reason='Synthetic unit source correction',facets=dict(technical_mechanism=dict(text='在器件中采用5 nm多孔层降低漂移',quotes=[quote])),parameter_kind_fixes=[])})
  with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
   dest=Path(tmp);(dest/'evidence').mkdir();(dest/'evidence/ASSISTANT_SOURCE_AMENDMENTS.json').write_text(json.dumps(patch_data))
   with patch.object(curation,'W',dest):
    out=curation.apply(original,d);again=curation.apply(original,d)
  self.assertEqual(common.object_hash(original),prior)
  self.assertEqual(out['source_model_contribution_id'],original['contribution_id'])
  self.assertNotEqual(out['contribution_id'],original['contribution_id'])
  self.assertEqual(out['contribution_id'],again['contribution_id'])
  self.assertEqual(out['semantic_validation_status'],'AI_SOURCE_CORRECTED_PENDING_HUMAN_REVIEW')
 def test_source_amendment_rejects_wrong_original_quote(self):
  import curation
  d,r=fixture();original=schema.audit_wire_extraction(to_wire(r),d)['contributions'][0]
  patch_data=dict(families={d['family_id']:dict(reason='INVALID SYNTHETIC TEST',facets=dict(technical_mechanism=dict(text='test',quotes=[dict(field='abstract',start=0,end=4,quote='FAKE')])))})
  with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
   dest=Path(tmp);(dest/'evidence').mkdir();(dest/'evidence/ASSISTANT_SOURCE_AMENDMENTS.json').write_text(json.dumps(patch_data))
   with patch.object(curation,'W',dest):
    with self.assertRaises(AssertionError):curation.apply(original,d)


class FreezeTests(unittest.TestCase):
 def test_missing_ssd_blocks_save_before_creating_parent(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
   w=Path(tmp);target=w/'must-not-create/result.json'
   with patch.object(common,'W',w),patch.object(common.Path,'is_mount',return_value=False):
    with self.assertRaises(AssertionError):common.save(str(target),dict(test_only=True))
   self.assertFalse(target.parent.exists())

 def test_existing_core_is_reused_before_any_output_write(self):
  import build_kb,posthoc_relevance
  with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
   w=Path(tmp);(w/'evidence').mkdir();(w/'outputs').mkdir()
   (w/'evidence/CORE_FREEZE.json').write_text('{}');target=w/'outputs/TECHNOLOGY_CONCEPTS.parquet';target.write_bytes(b'FROZEN TEST SENTINEL')
   with patch.object(build_kb,'W',w),patch.object(build_kb,'guard'),patch.object(build_kb,'event'),patch.object(posthoc_relevance,'verify_freeze',return_value={'test_only':True}):
    self.assertEqual(build_kb.build(),{'test_only':True})
   self.assertEqual(target.read_bytes(),b'FROZEN TEST SENTINEL')
 def test_posthoc_guard_rejects_modified_frozen_working_data(self):
  import posthoc_relevance
  with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
   w=Path(tmp);(w/'evidence').mkdir();(w/'working').mkdir();p=w/'working/source.json';p.write_text('ORIGINAL')
   receipt=dict(files_sha256={},working_sha256={'working/source.json':common.sha(p)},selected_input_sha256={})
   (w/'evidence/CORE_FREEZE.json').write_text(json.dumps(receipt));p.write_text('MODIFIED')
   with patch.object(common,'W',w),patch.object(posthoc_relevance,'W',w):
    with self.assertRaises(AssertionError):posthoc_relevance.verify_freeze()


class SamePolicyTests(unittest.TestCase):
 def test_same_respects_second_check_and_failed_confirmation(self):
  import merge
  from types import SimpleNamespace
  with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
   w=Path(tmp);(w/'evidence').mkdir()
   j=object.__new__(merge.Judge)
   with patch.object(merge,'W',w),patch.object(j,'existing',return_value={'relation':'Same','_equivalence_usable':False}):
    self.assertIsNone(j.relation('a','b'))
   (w/'evidence/SAME_CONFIRMATION_POLICY.json').write_text('{}')
   for payload,expected in [({'relation':'Same'},None),({'relation':'Same','_same_confirmation_status':'DUAL_SAME'},'Same'),({'relation':'Same','_source_reviewed':True},'Same'),({'relation':'Related'},'Related')]:
    with patch.object(merge,'W',w),patch.object(j,'existing',return_value=payload):
     self.assertEqual(j.relation('a','b'),expected)


class RelevanceTransportTests(unittest.TestCase):
 def test_short_ids_are_scoped_to_each_concept_and_copy_true_ids(self):
  import posthoc_relevance as r
  batch=[dict(technology_id='LONG_A',sources=[dict(contribution_id='CID_A')]),dict(technology_id='LONG_B',sources=[dict(contribution_id='CID_B')])]
  body,wire,mapping=r.short_transport(batch)
  self.assertEqual(body[0]['sources'][0]['contribution_id'],'R1')
  self.assertEqual(batch[0]['sources'][0]['contribution_id'],'CID_A')
  raw=dict(relevance=[dict(technology_id='T001',patent_evidence=[dict(contribution_id='R1',evidence_ids=['E1'])]),dict(technology_id='T002',patent_evidence=[dict(contribution_id='R1',evidence_ids=['E2'])])])
  out=r.canonical_relevance(raw,mapping)
  self.assertEqual(out['LONG_A']['patent_evidence'][0]['contribution_id'],'CID_A')
  self.assertEqual(out['LONG_B']['patent_evidence'][0]['contribution_id'],'CID_B')
  raw['relevance'][0]['patent_evidence'][0]['contribution_id']='R9'
  with self.assertRaises(AssertionError):r.canonical_relevance(raw,mapping)


class StreamingReceiptTests(unittest.TestCase):
 setUp=CacheTests.setUp
 tearDown=CacheTests.tearDown
 def test_terminal_receipt_is_saved_without_waiting_for_connection_eof(self):
  class Stream:
   def __init__(self):self.rows=iter([dict(message=dict(content='hel'),done=False),dict(message=dict(content='lo'),done=True,prompt_eval_count=7,eval_count=2)])
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def __iter__(self):return self
   def __next__(self):
    try:return (json.dumps(next(self.rows))+'\n').encode()
    except StopIteration:raise AssertionError('Should stop at terminal done receipt')
  with patch.object(extract.OPENER,'open',return_value=Stream()):
   raw=extract.api('/api/chat',dict(stream=True),'240',receipt_id='synthetic_stream')
  self.assertEqual(raw['message']['content'],'hello');self.assertEqual(raw['eval_count'],2)
  self.assertEqual(len((self.w/'responses/synthetic_stream.stream.jsonl').read_text().splitlines()),2)
 def test_slow_nonterminal_stream_is_bounded_and_retained(self):
  import io
  raw=(json.dumps(dict(message=dict(content='partial'),done=False))+'\n').encode()
  with patch.object(extract.OPENER,'open',return_value=io.BytesIO(raw)),patch.object(extract.time,'time',side_effect=[0,181]):
   with self.assertRaisesRegex(extract.ServiceUnavailable,'elapsed limit'):extract.api('/api/chat',dict(stream=True),receipt_id='synthetic_slow')
  self.assertIn('partial',(self.w/'responses/synthetic_slow.stream.jsonl').read_text())
 def test_incomplete_stream_is_never_completed(self):
  import io
  with patch.object(extract.OPENER,'open',return_value=io.BytesIO((json.dumps(dict(message=dict(content='partial'),done=False))+'\n').encode())):
   with self.assertRaises(extract.ServiceUnavailable):extract.api('/api/chat',dict(stream=True),receipt_id='synthetic_partial')
  self.assertTrue((self.w/'responses/synthetic_partial.stream.jsonl').exists())


class CommonConceptScopeTests(unittest.TestCase):
 def test_single_representative_number_cannot_become_common_condition(self):
  import concepts
  group=['a','b'];card=dict(group_key=common.object_hash(group))
  records={'a':dict(source_title='film',source_abstract='A 5 nm porous layer.'),'b':dict(source_title='film',source_abstract='A porous layer.')}
  result=dict(group_key=card['group_key'],name_zh='多孔层结构',core_mechanism='使用多孔层',applicable_conditions='5 nm')
  with self.assertRaises(AssertionError):concepts.audit_common_scope(result,card,group,records)
  result['applicable_conditions']=None;concepts.audit_common_scope(result,card,group,records)
 def test_parameter_present_in_all_members_can_be_retained(self):
  import concepts
  group=['a','b'];card=dict(group_key=common.object_hash(group))
  records={'a':dict(source_title='film',source_abstract='A 5 nm layer.'),'b':dict(source_title='layer',source_abstract='Thickness is 5 nm.')}
  result=dict(group_key=card['group_key'],name_zh='多孔层结构',core_mechanism='使用多孔层',applicable_conditions='5 nm')
  concepts.audit_common_scope(result,card,group,records)


class HistoryTransportTests(unittest.TestCase):
 def test_history_short_references_are_scoped_to_their_family(self):
  import posthoc_history as h
  batch=[dict(family_id='REAL_A',source_spans=[dict(text='complete A')],contributions=[dict(contribution_id='CID_A',title='redundant',abstract='redundant')]),dict(family_id='REAL_B',source_spans=[dict(text='complete B')],contributions=[dict(contribution_id='CID_B')])]
  body,wire,mapping=h.short_history_batch(batch)
  self.assertEqual(body[0]['source_spans'],batch[0]['source_spans'])
  raw=dict(rows=[dict(family_id='H001',support_contribution_ids=['R1']),dict(family_id='H002',support_contribution_ids=['R1'])])
  out=h.canonical_history(raw,mapping)
  self.assertEqual(out['REAL_A']['support_contribution_ids'],['CID_A'])
  self.assertEqual(out['REAL_B']['support_contribution_ids'],['CID_B'])
  raw['rows'][0]['support_contribution_ids']=['R7']
  with self.assertRaises(AssertionError):h.canonical_history(raw,mapping)
class ReceiptFailureAttributionTests(unittest.TestCase):
 setUp=CacheTests.setUp
 tearDown=CacheTests.tearDown
 def test_internal_validation_failure_carries_actual_request_receipt(self):
  raw=dict(done=True,done_reason='length',message=dict(content='{}'),prompt_eval_count=7,eval_count=2)
  with patch.object(extract,'api',return_value=raw):
   with self.assertRaises(ValueError) as failure:extract.request('unit_test','receipt-failure',[],schema.EXTRACTION_SCHEMA,1,self.conn)
  rid=failure.exception.request_id
  self.assertEqual(self.conn.execute('SELECT status FROM requests WHERE request_id=?',(rid,)).fetchone()[0],'VALIDATION_FAILED')

if __name__=='__main__':unittest.main(verbosity=2)





class CoreFreezeBoundaryTests(unittest.TestCase):
 def test_frozen_workspace_rejects_discovery_mutation(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'evidence').mkdir();(root/'evidence/CORE_FREEZE.json').write_text('{}')
   with patch.object(common,'W',root):
    with self.assertRaisesRegex(AssertionError,'frozen'):common.require_unfrozen()
 def test_new_workspace_can_start_discovery(self):
  with tempfile.TemporaryDirectory() as tmp:
   with patch.object(common,'W',Path(tmp)):common.require_unfrozen()
