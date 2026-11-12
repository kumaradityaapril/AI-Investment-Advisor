from datetime import datetime, timezone
import json
import logging
from typing import Any, TypedDict

from google import genai
from google.genai import types
from langgraph.graph import END, StateGraph
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.research_agent import (
    EvidenceEvaluationResult,
    EvidenceItem,
    ResearchReport,
    ResearchRequest,
    ToolSelectionDecision,
)
from app.services.advisor_output_validation_service import (
    UNSAFE_FINANCIAL_PATTERNS,
    _is_negated,
)
from app.services.research_tools import (
    calculate_financial_metrics,
    search_financial_documents,
    search_financial_information,
)

logger = logging.getLogger(__name__)


class ResearchAgentError(Exception):
    """Raised when the AI Research Agent fails or encounters safety violations."""


class ResearchState(TypedDict):
    question: str
    user_id: int
    db: Any
    gemini_client: Any
    max_iterations: int
    iteration: int
    gathered_evidence: list[EvidenceItem]
    next_step: str
    selected_tool_name: str | None
    selected_tool_args: dict[str, Any]
    is_sufficient: bool
    evaluation_reasoning: str | None
    report: ResearchReport | None
    error: str | None


def _get_gemini_client() -> genai.Client:
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options={"api_version": "v1beta", "timeout": 30000},
    )


def plan_node(state: ResearchState) -> dict[str, Any]:
    """Decide which bounded tool to invoke next or proceed to synthesis."""
    iteration = state["iteration"]
    max_iter = state["max_iterations"]
    question = state["question"]
    evidence = state["gathered_evidence"]
    client = state["gemini_client"]

    if iteration >= max_iter:
        logger.info("Agent reached max iterations (%d/%d). Moving to synthesis.", iteration, max_iter)
        return {"next_step": "synthesize"}

    evidence_summary = [
        {"title": e.source_title, "snippet": e.content_snippet[:200]}
        for e in evidence
    ]

    prompt = f"""You are an autonomous AI Financial Research Agent planning the next step for this investor query:
QUESTION: "{question}"

CURRENT EVIDENCE GATHERED ({len(evidence)} items):
{json.dumps(evidence_summary, indent=2)}

AVAILABLE TOOLS:
1. "search_financial_documents": Search user's uploaded/indexed financial documents and portfolio notes via RAG. Tool args: {{"query": "search query"}}
2. "calculate_financial_metrics": Deterministic math calculations. Tool args: {{"calculation_type": "future_value_lumpsum"|"future_value_sip"|"monthly_surplus"|"savings_rate"|"expense_ratio"|"required_monthly_sip"|"goal_shortfall", "parameters": {{...}}}}
3. "search_financial_information": Curated verified knowledge of Indian tax rules (80C, LTCG/STCG), investment schemes (PPF, FD, SGB, NPS), and regulatory standards. Tool args: {{"topic": "keywords"}}

INSTRUCTIONS:
- If you need factual information, calculations, or user documents to answer the question, select action "use_tool" with the tool_name and valid tool_args.
- If you have sufficient evidence or no further tools are appropriate, select action "finish_research".
- Return your decision adhering to ToolSelectionDecision schema."""

    try:
        response = client.models.generate_content(
            model=settings.advisor_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=800,
                response_mime_type="application/json",
                response_schema=ToolSelectionDecision,
            ),
        )
        decision = getattr(response, "parsed", None)
        if not isinstance(decision, ToolSelectionDecision):
            text = getattr(response, "text", "")
            decision = ToolSelectionDecision.model_validate_json(text)

        if decision.action == "use_tool" and decision.tool_name:
            return {
                "selected_tool_name": decision.tool_name,
                "selected_tool_args": decision.tool_args or {},
                "iteration": iteration + 1,
                "next_step": "tool",
            }
        else:
            return {"next_step": "synthesize"}

    except Exception as exc:
        logger.warning("Planning step fallback to synthesis due to error: %s", exc)
        return {"next_step": "synthesize"}


