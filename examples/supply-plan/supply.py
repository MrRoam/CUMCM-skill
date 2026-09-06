#!/usr/bin/env python3
"""Synthetic six-site exercise: standard-library evaluation and exact enumeration."""
import argparse
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path


def load(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    scope = data["evaluation"]
    assert data["synthetic"] is True, "This fixture only supports synthetic data"
    assert scope["annual_cost_unit"] == "CNY/year", "Unsupported cost unit: convert explicitly before evaluation"
    assert scope["coverage"] == "union_of_disjoint_demand_groups"
    assert scope["objective"] == "covered_people_per_10000_CNY_annual_cost"
    assert scope["objective_unit"] == "people/(10000 CNY/year)"
    assert scope["capacity"] == "unlimited" and scope["cost_rule"] == "sum_of_selected_fixed_annual_costs"
    assert type(scope["max_sites"]) is int and scope["max_sites"] > 0
    assert type(scope["min_covered_people"]) is int and scope["min_covered_people"] > 0
    groups = {g["id"]: g["people"] for g in data["groups"]}
    sites = {s["id"]: s for s in data["sites"]}
    assert len(groups) == len(data["groups"]) and len(sites) == len(data["sites"]), "Duplicate IDs"
    assert all(type(n) is int and n > 0 for n in groups.values())
    for site in sites.values():
        assert type(site["annual_cost"]) is int and site["annual_cost"] > 0
        assert len(set(site["covers"])) == len(site["covers"]) and set(site["covers"]) <= set(groups)
    return data


def evaluate(data, selected):
    sites = {s["id"]: s for s in data["sites"]}
    assert len(set(selected)) == len(selected), "Duplicate selected site"
    assert set(selected) <= set(sites), "Unknown selected site"
    covered = set().union(*(set(sites[s]["covers"]) for s in selected))
    people = sum(g["people"] for g in data["groups"] if g["id"] in covered)
    cost = sum(sites[s]["annual_cost"] for s in selected)
    score = Fraction(people * 10000, cost) if cost else Fraction(0)
    scope = data["evaluation"]
    return {"selected": sorted(selected), "covered_groups": sorted(covered),
            "covered_people": people, "annual_cost_CNY": cost,
            "score": float(score), "score_exact": str(score),
            "score_unit": scope["objective_unit"],
            "feasible": bool(selected) and len(selected) <= scope["max_sites"]
                        and people >= scope["min_covered_people"]}


def subsets(data):
    names = sorted(s["id"] for s in data["sites"])
    return [p for count in range(len(names) + 1) for p in itertools.combinations(names, count)]


def solve(data):
    results = [evaluate(data, selected) for selected in subsets(data)]
    feasible = [r for r in results if r["feasible"]]
    assert feasible, "No feasible subset"
    best_score = max(Fraction(r["score_exact"]) for r in feasible)
    best = [r for r in feasible if Fraction(r["score_exact"]) == best_score]
    max_coverage = max(r["covered_people"] for r in feasible)
    return {"subsets_enumerated": len(results), "feasible_subsets": len(feasible),
            "optima": best, "maximum_coverage_plans": [r for r in feasible if r["covered_people"] == max_coverage],
            "proof_scope": "All subsets enumerated; exact rational objective comparison under declared synthetic model."}


def verify(data):
    # Independent coverage implementation: scan demand groups and test membership;
    # do not reuse evaluate's union/sum construction or the solver's candidate list.
    sites = data["sites"]
    checked = 0
    feasible = []
    for mask in range(1 << len(sites)):
        chosen = [s for i, s in enumerate(sites) if mask & (1 << i)]
        groups, people, cost = [], 0, 0
        for group in data["groups"]:
            if any(group["id"] in site["covers"] for site in chosen):
                groups.append(group["id"])
                people += group["people"]
        for site in chosen:
            cost += site["annual_cost"]
        ok = 0 < len(chosen) <= data["evaluation"]["max_sites"] and people >= data["evaluation"]["min_covered_people"]
        ratio = Fraction(10000 * people, cost) if cost else Fraction(0)
        names = sorted(site["id"] for site in chosen)
        actual = evaluate(data, names)
        assert (people, cost, sorted(groups), ok, str(ratio)) == (actual["covered_people"], actual["annual_cost_CNY"], actual["covered_groups"], actual["feasible"], actual["score_exact"])
        if ok:
            feasible.append((ratio, names))
        checked += 1
    best = max(ratio for ratio, names in feasible)
    expected = sorted(names for ratio, names in feasible if ratio == best)
    assert expected == sorted(r["selected"] for r in solve(data)["optima"])
    return {"independent_subsets_checked": checked, "exact_optimum_agrees": True,
            "boundary": "Independent implementation check, not external validation of real-world assumptions."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("evaluate", "solve", "verify"))
    parser.add_argument("--data", default=str(Path(__file__).with_name("data.json")))
    parser.add_argument("--select", nargs="*", default=[])
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        path = Path(args.data)
        data = load(path)
        payload = evaluate(data, args.select) if args.action == "evaluate" else globals()[args.action](data)
        result = {"synthetic": True, "evaluation": data["evaluation"], "result": payload,
                  "data_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            with Path(args.output).open("x", encoding="utf-8") as stream:
                stream.write(text)
        print(text, end="")
    except (AssertionError, ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, "Supply error: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
