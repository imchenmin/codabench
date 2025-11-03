# 数据与输入输出

输入目录 `/input/cases/<case_id>/`：
- `jobs.json`：作业与操作序列，含 `processing_time`（可选）。
- `machines.json`：资源列表（`machine_id`）。
- `constraints.json`：维护/禁止窗口（`windows[*]`）。

输出文件 `schedule.json`：
- 顶层 `case_id` 与 `<case_id>` 一致；
- `machines[*].machine_id` 与资源匹配；
- `timeline[*]` 片段包含 `type`、`start`、`end`，`task` 片段需含 `job_id`、`op_id`。

具体示例与说明参见仓库 `README.md` 与 `GUIDE.md`。