from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.user import User
from app.schemas.research_agent import (
    EvidenceEvaluationResult,
    EvidenceItem,
    ResearchReport,
    ResearchRequest,
    ToolSelectionDecision,
)
from app.services.research_agent_service import (
    ResearchAgentError,
    _validate_research_safety,
    build_research_graph,
    evaluate_evidence_node,
    plan_node,
    run_research_agent,
    synthesize_report_node,
    tool_execution_node,
)
from app.services.research_tools import (
    calculate_financial_metrics,
    search_financial_documents,
    search_financial_information,
)

client = TestClient(app)


@pytest.fixture
def test_users():
    db = SessionLocal()
    u1 = User(
        email=f"research_u1_{uuid4().hex[:6]}@example.com",
        hashed_password="pw1",
    )
    db.add(u1)
    db.commit()
    db.refresh(u1)
    user1_id = u1.id
    db.close()

    yield user1_id

    clean_db = SessionLocal()
    try:
        user1 = clean_db.get(User, user1_id)
        if user1:
            clean_db.delete(user1)
        clean_db.commit()
    finally:
        clean_db.close()


@pytest.fixture
def sample_research_report():
    return ResearchReport(
        research_question="What are the tax implications and expected returns of PPF vs Equity Mutual Funds?",
        summary="PPF provides government-backed capital protection and EEE tax exemption, whereas Equity Mutual Funds provide market-linked growth subject to capital gains tax.",
        key_findings=[
            "PPF offers ~7.1% interest with complete tax exemption on interest and maturity under Section 80C.",
            "Equity mutual funds are subject to 12.5% LTCG above ₹1.25 Lakh per financial year.",
        ],
        supporting_evidence=[
            EvidenceItem(
                source_type="financial_information",
                source_title="Public Provident Fund (PPF) Statutory Guidelines",
                reference_id="PPF_SCHEME_2019",
                content_snippet="PPF enjoys EEE tax status with statutory interest.",
                confidence_score=0.95,
            )
        ],
        sources=[
            "Public Provident Fund (PPF) Statutory Guidelines",
            "Finance Act 2024 Equity Taxation Provisions",
        ],
        risks_and_limitations=[
            "PPF has a mandatory 15-year lock-in period.",
            "Equity mutual funds carry market risk and lack capital protection.",
        ],
    )


# -------------------------------------------------------------
# 1. Bounded Tools Unit Tests
# -------------------------------------------------------------

def test_search_financial_documents_rejects_invalid_user_id():
    db = SessionLocal()
    try:
        assert search_financial_documents(query="income", user_id=True, db=db) == []  # type: ignore
        assert search_financial_documents(query="income", user_id=0, db=db) == []
        assert search_financial_documents(query="income", user_id=-5, db=db) == []
        assert search_financial_documents(query="", user_id=1, db=db) == []
    finally:
        db.close()


def test_search_financial_documents_returns_mapped_evidence(monkeypatch):
    db = SessionLocal()
    try:
        mock_chunk = MagicMock()
        mock_chunk.chunk_id = 42
        mock_chunk.document_name = "tax_statement.pdf"
        mock_chunk.content = "Total gross salary was ₹12,00,000 for FY 2024-25."
        mock_chunk.relevance_score = 92.5

        monkeypatch.setattr(
            "app.services.research_tools.retrieve_and_rerank",
            lambda **kwargs: [mock_chunk],
        )

        results = search_financial_documents(query="salary", user_id=1, db=db)
        assert len(results) == 1
        assert results[0].source_type == "financial_document"
        assert results[0].source_title == "tax_statement.pdf"
        assert results[0].reference_id == "chunk_42"
        assert results[0].confidence_score == 0.925
    finally:
        db.close()


