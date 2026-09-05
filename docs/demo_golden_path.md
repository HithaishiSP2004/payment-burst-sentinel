# Payment Burst Sentinel — 5-Minute Evaluator Golden Path

This document provides an exact, reproducible walkthrough designed for a 5-minute video pitch or live evaluator demo. All data points and actions are verified against real repository data.

**Governing Principle:**  
*"Deterministic systems detect. Gemini explains. Humans decide."*

---

## Preparation (30 Seconds)

1. **Start Backend**:
   ```bash
   uvicorn backend.api:app --host 0.0.0.0 --port 8000
   ```
2. **Start Frontend**:
   ```bash
   cd frontend && npm run dev
   ```
3. Open browser to: `http://localhost:3000`

> **Note on Deployment**: Track 02 submission requires a public repo, 5-minute pitch video, and architecture. Live cloud deployment is optional. This golden path runs against the clean local development setup.

---

## The 8-Step Walkthrough

### Step 1: System Overview (Monitor Screen)
- **Navigation**: Home screen (`/` or click `Monitor` in sidebar).
- **What Evaluator Sees**:
  - Hero statistics: **693** Merchants Monitored, **337,151** Merchant-Days Analyzed, **42,665** Total Flagged Events.
  - **7.13× Enrichment Card**: Explaining that flagged days are 7.13× more likely to contain fraud-tagged transactions than behaviorally normal days.
  - **Live Behavioral Stream**: Monitored merchants sorted by severity.
- **Presenter Script**:
  > *"Payment Burst Sentinel is a defensive risk intelligence system built for Razorpay Track 02. Traditional fraud engines rely on static volume thresholds, but what is normal varies wildly per merchant. We model each merchant against their own rolling 30-day behavioral baseline using median and median absolute deviation. Our held-out evaluation demonstrates a 7.13× fraud concentration in flagged days compared to normal days."*

---

### Step 2: Investigation Index (Investigations Screen)
- **Navigation**: Click `Investigations` in sidebar.
- **What Evaluator Sees**:
  - Filter chips for `Risk` (`All`, `High`, `Elevated`) and `Signal` (`All`, `Amount`, `Volume`, `Combined`).
  - Paginated list of 16,090 test-period deviations with clear deviation indicators.
- **Action**: Click the `High` risk filter chip.
- **Presenter Script**:
  > *"Here in the Investigations Index, analysts can instantly prioritize severe deviations. Notice every item exposes its primary signal—such as payment value or transaction volume—alongside the exact statistical deviation in MADs."*

---

### Step 3: Evidence-First Workspace (Investigation Detail)
- **Navigation**: Click on the first high-severity anomaly: **Kovacek Ltd** (`2020-11-27`).
- **What Evaluator Sees**:
  - **01 Header**: Factual classification tags (HIGH, Amount Anomaly), reference ID, and provenance (`Frozen Historical Data`).
  - **02 Executive Snapshot**: Four factual cards showing Observed Value (₹19,365), Expected Baseline (~₹11), Deviation (+1935.4 MADs), and Baseline History (25/30 days used).
- **Presenter Script**:
  > *"When an analyst clicks an investigation, they enter the Phase 18 Evidence Workspace. Notice that before any AI is invoked, the deterministic evidence is front and center: Kovacek Ltd typically processes ₹11 per day; on November 27th, it spiked to ₹19,365—an 1801× deviation above its baseline."*

---

### Step 4: Primary Evidence vs. Context & Factual Statements
- **Navigation**: Scroll down through Sections 03, 04, 05, and 06.
- **What Evaluator Sees**:
  - **01 Primary Detection Evidence**: Relative Magnitude Comparison Meter showing baseline vs observed burst.
  - **02 Behavioral Context**: Transaction volume remained at 1 tx (normal volume, extreme amount anomaly).
  - **03 Factual Detection Statements**: Bulleted factual statements derived strictly from frozen data.
  - **04 Detection Signal Map**: 3 grouped cards: Confirmed Evidence, Analytical Context, and System Boundaries.
- **Presenter Script**:
  > *"We separate the primary reason for detection from contextual signals. The transaction count was normal at 1 transaction, meaning this wasn't a transaction burst, but a high-ticket payment value anomaly. System boundaries clearly confirm that external ingestion was not involved and automated action was not triggered."*

---

### Step 5: Gemini AI Advisory Brief & Fallback Handling
- **Navigation**: Scroll to **05 AI Investigation Intelligence**.
- **Action**: Click `Generate AI Brief`.
- **What Evaluator Sees**:
  - **If `GEMINI_API_KEY` is present**: Generates a structured brief with Headline, Summary, What Changed (with stable references `E1`–`E6`), Key Evidence, Investigate Next, What Remains Unknown, and Safety Note.
  - **If `GEMINI_API_KEY` is absent**: Gracefully displays the `AI NOT CONFIGURED` fallback panel explaining that deterministic evidence remains 100% available.
