# AI Video Workflow

AI 短视频 / 影视分镜生产工作流（Human-in-the-loop）。

**当前阶段：故事 → AI 分析 → AI 分镜 → 人工修改 → 确认分镜 → 生成场景图 → 确认图片 → 生成视频 → 确认视频（工作流代码已完整；图片/视频生成依赖外部引擎 ComfyUI，未配置时前端会给出引导）。**

尚未实现：多镜头批量出片、自动剪辑、剪映自动化等后续阶段。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy 2.0 / psycopg 3 / pydantic-settings |
| 数据库 | PostgreSQL 16（Docker 容器 `ai-video-workflow-postgres`，宿主机端口 **5436**） |
| 前端 | Vue 3 / Vite / TypeScript / Element Plus / Vue Router / Pinia / Axios |
| 存储 | 本地 `storage/` 目录（后续接 MinIO / OSS） |
| LLM | OpenAI 兼容 API（当前本地 Ollama `qwen2.5:3b`，可无缝切换 DeepSeek / OpenAI） |
| 图片/视频生成 | Provider 抽象（`none` / `comfyui`），业务代码不耦合具体模型，全部由 `.env` 决定 |
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
6. 在已确认的 Shot 卡片「生成与确认」区：生成场景图 → 查看大图 → 确认图片
7. 确认图片后：生成视频 → 播放器预览 → 确认视频（该 Shot 完成）
```

项目状态：draft → story_analyzing → storyboard_generated → storyboard_reviewing → storyboard_confirmed。
已确认的分镜再次修改会自动回到 storyboard_reviewing / draft 状态。

图片 / 视频必须人工确认：重新生成会保留旧文件（version 递增）；视频生成强制要求最新场景图已确认。

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
| GET | /api/shots/{shot_id}/assets | 镜头产物列表（场景图 / 视频） |
| POST | /api/shots/{shot_id}/images/generate | 生成场景图（调用 .env 配置的 ImageProvider） |
| POST | /api/shots/{shot_id}/images/upload | 上传外部工具生成的场景图（provider=manual） |
| POST | /api/shots/{shot_id}/images/confirm | 人工确认最新场景图 |
| POST | /api/shots/{shot_id}/videos/generate | 生成视频（I2V，要求最新场景图已确认） |
| POST | /api/shots/{shot_id}/videos/upload | 上传外部工具生成的视频（provider=manual） |
| POST | /api/shots/{shot_id}/videos/confirm | 人工确认最新视频 |
| GET | /api/system/config | 当前模型配置 |
| GET | /api/system/check-env | 本地生成环境检查（GPU / 显存 / PyTorch / ComfyUI / 模型就绪） |

角色图片保存至 `storage/projects/{project_id}/characters/`，场景图 `.../shots/{shot_id}/images/`，视频 `.../shots/{shot_id}/videos/`，数据库仅存相对路径；产物同时通过 `/storage/` 静态目录访问。

## LLM 配置

`backend/.env`：

```env
LLM_API_KEY=你的密钥
LLM_BASE_URL=https://api.deepseek.com/v1   # 或 OpenAI / Ollama 等兼容地址
LLM_MODEL=deepseek-chat
```

当前默认使用本机 Ollama（`http://localhost:11434/v1` + `qwen2.5:3b`）做开发测试。
更换模型只需改这三个环境变量，业务代码不变。

## 零成本出片（当前默认路径：外部工具 + 人工回传）

本机未安装 ComfyUI 且显存只有 6GB，本地跑 LTX-Video 属超配运行。当前采用零成本人工闭环：

```text
分镜确认后 → 复制图片 Prompt → 外部图片工具生成场景图 → 下载 → 「上传场景图」→ 确认图片
           → 复制视频 Prompt → 外部视频工具（免费额度）图生视频 → 下载 mp4 → 「上传视频」→ 播放确认
```

