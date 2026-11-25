from datetime import datetime, timezone
from decimal import Decimal
import json
import logging
import re
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
    MARKET_INSTRUMENT_PATTERN,
    SOVEREIGN_STATUTORY_PATTERN,
    UNSAFE_FINANCIAL_PATTERNS,
    _is_negated,
)
from app.services.groq_service import (
    GroqRateLimitError,
    call_groq_structured,
    is_groq_enabled,
)
from app.services.plain_language_service import (
    PLAIN_LANGUAGE_COMMUNICATION_RULES,
    annotate_research_report,
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


def _dedupe_evidence(items: list[EvidenceItem]) -> list[EvidenceItem]:
    """Deduplicate evidence items while preserving order."""
    seen: set[tuple[str, str]] = set()
    unique: list[EvidenceItem] = []
    for item in items:
        key = (item.source_type, item.reference_id)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _try_deterministic_calculation(question: str) -> EvidenceItem | None:
    """Detect and run exact Decimal financial calculations when asked in the research query."""
    q = question.lower()
    amt_match = re.search(r"(?:₹|inr\s*|rs\.?\s*)(\d[\d,]*(?:\.\d+)?)\s*(lakh|lakhs|lac|crore|crores|cr|k)?", question, re.IGNORECASE)
    rate_match = re.search(r"(\d+(?:\.\d+)?)\s*%", question)
    months_match = re.search(r"\b(\d+)\s*months?\b", q)
    years_match = re.search(r"\b(\d+)\s*(?:years?|yrs?)\b", q)

    if not (amt_match and rate_match and (months_match or years_match)):
        return None

    try:
        amount = Decimal(amt_match.group(1).replace(",", ""))
        suffix = (amt_match.group(2) or "").lower()
        mult = {"k": 1000, "lakh": 100000, "lakhs": 100000, "lac": 100000, "crore": 10000000, "crores": 10000000, "cr": 10000000}
        if suffix in mult:
            amount *= Decimal(mult[suffix])
        rate = Decimal(rate_match.group(1))
        months = int(months_match.group(1)) if months_match else int(years_match.group(1)) * 12

        if "required" in q and "sip" in q:
            return calculate_financial_metrics(
                "required_monthly_sip",
                {"target_amount": amount, "current_amount": 0, "annual_rate_percent": rate, "time_horizon_months": months},
            )
        if "sip" in q or "monthly" in q:
            return calculate_financial_metrics(
                "future_value_sip",
                {"monthly_contribution": amount, "annual_rate_percent": rate, "time_horizon_months": months},
            )
        if "lump" in q or "future value" in q:
            return calculate_financial_metrics(
                "future_value_lumpsum",
                {"principal": amount, "annual_rate_percent": rate, "time_horizon_months": months},
            )
    except Exception as exc:
        logger.warning("Deterministic research calculation skipped: %s", exc)
    return None


def _gather_baseline_evidence(
    question: str,
    user_id: int,
    db: Any,
) -> list[EvidenceItem]:
    """Gather verified evidence from curated knowledge, user's indexed PDFs, and deterministic math."""
    collected: list[EvidenceItem] = []

    calc_item = _try_deterministic_calculation(question)
    if calc_item is not None and (calc_item.confidence_score or 0) > 0:
        collected.append(calc_item)

    try:
        collected.extend(search_financial_information(topic=question)[:3])
    except Exception as exc:
        logger.warning("Baseline financial knowledge search failed: %s", exc)

    if db is not None and isinstance(user_id, int) and user_id > 0:
        try:
            doc_items = search_financial_documents(
                query=question,
                user_id=user_id,
                db=db,
                limit=2,
            )
            collected.extend(doc_items)
        except Exception as exc:
            logger.warning("Baseline document search skipped/failed: %s", exc)

    return _dedupe_evidence(collected)


def _call_research_llm(
    prompt: str,
    response_model: type[Any],
    client: Any,
    system_instruction: str,
    temperature: float = 0.2,
    max_output_tokens: int = 1500,
) -> Any:
    """Invoke Groq when no explicit Gemini client is provided; fall back to Gemini on rate limit if configured."""
    if client is None and is_groq_enabled():
        try:
            return call_groq_structured(
                prompt=prompt,
                response_model=response_model,
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
        except GroqRateLimitError:
            if settings.gemini_api_key.strip():
                logger.warning("Groq rate limit persisted during research; falling back to Gemini.")
                client = _get_gemini_client()
            else:
                raise

    if client is None:
        client = _get_gemini_client()

    response = client.models.generate_content(
        model=settings.advisor_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
            response_schema=response_model,
        ),
    )
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, response_model):
        return parsed
    text = getattr(response, "text", "")
    return response_model.model_validate_json(text)


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

    # Token-efficient deterministic multi-tool gathering when running on Groq (saves ~3,500 TPM tokens)
    if client is None and is_groq_enabled():
        if not evidence:
            return {
                "selected_tool_name": "gather_all_evidence",
                "selected_tool_args": {"topic": question},
                "iteration": iteration + 1,
                "next_step": "tool",
            }
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
3. "search_financial_information": Curated verified knowledge of Indian tax rules (80C, LTCG/STCG, Old/New tax regime), investment schemes (Nifty 50 Index Funds, ELSS, PPF, FD, SGB, NPS, SCSS), emergency fund rules (salaried vs freelancers), and regulatory standards. Tool args: {{"topic": "keywords"}}