def test_calculate_financial_metrics_deterministic():
    # 1. Future value lump sum
    lump = calculate_financial_metrics(
        "future_value_lumpsum",
        {"principal": "100000", "annual_rate_percent": "10", "tenure_years": 2},
    )
    assert lump.source_type == "financial_calculation"
    assert "₹122039.10" in lump.content_snippet
    assert lump.confidence_score == 1.0

    # 2. Future value SIP
    sip = calculate_financial_metrics(
        "future_value_sip",
        {"monthly_contribution": "5000", "annual_rate_percent": "12", "time_horizon_months": 12},
    )
    assert sip.source_type == "financial_calculation"
    assert "₹63412.52" in sip.content_snippet

    # 3. Monthly surplus
    surplus = calculate_financial_metrics(
        "monthly_surplus",
        {"monthly_income": "100000", "monthly_expenses": "60000"},
    )
    assert "₹40000.00" in surplus.content_snippet

    # 4. Unsupported calculation handled safely
    invalid = calculate_financial_metrics("unknown_formula", {})
    assert "Calculation error" in invalid.content_snippet
    assert invalid.confidence_score == 0.0


def test_search_financial_information():
    # 1. Matches PPF
    ppf_info = search_financial_information("Tell me about PPF tax exemption rules")
    assert len(ppf_info) >= 1
    assert any("PPF" in item.source_title for item in ppf_info)
    assert any("EEE" in item.content_snippet for item in ppf_info)

    # 2. Matches Fixed Deposit
    fd_info = search_financial_information("Are bank FD deposits insured by DICGC?")
    assert len(fd_info) >= 1
    assert any("DICGC" in item.content_snippet for item in fd_info)

    # 3. Matches Equity & Capital gains
    equity_info = search_financial_information("What is LTCG tax on mutual funds?")
    assert len(equity_info) >= 1
    assert any("12.5%" in item.content_snippet for item in equity_info)


# -------------------------------------------------------------
# 2. Safety Validation Tests
# -------------------------------------------------------------

def test_research_safety_rejects_guaranteed_returns(sample_research_report):
    sample_research_report.summary = "This portfolio promises guaranteed returns with risk-free investment."
    with pytest.raises(ResearchAgentError, match="disallowed certainty"):
        _validate_research_safety(sample_research_report)


def test_research_safety_allows_negated_risk_warnings(sample_research_report):
    sample_research_report.summary = "Mutual fund returns are not guaranteed and capital is not risk-free."
    # Should not raise exception
    _validate_research_safety(sample_research_report)


# -------------------------------------------------------------
# 3. LangGraph Workflow Nodes & Graph Tests
# -------------------------------------------------------------

def test_build_research_graph_compilation():
    graph = build_research_graph()
    assert graph is not None


