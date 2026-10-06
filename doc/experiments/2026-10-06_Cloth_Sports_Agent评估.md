# Cloth→Sports Agent证据与筛选评估

## 预先登记：2026-10-06

状态：首批开发集诊断评估已完成；未调用新LLM，未修改v5 prompt，未训练G。内部验证/正式测试未读取。

- 范围：首批20位prompt_dev用户、200对候选、800条既有Qwen判断。
- 源码：`scripts/evaluate_agent_pilot.py`；冻结设置与输入/输出哈希：`doc/experiments/2026-10-06_agent_evaluation/evaluation_request.json`。
- 输入：已归档的`inputs_prompt_dev/agent_inputs.jsonl`与`feedback_v5.jsonl`。模型与prompt版本保持不变。
- 诊断样本：5位用户42/1365/1773/1991/2174的全部10候选，共50对、200条角色输出。按可见证据有目的地选取，覆盖密集支持、通用词匹配、弱支持和低热门度；选择在计算目标命中前固定。
- 证据复核：由AI助手逐条审阅，不冒充独立人工金标准。理由忠实性和标签/理由一致性与目标命中分开报告；不将主观ABC参考判断称为真实用户偏好。
- 目标反馈：只读取内部开发集`hidden_feedback/prompt_dev.pkl`。内部prompt_val、正式验证/测试不读取；隐藏目标标签不加入Agent输入、示例或记忆。
- 指标：A/B/C及A+B候选的已观察交互匹配率、候选命中保留率、隐藏历史召回；等量每用户Top5比较pA、pA−pC、G和语义；固定多角色筛选规则，不据结果挑阈值。
- 边界：未匹配=没有观察到对应目标交互，不等于不喜欢或C金标签。本次指标限定已召回200候选，不是完整目录HR/NDCG，也不是正式推荐训练收益。20位用户是探索性开发诊断，剩余15位也不作为独立最终测试。
- 同ASIN候选与不同ASIN候选分层，保留每用户结果；名义Wilson区间仅作描述，未处理用户内相关性，不用于显著性结论。

## 脚本、日志与产物

结果根目录：`doc/experiments/2026-10-06_agent_evaluation/`。

- `review_selection.json`、`review_inputs.jsonl`、`review_compact.csv`：不含目标标签的50对诊断样本。
- `assistant_review.jsonl`、`assistant_review.md`：AI助手证据复核，后续需要研究者确认。
- `evaluation_results.json`：全部200对已观察交互评估与分层统计。
- `observed_matches_evaluation_only.csv`：仅供评估的命中标记，与Agent查询输入隔离。
- `evaluation.log`：最终执行日志；两个早期执行失败的日志及请求快照单独保留。
- `review_for_researcher.csv`：50对/200角色输出的完整输入、证据、原理由与助手意见；`review_for_researcher_compact.csv`为不重复输入的轻量复核表。人工确认标签/意见列留空。
- `duplicate_review_audit.json`：两域重复评论逐字段来源核验。
- `verification.json`：最终完整性、源码/输入哈希与统计一致性核验。
- 复核与审计源码：`scripts/record_agent_evidence_review.py`、`scripts/audit_pilot_duplicate_reviews.py`；测试：`tests/test_agent_pilot_evaluation.py`。

## 运行命令

```powershell
F:\anaconda3\python.exe scripts/evaluate_agent_pilot.py prepare
F:\anaconda3\python.exe scripts/evaluate_agent_pilot.py evaluate
```

## 结论摘要

本轮完成50对/200角色输出的AI助手证据审阅，以及全部20位开发用户/200候选的隐藏Sports历史匹配。AI助手审阅不是独立专家ABC金标签；暂定参考标签不能直接作为模型准确率依据或自动写入记忆。

**优先问题不仅是prompt：候选命中主要来自两域重复评论/同ASIN。** 20位用户隐藏目标历史219条，200候选只匹配11条，候选隐藏历史召回上限为5.02%。其中9个匹配是用户源历史同ASIN，且9个都核对出两域原始用户、ASIN、时间、评分、评论正文、摘要完全一致。不同ASIN候选191个，仅匹配2条。

