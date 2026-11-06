#!/usr/bin/env python3
"""Pull Weld County recorded Site Plan Review cases (Site_Plan_Review_open_data polygon
layer) into the step 4 shared format.

Usage:  python3 pull_weld_county_site_plan_reviews.py [--since YYYY-MM-DD] [--fresh]

--since  DATE_ (plat recording date) cursor, default 2023-01-01; any other value writes to
         scrape_<slug>_since_<date>.csv so the full file is kept.
--fresh  ignore today's raw cache and refetch.

The layer carries the case number, recording date, zoning, parcel, acreage and reception
number but no name, address or description. Two joins fill those in:
  Ownership table (PARCELNB, 12 digit, zero padded)  owner name (companies only), the
      assessor BUSINESSNAME, situs address and city, and the personal property (P) accounts
      sitting on the parcel (tenant_accounts, companies only).
  Planning Cases view (CaseID = B1_ALT_ID)  the case description and title while the case
      is still active.
Raw pages are cached under raw/weld_county_site_plan_reviews/<since>_<UTC day>/.
"""
import argparse, os, re, shutil, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weld_agol_common as wc

LAYER = wc.SPR
SLUG = "weld_county_site_plan_reviews"
SOURCE = "Weld County site plan reviews"
OUT = os.path.join(wc.WELD_DIR, "scrape_%s.csv" % SLUG)

FIELDS = ["OBJECTID", "SPR_S", "SUBDIVISIO", "LOTS", "BLOCK", "S_T_R", "ZONING", "PARCEL__",
          "STATUS", "ACRES", "RECP_NUM", "DATE_", "CASE_NAME", "B1_ALT_ID", "PER_STATUS"]
PC_FIELDS = ["FID", "CaseID", "Title", "Category", "Description"]

EXTRA_COLS = ["industrial_use", "parcel_number", "zoning", "acreage", "case_number",
              "reception_number", "amendment", "business_name", "tenant_accounts", "owner_account",
              "owner_account_type", "subdivision", "lots", "section_township_range", "permit_status",
              "planning_status", "title", "latitude", "longitude", "parser_version"]


