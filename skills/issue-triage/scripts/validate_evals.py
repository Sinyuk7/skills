#!/usr/bin/env python3
"""Validate issue-triage eval files locally.

Checks two files under skills/issue-triage/evals/:
  - evals.json (task-level evals)
  - routing-evals.json (router-level evals)

Exit code:
  0 = all checks passed
  1 = at least one check failed

Checks performed:
  evals.json:
    - schema fields present (skill_name, version, groups, priority_order, evals[])
    - every eval has: id, title, group, priority, prompt, setup, expectations[]
    - every eval.group appears in groups[]
    - every eval.priority appears in priority_order
    - eval ids are unique and follow 'E\\d+' pattern
    - expectations is a non-empty list of strings
    - no empty / placeholder prompts

  routing-evals.json:
    - schema fields present (skill_name, cases[], expected_mode_legend)
    - every case has: id, request, expected_skills, expected_mode, ambiguity, reason
    - case ids are unique
    - every expected_mode appears as a key in expected_mode_legend
    - exclusive / sequential cases must have non-empty expected_skills
    - abstain cases must have empty expected_skills
    - ambiguity value is one of {low, medium, high}
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
EVALS_JSON = SKILL_ROOT / "evals" / "evals.json"
ROUTING_EVALS_JSON = SKILL_ROOT / "evals" / "routing-evals.json"

EVAL_ID_RE = re.compile(r"^E\d+$")
VALID_AMBIGUITY = {"low", "medium", "high"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def ok(self) -> bool:
        return not self.errors


def _require_keys(obj: dict, keys: list[str], context: str, report: Report) -> None:
    for k in keys:
        if k not in obj:
            report.err(f"{context}: missing required key '{k}'")


def validate_evals_json(path: Path, report: Report) -> None:
    if not path.exists():
        report.err(f"{path} does not exist")
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.err(f"{path}: invalid JSON: {exc}")
        return

    _require_keys(data, ["skill_name", "version", "groups", "priority_order", "evals"], str(path), report)
    groups = set(data.get("groups", []))
    priorities = set(data.get("priority_order", []))
    evals = data.get("evals", [])

    if not isinstance(evals, list) or not evals:
        report.err(f"{path}: evals must be a non-empty array")
        return

    seen_ids: set[str] = set()

    for i, ev in enumerate(evals):
        ctx = f"{path.name}[evals[{i}]]"
        if not isinstance(ev, dict):
            report.err(f"{ctx}: entry must be an object")
            continue

        _require_keys(
            ev,
            ["id", "title", "group", "priority", "prompt", "setup", "expectations"],
            ctx,
            report,
        )

        eid = ev.get("id", "")
        if eid in seen_ids:
            report.err(f"{ctx}: duplicate id '{eid}'")
        seen_ids.add(eid)

        if not isinstance(eid, str) or not EVAL_ID_RE.match(eid):
            report.err(f"{ctx}: id '{eid}' must match ^E\\d+$")

        grp = ev.get("group", "")
        if grp and grp not in groups:
            report.err(f"{ctx}: group '{grp}' not declared in groups[]")

        prio = ev.get("priority", "")
        if prio and prio not in priorities:
            report.err(f"{ctx}: priority '{prio}' not in priority_order {sorted(priorities)}")

        title = ev.get("title", "")
        if not isinstance(title, str) or not title.strip():
            report.err(f"{ctx}: title must be a non-empty string")

        prompt = ev.get("prompt", "")
        if not isinstance(prompt, str) or not prompt.strip():
            report.err(f"{ctx}: prompt must be a non-empty string")

        expectations = ev.get("expectations", [])
        if not isinstance(expectations, list) or not expectations:
            report.err(f"{ctx}: expectations must be a non-empty array")
        else:
            for j, e in enumerate(expectations):
                if not isinstance(e, str) or not e.strip():
                    report.err(f"{ctx}.expectations[{j}]: must be a non-empty string")

    # Coverage sanity: every declared group should have at least one eval
    used_groups = {ev.get("group") for ev in evals if isinstance(ev, dict)}
    unused_groups = groups - used_groups
    if unused_groups:
        report.warn(
            f"{path.name}: declared groups with no evals: {sorted(unused_groups)}"
        )

    # Coverage sanity: priorities the author declared as available but never used
    used_prios = {ev.get("priority") for ev in evals if isinstance(ev, dict)}
    unused_prios = priorities - used_prios
    if unused_prios:
        report.warn(
            f"{path.name}: declared priorities with no evals: {sorted(unused_prios)}"
        )


def validate_routing_evals(path: Path, report: Report) -> None:
    if not path.exists():
        report.err(f"{path} does not exist")
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.err(f"{path}: invalid JSON: {exc}")
        return

    _require_keys(data, ["skill_name", "cases", "expected_mode_legend"], str(path), report)

    legend = data.get("expected_mode_legend", {})
    if not isinstance(legend, dict) or not legend:
        report.err(f"{path}: expected_mode_legend must be a non-empty object")
        return

    valid_modes = set(legend.keys())
    cases = data.get("cases", [])
    if not isinstance(cases, list) or not cases:
        report.err(f"{path}: cases must be a non-empty array")
        return

    seen_ids: set[str] = set()

    for i, c in enumerate(cases):
        ctx = f"{path.name}[cases[{i}]]"
        if not isinstance(c, dict):
            report.err(f"{ctx}: entry must be an object")
            continue

        _require_keys(
            c,
            ["id", "request", "expected_skills", "expected_mode", "ambiguity", "reason"],
            ctx,
            report,
        )

        cid = c.get("id", "")
        if cid in seen_ids:
            report.err(f"{ctx}: duplicate id '{cid}'")
        seen_ids.add(cid)

        mode = c.get("expected_mode", "")
        if mode and mode not in valid_modes:
            report.err(
                f"{ctx}: expected_mode '{mode}' not in legend {sorted(valid_modes)}"
            )

        amb = c.get("ambiguity", "")
        if amb and amb not in VALID_AMBIGUITY:
            report.err(
                f"{ctx}: ambiguity '{amb}' not in {sorted(VALID_AMBIGUITY)}"
            )

        skills = c.get("expected_skills", [])
        if not isinstance(skills, list):
            report.err(f"{ctx}: expected_skills must be an array")
            continue

        if mode in {"exclusive", "sequential", "partial_refuse"} and not skills:
            report.err(
                f"{ctx}: expected_mode '{mode}' requires a non-empty expected_skills array"
            )
        if mode == "abstain" and skills:
            report.err(
                f"{ctx}: expected_mode 'abstain' requires empty expected_skills"
            )
        if mode == "sequential" and len(skills) < 2:
            report.err(
                f"{ctx}: expected_mode 'sequential' requires ≥2 skills in order"
            )

        req = c.get("request", "")
        if not isinstance(req, str) or not req.strip():
            report.err(f"{ctx}: request must be a non-empty string")

    # Mode coverage sanity
    used_modes = {c.get("expected_mode") for c in cases if isinstance(c, dict)}
    unused_modes = valid_modes - used_modes
    if unused_modes:
        report.warn(
            f"{path.name}: legend modes with no cases: {sorted(unused_modes)}"
        )


def main() -> int:
    report = Report()
    validate_evals_json(EVALS_JSON, report)
    validate_routing_evals(ROUTING_EVALS_JSON, report)

    for w in report.warnings:
        print(f"WARN: {w}")

    for e in report.errors:
        print(f"FAIL: {e}")

    if report.ok():
        print(
            f"OK: {EVALS_JSON.name} and {ROUTING_EVALS_JSON.name} pass all checks."
        )
        return 0
    print(f"\n{len(report.errors)} error(s), {len(report.warnings)} warning(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
