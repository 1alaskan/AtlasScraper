#!/usr/bin/env python3
"""Pull Denver concept and site development plan applications (ArcGIS REST).

Usage:  python3 pull_denver_site_plans.py [--since YYYY-MM-DD] [--fresh]

--since  FILE_OPEN_DATE cursor (default 2024-01-01).
--fresh  ignore today's raw cache and refetch.
Raw pages are cached under raw/siteplans_<since>_<UTC day>/.
"""
import argparse, os, shutil, sys, urllib.parse
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arcgis_common as ac

HERE = os.path.dirname(os.path.abspath(__file__))
LAYER = ac.HOST + "/SDPConceptDynamic/FeatureServer/0"
SOURCE = "Denver concept and site plans"
OUT = os.path.join(HERE, "scrape_denver_site_plans.csv")

# Staff contact fields PROJ_MGR, MGR_PHONE, MGR_EMAIL are deliberately not requested.
FIELDS = ["OBJECTID", "RECORD_ID", "APPLICATION_TYPE", "Record_Type", "FILE_OPEN_DATE",
          "APPL_STATUS", "APPL_STATUS_DATE", "PARENT_RECORD_ID", "ADDRESS", "CITY", "STATE",
          "ZIP_CODE", "ACTIVE_FLAG", "MATCHMETHOD", "MATCHSCORE", "NEIGHBORHOOD", "NOTES"]

EXTRA_COLS = ["status", "status_date", "record_type_group", "parent_record_id", "active_flag",
              "neighborhood", "zone_district", "zone_dist_type", "zone_description", "industrial_zoning",
              "latitude", "longitude", "match_method", "match_score", "parser_version"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    raw_root = os.path.join(HERE, "raw")
    cache = os.path.join(raw_root, "siteplans_%s_%s" % (a.since, day))
    ref_cache = os.path.join(raw_root, "reference_%s" % day)
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)
    where = "FILE_OPEN_DATE >= TIMESTAMP '%s 00:00:00'" % a.since

    ac.require_fields(LAYER, FIELDS)
    n_source = ac.source_count(LAYER, where)
    print("source count for filter:", n_source)
    feats = ac.fetch_all(LAYER, where, FIELDS, cache, page_size=1000)
    zoning = ac.load_zoning(ref_cache)

    rows = []
    for f in feats:
        at = f["attributes"]
        g = f.get("geometry") or {}
        x, y = g.get("x"), g.get("y")
        geocoded = ac.in_denver_bbox(x, y)
        zd = zt = zdesc = ""
        if geocoded:
            z = zoning.find(x, y)
            if z:
                zd, zt, zdesc = ac.clean(z.get("ZONE_DISTRICT")), ac.clean(z.get("ZONE_DIST_TYPE")), ac.clean(z.get("ZONE_DESCRIPTION"))
        rid = ac.clean(at.get("RECORD_ID"))
        url = LAYER + "/query?" + urllib.parse.urlencode(
            {"where": "RECORD_ID='%s'" % rid, "outFields": "*", "f": "html"})
        ms = at.get("MATCHSCORE")
        rows.append({
            "source": SOURCE, "source_level": "County (Denver)", "record_id": rid,
            "record_date": ac.ms_to_date(at.get("FILE_OPEN_DATE")), "date_type": "opened",
            "record_type": ac.clean(at.get("APPLICATION_TYPE")),
            "company_name": "", "company_role": "unknown",
            "site_address": ac.clean(at.get("ADDRESS")),
            "city": "Denver", "county": "Denver",  # layer carries Denver/DENVER/blank; the layer is Denver only
            "zip": ac.clean(at.get("ZIP_CODE"))[:5],
            "description": ac.clean(at.get("NOTES"), 500),
            "flag": "Y", "flag_rule": "all concept and site plan applications",
            "source_url": url, "retrieved_at": f["_fetched_at"],
            "status": ac.clean(at.get("APPL_STATUS")),
            "status_date": ac.ms_to_date(at.get("APPL_STATUS_DATE")),
            "record_type_group": ac.clean(at.get("Record_Type")),
            "parent_record_id": ac.clean(at.get("PARENT_RECORD_ID")),
            "active_flag": ac.clean(at.get("ACTIVE_FLAG")),
            "neighborhood": ac.clean(at.get("NEIGHBORHOOD")),
            "zone_district": zd, "zone_dist_type": zt, "zone_description": zdesc,
            "industrial_zoning": ("Y" if ac.is_industrial_zone(zd, zt) else "N") if zd else "",
            "latitude": "%.6f" % y if geocoded else "", "longitude": "%.6f" % x if geocoded else "",
            "match_method": ac.clean(at.get("MATCHMETHOD")),
            "match_score": "" if ms is None else "%g" % ms,
            "parser_version": ac.PARSER_VERSION})
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    ac.write_csv(OUT, ac.COMMON_COLS + EXTRA_COLS, rows)
    print("rows written: %d (source count %d)" % (len(rows), n_source))
    if len(rows) != n_source:
        raise SystemExit("ROW COUNT MISMATCH against source")


if __name__ == "__main__":
    main()
