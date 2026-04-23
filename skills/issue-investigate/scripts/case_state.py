#!/usr/bin/env python3
"""Deterministic helpers for issue-investigate case state management."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def optional_json(value: str | None, fallback: Any) -> Any:
    if value is None:
        return fallback
    parsed = json.loads(value)
    return parsed


def case_dir(project_root: str, case_id: str) -> Path:
    return Path(project_root).resolve() / ".issue-flow" / "cases" / case_id


def case_file(project_root: str, case_id: str) -> Path:
    return case_dir(project_root, case_id) / "case.yaml"


def load_case(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a YAML object.")
    return data


def dump_case(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)


def merge_evidence_sources(existing: Any, incoming: Any) -> list[dict[str, Any]]:
    current = list(existing or [])
    merged: list[dict[str, Any]] = []
    seen = set()

    for item in current + list(incoming or []):
        if not isinstance(item, dict):
            continue
        key = (item.get("kind"), item.get("path"))
        if key in seen:
            continue
        seen.add(key)
        merged.append(deepcopy(item))
    return merged


def merge_case(existing: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(existing)

    for key, value in payload.items():
        if value is None:
            continue
        if key == "evidence_sources":
            merged[key] = merge_evidence_sources(existing.get(key, []), value)
            continue
        if isinstance(value, dict) and isinstance(existing.get(key), dict):
            nested = deepcopy(existing[key])
            nested.update(value)
            merged[key] = nested
            continue
        merged[key] = deepcopy(value)

    return merged


def ensure_base_fields(data: dict[str, Any], case_id_value: str, status: str | None) -> dict[str, Any]:
    timestamp = now_iso()
    if "case_id" not in data:
        data["case_id"] = case_id_value
    if "created" not in data:
        data["created"] = timestamp
    data["updated"] = timestamp
    if status:
        data["status"] = status
    elif "status" not in data:
        data["status"] = "investigating"
    return data


def command_init_case(args: argparse.Namespace) -> None:
    payload = {
        "summary": args.summary,
        "user_context": args.user_context,
        "evidence_sources": optional_json(args.evidence_sources, []),
        "next_step": {
            "action": "investigate",
            "note": "Normalizing target and inspecting evidence",
        },
    }
    update_case(args.project_root, args.case_id, payload, "investigating")


def command_record_target(args: argparse.Namespace) -> None:
    payload = {
        "primary_question": args.primary_question,
        "primary_time_anchor": args.primary_time_anchor,
        "named_stakeholders": optional_json(args.named_stakeholders, []),
        "secondary_anchors": optional_json(args.secondary_anchors, []),
        "next_step": {
            "action": "investigate",
            "note": "Primary target normalized",
        },
    }
    update_case(args.project_root, args.case_id, payload, "investigating")


def command_record_root_cause(args: argparse.Namespace) -> None:
    payload = {
        "evidence_window": optional_json(args.evidence_window, {}),
        "root_cause": {
            "summary": args.summary,
            "location": args.location,
            "evidence_refs": optional_json(args.evidence_refs, []),
        },
        "next_step": {
            "action": "resolve",
            "note": "Investigation complete",
        },
    }
    update_case(args.project_root, args.case_id, payload, "investigated", clear="blocked_reason")


def command_record_blocked(args: argparse.Namespace) -> None:
    payload = {
        "blocked_reason": {
            "kind": args.kind,
            "detail": args.detail,
        },
        "next_step": {
            "action": "blocked",
            "note": args.next_step,
        },
    }
    update_case(args.project_root, args.case_id, payload, "blocked", clear="root_cause")


def update_case(
    project_root: str,
    case_id_value: str,
    payload: dict[str, Any],
    status: str,
    clear: str | None = None,
) -> None:
    path = case_file(project_root, case_id_value)
    existing = load_case(path)
    merged = ensure_base_fields(merge_case(existing, payload), case_id_value, status)
    if clear:
        merged.pop(clear, None)
    dump_case(path, merged)
    print(json.dumps({"case_dir": str(path.parent), "case_file": str(path)}, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init_case = sub.add_parser("init-case", help="Create or reopen a case for investigation.")
    init_case.add_argument("--project-root", required=True)
    init_case.add_argument("--case-id", required=True)
    init_case.add_argument("--summary", required=True)
    init_case.add_argument("--user-context", default="")
    init_case.add_argument("--evidence-sources", help="JSON array of evidence source objects.")
    init_case.set_defaults(func=command_init_case)

    record_target = sub.add_parser("record-target", help="Persist the normalized investigation target.")
    record_target.add_argument("--project-root", required=True)
    record_target.add_argument("--case-id", required=True)
    record_target.add_argument("--primary-question", required=True)
    record_target.add_argument("--primary-time-anchor")
    record_target.add_argument("--named-stakeholders", help="JSON array.")
    record_target.add_argument("--secondary-anchors", help="JSON array.")
    record_target.set_defaults(func=command_record_target)

    record_root_cause = sub.add_parser("record-root-cause", help="Mark the case investigated.")
    record_root_cause.add_argument("--project-root", required=True)
    record_root_cause.add_argument("--case-id", required=True)
    record_root_cause.add_argument("--summary", required=True)
    record_root_cause.add_argument("--location", default="")
    record_root_cause.add_argument("--evidence-refs", help="JSON array.")
    record_root_cause.add_argument("--evidence-window", help="JSON object.")
    record_root_cause.set_defaults(func=command_record_root_cause)

    record_blocked = sub.add_parser("record-blocked", help="Mark the case blocked.")
    record_blocked.add_argument("--project-root", required=True)
    record_blocked.add_argument("--case-id", required=True)
    record_blocked.add_argument("--kind", required=True, choices=["missing_evidence", "ambiguous_anchor", "anchor_mismatch", "insufficient_context"])
    record_blocked.add_argument("--detail", required=True)
    record_blocked.add_argument("--next-step", required=True)
    record_blocked.set_defaults(func=command_record_blocked)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