- 上传的图片/视频走与 API 生成完全相同的 Asset 版本机制（provider=manual），保存到
  `storage/projects/{pid}/shots/{sid}/images|videos/`，旧版本保留
- 支持 png/jpg/jpeg/webp 与 mp4/webm/mov
- 免费/免费额度工具举例：即梦、可灵、海螺等（任选，注意每日免费额度）
- 以后装好 ComfyUI 后，`.env` 切换 Provider 即可回到全自动路径，前端流程不变

## 图片 / 视频生成（ComfyUI 本地方案）

模型选择完全由 `.env` 决定，业务代码通过 Provider 工厂获取实现，不耦合任何具体模型：

```env
IMAGE_PROVIDER=comfyui          # none = 未配置（前端给出引导）
IMAGE_MODEL=sd15.safetensors    # ComfyUI models/checkpoints/ 中的文件名
VIDEO_PROVIDER=comfyui
VIDEO_MODEL=ltxv-2b-0.9.6-distilled-fp8.safetensors   # ComfyUI models/unet/
VIDEO_CLIP_MODEL=t5xxl_fp16.safetensors               # ComfyUI models/clip/
VIDEO_VAE_MODEL=ltxv_vae_bf16.safetensors             # ComfyUI models/vae/
VIDEO_FPS=24
COMFYUI_URL=http://127.0.0.1:8188
```

### ComfyUI 连接方式

1. 安装并启动 ComfyUI（ portable 版或 `python main.py`），默认监听 `http://127.0.0.1:8188`
2. 本项目把「workflow API JSON 模板 + 占位符」提交到 ComfyUI `POST /prompt`，轮询 `/history`，经 `/view` 取回文件
3. 模板位于 `backend/app/services/comfyui_workflows/`：
   - `image_workflow.json`：默认 SD1.5 文生图（占位符 `__PROMPT__` `__WIDTH__` `__HEIGHT__` `__SEED__` `__MODEL__` 等）
   - `video_workflow.json`：默认 LTX-Video I2V（占位符 `__IMAGE__` `__UNET__` `__CLIP__` `__VAE__` `__FRAMES__` 等，需 ComfyUI 0.3.10+ 原生 CreateVideo/SaveVideo 节点）
4. 想用别的工作流：在 ComfyUI 中开启开发者模式 → 导出 API 格式 JSON → 覆盖对应模板文件，把需要动态替换的值写成占位符即可
5. 可在「模型设置」页点击「检查本地生成环境」验证 GPU / 显存 / ComfyUI 连通性 / 模型是否在已装列表中

### 零成本方案与硬件要求（如实说明）

| 环节 | 推荐方案 | 显存要求 |
| --- | --- | --- |
| LLM | Ollama qwen2.5:3b（已就绪） | ~3 GB |
| 图片 | ComfyUI + SD1.5（512~768 分辨率） | ~3-4 GB，可行 |
| 视频 | ComfyUI + LTX-Video 2B distilled（fp8 + offload） | 官方建议 8GB+；6GB 显存仅能出低分辨率/短时长，勉强可用 |

> 本机为 RTX 4050 Laptop（6GB 显存）：图片生成可用；LTX-Video 视频生成属于超配运行，
> 速度慢且可能 OOM。若无法运行，可选：A. 更轻量本地方案；B. 第三方免费额度 API；
> C. 付费 API。不会默认绑定任何付费服务。

### 未配置时的行为

`IMAGE_PROVIDER` / `VIDEO_PROVIDER` 为 `none` 时，点击生成按钮会收到明确的引导提示
（安装 ComfyUI 或配置 API），不会假装生成成功。

## PostgreSQL 容器操作

```bash
docker start ai-video-workflow-postgres   # 启动
docker stop ai-video-workflow-postgres    # 停止
docker ps --filter name=ai-video-workflow-postgres
```

详见 [docker/README.md](docker/README.md)。

## 后续阶段（未实现）

多个 Shot 批量生成 → 按镜头编号整理素材 → 导出剪映。
