import fs from "node:fs/promises";
import {SpreadsheetFile,FileBlob} from "@oai/artifact-tool";
const root="/Volumes/Fuji_SSD_Work/workspaces/a55_d2_technology_kb";
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(root+"/outputs/01a171fb-0dd6-7792-b36b-80e200aba942/TECHNOLOGY_KNOWLEDGE_BASE.xlsx"));
const data=JSON.parse(await fs.readFile(root+"/working/WORKBOOK_DATA.json","utf8"));
let n=0,nonempty=0;
for(const [name,d] of Object.entries(data.tables)){
const got=wb.worksheets.getItem(name).getRangeByIndexes(1,0,d.rows.length,d.headers.length).values;
for(let i=0;i<d.rows.length;i++)for(let j=0;j<d.headers.length;j++){
if(JSON.stringify(got[i][j]??null)!==JSON.stringify(d.rows[i][j]??null)){n++;if(d.rows[i][j]!==""&&nonempty++<8)console.log(JSON.stringify({sheet:name,row:i+2,column:d.headers[j],expected:d.rows[i][j],actual:got[i][j]}));}
}}
console.log("TOTAL_DIFFERENCES",n,"NONEMPTY_DIFFERENCES",nonempty);