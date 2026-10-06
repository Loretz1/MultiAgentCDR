# Cloth→Sports 本机数据准备（2026-10-05）

状态：当前 v2（90/5/5）已于 2026-10-06 09:03:03（北京时间）完成，CPU 处理 242.3 秒，[新版审计](2026-10-06_cloth_sports_90_5_5/audit.md) 通过。v1（60/20/20）于 08:48:55 完成并完整保留；首版四份文件校验通过，CPU 处理 226.5 秒，直连恢复后的下载及处理共 403 秒。首版最终状态见 [status.md](2026-10-05_cloth_sports_local/status.md)，完整状态见同目录 `pipeline_status.json`。

22:49 进度快照：已下载约 80 / 580 MB，总平均速度约 170KB/s；按最大剩余文件的速度推算下载还需约 102 分钟，CPU 处理暂预留 10～20 分钟。考虑网络波动，预计还需 1.5～2.5 小时，约于 10 月 6 日 00:20～01:20 完成。最初两分钟按总速度估算的 1～1.5 小时已由此估计更新。

- 数据集：Amazon2014，Clothing_Shoes_and_Jewelry → Sports_and_Outdoors，官方 5-core reviews 和 metadata，共四个压缩文件。
- 本机项目：`F:\Projects\MultiAgentCDR`；Python 3.13，约 16GB 内存，使用 CPU 做数据处理。
- 下载器：`scripts/download_cloth_sports_data.py`；四文件并发、断点续传、大小/SHA256/gzip CRC 校验。
- 后台编排：`scripts/run_cloth_sports_local.py`，等待下载成功后自动执行处理；下载失败时停止并记录错误。初次下载 PID 20232，编排 PID 12700；当前运行 PID 以日志目录 `download.pid`、`pipeline.pid` 为准。
- 处理脚本：`scripts/prepare_cloth_sports_data.py`；独立脚本，不修改原始 Benchmark 模型。
- 正式划分：all_users，cold valid/test 各为原始重叠用户的 10%，warm valid/test 为 0，种子 999；沿用 Benchmark 编号与交互协议，保留低星交互。
- 内部划分：v1 为 support/prompt_dev/prompt_val（60%/20%/20%），v2 改为 90%/5%/5%，种子均为 999；开发和内部验证用户的目标历史单独保存，不进入可见证据。
- 原始数据：`CDRec/data/Amazon2014/<domain>/raw/`。
- 证据基础产物：`CDRec/data/agent_evidence/cloth_to_sports/v1/`。
- 日志与审计：`doc/experiments/2026-10-05_cloth_sports_local/`；包括下载状态和日志、预处理日志、数据审计报告。

本轮产物为原始数据、划分、静态物品文本、源域模板摘要和训练统计。语义向量、G 训练及四 Agent 模型反馈在后续阶段完成。

## 结果

| 检查 | 当前结果 |
|---|---|
| 官方四文件可达性 | HTTP 200，支持断点续传，共 579,693,178 字节 |
| 独立小样本集成测试 | 7 项通过：Benchmark 一致性、内部隔离、原评分/评论保留、静态元数据筛选、关键字段校验、成功自动接续、下载失败不处理 |
| 本机元数据解析抽样 | 10,000 行用时 0.84 秒，约 11,975 行/秒；不代表全流程耗时 |
| 真实全量下载与校验 | 四份全部完成，大小与 gzip CRC 校验通过，SHA256 见 `download_status.json` |
| 真实全量划分及审计 | 已完成，审计检查通过；结果见 [audit.md](2026-10-05_cloth_sports_local/audit.md) 和同目录 `audit.json` |
| 全量划分独立检查 | 已确认正式冷用户按 raw identity 不进入目标训练；内部隐藏历史与可见历史完整分割，详见 `full_split_verification.json` |

测试脚本：`tests/test_cloth_sports_preparation.py`。完整成功标志为 `pipeline_status.json` 中 `state: complete`，且离线产物目录存在 `manifest.json`（`state: complete`）。

保持本机开机、联网且不进入睡眠。后台任务独立于聊天窗口，但关机、睡眠或系统终止进程会中断处理。若任务已经停止，可在项目目录重启并续传：

```powershell
& 'F:\anaconda3\python.exe' -u scripts/run_cloth_sports_local.py --direct --download-attempts 20
```

