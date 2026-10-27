import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import *
from pipeline import validate_extraction,validate_audit,claims
from client import validate
from design import EXTRACTION,AUDIT
class Integrity(unittest.TestCase):
 def test_unicode_spans(self):
  d=dict(title='圧電 Nb/Sc 液滴',abstract='A-site α≤0.49x\n工艺'+('☀️ Nb/Sc '+'汉字')*85)
  for f in ['title','abstract']:
   ss=[r for r in spans(d) if r['field']==f];self.assertEqual(''.join(s['text'] for s in ss),d[f])
   for s in ss:self.assertEqual(d[f][s['start']:s['end']],s['text'])
 def test_title_only_no_mechanism(self):
  d=dict(family_id='f',title='压电',abstract='')
  v=dict(family_id='f',source_status='TITLE_ONLY',contributions=[],abstention_reason='No abstract')
  validate_extraction(v,d)
  with self.assertRaises((AssertionError,ValueError)):validate_extraction(dict(v,family_id='g'),d)
 def test_holdout_isolation(self):
  lock=load('inputs/SPLIT_LOCK.json');self.assertEqual(len(lock['development']),98);self.assertEqual(len(lock['holdout']),42)
  self.assertFalse(set(lock['development'])&set(lock['holdout']));self.assertFalse(set(lock['holdout'])&set(lock['known_issues_excluded_from_holdout']))
  self.assertFalse((set(lock['development'])|set(lock['holdout']))&set(lock['historical_ids_excluded_from_independent_eval']))
 def test_schema_rejects_fake_status(self):
  with self.assertRaises(ValueError):validate(dict(family_id='f',source_status='SUCCESS',contributions=[],abstention_reason=None),EXTRACTION)
 def test_d2_inputs_unchanged(self):
  for p,h in load('inputs/D2_LOCK.json')['files'].items():self.assertEqual(sha(D2/p),h,p)
if __name__=='__main__':unittest.main()
