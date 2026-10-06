# OpenLux gpt-5.6-luna 四证据 Agent 接口探针（2026-09-25）

## 目的与环境

- 目的：验证四个证据 Agent 能否通过 OpenLux 的 `gpt-5.6-luna` 获得简短理由、A/B/C 预测及计算熵置信度所需的三个标签概率。
- 类型：接口兼容性探针；输入为合成证据，不是 CDRec 实验数据，不能据此评价推荐效果。
- 接口：`https://api.openlux.ai/v1`；模型：`gpt-5.6-luna`。密钥仅通过终端隐藏输入提供，未写入脚本或本记录。
- 运行文件：`scripts/probe_openlux.py`。本机 Windows / Python 3.13 / httpx。

## 配置

- `/v1/models` 列表中包含请求的模型。
- Responses 请求使用 `reasoning.effort=none`、`include=["message.output_text.logprobs"]`、`top_logprobs=20`、`temperature=1`；Chat 请求使用 `reasoning_effort=none`、`logprobs=true`、`top_logprobs=20`。
- 四个角色共享合成的源域偏好和目标候选描述，各自获得一条角色证据；输出格式为一句 `Reasoning` 加末尾 `Prediction: A/B/C`。

## 观察结果

| 探针 | 理由与预测 | A/B/C 概率所需信息 |
| --- | --- | --- |
| Responses，初始四角色提示词 | 四个角色均返回理由和预测；Semantic、Collaborative、Overlap 为 A；Popularity/Bias 的理由认为流行偏差明显，却给出 A | 标签位置只找到输出标签，三类不齐 |
| Responses，Semantic 复测 | 返回 A | 标签位置 `top_logprobs` 只有一个候选 token（` A`），尽管请求值为 20 |
| Chat，Semantic 复测 | 返回 A | `logprobs.content` 为空；加入 `reasoning_effort=none` 后仍为空 |
| Responses，加入明确角色边界后复测 Popularity/Bias | 理由指出高流行度、低个性化支持，预测改为 B | 标签位置仍只有一个候选 token（` B`） |

## 结论与后续

该接口已打通 `reasoning` 和 `prediction`，但本次返回不足以计算文档要求的 A/B/C 条件概率及熵置信度。缺失类别不能补零，也不能改用模型自报的数值。初始 Popularity/Bias 的理由与标签不一致，加入“高流行度本身不能判 Strong”等角色边界后，在这个合成例子上得到一致的 B；这只证明提示词需要角色约束。

下一步用能取得三个完整 logits 的开放权重模型实现置信度，并在真实 CDRec 训练数据上检查四类证据、候选召回和输出质量。若继续使用 OpenLux，需要服务商提供该模型在相同标签位置返回 A/B/C 三个 logprob 的接口证明及实测结果。
