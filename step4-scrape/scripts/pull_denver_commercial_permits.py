#!/usr/bin/env python3
"""Pull Denver commercial construction permits (ArcGIS REST) into the step 4 shared format.

Usage:  python3 pull_denver_commercial_permits.py [--since YYYY-MM-DD] [--fresh]

--since  DATE_RECEIVED cursor (default 2024-01-01). For an incremental run pass the last
         record_date already held and de-duplicate on record_id downstream.
--fresh  ignore today's raw cache and refetch.
Raw pages are cached under raw/permits_<since>_<UTC day>/ so a broken run resumes.
"""
import argparse, os, re, shutil, sys, urllib.parse
from collections import Counter
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arcgis_common as ac

HERE = os.path.dirname(os.path.abspath(__file__))
LAYER = ac.HOST + "/ODC_DEV_COMMERCIALCONSTPERMIT_P/FeatureServer/317"
SOURCE = "Denver commercial construction permits"
OUT = os.path.join(HERE, "scrape_denver_commercial_permits.csv")

# Fields retrieved. BID_AUTHNAME (a person-name style field, empty in practice) and
# GLOBALID are deliberately not requested.
FIELDS = ["OBJECTID", "PERMIT_NUM", "DATE_RECEIVED", "DATE_ISSUED", "FINAL_DATE", "CANCEL",
          "ADDRESS", "LOCATION", "CLASS", "UNITS", "VALUATION", "PERMIT_FEE", "CONTRACTOR_NAME",
          "LOG_NUM", "EXEMPT", "CO_REQUIRED", "DATE_CO_ISSUED", "SCHEDNUM",
          "STAT_CODE_1", "STAT_CODE_2", "STAT_CODE_3", "NEIGHBORHOOD"]

EXTRA_COLS = ["valuation", "date_issued", "final_date", "cancel_date", "class", "contractor",
              "neighborhood", "neighborhood_source", "zone_district", "zone_dist_type",
              "zone_description", "zoning_source", "industrial_zoning", "parcel_class", "schedule_number", "location_detail", "units", "permit_fee",
              "log_number", "co_required", "date_co_issued", "exempt_code", "stat_code_1",
              "stat_code_2", "stat_code_3", "latitude", "longitude", "location_source", "parser_version"]

VALUATION_MIN = 250000

# Denver statistical neighborhoods treated as industrial-heavy (layer's own spelling).
INDUSTRIAL_NBHD = {
    "Elyria Swansea", "Globeville", "Northeast Park Hill", "Montbello", "Central Park",
    "Stapleton", "DIA", "Gateway - Green Valley Ranch", "Sun Valley", "Valverde",
    "Athmar Park", "Baker", "Overland", "College View - South Platte", "Ruby Hill",
    "Lincoln Park", "Five Points", "Sunnyside", "Chaffee Park", "Regis", "Cole", "Clayton"}


is_industrial_zone = ac.is_industrial_zone


BUSINESS_HINT = re.compile(
    r"\b(llc|l\.l\.c|inc|incorporated|corp|corporation|co|company|ltd|lp|llp|pllc|pc|"
    r"construction|constructors?|contractors?|contracting|builders?|building|group|services?|"
    r"electric|electrical|mechanical|plumbing|roofing|restoration|development|enterprises?|"
    r"associates|partners|solutions|systems|design|homes|properties|industries|interiors|"
    r"remodeling|renovations?|signs?|fire|steel|concrete|glass|events?|productions?|"
    r"management|engineering|commercial|general|facilities|facility|installations?|"
    r"denver|colorado|university|school|city|county|airlines?|airport|rtd|dba|and|of|the|"
    r"hospital|developed|incorporation|fastsigns|companies|international|pools?|carpentry|"
    r"doctor|partnership|applied|constructon|daikin|planet|empire)\b|\d|&",
    re.I)


