import fs from "node:fs/promises";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { Workbook, SpreadsheetFile, FileBlob } from "@oai/artifact-tool";
const root=path.resolve(path.dirname(new URL(import.meta.url).pathname),"..");
const data=JSON.parse(await fs.readFile(path.join(root,"working/WORKBOOK_DATA.json"),"utf8"));
const out=path.join(root,"outputs/01a171fb-0dd6-7792-b36b-80e200aba942");
function guardSSD(){
 const xml=execFileSync("/usr/sbin/diskutil",["info","-plist","/Volumes/Fuji_SSD_Work"],{encoding:"utf8"});
 if(!/<key>VolumeUUID<\/key>\s*<string>534D9B75-27C9-49B5-89A0-4DF7E631107C<\/string>/.test(xml)||!/<key>FilesystemType<\/key>\s*<string>apfs<\/string>/.test(xml))throw Error("SSD unavailable or wrong identity; stop without local fallback");
}
guardSSD();
await fs.mkdir(out,{recursive:true});
const wb=Workbook.create();
const names=["Overview","Technology Concepts","Patent Contributions","Patent–Technology","Technology Relations","Cluster–Technology","Review Queue","Historical Validation"];
for(const name of names)wb.worksheets.add(name);
const font="Arial",ink="#18354B",header="#234A65",amber="#FFF1CC";
function col(n){let s="";while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;}
function table(name,headers,rows,widths){
 const sh=wb.worksheets.getItem(name);sh.showGridLines=false;
 const vals=[headers,...rows].map(r=>r.map(v=>typeof v==="string"&&v.startsWith("=")?"'"+v:v));
 const range=sh.getRangeByIndexes(0,0,vals.length,headers.length);range.values=vals;
 range.format.font={name:font,size:10,color:"#172B3A"};range.format.verticalAlignment="top";
 range.format.rowHeight=40;
 const hr=sh.getRangeByIndexes(0,0,1,headers.length);hr.format={fill:header,font:{name:font,size:10,bold:true,color:"#FFFFFF"},horizontalAlignment:"center",verticalAlignment:"center",rowHeight:30,wrapText:true};
 for(let j=0;j<headers.length;j++){
  const col=sh.getRangeByIndexes(0,j,vals.length,1);col.format.columnWidth=widths[j]||24;
  if(j>1)col.format.wrapText=true;
 }
 if(vals.length>1){const t=sh.tables.add("A1:"+col(headers.length)+vals.length,true,"D2_"+names.indexOf(name));t.showFilterButton=true;}
 if(rows.length)sh.getRangeByIndexes(1,0,rows.length,headers.length).format.autofitRows();
 sh.freezePanes.freezeRows(1);sh.freezePanes.freezeColumns(2);
 return sh;
}
const definitions=data.tables;
for(const name of names.slice(1)){
 const def=definitions[name];const sh=table(name,def.headers,def.rows,def.widths);
 for(const j of def.editableColumns||[]){
  if(def.rows.length)sh.getRangeByIndexes(1,j,def.rows.length,1).format.fill=amber;
 }
 if(name==="Review Queue"&&def.rows.length){
  const j=def.reviewStatusColumn;
  sh.getRangeByIndexes(1,j,def.rows.length,1).dataValidation={rule:{type:"list",values:["待人工","支持","需修改","不支持","无法判断"]}};
  const a=sh.getRangeByIndexes(1,j,def.rows.length,1);
  a.conditionalFormats.add("containsText",{text:"需修改",format:{fill:"#FCE5E5",font:{color:"#9B2020",bold:true}}});
 }
}
const sh=wb.worksheets.getItem("Overview");sh.showGridLines=false;sh.tabColor=ink;
sh.getRange("A1:I48").format.font={name:font,size:10,color:"#172B3A"};
sh.getRange("A2").values=[["FUJIFILM 技术知识库 · D2"]];sh.getRange("A2").format.font={name:font,size:15,bold:true,color:ink};
sh.getRange("A3").values=[[data.subtitle]];sh.getRange("A3:I3").format.rowHeight=22;
sh.getRange("A5:B5").values=[["范围与结果","数量"]];
sh.getRange("A6:B13").values=data.metrics;
sh.getRange("A5:B5").format={fill:header,font:{name:font,size:10,bold:true,color:"#FFFFFF"},rowHeight:28};
sh.getRange("A6:B13").format.rowHeight=23;sh.getRange("B6:B13").setNumberFormat("#,##0");
sh.getRange("D5:I5").values=[["实验群","总体族数","本次族数","明确机制族","候选机制数","覆盖"]];
sh.getRange("D6:I16").values=data.cohorts;
sh.getRange("D5:I5").format={fill:header,font:{name:font,size:10,bold:true,color:"#FFFFFF"},horizontalAlignment:"center",wrapText:true,rowHeight:28};
sh.getRange("D6:I16").format.rowHeight=24;sh.getRange("E6:H16").setNumberFormat("#,##0");
sh.getRange("A18").values=[["候选节点尚未经独立人审；原文引句校验不等于语义正确。混合群及 Noise 仅覆盖抽样成员。"]];
sh.getRange("A19").values=[["主张效果按摘要表述保留。喷头可迁移判断属于事后评估，不表示已实际采用。"]];
sh.getRange("A21").values=[["真实技术案例"]];sh.getRange("A21").format.font={name:font,size:13,bold:true,color:ink};
sh.getRange("A23:I23").values=[["技术名称","Technology ID","领域","Family ID","原文证据","原文字段","喷头关系","证据性质","待核验点"]];
sh.getRange("A24:I43").values=data.cases;
sh.getRange("A23:I23").format={fill:header,font:{name:font,size:10,bold:true,color:"#FFFFFF"},rowHeight:30};
sh.getRange("A24:I43").format.wrapText=true;sh.getRange("A24:I43").format.verticalAlignment="top";sh.getRange("A24:I43").format.rowHeight=92;
for(const [col,width] of [["A",39],["B",26],["C",4],["D",33],["E",25],["F",24],["G",22],["H",24],["I",25]])sh.getRange(col+"1:"+col+"48").format.columnWidth=width;
// Case evidence has its own readable wide column; cohort numerical columns remain compact enough.
sh.getRange("E1:E48").format.columnWidth=58;sh.getRange("C1:C48").format.columnWidth=25;
sh.getRange("A24:I43").format.autofitRows();
wb.recalculate();
console.log((await wb.inspect({kind:"region",sheetId:"Overview",range:"A5:B13",maxChars:2200,tableMaxRows:9,tableMaxCols:2})).ndjson);
console.log((await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:20},summary:"Final formula error scan"})).ndjson);
const xlsx=await SpreadsheetFile.exportXlsx(wb);guardSSD();await xlsx.save(path.join(out,"TECHNOLOGY_KNOWLEDGE_BASE.xlsx"));
const readback=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(out,"TECHNOLOGY_KNOWLEDGE_BASE.xlsx")));
console.log((await readback.inspect({kind:"sheet",include:"id,name",maxChars:2500})).ndjson);
const expected=data.tables;
for(const name of names.slice(1)){
 const sht=readback.worksheets.getItem(name);const d=expected[name];
 const got=sht.getRangeByIndexes(0,0,d.rows.length+1,d.headers.length).values;
 if(got.length!==d.rows.length+1)throw Error("Row count mismatch "+name);
 if(JSON.stringify(got[0])!==JSON.stringify(d.headers))throw Error("Header mismatch "+name);
 for(let i=0;i<d.rows.length;i++){
  const expectedRow=d.rows[i].map(v=>v??null);
  const actualRow=got[i+1].map((v,j)=>typeof expectedRow[j]==="string"&&expectedRow[j].startsWith("=")&&v==="\u0027"+expectedRow[j]?v.slice(1):v);
  if(JSON.stringify(actualRow)!==JSON.stringify(expectedRow))throw Error("Saved value mismatch "+name+" row "+(i+2));
 }
}
await fs.writeFile(path.join(root,"evidence/WORKBOOK_READBACK.json"),JSON.stringify({at:new Date().toISOString(),worksheets:names,rows:Object.fromEntries(names.slice(1).map(n=>[n,expected[n].rows.length])),status:"VALUES_READ_BACK",humanGold:false},null,2));
for(const name of names){
 const range=name==="Overview"?"A2:B13":"A1:D4";
 const render=await readback.render({sheetName:name,range,scale:1,format:"png"});
 guardSSD();await fs.writeFile(path.join(out,name.replaceAll("–","_").replaceAll(" ","_")+".png"),new Uint8Array(await render.arrayBuffer()));
}
for(const [sheetName,range,filename] of [
 ["Overview","A23:F25","Cases_Preview.png"],
 ["Technology Concepts","D1:H4","Mechanism_Preview.png"],
 ["Review Queue","H1:N4","Human_Review_Preview.png"]
]){
 const render=await readback.render({sheetName,range,scale:1,format:"png"});
 guardSSD();await fs.writeFile(path.join(out,filename),new Uint8Array(await render.arrayBuffer()));
}
console.log("WORKBOOK_EXPORTED_AND_READ_BACK");
