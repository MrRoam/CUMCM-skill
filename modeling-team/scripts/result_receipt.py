#!/usr/bin/env python3
"""Seal/check/compare declared result provenance. Python 3.8+, no execution.

Spec (paths relative to --root; references use JSON Pointer, RFC 6901):
{"inputs":{"data":"data.csv"}, "evaluators":{"model":"model.py"},
 "candidate":{"layout":"layout.csv"}, "run":{"settings":"run.json"},
 "evaluation":{"assumptions":{"path":"scope.json","pointer":""}},
 "metrics":{"score":{"path":"result.json","pointer":"/score",
                      "unit":"kW/m2","direction":"max"}}}

evaluation must include assumptions, averaging/validation definition, constraints
and numerical accuracy settings needed for a fair comparison. Select those fields
from actual JSON files; exclude candidate decisions, seed and search algorithm.
Units may instead be references {"path":...,"pointer":...}. Literal units are
declarations, not physical validation. No tool can infer omitted model assumptions.
Files in all roles are verified; only inputs/evaluators/evaluation define shared
comparison scope. Candidate and run differences are expected, not disqualifying.
Register the entry point AND every local physics/preprocessing module it calls,
evaluation-affecting configuration, and actual dependency versions (for example
a lock file). Read their dependencies before claiming registration is complete.
No automatic dependency discovery is performed: unchecked coverage means only
registered files/fields are comparable, never the entire mathematical model.
Changed file bytes can be comments/formatting; inspect the diff or recompute with
common evaluator/data versions. Resealing old outputs is not recomputation.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path, PureWindowsPath

VERSION = "modeling-result-receipt/1"
BOUNDARY = "Only declared provenance and comparison scope checked; no mathematical, optimality or human-review claim."
COVERAGE = "Dependency coverage is not inferred; only registered files and fields were checked."


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local(root, name):
    require(isinstance(name, str) and bool(name.strip()), "Path must be nonempty text")
    p = Path(name)
    require(not p.is_absolute() and not PureWindowsPath(name).drive
            and not PureWindowsPath(name).root, "Absolute path forbidden: " + name)
    require(".." not in p.parts and ".." not in PureWindowsPath(name).parts,
            "Parent traversal forbidden: " + name)
    resolved = (root / p).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ValueError("Path escapes project root: " + name)
    return resolved


def read_json(path):
    require(path.is_file(), "Missing file: " + str(path))
    require(path.stat().st_size <= 4_000_000, "JSON exceeds 4 MB: " + str(path))
    def reject(value):
        raise ValueError("Nonfinite JSON value: " + value)
    with path.open(encoding="utf-8-sig") as stream:
        return json.load(stream, parse_constant=reject)


def digest(path):
    require(path.is_file(), "Missing file: " + str(path))
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def at_pointer(document, pointer):
    require(isinstance(pointer, str) and (pointer == "" or pointer.startswith("/")),
            "JSON pointer must be empty or start with /")
    if pointer == "":
        return document
    value = document
    for part in pointer[1:].split("/"):
        i = 0
        while i < len(part):
            if part[i] == "~":
                require(i + 1 < len(part) and part[i + 1] in "01", "Invalid JSON pointer escape")
                i += 1
            i += 1
        key = part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            require(key.isdigit() and (key == "0" or not key.startswith("0")), "Invalid array index")
            value = value[int(key)]
        else:
            require(isinstance(value, dict), "JSON pointer traverses a scalar")
            value = value[key]
    return value


def mapping(value, label, nonempty=True):
    require(isinstance(value, dict) and (bool(value) or not nonempty), label + " must be a nonempty object")
    require(all(isinstance(k, str) and bool(k.strip()) for k in value), label + " names must be nonempty")
    return value


def file_record(root, name):
    return {"path": name, "sha256": digest(local(root, name))}


def reference(root, ref):
    mapping(ref, "Reference")
    require(set(ref) == {"path", "pointer"}, "Reference needs only path and pointer")
    record = file_record(root, ref["path"])
    record["pointer"] = ref["pointer"]
    record["value"] = at_pointer(read_json(local(root, ref["path"])), ref["pointer"])
    # Also rejects overflowed floats such as 1e999 anywhere in a selected value.
    json.dumps(record["value"], allow_nan=False)
    return record


def numeric(value):
    require(type(value) in (int, float) and math.isfinite(value), "Metric must be a finite number, not null/bool/text")


def seal(root, spec):
    mapping(spec, "Spec")
    allowed = {"inputs", "evaluators", "candidate", "run", "evaluation", "metrics"}
    require(not set(spec) - allowed, "Unknown spec fields: " + str(set(spec) - allowed))
    result = {"format": VERSION, "boundary": BOUNDARY}
    for role in ("inputs", "evaluators", "candidate", "run"):
        entries = mapping(spec.get(role, {}), role, role != "run")
        result[role] = {name: file_record(root, path) for name, path in entries.items()}
    result["evaluation"] = {name: reference(root, ref) for name, ref in
                            mapping(spec.get("evaluation"), "evaluation").items()}
    result["metrics"] = {}
    for name, metric in mapping(spec.get("metrics"), "metrics").items():
        mapping(metric, "Metric " + name)
        require(set(metric) == {"path", "pointer", "unit", "direction"},
                "Metric needs path, pointer, unit and direction: " + name)
        record = reference(root, {k: metric[k] for k in ("path", "pointer")})
        numeric(record["value"])
        unit = metric["unit"]
        if isinstance(unit, dict):
            record["unit_source"] = reference(root, unit)
            unit = record["unit_source"]["value"]
        require(isinstance(unit, str) and bool(unit.strip()), "Unit must be nonempty; use '1' for dimensionless")
        require(metric["direction"] in ("max", "min"), "Direction must be max or min")
        record.update(unit=unit, direction=metric["direction"])
        result["metrics"][name] = record
    return result


def check(root, receipt):
    mapping(receipt, "Receipt")
    require(receipt.get("format") == VERSION, "Unknown receipt format")
    # Rebuild from recorded sources, so metric edits and changed files both fail.
    spec = {}
    for role in ("inputs", "evaluators", "candidate", "run"):
        spec[role] = {name: record["path"] for name, record in
                      mapping(receipt.get(role), role, role != "run").items()}
    spec["evaluation"] = {name: {k: record[k] for k in ("path", "pointer")}
                          for name, record in mapping(receipt.get("evaluation"), "evaluation").items()}
    spec["metrics"] = {}
    for name, record in mapping(receipt.get("metrics"), "metrics").items():
        metric = {k: record[k] for k in ("path", "pointer", "unit", "direction")}
        if "unit_source" in record:
            metric["unit"] = {k: record["unit_source"][k] for k in ("path", "pointer")}
        spec["metrics"][name] = metric
    fresh = seal(root, spec)
    for section in fresh:
        require(fresh[section] == receipt.get(section), "Changed or inconsistent receipt section: " + section)
    return fresh


def compare(root_a, a, root_b, b):
    a, b = check(root_a, a), check(root_b, b)
    mismatches = []
    file_changes = []
    for role in ("inputs", "evaluators"):
        if {k: v["sha256"] for k, v in a[role].items()} != {k: v["sha256"] for k, v in b[role].items()}:
            file_changes.append(role)
    if {k: v["value"] for k, v in a["evaluation"].items()} != {k: v["value"] for k, v in b["evaluation"].items()}:
        mismatches.append("evaluation")
    if set(a["metrics"]) != set(b["metrics"]):
        mismatches.append("metric names")
    for name in set(a["metrics"]) & set(b["metrics"]):
        for key in ("unit", "direction"):
            if a["metrics"][name][key] != b["metrics"][name][key]:
                mismatches.append(name + ":" + key)
    reasons = []
    if file_changes:
        reasons.append("registered file content changed (" + ", ".join(file_changes)
                       + "); semantic equivalence unknown; inspect diff or recompute with common evaluator/data versions")
    if mismatches:
        reasons.append("declared evaluation/metric values differ: " + ", ".join(mismatches))
    require(not reasons, "Refuse direct ranking; " + "; ".join(reasons))
    comparisons = {}
    for name, record in a["metrics"].items():
        av, bv = record["value"], b["metrics"][name]["value"]
        winner = "tie" if av == bv else ("a" if (av > bv) == (record["direction"] == "max") else "b")
        comparisons[name] = {"a": av, "b": bv, "b_minus_a": bv - av,
                             "unit": record["unit"], "better_numeric_value": winner}
    return {"comparable_under_declared_scope": True, "metrics": comparisons,
            "coverage_note": COVERAGE,
            "boundary": BOUNDARY + " Numeric ordering does not establish feasibility or statistical significance."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("seal", "check", "compare"))
    parser.add_argument("source", help="Spec for seal, receipt for check/compare")
    parser.add_argument("--root", default=".", help="Project root; all paths must stay inside it")
    parser.add_argument("--out", help="New receipt path for seal; existing files are never overwritten")
    parser.add_argument("--other", help="Second receipt for compare")
    parser.add_argument("--other-root", help="Second checkout root; defaults to --root")
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve()
        require(root.is_dir(), "Project root is missing")
        source = read_json(local(root, args.source))
        if args.action == "seal":
            require(args.out is not None, "seal requires --out")
            output = local(root, args.out)
            result = seal(root, source)
            with output.open("x", encoding="utf-8") as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write("\n")
            result = {"sealed": args.out, "boundary": BOUNDARY, "coverage_note": COVERAGE}
        elif args.action == "check":
            check(root, source)
            result = {"provenance_valid": True, "boundary": BOUNDARY, "coverage_note": COVERAGE}
        else:
            require(args.other is not None, "compare requires --other")
            other_root = Path(args.other_root).resolve() if args.other_root else root
            result = compare(root, source, other_root, read_json(local(other_root, args.other)))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, IndexError, TypeError, OverflowError) as exc:
        print("Receipt error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
