# Payment Burst Sentinel

**A deterministic behavioral anomaly intelligence system that identifies unusual merchant payment bursts, evaluates them transparently, and provides evidence-grounded AI investigation support.**

Built for the **Razorpay AI Buildathon — Track 02: AI Risk Manager**.  
**Repository:** [https://github.com/HithaishiSP2004/payment-burst-sentinel](https://github.com/HithaishiSP2004/payment-burst-sentinel)

---

## 1. Core Principle

> ### **"Deterministic systems detect. Gemini explains. Humans decide."**

Payment Burst Sentinel enforces a strict, defense-only boundary for payment platforms:
- **The detection pipeline is fully deterministic**: Frozen statistical algorithms compute rolling historical merchant baselines and flag behavioral anomalies.
- **AI is strictly advisory**: Google Gemini receives structured, deterministic evidence to explain anomalies, synthesize changes, and suggest defensive investigation questions.
- **Humans make the final decision**: The platform never autonomously blocks payments, freezes accounts, or cancels transactions.

---

## 2. The Problem

Traditional payment fraud detection systems that rely on static thresholds or aggregate volume miss a fundamental reality: **what is "normal" differs per merchant.**

- A ₹50,000 daily volume is routine for a mid-market retailer but extraordinary for a micro-merchant.
- In our exploratory analysis of historical transaction data, **high transaction volume alone was not strongly associated with fraud**.
- Static aggregate rules flood risk operations with false positives on large merchants while missing subtle bursts in smaller ones.

**The Solution:** Model each merchant against their own historical baseline rather than platform-wide assumptions.

---

## 3. What the System Does

```
Historical Payment Transactions (693 merchants, 337,151 merchant-days)
         ↓
Rolling 30-Day Behavioral Baseline Engine (Median + MAD per merchant)
         ↓
Deterministic Anomaly Detector (Velocity & Amount Deviation; Elevated ≥4, High ≥5)
         ↓
Held-Out Temporal Evaluation (Enrichment, Proxy-Positive Coverage, Cost Modeling)
         ↓
FastAPI Intelligence API (Port 8000: Parquet-backed, read-only analytics)
         ↓
Next.js 16 Investigation Interface (6 interactive forensic screens)
         ↓
Gemini AI Advisory Brief (Optional, evidence-grounded, 7 safety guardrails)
         ↓
Human Analyst Decision (Final risk review & platform action)
```

---

## 4. Key Results

All evaluation metrics are computed on a temporal held-out test split (126,574 merchant-days) with frozen detection thresholds:

| Metric | Measured Value | Meaning |
| :--- | :---: | :--- |
| **Enrichment vs. Normal** | **7.13×** | Flagged merchant-days contain proxy fraud labels at 7.13× the rate observed on behaviorally normal merchant-days (6.644% vs. 0.932%). |
| **Enrichment vs. Overall** | **4.01×** | Flagged merchant-days have a 4.01× higher fraud concentration than the overall merchant-day population (6.644% vs. 1.658%). |
| **Proxy-Positive Recall** | **50.93%** | Percentage of fraud-containing merchant-days captured by behavioral flags (1,069 / 2,099). |
| **Alert Efficiency** | **15.05 alerts / positive day** | Total alerts generated per fraud-containing day captured (16,090 alerts / 1,069 captured days). |
| **Behavioral vs. Volume Baseline** | **7.13× vs. 1.83×** (3.9× ratio) | Behavioral enrichment: 7.13× vs. 1.83× for the naive volume-only baseline — a 3.9× enrichment ratio. |

> **Important Methodology Distinction:**  
> These are **merchant-day proxy metrics**. Payment Burst Sentinel is a behavioral anomaly intelligence system, **not** a transaction-level fraud classifier. Transaction fraud tags serve as a proxy ground truth to validate behavioral burst correlation.

---

## 5. How Detection Works

Every merchant receives a customized behavioral baseline calculated across a **rolling 30-day historical window**:

1. **Robust Central Tendency**: Uses **Median** rather than mean, resisting skew from previous transaction spikes.
2. **Robust Variability**: Uses **MAD (Median Absolute Deviation)**:
   $$\text{MAD} = \text{median}(|x_i - \text{median}(X)|)$$
   Scaled to estimate normal standard deviation ($\times 1.4826$).
3. **Dual-Signal Upward Deviation**:
   - **Transaction Velocity Deviation**: Number of transactions vs. merchant's norm.
   - **Payment Value Deviation**: Total payment volume vs. merchant's norm.
4. **Composite Score**: $\text{Composite} = \max(\text{velocity\_deviation}, \text{amount\_deviation})$
5. **Detection Thresholds**:
   - **Normal**: $< 4.0\text{ MADs}$ (within typical behavioral variability)
   - **Elevated Risk**: $\ge 4.0\text{ MADs}$ (unusual statistical deviation)
   - **High Risk**: $\ge 5.0\text{ MADs}$ (severe behavioral burst)

---

## 6. Product Experience (Screens)

Payment Burst Sentinel provides a unified, dark-mode forensic workspace consisting of 6 dedicated screens:

| Screen | Purpose & Capabilities |
| :--- | :--- |
| **1. Monitor** | Executive system overview: monitored merchant count (693), behavioral deviation breakdown, 7.13× enrichment card, and prioritized live deviation stream. |
| **2. Investigations Index** | Filterable, paginated index of flagged merchant-days. Filter by risk level (`High`, `Elevated`) and signal type (`Amount`, `Volume`, `Combined`). |
| **3. Investigation Workspace** | **Evidence Workspace**: 8-section deep dive displaying Primary Evidence, Behavioral Context, Relative Magnitude Meter, Factual Statements, Signal Map, Gemini Brief, and Human Decision Boundary. |
| **4. Merchant Rhythm** | 90-day interactive merchant behavioral timeline. Visualizes daily transactions and amounts against expected median and variability ranges. |
| **5. Detection Evaluation** | **Evaluation Workspace**: 8 sections detailing held-out methodology, confusion matrix, proxy metrics, signal dominance, and interactive Scenario Cost Model (Lean / Standard / Intensive). |
| **6. Integration Readiness** | **Integration Workspace**: Provider abstraction flow, canonical event schema (`Decimal`, `UTC`), bounded idempotency, Razorpay HMAC verification boundary, and isolated demo simulator. |

---

## 7. AI Investigation Intelligence

The AI layer transforms raw mathematical deviations into structured, understandable investigation intelligence.

```
Deterministic Evidence (E1–E6) → Prompt Injection Shield → Google Gemini (Flash Cascade) → 7 Guardrails → Cached Brief
```

### What Gemini Does:
- **Explains deterministic evidence**: Synthesizes amount and velocity signals into a cohesive narrative.
- **Identifies what changed**: Highlights specific deviations with stable evidence references (`E1`–`E6`).
- **Surfaces unknowns**: Explicitly identifies missing contextual information.
- **Proposes next steps**: Suggests defensive investigation questions for the risk analyst.

### What Gemini NEVER Does:
- ❌ Does **not** detect anomalies or assign risk levels.
- ❌ Does **not** alter statistical thresholds or baseline calculations.
- ❌ Does **not** declare confirmed fraud as fact.
- ❌ Does **not** autonomously block payments, freeze accounts, or decline transactions.
- ❌ Does **not** access external tools or query live production databases.

### Graceful AI Fallback:
If `GEMINI_API_KEY` is absent, `AI_ENABLED=false`, or external API calls fail, the backend engages `FallbackProvider`. The frontend displays an honest *"AI Not Configured"* notice while **all deterministic evidence and factual statements remain fully available**.

---

## 8. Integration Readiness Layer

Payment Burst Sentinel is architected for integration into payment platforms like Razorpay while maintaining strict isolation from the analytical core:

- **Provider-Neutral Canonical Event**: Enforces `Decimal` amounts (never floating point) and timezone-aware UTC timestamps.
- **Strict Validation**: Validates payload schemas, sizes, and structure.
- **Bounded Idempotency**: In-memory LRU store keyed by `source + source_event_id`.
- **Razorpay Adapter Boundary**: Secure HMAC-SHA256 signature verification code (`hmac.compare_digest`).
- **Simulated Demo Pipeline**: Generates synthetic demo events to prove pipeline behavior.

> **Source Honesty Boundary:**  
> `adapter_ready ≠ connected`. The application clearly states that the Razorpay adapter represents **readiness architecture**, not live merchant connectivity. External demo payloads are labeled **SIMULATED** and **never** alter historical parquet files, update baselines, or trigger detection.

---

## 9. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PAYMENT BURST SENTINEL                             │
│                     Complete Subsystem Architecture                         │
└─────────────────────────────────────────────────────────────────────────────┘

 [ HISTORICAL BENCHMARK DATA ] (IEEE-CIS: 693 merchants, 337,151 merchant-days)
              │
              ▼
 ┌─────────────────────────┐
 │   LOCKED ANALYTICAL     │  • 30-Day Rolling Median + MAD Baselines
 │         CORE            │  • Deterministic Anomaly Detector (Elevated ≥4, High ≥5)
 │       (FROZEN)          │  • Held-Out Evaluation & Scenario Workload Engine
 └────────────┬────────────┘
              │ Read-Only Analytics
              ▼
 ┌─────────────────────────┐      ┌──────────────────────────────────────────┐
 │     FASTAPI BACKEND     │◄────►│  GEMINI ADVISORY LAYER (Phase 15)        │
 │       (Port 8000)       │      │  • Evidence Builder (E1–E6)              │
 └────────────┬────────────┘      │  • 7 Safety Guardrails & Injection Shield│
              │                   │  • Graceful Fallback Provider            │
              │                   └──────────────────────────────────────────┘
              │                   ┌──────────────────────────────────────────┐
              ├──────────────────►│  INTEGRATION READINESS (Phase 16)        │
              │                   │  • Canonical Event Schema (Decimal, UTC) │
              │                   │  • Bounded Idempotency Store             │
              │                   │  • Razorpay HMAC Signature Boundary      │
              │                   │  • Isolated Demo Ingestion (SIMULATED)   │
              │                   │    [STOP: Never alters analytical core]  │
              │                   └──────────────────────────────────────────┘
              ▼ HTTP / JSON
 ┌─────────────────────────┐
 │    NEXT.JS 16 FRONTEND  │  • Monitor Screen (Overview & Hero Cards)
 │       (Port 3000)       │  • Investigations Index (Filtering & Pagination)
 │                         │  • Investigation Workspace (8-Section Forensic View)
 └────────────┬────────────┘  • Merchant Rhythm (90-Day Interactive Timeline)
              │               • Detection Evaluation (8-Section Proxy Analysis)
              │               • Integration Workspace (Readiness Flow & Demo)
              ▼
 ┌─────────────────────────┐
 │  HUMAN DECISION BOUNDARY│  "Deterministic systems detect. Gemini explains.
 │      (DEFENSE-ONLY)     │   Humans decide."
 └─────────────────────────┘
```

---

## 10. Quick Start

### Prerequisites
- Python 3.10+
- Node.js 20+
- npm 10+

### 1. Clone & Backend Setup

```bash
# Clone the repository
git clone https://github.com/HithaishiSP2004/payment-burst-sentinel.git
cd payment-burst-sentinel

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (optional)
cp .env.example .env
# Edit .env to add GEMINI_API_KEY if testing live AI features

# 4. Start backend server
uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

Verify backend health: [http://localhost:8000/api/overview](http://localhost:8000/api/overview)

### 2. Frontend Setup

```bash
# In a separate terminal, from project root
cd frontend

# 1. Install dependencies
npm install

# 2. Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 11. Environment Variables

Configure via `.env` in the project root:

| Variable | Required | Default | Purpose |
| :--- | :---: | :---: | :--- |
| `GEMINI_API_KEY` | Optional | *(none)* | Google AI Studio API key for Gemini advisory briefs. Application functions fully without it. |
| `GEMINI_MODEL` | Optional | `gemini-3.8-flash,gemini-3.7-flash,gemini-3.5-flash,gemini-3.5-flash-lite,gemini-2.5-flash` | Configurable primary model or priority fallback cascade. Automatically cascades to next model on rate limits or service unavailability. |
| `AI_ENABLED` | Optional | `true` | Set to `false` to disable AI endpoints completely. |
| `ALLOWED_ORIGINS` | Optional | `*` | Comma-separated list of allowed CORS origins. Unset allows all origins for local development. |
| `INTEGRATION_MODE` | Optional | `dataset` | Data mode: `dataset` (default), `demo`, `sandbox`. |
| `RAZORPAY_INTEGRATION_ENABLED` | Optional | `false` | Readiness flag for Razorpay adapter boundary. |
| `RAZORPAY_WEBHOOK_SECRET` | Optional | *(none)* | Secret used for HMAC-SHA256 signature verification tests. |
| `NEXT_PUBLIC_API_BASE_URL` | Optional | `http://localhost:8000` | Frontend backend API target (set in `frontend/.env.local`). |

---

## 12. Testing & Quality Verification

All tests run locally and in GitHub Actions CI:

```bash
# Backend test suite (78 tests)
python -m pytest tests/ -v

# Frontend test suite (181 tests)
cd frontend
npm test

# Frontend production build validation
npm run build
```

### Current Test Baseline:
- **Backend**: **78 / 78 passing** (`tests/test_integration.py`, `tests/test_phase14_evaluation.py`, `tests/test_ai_provider.py`)
- **Frontend**: **181 / 181 passing** across 10 test suites in Vitest
- **Total Automated Tests**: **259 / 259 passing**
- **Production Build**: Next.js 16.3.3 Turbopack build succeeds with zero errors

### Continuous Integration (CI):
GitHub Actions workflow (`.github/workflows/ci.yml`) runs on push and PR:
- **Frontend Job**: `npm ci` → `npm test` → `npm run test:coverage` → `npm run build`
- **Backend Job**: `pip install -r requirements.txt` → `python -m pytest tests/ -v` → import validation

---

## 13. Limitations & Transparency

1. **Historical Benchmark Data**: Built upon historical transaction data derived from the IEEE-CIS benchmark; does not reflect live streaming production traffic.
2. **Merchant-Day Proxy Evaluation**: Fraud labels exist at the individual transaction level; their presence within a merchant-day is utilized as a proxy indicator for evaluating burst correlation.
3. **Not a Fraud Classifier**: The system detects behavioral anomalies and payment bursts. Anomaly $\ne$ fraud.
4. **Scenario-Based Cost Modeling**: The investigation cost model applies illustrative review-time assumptions (e.g. 15 mins @ ₹500/hr) to model operational burden; these are not internal Razorpay cost figures.
5. **Readiness Boundary Only**: The Razorpay adapter demonstrates payload validation, canonical mapping, and signature verification. It does not connect to live merchant accounts or process live funds.
6. **Advisory AI**: Gemini explains deterministic evidence. It cannot alter detection thresholds, reclassify events, or initiate actions.
7. **Human Review Mandatory**: All operational and financial mitigation decisions remain under the sole authority of human risk analysts.

---

## 14. Project Structure

```
payment-burst-sentinel/
├── backend/
│   ├── ai/                      # Gemini AI Advisory Layer (Phase 15)
│   │   ├── gemini_provider.py   # Native structured output with Pydantic
│   │   ├── fallback_provider.py # Graceful unconfigured fallback
│   │   ├── guardrails.py        # 7 post-generation safety validations
│   │   ├── prompt_builder.py    # Injection-resistant system & user prompts
│   │   ├── evidence_builder.py  # Stable evidence mapping (E1–E6)
│   │   └── service.py           # Orchestration & caching layer
│   ├── integrations/            # Integration Readiness Layer (Phase 16)
│   │   ├── schemas.py           # CanonicalPaymentEvent (Decimal, UTC)
│   │   ├── razorpay_adapter.py  # HMAC-SHA256 signature verification boundary
│   │   ├── validator.py         # Payload schema & size validation
│   │   ├── idempotency.py       # Bounded in-memory idempotency store
│   │   └── demo_provider.py     # Isolated synthetic demo pipeline
│   ├── anomaly_detector.py      # [FROZEN] Upward deviation detector (Phase 4)
│   ├── baseline_engine.py       # [FROZEN] Rolling 30-day median+MAD (Phase 3)
│   ├── evaluation.py            # [FROZEN] Held-out evaluation logic (Phase 5/14)
│   ├── config.py                # [FROZEN] Project constants & schemas
│   └── api.py                   # FastAPI application & route handlers
├── frontend/
│   ├── app/                     # Next.js App Router (page.tsx, layout.tsx)
│   ├── components/
│   │   ├── screens/             # 6 forensic screens (Monitor, Workspace, etc.)
│   │   ├── ai/                  # AIInvestigationBrief component
│   │   ├── layout/              # Sidebar & mobile navigation
│   │   └── shared/              # Loading, empty, and error states
│   ├── lib/                     # API client & utility functions
│   ├── types/                   # TypeScript interfaces
│   └── tests/                   # 181 Vitest & React Testing Library tests
├── data/
│   └── processed/               # [FROZEN] Parquet & JSON analytical outputs
├── docs/                        # Architectural documentation, golden path & pitch script
├── tests/                       # 78 Pytest backend integration tests
├── .github/workflows/ci.yml     # Automated CI pipeline
├── requirements.txt             # Python backend & test dependencies
└── .env.example                 # Environment configuration template
```

---

## 15. Evolution History

| Phase | Milestone Description | Status |
| :---: | :--- | :---: |
| **0–2** | Foundation, Data Ingestion, and Exploratory Data Analysis. Proved volume alone is uninformative for fraud. | ✅ Complete |
| **3** | Rolling 30-Day Behavioral Baseline Engine (Median + MAD per merchant). | ✅ Complete (Locked) |
| **4** | Dual-Signal Behavioral Anomaly Detection Engine (Velocity + Amount; Elevated ≥4, High ≥5). | ✅ Complete (Locked) |
| **5** | Held-Out Temporal Evaluation Methodology (Enrichment metrics, zero test tuning). | ✅ Complete (Locked) |
| **6–9** | FastAPI Backend, Next.js Foundation, Visual Refinement, Component Architecture. | ✅ Complete |
| **10–13**| Automated Testing, Continuous Integration, Environment Hardening, and Production Configuration. | ✅ Complete |
| **14** | False-Positive Cost Engine, Proxy Confusion Matrix, Investigation Workload Model. | ✅ Complete (Locked) |
| **15** | Gemini AI Investigation Intelligence Layer (Structured output, E1–E6, 7 safety guardrails). | ✅ Complete |
| **16** | Razorpay Ecosystem Integration Readiness (Canonical schema, HMAC boundary, demo ingestion). | ✅ Complete (Locked) |
| **17** | Product UI Precision, Responsive Layout Stabilization, Architecture Flow Polish. | ✅ Complete |
| **18** | Investigation Evidence Workspace (8-section forensic investigation deep-dive). | ✅ Complete |
| **19** | Detection Evaluation Workspace (8-section proxy metric hardening, cross-tabulation). | ✅ Complete |
| **Final** | Submission Audit & Lockdown (Truth audit, metric consistency, pitch script, verified public repo lock). | ✅ Complete |

---

## 16. Submission Note

Payment Burst Sentinel was engineered for the **Razorpay AI Buildathon (Track 02: AI Risk Manager)** as a defensive, transparent financial risk intelligence platform. The complete submission showcase consists of the public repository, the 5-minute pitch video (`docs/final_5_minute_pitch_script.md`), and the verified subsystem architecture. Rather than making unsubstantiated claims of autonomous AI fraud prevention, it demonstrates how deterministic statistical baselines and grounded AI explanation work together to empower human risk analysts to make fast, informed decisions.
