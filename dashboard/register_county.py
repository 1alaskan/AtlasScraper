#!/usr/bin/env python3
"""Add or update a county in dashboard/counties.json so it shows on the Streamlit site.

Usage (paths are relative to the repo root):

    python3 dashboard/register_county.py \
        --slug arapahoe --name "Arapahoe County" --version v3 --run-date 2026-11-10 \
        --ranked step5-analysis/arapahoe/arapahoe_ranked_accounts_v3.csv \
        --evidence step5-analysis/arapahoe/arapahoe_evidence_v3.csv \
        --notes step5-analysis/arapahoe/arapahoe_analysis_notes.md \
        --extra-notes step5-analysis/arapahoe/review_findings.md

Re-running with the same --slug replaces that county's entry. Commit the JSON
and push to main; Streamlit Community Cloud redeploys from main on its own.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "dashboard" / "counties.json"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--slug", required=True, help="lowercase slug, e.g. adams, el_paso")
    p.add_argument("--name", required=True, help='display name, e.g. "Adams County"')
    p.add_argument("--ranked", required=True, help="ranked accounts CSV (repo-relative)")
    p.add_argument("--evidence", required=True, help="evidence CSV (repo-relative)")
    p.add_argument("--notes", required=True, help="analysis notes markdown (repo-relative)")
    p.add_argument("--version", default="v3", help="pipeline version label, e.g. v3, v3b")
    p.add_argument("--run-date", required=True, help="YYYY-MM-DD the ranking was built")
    p.add_argument("--extra-notes", nargs="*", default=[], help="other markdown files to show under Notes")
    a = p.parse_args()

    missing = [f for f in [a.ranked, a.evidence, a.notes, *a.extra_notes] if not (ROOT / f).exists()]
    if missing:
        print("These files do not exist in the repo:", *missing, sep="\n  ", file=sys.stderr)
        return 1

    reg = json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {"counties": []}
    entry = {
        "slug": a.slug,
        "name": a.name,
        "version": a.version,
        "run_date": a.run_date,
        "ranked": a.ranked,
        "evidence": a.evidence,
        "notes": a.notes,
        "extra_notes": a.extra_notes,
    }
    counties = [c for c in reg["counties"] if c["slug"] != a.slug]
    counties.append(entry)
    reg["counties"] = counties
    REGISTRY.write_text(json.dumps(reg, indent=2) + "\n")
    print(f"Registered {a.name} ({a.slug}) -> {REGISTRY.relative_to(ROOT)}; {len(counties)} counties listed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
