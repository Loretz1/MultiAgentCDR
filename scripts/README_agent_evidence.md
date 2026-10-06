# Cloth→Sports 离线证据流水线

当前用途：提前准备下次 4090 实例。完整 GPU 阶段尚未运行；本机小样本检查只验证实现和数据隔离。

## 1. 本机准备与上传

在项目根目录使用已有的数据处理 Python 环境运行：

```powershell
F:\anaconda3\python.exe scripts/prepare_agent_server.py build
```

输出 `doc/experiments/transfer/cloth_sports_server_v2.tar.gz`，以及同名 `.report.json`（大小、SHA256）和 `.contents.json`（文件清单）。原始数据无需重新下载。

数据包使用 v2 的 **278,677 条源域交互、284,523 条可见目标域交互**。支持/开发/验证用户为 **2816/156/156**。只含交互整数数组、分组、ID 映射、源域画像和静态物品目录；不含隐藏目标反馈、正式评估标签、完整目标历史、原始压缩文件或密钥。源域单域用户与目标域单域用户允许数字 ID 相同；只有支持/开发/验证重叠用户要求原始身份一致。

后续租用实例后上传压缩包，解压到持久化目录；不要放在实例销毁即删除的临时目录。以下 `/home/featurize/work` 仅为示例，届时先核实实际目录：

```bash
mkdir -p /home/featurize/work
tar -xzf cloth_sports_server_v2.tar.gz -C /home/featurize/work
cd /home/featurize/work/MultiAgentCDR
bash scripts/bootstrap_agent_server.sh
bash scripts/run_agent_evidence.sh
```

默认使用 Python 3.10–3.12（优先 3.11），独立环境 `$HOME/venvs/agent-evidence`；PyTorch 2.8.0 CUDA 12.8，编码依赖固定在 requirements 文件。基础 Python 可用 `BASE_PYTHON=/path/to/python3.11` 指定。安装后检查 CUDA 并保存依赖清单和 `nvidia-smi`。

编码、G 训练、证据导出依次执行；任一阶段失败即停止。首次完整运行需在服务器验收安装和真实 BGE 输出，再验收 200 对候选输入。下载模型与数据传输时间取决于网络，目前没有实测 GPU 工时；启动后根据日志给出剩余时间。

## 2. 输入与计算规则

|Agent|字段|构造方法|
|---|---|---|
|Semantic|画像、候选描述、similarity/rank、正负历史、matched/unmatched concepts、缺失标记|两域静态文本统一由 BGE 编码并 L2 归一化；源用户取每件物品最新的 4–5 星记录，按 rating−3 加权平均再归一化。无正历史时相似度缺失，跳过语义召回。记录最多 5 条相关正历史、3 条负历史。概念首版取标题/品牌/末级类别中的字面词匹配，保留原文片段、字段、物品及评论 record_id；不声称同义匹配。|
|Collaborative|g_raw、rank/percentile、候选池大小、源历史长度、映射支持规模、物品可见用户数|复用未改动的 EMCDR；源域 BPR 10 轮→可见目标域 BPR 10 轮→仅支持用户映射 MSE 1000 轮。学习率 0.01/0.01/0.001，64 维，seed=999。冻结后使用 mapped_source_user dot target_item。固定轮数作为首轮设置，不代表已找到最佳参数。|
|Overlap|实际近邻人数、直接/间接/并集支持人数及率、加权率、支持例子|源域二值训练行为余弦，在支持池中取最多 20 位正相似用户、排除自己；目标邻居为可见目标训练共现余弦前 20 个正相似物品。直接与间接支持按用户并集去重；分母为实际近邻人数。|
|Popularity/Bias|交互数、独立用户数、热度排名/分位、全局/局部支持率、平滑及相对支持|统计当前可见目标训练。global_rate=物品独立用户数/可见目标独立用户数；local_rate=直接支持人数/实际源近邻人数。平滑=(local_users+10×global_rate)/(K+10)；relative=平滑/max(global_rate,1/N)。无近邻则局部率缺失。曝光不可用，不能解释为因果偏差。|

源域画像保持原有 `rating_categories_v1` 模板，不调用 LLM；原评论在本机旁路保留，首版 Agent 通过 record_id 追溯，不把长评论全部塞入 prompt。候选文本由静态标题、品牌、类别、属性和描述构造；每个请求公共画像最多 1400 字符、候选描述最多 1000 字符，截取规则写入 provenance。编码最大 512 tokens，标题等字段排在长描述前面。