def tool_execution_node(state: ResearchState) -> dict[str, Any]:
    """Execute the selected bounded tool and collect evidence."""
    tool_name = state.get("selected_tool_name")
    args = state.get("selected_tool_args") or {}
    user_id = state["user_id"]
    db = state["db"]
    new_evidence: list[EvidenceItem] = []

    logger.info("Executing tool '%s' with args %s for user %s", tool_name, args, user_id)

    try:
        if tool_name == "search_financial_documents":
            query = str(args.get("query") or state["question"])
            items = search_financial_documents(query=query, user_id=user_id, db=db, limit=3)
            new_evidence.extend(items)

        elif tool_name == "calculate_financial_metrics":
            calc_type = str(args.get("calculation_type") or "future_value_lumpsum")
            params = args.get("parameters") or {}
            item = calculate_financial_metrics(calculation_type=calc_type, parameters=params)
            new_evidence.append(item)

        elif tool_name == "search_financial_information":
            topic = str(args.get("topic") or state["question"])
            items = search_financial_information(topic=topic)
            new_evidence.extend(items)

        else:
            logger.warning("Unknown tool '%s' called.", tool_name)

    except Exception as exc:
        logger.exception("Error executing tool %s: %s", tool_name, exc)

    updated_evidence = list(state["gathered_evidence"]) + new_evidence
    return {
        "gathered_evidence": updated_evidence,
        "next_step": "evaluate",
    }


def evaluate_evidence_node(state: ResearchState) -> dict[str, Any]:
    """Evaluate whether the evidence collected so far is sufficient to answer the question."""
    iteration = state["iteration"]
    max_iter = state["max_iterations"]
    question = state["question"]
    evidence = state["gathered_evidence"]
    client = state["gemini_client"]

    if iteration >= max_iter or not evidence:
        return {"is_sufficient": True, "next_step": "synthesize"}

    evidence_summary = [
        {"source": e.source_title, "snippet": e.content_snippet}
        for e in evidence
    ]

    prompt = f"""Evaluate whether the gathered evidence is sufficient to thoroughly answer this financial research question:
QUESTION: "{question}"

EVIDENCE COLLECTED:
{json.dumps(evidence_summary, indent=2)}

INSTRUCTIONS:
- If the evidence provides enough information to formulate a well-supported, factual research report, set is_sufficient=True.
- If a critical piece of information is missing and an additional search or calculation could find it, set is_sufficient=False.
- Return your evaluation matching EvidenceEvaluationResult schema."""

    try:
        response = client.models.generate_content(
            model=settings.advisor_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=600,
                response_mime_type="application/json",
                response_schema=EvidenceEvaluationResult,
            ),
        )
        evaluation = getattr(response, "parsed", None)
        if not isinstance(evaluation, EvidenceEvaluationResult):
            text = getattr(response, "text", "")
            evaluation = EvidenceEvaluationResult.model_validate_json(text)

        if evaluation.is_sufficient:
            return {"is_sufficient": True, "next_step": "synthesize"}
        else:
            return {"is_sufficient": False, "next_step": "plan"}

    except Exception as exc:
        logger.warning("Evidence evaluation fallback to synthesis: %s", exc)
        return {"is_sufficient": True, "next_step": "synthesize"}


def _validate_research_safety(report: ResearchReport) -> None:
    """Enforce strict guardrails against guaranteed returns, certainties, and unverified promises."""
    texts = [
        report.summary,
        *report.key_findings,
        *report.risks_and_limitations,
    ]
    for text in texts:
        for pattern in UNSAFE_FINANCIAL_PATTERNS:
            for match in pattern.finditer(text):
                if _is_negated(text, match.start()):
                    continue
                raise ResearchAgentError(
                    "Research report contains disallowed certainty or guaranteed returns language."
                )


