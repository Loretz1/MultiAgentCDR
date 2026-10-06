## 结论摘要

全部156位开发用户召回诊断已完成；隐藏Sports历史1,577条，其中源历史已有同ASIN165条、不同ASIN1,412条。当前165条只按物品ASIN对应分类，没有逐条证明原始评论相同；此前20用户中的9条重复评论已在上一轮核验。

1. 增加候选有用：标准RRF从每人10个扩大到200个，全部已观察命中69→221，总体Recall 4.38%→14.01%；不同ASIN命中11→92。
2. 当前语义召回主要覆盖源历史已有物品：Top200命中142条，其中133条同ASIN、不同ASIN仅9条；不同ASIN Recall只有0.64%。该结论限定现有BGE画像与当前开发集，不代表语义方法普遍无效。
3. 不同ASIN覆盖以G更好：G Top200不同ASIN命中146条/1,412=10.34%，RRF Top200为92条/1,412=6.52%。固定等权RRF虽然总体命中更多，但不同ASIN覆盖低于G单独召回。
4. 每路Top200并集有61,674候选，全部命中290、不同ASIN154（10.91%）；G Top200有31,200候选、不同ASIN146。扩大两路并集几乎翻倍候选预算，仅额外覆盖8条不同ASIN交互。
5. 用户1753没有可用的正评价语义画像，其语义召回为空，G仍正常。因此语义总候选数是155×K，G/RRF是156×K；不同ASIN隐藏历史存在于155位用户，分层macro分母为155而不是156。

## 标准目录：同总预算比较

总体Recall=命中/1,577；不同ASIN Recall=不同ASIN命中/1,412。表中候选集合含两种ASIN，原Benchmark不修改。语义有1位用户无画像，其他用户使用相同K预算。

<table header-row="true">
<tr><td>方法</td><td>每人K</td><td>候选数</td><td>全部命中</td><td>总体Recall</td><td>同ASIN命中</td><td>不同ASIN命中</td><td>不同ASIN Recall</td></tr>
<tr><td>语义</td><td>10</td><td>1550</td><td>66</td><td>4.19%</td><td>66</td><td>0</td><td>0.00%</td></tr>
<tr><td>G</td><td>10</td><td>1560</td><td>24</td><td>1.52%</td><td>7</td><td>17</td><td>1.20%</td></tr>
<tr><td>RRF合并</td><td>10</td><td>1560</td><td>69</td><td>4.38%</td><td>58</td><td>11</td><td>0.78%</td></tr>
<tr><td>语义</td><td>50</td><td>7750</td><td>109</td><td>6.91%</td><td>106</td><td>3</td><td>0.21%</td></tr>
<tr><td>G</td><td>50</td><td>7800</td><td>63</td><td>3.99%</td><td>12</td><td>51</td><td>3.61%</td></tr>
<tr><td>RRF合并</td><td>50</td><td>7800</td><td>133</td><td>8.43%</td><td>97</td><td>36</td><td>2.55%</td></tr>
<tr><td>语义</td><td>100</td><td>15500</td><td>126</td><td>7.99%</td><td>123</td><td>3</td><td>0.21%</td></tr>
<tr><td>G</td><td>100</td><td>15600</td><td>107</td><td>6.79%</td><td>18</td><td>89</td><td>6.30%</td></tr>
<tr><td>RRF合并</td><td>100</td><td>15600</td><td>166</td><td>10.53%</td><td>113</td><td>53</td><td>3.75%</td></tr>
<tr><td>语义</td><td>200</td><td>31000</td><td>142</td><td>9.00%</td><td>133</td><td>9</td><td>0.64%</td></tr>
<tr><td>G</td><td>200</td><td>31200</td><td>168</td><td>10.65%</td><td>22</td><td>146</td><td>10.34%</td></tr>
<tr><td>RRF合并</td><td>200</td><td>31200</td><td>221</td><td>14.01%</td><td>129</td><td>92</td><td>6.52%</td></tr>
</table>

## 两路并集：更大预算参照

每路各取K后并集去重，最多每人2K；不能把该表与总预算K的上表当作等预算收益。

<table header-row="true">
<tr><td>每路K</td><td>实际候选总数</td><td>全部命中</td><td>总体Recall</td><td>不同ASIN命中</td><td>不同ASIN Recall</td></tr>
<tr><td>10</td><td>3108</td><td>88</td><td>5.58%</td><td>17</td><td>1.20%</td></tr>
<tr><td>50</td><td>15519</td><td>165</td><td>10.46%</td><td>54</td><td>3.82%</td></tr>
<tr><td>100</td><td>30969</td><td>220</td><td>13.95%</td><td>92</td><td>6.52%</td></tr>
<tr><td>200</td><td>61674</td><td>290</td><td>18.39%</td><td>154</td><td>10.91%</td></tr>
</table>

