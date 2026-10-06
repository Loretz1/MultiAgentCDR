# Cloth→Sports G100四证据v6

## 原方案核对与范围纠正（2026-10-06）

原文 `doc/Multi-Agent_Debate_CDR.pdf` 第1页明确规定先按Popularity召回，再对每个候选构造四类证据。此前将主流程切换到G Top100偏离原方案；本记录保留为已暂停的G召回扩展准备，不代表原Popularity主流程已完成。原文未规定K=100或热度的具体统计口径。

主流程记录纠正为Popularity候选→Semantic/Collaborative/Overlap/Popularity-Bias四角色评价。G继续可作为Collaborative证据模型；G/语义/RRF召回结果保留为对照诊断。Popularity候选覆盖尚未计算，之前的G/语义/RRF命中率不能作为Popularity结果。已有冻结脚本、输入和request按原样保留，不覆盖成Popularity。实验保持暂停。

## 设置与状态

**已按用户要求暂停，后续不自动启动采集。** 完整15,600对输入、审计结果、冻结脚本和本机采集包保留。本轮Agent采集未启动。Featurize `workspace.featurize.cn:64836` 当前仍拒绝SSH连接，无法远程确认或停止此前启动的Qwen服务（最后确认15:56，PID3411）；停止服务器进程/实例尚未确认，需通过Featurize控制台停止实例以结束计费。

- 使用全部156位**开发用户**、每人G Top100，共15,600对；内部156位验证用户保持隔离，冻结prompt后再独立评估。
- 复用既有BGE、EMCDR G和可见训练数据。原始Baseline与原导出/采集脚本不修改。标准目标目录保留同ASIN物品，评价时分层。
- 本机生成完整四类证据；只上传证据输入、冻结脚本和设置，不上传隐藏开发/验证标签或正式测试。
- v6全量采集62,400条角色判断，另选200对覆盖全部开发用户的可见证据诊断样本采集v5对照。该选择只用源侧/可见训练证据，不按目标命中挑样本。
- 先测200对v6与v5，接口/概率验收通过后继续同一v6输出文件的剩余输入。数值验收不代表prompt质量通过；全量v6用于开发诊断，尚未经独立人工审核。
- 模型仍为Qwen3-30B-A3B-Instruct-2507-FP8，revision `5a5a776300a41aaa681dd7ff0106608ef2bc90db`；固定4对并发，8192上下文，原始logprob模式。
- v6只修正字段语义、比较方向、缺失字段与曝光断言，增加角色证据判断说明；不使用隐藏反馈示例/记忆，不强行均衡ABC。A/B/C概率获取与entropy confidence公式沿用原实现，confidence未校准为正确率。
- Semantic增加显式正源评分均值；历史相关物品向量只计算当前用户历史以加速，证据含义不变。v5/v6使用同一份新输入，避免输入差异混入prompt对照。

## 源码、日志与复现

- `scripts/export_g100_agent_evidence.py`：独立G Top100输入导出；`scripts/agent_prompts_v6.py`：四角色v6准则。
- `scripts/collect_g100_feedback.py`：独立v5/v6恢复采集、限量吞吐测量、进度/剩余时间写入。
- `scripts/start_g100_vllm.sh`：8192上下文服务；`scripts/run_g100_v6_background.py`与`scripts/launch_g100_v6.sh`：后台分阶段协调/重试；`scripts/audit_g100_feedback.py`：独立概率复算。`scripts/prepare_g100_sampling.py`：仅依据可见证据选择200对对照。
- 冻结设置/本机日志目录：`doc/experiments/2026-10-06_g100_v6/`，`experiment_request.json`、`input_export.log`、`tests.log`、后续`launch_status.json`。
- 全量输入本机位置：`runs/g100_dev_v1/inputs/`；重排全量和对照输入`runs/g100_dev_v1/ready/`，完整大输入不进入Git。
- 服务器目录：`/home/featurize/agent_runtime/2026-10-06_g100_v6`；日志`logs/bootstrap.log`、`logs/vllm.log`、`logs/experiment.log`、`logs/v6_attempts.log`和`logs/v5_short_attempts.log`；反馈`outputs/v5_feedback.jsonl`、`outputs/v6_feedback.jsonl`。
- 每阶段独立request/summary/progress文件；原始输出按pair_id关联。失败成功输出保留，后台自动恢复暂时失败。

## 运行中结果

5项采集/恢复/概率审计测试通过；全15,600对G排名与已冻结候选诊断一致；新增正源评分均值已独立复算。输入及审计记录存于本机实验目录。

本轮已暂停，GPU Agent采集未启动，不再安排自动启动。此前8–12小时仅为历史粗估；恢复实验需用户明确指示。远程Qwen进程是否已停止无法确认（SSH拒绝连接）。
