import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import {Workbook,SpreadsheetFile,FileBlob} from "@oai/artifact-tool";
const ROOT="/Volumes/Fuji_SSD_Work/workspaces/a55_d3_quality_convergence";
const OUT=path.join(ROOT,"outputs/01a171fb-0dd6-7792-b36b-80e200aba942");
const data=JSON.parse(await fs.readFile(path.join(ROOT,"working/WORKBOOK_DATA.json"),"utf8"));
await fs.mkdir(path.join(OUT,"previews"),{recursive:true});
const qa=[];
const letters=n=>{let s="";for(;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const legal=v=>typeof v==="string"&&v.startsWith("=")?"'"+v:v;
const norm=v=>v===undefined||v===""?null:v;
const dims=["对象","问题","机制","材料","工艺方法","工序顺序","参数","效果","多贡献","虚构","来源充分性","A应用证据","B工程关联"];
const judgments=["Correct","Partially Correct","Incorrect","Insufficient Source Evidence","Uncertain"];
const Adefs=[["A1","明确喷头应用"],["A2","明确喷头制造"],["A3","喷头邻接系统"],["A4","无明确喷头应用证据"],["AU","不确定"]];
const Bdefs=[["B1","直接技术关联"],["B2","制造关联"],["B3","可迁移"],["B4","仅背景"],["B5","未识别联系"],["BU","不确定"]];
function sheet(wb,name,title,headers,rows,widths){
 const s=wb.worksheets.add(name);s.showGridLines=false;
 const n=headers.length,end=letters(n),last=5+rows.length;
 s.getRange("A2").values=[[title]];s.getRange("A2").format.font={name:"Arial",size:14,bold:true,color:"#172B4D"};
 s.getRange("A3:"+end+"3").format.borders={bottom:{style:"thin",color:"#A4B4C8"}};
 const matrix=[headers,...rows].map(r=>r.map(legal));
 s.getRange("A5:"+end+last).values=matrix;
 const region=s.getRange("A5:"+end+last);region.format.font={name:"Arial",size:10,color:"#172B4D"};region.format.wrapText=true;region.format.verticalAlignment="top";
 for(let c=0;c<n;c++)s.getRange(letters(c+1)+"5:"+letters(c+1)+last).format.columnWidth=widths[c]||25;
 if(rows.length) s.getRange("A6:"+end+last).format.autofitRows();
 // Explicit CJK line-height allowance; native autofit underestimates some Japanese glyphs.
 for(let i=0;i<rows.length;i++){
  let lines=1;
  for(let c=0;c<n;c++){
   const v=rows[i][c];if(v===null||v===undefined)continue;
   const available=Math.max(8,(widths[c]||25)-2);
   const count=String(v).split("\n").reduce((sum,part)=>sum+Math.max(1,Math.ceil(Array.from(part).reduce((z,ch)=>z+(ch.charCodeAt(0)>255?2:1),0)/available)),0);
   lines=Math.max(lines,count);
  }
  s.getRange("A"+(i+6)+":"+end+(i+6)).format.rowHeight=Math.min(409,Math.max(20,lines*13+5));
 }
 s.getRange("A5:"+end+"5").format={fill:"#253858",font:{name:"Arial",size:10,bold:true,color:"#FFFFFF"},wrapText:true,horizontalAlignment:"center",verticalAlignment:"center",rowHeight:32};
 if(rows.length){const t=s.tables.add("A5:"+end+last,true,"T_"+name.replace(/[^a-zA-Z0-9]/g,""));t.showFilterButton=true;}
 if(rows.length>15){s.freezePanes.freezeRows(5);s.freezePanes.freezeColumns(name==="Human review"?3:1);}
 if(rows.length) s.getRange("A6:"+end+last).conditionalFormats.add("containsText",{text:"FAILED",format:{fill:"#FDE9E7",font:{color:"#AE2A19",bold:true}}});
 return {s,name,matrix,start:5,rows,cols:n,last,formulaCells:new Set()};
}
function formula(rec,row,col,value){rec.s.getCell(row-1,col-1).formulas=[[value]];rec.formulaCells.add((row-5)+","+(col-1));}
function summary(wb,name,title,rows,widths=[37,110]){
 return sheet(wb,name,title,["事项","结果"],rows,widths);
}
async function finish(wb,name,recs,extra=[]){
 wb.recalculate();
 for(const rec of recs){
  const check=rec.s.getRange("A5:"+letters(rec.cols)+rec.last).values;
  for(let r=0;r<rec.matrix.length;r++)for(let c=0;c<rec.cols;c++){
   if(rec.formulaCells.has(r+","+c))continue;
   assert.deepEqual(norm(check[r]?.[c]),norm(rec.matrix[r][c]),name+" in-memory "+rec.name+" "+r+","+c);
  }
  let range=rec.cols===2?"A2:B"+Math.min(rec.last,14):"A2:"+letters(Math.min(rec.cols,7))+"9";
  const blob=await wb.render({sheetName:rec.name,range,scale:1,format:"png"});
  await fs.writeFile(path.join(OUT,"previews",name+"__"+rec.name.replaceAll(" ","_")+".png"),new Uint8Array(await blob.arrayBuffer()));
 }
 for(const e of extra){const blob=await wb.render({sheetName:e.sheet,range:e.range,scale:1,format:"png"});await fs.writeFile(path.join(OUT,"previews",name+"__"+e.suffix+".png"),new Uint8Array(await blob.arrayBuffer()));}
 const scan=await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:50},maxChars:4000});
 const file=path.join(OUT,name+".xlsx");const x=await SpreadsheetFile.exportXlsx(wb);await x.save(file);
 const reopened=await SpreadsheetFile.importXlsx(await FileBlob.load(file));
 let cells=0;
 for(const rec of recs){
  const v=reopened.worksheets.getItem(rec.name).getRange("A5:"+letters(rec.cols)+rec.last).values;
  for(let r=0;r<rec.matrix.length;r++)for(let c=0;c<rec.cols;c++){
   if(rec.formulaCells.has(r+","+c))continue;
   let actual=norm(v[r]?.[c]),expected=norm(rec.matrix[r][c]);
   if(typeof expected==="string"&&expected.startsWith("'=")&&actual===expected.slice(1))actual=expected;
   assert.deepEqual(actual,expected,name+" exported "+rec.name+" "+r+","+c);cells++;
  }
 }
 await fs.unlink(path.join(ROOT,name+".xlsx")).catch(e=>{if(e.code!=="ENOENT")throw e;});
 await fs.symlink(path.relative(ROOT,file),path.join(ROOT,name+".xlsx"));
 qa.push({file,sheets:recs.map(r=>r.name),nonformula_cells_verified:cells,error_scan:scan.ndjson,readback:true});
 console.log(JSON.stringify({exported:name,sheets:recs.length,nonformula_cells_verified:cells}));
}
{
 const w=Workbook.create(),r=[];
 const ov=summary(w,"Overview","D3 独立样本与人工审核",[
  ["唯一评估族",140],["Development",98],["Holdout",42],["历史专项","45族另行统计，39原发现与6探针；不混入独立评估"],
  ["标签等级","现有模型审核为Silver。Human列全空；人工Gold=0。"],
  ["人工操作","在Human review填写判定、审核人、时间和理由；完整填写后可由导入程序生成独立Gold表。"],
  ["人工表已填写行",null],["原文","Source text无损分段保存Title/Abstract；S编号及Unicode起止位置与证据一致。"],
  ["版本","D3.1冻结主评估；D3.1-R1仅为后续相关性争议裁决，不回改盲测预测。"]]);r.push(ov);
 const hdr=["Family ID","分集","来源队列","语言","摘要字符数","抽样代理（非真值）","标题","D2原机制","D3机制","处理状态","原文哈希","抽样原因"];
 r.push(sheet(w,"Development","98族开发样本",hdr,data.dev,[23,18,46,10,15,42,58,68,80,19,28,40]));
 r.push(sheet(w,"Holdout","42族冻结盲测",hdr,data.holdout,[23,18,46,10,15,42,58,68,80,19,28,40]));
 const humanRows=data.human.map(x=>[...x,null]);
 const human=sheet(w,"Human review","人工审核入口（空白，尚无Gold）",["Family ID","分集","待审核版本","原文哈希","审核者","审核时间","审核理由",...dims.map(x=>"Human_"+x),"填写状态"],humanRows,[23,17,25,28,19,22,65,...dims.map(()=>27),28]);r.push(human);
 human.s.getRange("E6:T"+human.last).format.fill="#FFF2CC";
 for(let c=8;c<=20;c++){const list=c<=18?judgments:c===19?Adefs.map(x=>x[0]):Bdefs.map(x=>x[0]);human.s.getRange(letters(c)+"6:"+letters(c)+human.last).dataValidation={rule:{type:"list",values:list}};}
 human.s.getRange("F6:F"+human.last).setNumberFormat("yyyy-mm-dd");
 for(let row=6;row<=human.last;row++)formula(human,row,21,'=IF(COUNTBLANK(E'+row+':T'+row+')>0,"待人工审核","已填写（待导入）")');
 formula(ov,12,2,'=COUNTIFS(\'Human review\'!$U$6:$U$'+human.last+',"已填写（待导入）")');
 // Prove completion logic reacts, then restore every placeholder.
 human.s.getRange("E6:G6").values=[["TEST ONLY","2026-10-27","TEST ONLY"]];
 human.s.getRange("H6:R6").values=[Array(11).fill("Correct")];
 assert.equal(human.s.getRange("U6").values[0][0],"待人工审核");
 human.s.getRange("S6:T6").values=[["A1","B1"]];w.recalculate();
 assert.equal(human.s.getRange("U6").values[0][0],"已填写（待导入）");
 human.s.getRange("E6:T6").values=[Array(16).fill(null)];w.recalculate();
 assert.equal(human.s.getRange("U6").values[0][0],"待人工审核");
 r.push(sheet(w,"History","45族历史专项回归",["Family ID","独立范围","历史分支","历史节点","恢复判定","原文充分性","对象","问题","办法","材料参数","原Unrelated是否错误","D2到D3变化","理由","摘要未披露的历史细节","需全文","审核请求"],data.history,[23,25,18,20,32,24,27,27,27,27,22,74,80,80,15,48]));
 r.push(sheet(w,"Source text","评估原文（完整无损分段）",["Family ID","Source ID","字段","Start","End","原文片段","原文哈希"],data.sources_eval,[23,16,15,11,11,115,28]));
 r.push(sheet(w,"Protocol","评估口径",["项目","规则"],[
  ["抽样","固定种子20261027；11队列分层，历史45和已知问题不进入holdout；代理类别不是Gold。"],
  ["标签","Correct / Partially Correct / Incorrect / Insufficient Source Evidence / Uncertain。"],
  ["正确率","Correct / (Correct+Partially Correct+Incorrect)，来源不足与不确定单列。"],
  ["盲测","代码/提示词/Schema在盲测前冻结；仅预定配置、固定重试和缓存恢复。"],
  ["证据","位置一致、字段支持、完整结论三层分开；推断与无支持结论不标为已确认事实。"],
  ["来源","D2冻结Title/Abstract、原贡献/概念/关系表；D3_PATENT_CONTRIBUTIONS与D3_LABELS、D3_MANIFEST及D3_EVALUATION_PROTOCOL.md。"],
  ["人工输入","黄色列供真实人工填写；不得复制Silver当成人工Gold。"]],[28,120]));
 await finish(w,"D3_EVALUATION_SET",r,[{sheet:"Human review",range:"H5:N8",suffix:"Human_fields"}]);
}
{
 const w=Workbook.create(),r=[];
 const summaryRec=sheet(w,"Summary","D2与D3质量对照",["分集","D2可判定数","D2机制Correct率","D3可判定数","D3机制Correct率","变化（百分点）","证据等级"],[["Development",null,null,null,null,null,"Silver"],["Holdout",null,null,null,null,null,"Silver"]],[21,20,24,20,24,24,19]);r.push(summaryRec);
 const metrics=data.metrics.map(m=>[m.scope,m.split,m.configuration,m.metric,m.numerator,m.denominator,null,m.label_tier,m.sample_n,m.unknown_n,m.unit,m.notes]);
 const met=sheet(w,"Metrics","完整指标、分母与未知项",["范围","分集","配置","指标","分子","分母","值","标签等级","样本数","未知/不适用数","单位","分母说明"],metrics,[28,19,28,47,16,16,18,18,14,20,25,110]);r.push(met);
 for(let i=0;i<metrics.length;i++){const row=i+6;formula(met,row,7,'=IF(COUNTBLANK(E'+row+':F'+row+')>0,"N/A",IF(F'+row+'=0,"N/A",E'+row+'/F'+row+'))');met.s.getRange("G"+row).setNumberFormat(data.metrics[i].unit==="rate"?"0.0%":"0.0000");}
 for(const [i,split]of ["development","holdout"].entries()){
  const rr=i+6;
  for(const [conf,denCol,valueCol]of [["D2_ARCHIVED",2,3],["D3_FULL",4,5]]){
   const idx=data.metrics.findIndex(m=>m.scope==="paired_full"&&m.split===split&&m.configuration===conf&&m.metric==="technical_mechanism_correct_rate");assert(idx>=0);
   formula(summaryRec,rr,denCol,"='Metrics'!F"+(idx+6));formula(summaryRec,rr,valueCol,"='Metrics'!G"+(idx+6));summaryRec.s.getRange(letters(valueCol)+rr).setNumberFormat("0.0%");
  }
  formula(summaryRec,rr,6,'=IF(OR(C'+rr+'="N/A",E'+rr+'="N/A"),"N/A",(E'+rr+'-C'+rr+')*100)');summaryRec.s.getRange("F"+rr).setNumberFormat('0.0" pp"');
 }
 summaryRec.s.getRange("A3").values=[["人工Gold=0，人工准确率N/A；下列为同模型Silver对照。"]];
 summaryRec.s.getRange("A3").format.font={name:"Arial",size:10,color:"#5E6C84"};
 const use=sheet(w,"Usage","真实调用和费用估算（账单未知）",["阶段","尝试","返回usage","有效输出","失败","输入token","输出token","缓存命中token","峰时USD上界估算","usage缺失","耗时秒累计"],data.usage.map(x=>[x.kind,x.attempts,x.model_responses,x.validated,x.failed,x.prompt_tokens,x.output_tokens,x.cache_hit_tokens,x.peak_usd_upper_estimate,x.missing_usage,x.wall_s_sum]),[30,14,17,17,14,20,20,22,27,19,22]);r.push(use);
 use.s.getRange("I6:I"+use.last).setNumberFormat('"$"0.000000');
 r.push(sheet(w,"Confusions","定向相关性样本混淆计数",["系统","原预测","独立Silver参考","节点数"],data.confusions.map(x=>[x.system,x.predicted,x.reference,x.count]),[25,25,35,18]));
 r.push(sheet(w,"Failures","运行失败（不当作弃判）",["Family ID","状态","错误","标题","原文哈希"],data.status.filter(x=>!["VALID","QUARANTINED"].includes(x.status)).map(x=>[x.family_id,x.status,x.error,x.source_title,x.source_text_hash]),[24,25,115,75,30]));
 // Verify every ratio against independent Python-produced numerator/denominator.
 w.recalculate();
 for(let i=0;i<data.metrics.length;i++){const actual=met.s.getRange("G"+(i+6)).values[0][0],m=data.metrics[i];if(m.value===null)assert.equal(actual,"N/A");else assert(Math.abs(actual-m.value)<1e-10);}
 await finish(w,"D3_QUALITY_METRICS",r);
}
{
 const w=Workbook.create(),r=[];
 const summaryRec=sheet(w,"Summary","喷头相关性双轴结果",["A轴","文献应用证据","族数","B轴","工程关联","族数"],Adefs.map((a,i)=>[a[0],a[1],null,Bdefs[i]?.[0]||null,Bdefs[i]?.[1]||null,null]).concat([[null,null,null,"BU","不确定",null]]),[17,39,17,17,35,17]);r.push(summaryRec);
 const labels=sheet(w,"Labels","1117族双轴标签与解释",["Family ID","A应用证据","B工程关联","D2归档类别","喷头技术对象","可能应用","机制关联理由","工程推断（非文献事实）","关键适用条件","待验证问题","原文应用证据","抽取状态","版本","冻结A轴","冻结B轴","需全文","原文哈希"],data.relevance,[24,18,18,27,43,60,95,95,90,90,90,22,28,18,18,16,28]);r.push(labels);
 for(let i=0;i<Adefs.length;i++)formula(summaryRec,i+6,3,'=COUNTIFS(\'Labels\'!$B$6:$B$'+labels.last+',"'+Adefs[i][0]+'")');
 for(let i=0;i<Bdefs.length;i++)formula(summaryRec,i+6,6,'=COUNTIFS(\'Labels\'!$C$6:$C$'+labels.last+',"'+Bdefs[i][0]+'")');
 summaryRec.s.getRange("A3").values=[["全部为Silver；R1为事后修订，冻结A/B保留。失败留空。"]];
 summaryRec.s.getRange("A3").format.font={name:"Arial",size:10,color:"#5E6C84"};
 r.push(sheet(w,"Node audit","151节点双向原文复审",["Technology ID","支持Family IDs","抽样原因","D2最终类别","独立Silver旧类参考","A轴","B轴","机制理由","工程推断","适用条件","来源族是否冲突","冲突解释","原机制支持度","需全文","审核请求"],data.node_audits,[29,40,48,24,28,16,16,95,95,90,22,90,30,16,48]));
 r.push(sheet(w,"Source text","主范围原文（无损分段）",["Family ID","Source ID","字段","Start","End","原文片段","原文哈希"],data.sources_all,[24,16,15,11,11,115,28]));
 await finish(w,"D3_PRINTHEAD_RELEVANCE",r,[{sheet:"Labels",range:"M5:Q9",suffix:"Label_versions"}]);
}
await fs.writeFile(path.join(ROOT,"evidence/WORKBOOK_QA.json"),JSON.stringify({at:new Date().toISOString(),workbooks:qa,human_input_completion_logic_tested:true,test_inputs_restored:true,formulas_recalculated:true,native_excel_application_tested:false},null,2));
