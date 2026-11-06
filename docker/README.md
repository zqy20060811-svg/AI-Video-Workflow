# PostgreSQL Docker 环境（本机开发）

## 当前实例

| 项目 | 值 |
| --- | --- |
| 容器名称 | `ai-video-workflow-postgres` |
| 镜像 | `postgres:16`（官方镜像，本地已有） |
| 宿主机端口 | **5436**（5432/5433/5435 已被现有容器占用，5434 被已停止容器注册，故选择 5436） |
| 数据库名 | `ai_video_workflow` |
| 用户名 | `postgres` |
| 密码 | 见 `backend/.env`（不写入代码与文档） |
| 数据卷 | `ai-video-workflow-pgdata` |

## 常用命令

```bash
# 启动
docker start ai-video-workflow-postgres

# 停止
docker stop ai-video-workflow-postgres

# 状态
docker ps --filter name=ai-video-workflow-postgres

# 连接测试
docker exec ai-video-workflow-postgres pg_isready -U postgres
```

> 注意：本机已有其他 PostgreSQL / Redis 容器（5432、5433、5435、6380 等），本项目容器独立运行，请勿删除或修改它们。
