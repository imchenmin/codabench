# Java SDK 指南

- 要求：JDK 17。
- JSON 解析库：推荐 `Gson`（`run.sh` 会自动下载 `gson-2.10.1.jar`）。
- 编译：`javac -cp gson-2.10.1.jar Main.java`；运行：`java -cp .:gson-2.10.1.jar Main <case_dir> <out_file>`（运行 `run.sh` 自动完成）。
- 功能：读取并解析 `<case_dir>/jobs.json`、`machines.json`、`constraints.json`，生成按机台初始化的 `schedule.json`。