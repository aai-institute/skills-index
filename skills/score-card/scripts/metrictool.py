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
import re
import sys
from pathlib import Path

import yaml

KINDS = {"judge", "computed", "checklist"}
TOLERANCE = 1e-6
OPS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq}
NORMALIZE_FIELDS = {  # required fields per type
    "linear": ("worst", "best"),
    "band": ("ideal_min", "ideal_max"),
    "threshold": ("op", "value"),
}
# band: zero_below / zero_above are optional; leaving one out means no penalty on that side.
BAND_ORDER = ("zero_below", "ideal_min", "ideal_max", "zero_above")
TOP_KEYS = {"name", "version", "artifact", "owner", "context", "references", "accept_threshold",
            "terms", "gates", "caps"}
TERM_KEYS = {"id", "name", "weight", "kind", "description", "rubric", "examples", "measure",
             "normalize", "items"}


class MetricError(Exception):
    pass


def load_metric(path: str) -> dict:
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except OSError as e:
        raise MetricError(f"cannot read {path}: {e.strerror}") from e
    except yaml.YAMLError as e:
        raise MetricError(f"{path} is not valid YAML: {e}") from e


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate(metric, base_dir: Path | None = None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). base_dir is used to check that references exist."""
    if not isinstance(metric, dict):
        return ["metric file must be a YAML mapping"], []
    errors, warnings = [], []
    for key in ("name", "artifact", "terms"):
        if key not in metric:
            errors.append(f"missing top-level key '{key}'")
    unknown = sorted(set(metric) - TOP_KEYS)
    if unknown:
        warnings.append(f"unknown top-level keys {unknown} are ignored by all tools")

    threshold = metric.get("accept_threshold")
    if threshold is not None and not (is_number(threshold) and 0 <= threshold <= 1):
        errors.append("'accept_threshold' must be a number in [0, 1]")

    refs = metric.get("references")
    if refs is not None:
        if not isinstance(refs, dict):
            errors.append("'references' must be a mapping of name -> path")
        elif base_dir is not None:
            for name, ref in refs.items():
                if isinstance(ref, str) and "://" not in ref and not (base_dir / ref).exists():
                    warnings.append(f"reference '{name}' not found: {ref} "
                                    f"(paths are relative to the metric file)")

    terms = metric.get("terms") or []
    if not isinstance(terms, list):
        errors.append("'terms' must be a list")
        terms = []
    if not terms and "terms" in metric:
        errors.append("metric needs at least one term")

    seen, total = set(), 0.0
    for i, term in enumerate(terms):
        if not isinstance(term, dict):
            errors.append(f"terms[{i}]: each term must be a mapping with id, weight, kind, ...")
            continue
        tid = term.get("id")
        where = f"terms[{i}] ({tid})"
        if not tid:
            errors.append(f"{where}: missing 'id'")
        elif tid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(tid)
        extra = sorted(set(term) - TERM_KEYS)
        if extra:
            warnings.append(f"{where}: unknown keys {extra} are ignored")

        weight = term.get("weight")
        if not is_number(weight) or weight <= 0:
            errors.append(f"{where}: 'weight' must be a positive number")
        else:
            total += weight

        kind = term.get("kind")
        if kind not in KINDS:
            errors.append(f"{where}: 'kind' must be one of {sorted(KINDS)}")
        elif kind == "judge":
            errors.extend(f"{where}: {e}" for e in validate_rubric(term.get("rubric")))
        elif kind == "computed":
            if not term.get("measure"):
                errors.append(f"{where}: computed term needs 'measure'")
            errors.extend(f"{where}: {e}" for e in validate_normalize(term.get("normalize")))
        elif kind == "checklist":
            errors.extend(f"{where}: {e}" for e in validate_checks(term.get("items"), "item", required=True))

    if terms and all(isinstance(t, dict) for t in terms) and abs(total - 1.0) > TOLERANCE:
        errors.append(f"weights sum to {total:.6f}, not 1 (run 'normalize-weights')")

    errors.extend(f"gates: {e}" for e in validate_checks(metric.get("gates"), "gate", required=False))
    caps = metric.get("caps")
    errors.extend(f"caps: {e}" for e in validate_checks(caps, "cap", required=False))
    for cap in caps if isinstance(caps, list) else []:
        if isinstance(cap, dict) and not (is_number(cap.get("max_total")) and 0 <= cap["max_total"] <= 1):
            errors.append(f"caps: cap {cap.get('id')}: 'max_total' must be a number in [0, 1]")
    return errors, warnings


def validate_rubric(rubric) -> list[str]:
    if not isinstance(rubric, dict) or not rubric:
        return ["judge term needs a 'rubric' mapping of score -> description"]
    levels = []
    for key in rubric:
        try:
            levels.append(float(key))
        except (TypeError, ValueError):
            return [f"rubric anchor '{key}' is not a number; use scores like 0.0, 0.5, 1.0"]
    if not {0.0, 0.5, 1.0} <= set(levels):
        return ["rubric needs at least the anchors 0.0, 0.5 and 1.0"]
    if any(not 0 <= lvl <= 1 for lvl in levels):
        return ["rubric anchors must lie in [0, 1]"]
    return []


def validate_checks(entries, what: str, required: bool) -> list[str]:
    if entries is None:
        return [f"needs a list of {what}s"] if required else []
    if not isinstance(entries, list) or (required and not entries):
        return [f"{what}s must be a non-empty list" if required else f"{what}s must be a list"]
    errors, ids = [], []
    for j, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"{what} {j}: must be a mapping with 'id' and 'check'")
            continue
        ids.append(entry.get("id"))
        if not entry.get("check"):
            errors.append(f"{what} {entry.get('id') or j}: missing 'check'")
    if None in ids or len(set(ids)) != len(ids):
        errors.append(f"every {what} needs a unique 'id'")
    return errors


def validate_normalize(spec) -> list[str]:
    if not isinstance(spec, dict) or spec.get("type") not in NORMALIZE_FIELDS:
        return [f"'normalize.type' must be one of {sorted(NORMALIZE_FIELDS)}"]
    missing = [f for f in NORMALIZE_FIELDS[spec["type"]] if f not in spec]
    if missing:
        return [f"normalize ({spec['type']}) is missing {missing}"]
    fields = BAND_ORDER if spec["type"] == "band" else NORMALIZE_FIELDS[spec["type"]]
    numeric = [f for f in fields if f != "op" and f in spec]
    not_numbers = [f for f in numeric if not is_number(spec[f])]
    if not_numbers:
        return [f"normalize ({spec['type']}): {not_numbers} must be numbers"]
    if spec["type"] == "linear" and spec["worst"] == spec["best"]:
        return ["normalize (linear): 'worst' and 'best' must differ"]
    if spec["type"] == "band":
        points = [spec[f] for f in BAND_ORDER if f in spec]
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
        lo0, lo1, hi1, hi0 = (spec.get(f) for f in BAND_ORDER)
        if lo1 <= raw <= hi1:
            return 1.0
        if raw < lo1:
            if lo0 is None:
                return 1.0
            return clamp((raw - lo0) / (lo1 - lo0)) if lo1 > lo0 else 0.0
        if hi0 is None:
            return 1.0
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

    cap_results = scores.get("caps", {})
    caps = []
    for cap in metric.get("caps") or []:
        result = cap_results.get(cap["id"])
        if result is None:
            raise ValueError(f"no result for cap '{cap['id']}'")
        caps.append({"id": cap["id"], "pass": bool(result["pass"]), "max_total": cap["max_total"],
                     "evidence": result.get("evidence", "")})

    total_uncapped = round(sum(r["contribution"] for r in rows), 4)
    failed_caps = [c for c in caps if not c["pass"]]
    total = min([total_uncapped] + [c["max_total"] for c in failed_caps])
    threshold = metric.get("accept_threshold")
    meets_threshold = threshold is None or total >= threshold
    return {
        "artifact": scores.get("artifact"),
        "metric": metric["name"],
        "metric_version": metric.get("version"),
        "total": total,
        "total_uncapped": total_uncapped,
        "capped_by": [c["id"] for c in failed_caps],
        "accept_threshold": threshold,
        "meets_threshold": meets_threshold,
        "gates_passed": all(g["pass"] for g in gates),
        "acceptable": all(g["pass"] for g in gates) and meets_threshold,
        "terms": rows,
        "gates": gates,
        "caps": caps,
        "biggest_levers": [r["id"] for r in sorted(rows, key=lambda r: -r["headroom"]) if r["headroom"] > 0],
    }


def to_markdown(result: dict) -> str:
    threshold = result.get("accept_threshold")
    lines = [
        f"**Total: {result['total']:.2f}** / 1.00 — metric `{result['metric']}` v{result['metric_version']}"
        + (f" (accept at ≥ {threshold:.2f})" if threshold is not None else ""),
        f"**Gates:** {'all passed' if result['gates_passed'] else 'FAILED'}",
        *([f"**Capped** by {', '.join(result['capped_by'])} (uncapped total {result['total_uncapped']:.2f})"]
          if result.get("capped_by") else []),
        f"**Acceptable:** {'yes' if result['acceptable'] else 'no'}",
        "",
        "| Term | Weight | Score | Contribution | Headroom |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in result["terms"]:
        lines.append(f"| {r['name']} | {r['weight']:.2f} | {r['score']:.2f} | {r['contribution']:.3f} | {r['headroom']:.3f} |")
    for g in result["gates"]:
        lines.append(f"\n- Gate `{g['id']}`: {'pass' if g['pass'] else 'FAIL'} — {g['evidence']}")
    for c in result.get("caps", []):
        lines.append(f"\n- Cap `{c['id']}` (max {c['max_total']:.2f}): {'pass' if c['pass'] else 'FAIL'} — {c['evidence']}")
    return "\n".join(lines)


def normalize_weights(path: str, metric: dict) -> str:
    """Rescale weights to sum to 1 (3 decimals) and rewrite only the weight lines."""
    terms = metric["terms"]
    total = sum(t["weight"] for t in terms)
    new = [round(t["weight"] / total, 3) for t in terms]
    # Put any rounding residue on the largest term so the sum is exactly 1.
    largest = max(range(len(new)), key=lambda i: new[i])
    new[largest] = round(new[largest] + 1 - sum(new), 3)

    text = Path(path).read_text()
    # Matches block style ("weight: 0.3") and flow style ("{id: a, weight: 0.3, ...}").
    pattern = re.compile(r"((?<![\w-])weight:\s*)([0-9][0-9.eE+-]*)()")
    matches = list(pattern.finditer(text))
    if len(matches) == len(terms):
        # Edit the weight lines in place so comments and formatting survive.
        values = iter(new)
        text = pattern.sub(lambda m: f"{m.group(1)}{next(values):g}{m.group(3)}", text)
        Path(path).write_text(text)
    else:
        for t, w in zip(terms, new):
            t["weight"] = w
        Path(path).write_text(yaml.safe_dump(metric, sort_keys=False, allow_unicode=True, width=100))
        print("note: rewrote the whole file; YAML comments were not kept", file=sys.stderr)
    return f"weights rescaled (previous sum {total:g}): " + ", ".join(
        f"{t['id']}={w:g}" for t, w in zip(terms, new))


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

    try:
        metric = load_metric(args.metric)
    except MetricError as e:
        print(f"Metric is invalid:\n  - {e}", file=sys.stderr)
        return 1

    errors, warnings = validate(metric, Path(args.metric).resolve().parent)
    if args.cmd == "normalize-weights":
        # A wrong weight sum is what normalize-weights fixes.
        errors = [e for e in errors if not e.startswith("weights sum to")]
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        print("Metric is invalid:\n" + "\n".join(f"  - {e}" for e in errors), file=sys.stderr)
        return 1

    if args.cmd == "normalize-weights":
        print(normalize_weights(args.metric, metric))
        return 0
    if args.cmd == "validate":
        caps = len(metric.get("caps") or [])
        print(f"OK: '{metric['name']}' with {len(metric['terms'])} terms, {len(metric.get('gates') or [])} gates"
              + (f", {caps} caps" if caps else "")
              + (f", {len(warnings)} warning(s)" if warnings else ""))
        return 0

    try:
        with open(args.scores) as f:
            scores = json.load(f)
        result = aggregate(metric, scores)
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
        print(f"Cannot aggregate: {e}", file=sys.stderr)
        return 1
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(to_markdown(result) if args.markdown else json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
