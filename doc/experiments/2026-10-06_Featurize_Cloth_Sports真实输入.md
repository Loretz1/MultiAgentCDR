# Featurize Cloth→Sports 真实输入与反馈

## 完成状态

2026-10-06 10:45:58 完成本机归档校验，自09:39:59启动部署约66分钟，含连接上传约70分钟。全目录编码、全可见数据G训练及首批20位开发用户×10候选×4 Agent完成；尚未扩展全部156位开发用户或使用隐藏目标反馈评价推荐性能。

Notion：[真实输入与反馈](https://app.notion.com/p/3f16864168f5819d8463d9dfe0fa6a5d)。

## 当前进展与实例入口

Notion页面开头已于2026-10-06 11:06重新写入并回读核对，标题为“最新进展：四个Agent真实输入与输出（首批200对）”。此处验证的是接口返回内容，尚未确认用户客户端显示一致。

**已完成离线输入构建链路和首批20位用户验收；全部开发/验证用户的候选与证据还未导出。**

| 内容 | 当前进展 |
|---|---|
| 源摘要/两域静态目录 | 全量完成 |
| BGE/源用户向量、G checkpoint | 全量可见范围完成 |
| 四Agent真实输入与输出 | 首批20位用户、200对输入、800判断完成 |
| 全部156位开发用户、156位内部验证用户 | 尚未扩展 |
| prompt/记忆调优、下游伪交互训练 | 尚未完成 |

[四个Agent完整输入/输出实例](2026-10-06_featurize_real/real_example.md)：含公共上下文来源、每个角色字段含义/计算方法、完整证据JSON、system指令、原始reasoning/prediction/confidence及复核意见。

## 运行设置（计算前登记）

- 服务器：`workspace.featurize.cn:24706`；RTX4090，49140MiB，驱动610.57.04，Python3.11.8。
- 初始目录：`/home/featurize/work/MultiAgentCDR_runs/2026-10-06_cloth_sports/MultiAgentCDR`；最终验证/归档目录：`/home/featurize/agent_runtime/pilot_v5/MultiAgentCDR`。
- 数据v2：源交互278677，可见目标交互284523，support/dev/val=2816/156/156；隐藏目标反馈和正式评估标签不上传。
- 配置：`scripts/configs/cloth_sports_agent.json`，seed999。语义/G各召回50、RRF常数60、保留10候选，源/目标邻居最多20。
- 编码：BGE-base-en-v1.5，revision `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`；统一归一化768维，源用户由最新4–5星历史按评分减3加权。
- G：复用未修改原始EMCDR；源/目标BPR各10轮、映射1000轮，维度64，仅支持池映射；固定轮数，不按隐藏反馈选模型。
- Qwen：Qwen3-30B-A3B-Instruct-2507-FP8，revision `5a5a776300a41aaa681dd7ff0106608ef2bc90db`。
- vLLM0.29.0，raw_logprobs、上下文4096、max_num_seqs4、显存利用率0.85，FlashInfer sampler关闭。Marlin权重压缩路径，运行器约29.11GiB。
- 4个候选对并发；先96-token理由，再在Prediction前缀请求1 token，显式取三标签原始logprob；temperature0，不施加标签强制采样约束。
- 原上传包SHA256：`ab0cfabb29f6d0aa32a656b1eeb1448754ac23edeacf6e9c8351e762e01d331f`。

## 阶段结果

| 阶段 | 结果/耗时 |
|---|---|
| 全目录编码与源用户向量 | 170.024秒；39387源用户、23033源物品、18357目标物品 |
| G三阶段训练 | 23.205秒；映射仅用2816位支持用户 |
| 候选/四类证据 | 200对；不插入隐藏正例，不读取隐藏目标反馈 |
| 独立输入核验 | G分数/排名、语义分数、字面概念来源、支持人数/分母、热门统计，各200对通过 |
| 上下文核验 | 800角色前缀；最长1930token，加160预留低于4096 |
| v4反馈 | 189.807秒；180对完整，20对理由token/格式失败，原始结果保留 |
| v5反馈 | 累计359.654秒；首次196对、4次ReadTimeout，恢复后200对完成；无理由格式失败 |
| 结果回传 | 274110025字节，124.7秒 |
| 本机验收 | 包SHA256、80份文件大小/哈希、200对/800判断、三标签概率/Confidence/Label mass复算通过 |

v5只增加理由最多35词/320字符、引用1–2个关键统计与数字展示四舍五入的要求；角色准则、评分提示和概率计算沿用v4。最终200对统一v5，不混用v4。35词/320字符是提示约束，执行校验仍采用原96-token、单行且不超过400字符标准。

## 四角色结果

| Agent | A | B | C | 平均Confidence | Confidence≥0.95 | 最小Label mass |
|---|---:|---:|---:|---:|---:|---:|
| semantic | 83 | 30 | 87 | 0.9267 | 81.0% | 0.993278 |
| collaborative | 115 | 62 | 23 | 0.9505 | 85.5% | 0.994564 |
| overlap | 2 | 100 | 98 | 0.9861 | 95.5% | 0.998968 |
| popularity_bias | 0 | 2 | 198 | 0.9903 | 95.5% | 0.995253 |

Confidence=`1-H(pABC)/ln(3)`表示标签分布集中程度，未校准为判断正确概率。200候选有9对与用户源历史共享ASIN，后续单独分析；尚无HR/NDCG等推荐收益结论。

## 实例与判断质量

完整真实输入输出见 [real_example.md](2026-10-06_featurize_real/real_example.md)。四角色两阶段请求由保存输入、理由、实际前缀及执行源码重建在 `real_example_requests.json`，不是原始HTTP报文抓包。

抽查用户1365、候选2456应急保温毯：Semantic只匹配通用词pack，理由说支持有限却输出A；Collaborative混淆候选全局训练用户数与邻居证据；Popularity/Bias在exposure_available=false时声称曝光高并归因偏差。需要人工复核和prompt调优，当前结果不能直接视为可信伪交互。

## 存储问题与来源

work目录访问/日志写入出现长时间阻塞。10:34:07重启vLLM，将服务日志移至实例本地盘；10:42复制完整runs到本地盘完成验收和归档，原目录保留。旧目录最终汇总曾失败，其底层错误未留在当前覆盖后的结果验证日志中；本地盘重做通过。归档的 `finalization_status.json`、`pilot_status_v4.json` 是历史失败记录，当前状态以 `pilot_status.json`、`result_summary.json` 和本机 `archive_verification.json` 为准。

## 本机归档索引

根目录：`doc/experiments/2026-10-06_featurize_real/`。

- `pilot_results_v5.tar.gz`：完整服务器结果/执行源码快照，已解压至 `artifacts/MultiAgentCDR/`；不含Qwen权重、环境或密钥。
- `archive_verification.json`：本机校验；`artifacts/result_archive_manifest.json`：80份文件SHA256。
- `result_summary.json`：角色统计、三组真实实例与共享ASIN统计；`local_verified_summary.json`：本机复算。
- `artifacts/MultiAgentCDR/runs/pilot_v1/encoder/`：全目录/源用户向量及manifest。
- `.../g/`：checkpoint、映射源用户/目标物品向量、逐轮训练日志及manifest。
- `.../inputs_prompt_dev/`：200对证据、召回轨迹、来源manifest。
- `.../feedback_v5.jsonl`：200对完整输出，含prediction/reasoning/confidence及三标签logprob/概率/Label mass。
- `.../feedback.jsonl`、`feedback.summary.json`、`feedback_v5_first_attempt.summary.json`：原v4及v5历史失败清单。
- `.../logs/`、`runs/setup/`：部署、编码/G、输入核验、接口探针、采集、vLLM及最终校验日志，硬件与两个环境依赖锁。
- `artifacts/MultiAgentCDR/scripts/`、`CDRec/src/`：实际执行代码；原可见数据包本机保留在 `doc/experiments/transfer/cloth_sports_server_v2.tar.gz`，无需重下Raw文件。

完成后修正本机调度脚本 `run_real_agent_pilot.py`：采用v5最终采集/复算，健康检查绕过环境代理；只做语法校验，没有再次执行GPU流水线，本次代码以归档快照为准。后续项目和日志使用实例本地盘，完成后回传。

## 下一步

人工复核首批证据和理由，明确A/B/C准则并修正无曝光归因、通用词匹配与未观察交互表述；在开发集调优prompt/记忆后扩展156位开发用户。内部156位验证用户保持隔离；方案冻结后恢复原训练重叠用户的目标历史、重训G并重建证据，再进行伪交互和下游推荐实验。

结果包SHA256：`97732de61b3e160045fbc7067fc1cc5c18ab35ebe5dac871cf888dd3c1627154`。
