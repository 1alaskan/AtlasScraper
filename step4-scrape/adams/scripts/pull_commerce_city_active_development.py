#!/usr/bin/env python3
"""Snapshot the Commerce City "Active Development" layers (eTRAKiT projects and permits mirrored
nightly to ArcGIS Enterprise; only active records are kept, so the layers have no history) into
a dated snapshot log that only ever grows, then write the step 4 CSV from the log.

Usage:  python3 pull_commerce_city_active_development.py [--since YYYY-MM-DD] [--fresh]

--since  not a server filter here (the layers are a snapshot and every row is kept); it only
         limits which log rows reach the CSV by APPLIED_DT. Default 2000-01-01 (everything).
--fresh  ignore today's raw cache and refetch.

Each run: fetch both layers in full (a few hundred rows), cache the raw pages under
raw/commerce_city_active_development/<UTC day>/, then merge into
step4-scrape/adams/snapshot_commerce_city_active_development.csv keyed on
(layer, PROJECT_NO, PIN, SITE_ADDR). Rows seen for the first time are appended with first_seen;
rows seen again have last_seen and their status fields updated; rows no longer in the layer are
never deleted and get dropped_from_layer set to the first run that missed them. Run it weekly.
The step 4 CSV scrape_commerce_city_active_development.csv is rewritten from the whole log.
"""
import argparse, csv, os, re, shutil, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc_common as cc

LAYERS = {
    "under_review": cc.C3_HOST + "/CS_Active_Development_UnderReview/MapServer/0",
    "under_construction": cc.C3_HOST + "/CS_Active_Development_UnderConst/MapServer/0",
}
SLUG = "commerce_city_active_development"
SOURCE = "Commerce City active development"
OUT = os.path.join(cc.ADAMS_DIR, "scrape_%s.csv" % SLUG)
LOG = os.path.join(cc.ADAMS_DIR, "snapshot_%s.csv" % SLUG)

# PLANNER (a staff member's name), created_user, last_edited_user and IMG_URL are not requested.
FIELDS = ["OBJECTID", "PIN", "PROJECT_NO", "PROJECTTYP", "PROJECT_SU", "SITE_ADDR", "DELIVERY_A", "STATUS",
          "APPROVED_D", "CLOSED_DT", "APPLIED_DT", "STATUS_DT", "CREATE_DT", "URL", "ADCO_URL_R", "DETAILS",
          "CITY", "ZIP_CODE", "DESCRIPTIO", "FILTER", "SUBD_NAME", "IS_PERMIT"]

KEY = ["layer", "project_no", "pin", "site_address"]
LOG_COLS = KEY + ["first_seen", "last_seen", "dropped_from_layer", "project_type", "project_subtype",
                  "is_permit", "filter_group", "status", "applied_date", "status_date", "approved_date",
                  "closed_date", "layer_create_date", "project_name", "details", "delivery_address",
                  "city", "zip", "subdivision", "etrakit_url", "county_parcel_url", "latitude", "longitude",
                  "layer_row_count", "retrieved_at"]

EXTRA_COLS = ["industrial_use", "residential", "layer", "project_type", "project_subtype", "is_permit",
              "filter_group", "status", "status_date", "approved_date", "closed_date", "first_seen",
              "last_seen", "dropped_from_layer", "layer_row_count", "details", "subdivision", "parcel_number", "etrakit_url",
              "county_parcel_url", "latitude", "longitude", "parser_version"]


