# C SDK 指南

- 编译器：gcc；建议参数：`-O2 -pipe`。
- JSON 解析库：使用 `cJSON`（入口脚本会自动下载到 `vendor/`）。
- 编译：`gcc -O2 -pipe main.c vendor/cJSON.c -Ivendor -o predict`（运行 `run.sh` 自动完成）。
- 运行：`./predict <case_dir> <out_file>`。
- 功能：读取 `<case_dir>/jobs.json`、`machines.json`、`constraints.json` 并解析，生成包含 `case_id` 与按机台初始化的 `machines.timeline` 的 `schedule.json`。