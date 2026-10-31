#!/usr/bin/env python3
"""Pull Adams County Building Permits (Accela Building module mirrored to ArcGIS Online,
"Eye On Adams") into the step 4 shared format. Non-residential permits only.

Usage:  python3 pull_adams_county_building_permits.py [--since YYYY-MM-DD] [--fresh]

--since  CaseOpened cursor (default 2024-01-01). The default run also carries in 2023 permits
         whose ApplicationStatus is still active. For an incremental run pass the last
         record_date already held and de-duplicate on record_id downstream.
--fresh  ignore today's raw cache and refetch.
Raw pages are cached under raw/adams_county_building_permits/<since>_<UTC day>/. The raw
pages hold every permit (residential included) so the residential count can be reported;
only non-residential rows reach the CSV.
"""
import argparse, os, re, shutil, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc_common as cc

LAYER = cc.ADAMS_HOST + "/Building_Permits_Eye_On_Adams/FeatureServer/0"
SLUG = "adams_county_building_permits"
SOURCE = "Adams County building permits"
OUT = os.path.join(cc.ADAMS_DIR, "scrape_%s.csv" % SLUG)

FIELDS = ["ObjectID", "RecordID_", "Subdivision", "Parcel_", "Description", "ApplicationStatus",
          "TypeOfWork", "ClassOfWork", "BuildingUse", "TotalSQFT", "CensusCode", "CaseOpened",
          "CombinedAddress", "X", "Y", "LinkToAccela"]

EXTRA_COLS = ["permit_type", "type_of_work", "class_of_work", "building_use", "census_code",
              "square_feet", "status", "subdivision", "parcel_number", "industrial_property",
              "latitude", "longitude", "accela_url", "parser_version"]

FINISHED = ("Case Finaled", "Case Closed", "Closed", "Closed, Approved", "C of O Issued", "CO Issued")
RES_USE = {"residential", "single family", "mobile home"}
RES_CENSUS = re.compile(r"^(0[1-5]|1[02]|3[346]) |accessory dwelling", re.I)
RES_WORK = {"single family dwelling", "accessory dwelling unit", "basement finish", "basement finished",
            "garage", "garage; attached", "garage; detached", "hot tub, spa", "swimming pool",
            "mobile home setup", "modular home", "multi family", "water heater", "water softener",
            "water treatment system", "reverse osmosis system", "siding", "fence", "furnace",
            "ac and furnace", "air cond.", "air conditioning", "floor heating", "radiant heating",
            "solar hydronic", "solar pv", "re roof", "sub panel", "subpanel - up to 200amps",
            "service change - up to 200 amps", "foundation stabilization"}
CONSTRUCTION_CLASS = {"new", "addition", "change in use", "alteration"}
CONSTRUCTION_WORK = {"tenant finish", "warehouse", "core & shell", "office", "other", ""}

# Name extraction from the free-text description. Conservative: only after a trigger phrase
# ("for", "tenant:", "owned by", "dba") take the run of capitalised tokens that follows, stop at the
# first lowercase word or punctuation, and drop generic first words. Nothing else is tried.
TRIGGER_RE = re.compile(r"\b(?:tenant finish for|tenant improvements? for|buildout for|build-out for|TI for|"
                        r"improvements for|for|tenant\s*(?:name)?\s*[:\-]|tenant|owned by|operated by|"
                        r"d/?b/?a|on behalf of|client[:\-]?)\s+", re.I)
