"""Run the eval fixtures against the real skills.

  just eval                      # all cases
  just eval --case clean-roles   # one case
  just eval-changed              # only cases affected by changes vs origin/main

Costs real tokens (your Claude login or ANTHROPIC_API_KEY). Defaults: model
haiku (EVAL_MODEL), 3 repeats, a case passes at 2 of 3, $1 per run, $10 total.
"""

import argparse
import asyncio
import math
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import json  # noqa: E402

from grade import grade_step, snapshot  # noqa: E402
from runner import run_step  # noqa: E402
from selection import FIXTURES, ROOT, affected, changed_paths, load_cases  # noqa: E402


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case", action="append", default=[], help="case name (repeatable)")
    p.add_argument("--changed-from", metavar="REF", help="select cases affected by changes vs REF")
    p.add_argument("--list", action="store_true", help="print the selected cases and exit")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--model", default=os.environ.get("EVAL_MODEL", "haiku"))
    p.add_argument("--budget", type=float, default=1.0, help="max USD per run")
    p.add_argument("--max-total-usd", type=float, default=10.0, help="abort when total cost reaches this")
    p.add_argument("--max-turns", type=int, default=60)
    p.add_argument(
        "--cli",
        default=os.environ.get("EVAL_CLAUDE_CLI") or shutil.which("claude"),
        help="claude executable (default: EVAL_CLAUDE_CLI, else `claude` on PATH, else the SDK's bundled copy)",
    )
    p.add_argument("--plugin-root", default=str(ROOT), help="plugin directory to load (default: this repo)")
    p.add_argument("--out", default=str(ROOT / "tests" / "evals" / "out"))
    p.add_argument("--keep", action="store_true", help="keep scratch projects")
    return p.parse_args(argv)


def select(args, cases):
    if args.case:
        unknown = [c for c in args.case if c not in cases]
        if unknown:
            sys.exit(f"unknown case(s): {unknown}; have {sorted(cases)}")
        return args.case
    if args.changed_from:
        return affected(changed_paths(args.changed_from), cases)
    return sorted(cases)


async def run_case_once(name, spec, args, out_dir, run_no):
    scratch = Path(tempfile.mkdtemp(prefix=f"castlist-eval-{name}-"))
    project = scratch / "project"
    shutil.copytree(FIXTURES / name / "project", project)
    failures, warnings, cost = [], [], 0.0
    try:
        for i, step in enumerate(spec["steps"], 1):
            before = snapshot(project)
            res = await run_step(
                step["prompt"], step.get("answers", []), project, args.plugin_root,
                args.model, args.budget, args.max_turns, args.cli,
            )
            after = snapshot(project)
            cost += res.cost
            step_fail, step_warn = [], []
            if res.error:
                step_fail.append(res.error)
            g_fail, g_warn = grade_step(
                step.get("expect", {}), before, after, project,
                len(res.questions), res.unmatched, res.texts + [
                    q.get("question", "") + " " + " ".join(o.get("label", "") for o in q.get("options", []))
                    for q in res.questions
                ],
            )
            step_fail += g_fail
            step_warn += g_warn
            for d in res.denied:
                step_warn.append(f"denied tool call: {d}")
            failures += [f"step {i}: {m}" for m in step_fail]
            warnings += [f"step {i}: {m}" for m in step_warn]
            run_dir = Path(out_dir) / name / f"run{run_no}"
            run_dir.mkdir(parents=True, exist_ok=True)
            with open(run_dir / f"step{i}.jsonl", "w") as fh:
                for row in res.transcript:
                    fh.write(json.dumps(row, default=repr) + "\n")
            (run_dir / f"step{i}.json").write_text(json.dumps({
                "prompt": step["prompt"], "subtype": res.subtype, "turns": res.turns,
                "duration_ms": res.duration_ms, "cost_usd": res.cost,
                "questions": [q.get("question") for q in res.questions],
                "failures": step_fail, "warnings": step_warn,
                "final_text": "\n".join(res.texts)[-4000:],
            }, indent=2))
            if res.error and not res.loaded and not res.transcript[1:]:
                break
    finally:
        if not args.keep:
            shutil.rmtree(scratch, ignore_errors=True)
        else:
            print(f"  kept {scratch}")
    return failures, warnings, cost


async def main_async(args):
    cases = load_cases()
    selected = select(args, cases)
    if not selected:
        print("no affected eval cases")
        return 0
    if args.list:
        print("\n".join(selected))
        return 0

    need = math.ceil(args.repeats * 2 / 3)
    total, aborted, rows, exit_code = 0.0, False, [], 0
    print(f"model={args.model} cli={args.cli or 'bundled'} repeats={args.repeats} need={need}")
    for name in selected:
        spec, passes, case_cost, notes = cases[name], 0, 0.0, []
        for run_no in range(1, args.repeats + 1):
            if total >= args.max_total_usd:
                aborted = True
                break
            failures, warnings, cost = await run_case_once(name, spec, args, args.out, run_no)
            total += cost
            case_cost += cost
            passes += not failures
            status = "PASS" if not failures else "FAIL"
            print(f"  {name} run {run_no}: {status} (${cost:.3f})")
            for m in failures[:3]:
                print(f"    - {m}")
            notes += failures[:1] or warnings[:1]
        gating = spec.get("gating", True)
        ok = passes >= need
        rows.append((name, passes, args.repeats, case_cost, ok, gating, notes[:1]))
        if gating and not ok:
            exit_code = 1
        if aborted:
            break

    lines = ["| case | passes | cost | result | note |", "|---|---|---|---|---|"]
    for name, passes, reps, cost, ok, gating, note in rows:
        result = "PASS" if ok else ("FAIL" if gating else "fail (non-gating)")
        lines.append(f"| {name} | {passes}/{reps} | ${cost:.2f} | {result} | {(note[0] if note else '')[:80]} |")
    lines.append(f"\nTotal cost: ${total:.2f}")
    summary = "\n".join(lines)
    print("\n" + summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as fh:
            fh.write(f"## Eval results ({args.model})\n\n{summary}\n")
    if aborted:
        print(f"aborted: total cost reached ${args.max_total_usd:.2f}", file=sys.stderr)
        return 2
    return exit_code


def main():
    sys.exit(asyncio.run(main_async(parse_args())))


if __name__ == "__main__":
    main()
