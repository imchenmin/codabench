# 评测说明

评分程序校验 JSON 结构、时间片约束与处理时长一致性，并计算：
- Avg Makespan：各用例 Makespan 的平均值（越小越好）。
- Avg Utilization：基于总时长与机台数量的平均利用率（%）。
- Avg OEE：扣除计划维护窗口后的有效产出率（%）。

违规校验包括：
- 同机台时间片重叠或负时长；
- `task` 片段时长与 `processing_time` 不一致（如提供）；
- 任务与约束窗口（maintenance/forbidden）时间段发生重叠。