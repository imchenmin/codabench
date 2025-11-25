# Python SDK 指南

 - 要求：Python 3.10。
 - JSON 解析库：使用标准库 `json`。
 - 入口脚本：`run.sh <case_dir> <out_file>`（内部调用 `run.py`）。
 - 功能：读取并解析 `<case_dir>/jobs.json`、`machines.json`、`constraints.json`，生成按机台初始化的 `schedule.json`。