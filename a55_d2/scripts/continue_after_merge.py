"""Continue authorized local discovery phases after the active comparison worker releases."""
from common import *
import fcntl,traceback
def main():
 guard();lock=(W/'state/worker.lock').open('a')
 event('discovery_continuation_waiting',dependency='first comparison worker')
 fcntl.flock(lock,fcntl.LOCK_EX)
 guard();assert not (W/'evidence/CORE_FREEZE.json').exists()
 grouped=load('working/all_selected/CONTRIBUTION_GROUPS.json')
 assert grouped['contributions']==975,'Unexpected contribution set; inspect rather than silently substitute'
 if not grouped.get('same_confirmation_receipt'):
  import confirm_same
  save('evidence/DISCOVERY_CONTINUATION.json',dict(at=now(),stage='same_confirmation',complete=False))
  confirm_same.main()
 import concepts
 save('evidence/DISCOVERY_CONTINUATION.json',dict(at=now(),stage='concept_naming',complete=False))
 concepts.run('all_selected')
 naming=load('working/all_selected/CONCEPT_NAMES.json')
 save('evidence/DISCOVERY_CONTINUATION.json',dict(at=now(),stage='names_ready_for_review',complete=naming['missing']==0,named=len(naming['names']),missing=naming['missing'],core_frozen=False,historical_inputs_read=False))
 event('discovery_names_ready',named=len(naming['names']),missing=naming['missing'],requires_source_name_review_before_freeze=True)
if __name__=='__main__':
 try:main()
 except Exception as e:
  save('evidence/DISCOVERY_CONTINUATION_ERROR.json',dict(at=now(),error=str(e),traceback=traceback.format_exc(),complete=False));raise