## 补充：召回前排除用户源历史同ASIN并补足K

过滤仅根据可见源历史，不使用隐藏目标历史。此为新物品迁移诊断，不覆盖或替代标准Benchmark结果。该版本的命中均为不同ASIN，Recall分母为1,412。

<table header-row="true">
<tr><td>方法</td><td>每人K</td><td>候选数</td><td>不同ASIN命中</td><td>不同ASIN Recall</td></tr>
<tr><td>语义</td><td>10</td><td>1550</td><td>0</td><td>0.00%</td></tr>
<tr><td>G</td><td>10</td><td>1560</td><td>18</td><td>1.27%</td></tr>
<tr><td>RRF合并</td><td>10</td><td>1560</td><td>12</td><td>0.85%</td></tr>
<tr><td>语义</td><td>50</td><td>7750</td><td>3</td><td>0.21%</td></tr>
<tr><td>G</td><td>50</td><td>7800</td><td>51</td><td>3.61%</td></tr>
<tr><td>RRF合并</td><td>50</td><td>7800</td><td>36</td><td>2.55%</td></tr>
<tr><td>语义</td><td>100</td><td>15500</td><td>3</td><td>0.21%</td></tr>
<tr><td>G</td><td>100</td><td>15600</td><td>89</td><td>6.30%</td></tr>
<tr><td>RRF合并</td><td>100</td><td>15600</td><td>53</td><td>3.75%</td></tr>
<tr><td>语义</td><td>200</td><td>31000</td><td>9</td><td>0.64%</td></tr>
<tr><td>G</td><td>200</td><td>31200</td><td>146</td><td>10.34%</td></tr>
<tr><td>RRF合并</td><td>200</td><td>31200</td><td>92</td><td>6.52%</td></tr>
</table>

## 每用户指标：标准Top200

micro按隐藏交互总数加权；macro先计算各用户召回再平均。完整逐用户结果见 `per_user_metrics.csv`，包含无命中用户。

<table header-row="true">
<tr><td>方法</td><td>总体micro</td><td>总体macro</td><td>不同ASIN micro</td><td>不同ASIN macro</td><td>有命中用户/156</td></tr>
<tr><td>语义</td><td>9.00%</td><td>13.09%</td><td>0.64%</td><td>1.11%</td><td>80</td></tr>
<tr><td>G</td><td>10.65%</td><td>10.77%</td><td>10.34%</td><td>10.39%</td><td>79</td></tr>
<tr><td>RRF合并</td><td>14.01%</td><td>17.72%</td><td>6.52%</td><td>6.78%</td><td>106</td></tr>
</table>

## 复现与完整性

- 原20用户/200候选完全复现，语义分数最大绝对误差2.38e-7，G为4.77e-7；旧候选隐藏历史匹配11条、不同ASIN2条复现。
- 新RRF采用固定每路Top200，旧试点是每路Top50，因此新Top10与旧Top10可能不是同一名单；候选深度已经在计算前登记，不把两种配置混作同一方案。
- 32组结果=2种ASIN策略×4种召回方法×4个K。候选随K嵌套、无重复、ID/分数合法；统计与逐用户/隐藏历史记录独立核对。
- 候选缓存的bundle、BGE、G与源码SHA256均已固定；候选生成阶段不读取隐藏目标标签。仅评价阶段读取内部prompt_dev.pkl，内部prompt_val及正式测试未读取。
- 5项指标测试通过，含完整历史分母、无命中用户、不同ASIN分母为空、RRF并列/并集预算、ASIN跨域编号和先过滤再补足候选。
- 本机候选生成6.459秒，开发历史匹配0.280秒，不含脚本编写、检查与文档同步；Qwen调用0次、GPU使用0次。

## 完成范围与后续建议

本轮完成所有156位开发用户的候选排名与覆盖评价，未为这些新增候选生成完整四角色输入或LLM反馈。已有排名可供下一步导出四类证据，评价CSV中的目标标签不得回填到Agent输入。

建议下一轮以G Top100/200作为不同ASIN召回基准，并保留标准RRF和语义对照；先小规模修正v6字段解释与判断准则、在固定候选上对照v5/v6。是否采用排除同ASIN版本需与标准Benchmark结果分开登记。当前G Top200不同ASIN覆盖仍只有10.34%，召回改进也需继续推进。

本轮指标描述已观察隐藏交互覆盖，不是喜欢/不喜欢准确率、完整推荐HR/NDCG、Agent筛选增益或下游训练收益；未匹配不能作为C金标签。所有开发用户已用于诊断，独立内部验证仍留待方案冻结后评价。