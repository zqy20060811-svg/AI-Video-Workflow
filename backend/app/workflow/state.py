"""LangGraph 工作流状态定义。

工作流：START → story_analysis → storyboard_generation → END
（human_review 为人工确认环节，由 API /storyboard/confirm 完成，不在自动工作流内）
"""

from typing import Any, TypedDict


class WorkflowState(TypedDict, total=False):
    """分镜生产工作流共享状态。"""

    project_id: int
    story: str
    # 角色信息文本（名称、描述、是否已有三视图）
    characters_info: str
    # 故事结构化分析结果
    story_analysis: dict[str, Any]
    # 分镜列表（每个元素为一个 Shot 字典）
    shots: list[dict[str, Any]]
    # 工作流中的错误信息
    error: str
