# Taskwiser Hiring Funnel QA

Python proof-of-work for a junior software engineer application. The tool audits Taskwiser-style candidate pipeline events for duplicate applications, screening response-time breaches and stage-history quality, then writes JSON and HTML reports.

## Run

```bash
python3 -m unittest -v
python3 hiring_funnel.py sample_events.jsonl --screen-sla-hours 48
```

Outputs:

- `hiring-funnel-report.json` for pipeline checks
- `hiring-funnel-report.html` for human review

The JSONL fixture is representative sample data only, not production candidate data or a claimed Taskwiser metric.
