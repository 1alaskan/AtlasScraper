#!/usr/bin/env python3
"""Pull Aurora development applications (AMANDA via ArcGIS Enterprise, OpenData layer 180),
Adams County side only.

Usage:  python3 pull_aurora_development_applications.py [--since YYYY-MM-DD] [--fresh]

--since  InDate cursor (default 2024-01-01). 2023 cases that are still open are always
         carried in (the layer keeps Retired history, so status is testable here).
--fresh  ignore the raw cache and refetch.

The whole date range is pulled in one where clause (InDate only: Cloudflare in front of
ags.auroragov.org returns 403 for some County clauses, so County and nulls are filtered
client-side, as the step 2 notes say). Raw pages go to raw/aurora_development_applications/.
CaseMan (a staff name) is deliberately not requested.
"""
import argparse, json, os, re, shutil, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aurora_brighton_common as c

LAYER = c.AURORA + "/180"
SOURCE = "Aurora development applications"
SLUG = "aurora_development_applications"
OUT = os.path.join(c.ADAMS_DIR, "scrape_%s.csv" % SLUG)
CACHE = os.path.join(c.RAW_ROOT, SLUG)

FIELDS = ["OBJECTID", "FolderRSN", "PropertyRSN", "PropX", "PropY", "InDate", "foldercondition",
          "folderdescription", "FolderStatus", "FolderName", "DANum", "Address", "Parcel", "zip",
          "County", "SiteAcreage", "ExistZone", "PropZone", "PropNumDwell", "PropNumHotel",
          "ZoneInit", "ZoneReZone", "GDPNew", "GDPAmended", "FDPNew", "FDPAmended", "MasterPlan",
          "SitePlanNew", "SitePlanAmended", "CSPNew", "CSPAmended", "SubPlatNew", "SubPlatAmend",
          "SubPlatVac", "CondUse", "SignAppr", "Vac", "DefPubImpr", "SubReplat", "created_date",
          "last_edited_date"]

CASE_FLAGS = [("ZoneInit", "initial zoning"), ("ZoneReZone", "rezoning"), ("GDPNew", "GDP new"),
              ("GDPAmended", "GDP amendment"), ("FDPNew", "FDP new"), ("FDPAmended", "FDP amendment"),
              ("MasterPlan", "master plan"), ("SitePlanNew", "site plan new"),
              ("SitePlanAmended", "site plan amendment"), ("CSPNew", "CSP new"),
              ("CSPAmended", "CSP amendment"), ("SubPlatNew", "plat new"), ("SubPlatAmend", "plat amendment"),
              ("SubPlatVac", "plat vacation"), ("CondUse", "conditional use"), ("SignAppr", "sign approval"),
              ("Vac", "vacation"), ("DefPubImpr", "deferred public improvements"), ("SubReplat", "replat")]

CLOSED = {"Retired", "Denied & Retired", "Retire File"}

EXTRA_COLS = ["folder_name", "da_number", "folder_rsn", "status", "case_type", "use", "square_feet",
              "industrial_use", "site_acreage", "exist_zone", "prop_zone", "prop_num_dwell",
              "prop_num_hotel", "parcel", "county_field", "county_basis", "zoning_district", "zoning_name",
              "zoning_class", "carried_in_2023", "latitude", "longitude", "created_date",
              "last_edited_date", "parser_version"]

