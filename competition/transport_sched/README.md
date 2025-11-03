# 传输调度 benchmark

本比赛采用“自定义评估”模板，参赛者提交可执行程序（或脚本），在给定 10 组用例上生成甘特图 JSON 结果，由评分程序校验并计算指标。

## 比赛目标与规则
- 目标：在约束条件下为运输任务生成调度方案，最小化总工期（Makespan）。
- 输入：每个用例包含 3 个 JSON 文件：
  - `jobs.json`：运输任务列表（`jobs`）及其操作序列（`operations`，含 `processing_time`）。
  - `machines.json`：可用运输资源（车辆/设备），字段采用 `machine_id` 表示资源标识。
  - `constraints.json`：时间窗、容量限制、维护/休息窗口等约束（`windows`）。
- 输出：`schedule.json`（甘特图 JSON），包含每台资源的时间线片段：
  ```json
  {
    "case_id": "case_01",
    "machines": [
      {
        "machine_id": "V1",
        "timeline": [
          {"type": "task", "job_id": "J1", "op_id": "O1", "start": 0, "end": 10},
          {"type": "maintenance", "start": 10, "end": 12}
        ]
      }
    ]
  }
  ```
  - 要求：同一机台时间片不可重叠；`task` 片段的 `end-start` 应与 `jobs.json` 定义的 `processing_time` 一致（如提供）。

## 运行环境与路径
- 自动解压：平台会解压参赛 ZIP 包至 `PROGRAM_DIR`。
- 输入路径：`/input/cases/<case_id>/`（平台传入 `INPUT_DIR`）。
- 输出路径：`/output/`（平台传入 `OUTPUT_DIR`），评测程序会读取 `predictions/` 下各用例的 `schedule.json`。
- 超时与内存：在 ingestion 中可通过环境变量设置 `TIMEOUT_SECONDS` 与 `MEMORY_LIMIT_MB`（见下）。

## 参赛程序与 SDK
- 允许语言：Java（JDK 17）、C（gcc，`-O2 -pipe -static` 可选）、Python（3.10，依赖见 `requirements.txt`）、C++（C++17，`-O2 -pipe`）。
- 入口约定（任选其一）：
  - `run.sh <case_dir> <out_file>`
  - `run.py --input <case_dir> --output <out_file>`
  - `main.py --input <case_dir> --output <out_file>`
  - `predict.py::predict(case_dir, out_file)`
- 提交包需包含：可执行入口、必要依赖、清晰的运行说明文档。

## 评分与可视化
- 评分主指标：平均 Makespan（越小越好）。
- 次要指标：资源利用率（Utilization）、OEE（如维护窗口提供）。
- 评测生成 `scores.txt`/`scores.json` 以及 `detailed_result.html` 报告，可在网页端展示并下载测试用例与结果对比。

## 目录结构
```
competition/transport_sched/
  codabench.yaml
  README.md
  datasets/
    public/cases/case_01..case_10/{jobs.json,machines.json,constraints.json}
  ingestion_program/{run.py,requirements.txt}
  scoring_program/{score.py,requirements.txt}
  baseline_submission/python/ ...
  sdks/{java,c,python,cpp}/ ...
```