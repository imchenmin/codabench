# Codabench 多语言提交镜像

该 Dockerfile 基于 `ubuntu:22.04`，预装 C/C++、Java 与 Python 的常用工具链。

## 构建

```bash
docker build -t your-org/codabench-multilang:latest -f submission_images/multilang/Dockerfile submission_images/multilang
```

## 运行脚本

镜像随附 `/usr/local/bin/language_entry.sh`，可结合 `metadata.yaml` 中的 `command` 字段使用：

```yaml
command: bash -lc "language_entry.sh"
```

脚本会自动探测源码语言（或通过设置 `LANGUAGE` 环境变量显式指定）并完成编译执行，输出仍需写入 `/app/output`。根据需要也可以忽略该脚本，自行在提交包中提供 `run.sh`。
