# AI Integration Boundary — Payment Burst Sentinel

> **Phase 14 Architecture → Phase 15 Implemented**
>
> This document was created in Phase 14. The AI integration has been
> **fully implemented in Phase 15** using the `google-genai` SDK with
> Gemini structured output. See `docs/phase15_ai_investigation_intelligence.md`
> for the complete implementation reference.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│           LAYER 1 — LOCKED CORE              │
│                                              │
│  Phase 3 Baseline Engine                     │
│  Phase 4 Anomaly Detector                    │
│  Phase 5 Evaluation                          │
│                                              │
│  ❌ NO CHANGES                               │
└──────────────────────────────────────────────┘
                    ↓
          READ-ONLY ANALYTICS
                    ↓
┌──────────────────────────────────────────────┐
│      LAYER 2 — SUBMISSION EVALUATION         │
│                                              │
│  Proxy Precision / Recall / F1               │
│  Confusion Matrix                            │
│  Alert Efficiency                            │
│  Investigation Burden                        │
│  Scenario Cost Modeling                      │
│                                              │
│  ✓ DERIVED ONLY                              │
└──────────────────────────────────────────────┘
                    ↓
            STRUCTURED EVIDENCE
                    ↓
┌──────────────────────────────────────────────┐
│          LAYER 3 — AI FOUNDATION             │
│                                              │
│  AI Provider Abstraction                     │
│  Evidence Contract                           │
│  Gemini Integration Boundary                 │
│                                              │
│  ❌ DOES NOT MODIFY DETECTION                 │
└──────────────────────────────────────────────┘
```

---

## Structured Evidence Contract

### AI Input — What Gemini Receives

Gemini receives **structured, deterministic evidence only**. It does NOT
query parquet files, databases, or raw data directly.

```json
{
  "merchant": "Kovacek Ltd",
  "date": "2020-12-27",
  "risk_level": "high",
  "anomaly_type": "combined_anomaly",
  "transaction_count": 10,
  "expected_tx_count": 4,
  "tx_variability": 1.2,
  "velocity_deviation": 6.0,
  "total_amount": 724.95,
  "expected_total_amount": 245.14,
  "amount_variability": 85.3,
  "amount_deviation": 6.77,
  "composite_deviation": 6.77,
  "historical_days_used": 30,
  "baseline_status": "sufficient_history",
  "deterministic_evidence": [
    "Payment value ₹724.95 vs expected ~₹245.14 (+6.77 MADs)",
    "Transaction count 10 vs expected ~4 (+6.0 MADs)",
    "Both signals exceeded elevated threshold (4.0 MADs)",
    "Merchant has 30 days of behavioral history"
  ]
}
```

### AI Output — What Gemini May Produce

```json
{
  "investigation_summary": "...",
  "key_behavioral_change": "...",
  "recommended_review_questions": ["..."],
  "confidence_limitations": ["..."]
}
```

### AI Output — What Gemini Must NEVER Produce

| Forbidden Output         | Reason                                      |
|--------------------------|---------------------------------------------|
| `fraud_probability`      | System detects anomalies, not fraud          |
| `approve_payment`        | No autonomous financial action               |
| `decline_payment`        | No autonomous financial action               |
| `block_merchant`         | No autonomous financial action               |
| `freeze_account`         | No autonomous financial action               |

---

## 5 Non-Negotiable AI Rules

### Rule 1 — AI Cannot Alter Detection

Gemini cannot modify:
- Deviation scores
- Thresholds
- Risk levels
- Anomaly types
- Baseline calculations

The detection pipeline output is **read-only** to the AI layer.

### Rule 2 — AI Receives Deterministic Evidence

The AI layer must consume the output of the existing analytical pipeline.
Never raw, uncontrolled calculations. The structured evidence contract
above defines the exact data boundary.

### Rule 3 — Failure Isolation

```
Gemini unavailable
        ↓
AI summary unavailable
        ↓
Detection system continues normally
```

AI failure must **never** break the dashboard. The application must remain
fully usable if Gemini is unavailable.

### Rule 4 — No Fabricated Facts

The prompt must explicitly instruct Gemini:

> "Use only supplied evidence. Do not invent transactions, causes,
> merchant history, or fraud outcomes."

Every AI summary must include uncertainty when appropriate.

### Rule 5 — No Autonomous Financial Action

The system flow must always be:

```
DETECT → EXPLAIN → PRIORITIZE → HUMAN REVIEWS
```

Never:

```
DETECT → AUTOMATICALLY BLOCK
```

---

## Gemini Configuration

### Environment Variables

```
GEMINI_API_KEY=            # Required for Phase 15
GEMINI_MODEL=gemini-pro    # Optional: model selection
```

### Security Requirements

- Do NOT hardcode API keys
- Do NOT expose keys to the frontend
- Do NOT commit `.env` files
- Do NOT create client-side Gemini calls
- All AI calls must go through the backend

### Provider Abstraction

Future implementation should support provider abstraction:

```python
class AIProvider(ABC):
    @abstractmethod
    async def summarize_investigation(self, evidence: dict) -> dict:
        ...

class GeminiProvider(AIProvider):
    async def summarize_investigation(self, evidence: dict) -> dict:
        # Gemini-specific implementation
        ...

class FallbackProvider(AIProvider):
    async def summarize_investigation(self, evidence: dict) -> dict:
        # Returns structured evidence without AI summary
        return {"summary": "AI unavailable", "evidence": evidence}
```

---

## Phase 15 Readiness Checklist

- [x] Structured evidence contract defined
- [x] AI input/output boundaries documented
- [x] 5 non-negotiable rules established
- [x] Failure isolation requirement specified
- [x] Provider abstraction architecture documented
- [x] Environment variable preparation complete
- [x] Security requirements documented
- [x] Gemini API key obtained ✅ Phase 15
- [x] Backend AI endpoint implemented ✅ Phase 15
- [x] Frontend AI summary component ✅ Phase 15
