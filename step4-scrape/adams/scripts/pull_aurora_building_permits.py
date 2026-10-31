#!/usr/bin/env python3
"""Pull Aurora building permits (AMANDA via ArcGIS Enterprise, OpenData layer 44),
Adams County side only (PropY > 1,695,150 ft, the E Colfax Ave county line).

Usage:  python3 pull_aurora_building_permits.py [--since YYYY-MM-DD] [--fresh]

The pull always covers InDate 2023-01-01 onward, one calendar month per request, with the
PropY cut in the where clause. 2023 rows are kept only when they are non-residential
construction permits (the layer has no status, final or expiry field, so "still active"
cannot be tested; they are tagged carried_in_2023 = Y). Residential rows are left out
and counted.
--since  refetch the months from this date on (incremental refresh); earlier months are
         read from the raw cache. Default: fetch only months not yet cached.
--fresh  drop the whole raw cache and refetch everything.
Raw pages: raw/aurora_building_permits/. FolderCondition (staff notes with names and phone
numbers) is deliberately not requested.
"""
import argparse, json, os, re, shutil, sys, urllib.parse
from collections import Counter
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aurora_brighton_common as c

LAYER = c.AURORA + "/44"
SOURCE = "Aurora building permits"
SLUG = "aurora_building_permits"
OUT = os.path.join(c.ADAMS_DIR, "scrape_%s.csv" % SLUG)
CACHE = os.path.join(c.RAW_ROOT, SLUG)
START = "2023-01-01"

FIELDS = ["OBJECTID", "FolderRSN", "Permit_", "InDate", "FolderType", "FolderDesc", "FolderGroupDesc",
          "SubDesc", "FolderDescription", "IssueDate", "valuation", "PropertyRSN", "PropX", "PropY",
          "Address", "PropertyRoll"]

RES_SUBDESC = {"Roofing-RT2", "Single-Family Detached", "Solar PV Residential Permit",
               "Residential Miscellaneous", "Basement Finish Permit", "Damage Repair-RT6",
               "Residential Patio Cover", "Residential Deck Permit", "Residential Addition Permit",
               "Res. Hook, Set, & Tie-RT4", "Single Family Detached Plan", "Sales Trailer - Residential",
               "Sales Office for Residential", "Residential Elevator Permit", "Multi-Family Building"}
RES_FOLDERDESC = {"Permit from Residential Master", "Permit for Custom S.F. Residential",
                  "Multi-Family Permit from Master"}
RES_TEXT = re.compile(r"\bRESIDENTIAL\b|\bRESIDENCE\b|\bSINGLE[- ]FAMILY\b|\bSFD\b|\bSFR\b|\bBASEMENT\b|"
                      r"\bDUPLEX\w*|\bTOWNHOME\w*|\bTOWNHOUSE\w*|\bADU\b|\bAPARTMENT\w*|\bMULTI[- ]?FAMILY\b|"
                      r"\bHOMEOWNER\b|\bMOBILE HOME\b|\bMODULAR HOME\b|\bPATIO COVER\b", re.I)

# Building-class subtypes (new building, addition, tenant finish, change of use)
BUILDING_SUBDESC = {"Tenant Improvement", "Tenant Finish-NT1", "Non-Res. Addition-NT8", "Change in Occupancy",
                    "Storage Use Building", "Factory Use Building", "Business Use Building",
                    "Mercantile Use Building", "Assembly Building", "Hazardous Occupancy Bldg",
                    "Group U Building", "Hotel Building", "Group E", "Racking/High Piled Combustibles",
                    "Above Ground Fuel Storage", "Below Ground Fuel Storage", "Hazardous Materials"}
INDUSTRIAL_SUBDESC = {"Factory Use Building", "Storage Use Building", "Hazardous Occupancy Bldg",
                      "Racking/High Piled Combustibles", "Above Ground Fuel Storage",
                      "Below Ground Fuel Storage", "Hazardous Materials"}
# Not construction work: never tier A or B, kept with flag N.
EXCLUDED_SUBDESC = {"Sign Permit-Wall Mount/Cabinet", "Sign Permit-Ground/Monument > 6'",
                    "Sign Permit-Monument <= 6'", "Roofing Commercial-NT2", "Ground Mount Antennae",
                    "Rooftop Mount Antennae", "Radio Frequency", "Demolition Full Structure-8Q",
                    "Partial Demolition-8Q", "Temporary Sales/Construction Office-NT4",
                    "Sales Trailer - Commercial", "Gating System", "Fence Permit", "Commercial Swimming Pool",
                    "Occupancy Load Sign Calculation", "Non-Res Fire Damage Repair-NT6", "Private Development",
                    "City Project"}
