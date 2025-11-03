# 传输调度 Benchmark 概览

本比赛旨在在给定约束下为运输任务生成可执行调度，目标最小化平均总工期（Avg Makespan），并兼顾资源利用率与 OEE 指标。

核心要点：
- 输入包含 `jobs.json`、`machines.json`、`constraints.json`；输出为 `schedule.json`。
- 参赛者提交可执行程序，平台运行摄取程序逐案生成预测，再由评分程序校验与计分。
- 评测会生成 `scores.txt`/`scores.json` 以及 `detailed_result.html` 可视化报告。