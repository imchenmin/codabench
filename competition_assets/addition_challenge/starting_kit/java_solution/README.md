# Java 基线解题包

该示例演示如何读取公开数据 `inputs.csv`，计算加法结果并生成 `predictions.csv`。竞赛为**程序提交**模式，平台会自动调用参赛者提供的 `build.sh`。

## 使用方式

```bash
./build.sh
```

执行后将在 `output/predictions.csv` 中生成提交文件。

## 提交规范

- 提交压缩包需包含 `build.sh`、源码目录（例如 `src/`）以及所需资源。
- 平台会执行 `bash build.sh <输入路径> <输出路径>`，同样可以通过环境变量 `INPUT_CSV` 与 `OUTPUT_CSV` 读取路径。
- 脚本应当在给定输出路径处生成带表头 `id,sum` 的 `predictions.csv`。
- 请勿假设工作目录，可使用传入的绝对路径进行读写。
