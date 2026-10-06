## 结论摘要

本轮完成50对/200角色输出的AI助手证据审阅，以及全部20位开发用户/200候选的隐藏Sports历史匹配。AI助手审阅不是独立专家ABC金标签；暂定参考标签不能直接作为模型准确率依据或自动写入记忆。

**优先问题不仅是prompt：候选命中主要来自两域重复评论/同ASIN。** 20位用户隐藏目标历史219条，200候选只匹配11条，候选隐藏历史召回上限为5.02%。其中9个匹配是用户源历史同ASIN，且9个都核对出两域原始用户、ASIN、时间、评分、评论正文、摘要完全一致。不同ASIN候选191个，仅匹配2条。

目标文件未进入Agent输入，但同一真实交互在源历史中出现，构成跨域重复事件捷径。本次保留原Benchmark目录/训练行为，单独分层；没有修改ID映射或删改原始Baseline。11个已观察匹配中10个为4–5星，另1个为3星，因此已观察匹配也不等于正偏好。

## 证据忠实性与判断准则：50对诊断样本

<table header-row="true">
<tr><td>Agent</td><td>审阅输出数</td><td>事实/字段解释问题</td><td>推断/判断准则需复核</td></tr>
<tr><td>semantic</td><td>50</td><td>4</td><td>7</td></tr>
<tr><td>collaborative</td><td>50</td><td>11</td><td>0</td></tr>
<tr><td>overlap</td><td>50</td><td>0</td><td>3</td></tr>
<tr><td>popularity_bias</td><td>50</td><td>9</td><td>40</td></tr>
</table>

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

<table header-row="true">
<tr><td>固定规则</td><td>保留候选</td><td>已观察匹配</td><td>匹配率</td><td>候选命中保留率</td></tr>
<tr><td>全部候选</td><td>200</td><td>11</td><td>5.50%</td><td>100.00%</td></tr>
<tr><td>Semantic A</td><td>83</td><td>8</td><td>9.64%</td><td>72.73%</td></tr>
<tr><td>Collaborative A</td><td>115</td><td>4</td><td>3.48%</td><td>36.36%</td></tr>
<tr><td>Overlap A</td><td>2</td><td>2</td><td>100.00%</td><td>18.18%</td></tr>
<tr><td>Overlap A+B</td><td>102</td><td>8</td><td>7.84%</td><td>72.73%</td></tr>
<tr><td>Popularity A+B</td><td>2</td><td>2</td><td>100.00%</td><td>18.18%</td></tr>
<tr><td>至少2角色A</td><td>23</td><td>4</td><td>17.39%</td><td>36.36%</td></tr>
<tr><td>至少3角色非C</td><td>50</td><td>7</td><td>14.00%</td><td>63.64%</td></tr>
<tr><td>四角色均非C</td><td>1</td><td>1</td><td>100.00%</td><td>9.09%</td></tr>
<tr><td>四角色均A</td><td>0</td><td>0</td><td>—</td><td>0.00%</td></tr>
</table>

Overlap A与Popularity A+B各只有2条，2/2不能证明100%真实精确率。四角色均非C只留下1条，严格投票会损失大多数候选命中。至少3角色非C从200缩至50并保留7/11匹配，但7条全来自同ASIN重复事件，不能据此宣称新物品迁移收益。

## 等预算Top5：每位用户5个，共100个

<table header-row="true">
<tr><td>排序方式</td><td>已观察匹配/100</td><td>匹配率</td><td>不同ASIN匹配数</td></tr>
<tr><td>原始G分数</td><td>3/100</td><td>3.00%</td><td>2</td></tr>
<tr><td>原始语义相似度</td><td>8/100</td><td>8.00%</td><td>0</td></tr>
<tr><td>Collaborative pA</td><td>3/100</td><td>3.00%</td><td>1</td></tr>
<tr><td>Semantic pA</td><td>8/100</td><td>8.00%</td><td>0</td></tr>
<tr><td>Overlap pA</td><td>9/100</td><td>9.00%</td><td>1</td></tr>
<tr><td>Popularity pA</td><td>7/100</td><td>7.00%</td><td>0</td></tr>
</table>

当前样本Semantic与Collaborative的pA排序未比对应原始分数多保留已观察匹配；相同匹配数不表示排序名单完全一致。Overlap pA多保留一个匹配，样本过小且重复事件影响很大，不能作为稳定改进结论。没有因观察结果另选k或阈值。

## 同ASIN/不同ASIN分层

<table header-row="true">
<tr><td>候选类别</td><td>候选数</td><td>已观察匹配</td><td>匹配率</td></tr>
<tr><td>用户源历史已有同ASIN</td><td>9</td><td>9</td><td>100%</td></tr>
<tr><td>用户源历史无同ASIN</td><td>191</td><td>2</td><td>1.05%</td></tr>
</table>

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

## 可下载的复核资料
轻量复核表包含200条角色输出、原理由、助手意见和空白研究者确认列。完整输入与证据在本机同目录的 `review_for_researcher.csv`、`review_inputs.jsonl`，既有真实输入实验页也保留完整四角色实例。
