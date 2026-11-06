# AI Video Workflow

AI 短视频 / 影视分镜生产工作流（Human-in-the-loop）。

**当前阶段：项目初始化 + 基础工程骨架。** 仅包含前后端基础框架、数据库连接与基础 CRUD，未接入任何真实 AI 模型。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy 2.0 / psycopg 3 / pydantic-settings |
| 数据库 | PostgreSQL 16（Docker 容器 `ai-video-workflow-postgres`，宿主机端口 **5436**） |
| 前端 | Vue 3 / Vite / TypeScript / Element Plus / Vue Router / Pinia / Axios |
| 存储 | 本地 `storage/` 目录（后续接 MinIO / OSS） |
| 预留 | LangGraph（仅目录与依赖）、Redis（仅配置） |

## 目录结构

```
AI-Video-Workflow/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 应用入口（/api/health、CORS、启动建表）
│   │   ├── api/routes/     # projects / characters / shots 路由
│   │   ├── core/           # config（pydantic-settings）、database（Engine/Session/Base）
│   │   ├── models/         # Project / Character / Shot / Asset ORM 模型
│   │   ├── schemas/        # Pydantic 请求/响应模型
│   │   ├── services/       # storage_service（本地上传存储）
│   │   ├── workflow/       # LangGraph 占位（state.py + nodes/）
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── .env / .env.example
├── frontend/               # Vue 3 前端
│   └── src/
│       ├── api/            # axios 客户端与接口封装
│       ├── router/         # /  /projects/new  /projects/:id
│       ├── stores/         # Pinia（预留）
│       └── views/          # HomeView / ProjectCreateView / ProjectDetailView
├── storage/                # 本地文件存储（projects/ temp/）
├── docker/README.md        # PostgreSQL 容器说明
└── README.md
```

## 环境说明

- PostgreSQL：Docker 容器 `ai-video-workflow-postgres`，官方 `postgres:16` 镜像，宿主机端口 **5436**
  （5432/5433/5435 已被本机其他容器占用，5434 已被已停止容器注册，故选 5436），数据库名 `ai_video_workflow`。
  密码配置在 `backend/.env`，不出现在代码中。
- 前端端口 **5180**（本机 5173 已被其他应用占用）。
- Redis：本阶段仅保留 `REDIS_URL` 配置，未启动服务、未实现队列。

## 启动

### 后端

```bash
cd backend
# 首次：python -m venv .venv; .venv\Scripts\pip install -r requirements.txt
# 确保 PostgreSQL 容器已启动（docker start ai-video-workflow-postgres）
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

启动时自动 `Base.metadata.create_all` 建表（第一阶段不使用 Alembic）。

### 前端

```bash
cd frontend
# 首次：npm install
npm run dev
```

访问 http://localhost:5180

## 常用地址

| 地址 | 说明 |
| --- | --- |
| http://localhost:8000/api/health | 健康检查 |
| http://localhost:8000/api/docs | Swagger 文档 |
| http://localhost:5180 | 前端首页 |

## 当前可用 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/health | 健康检查 |
| POST | /api/projects | 创建项目（name / story / aspect_ratio） |
| GET | /api/projects | 项目列表 |
| GET | /api/projects/{id} | 项目详情（含角色、镜头、镜头数量） |
| POST | /api/projects/{id}/characters | 创建角色，multipart 上传 front_image / side_image / back_image（Form 字段：name、description） |
| GET | /api/projects/{id}/characters | 角色列表 |
| GET | /api/projects/{id}/shots | 镜头列表（占位，暂无数据） |

角色图片保存至 `storage/projects/{project_id}/characters/`，数据库仅存相对路径。

## PostgreSQL 容器操作

```bash
docker start ai-video-workflow-postgres   # 启动
docker stop ai-video-workflow-postgres    # 停止
docker ps --filter name=ai-video-workflow-postgres
```

详见 [docker/README.md](docker/README.md)。

## 后续阶段（未实现）

剧情优化与分镜生成（LangGraph）→ 图片 Prompt 生成 → 图片生成 → 视频生成 → 素材整理导出剪映。
AI 模型调用统一放入 services 层，届时接入。