USE_WORDS = [
    ("data center", re.compile(r"\bDATA CENTER\b", re.I)),
    ("industrial", re.compile(r"\bINDUSTRIAL\b", re.I)),
    ("manufacturing", re.compile(r"\bMANUFACTUR\w*|\bFACTORY\b|\bPLANT\b|\bFABRICAT\w*", re.I)),
    ("warehouse", re.compile(r"\bWAREHOUS\w*|\bSTORAGE BUILDING\b|\bCOLD STORAGE\b", re.I)),
    ("retail", re.compile(r"\bRETAIL\b|\bRESTAURANT\b|\bGAS STATION\b|\bFUELING STATION\b|\bCONVENIENCE\b|\bCAR WASH\b|\bDRIVE[- ]THR?U\b|\bLIQUOR\b|\bGROCERY\b", re.I)),
    ("distribution", re.compile(r"\bDISTRIBUTION\b|\bLOGISTICS\b|\bCROSS[- ]?DOCK\w*|\bFULFILLMENT\b|\bTRUCKING\b|\bTRUCK (STORAGE|TERMINAL|REPAIR|MAINTENANCE)\b|\bMOTOR FREIGHT\b|\bFREIGHT\b", re.I)),
    ("flex", re.compile(r"\bFLEX\b", re.I)),
    ("brewery", re.compile(r"\bBREW\w*", re.I)),
    ("residential", re.compile(r"\bRESIDENTIAL\b|\bSINGLE[- ]FAMILY\b|\bTOWNHOME\w*|\bAPARTMENT\w*|\bDWELLING\w*|\bMULTI[- ]?FAMILY\b|\bDUPLEX\w*|\bADU\b|\bHOUSING\b|\bHOMES\b", re.I)),
    ("hotel", re.compile(r"\bHOTEL\b|\bSUITES\b|\bINN\b", re.I)),
    ("office", re.compile(r"\bOFFICE\b|\bMEDICAL\b|\bCLINIC\b", re.I)),
    ("school or civic", re.compile(r"\bSCHOOL\b|\bCHURCH\b|\b(NEIGHBORHOOD|REGIONAL|PERIMETER|BUTTERFLY|SUNSET) PARKS?\b|\bPARK-N-RIDE\b|\bTRAILHEAD\b|\bFIRE STATION\b|\bLIBRARY\b|\bANIMAL SHELTER\b|\bRAIL STATION\b", re.I)),
]
INDUSTRIAL_USES = {"data center", "industrial", "manufacturing", "warehouse", "distribution", "flex", "brewery"}


