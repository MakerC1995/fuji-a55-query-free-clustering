from common import *
from pipeline import full
from experiments import active_main
import client

def main():
 guard();docs=load('inputs/ALL_DOCUMENTS.json');dev=set(load('inputs/SPLIT_LOCK.json')['development']);doc=next(d for d in docs if d['family_id'] in dev and active_main(d['family_id']) and active_main(d['family_id'])['status']=='VALID');before=active_main(doc['family_id']);n=len(list((W/'requests').glob('*.json')))
 class OfflineOnly:
  def open(self,*a,**kw):raise AssertionError('Resume proof prohibits any HTTP request')
 client.OPENER=OfflineOnly();after=full(doc)
 assert before['final_request_id']==after['final_request_id'] and before['final_audit_request_id']==after['final_audit_request_id']
 assert len(list((W/'requests').glob('*.json')))==n,'Unexpected fresh request'
 save('evidence/RESUME_PROOF.json',dict(at=now(),family_id=doc['family_id'],network_disabled_by_test_double=True,fresh_requests=0,original_request_id_unchanged=True,final_audit_request_id_unchanged=True,status=after['status']))
 print('PASS: complete cached family resumed with network disabled, zero new requests')
if __name__=='__main__':main()
