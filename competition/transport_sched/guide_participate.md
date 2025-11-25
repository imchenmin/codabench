# 传输调度 Benchmark 参赛选手操作指南

## 平台登录与加入比赛
- 首次参赛请先注册 Codabench 账号并完成邮箱验证；设置显示名与单位/团队信息。
- 登录 Codabench（或赛事方提供的统一入口），进入 `Competitions`。
- 搜索并进入“transport_sched”比赛页面，点击 `Join/Participate` 加入并同意规则。
- 熟悉页面栏目：`Overview`、`Files/Datasets`、`Submissions`、`Leaderboard/Results`。

## 数据集与目录结构
- 仓库示例数据路径：`datasets/public/cases/`（如 `case_01`）。
- 每个用例目录 `<case_id>` 下包含：
  - `jobs.json`
  - `machines.json`
  - `constraints.json`
- 你的程序需读取上述 3 个输入并生成 `schedule.json` 作为输出。

## SDK 获取与本地快速验证
- SDK 示例位置：
  - Python：`sdks/python/run.py`
  - C++：`sdks/cpp/main.cpp`
  - C：`sdks/c/main.c`
  - Java：`sdks/java/Main.java`
- 或按语言直接运行：
  - Python：`python3 your/run.py --input datasets/public/cases/case_01 --output out/schedule.json`
  - C++：`bash your/run.sh datasets/public/cases/case_01 out/schedule.json`
  - C：`bash your/run.sh datasets/public/cases/case_01 out/schedule.json`
  - Java：`bash your/run.sh datasets/public/cases/case_01 out/schedule.json`

## 程序入口与输出规范
- 入口约定（仅支持 `run.sh`，入口文件需位于提交 ZIP 根目录）：
  - `run.sh <case_dir> <out_file>`
- 输出文件：`schedule.json`。
- 结构要求：必须包含有效的 `machines` 与 `timeline` 时间片；时间片不可重叠、不可为负时长。

## 运行环境与限制
- 容器环境版本：
  - Python：`3.10.x`
  - C：`gcc 11.x`（建议：`-O2 -pipe -std=c11`）
  - C++：`g++ 11.x`（建议：`-O2 -pipe -std=c++17`）
  - Java：`OpenJDK 17.x`（`javac`/`java`）
  - 摄取阶段默认限制：
    - `TIMEOUT_SECONDS=300`
    - `MEMORY_LIMIT_MB=2048`
- 容器内版本查询示例：`python3 --version`、`gcc --version`、`g++ --version`、`javac -version`、`java -version`。

## 打包与在线提交
- 将入口文件与源代码、依赖说明打包为 ZIP。
- 入口文件为 `run.sh`，必须位于 ZIP 根目录，并按约定接收 `<case_dir>` 与 `<out_file>` 参数。
- 在线提交后，平台在容器中解压并按入口规则逐用例调用你的程序，收集生成的 `schedule.json` 进行评分。

## 看板与成绩查看
- 在比赛页面 `Submissions/Leaderboard/Results` 查看分数、日志与排名。
- 评分端会读取聚合预测并生成报告与得分，用于更新排行榜。

## 常见问题与排查
- 未识别入口：确保提供 `run.sh`，且入口文件位于 ZIP 根目录。
- 未生成 `schedule.json`：检查输出路径是否正确传入，并确保你的程序实际写出文件。
- JSON 结构错误：`machines` 字段缺失或类型错误会导致 `valid=false`；请检查字段类型与必填项。
- 时间片问题：`timeline` 中出现重叠或负时长会触发错误；请检查每台设备的时间片连续性与合法性。

## 快速检查清单
- 入口脚本 `run.sh` 是否在 ZIP 根目录，名称与参数符合约定。
- 本地对 `case_01` 成功生成 `out/schedule.json`，结构包含 `machines` 与合法 `timeline`。
- 程序在 300 秒内完成，峰值内存不超过 2GB。
- 提交后在 `Submissions/Leaderboard/Results` 能看到分数与日志，并可定位失败原因。