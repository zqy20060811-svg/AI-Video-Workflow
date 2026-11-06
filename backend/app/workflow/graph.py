"""LangGraph 工作流组装：START → story_analysis → storyboard_generation → END。

human_review（人工审核/确认）不在自动工作流内，
由 API `POST /api/projects/{id}/storyboard/confirm` 完成。
"""

from langgraph.graph import END, START, StateGraph

from app.workflow.nodes.story_analysis import story_analysis
from app.workflow.nodes.storyboard_generation import storyboard_generation
from app.workflow.state import WorkflowState


def build_storyboard_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("story_analysis", story_analysis)
    graph.add_node("storyboard_generation", storyboard_generation)
    graph.add_edge(START, "story_analysis")
    graph.add_edge("story_analysis", "storyboard_generation")
    graph.add_edge("storyboard_generation", END)
    return graph.compile()


storyboard_graph = build_storyboard_graph()