EXCLUDED_FOLDERDESC = {"Public Improvement Permit", "Tree Mitigation"}

PREFIX = re.compile(r"^(?:\s*\|?\s*(?:BUILDINGONLINE|PERMITSONLINE|BUILDING ONLINE)\s*\|?\s*)+", re.I)
PHONE = re.compile(r"\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b")
EMAIL = re.compile(r"\S+@\S+")
CODENAME = re.compile(r"\bPROJECT\s+([A-Z][A-Z0-9'\-]+)(?:\s+([A-Z][A-Z0-9'\-]+))?")
SCOPE_WORDS = {"TENANT", "TI", "FIRE", "CORE", "MAIN", "WATER", "ETHANOL", "TEMP", "TEMPORARY", "COMMERCIAL",
               "PHASE", "STRUCTURE", "CONVEYOR", "ADVISE", "BLDG", "BUILDING", "SITE", "REVISION", "ELECTRICAL",
               "MECHANICAL", "PLUMBING", "SHELL", "PMI", "NEW", "SUITE", "UNIT", "FOUNDATION", "OFFICE",
               "WAREHOUSE", "MANAGER", "MANAGEMENT", "PARKING", "STORAGE", "INTERIOR", "EXTERIOR", "SPRINKLER",
               "ALARM", "PUMP", "DEMO", "RACKING", "IS", "NO", "NUMBER", "ADDRESS",
               "REMODEL", "ADDITION", "EXPANSION", "SCOPE", "FULL", "PARTIAL", "ROOF", "SOLAR", "GENERATOR",
               "MEZZANINE", "SPEC", "LANDLORD", "CONSTRUCTION", "TRAILER", "FENCE", "SIGN", "SYSTEM", "SYSTEMS",
               "CHANGE", "WILL", "START", "WORK", "ONLY", "PLAN", "PLANS", "DRAWINGS", "PACKAGE", "EQUIPMENT",
               "BTS", "RENO", "RENOVATION", "HOOD", "SUPPRESSION", "RTU", "RTUS", "FENCE", "GATING", "FLOORS", "FLOOR",
               "1ST", "2ND", "3RD", "MODIFY", "REPLACE", "REPLACEMENT", "REPLACEMENTS", "COOLER", "COOLERS", "GROUND",
               "SUPPORT", "PLATFORM", "STRUCTURAL", "MULTI-LEVEL", "MINOR", "MAJOR", "INSTALL", "INSTALLATION",
               "SOLAR", "ELECTRIC", "ELEC", "MECH", "GAS", "WATER", "SEWER", "HVAC", "AC", "FURNACE", "BOILER",
               "LIGHTING", "LIGHTS", "EV", "CHARGER", "CHARGERS", "ACCESS", "CONTROL", "CAMERA", "CAMERAS",
               "SECURITY", "DOOR", "DOORS", "WINDOW", "WINDOWS", "ROOFING", "REROOF", "RE-ROOF", "DEFERRED",
               "SUBMITTAL", "AREA", "SPACE", "ROOM", "KITCHEN", "RESTROOM", "BATHROOM", "LOBBY", "CANOPY",
               "SUBDIVISION", "FILING", "FILLING", "LOT", "BUILDOUT", "BUILD-OUT", "FIT-OUT", "FITOUT", "RACK",
               "RACKS", "SHELVING", "TANK", "TANKS", "FUEL", "PROPANE", "DISPENSER", "FREEZER", "WALK-IN",
               "DEMOLITION", "ABATEMENT", "ASBESTOS", "TRANSFORMER", "SWITCHGEAR", "UPS", "BATTERY", "COOLING",
               "TOWER", "CHILLER", "COMPRESSOR", "DUST", "COLLECTION", "PAINT", "BOOTH", "CRANE", "CONVEYORS",
               "CONVEYOR", "MEZZ", "STAIRS", "STAIR", "RAMP", "DOCK", "LEVELER", "LEVELERS", "AWNING", "WALL",
               "SIGNS", "SIGNAGE", "MONUMENT", "TEMPORARY", "TEMP", "HEAT", "HEATERS", "HEATER", "SPRINKLERS",
               "ALARMS", "STROBES", "HEADS", "DEVICES", "PHASE1", "PHASE2", "BUILDING1", "BUILDING2", "DATA",
               "CABLING", "LOW", "VOLTAGE", "ANTENNA", "ANTENNAS", "DAS", "ERCES", "BDA", "TIE", "TIE-IN", "WITH",
               "W/", "PER", "ATTN", "SEE", "RE", "RE:", "REF", "REFERENCE"}
