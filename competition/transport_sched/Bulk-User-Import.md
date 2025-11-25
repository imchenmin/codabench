# 批量添加用户到比赛指南

## 概述
- 通过 CSV 批量创建用户，并将其加入指定比赛/基准。
- 推荐使用 `make import-users`；也可直接使用 `manage.py import_users_to_competition`。

## CSV 格式
- 最少两列：`username,password`
- 可选列：`email,is_active`
- 支持标题行，列名自动识别：`username,password,email,is_active`
- 示例：

```
username,password,email,is_active
alice,Passw0rd!,alice@example.com,true
bob,S3curePwd,,false
```

## 快速开始
- 通过比赛 ID 导入：

```
make import-users CSV=/path/users.csv OPTS="--competition-id 123 --status approved"
```

- 通过比赛密钥导入：

```
make import-users CSV=/path/users.csv OPTS="--competition-secret-key <uuid> --status approved"
```

- 干跑预览（不落库）：

```
make import-users CSV=/path/users.csv OPTS="--competition-id 123 --dry-run"
```

## 命令参数
- `--competition-id <id>`：通过比赛 ID 指定目标比赛。
- `--competition-secret-key <uuid>`：通过比赛密钥指定目标比赛（`src/apps/competitions/models.py:47`）。
- `--status {unknown,denied,approved,pending}`：参赛者状态（默认 `approved`）。
- `--reset-password`：重置已存在用户的密码为 CSV 值。
- `--require-email`：强制每行必须提供邮箱。
- `--update-email`：更新已存在用户的邮箱为 CSV 值。
- `--inactive`：新建用户默认设置为未激活。
- `--set-active-existing`：将已存在用户批量设置为激活。
- `--set-inactive-existing`：将已存在用户批量设置为未激活。
- `--dry-run`：仅解析与统计，不写入数据库。

## 行为说明
- 新用户：
  - 默认 `is_active=True`；若传 `--inactive` 或 CSV `is_active=false` 则未激活。
  - 若 CSV 提供 `email` 则写入；未开启 `--require-email` 时允许缺失。
- 已存在用户：
  - 可通过 `--reset-password` 重置密码。
  - 可通过 `--update-email` 更新邮箱（仅当 CSV 提供且不同）。
  - 激活状态可由 CSV 的 `is_active` 或通过 `--set-active-existing/--set-inactive-existing` 批量调整。
- 参赛者记录：
  - 为每个用户创建 `CompetitionParticipant`；重复加入同一比赛会计为“已存在”。

## 故障排查
- 只读临时目录错误（`/codalab_tmp`）：
  - 直接使用 `make import-users`（已自动设置可写临时目录），或运行时设置：

```
TEMP_SUBMISSION_STORAGE=/path/.tmp ./manage.py import_users_to_competition /path/users.csv --competition-id 123
```

- 重复参赛者（唯一约束）：
  - 命令会统计为 `participants_existing`，不影响执行。

- 不合法 CSV 行：
  - 缺少必要列或空值会被跳过；启用 `--require-email` 时缺邮箱的行会被跳过。

## 安全建议
- 首次导入建议使用 `--dry-run` 验证统计结果。
- 确保密码强度；避免将 CSV 存入版本库。

## 相关代码与入口
- 管理命令：`src/apps/commands/management/commands/import_users_to_competition.py`
- 参赛者模型与唯一约束：`src/apps/competitions/models.py:812`、`src/apps/competitions/models.py:831`
- 比赛密钥字段：`src/apps/competitions/models.py:47`
- 用户邮箱可为空：`src/apps/profiles/models.py:68`
- Make 入口：`Makefile:58`
