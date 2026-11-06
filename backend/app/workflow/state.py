"""LangGraph 工作流状态定义（占位）。

后续阶段将在此定义分镜生成工作流的状态结构：
story -> storyboard -> image_prompt -> image_gen -> video_gen -> export
"""

from typing import Any, TypedDict


class WorkflowState(TypedDict, total=False):
    """分镜生产工作流共享状态（预留结构，后续按需调整）。"""

    project_id: int
    story: str
    storyboard: list[dict[str, Any]]
    image_prompts: list[str]
    video_prompts: list[str]
    scene_images: list[str]
    shot_videos: list[str]
