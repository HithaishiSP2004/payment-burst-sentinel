# Payment Burst Sentinel — 5-Minute Video Pitch Script & Presenter Action Guide
## Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager

**Speaker Format:** Spoken walkthrough with step-by-step visual screen actions and click cues.  
**Target Duration:** 4 minutes 45 seconds to 5 minutes (~630 spoken words).  
**Core Thesis:** *"Deterministic systems detect. Gemini explains. Humans decide."*  
**Application URL:** `http://localhost:3000`

---

### [0:00 – 0:30] The Problem & The Hook
* **[🎬 SCREEN ACTION]:** Start on the **`Monitor`** tab (home screen at `http://localhost:3000`).
* **[👀 WHAT TO POINT AT]:** 
  - Point your cursor at the top 3 hero cards: **`693 Merchants Monitored`**, **`337,151 Merchant-Days Analyzed`**, and **`42,665 Flagged Merchant-Days`**.
  - Point directly to the prominent **`7.13× Enrichment Card`** showing the 6.644% vs 0.932% proxy fraud rate.
  - Briefly hover over the **`Live Behavioral Stream`** table below.

**[🎙️ WHAT TO SAY]:**
> "In payments, fraud risk isn't always visible in a single transaction. 
> 
> A merchant can look completely normal transaction by transaction, but its overall payment behavior can suddenly shift. A static global volume threshold can miss that context, because what is 'normal' varies wildly per merchant. Fifty thousand rupees daily might be standard for a supermarket, but extraordinary for a local bakery. 
> 
> When we analyzed historical merchant transaction data, aggregate transaction volume alone was poorly correlated with fraud. 
> 
> Payment Burst Sentinel was built to solve this: a defensive risk intelligence system that establishes individual behavioral rhythms for every merchant, detects statistical bursts, and arms human risk analysts with evidence-grounded AI explanations."

---

### [0:30 – 1:10] Detection Methodology
* **[🎬 SCREEN ACTION]:** In the left sidebar, click the **`Merchant Rhythm`** tab.
* **[👀 WHAT TO POINT AT]:**
  - Point to the quick-select merchant chips at the top (e.g., click or hover over **`Kovacek Ltd`**).
  - Point to the interactive **90-day daily bar chart**:
    - Show the horizontal dotted baseline line representing the **rolling 30-day Median**.
    - Show the shaded band representing the **Median Absolute Deviation (MAD)** variability range.
    - Point to the highlighted amber/red burst bar where the payment volume spikes way above the band.

**[🎙️ WHAT TO SAY]:**
> "Rather than imposing platform-wide static rules, we construct a rolling thirty-day behavioral baseline for each merchant. 
> 
> To handle skewed financial data robustly, we use the median rather than the mean, and the Median Absolute Deviation—or MAD—rather than standard deviation. This prevents past spikes from distorting what the system expects as normal.
> 
> Every day, we evaluate two distinct upward signals: transaction velocity deviation and payment value deviation. 
> 
> If a merchant's burst exceeds four MADs above baseline, we classify it as Elevated Risk. At five MADs or greater, it triggers a High Risk deviation. The mathematics are frozen, deterministic, and fully auditable."

---

### [1:10 – 1:35] Investigations Index
* **[🎬 SCREEN ACTION]:** In the left sidebar, click the **`Investigations`** tab.
* **[👉 CLICK BUTTON]:** Click the **`High`** risk filter chip at the top.
* **[👀 WHAT TO POINT AT]:**
  - Show the filtered index of severe anomalies.
  - Point to the top row: **`Kovacek Ltd`** (`2020-11-27`), highlighting the **`HIGH`** badge, **`Amount Anomaly`** tag, and the statistical deviation **`+1935.4 MADs`**.
* **[👉 CLICK ACTION]:** Click directly on the **`Kovacek Ltd`** row to open the complete Evidence Workspace.

**[🎙️ WHAT TO SAY]:**
> "Here in the Investigations Index, an analyst can immediately prioritize severe anomalies. Notice every item exposes its primary signal—such as payment value or transaction volume—alongside the exact statistical deviation in MADs. Let's open a real deviation from our held-out test set: Kovacek Ltd on November 27th, 2020."

---

