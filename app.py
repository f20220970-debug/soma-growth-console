"""Soma Growth Console: a founder's planning tool for a commission-revenue insurance brokerage.
Move the drivers and operating levers; see ARR, cash runway, unit economics and risk update live.
All inputs are illustrative. Model: arr-growth-model. Lever effect sizes: soma-brokerage-ops-lab (simulated)."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import levers as LV
import model as M

st.set_page_config(page_title="Soma Growth Console", layout="wide")

st.title("Growth Console: brokerage ARR and runway planner")
st.caption("Illustrative inputs, not company data. Driver model from arr-growth-model; lever effect sizes from "
           "simulated experiments in soma-brokerage-ops-lab.")

# ---------------- sidebar: drivers ----------------
sb = st.sidebar
sb.header("Scenario")
scenario = sb.radio("Start from", ["Bear", "Base", "Bull"], index=1, horizontal=True)
p0 = M.inputs(scenario)
sb.header("Growth drivers")
p = dict(p0)
p["start_leads"] = sb.number_input("Leads in month 1", 500, 50000, int(p0["start_leads"]), 500)
p["lead_growth"] = sb.slider("Lead growth, month on month", 0.0, 0.20, float(p0["lead_growth"]), 0.005, format="%.3f")
p["lead_to_bind"] = sb.slider("Lead-to-bind conversion", 0.05, 0.35, float(p0["lead_to_bind"]), 0.005, format="%.3f")
p["avg_premium"] = sb.number_input("Average annual premium per policy ($)", 300, 20000, int(p0["avg_premium"]), 100)
p["commission_rate"] = sb.slider("Commission rate", 0.05, 0.25, float(p0["commission_rate"]), 0.005, format="%.3f")
p["annual_renewal"] = sb.slider("Annual renewal rate", 0.50, 0.95, float(p0["annual_renewal"]), 0.01)
sb.header("Costs and cash")
p["cost_per_lead"] = sb.number_input("Cost per lead ($)", 1, 500, int(p0["cost_per_lead"]), 1)
p["leads_per_agent"] = sb.number_input("Leads one agent handles per month", 50, 5000, int(p0["leads_per_agent"]), 50)
p["agent_cost"] = sb.number_input("Cost per agent per month ($)", 500, 20000, int(p0["agent_cost"]), 250)
p["fixed_opex"] = sb.number_input("Fixed opex per month ($)", 0, 2_000_000, int(p0["fixed_opex"]), 10_000)
p["start_cash"] = sb.number_input("Starting cash ($)", 0, 100_000_000, int(p0["start_cash"]), 250_000)
p["target_arr"] = sb.number_input("Target ARR ($)", 1_000_000, 200_000_000, int(p0["target_arr"]), 1_000_000)

# ---------------- operating levers ----------------
st.subheader("Operating levers")
c1, c2, c3, c4 = st.columns(4)
ai_cov = c1.slider("AI agent covers after-hours leads", 0, 100, 0, 10, format="%d%%") / 100
routing = c2.toggle("Carrier appetite routing", value=False, help="Send each application to the carriers most likely to quote that industry")
review = c3.slider("Renewals given a proactive review", 0, 100, 0, 10, format="%d%%") / 100
ai_cost = c4.number_input("AI agent running cost per month ($)", 0, 200_000, 8_000 if ai_cov else 0, 1_000)

q, notes = LV.apply(p, ai_cov, routing, review, ai_cost)
base_df, base_s = M.run(p)
df, s = M.run(q)

# ---------------- headline metrics ----------------
fmt_m = lambda x: f"${x / 1e6:,.1f}M"
def month_txt(m):
    return f"Month {m}" if m else "Not within 24 months"

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("ARR at month 24", fmt_m(s["arr_m24"]), f"{(s['arr_m24'] / base_s['arr_m24'] - 1) * 100:+.1f}% vs no levers" if notes else None)
k2.metric("Target ARR reached", month_txt(s["month_target_hit"]))
k3.metric("Cash runs out", month_txt(s["cash_out_month"]) if s["cash_out_month"] else "Never (24 months)")
k4.metric("Extra cash needed", fmt_m(s["extra_cash_needed"]))
k5.metric("LTV / CAC", f"{s['ltv_to_cac']:.1f}x", f"payback {s['payback_months']:.1f} months", delta_color="off")
if notes:
    st.caption("Levers applied: " + " · ".join(notes))

# ---------------- charts ----------------
left, right = st.columns(2)
fig = go.Figure()
fig.add_scatter(x=df.month, y=df.arr, name="ARR with levers", line=dict(color="#1F3864", width=3))
if notes:
    fig.add_scatter(x=base_df.month, y=base_df.arr, name="ARR without levers", line=dict(color="#8EA9DB", dash="dash"))
fig.add_hline(y=q["target_arr"], line_dash="dot", line_color="#C00000", annotation_text="Target")
fig.update_layout(title="ARR (annualised commission)", height=360, yaxis_tickprefix="$", yaxis_tickformat=".2s", margin=dict(t=50, b=30),
                  legend=dict(orientation="h", y=-0.2))
left.plotly_chart(fig, width="stretch")

fig2 = go.Figure()
fig2.add_bar(x=df.month, y=df.cash, name="Cash", marker_color=np.where(df.cash < 0, "#C00000", "#548235"))
fig2.add_scatter(x=df.month, y=df.net_burn, name="Monthly net burn", line=dict(color="#7F7F7F"))
fig2.update_layout(title="Cash at month end and monthly net burn", height=360, yaxis_tickprefix="$", yaxis_tickformat=".2s",
                   margin=dict(t=50, b=30), legend=dict(orientation="h", y=-0.2))
right.plotly_chart(fig2, width="stretch")

# ---------------- risk ----------------
st.subheader("Risk: how likely is the plan?")
r1, r2 = st.columns([1, 2])
n = r1.select_slider("Monte Carlo runs", [500, 1000, 2000, 5000], 1000)
spread = r1.slider("Uncertainty on growth, conversion and renewal (± 1 s.d., relative)", 0.05, 0.40, 0.15, 0.05)


@st.cache_data(show_spinner=False)
def simulate(q_items, n, spread, seed=0):
    q = dict(q_items)
    r = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        x = dict(q)
        x["lead_growth"] = r.normal(q["lead_growth"], abs(q["lead_growth"]) * spread)
        x["lead_to_bind"] = max(.01, r.normal(q["lead_to_bind"], q["lead_to_bind"] * spread))
        churn = 1 - q["annual_renewal"]
        x["annual_renewal"] = float(np.clip(1 - r.normal(churn, churn * spread), .3, .98))
        x["cost_per_lead"] = max(1, r.normal(q["cost_per_lead"], q["cost_per_lead"] * spread))
        _, ss = M.run(x)
        out.append((ss["arr_m24"], ss["month_target_hit"] or 99, ss["min_cash"]))
    return pd.DataFrame(out, columns=["arr_m24", "hit", "min_cash"])


sims = simulate(tuple(sorted(q.items())), n, spread)
m1, m2, m3 = r1.columns(3)
m1.metric("Target by m18", f"{(sims.hit <= 18).mean():.0%}")
m2.metric("Target by m24", f"{(sims.hit <= 24).mean():.0%}")
m3.metric("Cash < 0", f"{(sims.min_cash < 0).mean():.0%}")
fig3 = go.Figure(go.Histogram(x=sims.arr_m24, nbinsx=40, marker_color="#1F3864"))
for pct, lab in zip(np.percentile(sims.arr_m24, [10, 50, 90]), ["P10", "P50", "P90"]):
    fig3.add_vline(x=pct, line_dash="dot", annotation_text=lab)
fig3.update_layout(title=f"ARR at month 24 across {n:,} runs", height=320, xaxis_tickprefix="$", xaxis_tickformat=".2s", margin=dict(t=50, b=30))
r2.plotly_chart(fig3, width="stretch")

# ---------------- table + download ----------------
with st.expander("Monthly model"):
    show = df[["month", "leads", "new_policies", "churned", "active", "arr", "revenue", "total_cost", "net_burn", "cash"]].copy()
    st.dataframe(show.style.format({c: "{:,.0f}" for c in show.columns if c != "month"}), width="stretch", hide_index=True)
    st.download_button("Download as CSV", show.to_csv(index=False), "growth_plan.csv", "text/csv")

st.caption("Built by Pavitra Seth · Source: github.com/f20220970-debug/soma-growth-console")
