from supervise import run,event
from pathlib import Path
import json,time
w=Path(__file__).resolve().parents[1]
event(dict(event='bounded_qwen_precompute_start',max_concurrent_workers=2,reason='Measured heavy graph RSS approximately 2.2GiB and free RAM above 4GiB; Qwen precompute peaks under 1.4GiB. ANN construction remains serial.'))
for k in [100,300,800]:
 for seed in [42,137]:assert run(['kmeans','qwen',k,seed])
assert run(['pca','qwen'])
for n,d,c,s in [(20000,30,10,5),(20000,30,30,15),(20000,30,100,50),(20000,50,30,15),(50000,30,30,15)]:
 assert run(['hdb','qwen',n,d,c,s],1800)
event(dict(event='bounded_qwen_precompute_complete'))
