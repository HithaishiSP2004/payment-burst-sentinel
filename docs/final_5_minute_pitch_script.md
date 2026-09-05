# Payment Burst Sentinel — 5-Minute Video Pitch Script
## Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager

**Speaker Format:** Natural spoken presentation for a 5-minute screen-recorded video demo.  
**Target Duration:** 4 minutes 45 seconds to 5 minutes (~630 spoken words).  
**Core Thesis:** *"Deterministic systems detect. Gemini explains. Humans decide."*

---

### [0:00 – 0:30] The Problem & The Hook
*(Screen: Monitor view, showing 693 merchants and the 7.13× enrichment card)*

"In payments, fraud risk isn't always visible in a single transaction. 

A merchant can look completely normal transaction by transaction, but its overall payment behavior can suddenly shift. Traditional fraud engines often rely on global volume thresholds. But in reality, what is 'normal' varies wildly per merchant. Fifty thousand rupees daily might be standard for a supermarket, but extraordinary for a local bakery. 

When we analyzed historical merchant transaction data, aggregate transaction volume alone was poorly correlated with fraud. 

Payment Burst Sentinel was built to solve this: a defensive risk intelligence system that establishes individual behavioral rhythms for every merchant, detects statistical bursts, and arms human risk analysts with evidence-grounded AI explanations."

---

### [0:30 – 1:10] Detection Methodology
*(Screen: Merchant Rhythm timeline showing rolling 30-day baseline and variability)*

"Rather than imposing platform-wide static rules, we construct a rolling thirty-day behavioral baseline for each merchant. 

To handle skewed financial data robustly, we use the median rather than the mean, and the Median Absolute Deviation—or MAD—rather than standard deviation. This prevents past spikes from distorting what the system expects as normal.

Every day, we evaluate two distinct upward signals: transaction velocity deviation and payment value deviation. 

If a merchant's burst exceeds four MADs above baseline, we classify it as Elevated Risk. At five MADs or greater, it triggers a High Risk deviation. The mathematics are frozen, deterministic, and fully auditable."

---

### [0:10 – 1:55] Investigation Evidence Workspace
*(Screen: Navigate to Investigations, filter by High Risk, click 'Kovacek Ltd' 2020-11-27)*

"Here in the Investigations Index, an analyst can immediately prioritize severe anomalies. Let's open a real deviation from our held-out test set: Kovacek Ltd on November 27th, 2020.

Notice what happens before any AI is touched. The Evidence Workspace lays out deterministic facts: 
Kovacek Ltd typically processes about ten rupees and seventy-five paise per day. On this day, payment volume surged to nineteen thousand, three hundred and sixty-four rupees. That's a nineteen-hundred-and-thirty-five MAD deviation.

Yet its transaction count remained at just one transaction. The system immediately isolates that this was a high-value amount burst, not a volume surge. Every statement is grounded in frozen, verifiable baseline data."

---

### [1:55 – 2:40] Gemini AI Advisory Layer
*(Screen: Scroll to AI Investigation Intelligence, click 'Generate AI Brief')*

"This is where Google Gemini enters the workflow—but crucially, Gemini is not the detector. 

The deterministic mathematical core has already identified the anomaly. Gemini receives only structured evidence items, labeled E1 through E6, through an injection-shielded prompt. 

Behind seven post-generation safety guardrails, Gemini synthesizes what changed, quotes exact evidence IDs, highlights critical unknowns, and suggests defensive investigative questions for the analyst. 

The guardrails explicitly forbid Gemini from declaring confirmed fraud or autonomously blocking payments. And if the AI service is offline or unconfigured, the system degrades gracefully—one hundred percent of deterministic evidence remains accessible."

---

### [2:40 – 3:35] Held-Out Evaluation & False-Positive Cost
*(Screen: Navigate to Detection Evaluation, highlight Confusion Matrix and Cost Model)*

"We evaluated Payment Burst Sentinel on a temporal held-out test split of over one hundred and twenty-six thousand merchant-days. 

Because our detector operates at the merchant-day level while fraud labels exist per transaction, we report our results transparently as proxy classification metrics.

Flagged days capture fifty point nine three percent of fraud-containing merchant-days, delivering a seven point one three times fraud enrichment compared to normal days. 

Because anomaly detection naturally surfaces false positives, we also model the operational workload. In our held-out test set, sixteen thousand and ninety alerts captured one thousand sixty-nine fraud-containing days, leaving fifteen thousand false-positive alerts. 

Using explicit scenario assumptions—for example, fifteen minutes per review at five hundred rupees an hour—our interactive model quantifies the exact analyst capacity required to triage these signals."

---

### [3:35 – 4:10] Why This Matters
*(Screen: Pan across Evaluation Workspace and back to Monitor)*

"We are not claiming to replace Razorpay's production fraud engines or real-time transaction firewalls. 

Payment Burst Sentinel provides an additive merchant-level behavioral lens. It catches the slow-burn merchants and sudden payment-value bursts that transaction-level rules overlook, while respecting the operational realities and review costs that risk teams face every day."

---

### [4:10 – 4:35] Integration Readiness Boundary
*(Screen: Navigate to Integration screen, click 'Ingest Demo Event')*

"Finally, we designed an integration readiness boundary. We implemented a provider-neutral canonical event schema enforcing UTC timestamps and exact Decimal amounts, paired with bounded idempotency and HMAC signature verification for Razorpay webhooks.

This demonstrates architectural readiness, while maintaining strict isolation: simulated demo events never modify historical data, never alter baselines, and never trigger detection."

---

### [4:35 – 5:00] Conclusion
*(Screen: Investigation Workspace showing Human Decision Boundary card)*

"The core design decision of Payment Burst Sentinel is its strict separation of responsibilities:

Deterministic systems detect.  
Gemini explains.  
Humans decide.

Thank you."
