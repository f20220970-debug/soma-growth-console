"""Operating levers -> model inputs. Effect sizes come from the simulated experiments in soma-brokerage-ops-lab
(https://github.com/f20220970-debug/soma-brokerage-ops-lab), so they are illustrative, not company facts."""

# effect sizes measured in the simulation
AFTER_HOURS_LIFT_FULL = 0.137      # +13.7% policies bound when the AI agent covers 100% of after-hours leads
ROUTING_BIND_LIFT = 60.7 / 49.3 - 1  # appetite routing: bind rate 49.3% -> 60.7% of applications
RENEWAL_REVIEW_LIFT = 0.068        # +6.8 pts renewal when every renewal gets a proactive review


def apply(p, ai_coverage=0.0, routing=False, review_coverage=0.0, ai_cost_per_month=0.0):
    """Return a copy of model inputs with operating levers applied, plus a note of what changed."""
    q = dict(p)
    conv_mult = (1 + AFTER_HOURS_LIFT_FULL * ai_coverage) * (1 + ROUTING_BIND_LIFT if routing else 1)
    q["lead_to_bind"] = p["lead_to_bind"] * conv_mult
    q["annual_renewal"] = min(.97, p["annual_renewal"] + RENEWAL_REVIEW_LIFT * review_coverage)
    q["fixed_opex"] = p["fixed_opex"] + ai_cost_per_month
    notes = []
    if ai_coverage:
        notes.append(f"AI after-hours coverage {ai_coverage:.0%}: conversion x{1 + AFTER_HOURS_LIFT_FULL * ai_coverage:.3f}")
    if routing:
        notes.append(f"Appetite routing: conversion x{1 + ROUTING_BIND_LIFT:.3f}")
    if review_coverage:
        notes.append(f"Renewal reviews on {review_coverage:.0%} of renewals: +{RENEWAL_REVIEW_LIFT * review_coverage * 100:.1f} pts renewal")
    return q, notes