def synthesize_report_node(state: ResearchState) -> dict[str, Any]:
    """Synthesize final grounded research report from gathered evidence."""
    question = state["question"]
    evidence = state["gathered_evidence"]
    client = state["gemini_client"]

    evidence_payload = [
        {
            "source_type": e.source_type,
            "source_title": e.source_title,
            "reference_id": e.reference_id,
            "content": e.content_snippet,
        }
        for e in evidence
    ]

    prompt = f"""You are an elite, objective Financial Research Agent. Synthesize a comprehensive research report for the user's question based strictly on the verified evidence gathered.

RESEARCH QUESTION:
"{question}"

VERIFIED EVIDENCE:
{json.dumps(evidence_payload, indent=2)}

INSTRUCTIONS:
1. Provide a clear, objective summary answering the research question.
2. Highlight key findings backed by the evidence.
3. Explicitly cite sources in the sources list.
4. Always include risks and limitations (e.g. market risk, inflation risk, liquidity constraints, tax policy changes).
5. NEVER state or imply guaranteed returns, risk-free investments, or certain profits.
6. Return the output matching the ResearchReport schema."""

    try:
        response = client.models.generate_content(
            model=settings.advisor_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=3500,
                response_mime_type="application/json",
                response_schema=ResearchReport,
            ),
        )
        report = getattr(response, "parsed", None)
        if not isinstance(report, ResearchReport):
            text = getattr(response, "text", "")
            report = ResearchReport.model_validate_json(text)

        # Merge evidence items gathered during execution
        if not report.supporting_evidence:
            report.supporting_evidence = evidence

        # Ensure question matches
        report.research_question = question

        _validate_research_safety(report)
        return {"report": report, "next_step": "done"}

    except Exception as exc:
        if isinstance(exc, ResearchAgentError):
            raise
        logger.exception("Failed to synthesize research report.")
        raise ResearchAgentError(f"Failed to synthesize research report: {exc}") from exc


def _route_from_plan(state: ResearchState) -> str:
    if state.get("next_step") == "tool":
        return "tool"
    return "synthesize"


def _route_from_eval(state: ResearchState) -> str:
    if state.get("is_sufficient") or state.get("iteration", 0) >= state.get("max_iterations", 3):
        return "synthesize"
    return "plan"


def build_research_graph() -> Any:
    """Build and compile the LangGraph workflow for the AI Research Agent."""
    workflow = StateGraph(ResearchState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("tool", tool_execution_node)
    workflow.add_node("evaluate", evaluate_evidence_node)
    workflow.add_node("synthesize", synthesize_report_node)

    workflow.set_entry_point("plan")

    workflow.add_conditional_edges(
        "plan",
        _route_from_plan,
        {
            "tool": "tool",
            "synthesize": "synthesize",
        },
    )
    workflow.add_edge("tool", "evaluate")
    workflow.add_conditional_edges(
        "evaluate",
        _route_from_eval,
        {
            "plan": "plan",
            "synthesize": "synthesize",
        },
    )
    workflow.add_edge("synthesize", END)

    return workflow.compile()


# Singleton compiled graph
_COMPILED_RESEARCH_GRAPH = build_research_graph()


def run_research_agent(
    db: Session,
    user_id: int,
    request: ResearchRequest,
    client: genai.Client | None = None,
) -> ResearchReport:
    """
    Execute autonomous financial research workflow with controlled bounded tools.
    """
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    if not request.question or not request.question.strip():
        raise ValueError("Research question cannot be empty.")

    if client is None:
        try:
            client = _get_gemini_client()
        except Exception as exc:
            raise ResearchAgentError(f"Failed to initialize Gemini client: {exc}") from exc

    initial_state: ResearchState = {
        "question": request.question.strip(),
        "user_id": user_id,
        "db": db,
        "gemini_client": client,
        "max_iterations": request.max_iterations,
        "iteration": 0,
        "gathered_evidence": [],
        "next_step": "plan",
        "selected_tool_name": None,
        "selected_tool_args": {},
        "is_sufficient": False,
        "evaluation_reasoning": None,
        "report": None,
        "error": None,
    }

    try:
        final_state = _COMPILED_RESEARCH_GRAPH.invoke(initial_state)
    except Exception as exc:
        if isinstance(exc, ResearchAgentError):
            raise
        logger.exception("LangGraph research execution failed.")
        raise ResearchAgentError(f"Research agent execution failed: {exc}") from exc

    report = final_state.get("report")
    if not isinstance(report, ResearchReport):
        raise ResearchAgentError("Research agent finished without producing a report.")

    return report