TOKEN_RE = re.compile(r"([A-Z0-9][\w&'\.\-]*|&|of|and|de|la)(?=\s|$|[,.;:)\-])")
GENERIC_FIRST = {"new", "the", "existing", "project", "building", "bldg", "tenant", "suite", "ste", "unit",
                 "commercial", "industrial", "retail", "office", "warehouse", "fire", "site", "a", "an",
                 "this", "phase", "lot", "block", "service", "services", "install", "installation",
                 "installing", "replacement", "repair", "removal", "future", "proposed", "additional",
                 "inventory", "safety", "power", "storage", "parking", "use", "their", "our", "my",
                 "your", "his", "her", "each", "all", "two", "three", "one", "second", "first", "level",
                 "floor", "roof", "exterior", "interior", "electrical", "mechanical", "plumbing", "hvac",
                 "equipment", "work", "scope", "permit", "water", "gas", "sale", "sales", "lease", "rent",
                 "details", "detail", "info", "information", "review", "approval", "inspection", "non",
                 "customer", "customers", "employee", "employees", "staff", "public", "general", "more",
                 "hail", "vehicle", "vehicles", "bay", "bays", "space", "spaces", "area", "areas", "food",
                 "truck", "trucks", "truck", "reference", "ref", "see", "attached", "bdp", "mep", "ada",
                 "egress", "exit", "sprinkler", "sprinklers", "alarm", "sign", "signage", "lighting", "lights",
                 "solar", "pv", "ev", "cell", "tower", "antenna", "antennas", "monument", "wall", "pole",
                 "fuel", "diesel", "propane", "tank", "tanks", "cooler", "freezer", "kitchen", "restaurant",
                 "hood", "kiln", "boiler", "furnace", "rtu", "rtus", "unit", "units", "panel", "panels",
                 "meter", "meters", "pedestal", "generator", "pump", "well", "wells", "pad", "pads", "i", "we",
                 "it", "they", "he", "she", "you", "please", "note", "approx", "approximately", "add", "adding",
                 "remove", "removing", "replace", "replacing", "construct", "constructing", "building", "demo",
                 "demolition", "demolish", "temporary", "temp", "construction", "contractor", "owner", "tenants",
                 "finish", "improvement", "improvements", "spaced", "correction", "barn", "barns", "shelter",
                 "ag", "midway", "a-assembly", "railroad", "access",
                 "arena", "renovation", "aux", "hay", "like", "mua", "low", "high", "spray", "paint", "hazard",
                 "build-out", "buildout", "ti", "tenant-finish", "walk-in", "drive", "thru", "class", "classes",
                 "mixed", "medical", "dental", "office/warehouse", "warehouse/office", "shell", "core", "spec",
                 "first", "second", "third", "ground", "tilt", "tilt-up", "pre-engineered", "metal", "steel",
                 "wood", "concrete", "asphalt", "gravel", "dirt", "grass", "turf", "irrigation", "landscape",
                 "landscaping", "trees", "tree", "fence", "fencing", "gate", "gates", "door", "doors", "window",
                 "windows", "canopy", "awning", "shade", "structure", "structures", "foundation", "footing",
                 "footings", "slab", "pad", "caisson", "caissons", "pier", "piers", "beam", "beams", "column",
                 "columns", "truss", "trusses", "deck", "decking", "stair", "stairs", "ramp", "ramps", "dock",
                 "docks", "mezzanine", "rack", "racks", "racking", "conveyor", "conveyors", "crane", "cranes",
                 "hoist", "hoists", "lift", "lifts", "elevator", "elevators", "escalator", "escalators",
                 "residential", "residents", "apartment", "apartments", "home", "homes", "house", "houses"}
STOP_INSIDE = {"at", "in", "located", "on", "to", "with", "project", "building", "suite", "ste", "unit",
               "bldg", "which", "that", "who", "is", "are", "was", "will", "as", "by", "from", "per", "under"}


ABBREV = {"inc", "co", "corp", "ltd", "llc", "l.l.c", "lp", "l.p", "mfg", "intl", "assn", "bros"}


