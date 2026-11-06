"""ComfyUI Provider：把工作流模板提交到本地 ComfyUI，等待完成并取回文件。

我们的项目不自己实现 Diffusion / 推理，只负责：
prompt → workflow JSON（模板 + 占位符替换）→ 提交 ComfyUI → 轮询 → 下载文件。

workflow 模板放在 app/services/comfyui_workflows/*.json，
占位符（如 "__PROMPT__"、"__WIDTH__"）在提交前替换为实际值。
用户可以用 ComfyUI 导出自己的 workflow API JSON 替换模板。
"""

import json
import random
import time
import uuid
from pathlib import Path

import httpx

from app.core.config import settings
from app.services.providers.base import (
    BaseImageProvider,
    BaseVideoProvider,
    ImageRequest,
    ProviderError,
    VideoRequest,
)

WORKFLOW_DIR = Path(__file__).resolve().parent.parent / "comfyui_workflows"

# 视频帧数：LTX 系列要求帧数为 8k+1
VIDEO_FPS = settings.VIDEO_FPS


def _frames_for_duration(duration: float) -> int:
    raw = max(1, round(duration * VIDEO_FPS))
    return (raw // 8) * 8 + 1


def _load_template(name: str) -> dict:
    path = WORKFLOW_DIR / name
    if not path.exists():
        raise ProviderError(f"ComfyUI workflow 模板不存在：{name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ProviderError(f"workflow 模板 {name} 不是合法 JSON：{e}") from e


def _apply_placeholders(node: object, mapping: dict[str, str]) -> object:
    """递归把模板中形如 "__KEY__" 的字符串值替换为 mapping 中的值。"""
    if isinstance(node, dict):
        return {k: _apply_placeholders(v, mapping) for k, v in node.items()}
    if isinstance(node, list):
        return [_apply_placeholders(v, mapping) for v in node]
    if isinstance(node, str) and node.startswith("__") and node.endswith("__"):
        key = node[2:-2]
        if key in mapping:
            return mapping[key]
        raise ProviderError(f"workflow 模板中的占位符 {node} 没有对应的配置值，请在 .env 中补充或修改模板")
    return node


class ComfyUIClient:
    """ComfyUI HTTP 客户端：提交任务、轮询历史、下载/上传文件。"""

    def __init__(self) -> None:
        self.base_url = settings.COMFYUI_URL.rstrip("/")
        self.client_id = uuid.uuid4().hex

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            resp = httpx.request(method, f"{self.base_url}{path}", timeout=30.0, **kwargs)
        except httpx.HTTPError as e:
            raise ProviderError(
                f"无法连接 ComfyUI（{self.base_url}）：{e}\n"
                "请确认 ComfyUI 已启动，且 .env 中 COMFYUI_URL 配置正确。"
            ) from e
        if resp.status_code >= 400:
            raise ProviderError(f"ComfyUI 返回错误（HTTP {resp.status_code}）：{resp.text[:300]}")
        return resp

    def upload_image(self, data: bytes, filename: str) -> str:
        """上传参考图到 ComfyUI，返回服务器端的文件名（供 LoadImage 使用）。"""
        resp = self._request(
            "POST",
            "/upload/image",
            files={"image": (filename, data)},
            data={"overwrite": "true"},
        )
        body = resp.json()
        name = body.get("name")
        if not name:
            raise ProviderError(f"ComfyUI 上传图片失败：{body}")
        subfolder = body.get("subfolder", "")
        return f"{subfolder}/{name}" if subfolder else name

    def submit_workflow(self, workflow: dict) -> str:
        resp = self._request("POST", "/prompt", json={"prompt": workflow, "client_id": self.client_id})
        body = resp.json()
        prompt_id = body.get("prompt_id")
        if not prompt_id:
            raise ProviderError(f"ComfyUI 提交工作流失败：{body}")
        return prompt_id

    def wait_for_outputs(self, prompt_id: str) -> dict:
        """轮询 /history 直到任务完成，返回 outputs 字典。"""
        deadline = time.monotonic() + settings.GEN_TIMEOUT
        while time.monotonic() < deadline:
            resp = self._request("GET", f"/history/{prompt_id}")
            history = resp.json().get(prompt_id)
            if history:
                status = history.get("status", {})
                if status.get("status_str") == "error":
                    messages = status.get("messages", [])
                    raise ProviderError(f"ComfyUI 任务执行失败：{messages[-1] if messages else '未知错误'}")
                outputs = history.get("outputs")
                if outputs:
                    return outputs
            time.sleep(settings.GEN_POLL_INTERVAL)
        raise ProviderError(
            f"ComfyUI 任务超时（超过 {int(settings.GEN_TIMEOUT)} 秒）。"
            "可能是模型过大导致生成过慢，请检查 ComfyUI 控制台日志。"
        )

    def download_file(self, file_info: dict) -> bytes:
        params = {
            "filename": file_info.get("filename"),
            "subfolder": file_info.get("subfolder", ""),
            "type": file_info.get("type", "output"),
        }
        return self._request("GET", "/view", params=params).content

    @staticmethod
    def pick_output(outputs: dict, extensions: tuple[str, ...]) -> dict:
        """从 history outputs 中找出第一个匹配扩展名的输出文件。"""
        for node_outputs in outputs.values():
            for key in ("images", "videos", "gifs", "files"):
                for item in node_outputs.get(key, []) or []:
                    filename = item.get("filename", "")
                    if filename.lower().endswith(extensions):
                        return item
        raise ProviderError(f"ComfyUI 输出中没有匹配的文件（期望扩展名：{extensions}）")


class ComfyUIImageProvider(BaseImageProvider):
    name = "comfyui"
    model = settings.IMAGE_MODEL

    def generate_image(self, request: ImageRequest) -> bytes:
        workflow = _load_template("image_workflow.json")
        mapping = {
            "PROMPT": request.prompt,
            "NEGATIVE_PROMPT": request.negative_prompt,
            "WIDTH": str(request.width),
            "HEIGHT": str(request.height),
            "SEED": str(random.randint(0, 2**32 - 1)),
            "MODEL": settings.IMAGE_MODEL,
        }
        client = ComfyUIClient()
        prompt_id = client.submit_workflow(_apply_placeholders(workflow, mapping))
        outputs = client.wait_for_outputs(prompt_id)
        file_info = client.pick_output(outputs, (".png", ".jpg", ".jpeg", ".webp"))
        return client.download_file(file_info)


class ComfyUIVideoProvider(BaseVideoProvider):
    name = "comfyui"
    model = settings.VIDEO_MODEL

    def generate_video(self, request: VideoRequest) -> bytes:
        workflow = _load_template("video_workflow.json")
        client = ComfyUIClient()
        image_name = client.upload_image(request.image, f"i2v_ref{request.image_ext}")
        mapping = {
            "PROMPT": request.prompt,
            "NEGATIVE_PROMPT": "",
            "WIDTH": str(request.width),
            "HEIGHT": str(request.height),
            "SEED": str(random.randint(0, 2**32 - 1)),
            "IMAGE": image_name,
            "UNET": settings.VIDEO_MODEL,
            "CLIP": settings.VIDEO_CLIP_MODEL,
            "VAE": settings.VIDEO_VAE_MODEL,
            "FPS": str(VIDEO_FPS),
            "FRAMES": str(_frames_for_duration(request.duration)),
        }
        prompt_id = client.submit_workflow(_apply_placeholders(workflow, mapping))
        outputs = client.wait_for_outputs(prompt_id)
        file_info = client.pick_output(outputs, (".mp4", ".webm", ".webp", ".gif"))
        return client.download_file(file_info)