INSTRUCTIONS:
- If CURRENT EVIDENCE GATHERED is empty (0 items), you MUST select action "use_tool" (typically "search_financial_information" or "search_financial_documents").
- If you need additional factual information, calculations, or user documents to answer the question thoroughly, select action "use_tool" with the tool_name and valid tool_args.
- Only select action "finish_research" once you have gathered verified evidence.
- Return your decision adhering to ToolSelectionDecision schema."""

    try:
        decision = _call_research_llm(
            prompt=prompt,
            response_model=ToolSelectionDecision,
            client=client,
            system_instruction="You are an autonomous financial research planner selecting the best tool to gather verified evidence.",
            temperature=0.1,
            max_output_tokens=600,
        )

        if decision.action == "use_tool" and decision.tool_name:
            return {
                "selected_tool_name": decision.tool_name,
                "selected_tool_args": decision.tool_args or {},
                "iteration": iteration + 1,
                "next_step": "tool",
            }

        # Never jump straight to synthesis with zero evidence on iteration 0
        if not evidence and iteration == 0:
            return {
                "selected_tool_name": "search_financial_information",
                "selected_tool_args": {"topic": question},
                "iteration": iteration + 1,
                "next_step": "tool",
            }
        return {"next_step": "synthesize"}

    except Exception as exc:
        logger.warning("Planning step fallback due to error: %s", exc)
        if not evidence and iteration == 0:
            return {
                "selected_tool_name": "search_financial_information",
                "selected_tool_args": {"topic": question},
                "iteration": iteration + 1,
                "next_step": "tool",
            }
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
        if tool_name == "gather_all_evidence":
            new_evidence.extend(
                _gather_baseline_evidence(
                    question=state["question"],
                    user_id=user_id,
                    db=db,
                )
            )

        elif tool_name == "search_financial_documents":
            query = str(args.get("query") or state["question"])
            items = search_financial_documents(query=query, user_id=user_id, db=db, limit=3)
            new_evidence.extend(items)
            # If user has no uploaded docs matching query, also pull approved financial knowledge
            if not items:
                new_evidence.extend(search_financial_information(topic=state["question"]))

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

    updated_evidence = _dedupe_evidence(list(state["gathered_evidence"]) + new_evidence)
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

    # When running on Groq, baseline multi-tool gather already ran all relevant tools in one pass
    if client is None and is_groq_enabled():
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
        evaluation = _call_research_llm(
            prompt=prompt,
            response_model=EvidenceEvaluationResult,
            client=client,
            system_instruction="You are an objective financial research evaluator.",
            temperature=0.1,
            max_output_tokens=600,
        )

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
                if _is_negated(text, match.start(), match.end()):
                    continue

                sentence_start = max(0, text.rfind(".", 0, match.start()) + 1)
                sentence_end = text.find(".", match.end())
                if sentence_end == -1:
                    sentence_end = len(text)
                sentence = text[sentence_start:sentence_end]

                if SOVEREIGN_STATUTORY_PATTERN.search(sentence) and not MARKET_INSTRUMENT_PATTERN.search(sentence):
                    continue

                logger.warning(
                    "Research report safety violation: pattern '%s' matched '%s' in context '%s'",
                    pattern.pattern,
                    match.group(0),
                    text,
                )
                raise ResearchAgentError(
                    "Research report contains disallowed certainty or guaranteed returns language."
                )


def synthesize_report_node(state: ResearchState) -> dict[str, Any]:
    """Synthesize final grounded research report from gathered evidence."""
    question = state["question"]
    evidence = list(state["gathered_evidence"])
    client = state["gemini_client"]

    # Guarantee verified evidence is present even if planning fell back early
    if not evidence:
        evidence = _gather_baseline_evidence(
            question=question,
            user_id=state["user_id"],
            db=state["db"],
        )

    evidence_payload = [
        {
            "source_type": e.source_type,
            "source_title": e.source_title,
            "reference_id": e.reference_id,
            "content": e.content_snippet[:550],
        }
        for e in evidence[:5]
    ]

    prompt = f"""You are an elite, objective Financial Research Agent. Synthesize a comprehensive, practical, easy-to-understand research report answering the user's question using the verified evidence gathered below.

