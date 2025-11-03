# 参赛指南（传输调度 benchmark）

## 输入输出规范
- 输入目录：`/input/cases/<case_id>/`
  - `jobs.json`：`jobs[*].job_id`，`operations[*].op_id`，`processing_time`（秒/单位时间）。
  - `machines.json`：`machines[*].machine_id`。
  - `constraints.json`：`windows[*]`，包含 `start`、`duration`、`machine_count`（用于 OEE 计算）。
- 输出文件：`schedule.json`
  - `case_id`：与 `<case_id>` 一致。
  - `machines[*].machine_id`：资源标识。
  - `machines[*].timeline[*]`：时间片，字段：`type` ∈ {`task`,`maintenance`}，`start`,`end`，若 `type=task` 需包含 `job_id`,`op_id`。
  - 同一机台时间片不可重叠；`end>=start`；若提供 `processing_time` 则要求 `end-start` 与之匹配。

## SDK格式要求
- Python（3.10）：入口 `run.py --input <case_dir> --output <out_file>`。
- Java（JDK 17）：入口 `run.sh` 编译并运行 `Main.java`。
- C（gcc）：入口 `run.sh` 编译并运行 `predict`；建议 `-O2 -pipe`。
- C++（C++17）：入口 `run.sh` 编译并运行 `predict`。
- 参赛包需包含：入口（脚本/可执行）、依赖说明、运行文档。

## 评分标准详解
- 主指标：平均 Makespan（越小越好）。
- 次指标：平均资源利用率（Utilization%）、平均 OEE%。
- JSON校验：字段完整性、时间片不重叠、时长与 `processing_time` 一致（如提供）。
- 输出：`scores.txt`、`scores.json`、`detailed_result.html`（网页展示）。

## 运行环境与限制
- 自动解压至 `PROGRAM_DIR`；ingestion 环境变量：
  - `TIMEOUT_SECONDS`（默认 300）
  - `MEMORY_LIMIT_MB`（默认 2048，POSIX 下以 RLIMIT 方式限制）

## 常见问题
- 报错“未找到可执行入口”：确保提供 `run.sh/run.py/main.py/predict.py::predict`。
- 报告为空或 invalid：检查 `machines` 字段与 `timeline` 时间片是否正确。