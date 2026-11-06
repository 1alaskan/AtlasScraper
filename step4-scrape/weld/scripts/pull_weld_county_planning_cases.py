#!/usr/bin/env python3
"""Snapshot the Weld County Planning Cases for Development Activity Map view (the active
USR, SPR, ZPAG, COZ and SIF cases mirrored from Accela to ArcGIS Online) into the step 4
shared format.

Usage:  python3 pull_weld_county_planning_cases.py [--since YYYY-MM-DD] [--fresh]

The layer carries no dates and no address, so every case is dated by the day this script
first saw it (record_date = first_seen, date_type = snapshot). The script keeps
snapshot_weld_county_planning_cases.csv (record_id, first_seen, last_seen, status, title)
and APPENDS cases never seen before; a case that drops out of the active view is kept in
the output with active = N and its last_seen day. Nothing is ever deleted.

--since  only affects the output file name for an incremental run (rows with first_seen
         on or after the date are also written to scrape_<slug>_since_<date>.csv).
--fresh  ignore today's raw cache and refetch (the snapshot file is still honoured).

Planner, PlannerEmail, Document and AlternativeText fields are never requested; the
Description field is scrubbed of planner names, e-mails and phones anyway.
Raw pages are cached under raw/weld_county_planning_cases/<UTC day>/.
"""
import argparse, os, re, shutil, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weld_agol_common as wc

LAYER = wc.PLANNING_CASES
SLUG = "weld_county_planning_cases"
SOURCE = "Weld County planning cases"
OUT = os.path.join(wc.WELD_DIR, "scrape_%s.csv" % SLUG)
SNAP = os.path.join(wc.WELD_DIR, "snapshot_%s.csv" % SLUG)

FIELDS = ["FID", "Item", "Show", "Type", "CaseID", "Title", "Category", "Latitude", "Longitude",
          "Description", "Epermit"]
SPR_FIELDS = ["OBJECTID", "B1_ALT_ID", "PARCEL__", "ZONING", "ACRES", "RECP_NUM", "DATE_"]

EXTRA_COLS = ["industrial_use", "parcel_number", "zoning", "status", "case_link", "latitude",
              "longitude", "title", "case_type_code", "first_seen", "last_seen", "active",
              "spr_recorded_date", "parser_version"]

# Words a title can be made of without naming anyone: a title with nothing else left is a
# use description ('Contractor Shop'), not a company or project name.
GENERIC = re.compile(
    r"\b(solar|energy|facility|facilities|project|mining|mine|sand|gravel|topsoil|kennel|dog|"
    r"contractor|contractor's|contractors|shop|office|offices|outdoor|indoor|storage|vehicle|"
    r"vehicles|rental|sales|repair|establishment|warehouse|construction|equipment|truck|trucks|"
    r"semi-trucks|semi|parking|trucking|transportation|transporation|company|business|"
    r"landscaping|event|events|center|centre|brewery|coffee|roaster|hemp|processing|"
    r"telecommunication|telecommunications|tower|oil|gas|support|service|services|operation|"
    r"operations|water|tank|tanks|treatment|plant|data|junkyard|commercial|commercia|salvage|"
    r"yard|lumberyard|woodworking|natural|compressor|station|battery|bess|rv|boat|car|"
    r"dealership|dealersehip|convenience|store|agritourism|winery|vineyard|class|v|injection|"
    r"well|ag|agricultural|to|and|or|of|in|the|for|a|an|zone|district|heating|cooling|"
    r"electrical|amend|amendment|adjust|boundary|lot|upgrades|existing|substation|"
    r"distribution|seed|units|expand|wind|golf|course|heavy|medium|light|industrial|"
    r"i-1|i-2|i-3|c-3|res|usr|spr|zpag|coz|sif|and/or|&)\b", re.I)
ENTITY = re.compile(r"\b(llc|l\.l\.c\.?|inc\.?|corp\.?|corporation|co\.?|company|ltd\.?|lp|llp|"
                    r"partners|partnership|holdings|enterprises|industries|equities|group)\b", re.I)


def classify_title(title):
    """Return (kind, company_name, role): kind is 'generic' for a plain use description
    ('Contractor Shop'), 'individual' when the leftover reads as a person's name, or
    'company' when the title names a company or project."""
    t = wc.clean(title)
    if not t:
        return "generic", "", ""
    rest = re.sub(r"\S*\d\S*", " ", t)           # case ids and numbers
    rest = re.sub(r"'s\b", "", rest)              # possessives: contractor's
    rest = GENERIC.sub(" ", rest)
    rest = re.sub(r"[^A-Za-z' \-]", " ", rest)
    if not [w for w in rest.split() if re.search(r"[A-Za-z]", w)]:
        return "generic", "", ""                  # pure use description
    if wc.looks_like_individual_project(t):
        return "individual", "", ""
    return "company", t, ("applicant" if ENTITY.search(t) else "project")


