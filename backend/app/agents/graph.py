from langgraph.graph import StateGraph, END
from typing import Literal
import logging
from .state import AgentState
from .nodes.intent import extract_intent
from .nodes.sql_generator import generate_sql
from .nodes.executor import execute_query
from .nodes.interpreter import interpret_data
from .nodes.viz_planner import plan_visualization
from .nodes.viz_generator import generate_viz_code
from .nodes.insight import generate_insight
from ..safety.validator import validate_sql_safety

logger = logging.getLogger(__name__)

def should_continue_after_validation(state: AgentState) -> Literal["execute", "error"]:
    if state.get("sql_valid"):
        return "execute"
    return "error"

def should_continue_after_execution(state: AgentState) -> Literal["interpret", "error"]:
    if state.get("execution_error"):
        return "error"
    if state.get("data"):
        return "interpret"
    return "error"

def error_handler(state: AgentState) -> AgentState:
    error_msg = (
        state.get("error") or 
        state.get("sql_error") or 
        state.get("execution_error") or 
        "Unknown error"
    )
    logger.error(f"Workflow error: {error_msg}")
    return {
        **state,
        "insight": f"Error: {error_msg}",
        "viz_code": None
    }

# Build graph
workflow = StateGraph(AgentState)

workflow.add_node("extract_intent", extract_intent)
workflow.add_node("generate_sql", generate_sql)
workflow.add_node("validate_sql", validate_sql_safety)
workflow.add_node("execute", execute_query)
workflow.add_node("interpret", interpret_data)
workflow.add_node("plan_viz", plan_visualization)
workflow.add_node("generate_viz", generate_viz_code)
workflow.add_node("generate_insight", generate_insight)
workflow.add_node("error", error_handler)

workflow.set_entry_point("extract_intent")
workflow.add_edge("extract_intent", "generate_sql")
workflow.add_edge("generate_sql", "validate_sql")

workflow.add_conditional_edges(
    "validate_sql",
    should_continue_after_validation,
    {"execute": "execute", "error": "error"}
)

workflow.add_conditional_edges(
    "execute",
    should_continue_after_execution,
    {"interpret": "interpret", "error": "error"}
)

workflow.add_edge("interpret", "plan_viz")
workflow.add_edge("plan_viz", "generate_viz")
workflow.add_edge("generate_viz", "generate_insight")
workflow.add_edge("generate_insight", END)
workflow.add_edge("error", END)

agent_graph = workflow.compile()
logger.info("Agent graph compiled")