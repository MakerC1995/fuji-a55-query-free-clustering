"""Record the actual installed runtime without installing or changing packages."""
from common import *
import importlib,importlib.metadata,platform
def main():
 guard();packages=[]
 for mod,dist in [('numpy','numpy'),('pandas','pandas'),('pyarrow','pyarrow'),('faiss','faiss-cpu')]:
  m=importlib.import_module(mod)
  try:v=importlib.metadata.version(dist)
  except importlib.metadata.PackageNotFoundError:v=getattr(m,'__version__','unknown')
  packages.append(dict(distribution=dist,module=mod,version=v,loaded_from=m.__file__))
 rec=dict(at=now(),python=sys.version,executable=sys.executable,platform=platform.platform(),machine=platform.machine(),sqlite=sqlite3.sqlite_version,packages=packages,python_entry=str(W/'run-python'),scientific_vendor=str(D1/'deps'),original_data_roots=[str(D1),str(BASE)],pip_install_performed=False)
 artifact=Path('/Users/shaoshuai/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/package.json')
 if artifact.exists():
  a=json.loads(artifact.read_text());rec['workbook_authoring_runtime']=dict(package=a.get('name'),version=a.get('version'),package_json_sha256=sha(artifact),bundled_node='/Users/shaoshuai/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
 save('evidence/RUNTIME_ENVIRONMENT.json',rec)
 (W/'configs/requirements-D2.lock.txt').write_text('# Actual direct scientific dependencies; recorded only, no installation performed. Python 3.12 / macOS arm64.\n'+'\n'.join(p['distribution']+'=='+p['version'] for p in packages)+'\n')
 print(stable(rec))
if __name__=='__main__':main()
