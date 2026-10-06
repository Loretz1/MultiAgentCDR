这是一份关于整个科研项目的总体需求，请你了解以下要求：

1. 在这个工作目录中，我希望研究Multi-Agent for Cross-Domain Recommendation。

2. 主要目录包含两个：/CDRec 和 /doc：
- /CDRec是项目的Benchmark，其中包含完整的跨域推荐评测逻辑，以及一些BaseLine模型代码，后续实验都将以该Benchmark为基础开展。
- /doc包含关于方法探讨的文档。随着实验不断开展，结论不断总结，文档会不断更新，记录下我们从实验中得出的结论、后续方法的改进计划等内容。
- /根目录中，目前包含overall.md总体说明文件，后续如果需要新建记录文件，请在/doc及其子目录中创建并在overall.md中增补新增文件的描述。

3. /doc文档文件包含（后续如果需要新增文件，请把文件描述添加于此）：
- "Multi-Agent_Debate_CDR.pdf"：这是方法初期探讨阶段的文档，其中规划了我们初步研究方法和大体方向。总体来说，我们希望设计一个插件式的方法，可以加入不同BaseLine方法中，获得跨域性能收益，提升源域冷用户在目标域的推荐指标。在我们的方法中，我们先按Popularity给源域用户召回目标域候选物品，再用多个智能体评价召回物品，得到prediction, reasoning和confidence，再建立agent之间的关系、图卷积、设置阈值，最终得到可信的伪交互集合，加入模型训练中。
- "四个证据Agent的构建.png"：说明四个证据 Agent 的角色、证据输入和提示词设计，以及 A/B/C 预测、简短理由与基于标签 token 概率的置信度获取方式。
- "experiments/2026-09-25_OpenLux_Luna接口探针.md"：记录 gpt-5.6-luna 在 OpenLux 上的四证据 Agent 模拟输入测试、标签概率接口结果及后续处理。
- "experiments/2026-09-28_Featurize_Qwen四证据Agent链路.md"：记录在 Featurize 单卡 4090 上部署 Qwen3 FP8、打通四证据 Agent 的 prediction/reasoning/confidence 链路，以及合成样例结果和限制；原始反馈与服务日志存于 `experiments/logs/`。
- "experiments/2026-10-05_Cloth_Sports本机数据准备.md"：记录本机真实数据下载、划分、输入基础产物与审计结果。
- "experiments/2026-10-06_Cloth_Sports服务器脚本准备.md"：记录离线证据脚本、服务器数据包、本机验证与启动方法。
- "experiments/2026-10-06_Featurize_Cloth_Sports真实输入.md"：记录新4090实例上的当前进展、真实证据构建和反馈；含四个Agent完整输入/输出实例入口。
- "experiments/2026-10-06_Cloth_Sports_Agent评估.md"：记录首批Agent证据复核、隐藏开发交互匹配与固定候选筛选评估。
- "experiments/2026-10-06_Cloth_Sports候选召回诊断.md"：记录156位开发用户的语义/G/合并召回覆盖、候选预算对照及同ASIN分层。
- "experiments/2026-10-06_Cloth_Sports_G100四证据v6.md"：记录156位开发用户G Top100证据导出、v5/v6对照及新4090实例的后台采集。
- "experiments/2026-10-06_Cloth_Sports_Popularity召回诊断.md"：记录按可见训练热度召回Top100，在原20位及全部156位开发用户上的覆盖与对照结果。
- "experiments/2026-10-06_Cloth_Sports召回预算对照.md"：比较Popularity、G、语义Top10/20/50/100的召回率及同ASIN分层。

4. 在进行实验时，如果需要对模型进行修改，请不要直接修改原始模型py文件，而是重新建立一个独立的py文件，以保证实验的可复现性。

5. 实验需要有序、清晰地整理到Notion文档“Multi-Agent CDR实验”中：
- 请在文档头部建立实验目录，以便快速检索实验。
- 每组实验的名称精简干练，能够直接表达出实验的目的。
- 每个实验中模型对应的py文件、实验对应log文件，需要在实验前清晰、简洁地整理好，以便后续可以查阅出每个实验的设置，确保实验的可复现性。
- 记录实验中模型文件的主要设计或修改，保证清晰易懂、不冗长。
- 以表格形式记录每组实验的结果。

6. TODO（详细计划与完成情况在 Notion 中维护）：

- [x] [Cloth→Sports 离线输入准备：首批20位用户验收完成](https://app.notion.com/p/3f06864168f581d6bc09fb8ad055d34f)
- [x] [Cloth→Sports 候选召回诊断：156位开发用户完成](https://app.notion.com/p/3f16864168f5816e9834ee1b6ab84306)
- [x] [Cloth→Sports Popularity召回诊断：20位及156位开发用户完成](https://app.notion.com/p/3f16864168f5812f928ed03e7b4f90c3)

7. 实验会在多台服务器上进行，为了保证一致性，请维护下方的实验记录区，该记录区记录所有正在进行的实验及其所在服务器。实验完成后，请把log拷贝到当前工作目录的对应位置，并删除下方的记录：
