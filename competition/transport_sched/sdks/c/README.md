# C SDK 指南

 - JSON 解析库：使用 `cJSON`（入口脚本会自动下载到 `vendor/`）。
 - 运行：`./run.sh <case_dir> <out_file>`。
 - 重要：Codabench 执行容器不保证存在 `gcc`。请在提交包中包含已编译好的 Linux amd64 ELF 二进制 `predict`，`run.sh` 将优先运行该二进制；若检测到非 ELF 或缺失 `predict`，且容器内存在 `gcc`，才会尝试编译。
 - 产物：读取 `<case_dir>/machine.json`、`job.json`（`am.json` 可选），生成包含资源时间线的 `schedule.json`，与基线评分一致。

 构建建议：
 - 使用 Linux 环境生成 ELF：`gcc -O2 -pipe main.c vendor/cJSON.c -Ivendor -o predict`
 - 或使用交叉编译器：`x86_64-linux-gnu-gcc`/`musl-gcc`（推荐静态链接以提升兼容性）
