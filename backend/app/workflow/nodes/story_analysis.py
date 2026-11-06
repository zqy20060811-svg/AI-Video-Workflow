"""节点：AI 故事结构化分析。"""

from app.services import llm_service
from app.workflow.state import WorkflowState

SYSTEM_PROMPT = """你是一名专业的影视故事分析师。请对给定的故事梗概进行结构化分析。
只输出一个 JSON 对象，包含以下字段：
{
  "title": "故事标题（简短）",
  "summary": "200字以内的故事摘要",
  "characters": [{"name": "角色名", "role": "主角/配角/反派", "profile": "角色简述"}],
  "main_conflict": "核心冲突，一句话",
  "story_structure": [{"stage": "起/承/转/合等", "description": "该阶段剧情"}],
  "key_events": ["关键事件1", "关键事件2"]
}"""


def story_analysis(state: WorkflowState) -> WorkflowState:
    """调用 LLM 对故事进行结构化分析，结果写入 state["story_analysis"]。"""
    story = state.get("story", "").strip()
    if not story:
        return {"error": "故事梗概为空，无法分析"}

    try:
        analysis = llm_service.generate_structured(
            SYSTEM_PROMPT,
            f"请分析以下故事梗概：\n\n{story}",
        )
    except llm_service.LLMError as e:
        return {"error": f"故事分析失败：{e}"}

    return {"story_analysis": analysis}