语义和 G 分数均不解释为交互概率。语义无正历史不等于 Reject；低星源历史作为独立证据保留。unmatched 表示没有找到字面支持，不能自动当作反对。

召回各取语义/G 前 50 个，RRF=sum(1/(60+rank)) 合并，按分数降序、物品 ID 升序破除平局，保留每人 10 候选。不读取隐藏历史、不强行加入正例。默认 seed=999 从开发组取 20 人；验证组另建输出目录。

排名集合为目标域完整静态目录（包括可见训练中没有观察的物品），排除 PAD=0；语义排名另外排除缺失向量。协同排名百分位=(N−rank)/max(1,N−1)×100；热门度百分位=目录中交互数不超过当前物品的比例×100，二者含义不同。二值行为的“支持”表示观察到交互，不能直接称为喜欢。

## 3. 产物与复跑

```text
runs/pilot_v1/
  encoder/{vectors.npz,manifest.json}
  g/{checkpoint.pt,vectors.npz,training.jsonl,manifest.json}
  inputs_prompt_dev/{agent_inputs.jsonl,candidate_trace.jsonl,manifest.json}
  logs/{preflight,encode,g,export}.log
```

每阶段记录配置、输入哈希、输出哈希。已完成且校验通过的同一阶段自动跳过；输入/配置改变必须用新目录。未完成训练重试从头开始，不自动续接优化器；训练日志会重置。不要混用 v1/v2 或 prompt 冻结后恢复全训练历史的产物。

单独导出验证组（不会重训 G）：

```bash
PY="$HOME/venvs/agent-evidence/bin/python"
"$PY" scripts/export_agent_evidence.py --bundle bundle --encoder runs/pilot_v1/encoder --g runs/pilot_v1/g --output runs/pilot_v1/inputs_prompt_val --group prompt_val
```

改变用户数/候选数时，复制配置并使用新的运行目录；实际人数和候选对数以 manifest 为准。

## 4. 验收后接入 Qwen

租用新实例后 Qwen 缓存和 vLLM 环境需重新建立；编码/G 环境与 vLLM 环境分开。既有模型为 `Qwen/Qwen3-30B-A3B-Instruct-2507-FP8`，历史固定 revision `5a5a776300a41aaa681dd7ff0106608ef2bc90db`。旧实例测试用 vLLM 0.29.0；新实例需重新检查驱动和 `/tokenize`、`logprob_token_ids` 支持。当前 bootstrap 只安装编码/G 依赖。

输入验收后启动既有 `start_agent_vllm.sh`，先用 2 对真实候选做接口检查：

```bash
"$HOME/venvs/agent-evidence/bin/python" scripts/collect_agent_feedback.py \
  --base-url http://127.0.0.1:8000/v1 \
  --model Qwen/Qwen3-30B-A3B-Instruct-2507-FP8 \
  --input runs/pilot_v1/inputs_prompt_dev/agent_inputs.jsonl \
  --output runs/pilot_v1/feedback_probe.jsonl --limit 2
```

采集器每次只传对应角色证据；四类 evidence 共存在文件中，但不会一起发送给每个 Agent。confidence 是 A/B/C 归一化分布的熵指标，仍需真实输入校验与后续标注校准。

完成后将 runs 的日志、manifest、输入/输出、checkpoint 和向量下载归档到本项目；先下载并校验，再停止实例，避免再次丢失模型与产物。

## 5. 本机检查

```powershell
$env:AGENT_TEST_TORCH_PYTHON='F:\anaconda3\envs\1.12.0+cu116\python.exe'
F:\anaconda3\python.exe -m unittest discover -s tests -p test_agent_evidence_pipeline.py -v
```

测试不下载模型，也不调用 API；用明确标记的测试向量验证计算，并在已有 Torch 环境执行真实 EMCDR CPU 微型训练。完整 BGE/CUDA/vLLM 兼容性留到新服务器验收。

依赖依据：[BGE 模型说明](https://huggingface.co/BAAI/bge-base-en-v1.5)、[SentenceTransformer 编码接口](https://sbert.net/docs/package_reference/sentence_transformer/model.html)、[PyTorch CUDA 安装版本](https://pytorch.org/get-started/previous-versions/)。
