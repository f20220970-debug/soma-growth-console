# Growth Console: brokerage ARR and runway planner

[![tests](https://github.com/f20220970-debug/soma-growth-console/actions/workflows/tests.yml/badge.svg)](https://github.com/f20220970-debug/soma-growth-console/actions/workflows/tests.yml)

**Live app:** (https://soma-growth-console-ctm3kxywkrrytky4rbgrxr.streamlit.app/)

A planning tool for a founder's office at a commission-revenue insurance brokerage. You move the drivers and operating levers, and ARR, cash runway, unit economics and plan risk update live. It's built for **Soma AI's Founder's Office** application.

> **All inputs are illustrative and none are company data.** The driver model comes from [arr-growth-model](https://github.com/f20220970-debug/arr-growth-model). Lever effect sizes come from simulated experiments in [soma-brokerage-ops-lab](https://github.com/f20220970-debug/soma-brokerage-ops-lab).

## What you can do

- **Drivers (sidebar):** set leads, growth, conversion, premium, commission, renewal, cost per lead, agent capacity and cost, opex and cash. You can start from Bear, Base or Bull.
- **Operating levers:**
  - AI agent coverage of after-hours leads (+13.7% bound at full coverage)
  - Carrier appetite routing (bind rate 49% → 61%)
  - Proactive renewal reviews (+6.8 pts renewal)
  - The AI agent's monthly running cost

  These are converted into model inputs in `levers.py`, so you see their effect on ARR and runway, net of cost.
- **Headline numbers:** ARR at month 24, the month the target is reached, the month cash runs out, extra cash needed, and LTV/CAC with payback.
- **Risk:** a Monte Carlo of 500–5,000 runs gives the chance of hitting the target by month 18 or 24, the chance cash goes negative, and the spread of ARR outcomes.
- **Export:** download the monthly model as a CSV.

**Example (Base case):** with no levers, the plan reaches $10M ARR in month 20 but runs out of cash in month 19. Turn the levers on to see whether they close the gap before a fundraise is needed.

## Run locally

```
pip install -r requirements.txt
streamlit run app.py
pytest -q     # renders the app headless (Streamlit AppTest) and checks that the levers move the numbers
```

## Deploy (free)

1. Sign in at share.streamlit.io with GitHub.
2. Choose New app → this repo → `app.py` → Deploy.
3. Paste the link at the top of this README.