def extract_company(desc):
    text = desc.replace("\r", " ").replace("\n", " ")
    upper_share = sum(c.isupper() for c in text if c.isalpha()) / max(1, sum(c.isalpha() for c in text))
    for m in TRIGGER_RE.finditer(text):
        pos = m.end()
        toks, ended = [], False
        while True:
            t = TOKEN_RE.match(text, pos)
            if not t:
                break
            tok = t.group(1)
            if tok.lower() in STOP_INSIDE:
                break
            pos = t.end()
            nxt = text[pos:pos + 1]
            if tok.endswith(".") and tok[:-1].lower().strip(".") not in ABBREV:
                tok, ended = tok[:-1], True
            toks.append(tok)
            if ended or nxt in (",", ";", ":", ")", "-", "/", "#", "@") or len(toks) >= 6:
                break
            sp = re.match(r"\s+", text[pos:])
            if not sp:
                break
            pos += sp.end()
        while toks and toks[-1].lower() in ("of", "and", "&", "de", "la"):
            toks.pop()
        if not toks or toks[0].lower().strip(".") in GENERIC_FIRST or toks[0].lower() in ("&", "of", "and"):
            continue
        if not re.match(r"[A-Za-z]", toks[0]):
            continue
        if len(toks) == 1 and len(toks[0]) < 3:
            continue
        name = cc.clean(" ".join(toks)).strip(" -:.,")
        if upper_share > 0.7 and len(toks) > 3:
            continue   # all-caps descriptions: a run of capitals is not a name
        if re.fullmatch(r"[\d\W]+", name) or cc.looks_like_individual(name):
            continue
        return name[:120]
    return ""


RES_WORDS = re.compile(r"\b(single family|sfd|sfr|duplex|townhome|townhouse|residence|dwelling|house|home|"
                       r"homeowner|my property|our property|basement|bedroom|bathroom|kitchen|patio|deck|"
                       r"pergola|carport|hot tub|swimming pool|adu|egress window|water heater|furnace|"
                       r"a/c|ac unit|hvac replacement|reroof|re-roof|re roof|shingle|solar|pv system|"
                       r"fence|siding|windows?|doors?|mobile home|manufactured home|modular home|"
                       r"apartments?|multi ?family|condo\w*|kw|kwdc|kwac|modules?|photovoltaic|pv|"
                       r"roof[- ]?mount\w*|grid[- ]?tied|inverters?|stucco|james hardie|mpu|"
                       r"main panel upgrade|tankless|outbuilding|shed|garage|tesla|powerwall|"
                       r"battery|backup generator|generac|ev charger|evse|combi|btu|afue|navien|lochinvar|"
                       r"burnham|rinnai|like for like|like-for-like|soffit|fascia|sheathing|porch|"
                       r"porches|reside|resided|vinyl|hardie|smartside|squares|sq)\b", re.I)
STRONG_NONRES = re.compile(r"\b(warehouse|manufactur\w*|industrial|tenant|commercial|business|facility|"
                           r"plant|restaurant|store|retail|office|church|school|clinic|hotel|shop)\b", re.I)


