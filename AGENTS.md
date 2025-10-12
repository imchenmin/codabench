# Repository Guidelines

## 项目结构与模块组织
Codabench 的 Django 后端位于 `src/`，可复用 app 放在 `src/apps/`，环境配置集中在 `src/settings/`。模板和静态资源分别在 `src/templates/` 与 `src/static/`，编译产物写入 `src/static/generated/`。跨项目工具与 Celery 配置在 `src/utils/`、`src/celery_config.py`，消息路由由 `src/routing.py` 管理。异步执行器位于 `compute_worker/`，Dockerfile、`Procfile` 与证书等部署文件保留在仓库根目录。各 app 自带测试，同时在 `src/tests/` 汇总集成场景。补充文档与演示材料集中在 `docs/` 与 `documentation/`，自定义运维脚本位于 `bin/` 及 `fabfile.py`，而 `maintenance_mode/` 提供维护窗口模板。

## 构建、测试与开发命令
首次运行 `poetry install` 安装 Python 依赖；若使用 Node 资产，请执行 `npm install`。使用 `docker compose up -d` 启动默认服务，随后执行 `docker compose exec django python manage.py migrate` 与 `docker compose exec django python manage.py collectstatic --noinput` 同步数据库与静态资源。本地静态检查用 `poetry run flake8 src`。前端资源由 `npm run build-stylus` 编译 Stylus，`npm run build-riot` 打包 Riot 组件，必要时通过 `npm run concat-riot` 合并标签。调试 Django 任务可以 `poetry run python manage.py shell_plus`，或使用 `poetry run celery -A src.celery_config worker` 检查队列行为。

## 代码风格与命名约定
Python 代码采用四空格缩进，函数使用 snake_case，类使用 PascalCase。`setup.cfg` 中的 flake8 规则强制单引号与导入顺序，请在提交前运行 `poetry run flake8`。当需要自定义管理命令时，将其放入对应 app 的 `management/commands/`。优先使用 Django `reverse` 生成 URL，将通用工具保存在所属 app 的 `utils.py`，仅在跨项目复用时提升至 `src/utils/`。`src/static/riot/` 中的标签文件维持 kebab-case 文件名，Stylus 变量与 mixin 使用连字符描述语义。

## 测试准则
项目使用 pytest，默认加载 `settings.test` 并复用测试数据库。执行 `poetry run pytest` 触发全部测试，或在容器内运行 `docker compose exec django pytest`。测试文件命名 `test_<feature>.py`，夹具采用具象的 snake_case，并将共享夹具放入 `conftest.py`。修复缺陷时补充回归用例，覆盖序列化器、服务层、Celery 任务与权限校验。浏览器流程可调用 `./run_selenium_tests.sh`，数据工厂保存在 `src/factories.py`，更新模型字段时务必同步调整。若引入新端点，请提供最少一个 API 测试与对应 schema 断言。

## 提交与拉取请求指引
提交信息使用祈使句单行摘要，例如 `add dataset size validator`、`fix flake8 warnings`，必要时附 `refs #123`。保持一次提交对应一个逻辑修改，长流程可拆分为“准备”“实现”“清理”三类。PR 描述需说明问题背景、解决方案与风险，列出迁移脚本或数据脚本。界面变更需附前后对比截图，新环境变量写入描述并更新样例配置。确认 CircleCI 状态通过，并在本地完成 `poetry run pytest` 与关键端到端场景后再请求审查。

## 环境与安全提示
复制 `.env_sample` 为 `.env` 管理本地密钥，避免将真实凭证写入仓库。`server_config_sample.yaml` 提供服务端示例配置，生产机密交由秘密管理工具或平台变量托管。使用 `reset_db.sh` 安全刷新数据，若需要临时停机，可启用 `maintenance_mode/` 中的模板。不要提交 `certs/`、`runtime.txt`、`version.json` 等生成文件的私有变更，涉及敏感权限时请通过运维渠道处理。

## 沟通与总结要求
在评审、讨论、更新日志以及本指引涉及的所有总结中，请始终使用中文进行回复与概述，确保团队沟通保持一致。提交 PR、评论缺陷或发布部署说明时也请遵循中文表达，以减少信息歧义并方便归档。

## 代理操作记录
所有代理需在每次执行命令或修改文件后，将对应操作以单行描述追加到 `RECORD.md`，确保日志完整可追溯。
