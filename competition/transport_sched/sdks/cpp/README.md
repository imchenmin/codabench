# C++ SDK 指南

- 标准：C++17。
- JSON 解析库：推荐 `nlohmann/json` 单头文件（`run.sh` 会自动下载 `json.hpp`）。
- 编译：`g++ -std=c++17 -O2 main.cpp -o predict`（运行 `run.sh` 自动完成）。
- 运行：`./predict <case_dir> <out_file>`。
- 功能：读取并解析 `<case_dir>/jobs.json`、`machines.json`、`constraints.json`，生成按机台初始化的 `schedule.json`。