- **Presenter Script**:
  > *"Gemini is strictly an explainer. It receives structured evidence items E1 through E6 behind 7 deterministic safety guardrails. It cannot declare confirmed fraud, cannot alter detection thresholds, and cannot autonomously block accounts. And if the AI service is offline or unconfigured, the system degrades gracefully with zero downtime."*

---

### Step 6: Human Decision Boundary
- **Navigation**: Scroll to **06 System Boundary (Human Decision Boundary)**.
- **What Evaluator Sees**:
  - Prominent boundary card with explicit guidance: *"Automated fraud classification, merchant blocking, and transaction enforcement are disabled. Final assessment remains a human decision."*
  - Action buttons: `View Merchant Rhythm →`, `View Detection Evaluation →`, `← Back to Investigations Index`.
- **Action**: Click `View Merchant Rhythm →`.
- **Presenter Script**:
  > *"The human analyst always makes the final call. From here, the analyst can seamlessly navigate to inspect the merchant's 90-day rhythm or review platform-wide evaluation."*

---

### Step 7: Merchant Rhythm (90-Day Behavioral Timeline)
- **Navigation**: On the `Merchant Rhythm` screen.
- **What Evaluator Sees**:
  - Interactive daily bar chart of the past 90 days.
  - Expected baseline median and variability range.
  - High-risk burst days highlighted in warm accent colors.
- **Presenter Script**:
  > *"The Merchant Rhythm screen visualizes the merchant's historical transaction cadence. Analysts can spot intermittent seasonality versus genuine anomalous bursts."*

---

### Step 8: Detection Evaluation & Workload Cost Modeling
- **Navigation**: Click `Evaluation` in sidebar.
- **What Evaluator Sees**:
  - **Section 01–03**: 8-section Evaluation Workspace showing 693 merchants, 126,574 test days, **7.13× enrichment vs normal**, and **50.93% Proxy-Positive Coverage**.
  - **Section 04**: Proxy Outcome Cross-Tabulation (Confusion Matrix: 1,069 TP, 15,021 FP, 1,030 FN, 109,454 TN).
  - **Section 07**: **Scenario-Based Investigation Workload Model** with Lean, Standard, and Intensive scenarios.
- **Presenter Script**:
  > *"We believe in transparent evaluation. We do not claim 99% fraud precision because anomaly is not fraud. Instead, we show that flagged days capture 50.9% of proxy fraud days with a 7.13× enrichment, and we provide an interactive cost model so risk leaders can quantify the operational workload of reviewing 15 alerts per positive day."*

---

### Step 9: Integration Readiness & Simulated Demo
- **Navigation**: Click `Integration` in sidebar.
- **Action**: Click `Ingest Demo Event`.
- **What Evaluator Sees**:
  - Provider abstraction flow (Provider → Validation → Canonical Event → STOP).
  - Normalized event output with UTC timestamp, Decimal amount, and idempotency status.
  - Explicit STOP boundary confirming: *"Historical Data: NOT MODIFIED · Detection: NOT TRIGGERED · AI Analysis: NOT TRIGGERED"*.
  - Clear badge: `ADAPTER READY ≠ CONNECTED`.
- **Presenter Script**:
  > *"Finally, the Integration Workspace demonstrates readiness for the Razorpay ecosystem. External payments are normalized into a canonical Decimal schema and checked for idempotency. The adapter is ready, but strictly isolated—external events never contaminate the analytical core."*

---

## Golden Path Summary Table

| Step | Target Screen | Primary Feature | Key Evaluator Takeaway |
| :---: | :--- | :--- | :--- |
| **1** | Monitor | 7.13× Enrichment Card | Behavioral baseline beats volume thresholds |
| **2** | Investigations | Risk & Signal Filters | Rapid triage of 16,000+ deviations |
| **3** | Investigation Detail | Executive Evidence Snapshot | Real data: ₹19,365 vs ₹11 expected |
| **4** | Investigation Detail | Signal Map & Boundaries | Amount burst isolated from volume |
| **5** | Investigation Detail | Gemini Brief / Fallback | Structured AI explainer with 7 guardrails |
| **6** | Investigation Detail | Human Decision Boundary | Defense-only; human retains decision |
| **7** | Merchant Rhythm | 90-Day Timeline Chart | Contextual historical rhythm |
| **8** | Evaluation | Confusion Matrix & Cost Model | Honest 50.93% coverage & workload modeling |
| **9** | Integration | Demo Ingestion Simulator | Canonical normalization with strict isolation |
