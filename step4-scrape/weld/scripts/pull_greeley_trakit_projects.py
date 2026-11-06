#!/usr/bin/env python3
"""Pull the City of Greeley TRAKiT Projects layer (CentralSquare TRAKiT planning cases
mirrored to ArcGIS Enterprise, active cases only) into the step 4 shared format.

Usage:  python3 pull_greeley_trakit_projects.py [--since YYYY-MM-DD] [--fresh]

The layer is a live view of open cases with no history, so every run snapshots the whole
layer (172 rows on 2026-11-06, one request) and APPENDS rows not seen before to the CSV.
Rows already held keep their record_date, company_name, retrieved_at and first_seen_at;
only the status columns (status, approved_date, last_seen_at, in_layer_last_run) are
refreshed. Nothing is ever deleted: a case that leaves the layer keeps its row with
in_layer_last_run = N.

--since  keep only new rows whose APPLIED date is on or after this date (default
         2023-01-01, the QA floor; the layer's oldest case was applied 2023-03-01).
--fresh  ignore today's raw snapshot and refetch.
Raw pages are cached under ../raw/greeley_trakit_projects/snapshot_<UTC day>/.
"""
import argparse, os, shutil, sys
from collections import Counter
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_common as cc

LAYER = "https://gis.greeleygov.com/arcgis_svr/rest/services/Data_Services/TrakitProjects/MapServer/0"
SLUG = "greeley_trakit_projects"
SOURCE = "Greeley TRAKiT projects"
OUT = os.path.join(cc.WELD_DIR, "scrape_%s.csv" % SLUG)
CASE_LINK = "https://trakit.greeleygov.com/etrakit/Search/project.aspx?activityNo=%s"

# PLANNER and EMAIL are staff fields and are not requested (brief: leave personal data unretrieved).
FIELDS = ["ESRI_OID", "UID", "PROJECT_NO", "PROJECT_NAME", "PROJECTTYPE", "PROJECTSUBTYPE", "STATUS",
          "SITE_ADDRESS", "PARCEL_ID", "APPLIED", "SUBMITTED", "APPROVED", "LON", "LAT", "APPLICANT"]