def case_type_code(t, case_id):
    t = wc.clean(t).upper()
    if t:
        return t
    m = re.search(r"([A-Z]{3,4})\d\d-", case_id or "")
    return m.group(1) if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    day = wc.today()
    cache = os.path.join(wc.RAW_ROOT, SLUG, day.replace("-", ""))
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)

    wc.require_fields(LAYER, FIELDS)
    n_source = wc.source_count(LAYER, "1=1")
    print("source count (all active cases):", n_source)
    feats = wc.fetch_all(LAYER, "1=1", FIELDS, cache, order="FID", geometry=False)
    if len(feats) != n_source:
        raise SystemExit("ROW COUNT MISMATCH against source: %d fetched, %d expected" % (len(feats), n_source))

    # Parcel, zoning and recording date for SPR cases, from the recorded SPR layer (case number key).
    ids = [wc.clean(f["attributes"].get("CaseID")) for f in feats]
    spr = wc.fetch_by_keys(wc.SPR, "B1_ALT_ID", [i for i in ids if "SPR" in i.upper()], SPR_FIELDS,
                           os.path.join(cache, "spr_join"))

    snap = wc.load_snapshot(SNAP)
    prev = {r["record_id"]: r for r in wc.read_csv(OUT)}
    rows, seen, individuals, rules = {}, set(), 0, Counter()
    for f in feats:
        at = f["attributes"]
        rid = wc.clean(at.get("CaseID"))
        if not rid:
            rid = "FID-%s" % at.get("FID")
        seen.add(rid)
        title = wc.clean(at.get("Title"))
        full_desc = wc.scrub_description(at.get("Description"), limit=None)
        desc = full_desc[:500]
        status = wc.clean(at.get("Category"))
        kind, name, role = classify_title(title)
        if kind == "individual":
            individuals += 1
            title = ""
        s = wc.update_snapshot(snap, rid, day, status=status, title=title)
        zoning = wc.zoning_from_text(full_desc + " " + title)
        j = (spr.get(rid) or [None])[0]
        parcel = wc.pad_parcel(j.get("PARCEL__")) if j else ""
        if j and not zoning:
            zoning = wc.clean(j.get("ZONING"))
        text = " ".join([title, full_desc, zoning])
        ind = "Y" if (wc.INDUSTRIAL_WORDS.search(text) or wc.industrial_zoning(zoning)) else "N"
        lat, lon = at.get("Latitude"), at.get("Longitude")
        rule = "all planning and development cases"
        rules[rule] += 1
        rows[rid] = {
            "source": SOURCE, "source_level": wc.SOURCE_LEVEL, "record_id": rid,
            "record_date": s["first_seen"], "date_type": "snapshot",
            "record_type": case_type_code(at.get("Type"), rid),
            "company_name": name, "company_role": role or "unknown",
            "site_address": "", "city": wc.UNINC, "county": wc.COUNTY, "zip": "",
            "description": desc, "flag": "Y", "flag_rule": rule,
            "source_url": wc.layer_query_url(LAYER, "CaseID='%s'" % rid),
            "retrieved_at": f["_fetched_at"],
            "industrial_use": ind, "parcel_number": parcel, "zoning": zoning, "status": status,
            "case_link": wc.clean(at.get("Epermit")),
            "latitude": "%.6f" % lat if lat else "", "longitude": "%.6f" % lon if lon else "",
            "title": title, "case_type_code": case_type_code(at.get("Type"), rid),
            "first_seen": s["first_seen"], "last_seen": s["last_seen"], "active": "Y",
            "spr_recorded_date": wc.ms_to_date(j.get("DATE_")) if j else "",
            "parser_version": wc.PARSER_VERSION}
    # Cases that left the active view since an earlier run: keep, never delete.
    dropped = 0
    for rid, r in prev.items():
        if rid not in rows:
            r = dict(r)
            r["active"] = "N"
            rows[rid] = r
            dropped += 1
    out_rows = sorted(rows.values(), key=lambda r: (r["record_date"], r["record_id"]))
    wc.write_csv(OUT, wc.COMMON_COLS + EXTRA_COLS, out_rows)
    wc.write_snapshot(SNAP, snap, ["status", "title"])
    if a.since:
        inc = [r for r in out_rows if r["first_seen"] >= a.since]
        wc.write_csv(OUT.replace(".csv", "_since_%s.csv" % a.since), wc.COMMON_COLS + EXTRA_COLS, inc)
        print("incremental rows (first_seen >= %s): %d" % (a.since, len(inc)))
    print("rows written: %d (active today %d, source count %d, kept from earlier runs %d)"
          % (len(out_rows), len(seen), n_source, dropped))
    print("titles blanked as probable individuals:", individuals)
    print("company_name filled:", sum(1 for r in out_rows if r["company_name"]))
    print("flag rules:", rules.most_common())
    print("industrial_use:", Counter(r["industrial_use"] for r in out_rows))
    print("types:", Counter(r["record_type"] for r in out_rows).most_common())
    print("status:", Counter(r["status"] for r in out_rows).most_common())


if __name__ == "__main__":
    main()
