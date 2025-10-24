# 在 amd64 Ubuntu 上构建与部署 Codabench

本文档说明如何在 amd64 架构的 Ubuntu 上构建可部署的 Docker 镜像并启动整套服务。

## 前置条件
- 已安装 Docker 与 Docker Compose v2（`docker compose version` 可用）
- 克隆本仓库并切换到 `develop` 分支
- 准备 `.env`：`cp .env_sample .env` 并按实际环境修改数据库、RabbitMQ、MinIO 等变量

## 构建镜像（amd64）

可使用 Makefile 简化：

```
make build-all                  # 构建 codabench-web 与 compute-worker
# 或分别构建：
make build-web
make build-worker
```

等价的原始命令：

```
docker build --platform linux/amd64 -f Dockerfile.web -t codabench-web:latest .
docker build --platform linux/amd64 -f Dockerfile.compute_worker -t codabench-compute-worker:latest .
```

说明：
- `Dockerfile.web` 会安装 Python 依赖、构建前端（Stylus/Riot），并在启动时自动执行迁移与 collectstatic。
- `Dockerfile.compute_worker` 已固定 `linux/amd64` 平台，用于执行评测作业（需要宿主机 Docker Socket）。

## 启动服务

```
docker compose -f docker-compose.prod.yml up -d
```

包含服务：
- `django`：ASGI + Gunicorn（暴露 8000）
- `caddy`：反向代理与静态资源（80/443），与 `django` 共享命名卷 `staticfiles`
- `db`、`rabbit`、`redis`、`minio`、`createbuckets`、`flower`、`site_worker`、`compute_worker`

首启后可执行：

```
docker compose -f docker-compose.prod.yml exec django python manage.py createsuperuser
```

## 生产优化
- 若使用外部对象存储，建议在 `docker-compose.override.yml` 禁用 `minio` 与 `createbuckets`（参考 `codabench.wiki` 文档）。
- 如仅使用外部计算资源，可在 override 中禁用 `compute_worker`。
- 如需 HTTPS，请在 `Caddyfile` 配置域名与证书（默认已挂载 `./Caddyfile`）。

## 常用命令

```
make up                 # 以 prod 编排启动
make down               # 停止并清理卷
make logs               # 跟随日志
```

## 故障排查
- `django` 容器启动失败：检查数据库连通性与 `.env` 的 `DATABASE_URL`/`DB_*` 配置
- 静态资源 404：确认 `django` 中的 `collectstatic` 已执行且命名卷 `staticfiles` 已挂载给 `caddy`
- 提交执行失败：检查 `rabbit`、`compute_worker` 日志以及宿主机的 `/var/run/docker.sock` 挂载权限