def test_plan_node_tool_selection():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.parsed = ToolSelectionDecision(
        action="use_tool",
        tool_name="search_financial_information",
        tool_args={"topic": "PPF"},
        reasoning="Need statutory PPF facts",
    )
    mock_client.models.generate_content.return_value = mock_resp

    state = {
        "question": "What is PPF?",
        "user_id": 1,
        "db": None,
        "gemini_client": mock_client,
        "max_iterations": 3,
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

    result = plan_node(state)
    assert result["next_step"] == "tool"
    assert result["selected_tool_name"] == "search_financial_information"
    assert result["iteration"] == 1


def test_plan_node_respects_max_iterations():
    mock_client = MagicMock()
    state = {
        "question": "What is PPF?",
        "user_id": 1,
        "db": None,
        "gemini_client": mock_client,
        "max_iterations": 2,
        "iteration": 2,  # already at max!
        "gathered_evidence": [],
        "next_step": "plan",
        "selected_tool_name": None,
        "selected_tool_args": {},
        "is_sufficient": False,
        "evaluation_reasoning": None,
        "report": None,
        "error": None,
    }
    result = plan_node(state)
    assert result["next_step"] == "synthesize"
    mock_client.models.generate_content.assert_not_called()


def test_tool_execution_node_appends_evidence():
    state = {
        "question": "Tax rules",
        "user_id": 1,
        "db": None,
        "gemini_client": None,
        "max_iterations": 3,
        "iteration": 1,
        "gathered_evidence": [],
        "next_step": "tool",
        "selected_tool_name": "search_financial_information",
        "selected_tool_args": {"topic": "80C"},
        "is_sufficient": False,
        "evaluation_reasoning": None,
        "report": None,
        "error": None,
    }
    result = tool_execution_node(state)
    assert result["next_step"] == "evaluate"
    assert len(result["gathered_evidence"]) >= 1
    assert result["gathered_evidence"][0].source_type == "financial_information"


def test_evaluate_evidence_node():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.parsed = EvidenceEvaluationResult(
        is_sufficient=True,
        reasoning="Collected verified rules.",
    )
    mock_client.models.generate_content.return_value = mock_resp

    state = {
        "question": "What is 80C limit?",
        "user_id": 1,
        "db": None,
        "gemini_client": mock_client,
        "max_iterations": 3,
        "iteration": 1,
        "gathered_evidence": [
            EvidenceItem(
                source_type="financial_information",
                source_title="Section 80C",
                reference_id="80C",
                content_snippet="Limit is ₹1.5 Lakh.",
            )
        ],
        "next_step": "evaluate",
        "selected_tool_name": None,
        "selected_tool_args": {},
        "is_sufficient": False,
        "evaluation_reasoning": None,
        "report": None,
        "error": None,
    }
    result = evaluate_evidence_node(state)
    assert result["is_sufficient"] is True
    assert result["next_step"] == "synthesize"


def test_synthesize_report_node(sample_research_report):
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.parsed = sample_research_report
    mock_client.models.generate_content.return_value = mock_resp

    state = {
        "question": sample_research_report.research_question,
        "user_id": 1,
        "db": None,
        "gemini_client": mock_client,
        "max_iterations": 3,
        "iteration": 1,
        "gathered_evidence": sample_research_report.supporting_evidence,
        "next_step": "synthesize",
        "selected_tool_name": None,
        "selected_tool_args": {},
        "is_sufficient": True,
        "evaluation_reasoning": None,
        "report": None,
        "error": None,
    }
    result = synthesize_report_node(state)
    assert result["next_step"] == "done"
    assert result["report"] == sample_research_report


# -------------------------------------------------------------
# 4. End-to-End Service & API Integration Tests
# -------------------------------------------------------------

def test_run_research_agent_service(test_users, sample_research_report, monkeypatch):
    user1_id = test_users
    db = SessionLocal()
    try:
        # Patch the graph execution to return final state with sample report
        monkeypatch.setattr(
            "app.services.research_agent_service._COMPILED_RESEARCH_GRAPH.invoke",
            lambda state: {"report": sample_research_report},
        )

        report = run_research_agent(
            db=db,
            user_id=user1_id,
            request=ResearchRequest(
                question="PPF vs Mutual Funds comparison",
                max_iterations=2,
            ),
            client=MagicMock(),
        )

        assert report.summary == sample_research_report.summary
        assert len(report.key_findings) >= 1
        assert len(report.sources) >= 1
    finally:
        db.close()


def test_advisor_research_api_endpoint(test_users, sample_research_report, monkeypatch):
    user1_id = test_users
    db = SessionLocal()
    user1 = db.get(User, user1_id)

    from app.api.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user1

    try:
        monkeypatch.setattr(
            "app.api.advisor.run_research_agent",
            lambda **kwargs: sample_research_report,
        )
        monkeypatch.setattr(
            "app.api.research.run_research_agent",
            lambda **kwargs: sample_research_report,
        )

        # 1. POST /advisor/research
        res1 = client.post(
            "/advisor/research",
            json={"question": "Analyze PPF vs Mutual Funds for long term", "max_iterations": 3},
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert "summary" in data1
        assert len(data1["key_findings"]) >= 1
        assert len(data1["sources"]) >= 1

        # 2. POST /research (dedicated router)
        res2 = client.post(
            "/research",
            json={"question": "Analyze PPF vs Mutual Funds for long term", "max_iterations": 3},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["summary"] == sample_research_report.summary

        # 3. Invalid empty question returns 422 (Pydantic validation min_length=3)
        res_bad = client.post(
            "/advisor/research",
            json={"question": "ab"},
        )
        assert res_bad.status_code == 422

    finally:
        app.dependency_overrides.clear()
        db.close()


def test_advisor_research_api_unauthorized():
    res = client.post(
        "/advisor/research",
        json={"question": "Analyze PPF tax implications"},
    )
    assert res.status_code == 401