目标文件未进入Agent输入，但同一真实交互在源历史中出现，构成跨域重复事件捷径。本次保留原Benchmark目录/训练行为，单独分层；没有修改ID映射或删改原始Baseline。11个已观察匹配中10个为4–5星，另1个为3星，因此已观察匹配也不等于正偏好。

## 证据忠实性与判断准则：50对诊断样本

| Agent | 审阅输出数 | 事实/字段解释问题 | 推断/判断准则需复核 |
|---|---:|---:|---:|
| semantic | 50 | 4 | 7 |
| collaborative | 50 | 11 | 0 |
| overlap | 50 | 0 | 3 |
| popularity_bias | 50 | 9 | 40 |

两个问题列可重叠；有目的取样，不作为全量错误率或专家审核通过率。未标记错误也不代表ABC正确。24条输出被助手标记为事实/字段解释问题，其中22条confidence≥0.95；高confidence并不能保证证据理解正确。

关键实例（来自已保存v5输出）：

- 用户1773/候选7399：Popularity理由称局部5.88%“far below”全局0.65%，比较方向反了。
- 用户42/候选15483：平滑局部6.7%被称为接近全局0.12%，实际约56倍。
- 用户1773/候选7553：缺少description被解释为文本向量不存在；missing_target_text_vector实际false。
- 用户42/候选14054：理由声称正评分均值5.0，输入4/4/5/5实际均值4.5。
- 用户1991/候选6506：Collaborative称99.98排名百分位很低，方向错误。
- 用户42/候选14764：局部直接支持17/20=85%，全局约0.49%，仍仅凭热门/无曝光数据判拒绝；这是判断准则问题，不可从该观察证明因果偏差。
- 用户1365/候选2456：唯一字面词pack、语义rank13692，理由承认支持有限却输出A。

原始输入/输出摘录，方便直接复核：

- 用户1773/候选7399，Popularity/Bias：输入local_support_rate=1/17≈5.88%，global_support_rate≈0.65%；prediction=C，confidence=0.982428。原理由：
  > Only 1 user in local group supported it (local support rate 5.88%), far below global rate (0.65%); high popularity percentile (99.8%) suggests bias; insufficient personalized support despite high visibility.
  5.88%实际高于0.65%，不是“far below”；无曝光数据也不能断言high visibility。
- 用户1991/候选6506，Collaborative：输入rank_percentile≈99.98（越高越靠前），candidate_visible_train_users=73、mapping_support_users=2816；prediction=B，confidence=0.813049。原理由：
  > G score 1.47 and 73 visible training users suggest moderate support, but low rank percentile (99.98) and high mapping support (2816) indicate sparse user overlap; evidence is limited by low target-side visibility.
  将99.98称为低百分位、从映射总人数推断交集稀疏均不成立。

全部50对/200条审阅：`2026-10-06_agent_evaluation/assistant_review.md`、`assistant_review.jsonl`。语义等角色有暂定参考ABC；边界未校准处保留U或A_or_B，不计算准确率。

## 隐藏目标交互匹配：固定候选内评估

匹配定义：候选(u,i)是否出现在本机内部prompt_dev隐藏目标交互表。未匹配表示未观察，不是负偏好。匹配率=已观察匹配数/所选候选数；命中保留率=保留匹配数/原候选11个匹配数。

| 固定规则 | 保留候选 | 已观察匹配 | 匹配率 | 候选命中保留率 |
|---|---:|---:|---:|---:|
| 全部候选 | 200 | 11 | 5.50% | 100.00% |
| Semantic A | 83 | 8 | 9.64% | 72.73% |
| Collaborative A | 115 | 4 | 3.48% | 36.36% |
| Overlap A | 2 | 2 | 100.00% | 18.18% |
| Overlap A+B | 102 | 8 | 7.84% | 72.73% |
| Popularity A+B | 2 | 2 | 100.00% | 18.18% |
| 至少2角色A | 23 | 4 | 17.39% | 36.36% |
| 至少3角色非C | 50 | 7 | 14.00% | 63.64% |
| 四角色均非C | 1 | 1 | 100.00% | 9.09% |
| 四角色均A | 0 | 0 | — | 0.00% |

