"""LLM Service：统一的 LLM 调用入口（OpenAI 兼容 API）。

模型通过 .env 配置（LLM_API_KEY / LLM_BASE_URL / LLM_MODEL），
更换 DeepSeek / OpenAI / Ollama / 其他兼容服务时无需修改业务代码。
"""

import json
import re

from openai import OpenAI

from app.core.config import settings


class LLMError(Exception):
    """LLM 调用或结构化解析失败。"""


def _client() -> OpenAI:
    return OpenAI(
        api_key=settings.LLM_API_KEY or "not-set",
        base_url=settings.LLM_BASE_URL,
    )


def _extract_json(text: str) -> dict:
    """从模型输出中提取 JSON 对象（容忍 markdown 代码块包裹）。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


def generate_structured(system: str, user: str) -> dict:
    """
    调用 LLM 生成结构化 JSON。
    优先使用 API 的 JSON 模式（response_format），不支持时回退普通模式；
    解析失败时自动重试一次（把错误信息带给模型要求修正），仍失败则抛 LLMError。
    """
    client = _client()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    def _chat() -> str:
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                temperature=settings.LLM_TEMPERATURE,
                response_format={"type": "json_object"},
            )
        except Exception:
            # 服务不支持 response_format 时回退普通模式
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                temperature=settings.LLM_TEMPERATURE,
            )
        return response.choices[0].message.content or ""

    for attempt in range(2):
        content = _chat()
        try:
            return _extract_json(content)
        except (json.JSONDecodeError, ValueError) as e:
            if attempt == 0:
                # 请求模型修复上一次输出
                messages.append({"role": "assistant", "content": content})
                messages.append(
                    {
                        "role": "user",
                        "content": f"你的输出无法解析为 JSON（{e}）。请只输出一个合法的 JSON 对象，不要任何其他文字。",
                    }
                )
            else:
                raise LLMError("模型输出无法解析为 JSON") from e

    raise LLMError("LLM 调用失败")  # 理论上不可达


def generate_text(system: str, user: str) -> str:
    """调用 LLM 生成纯文本。"""
    response = _client().chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=settings.LLM_TEMPERATURE,
    )
    return response.choices[0].message.content or ""
