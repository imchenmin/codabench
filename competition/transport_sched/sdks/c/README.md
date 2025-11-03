# C SDK 指南

- 编译器：gcc；建议参数：`-O2 -pipe`（如需静态：`-static`）。
- 编译：`gcc -O2 -pipe main.c -o predict`。
- 运行：`./predict <case_dir> <out_file>`；入口脚本 `run.sh` 已提供。