Overlap A与Popularity A+B各只有2条，2/2不能证明100%真实精确率。四角色均非C只留下1条，严格投票会损失大多数候选命中。至少3角色非C从200缩至50并保留7/11匹配，但7条全来自同ASIN重复事件，不能据此宣称新物品迁移收益。

## 等预算Top5：每位用户5个，共100个

| 排序方式 | 已观察匹配/100 | 匹配率 | 不同ASIN匹配数 |
|---|---:|---:|---:|
| 原始G分数 | 3/100 | 3.00% | 2 |
| 原始语义相似度 | 8/100 | 8.00% | 0 |
| Collaborative pA | 3/100 | 3.00% | 1 |
| Semantic pA | 8/100 | 8.00% | 0 |
| Overlap pA | 9/100 | 9.00% | 1 |
| Popularity pA | 7/100 | 7.00% | 0 |

当前样本Semantic与Collaborative的pA排序未比对应原始分数多保留已观察匹配；相同匹配数不表示排序名单完全一致。Overlap pA多保留一个匹配，样本过小且重复事件影响很大，不能作为稳定改进结论。没有因观察结果另选k或阈值。

## 同ASIN/不同ASIN分层

| 候选类别 | 候选数 | 已观察匹配 | 匹配率 |
|---|---:|---:|---:|
| 用户源历史已有同ASIN | 9 | 9 | 100% |
| 用户源历史无同ASIN | 191 | 2 | 1.05% |

Semantic A：同ASIN8/8；不同ASIN0/75。至少3角色非C：同ASIN7/7；不同ASIN0/43。Popularity判C的198条里有9条已观察匹配，因此不能直接把C作为融合的一票否决。

该结果证明当前样本的已观察匹配收益高度依赖重复事件；不同ASIN只有2条已观察匹配，没有足够信息评价真实正偏好识别能力。没有观察到匹配的候选仍可能是相关物品。

## 审计、复现与限制

- 800条概率/Confidence复算通过；3条存在精确并列最大概率，沿用原采集器A→B→C的并列处理。
- 4项指标单元测试通过：保留零选择用户、完整隐藏历史分母、空选择处理、逐用户TopK/标签并列规则。
- pkl与原始开发评论的219条(u,i)独立对齐通过；9条跨域重复事件逐字段核验通过。
- 初版评估脚本修正了并列argmax字典顺序和TopK列表集合转换两个执行问题；设置/k/选择规则不变，旧请求与失败日志保留。源码哈希以最终 `evaluation_request.json` 为准。
- 重复评论核验为看到同ASIN分层后追加的事后来源审计，记录在 `duplicate_review_audit.json`，未据此重训或改当前输入。
- 此次没有读取内部prompt_val或正式验证/测试。5位审阅用户与其余15位结果均只作开发诊断，不能冒充最终独立测试。
- 固定200候选只覆盖219条隐藏历史中的11条，候选阶段已限制后续筛选的召回上限。暂无全目录推荐指标、下游训练、校准正确率或显著性结论。

## 建议推进顺序

1. 明确新物品迁移评估：保留原Benchmark设置报告，同时增加“排除该用户源历史同ASIN候选”的诊断版本；先讨论如何处理两域重复真实事件。
2. 在开发用户上检查更宽的语义/G召回池及候选合并，增加可观察的新物品匹配数量，不向Agent插入隐藏正例。
3. 基于上述事实错误重写字段解释与v6 prompt：禁用曝光/因果断言、要求核对局部/全局方向、区分description与向量、禁止映射人数解释成邻居支持。
4. 冻结输入/候选版本后对照v5/v6。融合暂不采用Popularity C一票否决；设置须在新评估前登记。
5. 研究者确认助手参考标签，之后才将确认样例用于few-shot/记忆；内部验证保持独立，最后评价下游伪交互训练收益。

Notion：[本轮评估](https://app.notion.com/p/3f16864168f581d0b3a8cb1977dc6a4e)。