def derive_use(text):
    for label, rx in USE_WORDS:
        if rx.search(text):
            return label
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    if a.fresh:
        shutil.rmtree(CACHE, ignore_errors=True)
    os.makedirs(CACHE, exist_ok=True)

    c.require_fields(LAYER, FIELDS)
    carry_from = "2023-01-01"
    where = "InDate >= DATE '%s'" % carry_from
    n_source = c.arcgis_count(LAYER, where)
    print("source count for InDate >= %s (all counties): %d" % (carry_from, n_source))
    feats = c.arcgis_fetch(LAYER, where, FIELDS, CACHE, "da_%s" % carry_from, page_size=2000,
                           geometry=True, out_sr=4326)
    if len(feats) != n_source:
        raise SystemExit("Row count %d does not match source count %d" % (len(feats), n_source))
    zoning = c.load_aurora_zoning(os.path.join(c.RAW_ROOT, "aurora_zoning"))

    rows, left = [], {"arapahoe or douglas": 0, "county null south of line or no xy": 0,
                      "2023 closed": 0, "before since (open 2023 carried in)": 0}
    for f in feats:
        at = f["attributes"]
        date = c.ms_to_date(at.get("InDate"))
        county = c.clean(at.get("County")).upper()
        px, py = at.get("PropX"), at.get("PropY")
        if county == "ADAMS":
            basis = "County field"
        elif county in ("", "NONE") and px and py and py > c.COLFAX_Y:
            basis = "County null, PropY north of Colfax line"
        elif county in ("", "NONE"):
            left["county null south of line or no xy"] += 1
            continue
        else:
            left["arapahoe or douglas"] += 1
            continue
        status = c.clean(at.get("FolderStatus"))
        carried = ""
        if date < a.since:
            if status in CLOSED:
                left["2023 closed"] += 1
                continue
            carried = "Y"
            left["before since (open 2023 carried in)"] += 1

        name = c.clean(at.get("FolderName"))
        desc = c.clean(at.get("folderdescription"))
        text = name + " " + desc
        use = derive_use(text)
        sqft = c.sqft_from_text(desc)
        case_type = "; ".join(label for fld, label in CASE_FLAGS if c.clean(at.get(fld)).upper() in ("Y", "YES", "1", "TRUE"))
        zd = zn = zc = ""
        if px and py:
            z = zoning.find(px, py)
            if z:
                zd, zn = c.clean(z.get("DISTRICT_ID")), c.clean(z.get("Dist_Name"))
                zc = c.zoning_class(zd)
        industrial = "Y" if (use in INDUSTRIAL_USES or zc == "industrial" or
                             c.clean(at.get("PropZone")).upper() in ("I-1", "I-2") or
                             c.clean(at.get("ExistZone")).upper() in ("I-1", "I-2")) else "N"
        # FolderName is the project name as first filed; blank it when it reads as a person.
        company = "" if c.looks_like_person(name) else name
        g = f.get("geometry") or {}
        lon, lat = g.get("x"), g.get("y")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            lon = lat = None
            if px and py:   # Shape is null on some rows while PropX/PropY are populated
                lon, lat = c.stateplane_to_lonlat(px, py)
        if not case_type:
            up = name.upper()
            case_type = ("site plan minor amendment" if up.endswith("SP AM") or "MINOR AMENDMENT" in desc.upper()
                         else "site plan" if "SITE PLAN" in up else "")
        rid = c.clean(at.get("DANum")) or "RSN-%s" % at.get("FolderRSN")
        url = LAYER + "/query?" + urllib.parse.urlencode({"where": "FolderRSN=%s" % at.get("FolderRSN"),
                                                          "outFields": "*", "f": "html"})
        rows.append({
            "source": SOURCE, "source_level": "County (Adams)", "record_id": rid,
            "record_date": date, "date_type": "entered",
            "record_type": case_type or "development application",
            "company_name": company, "company_role": "project" if company else "unknown",
            "site_address": c.clean(at.get("Address")), "city": "Aurora", "county": "Adams",
            "zip": c.clean(at.get("zip"))[:5],
            "description": c.clean(desc, 500),
            "flag": "Y", "flag_rule": "all planning and development cases",
            "source_url": url, "retrieved_at": f["_fetched_at"],
            "folder_name": name, "da_number": c.clean(at.get("DANum")),
            "folder_rsn": str(at.get("FolderRSN") or ""), "status": status, "case_type": case_type,
            "use": use, "square_feet": sqft, "industrial_use": industrial,
            "site_acreage": c.clean(at.get("SiteAcreage")), "exist_zone": c.clean(at.get("ExistZone")),
            "prop_zone": c.clean(at.get("PropZone")), "prop_num_dwell": c.clean(at.get("PropNumDwell")),
            "prop_num_hotel": c.clean(at.get("PropNumHotel")), "parcel": c.clean(at.get("Parcel")),
            "county_field": c.clean(at.get("County")), "county_basis": basis,
            "zoning_district": zd, "zoning_name": zn, "zoning_class": zc, "carried_in_2023": carried,
            "latitude": "" if lat is None else round(lat, 6), "longitude": "" if lon is None else round(lon, 6),
            "created_date": c.ms_to_date(at.get("created_date")),
            "last_edited_date": c.ms_to_date(at.get("last_edited_date")),
            "parser_version": c.PARSER_VERSION,
        })
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    c.write_csv(OUT, c.COMMON_COLS + EXTRA_COLS, rows)
    s = c.summarize(rows)
    s["left_out"] = left
    s["industrial_use_Y"] = sum(1 for r in rows if r["industrial_use"] == "Y")
    s["county_basis"] = {k: sum(1 for r in rows if r["county_basis"] == k) for k in {r["county_basis"] for r in rows}}
    s["source_count_all_counties"] = n_source
    with open(os.path.join(CACHE, "summary.json"), "w") as fh:
        json.dump(s, fh, indent=1)
    print(json.dumps(s, indent=1))
    print("wrote", OUT, len(rows), "rows")


if __name__ == "__main__":
    main()
