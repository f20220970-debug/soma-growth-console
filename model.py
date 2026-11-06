"""Driver-based ARR model for a commission-revenue insurance brokerage (illustrative inputs, not company data).

The same model exists twice:
  - ARR_Growth_Model.xlsx : live Excel formulas (built by build_excel.py), for founders to play with
  - this file             : a Python mirror used for Monte Carlo and sensitivity runs; tests check both agree
"""
import json
import numpy as np, pandas as pd

MONTHS = 24
SCENARIOS = {  # name: (Bear, Base, Bull)
    "start_leads":        (6000, 6000, 6000),     # leads in month 1
    "lead_growth":        (.04, .07, .10),        # month-on-month
    "lead_to_bind":       (.12, .15, .18),
    "avg_premium":        (2100, 2300, 2500),     # USD per policy per year
    "commission_rate":    (.12, .13, .14),
    "annual_renewal":     (.75, .81, .86),
    "cost_per_lead":      (48, 40, 34),           # USD
    "leads_per_agent":    (500, 600, 700),        # per month
    "agent_cost":         (4000, 4000, 4000),     # USD per agent per month
    "fixed_opex":         (150000, 120000, 120000),
    "start_policies":     (4000, 4000, 4000),
    "start_cash":         (5_000_000, 5_000_000, 5_000_000),
    "target_arr":         (10_000_000, 10_000_000, 10_000_000),
}
LABELS = {
    "start_leads": "Leads in month 1", "lead_growth": "Lead growth, month on month", "lead_to_bind": "Lead-to-bind conversion",
    "avg_premium": "Average annual premium per policy ($)", "commission_rate": "Commission rate",
    "annual_renewal": "Annual renewal rate", "cost_per_lead": "Cost per lead ($)", "leads_per_agent": "Leads one agent handles per month",
    "agent_cost": "Cost per agent per month ($)", "fixed_opex": "Fixed opex per month ($)", "start_policies": "Active policies at start",
    "start_cash": "Starting cash ($)", "target_arr": "Target ARR ($)",
}


def inputs(scenario="Base"):
    i = ["Bear", "Base", "Bull"].index(scenario)
    return {k: v[i] for k, v in SCENARIOS.items()}


def run(p, months=MONTHS):
    rows = []
    leads, active, cash = p["start_leads"], p["start_policies"], p["start_cash"]
    churn_m = 1 - p["annual_renewal"] ** (1 / 12)
    for m in range(1, months + 1):
        if m > 1:
            leads = leads * (1 + p["lead_growth"])
        new = leads * p["lead_to_bind"]
        churned = active * churn_m
        active = active + new - churned
        arr = active * p["avg_premium"] * p["commission_rate"]
        revenue = arr / 12
        marketing = leads * p["cost_per_lead"]
        agents = int(np.ceil(leads / p["leads_per_agent"] - 1e-9))
        cost = marketing + agents * p["agent_cost"] + p["fixed_opex"]
        cash = cash + revenue - cost
        rows.append(dict(month=m, leads=leads, new_policies=new, churned=churned, active=active, arr=arr, revenue=revenue,
                         marketing=marketing, agents=agents, total_cost=cost, net_burn=revenue - cost, cash=cash))
    df = pd.DataFrame(rows)
    hit = df[df.arr >= p["target_arr"]]
    cac = p["cost_per_lead"] / p["lead_to_bind"]
    ltv = p["avg_premium"] * p["commission_rate"] / (1 - p["annual_renewal"])
    return df, dict(arr_m12=df.arr.iat[11], arr_m24=df.arr.iat[-1],
                    month_target_hit=int(hit.month.iat[0]) if len(hit) else None,
                    min_cash=df.cash.min(), extra_cash_needed=max(0.0, -df.cash.min()), cash_out_month=int(df[df.cash < 0].month.iat[0]) if (df.cash < 0).any() else None,
                    cac_per_policy=cac, ltv=ltv, ltv_to_cac=ltv / cac, payback_months=12 * cac / (p["avg_premium"] * p["commission_rate"]))


def tornado(base="Base", swing=.2):
    """ARR at month 18 when each driver moves +/- 20% (one at a time)."""
    p0 = inputs(base)
    ref = run(p0, 18)[0].arr.iat[-1]
    rows = []
    # premium and commission rate move ARR identically (both multiply), as do start leads and conversion,
    # so one of each pair is shown
    for k in ["avg_premium", "lead_to_bind", "lead_growth", "annual_renewal"]:
        lo, hi = dict(p0), dict(p0)
        if k == "annual_renewal":       # swing churn, not renewal, so +/-20% stays below 100%
            c = 1 - p0[k]; lo[k], hi[k] = 1 - c * (1 + swing), 1 - c * (1 - swing)
        else:
            lo[k], hi[k] = p0[k] * (1 - swing), p0[k] * (1 + swing)
        a, b = run(lo, 18)[0].arr.iat[-1], run(hi, 18)[0].arr.iat[-1]
        name = "Revenue per policy (premium x commission)" if k == "avg_premium" else LABELS[k]
        rows.append(dict(driver=name, low=a, high=b, range=b - a))
    return pd.DataFrame(rows).sort_values("range", ascending=False), ref


def monte_carlo(n=5000, seed=0):
    """Uncertain drivers drawn around Base; everything else fixed."""
    r = np.random.default_rng(seed)
    p0 = inputs("Base")
    out = []
    for _ in range(n):
        p = dict(p0)
        p["lead_growth"] = r.normal(.07, .02)
        p["lead_to_bind"] = np.clip(r.normal(.15, .02), .05, .4)
        p["annual_renewal"] = np.clip(r.normal(.81, .04), .5, .97)
        p["cost_per_lead"] = max(10, r.normal(40, 7))
        p["avg_premium"] = r.normal(2300, 200)
        _, s = run(p)
        out.append((s["arr_m12"], s["arr_m24"], s["month_target_hit"] or 99, s["min_cash"]))
    d = pd.DataFrame(out, columns=["arr_m12", "arr_m24", "hit", "min_cash"])
    return dict(simulations=n,
                arr_m24_p10_p50_p90=[round(float(x)) for x in np.percentile(d.arr_m24, [10, 50, 90])],
                p_target_by_m18=round(float((d.hit <= 18).mean()) * 100, 1),
                p_target_by_m24=round(float((d.hit <= 24).mean()) * 100, 1),
                p_cash_below_zero=round(float((d.min_cash < 0).mean()) * 100, 1),
                p_cash_below_1m=round(float((d.min_cash < 1_000_000).mean()) * 100, 1))


def main():
    res = {}
    for sc in ["Bear", "Base", "Bull"]:
        _, s = run(inputs(sc))
        res[sc] = {k: (round(float(v), 2) if isinstance(v, (float, np.floating)) else v) for k, v in s.items()}
    t, ref = tornado()
    res["tornado_arr_m18"] = dict(base=round(float(ref)), drivers=[dict(driver=r.driver, low=round(r.low), high=round(r.high))
                                                                 for r in t.itertuples()])
    res["monte_carlo"] = monte_carlo()
    with open("results.json", "w") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