### [1:35 – 1:55] Evidence Workspace (Deterministic Facts)
* **[🎬 SCREEN ACTION]:** You are now inside the **`Investigation Evidence Workspace`** for Kovacek Ltd.
* **[👀 WHAT TO POINT AT]:**
  - **Section 02 (Executive Snapshot)**: Point to the 4 factual cards:
    - Observed Value: **`₹19,364.78`**
    - Expected Baseline: **`~₹10.75`**
    - Statistical Deviation: **`+1935.4 MADs`**
    - Baseline History: **`25/30 days`**
* **[📜 SCROLL DOWN]:** Scroll down slightly to **Section 03 & 04**:
  - Point to the **Relative Magnitude Meter** showing an **1801× deviation** above baseline.
  - Point to the **Behavioral Context** showing **Daily Transaction Count: 1 transaction** (normal transaction count, extreme payment value surge).

**[🎙️ WHAT TO SAY]:**
> "Notice what happens before any AI is touched. The Evidence Workspace lays out deterministic facts: 
> 
> Kovacek Ltd typically processes about ten rupees and seventy-five paise per day. On this day, payment volume surged to nineteen thousand, three hundred and sixty-four rupees. That's a deviation of more than nineteen hundred MADs from its baseline.
> 
> Yet its transaction count remained at just one transaction. The system immediately isolates that this was a high-value amount burst, not a volume surge. Every statement is grounded in frozen, verifiable baseline data."

---

### [1:55 – 2:40] Gemini AI Advisory Layer
* **[📜 SCROLL DOWN]:** Scroll down to **Section 07** titled:  
  **`Investigation Brief`**  
  *(Subtitle: "Generate an evidence-grounded Gemini summary of this behavioral anomaly")*
* **[👉 CLICK BUTTON]:** Click the prominent golden button: **`◇ Generate AI Brief`**
* **[👀 WHAT TO POINT AT & EXPLAIN]:**
  - As the brief generates (or loads from cache), point to the structured output sections:
    - **`Headline & Summary`**: Clear, plain-English synthesis of the anomaly.
    - **`What Changed`**: Point to the exact bracketed citations **`[E1]`**, **`[E2]`**, **`[E3]`** showing Gemini quoting only validated deterministic evidence.
    - **`Investigate Next`**: Point to the bulleted defensive questions suggested for the risk analyst.
    - **`What Remains Unknown`**: Point out this mandatory transparency field.
    - **`Safety Note`**: Point to the guardrail disclaimer confirming human authority.

**[🎙️ WHAT TO SAY]:**
> "This is where Google Gemini enters the workflow—but crucially, Gemini is not the detector. 
> 
> The deterministic mathematical core has already identified the anomaly. Gemini receives only structured evidence items, labeled E1 through E6, through an injection-shielded prompt. 
> 
> Behind seven post-generation safety guardrails, Gemini synthesizes what changed, quotes exact evidence IDs, highlights critical unknowns, and suggests defensive investigative questions for the analyst. 
> 
> The guardrails explicitly forbid Gemini from declaring confirmed fraud or autonomously blocking payments. And if the AI service is offline or unconfigured, the system degrades gracefully—one hundred percent of deterministic evidence remains accessible."

---

### [2:40 – 3:35] Held-Out Evaluation & False-Positive Cost
* **[🎬 SCREEN ACTION]:** In the left sidebar, click the **`Evaluation`** tab.
* **[👀 WHAT TO POINT AT]:**
  - Point to the top metric cards:
    - **`126,574`** Held-Out Merchant-Days
    - **`7.13×`** Fraud-Containing Day Enrichment vs Normal
    - **`50.93%`** Proxy-Positive Coverage (Recall)
* **[📜 SCROLL DOWN]:** Scroll down to **Section 04: Proxy Outcome Cross-Tabulation (Confusion Matrix)**:
  - Point directly to the matrix cells: **`1,069 True Positives`**, **`15,021 False Positives`**, and **`6.64% Proxy Precision`**.
* **[📜 SCROLL DOWN]:** Scroll down to **Section 07: Scenario-Based Investigation Workload Model**:
  - Point to the 3 scenario columns:
    - **Lean** (5 min @ ₹300/hr) → **₹3,75,525**
    - **Standard** (15 min @ ₹500/hr) → **₹18,77,625**
    - **Intensive** (30 min @ ₹800/hr) → **₹60,08,400**
  - Point out the **`15.05 alerts per positive day`** metric.

