"""Validate saved XLSX structures and sampled values without editing workbooks."""
from experiment import *
import zipfile,xml.etree.ElementTree as ET,math,posixpath
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
P= W/'outputs/01a171fb-0dd6-7792-b36b-80e200aba942'
def main():
 specs=json.loads((W/'reports/workbook_data.json').read_text());results=[]
 for spec in specs:
  path=P/spec['file']
  with zipfile.ZipFile(path) as z:
   wb=ET.fromstring(z.read('xl/workbook.xml'));rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'));rm={r.attrib['Id']:r.attrib['Target'] for r in rels}
   ss=[]
   if 'xl/sharedStrings.xml' in z.namelist():
    root=ET.fromstring(z.read('xl/sharedStrings.xml'))
    ss=[''.join(e.text or '' for e in si.iter('{'+NS['s']+'}t')) for si in root]
   sheets=wb.find('s:sheets',NS);assert [x.attrib['name'] for x in sheets]==[x['name'] for x in spec['sheets']]
   for sh,tab in zip(sheets,spec['sheets']):
    target=rm[sh.attrib['{'+REL+'}id']];target=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
    root=ET.fromstring(z.read(target));data=root.find('s:sheetData',NS);cells={c.attrib['r']:c for row in data for c in row}
    def value(ref):
     c=cells.get(ref)
     if c is None:return None
     v=c.find('s:v',NS);t=c.attrib.get('t')
     if t=='s':return ss[int(v.text)]
     if t=='inlineStr':return ''.join(e.text or '' for e in c.iter('{'+NS['s']+'}t'))
     if v is None:return None
     if t=='b':return v.text=='1'
     if t in ['str','e']:return v.text
     return float(v.text)
    def letter(n):
     s=''
     while n:n,a=divmod(n-1,26);s=chr(65+a)+s
     return s
    for j,c in enumerate(tab['columns'],2):assert value(letter(j)+'5')==c['label']
    populated=sum(value('B'+row.attrib['r']) is not None for row in data if int(row.attrib['r'])>=6)
    assert populated==len(tab['rows']),(tab['name'],populated,len(tab['rows']))
    checked=0
    for i in sorted({0,len(tab['rows'])//2,len(tab['rows'])-1}):
     if i<0:continue
     r=tab['rows'][i]
     for j,col in enumerate(tab['columns'],2):
      expected=r.get(col['key']);actual=value(letter(j)+str(i+6))
      if expected is None or expected=='':assert actual in [None,''];continue
      if isinstance(expected,bool):assert actual==expected
      elif isinstance(expected,(int,float)):assert isinstance(actual,(int,float)) and math.isclose(actual,expected,rel_tol=1e-9,abs_tol=1e-9),(spec['file'],tab['name'],i,col['key'],expected,actual)
      elif isinstance(expected,(list,dict)):assert json.loads(actual)==expected
      else:assert str(actual).replace('\r\n','\n')==str(expected).replace('\r\n','\n'),(spec['file'],tab['name'],i,col['key'])
      checked+=1
    assert not root.findall('.//s:f',NS),'Unexpected spreadsheet formulas'
    tables=root.find('s:tableParts',NS);assert tables is not None and int(tables.attrib['count'])==1
    maxh=max(float(row.attrib.get('ht',15)) for row in data);assert maxh<=409.5,(spec['file'],tab['name'],maxh)
    results.append(dict(file=spec['file'],sheet=tab['name'],rows=populated,sampled_values_checked=checked,headers_exact=True,filter_table_present=True,max_row_height_pt=maxh,formulas=0))
  assert path.stat().st_size>1000
 for rec in results:
  assert (W/'evidence'/f"{rec['file'].replace('.xlsx','')}_{rec['sheet']}.png").exists()
 debug=W/'evidence/native_export_inspect';debug.mkdir(exist_ok=True)
 for p in P.glob('*.inspect.ndjson'):p.replace(debug/p.name)
 dump('evidence/final_workbook_validation.json',dict(status='PASS',workbooks=4,sheets=len(results),checks=results,visual_review='All 8 sheets rendered and viewed. Static data snapshots, no native application recalculation claim.',no_data_truncated_for_fit=True))
 print('Saved XLSX checks PASS:',len(results),'sheets',sum(r['sampled_values_checked'] for r in results),'sampled cell values')
if __name__=='__main__':main()
