import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const W=path.resolve(path.dirname(new URL(import.meta.url).pathname),'..');
const out=path.join(W,'outputs','01a171fb-0dd6-7792-b36b-80e200aba942');
await fs.mkdir(out,{recursive:true});
const specs=JSON.parse(await fs.readFile(path.join(W,'reports/workbook_data.json'),'utf8'));
const qa=[];
for(const spec of specs.filter(s=>!process.argv[2]||s.file===process.argv[2])){
 const wb=Workbook.create();
 for(const [si,tab] of spec.sheets.entries()){
  const sh=wb.worksheets.add(tab.name);sh.showGridLines=false;
  const cols=tab.columns,rows=tab.rows;
  const title=tab.title??tab.name;
  sh.getRange('B2').values=[[title]];
  sh.getRange('B2').format.font={name:'Arial',size:14,bold:true,color:'#17324D'};
  sh.getRange('B3').values=[[tab.note??'来源：SSD 全库向量底座 v1；实际实验输出。Cluster 是分区，技术主题需证据核验。']];
  sh.getRange('B3').format.font={name:'Arial',size:10,italic:true,color:'#586777'};
  sh.getRange('B3').format.columnWidth=24;
  const head=sh.getRangeByIndexes(4,1,1,cols.length);head.values=[cols.map(c=>c.label)];
  head.format={fill:'#17324D',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',verticalAlignment:'center',rowHeight:34};
  if(rows.length){
   const matrix=rows.map(r=>cols.map(c=>{const v=r[c.key];return v===undefined||v===null?null:typeof v==='object'?JSON.stringify(v):typeof v==='string'&&v.startsWith('=')?"'"+v:v;}));
   for(let i=0;i<matrix.length;i+=500)sh.getRangeByIndexes(5+i,1,Math.min(500,matrix.length-i),cols.length).values=matrix.slice(i,i+500);
   const body=sh.getRangeByIndexes(5,1,rows.length,cols.length);
   body.format.font={name:'Arial',size:10,color:'#243749'};body.format.verticalAlignment='top';body.format.rowHeight=tab.rowHeight??48;
   cols.forEach((c,j)=>{
    const rng=sh.getRangeByIndexes(5,j+1,rows.length,1);rng.format.columnWidth=c.width??22;
    if(c.wrap)rng.format.wrapText=true;
    if(c.type==='number')rng.setNumberFormat(c.format??'#,##0.000');
    if(c.type==='integer')rng.setNumberFormat('#,##0');
    if(c.type==='percent')rng.setNumberFormat('0.0%');
   });
   if(rows.length>15){sh.freezePanes.freezeRows(5);sh.freezePanes.freezeColumns(3);}
   sh.tables.add('B5:'+colLetter(cols.length+1)+(rows.length+5),true,'DataTable'+si);
   body.format.autofitRows();
   // Alternating restrained row bands; no meaning encoded by color.
   for(let i=0;i<rows.length;i+=2)sh.getRangeByIndexes(5+i,1,1,cols.length).format.fill='#F1F5F8';
  }
  const width=Math.min(cols.length,6);const check=await wb.inspect({kind:'table',sheetId:tab.name,range:'B5:'+colLetter(width+1)+Math.min(rows.length+5,10),include:'values,formulas',tableMaxRows:5,tableMaxCols:width,maxChars:1800});
  qa.push({file:spec.file,sheet:tab.name,rows:rows.length,inspection:check.ndjson});
 }
 wb.recalculate();
 const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},maxChars:2000});
 qa.push({file:spec.file,errorScan:errors.ndjson});
 for(const tab of spec.sheets){
  const last=colLetter(Math.min(tab.columns.length,6)+1);
  const blob=await wb.render({sheetName:tab.name,range:'B2:'+last+'10',scale:1.5,format:'png'});
  const png=spec.file.replace('.xlsx','')+'_'+tab.name+'.png';
  await fs.writeFile(path.join(W,'evidence',png),new Uint8Array(await blob.arrayBuffer()));
 }
 const file=await SpreadsheetFile.exportXlsx(wb);await file.save(path.join(out,spec.file));
 await fs.writeFile(path.join(W,'evidence',spec.file.replace('.xlsx','')+'_qa.json'),JSON.stringify(qa.filter(x=>x.file===spec.file),null,2));
 console.log(JSON.stringify({file:spec.file,sheets:spec.sheets.length,rows:spec.sheets.map(s=>s.rows.length)}));
}
await fs.writeFile(path.join(W,'evidence/workbook_qa.json'),JSON.stringify(qa,null,2));
function colLetter(n){let s='';while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;}
