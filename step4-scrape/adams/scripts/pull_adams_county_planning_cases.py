#!/usr/bin/env python3
"""Pull Adams County Planning Cases (Accela Planning module mirrored to ArcGIS Online,
"Eye On Adams") into the step 4 shared format.

Usage:  python3 pull_adams_county_planning_cases.py [--since YYYY-MM-DD] [--fresh]

--since  DATE_OPENED cursor (default 2024-01-01; any other value writes to
         scrape_<slug>_since_<date>.csv so the full file is kept). The default run also carries in 2023
         cases whose RECORD_STATUS is still open. For an incremental run pass the last
         record_date already held and de-duplicate on (record_id, parcel_number) downstream.
--fresh  ignore today's raw cache and refetch.
Raw pages are cached under raw/adams_county_planning_cases/<since>_<UTC day>/.
"""
import argparse, os, re, shutil, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc_common as cc

LAYER = cc.ADAMS_HOST + "/Planning_Cases/FeatureServer/0"
SLUG = "adams_county_planning_cases"
SOURCE = "Adams County planning cases"
OUT = os.path.join(cc.ADAMS_DIR, "scrape_%s.csv" % SLUG)

FIELDS = ["OBJECTID", "RECORD_ID", "RECORD_NAME", "RECORD_STATUS", "DATE_STATUS", "RECORD_TYPE",
          "ADDR_FULL_LINE", "DATE_OPENED", "DESCRIPTION", "PARCEL_NBR", "x", "y", "LinkToAccela"]

EXTRA_COLS = ["industrial_use", "record_type_code", "status", "status_date", "parcel_number",
              "latitude", "longitude", "accela_url", "parser_version"]

# Statuses that mean a case is finished. Anything else on a 2023 case counts as still open.
CLOSED = re.compile(r"closed|cancel|denied|expired|withdrawn|^approved$|permit issued|^none$", re.I)


def record_type_code(rt):
    m = re.match(r"\s*([A-Z]{3})\b", rt or "")
    if m:
        return m.group(1)
    if (rt or "").lower().startswith("conceptual"):
        return "PRE"
    if (rt or "").lower().startswith("temporary"):
        return "TVM"
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    out = OUT if a.since == "2024-01-01" else OUT.replace(".csv", "_since_%s.csv" % a.since)
    day = cc.now_iso()[:10].replace("-", "")
    cache = os.path.join(cc.RAW_ROOT, SLUG, "%s_%s" % (a.since, day))
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)

    where = "DATE_OPENED >= DATE '%s'" % a.since
    if a.since <= "2024-01-01":
        # still-open 2023 cases ride along with the default pull
        closed_sql = ("RECORD_STATUS LIKE '%Closed%' OR RECORD_STATUS LIKE '%Cancel%' OR "
                      "RECORD_STATUS LIKE '%Denied%' OR RECORD_STATUS = 'Expired' OR "
                      "RECORD_STATUS = 'Withdrawn' OR RECORD_STATUS = 'Approved' OR "
                      "RECORD_STATUS = 'Permit Issued' OR RECORD_STATUS = 'None' OR RECORD_STATUS IS NULL")
        where = ("(%s) OR (DATE_OPENED >= DATE '2023-01-01' AND DATE_OPENED < DATE '%s' AND NOT (%s))"
                 % (where, a.since, closed_sql))

    cc.require_fields(LAYER, FIELDS)
    n_source = cc.source_count(LAYER, where)
    print("source count for filter:", n_source)
    feats = cc.fetch_all(LAYER, where, FIELDS, cache, page_size=2000, geometry=False)

    rows, individuals = [], 0
    for f in feats:
        at = f["attributes"]
        rid = cc.clean(at.get("RECORD_ID"))
        name = cc.clean(at.get("RECORD_NAME"))
        desc = cc.clean(at.get("DESCRIPTION"))
        rtype = cc.clean(at.get("RECORD_TYPE"))
        if name and cc.looks_like_individual_project(name):
            if desc.upper().startswith(name.upper()[:20]) or cc.looks_like_individual_project(desc):
                desc = ""
            name = ""
            individuals += 1
        elif desc and cc.looks_like_individual_project(desc):
            desc = ""
        text = " ".join([name, desc, rtype])
        ind = "Y" if cc.INDUSTRIAL_WORDS.search(text) else "N"
        x, y = at.get("x"), at.get("y")
        rows.append({
            "source": SOURCE, "source_level": cc.SOURCE_LEVEL, "record_id": rid,
            "record_date": cc.ms_to_date(at.get("DATE_OPENED")), "date_type": "opened",
            "record_type": rtype,
            "company_name": name, "company_role": "project" if name else "unknown",
            "site_address": cc.clean(at.get("ADDR_FULL_LINE")).rstrip("- ").strip(),
            "city": "Unincorporated Adams County", "county": cc.COUNTY, "zip": "",
            "description": cc.clean(desc, 500),
            "flag": "Y", "flag_rule": "all planning and development cases",
            "source_url": cc.layer_query_url(LAYER, "RECORD_ID='%s'" % rid),
            "retrieved_at": f["_fetched_at"],
            "industrial_use": ind, "record_type_code": record_type_code(rtype),
            "status": cc.clean(at.get("RECORD_STATUS")), "status_date": cc.ms_to_date(at.get("DATE_STATUS")),
            "parcel_number": cc.clean(at.get("PARCEL_NBR")),
            "latitude": "%.6f" % y if y else "", "longitude": "%.6f" % x if x else "",
            "accela_url": cc.clean(at.get("LinkToAccela")), "parser_version": cc.PARSER_VERSION})
    for r in rows:
        if r["site_address"] in ("0", "0 -", "-"):
            r["site_address"] = ""
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    cc.write_csv(out, cc.COMMON_COLS + EXTRA_COLS, rows)
    print("rows written: %d (source count %d)" % (len(rows), n_source))
    print("record names blanked as probable individuals:", individuals)
    print("distinct cases:", len({r["record_id"] for r in rows}))
    print("industrial_use:", Counter(r["industrial_use"] for r in rows))
    print("types:", Counter(r["record_type_code"] for r in rows).most_common())
    if len(rows) != n_source:
        raise SystemExit("ROW COUNT MISMATCH against source")


if __name__ == "__main__":
    main()