CONNECTORS = {"AT", "FOR", "THE", "AND", "OF", "IN", "ON", "TO", "A", "AN", "WITH"}
GENERIC_LEAD = re.compile(r"^(TENANT|FIRE|ELECTRICAL|MECHANICAL|PLUMBING|INSTALL|NEW|REPLACE|REMOVE|ADD|"
                          r"COMMERCIAL|RACKING|SOLAR|SIGN|ROOF|RE-ROOF|REROOF|DEMO|INTERIOR|EXTERIOR|"
                          r"REVISION|PLAN|TEMPORARY|TI\b|T\.I\.|REMODEL|BUILD|UNIT|SUITE|STE|BLDG|BUILDING|LEASE|REVISED|REVISE|"
                          r"FOUNDATION|SCOPE|STATED|COMMENTS|PERMIT|ADDRESS|CHANGE|RELOCATE|RELO|UPGRADE|REPAIR|"
                          r"EXISTING|PROPOSED|CONVERT|MODIFY|ADDING|MOVE|ELEVATOR|HVAC|PANEL|RTU|CAD|FDC)", re.I)

EXTRA_COLS = ["permit_number", "folder_rsn", "folder_type", "permit_type", "permit_subtype", "valuation",
              "valuation_raw", "issue_date", "permit_class", "industrial_word", "industrial_subtype",
              "zoning_district", "zoning_name", "zoning_class", "tier", "carried_in_2023", "scope_key",
              "property_rsn", "prop_y", "latitude", "longitude", "parser_version"]


