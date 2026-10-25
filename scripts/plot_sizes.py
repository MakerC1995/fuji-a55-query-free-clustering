"""Human-readable size figures with actual IDs in largest-20 panel."""
from experiment import *
from analyze import allruns,load
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
primary=json.loads((W/'comparison/primary_runs.json').read_text());records=[]
for r in allruns():
 if r['run_id'] not in primary:continue
 labels,ids=load(r);cs,sizes=np.unique(labels[labels>=0],return_counts=True);order=np.lexsort((cs,-sizes))[:20]
 fig,axs=plt.subplots(2,2,figsize=(12,8));fig.suptitle(r['run_id']+f" | n={len(ids):,}, noise={(labels<0).mean():.1%}")
 axs[0,0].hist(sizes,bins=40);axs[0,0].set(xlabel='Cluster size',ylabel='Clusters')
 axs[0,1].hist(sizes,bins=np.geomspace(max(1,sizes.min()),max(2,sizes.max()),40));axs[0,1].set(xscale='log',xlabel='Cluster size (log)',ylabel='Clusters')
 axs[1,0].bar(range(len(order)),sizes[order]);axs[1,0].set_xticks(range(len(order)),[str(v) for v in cs[order]],rotation=90,fontsize=8);axs[1,0].set(xlabel='Cluster ID (top 20 by size)',ylabel='Families')
 for rank,o in enumerate(order,1):records.append(dict(run_id=r['run_id'],scope_size=len(ids),rank=rank,cluster_id=int(cs[o]),cluster_size=int(sizes[o])))
 bins=[1,3,10,31,101,501,10**9];counts=np.histogram(sizes,bins)[0];axs[1,1].bar(['1–2','3–9','10–30','31–100','101–500','>500'],counts);axs[1,1].set(ylabel='Clusters')
 fig.tight_layout();fig.savefig(W/f"figures/{r['run_id']}_sizes.png",dpi=150);plt.close(fig)
pd.DataFrame(records).to_csv(W/'comparison/largest20_clusters.csv',index=False)
dump('evidence/figure_display_refinement.json',dict(status='PASS',actual_cluster_ids_on_largest20_axis=True,all_figures_from_frozen_labels=True,labels_modified=False,largest20_rows=len(records)))
print('Updated size figures and largest-20 ID table',len(records))
