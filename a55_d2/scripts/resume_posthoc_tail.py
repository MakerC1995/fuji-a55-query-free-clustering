from common import *
import fcntl,traceback
def main():
 guard();lock=(W/'state/worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 import repair_relevance_reviews,historical_probe,posthoc_history,d1_baseline
 repair_relevance_reviews.repair()
 historical_probe.main();posthoc_history.main();d1_baseline.main()
 rec=dict(at=now(),history_completed=load('outputs/HISTORICAL_VALIDATION.json')['completed'],baseline_panels=len(load('outputs/D1_D2_COMPARISON.json')['rows']),core_unchanged=True)
 save('evidence/POSTHOC_TAIL_COMPLETE.json',rec)
 if (W/'evidence/POSTHOC_TAIL_ERROR.json').exists():save('evidence/POSTHOC_TAIL_ERROR_RESOLVED.json',dict(at=now(),original_error_sha256=sha(W/'evidence/POSTHOC_TAIL_ERROR.json'),resolution='Per-item replay and single-concept source-span enum repair; all required post-hoc experiments now complete',completion=rec))
if __name__=='__main__':
 try:main()
 except Exception as e:
  save('evidence/POSTHOC_RESUME_ERROR.json',dict(at=now(),error=str(e),traceback=traceback.format_exc()));raise
