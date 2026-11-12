# AI Investment Advisor — Production-Grade Autonomous Wealth Advisory System

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Gemini](https://img.shields.io/badge/Google%20GenAI-Gemini%202.5%20%2F%201.5-4285F4.svg)](https://ai.google.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Orchestration-orange.svg)](https://www.langchain.com/langgraph)
[![Tests](https://img.shields.io/badge/Tests-167%20Passed%20%28100%25%29-brightgreen.svg)](#test-suite--quality-metrics)

An enterprise-ready, evidence-grounded AI Investment Advisory platform. Built with **FastAPI**, **PostgreSQL with pgvector**, **Google Gemini SDK (`google-genai`)**, and **LangGraph**. Designed from the ground up for strict regulatory compliance, mathematical determinism, and zero-hallucination guarantees.

---

## Key Highlights & Architectural Pillars

1. **Deterministic Financial Math First**: All numerical metrics (SIP future value, lump-sum compounding, surplus, debt-to-income, goal shortfalls) are computed deterministically using Python's `Decimal` with exact banker's rounding. The LLM is never permitted to perform ungrounded arithmetic.
2. **Hybrid RAG (Vector + BM25 Full-Text + Reciprocal Rank Fusion)**: Financial documents (PDF statements, portfolios) are parsed, chunked, and embedded into pgvector (768-dim HNSW). Queries run hybrid vector cosine similarity + PostgreSQL full-text search (`to_tsvector`), fused via RRF and reranked by Gemini.
3. **Multi-Layer Guardrail & Evidence Grounding Engine**:
   - **Verifiable Chunk ID Enforcement**: Every recommendation citing document evidence is verified against database ownership records.
   - **Numerical Claim Coverage**: Every currency amount and percentage in AI explanations must be declared in a structured ledger verified against trusted context.
   - **No-Guarantee & Safety Policy**: Rejection of promises, fixed-return claims on volatile assets, and unhedged concentration risks.
4. **Autonomous AI Research Agent (LangGraph)**: Controlled agentic workflow that gathers external financial guidelines, parses statutory rules (e.g. Section 80C, PPF, Sovereign Gold Bonds), cross-validates sources, and outputs citation-backed reports.
5. **Scenario Simulation Engine**: Simulates hypothetical adjustments (SIP step-ups, income shifts, expense spikes, return variations) and generates year-by-year compounding trajectories.
6. **Analysis History & Memory Diff**: Tracks snapshots over time and generates deterministic delta comparisons (net worth trajectory, goal progress, risk shifts) with Gemini narrative summaries.
7. **Empirical AI Evaluation Framework**: Automated evaluation suite with 6 benchmark test cases scoring financial accuracy, groundedness, disclaimer compliance, and safety.

---

## Architecture Diagrams

### 1. Overall System Architecture

```mermaid
flowchart TB
    subgraph ClientLayer["Client & Ingestion Layer"]
        User["Investor / Web Client"]
        DocUpload["Document Ingestion (PDFs)"]
    end

    subgraph FastAPILayer["FastAPI Application Gateway"]
        AuthMiddleware["JWT Authentication & RBAC"]
        RateLimiter["Rate Limiting & Correlation ID"]
        Router["API Routers (/advisor, /scenarios, /comparison, etc.)"]
    end

    subgraph CoreServices["Domain & Calculation Engines"]
        ContextService["Financial Context Engine"]
        CalcEngine["Deterministic Calculation Engine (Decimal)"]
        SimulatorService["Scenario Simulation Service"]
        DiffService["Analysis History & Diff Engine"]
        ResearchAgent["LangGraph AI Research Agent"]
    end

    subgraph RAGPipeline["Hybrid RAG & Retrieval Engine"]
        PDFParser["PyMuPDF / PDF Plumber Extractor"]
        Embedder["text-embedding-004 (768d)"]
        HybridSearch["Hybrid Retrieval (HNSW Vector + BM25 tsvector)"]
        RRF["Reciprocal Rank Fusion (k=60)"]
        Reranker["Gemini Contextual Reranker"]
    end

    subgraph Guardrails["Security & Verification Guardrails"]
        ClaimValidator["Numerical Claim Coverage Ledger"]
        EvidenceValidator["Evidence Ownership & State Guard"]
        SafetyValidator["Unsafe Language & Anti-Guarantee Filter"]
    end

    subgraph DataStore["Persistence & AI Services"]
        PG[("PostgreSQL 16 + pgvector (Port 5433)")]
        GeminiAPI["Google Gemini 2.5 / 1.5 Pro via google-genai"]
    end

    User --> AuthMiddleware
    DocUpload --> Router
    AuthMiddleware --> RateLimiter --> Router
    Router --> ContextService & SimulatorService & DiffService & ResearchAgent
    ContextService --> CalcEngine
    Router --> HybridSearch
    HybridSearch --> Embedder --> PG
    HybridSearch --> RRF --> Reranker --> CoreServices
    CoreServices --> GeminiAPI
    GeminiAPI --> Guardrails
    Guardrails --> ClaimValidator & EvidenceValidator & SafetyValidator
    ClaimValidator --> ContextService
    EvidenceValidator --> PG
    Guardrails --> Router
```

### 2. Database Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    users ||--o| profiles : "has"
    users ||--o{ financial_goals : "defines"
    users ||--o{ risk_assessments : "completes"
    users ||--o{ documents : "uploads"
    users ||--o{ analysis_histories : "saves"
    documents ||--o{ document_chunks : "chunked into"

    users {
        int id PK
        string email UK
        string hashed_password
        boolean is_active
        datetime created_at
    }

    profiles {
        int id PK
        int user_id FK,UK
        numeric monthly_income
        numeric monthly_expenses
        numeric savings
        numeric existing_investments
        datetime updated_at
    }

    financial_goals {
        int id PK
        int user_id FK
        string title
        string goal_type
        numeric target_amount
        int time_horizon_months
        numeric planned_monthly_investment
        datetime created_at
    }

    risk_assessments {
        int id PK
        int user_id FK
        jsonb answers
        int risk_score
        string risk_category
        datetime assessed_at
    }

    documents {
        int id PK
        int user_id FK
        string original_filename
        string stored_filename
        string content_type
        int file_size_bytes
        string status
        string indexing_status
        datetime created_at
    }

    document_chunks {
        int id PK
        int document_id FK
        int chunk_index
        int page_number
        text content
        vector embedding "768-dim HNSW"
        tsvector search_vector "GIN Indexed"
    }

    analysis_histories {
        int id PK
        int user_id FK
        jsonb financial_context_snapshot
        jsonb recommendations
        string risk_category
        datetime created_at
    }
```

### 3. AI Advisor Evidence-Grounded Hybrid RAG Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor User as Investor
    participant API as /advisor/analyze
    participant Context as Financial Context Engine
    participant RAG as Hybrid Retrieval (pgvector + BM25)
    participant Rerank as Gemini Reranker
    participant Gemini as Gemini LLM (Structured JSON)
    participant Guard as Output Guardrails & Ledger
    participant DB as PostgreSQL 16

    User->>API: POST /advisor/analyze {"question": "..."}
    API->>Context: build_financial_context(user_id)
    Context->>DB: Fetch Profile, Goals, Risk & compute Metrics (Decimal)
    DB-->>Context: Context Data
    Context-->>API: Validated FinancialContext
    API->>RAG: hybrid_search(query, user_id, top_k=10)
    RAG->>DB: Cosine Vector Search (<=>) & Full-Text Search (@@)
    DB-->>RAG: Vector matches & BM25 matches
    RAG->>API: Fusion Candidates (RRF score)
    API->>Rerank: rerank_chunks(candidates, question)
    Rerank-->>API: Top-5 Verified RerankedChunk
    API->>Gemini: generate_content(System Prompt + Context + Documents)
    Gemini-->>API: AIAdvisorGenerationResponse JSON
    API->>Guard: validate_and_enforce_advisor_output()
    Guard->>Guard: 1. Check prohibited guarantee language
    Guard->>Guard: 2. Verify all numbers declared in claims ledger
    Guard->>Guard: 3. Verify evidence chunks in DB with status='processed'
    Guard-->>API: Verified Advisor Response
    API->>DB: Save snapshot to AnalysisHistory
    API-->>User: 200 OK (Analysis + Verified Claims + Citations + Disclaimer)
```

### 4. LangGraph AI Research Agent Workflow

```mermaid
stateDiagram-v2
    [*] --> PlanResearch : User Question
    PlanResearch --> ExecuteTool : Identify Knowledge Needs
    state ExecuteTool {
        [*] --> FinancialInformationLookup : Instrument Info
        [*] --> MarketContextSearch : Benchmark Data
        [*] --> RegulatoryDatabaseQuery : Tax/RBI/SEBI Guidelines
    }
    ExecuteTool --> EvaluateFindings : Evidence Collected
    EvaluateFindings --> ExecuteTool : Missing Critical Information (iter < max)
    EvaluateFindings --> SynthesizeReport : Sufficient Grounded Evidence
    SynthesizeReport --> ValidateCitations : Check Source Grounding
    ValidateCitations --> [*] : Verified Research Report
```

---

## Technical Decision Rationale

| Architectural Decision | Chosen Solution | Evaluated Alternative | Technical Justification |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** | Flask, Django | High-performance asynchronous support (`asyncio`), automatic OpenAPI / Swagger documentation generation, and native Pydantic V2 data validation. |
| **Vector Storage** | **PostgreSQL + pgvector** | Pinecone, ChromaDB, Weaviate | Unified ACID database for relational profiles and vector embeddings. Eliminates distributed transactions, simplifies cross-user security isolation (`user_id` filters in SQL), and supports HNSW cosine indexes. |
| **Hybrid Search** | **HNSW Vector + BM25 Full-Text + RRF** | Pure Semantic Search | Pure vector search frequently misses exact financial terms (e.g., "Section 80C", "PPF", specific fund tickers). Reciprocal Rank Fusion (RRF $k=60$) balances semantic relevance with lexical precision. |
| **Financial Calculations** | **Python `Decimal`** | Floating-point (`float`), LLM math | Floating-point arithmetic suffers from IEEE 754 precision errors. LLMs frequently hallucinate compounding values. All cash flows, future values, and goal progress are computed deterministically. |
| **LLM Orchestration** | **`google-genai` SDK + LangGraph** | Heavy LangChain monolithic chains | Native Google GenAI SDK offers first-class structured JSON schema enforcement (`response_schema=BaseModel`), rapid inference, and low overhead. LangGraph provides transparent state transitions for multi-step research. |
| **Guardrails & Safety** | **Deterministic Claim & Evidence Ledger** | Pure LLM Self-Reflection | LLMs cannot reliably self-evaluate hallucinations. Hardcoded regex, numerical claim coverage, and database foreign-key checks ensure ungrounded numbers never reach the user. |

---

## API Catalog & Endpoint Reference

Access the interactive Swagger UI at `http://localhost:8000/docs` or ReDoc at `http://localhost:8000/redoc`.

### Authentication & Profile Management
- `POST /auth/register` — Register a new investor account.
- `POST /auth/login` — Authenticate and receive JWT bearer token.
- `GET /profile/me` — Retrieve active investor financial profile.
- `PUT /profile/me` — Create or update monthly income, expenses, liquid savings, and existing investments.

### Financial Goals & Risk Assessment
- `POST /goals` — Create a goal (retirement, emergency fund, education, wealth creation).
- `GET /goals` — List all active goals with target amounts and monthly contribution shortfalls.
- `DELETE /goals/{goal_id}` — Soft/hard delete a goal.
- `POST /risk-assessments` — Submit standardized risk assessment questionnaire (scores 0–20, mapped to `conservative`, `moderate`, `aggressive`).
- `GET /risk-assessments/latest` — Retrieve user's latest risk profile.

### Document Intelligence & Hybrid RAG
- `POST /documents/upload` — Upload financial PDF statement (validates MIME, size, magic bytes).
- `POST /documents/{document_id}/index` — Trigger chunking, embedding generation (`text-embedding-004`), and HNSW indexing.
- `GET /documents` — List uploaded documents and indexing statuses.
- `POST /search/hybrid` — Execute hybrid search across user's documents.

### AI Investment Advisory
- `POST /advisor/analyze` — Request personalized, evidence-grounded investment analysis. Enforces numerical claim ledger and verified citations.
- `POST /advisor/research` — Launch autonomous LangGraph research agent for complex market and regulatory inquiries.

### Investment Comparison & Analysis History
- `POST /investment-comparison/compare` — Compare 2 to 5 options side-by-side with deterministic future value projections and objective Gemini trade-off analysis.
- `GET /analysis-history` — Paginated history of prior advisor analyses.
- `GET /analysis-history/{analysis_id}` — Retrieve specific analysis snapshot.
- `POST /analysis-history/diff` — Compute quantitative delta between two historical snapshots (goal progress, risk shift, net worth change) with AI explanation.

### Financial Scenario Simulator
- `POST /scenarios/simulate` — Simulate hypothetical adjustments (e.g. ₹5,000 SIP increase, 10% income cut) and receive year-by-year compounding trajectory.

---

## Quickstart & Installation Guide

### Prerequisites
- Python 3.11+ (Python 3.13 supported)
- Docker Desktop (for PostgreSQL 16 with pgvector)
- Google Gemini API Key

### 1. Database Setup
Start the PostgreSQL container with pgvector:
```bash
docker compose up -d
```
*PostgreSQL runs on port `5433` (`investment_advisor` database).*

### 2. Virtual Environment & Dependencies
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate  # Windows (or source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
```

### 3. Environment Configuration
Create `backend/.env` (or copy from `.env.example`):
```ini
DATABASE_URL=postgresql+psycopg://investment_user:investment_password@localhost:5433/investment_advisor
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=supersecretjwtkey_min_32_characters_long_for_security
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENVIRONMENT=development
```

### 4. Database Migrations
Apply all Alembic database migrations up to head:
```bash
alembic upgrade head
```

### 5. Start the Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to `http://localhost:8000/docs` to test endpoints via Swagger UI.

---

## Test Suite & Quality Metrics

The test suite covers unit, integration, edge cases, and end-to-end user journeys:
```bash
pytest backend -c backend/pytest.ini -v
```

### Test Coverage Summary (167 Passing Tests)
| Test Category | Test File | Test Count | Status |
| :--- | :--- | :---: | :---: |
| **End-to-End User Journeys** | `test_end_to_end_integration.py` | 6 | **PASSED** |
| **AI Advisor Orchestration & Grounding** | `test_advisor_orchestration.py`, `test_advisor_prompt.py`, `test_advisor_output_validation.py` | 27 | **PASSED** |
| **Financial Calculations & Context** | `test_financial_calculation.py`, `test_financial_context.py`, `test_financial_claim_validation.py` | 24 | **PASSED** |
| **Document Processing & Hybrid RAG** | `test_document_processing.py`, `test_hybrid_retrieval.py`, `test_reranking.py` | 38 | **PASSED** |
| **Scenario Simulator & Projections** | `test_scenario_simulator.py` | 13 | **PASSED** |
| **Investment Comparison & History Diff** | `test_investment_comparison.py`, `test_analysis_history.py`, `test_analysis_diff.py` | 24 | **PASSED** |
| **LangGraph Research Agent** | `test_research_agent.py` | 12 | **PASSED** |
| **AI Evaluation Framework & Benchmarking** | `test_ai_evaluation.py` | 11 | **PASSED** |
| **Backend Hardening & Error Resilience** | `test_backend_hardening.py` | 12 | **PASSED** |
| **Total Test Suite** | **All Modules** | **167** | **100% PASSED** |

---

## Demonstration & Viva Script (Step-by-Step)

Follow this 5-stage workflow for project presentations and technical vivas:

### Stage 1: Investor Onboarding & Deterministic Metrics
1. **Register & Authenticate**: Call `POST /auth/register` and `POST /auth/login`. Obtain the Bearer token.
2. **Setup Financial Profile**: Call `PUT /profile/me` with `monthly_income=100000`, `monthly_expenses=60000`, `savings=200000`.
3. **Submit Risk Assessment**: Call `POST /risk-assessments` with score inputs; system deterministically classifies the investor as `moderate`.
4. **Inspect Context**: Call `GET /financial-analysis/me`. Highlight that `monthly_surplus=40000.00` and `savings_rate_percent=40.00` were computed via `Decimal` without LLM involvement.

### Stage 2: Document Ingestion & Hybrid RAG
1. **Upload Document**: Upload a PDF investment portfolio via `POST /documents/upload`.
2. **Execute Indexing**: Call `POST /documents/{id}/index`. Inspect the log output showing 768-dim embeddings generated and stored into `document_chunks` with HNSW vector and GIN tsvector indexes.
3. **Execute Hybrid Query**: Call `POST /search/hybrid` with question *"What is my asset allocation?"*. Show RRF fusion combining dense vector cosine similarity and sparse keyword ranks.

### Stage 3: Grounded Advisor Analysis & Guardrail Ledger
1. **Run Analysis**: Call `POST /advisor/analyze` with *"How should I allocate my ₹40,000 monthly surplus?"*.
2. **Inspect Guardrail Enforcement**:
   - Point out `financial_claims` ledger in the response verifying that the claimed ₹40,000 matches context `metrics.monthly_surplus`.
   - Point out `evidence` references linking back to verified database chunk IDs.
   - Point out the mandatory statutory disclaimer appended to the output.

### Stage 4: Financial Scenario Simulation & What-If Trajectories
1. **Simulate Step-Up**: Call `POST /scenarios/simulate` with `delta_monthly_investment=5000` over a 5-year horizon.
2. **Compare Trajectories**: Show the baseline corpus vs hypothetical corpus year-by-year compounding table and the objective trade-off explanation.

### Stage 5: LangGraph Autonomous Research Agent
1. **Run Market Inquiry**: Call `POST /advisor/research` with *"What are the tax implications of Sovereign Gold Bonds vs Physical Gold?"*.
2. **Demonstrate Agentic Flow**: Explain how the LangGraph state machine iterated across specialized tools to verify RBI guidelines and Section 80C exemptions without hallucination.

---

## License

This project is developed under the educational and open-source MIT License. Designed for academic and production portfolio evaluation.

