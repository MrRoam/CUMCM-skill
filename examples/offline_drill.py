#!/usr/bin/env python3
"""Create three synthetic local clones and offline bundles in a NEW --out directory.

No accounts, network, global Git writes or oracle files. Python 3.8+ and Git.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "examples/supply-plan"
RECEIPT = REPO / "modeling-team/scripts/result_receipt.py"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create(root):
    # Discard inherited Git overrides; don't read account/global configuration.
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="Synthetic Team Drill", GIT_COMMITTER_NAME="Synthetic Team Drill",
               GIT_AUTHOR_EMAIL="drill@example.invalid", GIT_COMMITTER_EMAIL="drill@example.invalid",
               GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")

    def git(path, *args):
        process = subprocess.run(["git", "-C", str(path)] + list(args), env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode:
            raise RuntimeError(process.stderr.decode("utf-8", "replace"))
        return process.stdout.decode("utf-8", "replace").strip()

    root.mkdir()  # Atomic refusal of existing output; preserve old evidence.
    source = root / "seed"
    source.mkdir()
    for name in ("TASK.md", "data.json", "supply.py", "sample_result.json"):
        shutil.copyfile(FIXTURE / name, source / name)
    (source / ".gitignore").write_text("__pycache__/\n.agents/\n", encoding="utf-8")
    (source / ".gitattributes").write_text("* text=auto\n*.json text eol=lf\n*.md text eol=lf\n*.py text eol=lf\n", encoding="utf-8")
    git(source, "init", "-b", "main")
    git(source, "config", "core.autocrlf", "false")
    git(source, "add", ".")
    git(source, "commit", "-m", "Synthetic supply-point task and evaluator")
    initial = git(source, "rev-parse", "HEAD")
    for name in ("modeler", "solver", "integrator"):
        git(root, "clone", "--no-hardlinks", str(source), name)
        git(root / name, "config", "core.autocrlf", "false")

    model = root / "modeler"
    git(model, "switch", "-c", "task/model-change")
    data = json.loads((model / "data.json").read_text(encoding="utf-8"))
    data["evaluation"]["min_covered_people"] = 900
    write(model / "data.json", data)
    task = (model / "TASK.md").read_text(encoding="utf-8")
    task = task.replace("至少覆盖700人", "至少覆盖900人").replace("满足练习的两项约束", "不满足新版最低900人的覆盖约束")
    (model / "TASK.md").write_text(task, encoding="utf-8")
    (model / "DECISION.md").write_text("合成演练中的团队决定：最低覆盖从700提高到900，其他口径保持不变。以当前data.json和TASK.md为准。\n", encoding="utf-8")
    git(model, "add", "data.json", "TASK.md", "DECISION.md")
    git(model, "commit", "-m", "Update minimum demand coverage")

    solver = root / "solver"
    git(solver, "switch", "-c", "task/solver")
    result = json.loads(subprocess.check_output([sys.executable, "-B", str(solver / "supply.py"), "solve"], env=env))
    write(solver / "outputs/result.json", result)
    spec = {"inputs": {"demand_and_costs": "data.json"}, "evaluators": {"coverage": "supply.py"},
            "candidate": {"selected_sites": "outputs/result.json"},
            "evaluation": {"scope": {"path": "data.json", "pointer": "/evaluation"}},
            "metrics": {"coverage_per_cost": {"path": "outputs/result.json", "pointer": "/result/optima/0/score",
                        "unit": {"path": "outputs/result.json", "pointer": "/evaluation/objective_unit"}, "direction": "max"}}}
    write(solver / "outputs/receipt-spec.json", spec)
    module_spec = importlib.util.spec_from_file_location("drill_receipt", RECEIPT)
    rr = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(rr)
    write(solver / "outputs/result-receipt.json", rr.seal(solver.resolve(), spec))
    git(solver, "add", "outputs")
    git(solver, "commit", "-m", "Deliver candidate and declared provenance")

    exchange = root / "exchange"
    exchange.mkdir()
    deliveries = (("modeler", "task/model-change"), ("solver", "task/solver"))
    for name, branch in deliveries:
        bundle = str(exchange / (name + ".bundle"))
        git(root / name, "bundle", "create", bundle, branch)
        git(root / name, "bundle", "verify", bundle)

    integrator = root / "integrator"
    git(integrator, "switch", "-c", "task/integration")
    for name, branch in deliveries:
        git(integrator, "fetch", str(exchange / (name + ".bundle")), branch + ":refs/remotes/team/" + name)
        git(integrator, "merge", "--no-edit", "refs/remotes/team/" + name)
    proof = {"simulation": "three local clones; no independent accounts or students",
             "initial_commit": initial, "integration_commit": git(integrator, "rev-parse", "HEAD"),
             "git_merge_clean": git(integrator, "status", "--porcelain") == "", "network_used": False}
    try:
        receipt = json.loads((integrator / "outputs/result-receipt.json").read_text(encoding="utf-8"))
        rr.check(integrator.resolve(), receipt)
        proof["receipt_rejected"] = False
    except ValueError as error:
        proof.update(receipt_rejected=True, receipt_error=str(error))
    if not proof["git_merge_clean"] or not proof["receipt_rejected"]:
        raise RuntimeError("Drill did not reproduce a clean merge with stale-result rejection")
    write(root / "setup-evidence.json", proof)
    return proof


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="Explicit new output directory; parent must already exist")
    args = parser.parse_args()
    try:
        output = Path(args.out).absolute()
        if output.exists() or output.is_symlink():
            raise ValueError("Output already exists; choose a new directory")
        if not output.parent.is_dir():
            raise ValueError("Output parent directory is missing")
        if not RECEIPT.is_file() or not FIXTURE.is_dir():
            raise ValueError("Run from an intact skills repository")
        if shutil.which("git") is None:
            raise ValueError("Git is required")
        print(json.dumps(create(output.resolve()), ensure_ascii=False))
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("Drill error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