def looks_like_individual(name):
    """Conservative: two or three plain alphabetic words and no business hint at all."""
    n = name.strip()
    if n.upper() in ("HOME OWNER", "HOMEOWNER", "OWNER"):
        return True
    if not n or BUSINESS_HINT.search(n):
        return False
    words = n.replace(",", " ").split()
    return 2 <= len(words) <= 3 and all(re.fullmatch(r"[A-Za-z][A-Za-z.'\-]*", w) for w in words)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    raw_root = os.path.join(HERE, "raw")
    cache = os.path.join(raw_root, "permits_%s_%s" % (a.since, day))
    ref_cache = os.path.join(raw_root, "reference_%s" % day)
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)
    where = "DATE_RECEIVED >= TIMESTAMP '%s 00:00:00'" % a.since

    ac.require_fields(LAYER, FIELDS)
    n_source = ac.source_count(LAYER, where)
    print("source count for filter:", n_source)
    feats = ac.fetch_all(LAYER, where, FIELDS, cache, page_size=1000)
    zoning = ac.load_zoning(ref_cache)
    nbhds = ac.load_neighborhoods(ref_cache)
    parcels = ac.load_parcels([ac.clean(f["attributes"].get("SCHEDNUM")) for f in feats], ref_cache)

    rows, individuals = [], 0
    for f in feats:
        at = f["attributes"]
        g = f.get("geometry") or {}
        x, y = g.get("x"), g.get("y")
        sched = ac.clean(at.get("SCHEDNUM"))
        parcel = parcels.get(sched)
        loc_src = ""
        if ac.in_denver_bbox(x, y):
            loc_src = "permit point"
        elif parcel and ac.in_denver_bbox(parcel.get("x"), parcel.get("y")):
            x, y, loc_src = parcel["x"], parcel["y"], "parcel situs point"
        else:
            x = y = None
        geocoded = bool(loc_src)
        nb = ac.clean(at.get("NEIGHBORHOOD"))
        nb_src = "layer" if nb else ""
        zd = zt = zdesc = zsrc = ""
        if geocoded:
            z = zoning.find(x, y)
            if z:
                zd, zt, zdesc = ac.clean(z.get("ZONE_DISTRICT")), ac.clean(z.get("ZONE_DIST_TYPE")), ac.clean(z.get("ZONE_DESCRIPTION"))
                zsrc = "zoning polygon at " + loc_src
            if not nb:
                h = nbhds.find(x, y)
                if h:
                    nb, nb_src = ac.clean(h.get("NBHD_NAME")), "spatial join at " + loc_src
        if not zd and parcel and ac.clean(parcel.get("ZONE_10")):
            zd, zsrc = ac.clean(parcel.get("ZONE_10")), "parcel ZONE_10"
        contractor = ac.clean(at.get("CONTRACTOR_NAME"))
        if contractor and looks_like_individual(contractor):
            contractor = ""
            individuals += 1
        val = at.get("VALUATION")
        flag, rule = "N", ""
        if val is not None and val >= VALUATION_MIN:
            # Zoning is the more specific evidence, so it is named first when both hold.
            if is_industrial_zone(zd, zt):
                flag, rule = "Y", "valuation >= 250k + industrial zoning: %s" % zd
            elif nb in INDUSTRIAL_NBHD:
                flag, rule = "Y", "valuation >= 250k + industrial neighborhood: %s" % nb
        pn = ac.clean(at.get("PERMIT_NUM"))
        url = LAYER + "/query?" + urllib.parse.urlencode(
            {"where": "PERMIT_NUM='%s'" % pn, "outFields": "*", "f": "html"})
        rows.append({
            "source": SOURCE, "source_level": "County (Denver)", "record_id": pn,
            "record_date": ac.ms_to_date(at.get("DATE_RECEIVED")), "date_type": "received",
            "record_type": ac.clean(at.get("CLASS")),
            "company_name": contractor, "company_role": "contractor" if contractor else "unknown",
            "site_address": ac.clean(at.get("ADDRESS")), "city": "Denver", "county": "Denver",
            "zip": ac.clean(parcel.get("SITUS_ZIP"))[:5] if parcel else "", "description": "", "flag": flag, "flag_rule": rule,
            "source_url": url, "retrieved_at": f["_fetched_at"],
            "valuation": "" if val is None else ("%d" % val if float(val).is_integer() else "%.2f" % val),
            "date_issued": ac.ms_to_date(at.get("DATE_ISSUED")),
            "final_date": ac.ms_to_date(at.get("FINAL_DATE")),
            "cancel_date": ac.ms_to_date(at.get("CANCEL")),
            "class": ac.clean(at.get("CLASS")), "contractor": contractor,
            "neighborhood": nb, "neighborhood_source": nb_src,
            "zone_district": zd, "zone_dist_type": zt, "zone_description": zdesc,
            "zoning_source": zsrc,
            "industrial_zoning": ("Y" if is_industrial_zone(zd, zt) else "N") if zd else "", "parcel_class": ac.clean(parcel.get("D_CLASS_CN")) if parcel else "",
            "schedule_number": sched,
            "location_detail": ac.clean(at.get("LOCATION")), "units": ac.clean(at.get("UNITS")),
            "permit_fee": "" if at.get("PERMIT_FEE") is None else "%g" % at["PERMIT_FEE"],
            "log_number": ac.clean(at.get("LOG_NUM")), "co_required": ac.clean(at.get("CO_REQUIRED")),
            "date_co_issued": ac.clean(at.get("DATE_CO_ISSUED")),
            "exempt_code": ac.clean(at.get("EXEMPT")),
            "stat_code_1": ac.clean(at.get("STAT_CODE_1")), "stat_code_2": ac.clean(at.get("STAT_CODE_2")),
            "stat_code_3": ac.clean(at.get("STAT_CODE_3")),
            "latitude": "%.6f" % y if geocoded else "", "longitude": "%.6f" % x if geocoded else "",
            "location_source": loc_src, "parser_version": ac.PARSER_VERSION})
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    ac.write_csv(OUT, ac.COMMON_COLS + EXTRA_COLS, rows)
    print("rows written: %d (source count %d)" % (len(rows), n_source))
    print("contractor names blanked as probable individuals:", individuals)
    print("flag rules:", Counter(r["flag_rule"].split(":")[0] for r in rows if r["flag"] == "Y"))
    if len(rows) != n_source:
        raise SystemExit("ROW COUNT MISMATCH against source")


if __name__ == "__main__":
    main()
