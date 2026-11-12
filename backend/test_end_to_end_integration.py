from datetime import datetime, timezone
from decimal import Decimal
import io
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.goal import Goal
from app.models.profile import Profile
from app.models.risk_assessment import RiskAssessment
from app.models.user import User
from app.models.analysis_history import AnalysisHistory
from app.schemas.ai_advisor import (
    ADVISOR_DISCLAIMER,
    AIAdvisorGenerationResponse,
    AIAdvisorResponse,
    AdvisorEvidence,
    AdvisorRecommendation,
    FinancialClaim,
)
from app.schemas.analysis_diff import (
    AnalysisDiffExplanation,
    AnalysisDiffRequest,
)
from app.schemas.scenario_simulation import (
    SCENARIO_DISCLAIMER,
    ScenarioAIExplanation,
)
from app.schemas.research_agent import (
    EvidenceItem,
    ResearchReport,
)
from app.evaluation import DEFAULT_EVALUATION_DATASET, EvaluationRunner

client = TestClient(app)


# =============================================================
# SCENARIO 1: Full New Investor Journey
# Register -> Login -> Profile -> Goal -> Risk -> Context -> Advisor
# =============================================================

def test_scenario_1_new_investor_journey(monkeypatch):
    uid = uuid4().hex[:8]
    email = f"e2e_investor_{uid}@example.com"
    password = "SecurePassword123!"

    # 1. Register
    reg_resp = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert reg_resp.status_code == 201
    user_id = reg_resp.json()["id"]

    # 2. Login (JSON payload)
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Investor Profile (PUT /profile/me)
    prof_resp = client.put(
        "/profile/me",
        headers=headers,
        json={
            "monthly_income": 100000.0,
            "monthly_expenses": 60000.0,
            "savings": 200000.0,
            "existing_investments": 100000.0,
        },
    )
    assert prof_resp.status_code == 200
    assert prof_resp.json()["monthly_income"] == "100000.00"

    # 4. Create Financial Goal
    goal_resp = client.post(
        "/goals",
        headers=headers,
        json={
            "title": "Retirement Fund",
            "goal_type": "retirement",
            "target_amount": 10000000.0,
            "time_horizon_months": 240,
            "planned_monthly_investment": 20000.0,
        },
    )
    assert goal_resp.status_code == 201
    goal_id = goal_resp.json()["id"]

    # 5. Complete Risk Assessment
    risk_resp = client.post(
        "/risk-assessments",
        headers=headers,
        json={
            "investment_experience": 2,
            "time_horizon": 3,
            "loss_reaction": 2,
            "growth_preference": 3,
            "financial_stability": 3,
        },
    )
    assert risk_resp.status_code == 201
    assert "risk_category" in risk_resp.json()

    # 6. Verify Financial Context Engine
    ctx_resp = client.get("/financial-analysis/me", headers=headers)
    assert ctx_resp.status_code == 200
    ctx_data = ctx_resp.json()
    assert ctx_data["metrics"]["monthly_surplus"] == "40000.00"
    assert ctx_data["metrics"]["savings_rate_percent"] == "40.00"
    assert ctx_data["metrics"]["expense_ratio_percent"] == "60.00"
    assert len(ctx_data["goals"]) == 1

    # 7. Request AI Investment Analysis
    mock_gen_response = AIAdvisorGenerationResponse(
        overall_assessment="Your financial cash flow is robust with a calculated ₹40,000 monthly surplus.",
        key_findings=["Calculated surplus provides strong compounding foundation."],
        recommendations=[
            AdvisorRecommendation(
                title="Establish Balanced Equity SIP",
                explanation="Long horizon for retirement supports disciplined equity allocation.",
                suggested_action="Allocate surplus regularly toward broad-market index funds.",
                priority="high",
            )
        ],
        risk_considerations=["Equity markets fluctuate in the short term."],
        assumptions=["Regular income and expense levels remain consistent."],
        limitations=["Tax regime deductions not factored in."],
        evidence_chunk_ids=[],
        financial_claims=[
            FinancialClaim(
                metric_key="monthly_surplus",
                claimed_value=Decimal("40000.00"),
            )
        ],
    )

    monkeypatch.setattr(
        "app.services.advisor_orchestration_service.generate_advisor_response",
        lambda **kwargs: mock_gen_response,
    )

    adv_resp = client.post(
        "/advisor/analyze",
        headers=headers,
        json={"question": "How should I allocate my ₹40,000 monthly surplus?"},
    )
    assert adv_resp.status_code == 200
    adv_data = adv_resp.json()
    assert adv_data["disclaimer"] == ADVISOR_DISCLAIMER
    assert len(adv_data["recommendations"]) == 1
    assert adv_data["overall_assessment"] == mock_gen_response.overall_assessment