**[🎙️ WHAT TO SAY]:**
> "We evaluated Payment Burst Sentinel on a temporal held-out test split of over one hundred and twenty-six thousand merchant-days. 
> 
> Because our detector operates at the merchant-day level while fraud labels exist per transaction, we report our results transparently as proxy classification metrics.
> 
> Flagged days capture fifty point nine three percent of fraud-containing merchant-days, delivering a seven point one three times fraud enrichment compared to normal days. 
> 
> Because anomaly detection naturally surfaces false positives, we also model the operational workload. In our held-out test set, sixteen thousand and ninety alerts captured one thousand sixty-nine fraud-containing days, leaving fifteen thousand false-positive alerts. 
> 
> Using explicit scenario assumptions—for example, fifteen minutes per review at five hundred rupees an hour—our interactive model quantifies the exact analyst capacity required to triage these signals."

---

### [3:35 – 4:10] Why This Matters (Ecosystem Positioning)
* **[🎬 SCREEN ACTION]:** Scroll back up to the top of **`Evaluation`** or click **`Monitor`** in the sidebar.
* **[👀 WHAT TO SHOW]:** Keep the clean interface visible while delivering the core value positioning.

**[🎙️ WHAT TO SAY]:**
> "We are not claiming to replace Razorpay's production fraud engines or real-time transaction firewalls. 
> 
> Instead, Payment Burst Sentinel adds a merchant-level behavioral lens alongside transaction-level risk controls, helping analysts investigate sudden payment-value bursts and unusual merchant behavior."

---

### [4:10 – 4:35] Integration Readiness Boundary
* **[🎬 SCREEN ACTION]:** In the left sidebar, click the **`Integration`** tab.
* **[👀 WHAT TO POINT AT]:**
  - Point to the 4-step diagram: **`Provider Abstraction → Input Validation → Canonical Schema (Decimal, UTC) → Processing Boundary (STOP)`**.
  - Point to the status card stating: **`ADAPTER READY ≠ CONNECTED`**.
* **[👉 CLICK BUTTON]:** Click the **`Ingest Demo Event`** button.
* **[👀 WHAT TO SHOW]:** Show the instant simulated response: UUID generated, UTC normalized, and note confirming that demo ingestion is isolated and never alters historical Parquet data.

**[🎙️ WHAT TO SAY]:**
> "Finally, we designed an integration readiness boundary. We implemented a provider-neutral canonical event schema enforcing UTC timestamps and exact Decimal amounts, paired with bounded idempotency and HMAC signature verification for Razorpay webhooks.
> 
> This demonstrates architectural readiness, while maintaining strict isolation: simulated demo events never modify historical data, never alter baselines, and never trigger detection."

---

### [4:35 – 5:00] Human Decision Boundary & Conclusion
* **[🎬 SCREEN ACTION]:** Click **`Investigations`** in sidebar → click **`Kovacek Ltd`** → scroll down to the bottom to **Section 08: System Boundary (Human Decision Boundary)**.
* **[👀 WHAT TO POINT AT]:** Point to the prominent amber warning card:  
  **`Automated fraud classification, merchant blocking, and transaction enforcement are disabled. Final assessment remains a human decision.`**
* **[🎙️ FINAL CLOSING WORDS]:** Deliver the closing with conviction:

> "The core design decision of Payment Burst Sentinel is its strict separation of responsibilities:
> 
> **Deterministic systems detect.**  
> **Gemini explains.**  
> **Humans decide.**
> 
> Thank you."

---

## 💡 Quick Tips for a Smooth Recording:
1. **Resolution:** Record at `1920x1080` (Full HD) or `1440x900`. Maximize your browser window.
2. **Pacing:** Speak at a steady, conversational pace. Don't rush when clicking; pause for 1–2 seconds on each screen so the viewer can absorb the visual cards.
3. **Cursor:** Use your mouse cursor as a visual pointer—circle the key numbers (7.13×, ₹19,364, 50.93%, cost cards) as you say them!
4. **Golden Path:** `Kovacek Ltd` (`2020-11-27`) is your hero example. Its numbers (+1935 MADs, 1 tx) make the behavioral concept immediately obvious to any judge.