def parse_val(s):
    s = c.clean(s).replace(",", "").replace("$", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return v if v > 1.0 else None   # 0 and 1.00 are placeholders on intake copies and revisions


def company_from_description(desc):
    """Conservative: a PROJECT codename anywhere, else the leading segment when it carries a
    business suffix. Never a bare name."""
    m = CODENAME.search(desc)
    if m and m.group(1) not in SCOPE_WORDS and not c.looks_like_person(m.group(1) + " " + (m.group(2) or "")):
        name = "PROJECT " + m.group(1)
        if m.group(2) and m.group(2) not in SCOPE_WORDS and m.group(2) not in CONNECTORS:
            name += " " + m.group(2)
        return name, "project"
    lead = re.split(r"\s+-\s+|\s*\|\s*|\s+@\s+|:\s|,\s|\s/\s", desc, maxsplit=1)[0].strip(" -|")
    toks = lead.split()
    cut = len(toks)
    for i, t in enumerate(toks):
        if t.upper().strip(".,;") in SCOPE_WORDS and i > 0:
            cut = i
            break
    lead = " ".join(toks[:cut]).strip(" -,")
    if 2 <= len(toks[:cut]) <= 8 and len(lead) <= 60 and c.CORP_SUFFIX.search(lead) and not GENERIC_LEAD.match(lead) \
            and not re.search(r"\d{3,}", lead) and not c.looks_like_person(lead):
        role = "tenant" if re.search(r"\bTENANT\b|\bTI\b|\bT\.I\.", desc, re.I) else "unknown"
        return lead, role
    return "", "unknown"


def scope_key(addr, desc):
    d = re.sub(r"[^A-Z0-9 ]", " ", desc.upper())
    d = re.sub(r"\s+", " ", d).strip()[:80]
    return (addr.upper().strip() + " | " + d).strip()


def fetch_months(since, fresh):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if fresh:
        shutil.rmtree(CACHE, ignore_errors=True)
    os.makedirs(CACHE, exist_ok=True)
    feats = []
    ranges = list(c.month_ranges(START, today[:7] + "-01"))
    ranges.append((today[:7] + "-01", None))   # open-ended tail for the current month and future-dated intakes
    for a, b in ranges:
        tag = "pm_%s" % a[:7]
        if since and a[:7] >= since[:7]:
            for fn in os.listdir(CACHE):
                if fn.startswith(tag + "_"):
                    os.remove(os.path.join(CACHE, fn))
        date_clause = "InDate >= DATE '%s'" % a + (" AND InDate < DATE '%s'" % b if b else "")
        where = date_clause + " AND PropY > %d" % int(c.COLFAX_Y)
        try:
            got = c.arcgis_fetch(LAYER, where, FIELDS, CACHE, tag, page_size=2000, geometry=True, out_sr=4326)
        except c.HttpRefused as e:
            # Documented fallback: the WAF refused this clause shape; pull the month by date only
            # and apply the county cut client-side.
            print("  403 on", tag, "-> date-only clause, client-side PropY cut", file=sys.stderr)
            got = c.arcgis_fetch(LAYER, date_clause, FIELDS, CACHE, tag + "_dateonly", page_size=2000,
                                 geometry=True, out_sr=4326)
            got = [g for g in got if (g["attributes"].get("PropY") or 0) > c.COLFAX_Y]
        feats.extend(got)
    return feats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None)
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    c.require_fields(LAYER, FIELDS)
    n_src_24 = c.arcgis_count(LAYER, "InDate >= DATE '2024-01-01' AND PropY > %d" % int(c.COLFAX_Y))
    n_src_23 = c.arcgis_count(LAYER, "InDate >= DATE '2023-01-01' AND InDate < DATE '2024-01-01' AND PropY > %d" % int(c.COLFAX_Y))
    n_all_24 = c.arcgis_count(LAYER, "InDate >= DATE '2024-01-01'")
    n_noxy_24 = c.arcgis_count(LAYER, "InDate >= DATE '2024-01-01' AND PropY IS NULL")
    print("source counts: Adams-side since 2024 %d, Adams-side 2023 %d, all since 2024 %d, no XY since 2024 %d"
          % (n_src_24, n_src_23, n_all_24, n_noxy_24))
    feats = fetch_months(a.since, a.fresh)
    if len(feats) != n_src_24 + n_src_23:
        raise SystemExit("Fetched %d rows, source says %d" % (len(feats), n_src_24 + n_src_23))
    zoning = c.load_aurora_zoning(os.path.join(c.RAW_ROOT, "aurora_zoning"))

    rows = []
    left = Counter()
    seen = set()
    for f in feats:
        at = f["attributes"]
        oid = at["OBJECTID"]
        if oid in seen:
            left["duplicate OBJECTID across pages"] += 1
            continue
        seen.add(oid)
        date = c.ms_to_date(at.get("InDate"))
        fdesc = c.clean(at.get("FolderDesc"))
        sdesc = c.clean(at.get("SubDesc"))
        desc_raw = c.clean(at.get("FolderDescription"))
        desc = PREFIX.sub("", desc_raw).strip(" |-")
        desc = EMAIL.sub("", PHONE.sub("", desc)).strip()
        residential = (sdesc in RES_SUBDESC or fdesc in RES_FOLDERDESC or bool(RES_TEXT.search(desc)))
        if residential:
            left["residential"] += 1
            continue
        building_class = sdesc in BUILDING_SUBDESC or fdesc in ("Commercial Building Permit", "Tenant Finish")
        carried = ""
        if date < "2024-01-01":
            if not building_class:
                left["2023 not a construction permit"] += 1
                continue
            carried = "Y"
        excluded = sdesc in EXCLUDED_SUBDESC or fdesc in EXCLUDED_FOLDERDESC
        val = parse_val(at.get("valuation"))
        px, py = at.get("PropX"), at.get("PropY")
        zd = zn = zc = ""
        if px and py:
            z = zoning.find(px, py)
            if z:
                zd, zn = c.clean(z.get("DISTRICT_ID")), c.clean(z.get("Dist_Name"))
                zc = c.zoning_class(zd)
        ind_sub = sdesc in INDUSTRIAL_SUBDESC
        wm = c.INDUSTRIAL_WORDS.search(desc)
        ind_word = wm.group(0).upper() if wm else ""
        # "Industrial property" = zoning I-1, I-2 or AD, or an industrial permit subtype; the layer has
        # no land-use field. A description word alone qualifies only for tier A (250k+).
        industrial_property = zc == "industrial" or ind_sub
        comm_ind = zc == "commercial-industrial"
        flag, rule, tier = "N", "", ""
        if not excluded:
            if val is not None and val >= 250000 and (industrial_property or ind_word):
                tier = "A"
                rule = "valuation 250k+ and industrial " + ("zoning" if zc == "industrial" else "subtype" if ind_sub else "word")
            elif val is not None and 50000 <= val < 250000 and (industrial_property or comm_ind):
                tier = "B3a"
                rule = "valuation 50k to 250k on industrial or commercial-industrial property"
            elif (val is None or val < 50000) and industrial_property:
                tier = "B3b"
                rule = "under 50k or no valuation on industrial property"
            if tier:
                flag = "Y"
        company, role = company_from_description(desc)
        g = f.get("geometry") or {}
        lon, lat = g.get("x"), g.get("y")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            lon = lat = None
            if px and py:
                lon, lat = c.stateplane_to_lonlat(px, py)
        permit = c.clean(at.get("Permit_"))
        addr = c.clean(at.get("Address"))
        url = LAYER + "/query?" + urllib.parse.urlencode({"where": "FolderRSN=%s" % at.get("FolderRSN"),
                                                          "outFields": "*", "f": "html"})
        rows.append({
            "source": SOURCE, "source_level": "County (Adams)", "record_id": permit or "RSN-%s" % at.get("FolderRSN"),
            "record_date": date, "date_type": "entered",
            "record_type": (fdesc + (": " + sdesc if sdesc else "")).strip(),
            "company_name": company, "company_role": role if company else "unknown",
            "site_address": addr, "city": "Aurora", "county": "Adams", "zip": "",
            "description": c.clean(desc, 500),
            "flag": flag, "flag_rule": rule, "source_url": url, "retrieved_at": f["_fetched_at"],
            "permit_number": permit, "folder_rsn": str(at.get("FolderRSN") or ""),
            "folder_type": c.clean(at.get("FolderType")), "permit_type": fdesc, "permit_subtype": sdesc,
            "valuation": "" if val is None else ("%.0f" % val), "valuation_raw": c.clean(at.get("valuation")),
            "issue_date": c.ms_to_date(at.get("IssueDate")),
            "permit_class": "building" if building_class else ("excluded" if excluded else "trade or other"),
            "industrial_word": ind_word, "industrial_subtype": "Y" if ind_sub else "",
            "zoning_district": zd, "zoning_name": zn, "zoning_class": zc, "tier": tier,
            "carried_in_2023": carried, "scope_key": scope_key(addr, desc),
            "property_rsn": str(at.get("PropertyRSN") or ""), "prop_y": "" if py is None else "%.0f" % py,
            "latitude": "" if lat is None else round(lat, 6), "longitude": "" if lon is None else round(lon, 6),
            "parser_version": c.PARSER_VERSION,
        })
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    c.write_csv(OUT, c.COMMON_COLS + EXTRA_COLS, rows)
    s = c.summarize(rows)
    s["left_out"] = dict(left)
    s["source_counts"] = {"adams_side_since_2024": n_src_24, "adams_side_2023": n_src_23,
                          "all_since_2024": n_all_24, "no_xy_since_2024": n_noxy_24,
                          "removed_by_propy_cut_since_2024": n_all_24 - n_src_24}
    s["tiers"] = dict(Counter(r["tier"] for r in rows if r["tier"]))
    s["permit_class"] = dict(Counter(r["permit_class"] for r in rows))
    s["zoning_class"] = dict(Counter(r["zoning_class"] or "none" for r in rows))
    s["valuation_blank"] = sum(1 for r in rows if not r["valuation"])
    s["carried_in_2023"] = sum(1 for r in rows if r["carried_in_2023"])
    sk = Counter(r["scope_key"] for r in rows)
    s["scope_key_groups_with_2plus"] = sum(1 for v in sk.values() if v > 1)
    s["rows_in_scope_key_groups_with_2plus"] = sum(v for v in sk.values() if v > 1)
    with open(os.path.join(CACHE, "summary.json"), "w") as fh:
        json.dump(s, fh, indent=1)
    print(json.dumps(s, indent=1))
    print("wrote", OUT, len(rows), "rows")


if __name__ == "__main__":
    main()