RESEARCH QUESTION:
"{question}"

VERIFIED EVIDENCE ({len(evidence_payload)} items):
{json.dumps(evidence_payload, indent=2)}

INSTRUCTIONS:
1. Directly and thoroughly answer the user's research question using the VERIFIED EVIDENCE above (plus standard, well-established Indian SEBI/RBI/Income Tax educational principles where helpful to connect the dots).
2. Write a clear, structured summary comparing key points, trade-offs, costs, tax rules, and practical takeaways.
3. Provide 4 to 6 concrete, actionable key findings backed by the evidence.
4. Populate the `sources` list with the exact titles/references from the VERIFIED EVIDENCE items you relied on.
5. Leave `supporting_evidence` as an empty array `[]` (the backend attaches the full verified evidence records automatically; do NOT copy long snippets into your JSON).
6. Always include 3 to 5 clear `risks_and_limitations` (e.g. market volatility, inflation, liquidity/lock-in constraints, tax policy changes).
7. NEVER state or imply guaranteed returns, risk-free investments, or certain profits for market-linked products.
8. Return ONLY a JSON object matching the ResearchReport schema.

{PLAIN_LANGUAGE_COMMUNICATION_RULES}"""

    try:
        report = _call_research_llm(
            prompt=prompt,
            response_model=ResearchReport,
            client=client,
            system_instruction=(
                "You are an expert financial research analyst producing clear, evidence-grounded "
                "research dossiers in simple, everyday English."
            ),
            temperature=0.2,
            max_output_tokens=1500,
        )

        # Always attach backend-verified evidence items gathered during execution
        if evidence:
            report.supporting_evidence = evidence

        # Ensure sources list contains actual verified source titles
        if evidence and (not report.sources or all("no " in s.lower() for s in report.sources)):
            report.sources = [
                f"{e.source_title} ({e.reference_id})"
                for e in evidence[:10]
            ]

        if not report.risks_and_limitations:
            report.risks_and_limitations = [
                "Market volatility, inflation, and changes in tax laws or government interest rates can affect actual returns.",
                "Always match investment lock-in periods and liquidity constraints with your personal financial goals.",
            ]

        # Ensure question matches
        report.research_question = question

        _validate_research_safety(report)
        report = annotate_research_report(report)
        return {"report": report, "gathered_evidence": evidence, "next_step": "done"}

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

    if client is None and not is_groq_enabled():
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