def is_residential(use, work, census, desc):
    """Plainly residential by the county's own labels. Commercial and Industrial rows are kept
    unless they are multi-family housing, because the county applies residential census codes
    ("34 - Res. Add and Alter Only") to commercial work too."""
    u, w = use.lower(), work.lower()
    res_prefix = bool(re.match(r"^\s*RE(S)?\b", desc, re.I))
    if u in RES_USE:
        return True
    if u in ("commercial", "industrial"):
        return w == "multi family" or census.startswith(("04 ", "05 ", "33 "))
    if u in ("agricultural business", "agricultural"):
        return res_prefix or w in RES_WORK
    # blank use: the description, work type and census code have to carry it
    if res_prefix or w in RES_WORK or RES_CENSUS.match(census):
        return True
    if w == "multi family":
        return True
    if w in ("", "other", "re roof", "boiler") and RES_WORDS.search(desc) and not STRONG_NONRES.search(desc) \
            and not re.match(r"^\s*(COM|IND|CASP)\b", desc, re.I):
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    day = cc.now_iso()[:10].replace("-", "")
    cache = os.path.join(cc.RAW_ROOT, SLUG, "%s_%s" % (a.since, day))
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)

    where = "CaseOpened >= DATE '%s'" % a.since
    if a.since <= "2024-01-01":
        where = ("(%s) OR (CaseOpened >= DATE '2023-01-01' AND CaseOpened < DATE '%s' AND "
                 "ApplicationStatus NOT IN (%s))" % (where, a.since, ",".join("'%s'" % s for s in FINISHED)))

    cc.require_fields(LAYER, FIELDS)
    n_source = cc.source_count(LAYER, where)
    print("source count for filter:", n_source)
    feats = cc.fetch_all(LAYER, where, FIELDS, cache, page_size=2000, geometry=False, order="ObjectID")
    if len(feats) != n_source:
        raise SystemExit("ROW COUNT MISMATCH against source: %d fetched, %d expected" % (len(feats), n_source))

    rows, residential, rules = [], Counter(), Counter()
    for f in feats:
        at = f["attributes"]
        use = cc.clean(at.get("BuildingUse"))
        work = cc.clean(at.get("TypeOfWork"))
        klass = cc.clean(at.get("ClassOfWork"))
        census = cc.clean(at.get("CensusCode"))
        desc = cc.clean(at.get("Description"))
        if is_residential(use, work, census, desc):
            residential[use or "(blank use)"] += 1
            continue
        prefix = re.match(r"^\s*([A-Z]{2,4})\s*-", desc)
        prefix = prefix.group(1).upper() if prefix else ""
        industrial_prop = (use.lower() == "industrial" or prefix == "IND" or census.startswith("20 "))
        text = " ".join([desc, use, work])
        ind_word = bool(cc.INDUSTRIAL_WORDS.search(text)) or industrial_prop
        construction = (klass.lower() in CONSTRUCTION_CLASS and work.lower() in CONSTRUCTION_WORK) \
            or work.lower() in ("tenant finish", "warehouse", "core & shell")
        flag, rule = "N", ""
        if construction and ind_word:
            flag, rule = "Y", "tier A: non-residential construction with industrial word, no valuation in layer"
        elif industrial_prop:
            flag, rule = "Y", "tier B3b: industrial property, non-residential, no valuation in layer"
        rules[rule] += 1
        name = extract_company(desc)
        rid = cc.clean(at.get("RecordID_"))
        x, y = at.get("X"), at.get("Y")
        sqft = cc.clean(at.get("TotalSQFT"))
        rows.append({
            "source": SOURCE, "source_level": cc.SOURCE_LEVEL, "record_id": rid,
            "record_date": cc.ms_to_date(at.get("CaseOpened")), "date_type": "opened",
            "record_type": " / ".join(p for p in (work, klass) if p),
            "company_name": name, "company_role": "tenant" if name else "unknown",
            "site_address": cc.clean(at.get("CombinedAddress")),
            "city": "Unincorporated Adams County", "county": cc.COUNTY, "zip": "",
            "description": cc.clean(desc, 500), "flag": flag, "flag_rule": rule,
            "source_url": cc.layer_query_url(LAYER, "RecordID_='%s'" % rid),
            "retrieved_at": f["_fetched_at"],
            "permit_type": rid.split("-")[0][:3] if rid else "", "type_of_work": work,
            "class_of_work": klass, "building_use": use, "census_code": census,
            "square_feet": sqft if re.fullmatch(r"\d+", sqft or "") and sqft != "0" else "",
            "status": cc.clean(at.get("ApplicationStatus")), "subdivision": cc.clean(at.get("Subdivision")),
            "parcel_number": cc.clean(at.get("Parcel_")), "industrial_property": "Y" if industrial_prop else "N",
            "latitude": "%.6f" % y if y else "", "longitude": "%.6f" % x if x else "",
            "accela_url": cc.clean(at.get("LinkToAccela")), "parser_version": cc.PARSER_VERSION})
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    cc.write_csv(OUT, cc.COMMON_COLS + EXTRA_COLS, rows)
    print("rows written: %d of %d in the source filter" % (len(rows), n_source))
    print("residential rows left out: %d %s" % (sum(residential.values()), residential.most_common()))
    print("flag rules:", rules.most_common())
    print("company names extracted:", sum(1 for r in rows if r["company_name"]))


if __name__ == "__main__":
    main()
