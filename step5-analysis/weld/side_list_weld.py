#!/usr/bin/env python3
"""Weld County side list: the county Tax Incentive Agreements and the flagged assessor sales, matched to the v3 ranked rows.

Matthew's decision (2026-11-06): the v3 method and points table stay unchanged for Weld; the incentive agreements, the assessor sales
and the personal property accounts, which have no slot in the method, are published beside the ranked list, and ranked rows that
match one are marked. A match is confirmed only on an exact normalised name OR an exact normalised street address; anything looser
is "possible". Nothing here changes a score.

Usage: python3 side_list_weld.py <v3 output folder> <step4 folder>   (writes weld_county_incentives.csv, weld_flagged_sales.csv and
       weld_side_list_matches.csv next to this script)
"""
import csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GENERIC_LEAD = {"COLORADO", "AMERICAN", "NORTH", "SOUTH", "WELD", "GREELEY", "FRONT", "ROCKY", "UNITED", "NATIONAL", "GENERAL", "MOUNTAIN", "WESTERN", "HIGH", "GREAT", "NORTHERN", "TEXAS", "PREMIER", "ADVANCED", "GLOBAL", "FIRST"}
SUFFIX = re.compile(r"\b(INC|LLC|L L C|CORP|CORPORATION|CO|COMPANY|LTD|LP|LLLP|LLP|INCORPORATED|THE|OF|DBA|D B A|US|USA|HOLDINGS?)\b")


def nname(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", (s or "").upper())
    s = SUFFIX.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def naddr(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", (s or "").upper())
    s = re.sub(r"\b(COUNTY ROAD|CR|WCR|WELD COUNTY ROAD)\b", "CR", s)
    s = re.sub(r"\b(STREET|ST|AVENUE|AVE|DRIVE|DR|ROAD|RD|BOULEVARD|BLVD|PARKWAY|PKWY|PLACE|PL|COURT|CT|LANE|LN|HIGHWAY|HWY|CIRCLE|CIR|WAY)\b", "", s)
    s = re.sub(r"\b(NORTH|N|SOUTH|S|EAST|E|WEST|W)\b", "", s)
    s = re.sub(r"\b(SUITE|STE|UNIT|BLDG|BUILDING)\b.*$", "", s)
    m = re.match(r"\s*(\d+)\s+([A-Z0-9 ]+)", s)
    return (m.group(1) + " " + re.sub(r"\s+", " ", m.group(2)).strip()) if m else ""


def main():
    out, s4 = sys.argv[1], sys.argv[2]
    ranked = list(csv.DictReader(open(os.path.join(out, "weld_ranked_accounts_v3.csv"))))
    by_name, by_addr = {}, {}
    for r in ranked:
        names = [r["company_name"]] + [v.strip() for v in r.get("name_variants", "").split(";") if v.strip()]
        for n in names:
            k = nname(n)
            if k and len(k) > 3:
                by_name.setdefault(k, []).append(r)
        a = naddr(r["site_address"])
        if a:
            by_addr.setdefault(a, []).append(r)

    def match(name, addr):
        hits = []
        k = nname(name)
        for r in by_name.get(k, []):
            if not any(h[0] == r["rank"] for h in hits):
                hits.append((r["rank"], r["company_name"], "confirmed: exact name"))
        a = naddr(addr)
        for r in by_addr.get(a, []) if a else []:
            if not any(h[0] == r["rank"] for h in hits):
                hits.append((r["rank"], r["company_name"], "possible: exact street address only (occupier may differ)"))
        if not hits and k:
            lead = k.split()[0]
            for kk, rs in by_name.items():
                if kk.split()[0] == lead and len(lead) > 4 and lead not in GENERIC_LEAD:
                    for r in rs:
                        hits.append((r["rank"], r["company_name"], "possible: shares the lead word"))
        return hits

    matches = []
    # incentive agreements
    inc = list(csv.DictReader(open(os.path.join(s4, "weld", "scrape_weld_incentive_agreements.csv"))))
    rows = []
    for r in inc:
        if r["flag"] != "Y":
            continue
        hits = match(r["company_name"], r["site_address"])
        rows.append(dict(record_date=r["record_date"], company_name=r["company_name"], site_address=r["site_address"], city=r["city"],
                         description=r["description"], project_codename=r.get("project_codename", ""), phase_1_cap=r.get("phase_1_cap", ""),
                         rebate_pct=r.get("rebate_pct", ""), term_years=r.get("term_years", ""), source_url=r["source_url"],
                         ranked_match="; ".join("rank %s %s (%s)" % h for h in hits) or "not in the ranked list"))
        for h in hits:
            matches.append(dict(side_source="county incentive agreement", side_record=r["record_id"], side_name=r["company_name"], side_address=r["site_address"], rank=h[0], ranked_name=h[1], match_class=h[2]))
    rows.sort(key=lambda x: x["record_date"], reverse=True)
    with open(os.path.join(HERE, "weld_county_incentives.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    # flagged sales
    sales = [r for r in csv.DictReader(open(os.path.join(s4, "weld", "scrape_weld_county_property_sales.csv"))) if r["flag"] == "Y"]
    srows = []
    for r in sales:
        hits = match(r["company_name"], r["site_address"])
        srows.append(dict(record_date=r["record_date"], grantee=r["company_name"], grantor=r.get("grantor", ""), site_address=r["site_address"], city=r["city"], zip=r["zip"],
                          sale_price=r.get("sale_price", ""), occupancy=r.get("occupancy_description", ""), building_sf=r.get("building_sf", ""), acreage=r.get("acreage", ""),
                          industrial_use=r.get("industrial_use", ""), ranked_match="; ".join("rank %s %s (%s)" % h for h in hits) or ""))
        for h in hits:
            matches.append(dict(side_source="assessor sale 2M+", side_record=r["record_id"], side_name=r["company_name"], side_address=r["site_address"], rank=h[0], ranked_name=h[1], match_class=h[2]))
    srows.sort(key=lambda x: x["record_date"], reverse=True)
    with open(os.path.join(HERE, "weld_flagged_sales.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(srows[0].keys())); w.writeheader(); w.writerows(srows)
    with open(os.path.join(HERE, "weld_side_list_matches.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["side_source", "side_record", "side_name", "side_address", "rank", "ranked_name", "match_class"]); w.writeheader(); w.writerows(matches)
    print("incentives %d (%d matched a ranked row); flagged sales %d (%d matched); match rows %d" % (
        len(rows), sum(1 for x in rows if not x["ranked_match"].startswith("not")), len(srows), sum(1 for x in srows if x["ranked_match"]), len(matches)))
    for x in rows:
        print("  %s | %s | %s" % (x["record_date"], x["company_name"][:45], x["ranked_match"][:90]))


if __name__ == "__main__":
    main()
