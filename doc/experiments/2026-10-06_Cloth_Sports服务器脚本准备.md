# Cloth→Sports 服务器脚本准备

## 最新进展（2026-10-06 11:06核对）

服务器实际部署与首批运行已完成：全目录BGE与全部源用户向量、全可见数据G、20位用户的200对四类证据与800条Qwen判断，已于10:45:58回传并通过文件哈希/概率复算验收。

当前进展及四个Agent完整实例：[真实输入与反馈](2026-10-06_Featurize_Cloth_Sports真实输入.md)；[Notion记录](https://app.notion.com/p/3f16864168f5819d8463d9dfe0fa6a5d)。全部开发/验证输入、prompt调优和下游伪交互训练尚未完成。

## 原始准备记录（计算前登记，按当时状态保留）

## 目的与运行边界

准备下一次 RTX 4090 48GB 租用所需的可移植数据、编码、G 训练、召回和四类证据导出脚本。当前仅在本机验证小样本和数据隔离；未启动远程实例。

## 预先固定的设置

- 输入：CPU v2；内部支持/开发/验证 = 2816/156/156。隐藏开发和验证用户的全部目标域历史。
- 编码：BAAI/bge-base-en-v1.5，固定 revision `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`，512 tokens，同一编码空间，正评分源域历史聚合。
- G：原始 `CDRec/src/models/emcdr.py`，源域 BPR→可见目标域 BPR→仅支持用户映射；固定轮数，不读隐藏反馈选模型。
- 试点：固定种子 999，从开发组取 20 人，每人召回 10 个候选；语义与 G 各取前 50，用 RRF 合并。
- 输出：四类证据 JSONL，可直接交给既有 `collect_agent_feedback.py`。具体字段、计算公式、运行命令见 `scripts/README_agent_evidence.md`。

## 脚本和日志

|阶段|脚本|日志/产物|
|---|---|---|
|隔离数据包|`prepare_agent_server.py`|`doc/experiments/2026-10-06_agent_pipeline_checks/`|
|文本编码|`encode_agent_text.py`|服务器 `runs/pilot_v1/logs/encode.log`|
|G 训练|`train_agent_g.py`|服务器 `runs/pilot_v1/logs/g.log`、`g/training.jsonl`|
|候选及证据|`export_agent_evidence.py`|服务器 `runs/pilot_v1/logs/export.log`|
|依赖与启动|`bootstrap_agent_server.sh`、`run_agent_evidence.sh`|服务器依赖锁定清单及日志|

## 验证记录

状态：本机准备完成；4090 尚未重新租用。脚本、配置和可移植数据包已经生成。

|检查/产物|结果|
|---|---|
|本机流水线测试|11/11 通过，包括实际 Torch 1.12.0 CPU EMCDR 微型训练、编码接口测试、召回/四角色结构、去重分母、隐藏反馈隔离、过期缓存拒绝|
|真实数据包|278,677 条源交互；284,523 条可见目标交互；2816/156/156 内部分组|
|画像/目录核对|39,387 份画像重建全部源训练交互；两域目录 ID 覆盖完整；146 位用户没有 4–5 星源评分，语义向量留空|
|压缩包验收|27 个文件完全匹配允许清单；解压后独立 preflight 通过全部哈希和数据隔离检查|
|Python/启动脚本|Python 编译检查、三份 Bash 脚本语法检查通过|
|GPU/API 调用|0；真实编码/G/Qwen 尚未执行|

上传包：`doc/experiments/transfer/cloth_sports_server_v2.tar.gz`，34,476,717 bytes，约 32.88 MiB。

SHA256：`ab0cfabb29f6d0aa32a656b1eeb1448754ac23edeacf6e9c8351e762e01d331f`。

检查日志位于 `doc/experiments/2026-10-06_agent_pipeline_checks/`：`tests.log`、`cpu_smoke.log`、`archive_preflight.log`；结构化汇总 `verification.json`，示例 `fixture_example.json` 明确标记为测试数据。

Notion：[Cloth→Sports 服务器脚本准备](https://app.notion.com/p/3f16864168f581c5b40dc94135719af5)。

## 下一步

本机所需准备已完成。下一步重新租用 4090 48GB 后，核实持久化目录和 Python/驱动，上传本包、安装独立环境并顺序运行 BGE→G→证据导出。首批真实 200 对输入人工核对后再接入 Qwen；运行后根据服务器日志估算实际工时。保存产物和日志后再停止实例。

真实 BGE 编码、完整 G 训练、Qwen 判断及正式推荐指标均尚未运行。小样本编码向量只用于测试，不能作为科研结果。
