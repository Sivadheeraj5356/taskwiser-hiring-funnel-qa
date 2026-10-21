#!/usr/bin/env python3
"""Audit Taskwiser-style candidate pipeline events and write JSON/HTML reports."""
import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

STAGES = ["applied", "screened", "interviewed", "offered", "hired"]


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_events(path):
    events = []
    for line_no, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        for field in ("candidate_id", "stage", "event_at", "source"):
            if field not in row:
                raise ValueError(f"line {line_no}: missing {field}")
        if row["stage"] not in STAGES:
            raise ValueError(f"line {line_no}: unknown stage {row['stage']}")
        events.append(row)
    return events


def build_report(events, screen_sla_hours=48):
    by_candidate = defaultdict(list)
    for row in events:
        by_candidate[row["candidate_id"]].append(row)

    candidates = []
    invalid_order = 0
    duplicates = 0
    sla_breaches = 0
    for candidate_id, rows in sorted(by_candidate.items()):
        rows.sort(key=lambda r: parse_time(r["event_at"]))
        stage_indexes = [STAGES.index(r["stage"]) for r in rows]
        has_invalid_order = any(b < a for a, b in zip(stage_indexes, stage_indexes[1:]))
        duplicate_stages = len(stage_indexes) - len(set(stage_indexes))
        applied_at = parse_time(rows[0]["event_at"])
        screened = [r for r in rows if r["stage"] == "screened"]
        screen_hours = None
        if screened:
            screen_hours = round((parse_time(screened[0]["event_at"]) - applied_at).total_seconds() / 3600, 2)
        invalid_order += has_invalid_order
        duplicates += duplicate_stages
        sla_breaches += bool(screen_hours is not None and screen_hours > screen_sla_hours)
        candidates.append({
            "candidate_id": candidate_id,
            "events": len(rows),
            "current_stage": rows[-1]["stage"],
            "source": rows[0]["source"],
            "screen_hours": screen_hours,
            "invalid_stage_order": has_invalid_order,
            "duplicate_stage_events": duplicate_stages,
        })

    total = len(candidates)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "screen_sla_hours": screen_sla_hours,
        "total_candidates": total,
        "invalid_stage_order": invalid_order,
        "duplicate_stage_events": duplicates,
        "screen_sla_breaches": sla_breaches,
        "candidates": candidates,
    }


def render_html(report):
    rows = "".join(
        f"<tr><td>{c['candidate_id']}</td><td>{c['current_stage']}</td><td>{c['source']}</td><td>{c['screen_hours'] if c['screen_hours'] is not None else '-'}</td><td>{'yes' if c['invalid_stage_order'] else 'no'}</td><td>{c['duplicate_stage_events']}</td></tr>"
        for c in report["candidates"]
    )
    return f"""<!doctype html><meta charset='utf-8'><title>Hiring funnel QA</title><style>body{{font-family:Inter,system-ui;margin:40px;color:#18201d}}table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #dfe7e2;padding:10px;text-align:left}}th{{background:#eef6f1}}</style><h1>Candidate pipeline QA</h1><p>{report['total_candidates']} candidates • {report['screen_sla_breaches']} screening SLA breaches • {report['invalid_stage_order']} stage-order issues</p><table><tr><th>Candidate</th><th>Current stage</th><th>Source</th><th>Screen hours</th><th>Order issue</th><th>Duplicate stages</th></tr>{rows}</table>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("events", help="JSONL events with candidate_id, stage, event_at, source")
    parser.add_argument("--screen-sla-hours", type=int, default=48)
    parser.add_argument("--json-out", default="hiring-funnel-report.json")
    parser.add_argument("--html-out", default="hiring-funnel-report.html")
    args = parser.parse_args()
    report = build_report(load_events(args.events), args.screen_sla_hours)
    Path(args.json_out).write_text(json.dumps(report, indent=2) + "\n")
    Path(args.html_out).write_text(render_html(report) + "\n")
    print(f"audited {report['total_candidates']} candidates; {report['screen_sla_breaches']} SLA breaches")


if __name__ == "__main__":
    main()
