"""Wait for relevance, then complete authorized post-freeze probes/history/control baseline."""
from common import *
import fcntl,traceback
def main():
 guard();lock=(W/'state/worker.lock').open('a');event('posthoc_tail_waiting',dependency='current relevance worker');fcntl.flock(lock,fcntl.LOCK_EX)
 from posthoc_relevance import verify_freeze
 verify_freeze()
 import historical_probe,posthoc_history,d1_baseline
 historical_probe.main();posthoc_history.main();d1_baseline.main()
 save('evidence/POSTHOC_TAIL_COMPLETE.json',dict(at=now(),history_completed=load('outputs/HISTORICAL_VALIDATION.json')['completed'],baseline_panels=len(load('outputs/D1_D2_COMPARISON.json')['rows']),core_unchanged=True));verify_freeze()
if __name__=='__main__':
 try:main()
 except Exception as e:
  save('evidence/POSTHOC_TAIL_ERROR.json',dict(at=now(),error=str(e),traceback=traceback.format_exc()));raise
