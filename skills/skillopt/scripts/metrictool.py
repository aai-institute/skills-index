#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6"]
# ///
"""Validate metric files and aggregate per-term scores into a total.

The format is described in references/metric-format.md (next to this scripts/ folder).

Usage (uv installs PyYAML on the fly):
  uv run scripts/metrictool.py validate METRIC.yaml
  uv run scripts/metrictool.py normalize-weights METRIC.yaml
  uv run scripts/metrictool.py aggregate METRIC.yaml SCORES.json [--out RESULT.json] [--markdown]
"""

from __future__ import annotations

import argparse
import json
import operator
import sys
from pathlib import Path

import yaml

KINDS = {"judge", "computed", "checklist"}
TOLERANCE = 1e-6
OPS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq}
NORMALIZE_FIELDS = {
    "linear": ("worst", "best"),
    "band": ("zero_below", "ideal_min", "ideal_max", "zero_above"),
    "threshold": ("op", "value"),
}


def load_metric(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def validate(metric) -> list[str]:
    if not isinstance(metric, dict):
        return ["metric file must be a YAML mapping"]
    errors = []
    for key in ("name", "artifact", "terms"):
        if key not in metric:
            errors.append(f"missing top-level key '{key}'")
    terms = metric.get("terms") or []
    if not terms:
        errors.append("metric needs at least one term")

    seen, total = set(), 0.0
    for i, term in enumerate(terms):
        tid = term.get("id")
        where = f"terms[{i}] ({tid})"
        if not tid:
            errors.append(f"{where}: missing 'id'")
        elif tid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(tid)

        weight = term.get("weight")
        if not isinstance(weight, (int, float)) or weight <= 0:
            errors.append(f"{where}: 'weight' must be a positive number")
        else:
            total += weight

        kind = term.get("kind")
        if kind not in KINDS:
            errors.append(f"{where}: 'kind' must be one of {sorted(KINDS)}")
        elif kind == "judge":
            rubric = term.get("rubric") or {}
            levels = {float(k) for k in rubric}
            if not {0.0, 0.5, 1.0} <= levels:
                errors.append(f"{where}: rubric needs at least the anchors 0.0, 0.5 and 1.0")
            if any(not 0 <= lvl <= 1 for lvl in levels):
                errors.append(f"{where}: rubric anchors must lie in [0, 1]")
        elif kind == "computed":
            if not term.get("measure"):
                errors.append(f"{where}: computed term needs 'measure'")
            errors.extend(f"{where}: {e}" for e in validate_normalize(term.get("normalize")))
        elif kind == "checklist":
            items = term.get("items") or []
            if not items:
                errors.append(f"{where}: checklist term needs 'items'")
            item_ids = [it.get("id") for it in items]
            if None in item_ids or len(set(item_ids)) != len(item_ids):
                errors.append(f"{where}: every checklist item needs a unique 'id'")

    if terms and abs(total - 1.0) > TOLERANCE:
        errors.append(f"weights sum to {total:.6f}, not 1 (run 'normalize-weights')")

    gate_ids = [g.get("id") for g in metric.get("gates") or []]
    if None in gate_ids or len(set(gate_ids)) != len(gate_ids):
        errors.append("every gate needs a unique 'id'")
    return errors


def validate_normalize(spec) -> list[str]:
    if not isinstance(spec, dict) or spec.get("type") not in NORMALIZE_FIELDS:
        return [f"'normalize.type' must be one of {sorted(NORMALIZE_FIELDS)}"]
    missing = [f for f in NORMALIZE_FIELDS[spec["type"]] if f not in spec]
    if missing:
        return [f"normalize ({spec['type']}) is missing {missing}"]
    if spec["type"] == "linear" and spec["worst"] == spec["best"]:
        return ["normalize (linear): 'worst' and 'best' must differ"]
    if spec["type"] == "band":
        points = [spec[f] for f in NORMALIZE_FIELDS["band"]]
        if points != sorted(points):
            return ["normalize (band): need zero_below <= ideal_min <= ideal_max <= zero_above"]
    if spec["type"] == "threshold" and spec["op"] not in OPS:
        return [f"normalize (threshold): 'op' must be one of {sorted(OPS)}"]
    return []


def normalize_raw(raw: float, spec: dict) -> float:
    kind = spec["type"]
    if kind == "linear":
        return clamp((raw - spec["worst"]) / (spec["best"] - spec["worst"]))
    if kind == "band":
        lo0, lo1, hi1, hi0 = (spec[f] for f in NORMALIZE_FIELDS["band"])
        if lo1 <= raw <= hi1:
            return 1.0
        if raw < lo1:
            return clamp((raw - lo0) / (lo1 - lo0)) if lo1 > lo0 else 0.0
        return clamp((hi0 - raw) / (hi0 - hi1)) if hi0 > hi1 else 0.0
    return 1.0 if OPS[spec["op"]](raw, spec["value"]) else 0.0


def term_score(term: dict, entry: dict) -> float:
    if "score" in entry:
        return clamp(float(entry["score"]))
    if term["kind"] == "computed" and "raw" in entry:
        return normalize_raw(float(entry["raw"]), term["normalize"])
    if term["kind"] == "checklist" and "items" in entry:
        ids = [it["id"] for it in term["items"]]
        missing = [i for i in ids if i not in entry["items"]]
        if missing:
            raise ValueError(f"term '{term['id']}': no result for checklist items {missing}")
        return sum(bool(entry["items"][i]) for i in ids) / len(ids)
    raise ValueError(f"term '{term['id']}': give 'score', 'raw' (computed) or 'items' (checklist)")


def aggregate(metric: dict, scores: dict) -> dict:
    entries = scores.get("terms", {})
    missing = [t["id"] for t in metric["terms"] if t["id"] not in entries]
    if missing:
        raise ValueError(f"no scores for terms {missing}")

    rows = []
    for term in metric["terms"]:
        entry = entries[term["id"]]
        score = term_score(term, entry)
        rows.append({
            "id": term["id"],
            "name": term.get("name", term["id"]),
            "weight": term["weight"],
            "score": round(score, 4),
            "contribution": round(term["weight"] * score, 4),
            # How much the total would gain if this term were perfect.
            "headroom": round(term["weight"] * (1 - score), 4),
            "evidence": entry.get("evidence", ""),
            "suggestion": entry.get("suggestion", ""),
        })

    gate_results = scores.get("gates", {})
    gates = []
    for gate in metric.get("gates") or []:
        result = gate_results.get(gate["id"])
        if result is None:
            raise ValueError(f"no result for gate '{gate['id']}'")
        gates.append({"id": gate["id"], "pass": bool(result["pass"]), "evidence": result.get("evidence", "")})

    return {
        "artifact": scores.get("artifact"),
        "metric": metric["name"],
        "metric_version": metric.get("version"),
        "total": round(sum(r["contribution"] for r in rows), 4),
        "acceptable": all(g["pass"] for g in gates),
        "terms": rows,
        "gates": gates,
        "biggest_levers": [r["id"] for r in sorted(rows, key=lambda r: -r["headroom"]) if r["headroom"] > 0],
    }


def to_markdown(result: dict) -> str:
    lines = [
        f"**Total: {result['total']:.2f}** / 1.00 — metric `{result['metric']}` v{result['metric_version']}",
        f"**Gates:** {'all passed' if result['acceptable'] else 'FAILED'}",
        "",
        "| Term | Weight | Score | Contribution | Headroom |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in result["terms"]:
        lines.append(f"| {r['name']} | {r['weight']:.2f} | {r['score']:.2f} | {r['contribution']:.3f} | {r['headroom']:.3f} |")
    for g in result["gates"]:
        lines.append(f"\n- Gate `{g['id']}`: {'pass' if g['pass'] else 'FAIL'} — {g['evidence']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_val = sub.add_parser("validate", help="check a metric file")
    p_val.add_argument("metric")
    p_norm = sub.add_parser("normalize-weights", help="rescale weights in place so they sum to 1")
    p_norm.add_argument("metric")
    p_agg = sub.add_parser("aggregate", help="combine a scores file into a total")
    p_agg.add_argument("metric")
    p_agg.add_argument("scores")
    p_agg.add_argument("--out", help="write the result JSON here")
    p_agg.add_argument("--markdown", action="store_true", help="also print a markdown table")
    args = parser.parse_args()

    metric = load_metric(args.metric)

    if args.cmd == "normalize-weights":
        total = sum(t["weight"] for t in metric["terms"])
        for t in metric["terms"]:
            t["weight"] = round(t["weight"] / total, 4)
        # Put any rounding residue on the largest term so the sum is exactly 1.
        largest = max(metric["terms"], key=lambda t: t["weight"])
        largest["weight"] = round(largest["weight"] + 1 - sum(t["weight"] for t in metric["terms"]), 4)
        Path(args.metric).write_text(yaml.safe_dump(metric, sort_keys=False, allow_unicode=True, width=100))
        print(f"weights rescaled (previous sum {total:g})")
        return 0

    errors = validate(metric)
    if errors:
        print("Metric is invalid:\n" + "\n".join(f"  - {e}" for e in errors), file=sys.stderr)
        return 1
    if args.cmd == "validate":
        print(f"OK: '{metric['name']}' with {len(metric['terms'])} terms, {len(metric.get('gates') or [])} gates")
        return 0

    with open(args.scores) as f:
        scores = json.load(f)
    try:
        result = aggregate(metric, scores)
    except ValueError as e:
        print(f"Cannot aggregate: {e}", file=sys.stderr)
        return 1
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(to_markdown(result) if args.markdown else json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
