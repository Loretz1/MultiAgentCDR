# Cloth→Sports Popularity召回诊断

## 设置与运行登记

已完成并验收；运行于本机CPU。遵循`Multi-Agent_Debate_CDR.pdf`第1页，候选主流程按Popularity召回；此前语义/G/RRF结果作为对照。

- 范围：原试点20位开发用户及全部156位开发用户，K=100；内部156位验证用户及正式验证/测试不读取。
- 热度主规则：可见Sports训练交互次数；独立训练用户数另作敏感性对照。原PDF未指定热度具体统计口径，此处明确登记首版选择。
- 按热度降序、物品ID升序取Top100，ID0不参与；所有用户共用同一份100物品名单。标准目录保留源历史同ASIN，仅在评价时分层，不做用户过滤。
- 热度只用v2可见训练数据；被隐藏的开发/内部验证目标历史不进入统计。候选完成并校验后，仅评价阶段读取内部开发反馈。
- 输出候选匹配率、总体micro/macro Recall、命中用户比例及同ASIN/不同ASIN分层；隐藏历史未匹配不代表不喜欢。
- 原20位用户从已归档的试点输入提取，不重新选用户；对照使用相同用户及同一隐藏反馈版本的已有Top100结果。
- 本轮不构造完整四Agent证据、不采集LLM反馈、不训练模型、不连接GPU服务器；远程实验继续暂停。

## 源码、日志与产物

- 独立源码：`scripts/diagnose_popularity_recall.py`；测试：`tests/test_popularity_recall.py`。
- 共享：`agent_pipeline_common.py`的数据校验/冻结机制，`diagnose_candidate_recall.py`的指标汇总与ASIN映射；原始Benchmark/模型/既有实验不修改。
- 本机产物：`doc/experiments/2026-10-06_popularity_recall/`，`request.json`在生成前冻结设置；`manifest.json`及`generation_audit.json`核验候选。
- `global_top100.json`与`top100_items.csv`：两个热度口径的排名、物品ASIN、标题和训练计数；`rankings.jsonl`与`candidate_pairs.jsonl`：逐用户固定候选，均无隐藏目标标签。候选对文件不是完整Agent输入。
- `results.json`、`aggregate_metrics.csv`、`per_user_metrics.csv`、`comparison_top100.csv`：结果与对照；`observed_history_evaluation_only.csv`含隐藏开发匹配，仅供评价，不可作为Agent输入。
- `tests.log`、`prepare.log`、`evaluate.log`、`evaluation_manifest.json`、`verification.json`：测试、日志与复核。

## 复现命令

```powershell
F:\anaconda3\python.exe -m unittest discover -s tests -p test_popularity_recall.py
F:\anaconda3\python.exe scripts/diagnose_popularity_recall.py prepare
F:\anaconda3\python.exe scripts/diagnose_popularity_recall.py evaluate
```

## 结果

### Popularity Top100主结果

候选匹配率=命中/候选数；总体Recall=命中/全部隐藏历史；不同ASIN Recall=不同ASIN命中/不同ASIN隐藏历史。指标是已观察历史覆盖，未匹配不代表不喜欢。

| 范围 | 候选数 | 全部命中 | 候选匹配率 | 总体Recall | 同ASIN命中 | 不同ASIN命中 | 不同ASIN Recall | 命中用户 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 原20位开发用户 | 2,000 | 12 | 0.60% | 12/219=5.48% | 1 | 11 | 11/200=5.50% | 8/20 |
| 全部156位开发用户 | 15,600 | 95 | 0.61% | 95/1577=6.02% | 5 | 90 | 90/1412=6.37% | 53/156 |

总体macro Recall：20用户4.85%，156用户4.63%；不同ASIN macro Recall分别4.60%和4.66%。156用户中155位有不同ASIN隐藏历史，分层macro分母为155。

### 全156位开发用户：固定Top100对照

| 方法 | 候选数 | 全部命中 | 总体Recall | 不同ASIN命中 | 不同ASIN Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Popularity | 15,600 | 95 | 6.02% | 90 | 6.37% |
| G | 15,600 | 107 | 6.79% | 89 | 6.30% |
| 语义 | 15,500 | 126 | 7.99% | 3 | 0.21% |
| RRF | 15,600 | 166 | 10.53% | 53 | 3.75% |

语义有1位用户无正评价画像，候选数为155×100；其他方案均156×100。对照来自同一划分、同一标签SHA与原用户集合，未重训G/BGE。

### 验收与结论

- 3项单元测试及6类运行复核通过。可见Sports训练284,523条，唯一用户—物品对也是284,523条，因此两种热度口径的完整Top100及顺序完全一致；Top100最小可见计数148。
- 标准Top100为同一份100物品，156位用户共15,600对候选；候选文件无隐藏目标标签，无强行插入正例。候选完成/验收后才读取内部开发反馈；内部验证和正式评估未读取。
- Popularity不同ASIN命中90条，G为89条，当前开发集覆盖基本相当；不能据1条差异宣称显著更好。G总体107条的额外覆盖主要来自同ASIN（18对5）。
- 当前Popularity只覆盖隐藏历史的6.02%，是后续筛选的候选覆盖上限；Agent筛选本身不能找回召回外的已观察交互。本轮未评价Agent筛选或下游训练收益。
- 本机候选生成1.294秒，评价0.089秒（不含开发/测试/文档同步）；Qwen调用0次，GPU使用0次。
- 本轮仅候选准备/诊断已完成。Popularity完整四Agent证据尚未导出，LLM反馈未采集；远程实验继续暂停。

Notion：[Popularity召回诊断](https://app.notion.com/p/3f16864168f5812f928ed03e7b4f90c3)。
