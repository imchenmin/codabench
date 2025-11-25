# 参赛指南（传输调度 benchmark）

## 输入输出规范
- 输入目录：`/input/cases/<case_id>/`
  - `jobs.json`
  - `machines.json`
  - `constraints.json`
- 输出文件：`schedule.json`

## SDK格式要求
 - Python（3.10）：入口 `run.sh <case_dir> <out_file>`（或 `run.py --input <case_dir> --output <out_file>`）。
- Java（JDK 17）：入口 `run.sh` 编译并运行 `Main.java`。
- C（gcc）：入口 `run.sh` 编译并运行 `predict`；建议 `-O2 -pipe`。
- C++（C++17）：入口 `run.sh` 编译并运行 `predict`。
- 参赛包需包含：入口（脚本/可执行）、依赖说明、运行文档。

## 运行环境与限制
- 自动解压至 `PROGRAM_DIR`；ingestion 环境变量：
  - `TIMEOUT_SECONDS`（默认 300）
  - `MEMORY_LIMIT_MB`（默认 2048，POSIX 下以 RLIMIT 方式限制）

## 判题容器环境
- Python：`3.10.x`（摄取与评分程序运行环境）。
- C 工具链：`gcc 11.x`，支持 `-std=c11`；推荐编译参数：`-O2 -pipe`。
- C++ 工具链：`g++ 11.x`，支持 `-std=c++17`；推荐编译参数：`-O2 -pipe -std=c++17`。
- Java：`OpenJDK 17.x`（`javac`/`java`）。
- Make：提供 `make`（如需统一构建，可在 `run.sh` 中调用）。
- 版本查询示例（容器内）：
  - `python3 --version`
  - `gcc --version`、`g++ --version`
  - `javac -version`、`java -version`

## 常见问题
- 报错“未找到可执行入口”：确保提供 `run.sh/run.py/main.py/predict.py::predict`。
- 报告为空或 invalid：检查 `machines` 字段与 `timeline` 时间片是否正确。

## 提交操作指南（详细）
- 准备数据与本地环境：
  - 克隆或下载比赛仓库，确认示例用例位于 `competition/transport_sched/datasets/public/cases/`。
  - 本地调试时，程序需对每个 `<case_dir>` 读取 `jobs.json`、`machines.json`、`constraints.json` 并输出 `schedule.json`。
- 编写程序入口：
  - 平台摄取程序会优先调用 `run.sh`，其次是 `run.py`、`main.py`，或 `predict.py::predict`（入口解析逻辑见 `competition/transport_sched/ingestion_program/run.py:93`）。
  - 你的入口需遵循调用约定：
    - `run.sh <case_dir> <out_file>`
    - `run.py --input <case_dir> --output <out_file>`
    - `main.py --input <case_dir> --output <out_file>`
    - `predict.py::predict(case_dir, out_file)`
- 语言与库建议：
  - Python：标准库 `json` 即可；示例参考 `competition/transport_sched/sdks/python/run.py:12`。
  - C++：推荐 `nlohmann/json` 单头文件；示例参考 `competition/transport_sched/sdks/cpp/main.cpp:17`。
  - C：推荐 `cJSON`；示例参考 `competition/transport_sched/sdks/c/main.c:35`。
  - Java：推荐 `Gson`；示例参考 `competition/transport_sched/sdks/java/Main.java:16`。
- 本地快速验证：
  - Python：`python3 your/run.py --input competition/transport_sched/datasets/public/cases/case_01 --output out/schedule.json`
  - C++：`bash your/run.sh competition/transport_sched/datasets/public/cases/case_01 out/schedule.json`
  - C：`bash your/run.sh competition/transport_sched/datasets/public/cases/case_01 out/schedule.json`
  - Java：`bash your/run.sh competition/transport_sched/datasets/public/cases/case_01 out/schedule.json`
  - 如需统一使用 `make`，可在 `run.sh` 内封装：`make build && make run CASE_DIR=<case_dir> OUT_FILE=<out_file>`。
- 打包与提交：
  - 将程序入口文件与代码、依赖说明打包为 ZIP（不需要 `metadata.yaml`，平台已有摄取配置）。
  - ZIP 内容放置于提交根目录，入口文件位于根目录（例如 `run.sh` 与源文件）。
  - 在线提交后，平台在容器中展开至 `/app/ingested_program` 或 `/app/program`，摄取程序会按入口规则对每个用例调用你的程序并收集 `schedule.json`（目录与索引写入逻辑见 `competition/transport_sched/ingestion_program/run.py:188`、`competition/transport_sched/ingestion_program/run.py:226`）。
  - 评分端读取聚合预测并计算得分与报告（见 `competition/transport_sched/scoring_program/score.py:62`、`competition/transport_sched/scoring_program/score.py:200`）。
- 资源与限制：
  - 摄取阶段默认超时 `TIMEOUT_SECONDS=300`，内存限制 `MEMORY_LIMIT_MB=2048`，可用于估计算法复杂度（见 `competition/transport_sched/ingestion_program/run.py:48`）。
  - 容器目录布局与共享目录参见 Codabench 文档与摄取程序中索引与聚合逻辑（见 `competition/transport_sched/ingestion_program/run.py:226`）。

## 常见错误排查（补充）
- 入口未被识别：确保提供 `run.sh` 或 `run.py/main.py/predict.py::predict`，并位于提交 ZIP 根目录（报错出处见 `competition/transport_sched/ingestion_program/run.py:103`）。
- 未生成 `schedule.json`：检查输出路径是否正确传入；摄取会复制到共享目录但依赖你的程序先生成（见 `competition/transport_sched/ingestion_program/run.py:204`）。
- JSON 结构错误：`machines` 缺失或字段类型错误将导致 `valid=false`，并给出详细消息（见 `competition/transport_sched/scoring_program/score.py:127`）。
- 时间片重叠或负时长：对应错误消息含机台与时间位置，便于定位（见 `competition/transport_sched/scoring_program/score.py:145`）。