def read_log():
    if not os.path.exists(LOG):
        return {}, []
    with open(LOG, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {tuple(r[k] for k in KEY): r for r in rows}, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2000-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    day = cc.now_iso()[:10]
    cache = os.path.join(cc.RAW_ROOT, SLUG, day.replace("-", ""))
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)

    seen_now, counts = {}, {}
    for layer, url in LAYERS.items():
        cc.require_fields(url, FIELDS)
        n = cc.source_count(url, "1=1")
        feats = cc.fetch_all(url, "1=1", FIELDS, os.path.join(cache, layer), page_size=1000, geometry=True)
        if len(feats) != n:
            raise SystemExit("%s: got %d rows, source says %d" % (layer, len(feats), n))
        counts[layer] = n
        for f in feats:
            at = f["attributes"]
            g = f.get("geometry") or {}
            key = (layer, cc.clean(at.get("PROJECT_NO")), cc.clean(at.get("PIN")), cc.clean(at.get("SITE_ADDR")))
            row = {
                "layer": layer, "project_no": key[1], "pin": key[2], "site_address": key[3],
                "project_type": cc.clean(at.get("PROJECTTYP")), "project_subtype": cc.clean(at.get("PROJECT_SU")),
                "is_permit": cc.clean(at.get("IS_PERMIT")), "filter_group": cc.clean(at.get("FILTER")),
                "status": cc.clean(at.get("STATUS")), "applied_date": cc.ms_to_date(at.get("APPLIED_DT")),
                "status_date": cc.ms_to_date(at.get("STATUS_DT")), "approved_date": cc.ms_to_date(at.get("APPROVED_D")),
                "closed_date": cc.ms_to_date(at.get("CLOSED_DT")), "layer_create_date": cc.ms_to_date(at.get("CREATE_DT")),
                "project_name": "" if cc.clean(at.get("DESCRIPTIO")).upper() in ("NA", "N/A", "") else cc.clean(at.get("DESCRIPTIO")),
                "details": cc.clean(at.get("DETAILS")), "delivery_address": cc.clean(at.get("DELIVERY_A")),
                "city": cc.clean(at.get("CITY")).title() or "Commerce City", "zip": cc.clean(at.get("ZIP_CODE"))[:5],
                "subdivision": cc.clean(at.get("SUBD_NAME")), "etrakit_url": cc.clean(at.get("URL")),
                "county_parcel_url": cc.clean(at.get("ADCO_URL_R")),
                "latitude": "%.6f" % g["y"] if g.get("y") is not None else "",
                "longitude": "%.6f" % g["x"] if g.get("x") is not None else "",
                "retrieved_at": f["_fetched_at"]}
            if key in seen_now:   # identical features except OBJECTID (multi-parcel plats): count them
                seen_now[key]["layer_row_count"] = str(int(seen_now[key]["layer_row_count"]) + 1)
                continue
            row["layer_row_count"] = "1"
            seen_now[key] = row

    log, log_rows = read_log()
    new, updated, dropped = 0, 0, 0
    for key, row in seen_now.items():
        if key in log:
            old = log[key]
            old.update({k: v for k, v in row.items() if k not in ("first_seen",)})
            old["last_seen"] = day
            old["dropped_from_layer"] = ""
            updated += 1
        else:
            row["first_seen"] = day
            row["last_seen"] = day
            row["dropped_from_layer"] = ""
            log[key] = row
            log_rows.append(row)
            new += 1
    for key, old in log.items():
        if key not in seen_now and not old.get("dropped_from_layer"):
            old["dropped_from_layer"] = day
            dropped += 1
    log_rows.sort(key=lambda r: (r["first_seen"], r["layer"], r["project_no"], r["pin"]))
    cc.write_csv(LOG, LOG_COLS, log_rows)
    print("layer counts:", counts, "| log: %d rows, %d new, %d updated, %d newly dropped" % (len(log_rows), new, updated, dropped))

    rows, rules = [], Counter()
    for r in log_rows:
        if r["applied_date"] and r["applied_date"] < a.since:
            continue
        name = r["project_name"]
        if name and cc.looks_like_individual_project(name):
            name = ""
        text = " ".join([r["project_type"], r["project_subtype"], name, r["details"]])
        ind = "Y" if cc.INDUSTRIAL_WORDS.search(text) else "N"
        res = "Y" if r["filter_group"].lower() == "residential" or r["project_type"].upper().startswith("RESIDENTIAL") else "N"
        rid = "%s/%s" % (r["project_no"], r["pin"]) if r["pin"] else r["project_no"]
        rule = "all planning and development cases"
        rules[rule] += 1
        rows.append({
            "source": SOURCE, "source_level": cc.SOURCE_LEVEL, "record_id": rid,
            "record_date": r["applied_date"] or r["first_seen"], "date_type": "applied" if r["applied_date"] else "first seen in layer",
            "record_type": r["project_type"] + (" / " + r["project_subtype"] if r["project_subtype"] else ""),
            "company_name": name, "company_role": "project" if name else "unknown",
            "site_address": r["site_address"] or r["delivery_address"], "city": r["city"], "county": cc.COUNTY,
            "zip": r["zip"],
            "description": cc.clean("; ".join(p for p in (r["project_name"] if name else "", r["details"],
                                                           "status " + r["status"] if r["status"] else "") if p), 500),
            "flag": "Y", "flag_rule": rule,
            "source_url": r["etrakit_url"] or cc.layer_query_url(LAYERS[r["layer"]], "PROJECT_NO='%s'" % r["project_no"]),
            "retrieved_at": r["retrieved_at"],
            "industrial_use": ind, "residential": res, "layer": r["layer"], "project_type": r["project_type"],
            "project_subtype": r["project_subtype"], "is_permit": r["is_permit"], "filter_group": r["filter_group"],
            "status": r["status"], "status_date": r["status_date"], "approved_date": r["approved_date"],
            "closed_date": r["closed_date"], "first_seen": r["first_seen"], "last_seen": r["last_seen"],
            "dropped_from_layer": r["dropped_from_layer"], "layer_row_count": r["layer_row_count"], "details": r["details"], "subdivision": r["subdivision"],
            "parcel_number": ("0" + r["pin"]) if re.fullmatch(r"\d{12}", r["pin"] or "") else r["pin"],
            "etrakit_url": r["etrakit_url"], "county_parcel_url": r["county_parcel_url"],
            "latitude": r["latitude"], "longitude": r["longitude"], "parser_version": cc.PARSER_VERSION})
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    cc.write_csv(OUT, cc.COMMON_COLS + EXTRA_COLS, rows)
    print("rows written: %d (layers now hold %d features, %d distinct keys)" % (
        len(rows), sum(counts.values()), len(seen_now)))
    print("industrial_use:", Counter(r["industrial_use"] for r in rows), "residential:", Counter(r["residential"] for r in rows))
    print("types:", Counter(r["project_type"] for r in rows).most_common())


if __name__ == "__main__":
    main()
