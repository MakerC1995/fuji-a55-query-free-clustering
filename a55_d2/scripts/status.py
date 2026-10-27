from common import *
def main():
 c=state_db()
 rows=c.execute('select status,count(*) from extraction group by status').fetchall()
 costs=c.execute('select kind,status,count(*),sum(prompt_tokens),sum(output_tokens),sum(wall_s) from requests group by kind,status').fetchall()
 save('evidence/PROGRESS.json',dict(at=now(),extraction_status=dict(rows),request_groups=[dict(zip(['kind','status','requests','prompt_tokens','output_tokens','wall_s'],r)) for r in costs]))
 print(stable(load('evidence/PROGRESS.json')))
if __name__=='__main__':main()
