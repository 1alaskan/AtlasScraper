#!/usr/bin/env python3
"""Print the v3 results as Markdown fragments (cut table, top rows, ground truth, sensitivity, rank changes).

Usage: python3 report_v3.py <v3 output folder> [cuts|top N|gt|sens|moves|rows]
"""
import json, sys

ORDER = ["flagged rows statewide", "flagged rows (every", "flagged rows", "zero-valuation", "flagged rows in the DIA", "flagged rows with county", "flagged rows with a Denver mailing",
         "rows whose county", "flagged rows with AIRS", "flagged rows with city", "no Colorado address", "outside ", "Colorado address outside", "debtor name has no business word",
         "SBA continuation", "ADDED: pharmacy", "paving", "forklifts", "dry-cleaner", "'bottling'", "dropped after", "February 2026", "registered-agent", "entity since",
         "DIA neighborhood on airport", "special events", "assessor parcel class", "ADDED in v3: permit cancelled", "permit cancelled", "not industrially zoned", "no usable street",
         "industrial stormwater general-permit renewal", "renewals", "wastewater", "airport construction", "portable", "flagged on acreage", "transit",
         "fuel stations", "emergency generators", "hospitals", "no street address", "no single street", "rows from minutes", "no Denver County",
         "kept at the weak tier (8 points): restaurant", "kept at the weak tier (8 points): towable", "kept at the weak tier (8 points): flagged word", "rows kept", "of the kept rows"]
SRC = ["Colorado UCC filings, tier A", "Colorado UCC filings, tier B", "Colorado business registrations, tier A", "Colorado business registrations, tier B",
       "Denver commercial construction permits, tier A", "Denver commercial construction permits, tier B", "Denver concept and site plans", "State water permits (WQCD)",
       "APCD air permit status", "Mile High CRE", "OEDIT EDC approvals"]


def _src_index(name):
    # Denver's sources keep their fixed order; another county's labels (its county permit and planning layers) sort after them,
    # in the order they first appear. Added 2026-11-06 for the Weld run; Denver output unchanged.
    if name in SRC:
        return SRC.index(name)
    if name not in _EXTRA:
        _EXTRA.append(name)
    return len(SRC) + _EXTRA.index(name)


_EXTRA = []


def okey(row):
    for i, k in enumerate(ORDER):
        if row[1].startswith(k):
            return (_src_index(row[0]), i)
    return (_src_index(row[0]), len(ORDER))


def main():
    r = json.load(open(sys.argv[1] + "/v3_report.json"))
    what = sys.argv[2] if len(sys.argv) > 2 else "all"
    if what in ("cuts", "all"):
        print("| Source | Step | Rows |\n|---|---|---|")
        for s, step, n in sorted(r["cuts"], key=okey):
            print("| %s | %s | %s |" % (s, step, "{:,}".format(n)))
    if what in ("top", "all"):
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 25
        print("\n| Rank | Step 5 | Tier B run | Company or address | Site | Stage | Score | Tier |\n|---|---|---|---|---|---|---|---|")
        for t in r["top"][:n]:
            print("| %d | %s | %s | %s | %s | %s | %.1f | %s |" % (t["rank"], t["r5"] or "new", t["r5b"] or "new", t["name"], t["addr"], t["stage"], t["score"], t["tier"]))
    if what in ("gt", "all"):
        print()
        for p, h in r["ground_truth"].items():
            print(p, "->", "; ".join("rank %s (%s) %s, %s, score %s" % tuple(x) for x in h) if h else "not ranked")
    if what in ("sens", "all"):
        print()
        for k, v in r["sensitivity"].items():
            print("%s: %d of 25 change; top 10 the same set: %s\n   in: %s\n   out: %s" % (k, v["changed"], v["top10_same"], "; ".join(v["enter"]), "; ".join(v["leave"])))
    if what in ("rows", "all"):
        print()
        print(json.dumps(r["rows"], indent=1))
        print(json.dumps(r["resolve_counts"], indent=1))
        print(json.dumps(r["geocoder"], indent=1))
        print(json.dumps(r["moves_over_10"], indent=1))
    if what == "moves":
        big = sorted([m for m in r["moves"] if abs(m["delta"]) > 10], key=lambda m: m["rank"])
        for m in big:
            print("%d (was %d) | %s | %s | %.1f (was %.1f) | %s | %s" % (m["rank"], m["was"], m["name"][:50], m["addr"][:26], m["score"], m["score_was"], m["cause"], m["what"]))


if __name__ == "__main__":
    main()
