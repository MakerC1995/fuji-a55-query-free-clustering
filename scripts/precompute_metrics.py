from analyze import metric,allruns
from experiment import guard,log
guard(1.7)
ids=['bge_k100_s42','bge_k300_s42','bge_k800_s42','bge_n238541_pca30_c30_s15','bge_n50000_pca30_c10_s5','bge_k30_mutual_r1.0_s42','bge_k30_sym_r1.0_s42','qwen_k300_s42']
for r in allruns():
 if r['run_id'] in ids:metric(r)
log('precomputed_frozen_BGE_metrics_complete',note='No LLM inputs or history accessed; all BGE partitions had completed before metric evaluation.')
