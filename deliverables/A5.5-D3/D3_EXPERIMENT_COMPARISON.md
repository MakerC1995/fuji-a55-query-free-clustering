# D3 实验对照

所有下列判断为同模型Silver，人工Gold=0。匿名顺序随机化不能消除同模型偏差。D2归档含原实际AI/审定修订，不是纯Qwen裸输出；DeepSeek复演为另一独立基线。

| 分集 | 配置 | 机制Correct | 材料保留 | 工艺保留 | 完整结论支持 |
|---|---|---|---|---|---|
| development | D2_ARCHIVED | 76.0% (19/25; N=28, unknown=3) | 68.9% (31/45; N=28, unknown=8) | 59.5% (22/37; N=28, unknown=12) | 46.2% (12/26; N=28, unknown=2) |
| development | D2_DEEPSEEK_REPLAY | 100.0% (25/25; N=28, unknown=3) | 80.0% (36/45; N=28, unknown=8) | 91.9% (34/37; N=28, unknown=12) | 84.6% (22/26; N=28, unknown=2) |
| development | D3_EXTRACT_ONLY | 96.0% (24/25; N=28, unknown=3) | 88.9% (40/45; N=28, unknown=8) | 97.3% (36/37; N=28, unknown=12) | 92.0% (23/25; N=28, unknown=3) |
| development | D3_FIDELITY | 92.0% (23/25; N=28, unknown=3) | 97.8% (44/45; N=28, unknown=8) | 100.0% (37/37; N=28, unknown=12) | 100.0% (25/25; N=28, unknown=3) |
| development | D3_EVIDENCE | 100.0% (25/25; N=28, unknown=3) | 97.8% (44/45; N=28, unknown=8) | 100.0% (37/37; N=28, unknown=12) | 100.0% (25/25; N=28, unknown=3) |
| development | D3_FULL | 100.0% (25/25; N=28, unknown=3) | 97.8% (44/45; N=28, unknown=8) | 100.0% (37/37; N=28, unknown=12) | 100.0% (25/25; N=28, unknown=3) |
| holdout | D2_ARCHIVED | 75.0% (18/24; N=39, unknown=15) | 74.1% (20/27; N=39, unknown=27) | 77.6% (38/49; N=39, unknown=25) | 60.0% (18/30; N=39, unknown=9) |
| holdout | D2_DEEPSEEK_REPLAY | 88.9% (24/27; N=39, unknown=12) | 70.4% (19/27; N=39, unknown=27) | 98.0% (48/49; N=39, unknown=25) | 67.7% (21/31; N=39, unknown=8) |
| holdout | D3_EXTRACT_ONLY | 100.0% (24/24; N=39, unknown=15) | 77.8% (21/27; N=39, unknown=27) | 89.8% (44/49; N=39, unknown=25) | 91.7% (22/24; N=39, unknown=15) |
| holdout | D3_FIDELITY | 100.0% (24/24; N=39, unknown=15) | 100.0% (27/27; N=39, unknown=27) | 100.0% (49/49; N=39, unknown=25) | 100.0% (24/24; N=39, unknown=15) |
| holdout | D3_EVIDENCE | 100.0% (24/24; N=39, unknown=15) | 100.0% (27/27; N=39, unknown=27) | 100.0% (49/49; N=39, unknown=25) | 100.0% (24/24; N=39, unknown=15) |
| holdout | D3_FULL | 100.0% (24/24; N=39, unknown=15) | 100.0% (27/27; N=39, unknown=27) | 100.0% (49/49; N=39, unknown=25) | 100.0% (24/24; N=39, unknown=15) |

上表严格使用全部五种贡献配置均可用的同源交集；失败与缺失会使分母小于98/42。D3_FULL与D3_EVIDENCE贡献文本相同，区别是独立双轴相关性。扩展95+盲测同源D2/完整D3对照见指标工作簿paired_full。不同配置的应有贡献/要素数若不一致，相关召回指标排除该样本并增加unknown。

## 可复现基线与消融限制
D2精确提示词/Schema/source-ID传输和2200输出上限已复演，但API模型、tokenizer和结构约束执行方式不同，不能声称复现原Qwen随机轨迹。原D2实际归档仍是主要基线。主版本、消融和费用均不补造失败。

## 贡献数量不能直接证明改善
{"0":138,"1":881,"2":56,"3":21,"4":1,"5":1}

正确贡献覆盖、过拆、遗漏、虚构、要素保真、两轴错误、来源不足、成本的numerator/denominator逐项在D3_METRICS及工作簿。Gold准确率全部N/A；Silver结果仅支持工程诊断。

## 模型更换的混杂因素

开发消融中旧Prompt的DeepSeek复演机制判定25/25，与完整D3相同，不能将对原Qwen归档的全部差异归于新流程。原归档还包括D2当时的AI修订；不是单一模型裸输出。保真要素和完整结论的变化是同源Silver诊断。

## 同源配置的实测调用成本

| 分集 | 配置 | 已有usage峰时估算USD/族 | 调用尝试/族 |
|---|---|---:|---:|
| development | D2_ARCHIVED | N/A | N/A |
| development | D2_DEEPSEEK_REPLAY | 0.000952 | 1.04 |
| development | D3_EXTRACT_ONLY | 0.001598 | 1.36 |
| development | D3_FIDELITY | 0.003234 | 2.21 |
| development | D3_EVIDENCE | 0.007181 | 3.86 |
| development | D3_FULL | 0.008253 | 4.86 |
| holdout | D2_ARCHIVED | N/A | N/A |
| holdout | D2_DEEPSEEK_REPLAY | 0.000558 | 1.00 |
| holdout | D3_EXTRACT_ONLY | 0.000934 | 1.28 |
| holdout | D3_FIDELITY | 0.002198 | 2.13 |
| holdout | D3_EVIDENCE | 0.004151 | 3.38 |
| holdout | D3_FULL | 0.004987 | 4.38 |

共享阶段只实际调用一次，按配置展示成本不能求和当账单。无usage尝试不假设免费，D2本地算力成本未知。
