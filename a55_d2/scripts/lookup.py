"""Read-only bidirectional lookup in the delivered SQLite prototype."""
from common import *
from posthoc_relevance import verify_freeze
import argparse
def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--family');g.add_argument('--technology');p.add_argument('--limit',type=int,default=20);a=p.parse_args()
 assert 1<=a.limit<=200
 guard();verify_freeze();path=W/'outputs/TECHNOLOGY_KNOWLEDGE_BASE.sqlite';assert path.is_file()
 db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON')
 if a.family:
  source=db.execute('SELECT * FROM patent_families WHERE family_id=?',(a.family,)).fetchone()
  if source is None:raise SystemExit('Family not in selected D2 discovery scope')
  contributions=[dict(r) for r in db.execute('SELECT * FROM patent_contributions WHERE family_id=? LIMIT ?',(a.family,a.limit))]
  concepts=[dict(r) for r in db.execute('SELECT t.*,r.contribution_id,r.relation_type FROM patent_technology_relations r JOIN technology_concepts t USING(technology_id) WHERE r.family_id=? LIMIT ?',(a.family,a.limit))]
  result=dict(family=dict(source),contributions=contributions,technologies=concepts,processing_status=[dict(r) for r in db.execute('SELECT * FROM patent_processing_status WHERE family_id=?',(a.family,))])
 else:
  node=db.execute('SELECT * FROM technology_concepts WHERE technology_id=?',(a.technology,)).fetchone()
  if node is None:raise SystemExit('Unknown Technology ID')
  rows=[dict(r) for r in db.execute('SELECT r.*,f.title,f.abstract,f.publication_id FROM patent_technology_relations r JOIN patent_families f USING(family_id) WHERE r.technology_id=? LIMIT ?',(a.technology,a.limit))]
  result=dict(technology=dict(node),patents=rows,children=[dict(r) for r in db.execute('SELECT technology_id,name,level FROM technology_concepts WHERE parent_technology_id=? LIMIT ?',(a.technology,a.limit))],relations=[dict(r) for r in db.execute('SELECT * FROM technology_relations WHERE source_technology_id=? OR target_technology_id=? LIMIT ?',(a.technology,a.technology,a.limit))])
 db.close();print(json.dumps(dict(result=result,limit=a.limit,scope='Selected D2 families; candidate mechanisms, not human Gold'),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
