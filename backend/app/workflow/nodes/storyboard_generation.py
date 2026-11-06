"""节点：AI 生成分镜。"""

import json

from app.services import llm_service
from app.workflow.state import WorkflowState

SYSTEM_PROMPT = """你是一名专业的影视分镜师。请根据故事梗概、故事分析和角色信息，生成一组分镜。

要求：
1. 分镜数量根据故事长度决定，一般 6-12 个。
2. 分镜中的出场角色必须来自【项目角色】列表中的角色，紧扣故事剧情，不要引入与故事无关的人物。
3. 每个 Shot 是一个 JSON 对象，字段如下：
{
  "shot_no": 1,
  "scene": "场景名称，如：废弃车站站台",
  "location": "具体地点",
  "time": "时间，如：深夜",
  "characters": ["出场角色名"],
  "action": "角色动作描述",
  "camera": "镜头语言，如：中景、特写、俯拍、推镜头",
  "visual_description": "画面描述：这一镜头观众实际能看到什么，具体、可视化",
  "dialogue": "台词，没有则为空字符串",
  "duration": 4,
  "image_prompt": "用于生成静态画面的英文提示词，包含画面主体、环境、光线、构图、风格",
  "video_prompt": "用于生成视频的提示词，描述镜头运动和画面中的动态变化"
}
3. 只输出一个 JSON 对象：{"shots": [Shot1, Shot2, ...]}
4. image_prompt 与 video_prompt 必须是英文；其余字段用中文。
5. 画面描述、image_prompt、video_prompt 各自独立成文，不要互相复制。"""


def storyboard_generation(state: WorkflowState) -> WorkflowState:
    """根据故事 + 分析结果 + 角色信息生成分镜列表，写入 state["shots"]。"""
    if state.get("error"):
        return {}

    story = state.get("story", "").strip()
    analysis = state.get("story_analysis") or {}
    characters_info = state.get("characters_info", "（项目尚未添加角色）")

    user_prompt = (
        f"【故事梗概】\n{story}\n\n"
        f"【故事分析结果】\n{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
        f"【项目角色（含三视图素材情况）】\n{characters_info}\n\n"
        "请生成分镜，只输出 JSON。"
    )

    try:
        result = llm_service.generate_structured(SYSTEM_PROMPT, user_prompt)
    except llm_service.LLMError as e:
        return {"error": f"分镜生成失败：{e}"}

    shots = result.get("shots")
    if not isinstance(shots, list) or not shots:
        return {"error": "分镜生成失败：模型未返回有效的 shots 列表"}

    # 规范化字段与编号
    normalized: list[dict] = []
    for i, s in enumerate(shots, start=1):
        if not isinstance(s, dict):
            continue
        normalized.append(
            {
                "shot_no": i,
                "scene": str(s.get("scene") or ""),
                "location": str(s.get("location") or ""),
                "time": str(s.get("time") or ""),
                "characters": s.get("characters") if isinstance(s.get("characters"), list) else [],
                "action": str(s.get("action") or ""),
                "camera": str(s.get("camera") or ""),
                "visual_description": str(s.get("visual_description") or ""),
                "dialogue": str(s.get("dialogue") or ""),
                "duration": float(s.get("duration") or 4),
                "image_prompt": str(s.get("image_prompt") or ""),
                "video_prompt": str(s.get("video_prompt") or ""),
            }
        )

    if not normalized:
        return {"error": "分镜生成失败：模型返回内容无法解析"}

    return {"shots": normalized}
