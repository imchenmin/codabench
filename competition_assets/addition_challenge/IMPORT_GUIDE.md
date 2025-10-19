# 简单加法挑战导入指南

## 1. 准备工作

- 确保已在 Codabench 拥有组织者权限。
- 下载竞赛包：`competition_assets/addition_challenge_bundle.zip`。

## 2. 导入竞赛

1. 登录 Codabench 后，进入 **My Competitions** 页面。
2. 点击 **Create Competition** → 选择 **Upload Bundle**。
3. 上传 `competition_assets/addition_challenge_bundle.zip`，等待平台解析完成。
4. 导入成功后，可在编辑器中查看并调整如下信息：
   - 基本信息（标题、描述、封面图）。
   - 阶段设置、提交限制等。
   - 确认评分程序与数据集均已列出。
5. 发布前可先在“私有”模式下进行测试提交。

## 3. 提交格式

- 参赛者需上传一个 zip 文件，内部包含 `predictions.csv`。
- `predictions.csv` 必须包含表头 `id,sum`，数据顺序与 `public_data/inputs.csv` 对齐。

## 4. Java 基线解题包

- 竞赛包中 `starting_kit/java_solution.zip` 即为官方 Java 基线。
- 使用方法：
  1. 解压后执行 `build.sh`（需要本地安装 Java 17+）。
  2. 程序会读取 `data/inputs.csv`，输出 `output/predictions.csv`。
  3. 将 `predictions.csv` 压缩为 zip 文件上传至 Codabench。

## 5. 本地测试评分程序（可选）

如需在本地验证评分脚本，可在 Docker 环境中模拟 Codabench 评分容器，将预测结果放入 `/app/output/res/predictions.csv`（平台会在评分阶段自动镜像至 `/app/input/res/`），参考脚本运行 `python3 scoring_program/scoring.py` 校验。
