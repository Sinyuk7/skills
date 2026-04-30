#!/usr/bin/env python3
"""Deterministic helpers for issue-triage case state management.

State model (3 states at top level):
  - investigating : Phase 1/2 in progress
  - blocked       : Phase 3 concluded with disposition.type=blocked
  - investigated  : Phase 3 concluded with any non-blocked disposition

Disposition types (terminal reasons, stored under `disposition.type`):
  - root_caused        : root cause confirmed; user may open a new session to fix
  - direction_only     : no confirmed root cause, but ranked investigation directions exist
  - blocked            : missing evidence / ambiguous anchor / anchor mismatch
  - wont_fix           : working as intended
  - duplicate          : duplicate of another case
  - already_fixed      : already fixed in some other commit / PR
  - cannot_reproduce   : evidence insufficient to reproduce
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_STATUSES = {"investigating", "blocked", "investigated"}

VALID_CLOSE_TYPES = {
    "root_caused",
    "wont_fix",
    "duplicate",
    "already_fixed",
    "cannot_reproduce",
}

VALID_BLOCKED_KINDS = {
    "missing_evidence",
    "ambiguous_anchor",
    "anchor_mismatch",
    "insufficient_context",
}


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
        if status not in VALID_STATUSES:
            raise SystemExit(f"Invalid status '{status}'. Allowed: {sorted(VALID_STATUSES)}")
        data["status"] = status
    elif "status" not in data:
        data["status"] = "investigating"
    return data


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


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


def command_record_guide(args: argparse.Namespace) -> None:
    """Record which troubleshooting guide Phase 2a used for task planning."""
    payload = {
        "troubleshooting_guide": {
            "status": args.status,  # preloaded_from_upstream | loaded_from_repo | none
            "source": args.source or "",
            "note": args.note or "",
        },
    }
    update_case(args.project_root, args.case_id, payload, "investigating")


def command_close(args: argparse.Namespace) -> None:
    """Close the case with a non-blocked disposition.

    status becomes 'investigated'. Disposition-specific fields:
      - root_caused:       --root-cause-location, --evidence-refs
      - duplicate:         --duplicate-of
      - already_fixed:     --reference
      - wont_fix:          rationale goes into --summary
      - cannot_reproduce:  --summary explains what was tried
    """
    if args.type not in VALID_CLOSE_TYPES:
        raise SystemExit(
            f"Invalid close type '{args.type}'. Allowed: {sorted(VALID_CLOSE_TYPES)}"
        )

    disposition: dict[str, Any] = {
        "type": args.type,
        "summary": args.summary,
    }
    if args.type == "root_caused":
        disposition["root_cause_location"] = args.root_cause_location or ""
        disposition["evidence_refs"] = optional_json(args.evidence_refs, [])
    if args.type == "duplicate":
        disposition["duplicate_of"] = args.duplicate_of or ""
    if args.type == "already_fixed":
        disposition["reference"] = args.reference or ""

    next_action = "sync_overmind" if args.type == "root_caused" else "close"

    payload = {
        "disposition": disposition,
        "evidence_window": optional_json(args.evidence_window, {}),
        "next_step": {
            "action": next_action,
            "note": args.next_step or "Triage complete",
        },
        "closed": now_iso(),
    }
    # Close must clear prior blocked_reason if any.
    update_case(
        args.project_root,
        args.case_id,
        payload,
        "investigated",
        clear=["blocked_reason"],
    )


def command_set_direction(args: argparse.Namespace) -> None:
    """Close the case with disposition=direction_only.

    Used when the investigation cannot confirm a root cause but has
    concrete, ranked hypotheses the user should pursue in a new session.
    """
    directions = optional_json(args.directions, [])
    if not isinstance(directions, list) or not directions:
        raise SystemExit("--directions must be a non-empty JSON array of direction objects.")

    disposition = {
        "type": "direction_only",
        "summary": args.summary,
        "investigation_directions": directions,
    }
    payload = {
        "disposition": disposition,
        "evidence_window": optional_json(args.evidence_window, {}),
        "next_step": {
            "action": "resume_in_new_session",
            "note": args.next_step or "Open a new session to pursue the ranked directions",
        },
        "closed": now_iso(),
    }
    update_case(
        args.project_root,
        args.case_id,
        payload,
        "investigated",
        clear=["blocked_reason"],
    )


def command_record_blocked(args: argparse.Namespace) -> None:
    if args.kind not in VALID_BLOCKED_KINDS:
        raise SystemExit(
            f"Invalid blocked kind '{args.kind}'. Allowed: {sorted(VALID_BLOCKED_KINDS)}"
        )
    disposition = {
        "type": "blocked",
        "summary": args.detail,
        "blocked_reason": {
            "kind": args.kind,
            "detail": args.detail,
        },
    }
    payload = {
        "disposition": disposition,
        # Keep the top-level blocked_reason for backwards-compat readers.
        "blocked_reason": {
            "kind": args.kind,
            "detail": args.detail,
        },
        "next_step": {
            "action": "await_evidence",
            "note": args.next_step,
        },
    }
    update_case(
        args.project_root,
        args.case_id,
        payload,
        "blocked",
        clear=["closed"],
    )


# ---------------------------------------------------------------------------
# Core update
# ---------------------------------------------------------------------------


def update_case(
    project_root: str,
    case_id_value: str,
    payload: dict[str, Any],
    status: str,
    clear: list[str] | None = None,
) -> None:
    path = case_file(project_root, case_id_value)
    existing = load_case(path)
    merged = ensure_base_fields(merge_case(existing, payload), case_id_value, status)
    for key in clear or []:
        merged.pop(key, None)
    dump_case(path, merged)
    print(json.dumps({"case_dir": str(path.parent), "case_file": str(path)}, ensure_ascii=False))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init_case = sub.add_parser("init-case", help="Create or reopen a case for triage.")
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

    record_guide = sub.add_parser(
        "record-guide",
        help="Record which troubleshooting guide informed Phase 2a planning.",
    )
    record_guide.add_argument("--project-root", required=True)
    record_guide.add_argument("--case-id", required=True)
    record_guide.add_argument(
        "--status",
        required=True,
        choices=["preloaded_from_upstream", "loaded_from_repo", "none"],
    )
    record_guide.add_argument("--source", default="")
    record_guide.add_argument("--note", default="")
    record_guide.set_defaults(func=command_record_guide)

    close = sub.add_parser(
        "close",
        help="Close the case with a non-blocked disposition (root_caused / wont_fix / duplicate / already_fixed / cannot_reproduce).",
    )
    close.add_argument("--project-root", required=True)
    close.add_argument("--case-id", required=True)
    close.add_argument("--type", required=True, choices=sorted(VALID_CLOSE_TYPES))
    close.add_argument("--summary", required=True)
    close.add_argument("--root-cause-location", help="For --type root_caused. e.g. 'foo/Bar.kt:142'")
    close.add_argument("--evidence-refs", help="For --type root_caused. JSON array.")
    close.add_argument("--duplicate-of", help="For --type duplicate.")
    close.add_argument("--reference", help="For --type already_fixed. commit SHA or PR link.")
    close.add_argument("--evidence-window", help="JSON object.")
    close.add_argument("--next-step", help="Short operator-facing note.")
    close.set_defaults(func=command_close)

    set_direction = sub.add_parser(
        "set-direction",
        help="Close the case with disposition=direction_only (ranked investigation directions, no confirmed root cause).",
    )
    set_direction.add_argument("--project-root", required=True)
    set_direction.add_argument("--case-id", required=True)
    set_direction.add_argument("--summary", required=True)
    set_direction.add_argument(
        "--directions",
        required=True,
        help='JSON array of direction objects, e.g. \'[{"rank":1,"hypothesis":"...","next_experiment":"..."}]\'',
    )
    set_direction.add_argument("--evidence-window", help="JSON object.")
    set_direction.add_argument("--next-step", help="Short operator-facing note.")
    set_direction.set_defaults(func=command_set_direction)

    record_blocked = sub.add_parser("record-blocked", help="Mark the case blocked.")
    record_blocked.add_argument("--project-root", required=True)
    record_blocked.add_argument("--case-id", required=True)
    record_blocked.add_argument(
        "--kind",
        required=True,
        choices=sorted(VALID_BLOCKED_KINDS),
    )
    record_blocked.add_argument("--detail", required=True)
    record_blocked.add_argument("--next-step", required=True)
    record_blocked.set_defaults(func=command_record_blocked)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


# yaml is imported lazily so that --help works without the dep.
import yaml  # noqa: E402  (must come after argparse setup? — fine at module bottom)


if __name__ == "__main__":
    main()