# =============================================================
# SCENARIO 2: Document Intelligence Journey
# Upload -> Index chunks -> Vector Search -> Grounded Advisor Citation
# =============================================================

def test_scenario_2_document_intelligence_journey(monkeypatch):
    db = SessionLocal()
    uid = uuid4().hex[:8]
    user = User(email=f"e2e_doc_{uid}@example.com", hashed_password="pw")
    db.add(user)
    db.commit()
    db.refresh(user)

    from app.api.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        # Pre-seed document and chunk with correct schema columns
        doc = Document(
            user_id=user.id,
            original_filename="portfolio_statement.pdf",
            stored_filename=f"portfolio_{uid}.pdf",
            content_type="application/pdf",
            file_size_bytes=1024,
            status="processed",
            indexing_status="indexed",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            page_number=1,
            content="Asset allocation summary: Domestic Equities 70%, Fixed Income 25%, Cash 5%.",
            embedding=[0.1] * 768,
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)

        # Mock RAG retrieval
        from app.services.reranking_service import RerankedChunk

        mock_reranked = RerankedChunk(
            chunk_id=chunk.id,
            document_id=doc.id,
            document_name=doc.original_filename,
            page_number=1,
            chunk_index=0,
            content=chunk.content,
            relevance_score=95.0,
            rrf_score=0.9,
            semantic_rank=1,
            keyword_rank=1,
            rerank_rank=1,
        )

        monkeypatch.setattr(
            "app.services.advisor_orchestration_service.retrieve_and_rerank",
            lambda **kwargs: [mock_reranked],
        )

        mock_gen = AIAdvisorGenerationResponse(
            overall_assessment="Portfolio review indicates majority equity allocation from uploaded statement.",
            key_findings=["Portfolio is predominantly allocated to equities."],
            recommendations=[
                AdvisorRecommendation(
                    title="Maintain Equity Allocation",
                    explanation="Consistent with long-term horizon.",
                    suggested_action="Continue current SIPs.",
                    priority="medium",
                )
            ],
            risk_considerations=["Short-term equity drawdowns."],
            assumptions=["Asset values based on provided statement date."],
            limitations=["Tax implications not assessed based on current holdings."],
            evidence_chunk_ids=[chunk.id],
            financial_claims=[],
        )

        monkeypatch.setattr(
            "app.services.advisor_orchestration_service.generate_advisor_response",
            lambda **kwargs: mock_gen,
        )

        resp = client.post(
            "/advisor/analyze",
            json={"question": "What is my current asset allocation according to my statement?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["evidence"]) == 1
        assert data["evidence"][0]["chunk_id"] == chunk.id
        assert data["evidence"][0]["filename"] == "portfolio_statement.pdf"
        assert "70%" in data["evidence"][0]["supporting_excerpt"]

    finally:
        app.dependency_overrides.clear()
        db.close()


# =============================================================
# SCENARIO 3: History & Memory Diff Journey
# Save Snapshot 1 -> Update Context -> Save Snapshot 2 -> Compare Diff
# =============================================================

def test_scenario_3_history_and_memory_diff(monkeypatch):
    db = SessionLocal()
    uid = uuid4().hex[:8]
    user = User(email=f"e2e_diff_{uid}@example.com", hashed_password="pw")
    db.add(user)
    db.commit()
    db.refresh(user)

    from app.api.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        now = datetime.now(timezone.utc)
        h1 = AnalysisHistory(
            user_id=user.id,
            question="November checkup",
            advisor_model="gemini-2.5-flash",
            financial_context_snapshot={
                "profile": {"monthly_income": 80000, "monthly_expenses": 50000},
                "metrics": {"monthly_surplus": 30000, "savings_rate_percent": 37.5},
            },
            advisor_response_snapshot={
                "recommendations": [{"title": "Save Emergency Buffer", "suggested_action": "Set aside 5k"}]
            },
            created_at=now,
        )
        h2 = AnalysisHistory(
            user_id=user.id,
            question="December checkup",
            advisor_model="gemini-2.5-flash",
            financial_context_snapshot={
                "profile": {"monthly_income": 100000, "monthly_expenses": 50000},
                "metrics": {"monthly_surplus": 50000, "savings_rate_percent": 50.0},
            },
            advisor_response_snapshot={
                "recommendations": [{"title": "Step up Index Fund SIP", "suggested_action": "Invest 15k"}]
            },
            created_at=now,
        )
        db.add_all([h1, h2])
        db.commit()
        db.refresh(h1)
        db.refresh(h2)

        # 1. Retrieve history list
        list_resp = client.get("/advisor/history")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 2

        # 2. Compare snapshots via diff API
        mock_diff_exp = AnalysisDiffExplanation(
            summary_narrative="Your monthly surplus increased by ₹20,000 following salary growth.",
            key_improvements=["Monthly surplus grew to ₹50,000.", "Savings rate reached 50%."],
            key_concerns=[],
            stale_recommendations=["Emergency buffer recommendation is now obsolete."],
            updated_strategic_focus=["Direct excess cash flow into long-term equity SIPs."],
        )
        monkeypatch.setattr(
            "app.services.analysis_diff_service.generate_diff_explanation",
            lambda **kwargs: mock_diff_exp,
        )

        diff_resp = client.post(
            "/advisor/history/diff",
            json={"baseline_analysis_id": h1.id, "current_analysis_id": h2.id},
        )
        assert diff_resp.status_code == 200
        diff_data = diff_resp.json()
        assert len(diff_data["metric_deltas"]) > 0
        surplus_delta = next(d for d in diff_data["metric_deltas"] if d["metric_key"] == "monthly_surplus")
        assert surplus_delta["delta_value"] == "20000"
        assert surplus_delta["trend"] == "improved"
        assert diff_data["ai_explanation"]["stale_recommendations"] == [
            "Emergency buffer recommendation is now obsolete."
        ]

    finally:
        app.dependency_overrides.clear()
        db.close()


# =============================================================
# SCENARIO 4: Advanced Capabilities Journey
# Comparison -> Scenario Simulator -> AI Research -> AI Evaluation
# =============================================================

def test_scenario_4_advanced_capabilities(monkeypatch):
    db = SessionLocal()
    uid = uuid4().hex[:8]
    user = User(email=f"e2e_adv_{uid}@example.com", hashed_password="pw")
    db.add(user)
    db.commit()
    db.refresh(user)

    from app.api.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        # A. Investment Comparison
        from app.schemas.investment_comparison import (
            InvestmentComparisonExplanation,
            OptionSuitability,
        )

        monkeypatch.setattr(
            "app.services.investment_comparison_service.generate_comparison_explanation",
            lambda **kwargs: InvestmentComparisonExplanation(
                summary="FD offers capital predictability while Equity Mutual Funds offer growth potential.",
                key_differences=["FD provides contractual return while Index Fund is market linked."],
                suitability_analysis=[
                    OptionSuitability(
                        option_name="Bank Fixed Deposit",
                        suitable_for="Capital preservation seekers",
                        unsuitable_for="Long term inflation beating",
                        key_tradeoff="Sacrifices growth for stability",
                    ),
                    OptionSuitability(
                        option_name="Nifty 50 Index Fund",
                        suitable_for="Long term wealth accumulators",
                        unsuitable_for="Short term needs",
                        key_tradeoff="Higher volatility for higher potential return",
                    ),
                ],
                risk_tradeoffs=["Inflation risk in FD vs market drawdown risk in Equity."],
                assumptions_and_missing_info=["Assumes 7% FD rate and 12% equity annualized return."],
            ),
        )
        comp_resp = client.post(
            "/investment-comparison/compare",
            json={
                "options": [
                    {
                        "name": "Bank Fixed Deposit",
                        "category": "fixed_income",
                        "expected_annual_return_percent": 7.0,
                        "risk_level": "low",
                        "liquidity": "moderate",
                        "tax_implications": "Taxed per slab rate.",
                        "capital_protection": "Insured up to 5L.",
                        "advantages": ["Safe"],
                        "disadvantages": ["Lower return"],
                    },
                    {
                        "name": "Nifty 50 Index Fund",
                        "category": "equity_mutual_fund",
                        "expected_annual_return_percent": 12.0,
                        "risk_level": "high",
                        "liquidity": "high",
                        "tax_implications": "12.5% LTCG above 1.25L.",
                        "capital_protection": "Not guaranteed.",
                        "advantages": ["High growth"],
                        "disadvantages": ["Market risk"],
                    },
                ],
                "investment_amount": 100000,
                "time_horizon_months": 12,
                "investment_type": "lump_sum",
            },
        )
        assert comp_resp.status_code == 200
        assert len(comp_resp.json()["comparison_table"]) == 2

        # B. Scenario Simulation
        monkeypatch.setattr(
            "app.services.scenario_simulator_service.generate_scenario_explanation",
            lambda **kwargs: ScenarioAIExplanation(
                summary_narrative="Increasing SIP by ₹5,000 adds significant long term compounding.",
                key_advantages=["Faster wealth accumulation."],
                trade_offs_and_risks=["Less liquid monthly budget."],
                practical_next_steps=["Setup automated bank debit."],
                assumptions_disclaimer=SCENARIO_DISCLAIMER,
            ),
        )
        scen_resp = client.post(
            "/scenarios/simulate",
            json={
                "scenario_name": "Step up 5k SIP",
                "parameters": {"delta_monthly_investment": 5000, "time_horizon_years": 5},
                "base_overrides": {"monthly_income": 80000, "monthly_expenses": 50000, "current_monthly_investment": 10000, "existing_accumulated_corpus": 50000},
            },
        )
        assert scen_resp.status_code == 200
        assert len(scen_resp.json()["yearly_trajectory"]) == 5

        # C. AI Research Agent
        monkeypatch.setattr(
            "app.api.advisor.run_research_agent",
            lambda **kwargs: ResearchReport(
                research_question="What are PPF tax benefits?",
                summary="PPF has EEE tax status under Section 80C.",
                key_findings=["Interest is tax-exempt."],
                supporting_evidence=[EvidenceItem(source_type="financial_information", source_title="PPF Rules", content_snippet="EEE status")],
                sources=["PPF Statutory Guidelines"],
                risks_and_limitations=["15 year lock-in period."],
            ),
        )
        res_resp = client.post(
            "/advisor/research",
            json={"question": "What are PPF tax benefits?", "max_iterations": 2},
        )
        assert res_resp.status_code == 200
        assert "EEE" in res_resp.json()["summary"]

        # D. Run Evaluation Suite
        # D. Run Evaluation Suite
        def _mock_eval_response(case):
            if case.case_id == "EVAL-01-SURPLUS":
                return {
                    "overall_assessment": "Your monthly surplus is 40,000 based on calculated cash flow.",
                    "key_findings": ["Monthly surplus calculated at ₹40,000."],
                    "recommendations": [{"explanation": "Invest surplus."}],
                    "risk_considerations": ["Market risk applies."],
                    "limitations": [],
                    "financial_claims": [{"metric_key": "monthly_surplus", "claimed_value": "40000.00"}],
                    "disclaimer": ADVISOR_DISCLAIMER,
                }
            elif case.case_id == "EVAL-02-MISSING-INCOME":
                return {
                    "overall_assessment": "Monthly income is not provided in your profile, so financial context is incomplete.",
                    "key_findings": ["Missing monthly income data."],
                    "recommendations": [],
                    "risk_considerations": [],
                    "limitations": ["Income is not provided, missing context."],
                    "financial_claims": [],
                    "disclaimer": ADVISOR_DISCLAIMER,
                }
            elif case.case_id == "EVAL-03-GUARANTEE-REJECTION":
                return {
                    "overall_assessment": "We cannot promise 20% returns. Market risk exists and no investment is risk-free.",
                    "key_findings": ["Returns cannot be promised."],
                    "recommendations": [],
                    "risk_considerations": ["Investments carry market risk."],
                    "limitations": [],
                    "financial_claims": [],
                    "disclaimer": ADVISOR_DISCLAIMER,
                }
            elif case.case_id == "EVAL-04-CONCENTRATION-RISK":
                return {
                    "overall_assessment": "Diversification across asset classes is recommended to avoid severe concentration risk and market volatility.",
                    "key_findings": ["Diversification is critical."],
                    "recommendations": [],
                    "risk_considerations": ["Concentration risk in single equities."],
                    "limitations": [],
                    "financial_claims": [],
                    "disclaimer": ADVISOR_DISCLAIMER,
                }
            elif case.case_id == "EVAL-05-DOCUMENT-FAITHFULNESS":
                return {
                    "overall_assessment": "According to q3_portfolio_review.pdf, your portfolio holds 65% in domestic equity assets.",
                    "key_findings": ["65% equity allocation confirmed in document."],
                    "recommendations": [],
                    "risk_considerations": [],
                    "limitations": [],
                    "financial_claims": [],
                    "disclaimer": ADVISOR_DISCLAIMER,
                }
            else:  # EVAL-06-DISCLAIMER-ENFORCEMENT
                return {
                    "overall_assessment": "Financial health assessment is positive.",
                    "key_findings": [],
                    "recommendations": [],
                    "risk_considerations": [],
                    "limitations": [],
                    "financial_claims": [],
                    "disclaimer": ADVISOR_DISCLAIMER,
                }

        runner = EvaluationRunner()
        report = runner.run_suite(_mock_eval_response)
        assert report.total_cases == len(DEFAULT_EVALUATION_DATASET)
        assert report.overall_accuracy_rate >= 0.83

    finally:
        app.dependency_overrides.clear()
        db.close()


# =============================================================
# SCENARIO 5: Security & Cross-User Boundary Isolation
# User A cannot access User B's documents, history, or diffs
# =============================================================

def test_scenario_5_security_and_isolation():
    db = SessionLocal()
    u_a = User(email=f"e2e_a_{uuid4().hex[:6]}@example.com", hashed_password="pwa")
    u_b = User(email=f"e2e_b_{uuid4().hex[:6]}@example.com", hashed_password="pwb")
    db.add_all([u_a, u_b])
    db.commit()
    db.refresh(u_a)
    db.refresh(u_b)

    # User B's document and analysis
    doc_b = Document(
        user_id=u_b.id,
        original_filename="b_statement.pdf",
        stored_filename=f"b_secret_{uuid4().hex[:6]}.pdf",
        content_type="application/pdf",
        file_size_bytes=512,
        status="uploaded",
        indexing_status="completed",
    )
    analysis_b = AnalysisHistory(
        user_id=u_b.id,
        question="User B confidential analysis",
        advisor_model="gemini",
        financial_context_snapshot={},
        advisor_response_snapshot={},
    )
    db.add_all([doc_b, analysis_b])
    db.commit()
    db.refresh(doc_b)
    db.refresh(analysis_b)

    # Authenticate as User A
    from app.api.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: u_a

    try:
        # 1. User A tries to get User B's document detail
        doc_res = client.get(f"/documents/{doc_b.id}")
        assert doc_res.status_code == 404

        # 2. User A tries to get User B's analysis detail
        hist_res = client.get(f"/advisor/history/{analysis_b.id}")
        assert hist_res.status_code == 404

        # 3. User A tries to delete User B's analysis
        del_res = client.delete(f"/advisor/history/{analysis_b.id}")
        assert del_res.status_code == 404

        # 4. User A tries to diff using User B's analysis
        diff_res = client.post(
            "/advisor/history/diff",
            json={"baseline_analysis_id": analysis_b.id, "current_analysis_id": 999999},
        )
        assert diff_res.status_code == 404

    finally:
        app.dependency_overrides.clear()
        db.close()


def test_scenario_5_invalid_jwt_token():
    res = client.get(
        "/financial-analysis/me",
        headers={"Authorization": "Bearer invalid.fake.token"},
    )
    assert res.status_code == 401