EXTRA_COLS = ["industrial_use", "industrial_word", "industrial_adjacent", "industrial_adjacent_word",
              "record_subtype", "status", "parcel_number", "applicant", "project_name",
              "applied_date", "submitted_date", "approved_date", "latitude", "longitude",
              "case_link", "object_id", "uid", "first_seen_at", "last_seen_at", "in_layer_last_run",
              "parser_version"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2023-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    cache = os.path.join(cc.RAW_ROOT, SLUG, "snapshot_%s" % day)
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)

    cc.require_fields(LAYER, FIELDS)
    n_source = cc.source_count(LAYER, "1=1")
    feats = cc.fetch_all(LAYER, "1=1", FIELDS, cache, page_size=1000, order="ESRI_OID")
    if len(feats) != n_source:
        raise SystemExit("ROW COUNT MISMATCH: fetched %d, source says %d" % (len(feats), n_source))
    print("source count (whole layer): %d" % n_source)

    # Surnames of individual applicants in this snapshot, used to blank owner-named plats.
    individuals = []
    for f in feats:
        comp, dropped = cc.company_from_applicant(f["attributes"].get("APPLICANT"))
        if dropped and not comp:
            individuals.append(f["attributes"].get("APPLICANT"))
    surnames = cc.surname_tokens(individuals)

    existing, _ = cc.read_csv(OUT)
    by_id = {r["record_id"]: r for r in existing}
    cols = cc.COMMON_COLS + EXTRA_COLS
    new_rows, updated, out_of_window = [], 0, 0
    applicants_blanked = names_blanked = 0
    seen = set()
    for f in feats:
        at = f["attributes"]
        rid = cc.clean(at.get("PROJECT_NO"))
        if not rid:
            raise SystemExit("blank PROJECT_NO on ESRI_OID %s" % at.get("ESRI_OID"))
        if rid in seen:
            raise SystemExit("duplicate PROJECT_NO %s in the layer" % rid)
        seen.add(rid)
        fetched = f["_fetched_at"]
        status_cols = {"status": cc.clean(at.get("STATUS")), "approved_date": cc.ms_to_date(at.get("APPROVED")),
                       "last_seen_at": fetched, "in_layer_last_run": "Y"}
        if rid in by_id:
            by_id[rid].update(status_cols)
            updated += 1
            continue
        rdate = cc.ms_to_date(at.get("APPLIED"))
        if not rdate or rdate < a.since:
            out_of_window += 1
            continue
        rtype = cc.clean(at.get("PROJECTTYPE"))
        subtype = cc.clean(at.get("PROJECTSUBTYPE"))
        raw_name = cc.clean(at.get("PROJECT_NAME")).strip('"')
        applicant, dropped = cc.company_from_applicant(at.get("APPLICANT"))
        if dropped:
            applicants_blanked += 1
        name, why = cc.scrub_project_name(raw_name, surnames)
        if why:
            names_blanked += 1
        if applicant:
            company, role = applicant, "applicant"
        else:
            company = cc.company_from_project_name(name)
            role = "project" if company else "unknown"
        # industrial words are read from the raw name (before any blanking), the type and subtype
        ind, ind_word, adj, adj_word = cc.industrial_flags(" ".join([raw_name, rtype, subtype]))
        lon, lat = at.get("LON"), at.get("LAT")
        has_pt = isinstance(lon, (int, float)) and isinstance(lat, (int, float)) and -106 < lon < -104 and 39 < lat < 41
        desc = name
        if subtype and subtype.upper() not in desc.upper():
            desc = (desc + " [" + subtype.title() + "]").strip() if desc else subtype.title()
        row = {
            "source": SOURCE, "source_level": cc.SOURCE_LEVEL, "record_id": rid,
            "record_date": rdate, "date_type": "applied", "record_type": rtype,
            "company_name": company, "company_role": role,
            "site_address": cc.clean(at.get("SITE_ADDRESS")), "city": "Greeley", "county": cc.COUNTY, "zip": "",
            "description": cc.clean(desc, 500), "flag": "Y", "flag_rule": cc.FLAG_RULE,
            "source_url": cc.layer_query_url(LAYER, "PROJECT_NO='%s'" % rid), "retrieved_at": fetched,
            "industrial_use": ind, "industrial_word": ind_word,
            "industrial_adjacent": adj, "industrial_adjacent_word": adj_word,
            "record_subtype": subtype, "parcel_number": cc.clean(at.get("PARCEL_ID")),
            "applicant": applicant, "project_name": name,
            "applied_date": rdate, "submitted_date": cc.ms_to_date(at.get("SUBMITTED")),
            "latitude": "%.6f" % lat if has_pt else "", "longitude": "%.6f" % lon if has_pt else "",
            "case_link": CASE_LINK % rid, "object_id": str(at.get("ESRI_OID")), "uid": cc.clean(at.get("UID")),
            "first_seen_at": fetched, "parser_version": cc.PARSER_VERSION}
        row.update(status_cols)
        new_rows.append(row)
    for rid, r in by_id.items():
        if rid not in seen:
            r["in_layer_last_run"] = "N"
    rows = existing + new_rows
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    cc.write_csv(OUT, cols, rows)
    print("rows in CSV: %d (new this run %d, already held and refreshed %d, no longer in layer %d, before --since %d)"
          % (len(rows), len(new_rows), updated, sum(1 for r in by_id.values() if r["in_layer_last_run"] == "N"), out_of_window))
    print("applicant strings blanked as individuals: %d; project names blanked: %d" % (applicants_blanked, names_blanked))
    print("industrial_use Y: %d; industrial_adjacent Y: %d" % (sum(1 for r in rows if r["industrial_use"] == "Y"),
                                                              sum(1 for r in rows if r["industrial_adjacent"] == "Y")))
    print("flag rules:", Counter(r["flag_rule"] for r in rows if r["flag"] == "Y"))
    print("types:", Counter(r["record_type"] for r in rows).most_common())


if __name__ == "__main__":
    main()
