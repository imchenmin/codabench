# 多语言提交模板

`*.zip` 文件可直接作为 Codabench 代码提交示例，覆盖 C、C++、Java、Python 四种语言。

- 解压后包含 `metadata.yaml` 以及对应的源码与 `run.sh`（Python 模板无需 `run.sh`）。
- `run.sh` 负责在 `/app/program` 中编译源码、并将结果写入 `/app/output/results.txt`。
- 如需集成多文件或更复杂逻辑，可在模板基础上扩展，同时保持输出目录不变。

模板目录中保留了未压缩的原始文件，便于根据自身需求修改后重新 `zip`：

```bash
# 重新打包 C++ 模板示例
cd templates/submissions/cpp
zip -r ../cpp_template.zip metadata.yaml run.sh src
```
