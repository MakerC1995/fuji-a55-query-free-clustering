from experiment import *
con=db();con.row_factory=sqlite3.Row
src=Path('/Volumes/Fuji_SSD_Work/patent/fuji/state/fuji_a51_retrieval_snapshot.sqlite')
if not src.exists():raise FileNotFoundError(src)
c=sqlite3.connect(src.as_uri()+'?mode=ro',uri=True);c.execute('PRAGMA query_only=ON')
schema=c.execute("select sql from sqlite_master where name='family_texts'").fetchone()[0]
ids=np.sort(np.random.default_rng(42).choice(N,40,replace=False))
checks=[]
for i in ids:
 d=dict(con.execute('select * from docs where row_idx=?',(int(i),)).fetchone())
 for field in ['title','abstract']:
  textid=d[field+'_text_id']
  if not textid:continue
  original=c.execute('select family_key,pub_id,field_name,language,text_value,source_record_hash from family_texts where text_id=?',(textid,)).fetchone()
  assert original is not None
  assert original[0]==d['family_id'] and original[1]==d['pub_id'] and original[4]==d[field],(i,field)
  checks.append(dict(row_idx=int(i),family_id=d['family_id'],field=field,text_id=textid,source_record_hash=original[5],exact_text_match=True))
dump('evidence/frozen_source_spotcheck.json',dict(status='PASS',rows=40,seed=42,source=str(src),checks=checks,schema=schema))
print('PASS',len(checks))
