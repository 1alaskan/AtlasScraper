#!/usr/bin/env python3
"""Step 5 v3 self-check: recompute every score from the evidence file and compare it with the ranked file.

Usage: python3 verify_v3.py <v3 output folder>

For each ranked row it rebuilds, from denver_evidence_v3.csv alone: the best points per source, the repeat-month
points, the independent-source bonus and the recency points. Stage and fit points are read from the row's own
"Points:" text (they are rule outcomes, not sums). It also checks the ground rules that can be tested by machine:
no em dashes, no email addresses or phone numbers in the evidence text, no Accela in a next step, every ranked row has
evidence, ranks are consecutive.
"""
import csv, re, sys
from collections import defaultdict

from v3_lib import *

csv.field_size_limit(10 ** 9)


def main():
    out = sys.argv[1]
    rk = list(csv.DictReader(open(out + "/denver_ranked_accounts_v3.csv", newline="", encoding="utf-8")))
    ev = list(csv.DictReader(open(out + "/denver_evidence_v3.csv", newline="", encoding="utf-8")))
    by = defaultdict(list)
    for e in ev:
        by[e["rank"]].append(e)
    pat = re.compile(r"Points: signal ([\d.]+) \((.*?)\); sources ([\d.]+); recency ([\d.]+); stage ([\d.]+); fit (-?[\d.]+)\s*$")
    bad = []
    for i, x in enumerate(rk, 1):
        if int(x["rank"]) != i:
            bad.append((x["rank"], "rank not consecutive"))
        rows = by.get(x["rank"], [])
        if not rows:
            bad.append((x["rank"], "no evidence rows"))
            continue
        m = pat.search(x["top_evidence"])
        if not m:
            bad.append((x["rank"], "points text not readable"))
            continue
        per, months = {}, defaultdict(set)
        for e in rows:
            p = float(e["points"])
            per[e["source"]] = max(per.get(e["source"], 0.0), p)
            if p >= REPEAT_MIN and e["record_date"]:
                months[e["source"]].add(e["record_date"][:7])
        signal = sum(per.values()) + sum(min(REPEAT_MAX, REPEAT_PTS * (len(v) - 1)) for v in months.values() if len(v) > 1)
        vals = [v for v in per.values() if v > 0]
        sig_n = sum(1 for v in vals if v >= SRC_SIGNAL_MIN)
        sup_n = sum(1 for v in vals if v < SRC_SIGNAL_MIN)
        bonus = (min(SRC_BONUS_MAX, SRC_BONUS * (sig_n - 1)) + min(SUP_BONUS_MAX, SUP_BONUS * sup_n)) if sig_n else min(SUP_BONUS_MAX, SUP_BONUS * max(0, sup_n - 1))
        dated = [e["record_date"] for e in rows if float(e["points"]) >= REC_MIN and e["record_date"]]
        latest = max(dated) if dated else ""
        rec = (REC_12 if latest >= D12 else REC_24 if latest >= D24 else 0) if latest else 0
        total = signal + bonus + rec + float(m.group(5)) + float(m.group(6))
        for label, got, want in (("signal", signal, float(m.group(1))), ("sources", bonus, float(m.group(3))), ("recency", rec, float(m.group(4))), ("score", total, float(x["score"]))):
            if abs(got - want) > 0.051:
                bad.append((x["rank"], "%s: evidence gives %s, ranked file says %s" % (label, g(got), g(want))))
        if float(m.group(5)) not in (0, 4, 8, 12) or float(m.group(6)) not in (-15, 0, 6, 15):
            bad.append((x["rank"], "stage or fit points outside the table"))
    text = open(out + "/denver_ranked_accounts_v3.csv", encoding="utf-8").read() + open(out + "/denver_evidence_v3.csv", encoding="utf-8").read()
    if chr(8212) in text:
        bad.append(("-", "em dash in an output file"))
    for e in ev:
        if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b", e["description"] + e["company_name"]):
            bad.append((e["rank"], "email address or phone number in the evidence file"))
    for x in rk:
        if re.search(r"accela", x["next_step"], re.I):
            bad.append((x["rank"], "next step mentions Accela"))
    scores = [float(x["score"]) for x in rk]
    print("ranked rows %d, evidence rows %d" % (len(rk), len(ev)))
    print("problems: %d" % len(bad))
    for b in bad[:40]:
        print("  rank %s: %s" % b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
