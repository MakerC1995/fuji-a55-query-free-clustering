"""Sequential supervisor with resource sampling and bounded HDBSCAN workers."""
from pathlib import Path
import os,sys,time,json,subprocess
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W/'deps'))
import psutil
ENTRY=str(W/'run-python')
def event(o):
 o['time']=time.strftime('%Y-%m-%dT%H:%M:%S%z')
 with (W/'logs/supervisor.jsonl').open('a') as f:f.write(json.dumps(o)+'\n')
 print(json.dumps(o),flush=True)
def run(args,limit=2400):
 key='_'.join(map(str,args));log=W/'logs'/f'{key}.log'
 event(dict(event='start',args=args))
 env=os.environ.copy();env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',VECLIB_MAXIMUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
 t=time.time();peak=0;low=0;reason=None
 with log.open('a') as out:
  p=subprocess.Popen([ENTRY,'--offline',str(W/'scripts/experiment.py'),*map(str,args)],cwd=W,stdout=out,stderr=subprocess.STDOUT,env=env)
  proc=psutil.Process(p.pid)
  while p.poll() is None:
   try:
    rss=proc.memory_info().rss+sum(c.memory_info().rss for c in proc.children(recursive=True));peak=max(peak,rss)
    avail=psutil.virtual_memory().available
    low=low+1 if avail<400*1024**2 else 0
    if rss>3.4*2**30:reason='worker_RSS_exceeded_3.4GiB'
    if low>=4:reason='available_RAM_below_400MiB_for_8_seconds'
    if time.time()-t>limit:reason=f'wall_time_exceeded_{limit}s'
    if reason:
     p.terminate()
     try:p.wait(10)
     except subprocess.TimeoutExpired:p.kill();p.wait()
     break
   except psutil.NoSuchProcess:break
   time.sleep(2)
 rc=p.wait()
 event(dict(event='finish',args=args,exit=rc,wall_s=time.time()-t,peak_worker_gib=peak/2**30,resource_stop=reason,log=str(log)))
 if rc:
  with (W/'evidence/failed_runs.jsonl').open('a') as f:f.write(json.dumps(dict(args=args,exit=rc,reason=reason,log=str(log)))+'\n')
 return rc==0
def gate(n,status,**extra):
 (W/f'evidence/{n}.json').write_text(json.dumps(dict(status=status,time=time.strftime('%Y-%m-%dT%H:%M:%S%z'),**extra),indent=2))
def main():
 assert run(['audit'],600),'Audit/pilot failed'
 gate('D1-G1','PASS',resource_budget=dict(serial=True,threads=2,max_worker_rss_gib=3.4,min_available_ram_mib=400,source='16GiB Mac actual environment',hdbscan_wall_cap_s=1800))
 for k in [100,300,800]:
  for seed in [42,137]:
   assert run(['kmeans','bge',k,seed]),'BGE KMeans failed'
 assert run(['pca','bge'])
 assert run(['samples'])
 for n,d,c,s in [(20000,30,10,5),(20000,30,30,15),(20000,30,100,50),(20000,50,30,15),(50000,30,10,5),(50000,30,30,15),(238541,30,30,15)]:
  ok=run(['hdb','bge',n,d,c,s],1800)
  if n==50000 and not ok:
   event(dict(event='larger_hdb_deferred',reason='50k_resource_failure_requires_review'));break
 assert run(['neighbors','bge'],7200),'BGE kNN failed'
 for k,rule,res,seeds in [(15,'mutual','0.5,1,2','42'),(30,'mutual','0.5,1,2','42,137'),(50,'mutual','1','42'),(30,'sym','0.5,1,2','42,137')]:
  assert run(['graph','bge',k,rule,res,seeds],2400)
 for k in [100,300,800]:
  for seed in [42,137]:
   assert run(['kmeans','qwen',k,seed])
 assert run(['pca','qwen'])
 for n,d,c,s in [(20000,30,10,5),(20000,30,30,15),(20000,30,100,50),(20000,50,30,15),(50000,30,30,15)]:
  run(['hdb','qwen',n,d,c,s],1800)
 assert run(['neighbors','qwen'],7200)
 for k,rule,res,seeds in [(15,'mutual','0.5,1,2','42'),(30,'mutual','0.5,1,2','42,137'),(50,'mutual','1','42'),(30,'sym','0.5,1,2','42,137')]:
  assert run(['graph','qwen',k,rule,res,seeds],2400)
 gate('D1-G2','COMPLETED_WITH_HDBSCAN_SCOPE_REVIEW_REQUIRED' if (W/'evidence/failed_runs.jsonl').exists() else 'PASS')
 event(dict(event='experiments_finished'))
if __name__=='__main__':main()
