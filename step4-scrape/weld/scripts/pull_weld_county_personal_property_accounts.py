#!/usr/bin/env python3
"""Snapshot the Weld County Assessor Ownership table's personal property (business
equipment) accounts, ACCTTYPE = Personal, into the step 4 shared format.

Usage:  python3 pull_weld_county_personal_property_accounts.py [--since YYYY-MM-DD] [--fresh]

This is a resolver snapshot, not a signal: every row is flag N. The table carries no
account creation date, so each account is dated by the day this script first saw it
(record_date = first_seen, date_type = snapshot). The script keeps
snapshot_weld_county_personal_property_accounts.csv (record_id, first_seen, last_seen,
business_name) and APPENDS accounts never seen before; an account that leaves the table is
kept in the output with active = N. Nothing is ever deleted. From now on a new P account
number is a dated "equipment declared at this site" event.

Only accounts whose BUSINESSNAME or owner NAME reads as a company are written; rows with no
company string at all (sole proprietors declared under a personal name) are left out and
counted. Mailing address fields (ADDRESS1, ADDRESS2) are never requested; only the mailing
city is kept.

--since  only affects the output file name for an incremental run (rows with first_seen on
         or after the date are also written to scrape_<slug>_since_<date>.csv).
--fresh  ignore today's raw cache and refetch (the snapshot file is still honoured).
Raw pages are cached under raw/weld_county_personal_property_accounts/<UTC day>/.
"""
import argparse, os, shutil, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weld_agol_common as wc

LAYER = wc.OWNERSHIP
SLUG = "weld_county_personal_property_accounts"
SOURCE = "Weld County assessor personal property accounts"
OUT = os.path.join(wc.WELD_DIR, "scrape_%s.csv" % SLUG)
SNAP = os.path.join(wc.WELD_DIR, "snapshot_%s.csv" % SLUG)

FIELDS = ["OBJECTID", "ACCOUNTNO", "NAME", "CITY", "STATE", "PARCELNB", "ACCTTYPE", "BUSINESSNAME",
          "STREETNO", "STREETNAME", "STREETALP", "STREETDIR", "STREETSUF", "LOCCITY", "SUBNAME"]

EXTRA_COLS = ["account_number", "parcel_number", "situs_city", "mailing_city", "mailing_state",
              "owner_name", "business_name", "subdivision", "first_seen", "last_seen", "active",
              "parser_version"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    day = wc.today()
    cache = os.path.join(wc.RAW_ROOT, SLUG, day.replace("-", ""))
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)

    where = "ACCTTYPE = 'Personal'"
    wc.require_fields(LAYER, FIELDS)
    n_source = wc.source_count(LAYER, where)
    print("source count for filter:", n_source)
    feats = wc.fetch_all(LAYER, where, FIELDS, cache, geometry=False)
    if len(feats) != n_source:
        raise SystemExit("ROW COUNT MISMATCH against source: %d fetched, %d expected" % (len(feats), n_source))

    snap = wc.load_snapshot(SNAP)
    prev = {r["record_id"]: r for r in wc.read_csv(OUT)}
    rows, seen, no_company, blanked = {}, set(), 0, 0
    for f in feats:
        at = f["attributes"]
        acct = wc.clean(at.get("ACCOUNTNO"))
        rid = acct or "OBJECTID-%s" % at.get("OBJECTID")
        biz, b1 = wc.company_or_blank(at.get("BUSINESSNAME"))
        owner, b2 = wc.company_or_blank(at.get("NAME"))
        blanked += b1 + b2
        name = biz or owner
        if not name:
            no_company += 1
            continue
        seen.add(rid)
        s = wc.update_snapshot(snap, rid, day, business_name=name)
        addr = wc.situs_address(at)
        situs_city = wc.weld_city(at.get("LOCCITY"))
        parts = ["personal property account %s" % acct]
        if owner and owner != name:
            parts.append("owner %s" % owner)
        if addr:
            parts.append("at %s, %s" % (addr, situs_city))
        else:
            parts.append("situs %s" % situs_city)
        if at.get("PARCELNB"):
            parts.append("parcel %s" % wc.clean(at.get("PARCELNB")))
        rows[rid] = {
            "source": SOURCE, "source_level": wc.SOURCE_LEVEL, "record_id": rid,
            "record_date": s["first_seen"], "date_type": "snapshot",
            "record_type": "personal property account",
            "company_name": name, "company_role": "owner",
            "site_address": addr, "city": situs_city, "county": wc.COUNTY, "zip": "",
            "description": wc.clean("; ".join(parts), 500), "flag": "N", "flag_rule": "",
            "source_url": wc.layer_query_url(LAYER, "ACCOUNTNO='%s'" % acct),
            "retrieved_at": f["_fetched_at"],
            "account_number": acct, "parcel_number": wc.clean(at.get("PARCELNB")),
            "situs_city": situs_city, "mailing_city": wc.clean(at.get("CITY")).title(),
            "mailing_state": wc.clean(at.get("STATE")), "owner_name": owner, "business_name": biz,
            "subdivision": wc.clean(at.get("SUBNAME")),
            "first_seen": s["first_seen"], "last_seen": s["last_seen"], "active": "Y",
            "parser_version": wc.PARSER_VERSION}
    dropped = 0
    for rid, r in prev.items():
        if rid not in rows:
            r = dict(r)
            r["active"] = "N"
            rows[rid] = r
            dropped += 1
    out_rows = sorted(rows.values(), key=lambda r: (r["record_date"], r["record_id"]))
    wc.write_csv(OUT, wc.COMMON_COLS + EXTRA_COLS, out_rows)
    wc.write_snapshot(SNAP, snap, ["business_name"])
    if a.since:
        inc = [r for r in out_rows if r["first_seen"] >= a.since]
        wc.write_csv(OUT.replace(".csv", "_since_%s.csv" % a.since), wc.COMMON_COLS + EXTRA_COLS, inc)
        print("incremental rows (first_seen >= %s): %d" % (a.since, len(inc)))
    print("rows written: %d (active today %d of %d source rows, kept from earlier runs %d)"
          % (len(out_rows), len(seen), n_source, dropped))
    print("rows left out with no company string (individual or blank names):", no_company)
    print("name fields blanked as individuals:", blanked)
    print("flag:", Counter(r["flag"] for r in out_rows))
    print("situs city:", Counter(r["situs_city"] for r in out_rows).most_common(10))
    print("null site_address:", sum(1 for r in out_rows if not r["site_address"]))


if __name__ == "__main__":
    main()