def pick_owner(rows):
    """From the Ownership rows on a parcel: the real-property account (R prefix), preferring
    an Industrial or Commercial account, then the P accounts on the parcel."""
    real = [o for o in rows if str(o.get("ACCOUNTNO") or "").upper().startswith("R")]
    rank = {"Industrial": 0, "Commercial": 1}
    real.sort(key=lambda o: (rank.get(o.get("ACCTTYPE"), 2), str(o.get("ACCOUNTNO"))))
    pers = [o for o in rows if str(o.get("ACCOUNTNO") or "").upper().startswith("P")]
    return (real[0] if real else (rows[0] if rows else None)), pers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2023-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    out = OUT if a.since == "2023-01-01" else OUT.replace(".csv", "_since_%s.csv" % a.since)
    day = wc.today().replace("-", "")
    cache = os.path.join(wc.RAW_ROOT, SLUG, "%s_%s" % (a.since, day))
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)

    where = "DATE_ >= DATE '%s'" % a.since
    wc.require_fields(LAYER, FIELDS)
    wc.require_fields(wc.OWNERSHIP, wc.OWNERSHIP_FIELDS)
    n_source = wc.source_count(LAYER, where)
    print("source count for filter:", n_source)
    feats = wc.fetch_all(LAYER, where, FIELDS, os.path.join(cache, "spr"), geometry=False,
                         extra={"returnCentroid": "true"})
    if len(feats) != n_source:
        raise SystemExit("ROW COUNT MISMATCH against source: %d fetched, %d expected" % (len(feats), n_source))

    parcels = [wc.pad_parcel(f["attributes"].get("PARCEL__")) for f in feats]
    owners = wc.fetch_by_keys(wc.OWNERSHIP, "PARCELNB", parcels, wc.OWNERSHIP_FIELDS,
                              os.path.join(cache, "ownership"))
    cases = wc.fetch_by_keys(wc.PLANNING_CASES, "CaseID",
                             [wc.clean(f["attributes"].get("B1_ALT_ID")) for f in feats], PC_FIELDS,
                             os.path.join(cache, "planning_cases"))

    rows, rules, blanked, no_parcel, no_owner = [], Counter(), 0, 0, 0
    for f in feats:
        at = f["attributes"]
        case = wc.clean(at.get("B1_ALT_ID")) or wc.clean(at.get("CASE_NAME"))
        rid = case or "OBJECTID-%s" % at.get("OBJECTID")
        parcel = wc.pad_parcel(at.get("PARCEL__"))
        if not parcel:
            no_parcel += 1
        owner, pers = pick_owner(owners.get(parcel, [])) if parcel else (None, [])
        if parcel and owner is None:
            no_owner += 1
        name, biz, addr, city, acct, accttype = "", "", "", "", "", ""
        if owner:
            name, b = wc.company_or_blank(owner.get("NAME"))
            blanked += b
            biz, b = wc.company_or_blank(owner.get("BUSINESSNAME"))
            blanked += b
            addr = wc.situs_address(owner)
            city = wc.weld_city(owner.get("LOCCITY"))
            acct = wc.clean(owner.get("ACCOUNTNO"))
            accttype = wc.clean(owner.get("ACCTTYPE"))
        tenants = []
        for p in pers:
            t, b = wc.company_or_blank(p.get("BUSINESSNAME") or p.get("NAME"))
            blanked += b
            if t and t not in tenants:
                tenants.append(t)
        if not name and biz:
            name = biz
        zoning = wc.clean(at.get("ZONING")).strip(", ")
        pc = (cases.get(case) or [None])[0]
        title = wc.clean(pc.get("Title")) if pc else ""
        pstatus = wc.clean(pc.get("Category")) if pc else ""
        pc_desc = wc.scrub_description(pc.get("Description"), limit=None) if pc else ""
        amend = "Y" if re.match(r"^\d*AM", case.upper()) else "N"
        parts = ["%s %s recorded %s" % ("Site plan review amendment" if amend == "Y" else "Site plan review",
                                        case, wc.ms_to_date(at.get("DATE_")))]
        if zoning:
            parts.append("zoning %s" % zoning)
        if at.get("ACRES"):
            parts.append("%s ac" % wc.num(at.get("ACRES"), "%.2f"))
        sub = wc.clean(at.get("SUBDIVISIO"))
        if sub and sub.upper() not in ("NA", "N/A"):
            parts.append("subdivision %s" % sub)
        if biz and biz != name:
            parts.append("assessor business name %s" % biz)
        if tenants:
            parts.append("personal property accounts on parcel: %s" % "; ".join(tenants))
        desc = "; ".join(parts) + (". " + pc_desc if pc_desc else "")
        text = " ".join([zoning, pc_desc, title, biz, " ".join(tenants)])
        ind = "Y" if (wc.industrial_zoning(zoning) or wc.INDUSTRIAL_WORDS.search(text)) else "N"
        rule = "all planning and development cases"
        rules[rule] += 1
        rows.append({
            "source": SOURCE, "source_level": wc.SOURCE_LEVEL, "record_id": rid,
            "record_date": wc.ms_to_date(at.get("DATE_")), "date_type": "recorded",
            "record_type": "site plan review",
            "company_name": name, "company_role": "owner" if name else "unknown",
            "site_address": addr, "city": city or wc.UNINC, "county": wc.COUNTY, "zip": "",
            "description": wc.clean(desc, 500), "flag": "Y", "flag_rule": rule,
            "source_url": wc.layer_query_url(LAYER, "B1_ALT_ID='%s'" % case),
            "retrieved_at": f["_fetched_at"],
            "industrial_use": ind, "parcel_number": parcel, "zoning": zoning,
            "acreage": wc.num(at.get("ACRES"), "%.3f"), "case_number": case,
            "reception_number": wc.clean(at.get("RECP_NUM")), "amendment": amend,
            "business_name": biz, "tenant_accounts": "; ".join(tenants), "owner_account": acct,
            "owner_account_type": accttype, "subdivision": sub, "lots": wc.clean(at.get("LOTS")),
            "section_township_range": wc.clean(at.get("S_T_R")),
            "permit_status": wc.clean(at.get("PER_STATUS")), "planning_status": pstatus, "title": title,
            "latitude": "%.6f" % f["centroid"]["y"] if f.get("centroid") else "",
            "longitude": "%.6f" % f["centroid"]["x"] if f.get("centroid") else "",
            "parser_version": wc.PARSER_VERSION})
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    wc.write_csv(out, wc.COMMON_COLS + EXTRA_COLS, rows)
    print("rows written: %d (source count %d)" % (len(rows), n_source))
    print("rows with parcel 0 (no join possible): %d; parcels with no Ownership row: %d" % (no_parcel, no_owner))
    print("owner or tenant names blanked as individuals:", blanked)
    print("company_name filled:", sum(1 for r in rows if r["company_name"]))
    print("flag rules:", rules.most_common())
    print("industrial_use:", Counter(r["industrial_use"] for r in rows))
    print("zoning:", Counter(r["zoning"] for r in rows).most_common())
    print("distinct record_id:", len({r["record_id"] for r in rows}))


if __name__ == "__main__":
    main()
