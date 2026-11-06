# AI Video Workflow

AI 短视频 / 影视分镜生产工作流（Human-in-the-loop）。

**当前阶段：故事 → AI 分析 → AI 分镜 → 人工修改 → 确认分镜（完整闭环已实现）。**
尚未实现：图片生成、视频生成、剪映自动化等后续阶段。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy 2.0 / psycopg 3 / pydantic-settings |
| 数据库 | PostgreSQL 16（Docker 容器 `ai-video-workflow-postgres`，宿主机端口 **5436**） |
| 前端 | Vue 3 / Vite / TypeScript / Element Plus / Vue Router / Pinia / Axios |
| 存储 | 本地 `storage/` 目录（后续接 MinIO / OSS） |
| LLM | OpenAI 兼容 API（当前本地 Ollama `qwen2.5:3b`，可无缝切换 DeepSeek / OpenAI） |
| 工作流 | LangGraph：story_analysis → storyboard_generation → human_review（人工确认） |

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

## 完整工作流使用步骤

```text
1. 新建项目（/projects/new）
2. 项目详情页上传角色三视图、填写故事梗概 → 保存故事
3. 点击「生成分镜」→ AI 分析故事 + 生成分镜（等待 1-3 分钟）
4. 自动跳转分镜管理页 → 查看/修改/新增/删除/排序分镜
5. 点击「确认全部分镜」
```

项目状态：draft → story_analyzing → storyboard_generated → storyboard_reviewing → storyboard_confirmed。
已确认的分镜再次修改会自动回到 storyboard_reviewing / draft 状态。

## 当前可用 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/health | 健康检查 |
| POST | /api/projects | 创建项目（name / story / aspect_ratio） |
| GET | /api/projects | 项目列表 |
| GET | /api/projects/{id} | 项目详情（含角色、镜头、故事分析） |
| PUT | /api/projects/{id} | 编辑项目（故事梗概 / 名称 / 画幅） |
| POST | /api/projects/{id}/characters | 创建角色，multipart 上传 front_image / side_image / back_image（Form 字段：name、description） |
| GET | /api/projects/{id}/characters | 角色列表 |
| POST | /api/projects/{id}/storyboard/story/analyze | AI 故事结构化分析 |
| POST | /api/projects/{id}/storyboard/generate | AI 生成分镜（LangGraph：分析 → 分镜 → 入库） |
| POST | /api/projects/{id}/storyboard/confirm | 确认全部分镜 |
| GET/POST | /api/projects/{id}/shots | 镜头列表 / 手动新增镜头 |
| GET/PUT/DELETE | /api/shots/{shot_id} | 单个镜头查询 / 修改（含调整顺序）/ 删除 |
| POST | /api/projects/{id}/shots/reorder | 批量调整镜头顺序 |

角色图片保存至 `storage/projects/{project_id}/characters/`，数据库仅存相对路径。

## LLM 配置

`backend/.env`：

```env
LLM_API_KEY=你的密钥
LLM_BASE_URL=https://api.deepseek.com/v1   # 或 OpenAI / Ollama 等兼容地址
LLM_MODEL=deepseek-chat
```

当前默认使用本机 Ollama（`http://localhost:11434/v1` + `qwen2.5:3b`）做开发测试。
更换模型只需改这三个环境变量，业务代码不变。

## PostgreSQL 容器操作

```bash
docker start ai-video-workflow-postgres   # 启动
docker stop ai-video-workflow-postgres    # 停止
docker ps --filter name=ai-video-workflow-postgres
```

详见 [docker/README.md](docker/README.md)。

## 后续阶段（未实现）

图片 Prompt 优化 → 图片生成 → 用户审核 → 视频生成 → 素材整理导出剪映。
AI 模型调用统一放在 services 层，届时接入。