[Notion 运行记录](https://app.notion.com/p/3f06864168f5811d83dfc2a45912518b)

## 2026-10-06 直连恢复

- 08:38 检查时，两份 reviews 已校验完成，两份 metadata 因连接断开、SSL 错误停留在重试阶段，共约 426/580 MB。早期完成时间估计已失准。
- 运行环境仍配置了本地代理。同一文件的范围请求测速：环境代理约 8.9 KB/s，忽略环境代理的直连约 86.4 KB/s；随后整文件续传的 30 秒实测约 1.25 MB/s。
- 08:42 保留全部已完成文件与 `.part`，停止原任务并用 `--direct --download-attempts 20` 恢复后台编排。已完成 reviews 再次校验；metadata 从断点续传。恢复编排 PID 35848，下载 PID 24916。
- 下载器新增显式直连及重试次数参数，进度写入粒度改为 256KB；编排器启动新下载前清除旧状态歧义并记录新 PID。原日志保留，恢复编排日志为 `pipeline.resume.stdout.log` / `pipeline.resume.stderr.log`。
- 修改后 7 项集成测试再次通过，结果保存在 `tests_2026-10-06.log`。下载恢复前的状态另存为 `download_status.before_direct_20261006.json` / `pipeline_status.before_direct_20261006.json`。

## 最终数据与产物

| 数据域 | Raw 用户数 | 5-core 物品数 | 原始交互数 |
|---|---:|---:|---:|
| Cloth | 39,387 | 23,033 | 278,677 |
| Sports | 35,598 | 18,357 | 296,337 |

- 原始重叠用户 3,908 人，正式训练 overlap 3,128 人；正式 cold valid/test 各 390 人。内部 support/dev/val 为 1,878/625/625 人，开发和内部验证的 13,867 条目标历史单独隐藏。
- 产出标准 Benchmark 映射与 6 份划分、两域物品静态目录、39,387 份源域模板摘要、原评分/评论/时间旁路、完整训练与内部可见训练两份热门度统计、版本与校验 manifest。
- 实验物品全部匹配到 metadata，文本空白为 0；Cloth/Sports 标题分别缺失 23/90 件，description 分别缺失 21,614/2,661 件（约 93.8%/14.5%）。语义编码应使用已整理的标题、类别、品牌等静态字段组合，并保留缺失标记。
- 两域共享 ASIN 为 704 个，维持 Benchmark 原物品集合并在审计中记录；原始 user/item 重复行均为 0。原评论、评分及低星记录全部保留。
- 语义编码、协同 G、邻居/共现、候选及完整四角色输入、Qwen 模型反馈属于后续阶段。本轮用户摘要为 `rating_categories_v1` 模板，原评论正文另存于可追溯旁路。

## 2026-10-06 内部比例调整：90/5/5

原因：首轮 60/20/20 隐藏了 40% 的训练重叠用户，会减少 G 的跨域映射监督及 Overlap 的支持用户。先保留 90% 支持，开发和验证各留 5% 用于小规模 prompt 试点；具体泛化效果仍由后续真实输入实验检验。

| 版本 | 支持池 | 开发 | 内部验证 |
|---|---:|---:|---:|
| v1：60/20/20 | 1,878 | 625 | 625 |
| v2：90/5/5 | 2,816 | 156 | 156 |

- v1 产物与审计完整保留；v2 写入 `CDRec/data/agent_evidence/cloth_to_sports/v2/`，日志及审计写入 `doc/experiments/2026-10-06_cloth_sports_90_5_5/`。
- 数据构建脚本新增 `--prompt-dev-ratio`、`--prompt-val-ratio`、`--internal-seed`，默认 0.05/0.05/999，保存请求比例与实际比例。60/20/20 可通过显式传入 0.2/0.2 复现；标准 Benchmark 划分调用原函数。
- 重建内部用户名单、可见/隐藏目标历史、评论旁路及热门统计。9 项集成测试通过，包括新比例人数、旧比例复现、种子一致性、非法比例拒绝、参数传递和数据隔离。
- 本次变更与结果已同步至 Notion 运行记录和 TODO。

```powershell
& 'F:\anaconda3\python.exe' -u scripts/prepare_cloth_sports_data.py --output-dir CDRec/data/agent_evidence/cloth_to_sports/v2 --report-dir doc/experiments/2026-10-06_cloth_sports_90_5_5 --prompt-dev-ratio 0.05 --prompt-val-ratio 0.05 --internal-seed 999
```

v2 状态：已完成。目标可见训练交互 284,523 条，临时隐藏交互 3,371 条。`audit.json` 中 7 项检查通过；独立全量检查确认支持池包含旧版支持用户、隐藏用户不进入可见目标训练、可见与隐藏历史完整还原正式训练。原始文件与 Benchmark 配置/函数哈希和 v1 一致。完整结果见 `2026-10-06_cloth_sports_90_5_5/audit.json`、`audit.md` 和 `full_split_verification.json`。
