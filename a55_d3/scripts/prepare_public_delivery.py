"""Allowlisted public delivery only; raw inputs and complete model logs stay on SSD."""
from common import *
from client import read_key
import shutil,zipfile,argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prepare-publication',action='store_true',required=True);ap.parse_args();guard();assert load('evidence/FINAL_VERIFICATION.json')['passed']
 repo=W.parent/'fuji-a55-query-free-clustering';assert (repo/'.git').is_dir();assert not subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip(),'Checkout changed; do not overwrite'
 allowed=['D3_REPORT.md','D3_EVALUATION_SET.xlsx','D3_QUALITY_METRICS.xlsx','D3_PATENT_CONTRIBUTIONS.parquet','D3_EVIDENCE_AUDIT.parquet','D3_PRINTHEAD_RELEVANCE.xlsx','D3_ERROR_ANALYSIS.md','D3_HISTORICAL_REGRESSION.md','D4_MERGE_TEST_CASES.parquet','D3_EXPERIMENT_COMPARISON.md','D3_EVALUATION_PROTOCOL.md','D3_LABELS.parquet','D3_PROCESSING_STATUS.parquet','D3_METRICS.parquet','D3_RELEVANCE_CONFUSIONS.parquet','D3_ERRORS.parquet','D3_PRINTHEAD_RELEVANCE.parquet','D3_REVIEW_QUEUE.parquet']
 m=load('D3_MANIFEST.json');m['final_execution_code_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=W,text=True).strip();m['workbook_qa']=load('evidence/WORKBOOK_QA.json');m['final_verification']=load('evidence/FINAL_VERIFICATION.json');m['publication_scope']='Only formal task deliverables and execution code. Raw input snapshots, complete API requests/responses/cache/logs remain on SSD and are not in public bundle.'
 code=[p for d in ['scripts','prompts','schemas','tests'] for p in (W/d).glob('*') if p.is_file()]+[W/'run-python',W/'AGENTS.md',W/'README.md',W/'D3_EVALUATION_PROTOCOL.md',W/'.gitignore']
 for n in allowed:m['artifacts'][n]=dict(sha256=sha(W/n),bytes=(W/n).stat().st_size)
 m['execution_code_files']={str(p.relative_to(W)):sha(p) for p in code};save('D3_MANIFEST.json',m)
 allowed+=['D3_MANIFEST.json'];bundle=W/'D3_PUBLIC_DELIVERY_BUNDLE.zip'
 with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for n in allowed:z.write(W/n,n)
  for p in code:z.write(p,'code/'+str(p.relative_to(W)))
 with zipfile.ZipFile(bundle) as z:
  assert z.testzip() is None
  assert all(not any(x in Path(n).parts for x in ['requests','responses','inputs','cache','logs','working']) for n in z.namelist())
 assert bundle.stat().st_size<95*2**20
 files=[W/n for n in allowed]+[bundle];key=read_key().encode()
 for p in code+files:
  assert key not in p.read_bytes(),'Credential detected; stop'
 release=dict(at=now(),repository='https://github.com/MakerC1995/fuji-a55-query-free-clustering',directory='deliverables/A5.5-D3',scope='Only formal D3 task deliverables and code; no raw inputs or complete model logs',files={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},code_files={str(p.relative_to(W)):sha(p) for p in code},credentials_excluded=True,databases_vectors_excluded=True,raw_inputs_and_model_logs_excluded=True)
 save('D3_RELEASE_MANIFEST.json',release);checks=W/'D3_CHECKSUMS.sha256';checks.write_text(''.join(v['sha256']+'  '+n+'\n' for n,v in release['files'].items()))
 dest=repo/'deliverables/A5.5-D3';codedest=repo/'a55_d3';assert not dest.exists() and not codedest.exists();dest.mkdir(parents=True);codedest.mkdir()
 for p in files+[W/'D3_RELEASE_MANIFEST.json',checks]:
  target=dest/p.name;shutil.copy2(p,target);assert sha(target)==sha(p)
 for p in code:
  target=codedest/p.relative_to(W);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);assert sha(target)==sha(p)
 (codedest/'PUBLISHED_EXECUTION.md').write_text('''# 执行与数据\n\n正式SSD工作区：/Volumes/Fuji_SSD_Work/workspaces/a55_d3_quality_convergence。按D3_MANIFEST指纹核对输入及D2兄弟工作区后使用SSD守护入口。代码不会自动下载数据库或生成向量。\n\n公开目录只含正式交付和代码。原始输入快照、全部模型请求/响应、缓存、详细修订链与usage账本保留在本地SSD，未放入公开包。公开交付中的源文证据属于任务要求的专利摘要/引文记录。\n\n人工Gold=0；19族处理失败、45族争议隔离不能改成全部成功。\n''')
 readme=repo/'README.md';readme.write_text('''## A5.5-D3 质量收敛交付\n\n代码：[a55_d3/](a55_d3/)；正式交付：[deliverables/A5.5-D3/](deliverables/A5.5-D3/)；[综合报告](deliverables/A5.5-D3/D3_REPORT.md)。\n\n官方deepseek-flash；98开发/42盲测。1117族全部尝试，1098族产出（含45族争议），19族失败；1065候选贡献、15294最终字段审计、151节点相关性复审、45族历史回归、39组D4困难样本。人工Gold=0，Silver不作为全自动扩大规模证明。原D1/D2冻结数据与概念ID不改。原始输入与完整模型调用日志仅保留SSD，不在公开包中。\n\n'''+readme.read_text())
 agents=repo/'AGENTS.md';agents.write_text('# D3追加归档\n\nD3代码在a55_d3/，正式交付在deliverables/A5.5-D3/。用户授权发布本轮代码和交付；原始输入快照、完整模型请求/响应、凭据不发布。D3主语义版本盲测前冻结；19失败、45争议及Gold=0不能改写成全部成功。后续LLM依用户指定使用官方deepseek-flash，不自动启动新付费批次、全库编码、聚类或正式D4归并。\n\n'+agents.read_text())
 save('evidence/PUBLICATION_PREPARED.json',dict(at=now(),destination=str(dest),code_destination=str(codedest),bundle_bytes=bundle.stat().st_size,all_copies_hash_verified=True,raw_inputs_model_logs_not_copied=True,commit_and_push_method='GitHub Desktop',not_yet_pushed=True))
 event('publication_prepared',destination=str(dest),files=len(files)+2,bundle_bytes=bundle.stat().st_size,raw_inputs_model_logs_not_copied=True)
if __name__=='__main__':main()
