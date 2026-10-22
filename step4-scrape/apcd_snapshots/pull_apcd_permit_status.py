#!/usr/bin/env python3
"""
pull_apcd_permit_status.py  (parser version 1.0, Step 4)

Pulls the Colorado APCD air permit status feed and writes
scrape_apcd_permit_status.csv in the shared Step 4 format.

Source page : https://apcdweb.dphe.state.co.us/PermitStatus/
JSON feed   : https://apcdweb.dphe.state.co.us/PermitStatusAPI/api/vResultsAPIs

Usage
  python3 -I pull_apcd_permit_status.py            # parse newest raw file in ./raw, no network
  python3 -I pull_apcd_permit_status.py --fetch    # one GET (one retry after a pause), save raw, parse
  python3 -I pull_apcd_permit_status.py --raw raw/permit_status_raw_<ts>.json

The feed is one unpaged GET of the whole table, so there is no cursor.
"Resumable" here means: every fetch is saved as a timestamped raw file and
parsing always runs from a local raw file. The feed only holds applications
processed in the last six months, so each saved raw file is a snapshot;
keep them to build history.

Personal data: the engineer name, email and phone fields are never written
to the CSV. They remain only in the raw JSON cache.
"""
import argparse
import csv
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "raw")
OUT_CSV = os.path.join(HERE, "scrape_apcd_permit_status.csv")
FEED_URL = "https://apcdweb.dphe.state.co.us/PermitStatusAPI/api/vResultsAPIs"
PAGE_URL = "https://apcdweb.dphe.state.co.us/PermitStatus/"
USER_AGENT = "step4-research-pull/1.0"
PARSER_VERSION = "1.0"
SCOPE_START = "2024-01-01"

EXPECTED_KEYS = {
    "company", "facility", "source", "permit", "serviceType", "permitIssuedOn",
    "engineer", "engineerEmail", "engineerPhone", "SER_TYPE", "PLA_ID", "Status",
    "Received", "Address_ID", "Own_ID", "PER_ID", "POI_ID",
}
DROP_KEYS = {"engineer", "engineerEmail", "engineerPhone"}  # staff contact fields

COLUMNS = [
    "source", "source_level", "record_id", "record_date", "date_type", "record_type",
    "company_name", "company_role", "site_address", "city", "county", "zip",
    "description", "flag", "flag_rule", "source_url", "retrieved_at",
    # extras
    "facility_name", "facility_raw", "facility_parse", "permit_number", "airs_id",
    "service_type_code", "permit_issued_on", "in_date_scope", "sector", "sector_rule",
    "PER_ID", "POI_ID", "PLA_ID", "Address_ID", "Own_ID", "parser_version",
]

# --------------------------------------------------------------------------
# Sector rule. Order: oil and gas operator name, fuel retail, oil and gas
# keyword, aggregate/concrete/asphalt, other.
# --------------------------------------------------------------------------

# Oil and gas operators, midstream and oilfield service companies observed in
# the feed on 2026-10-10 (matched as a prefix-free substring of the company).
OG_OPERATORS = [
    "1876 RESOURCES", "AMERICAN CEMENTING", "ANSCHUTZ EXPLORATION",
    "BARGATH", "BAYSWATER", "BEEMAN OIL", "BISON IV", "BISON OIL", "BNL (ENTERPRISE)",
    "BONANZA CREEK", "CHACO ENERGY", "CHEVRON", "CITATION OIL", "CIVITAS",
    "COLORADO INTERSTATE GAS", "COVALENCE DJ", "CRESTONE", "D90 ENERGY", "DCP OPERATING",
    "DESERT EAGLE OPERATING", "DIVIDE CREEK GATHERING", "DUNAMIS ENERGY",
    "ELEVATION MIDSTREAM", "ENTERPRISE GAS PROCESSING", "ET CRUDE TERMINALS",
    "EVERGREEN NATURAL RESOURCES", "EXTRACTION OIL", "FULCRUM ENERGY OPERATING",
    "FUNDARE", "GRAND MESA OPERATING", "GREEN NATURAL GAS VENTURES", "HALLIBURTON", "HIGHPOINT OPERATING", "HILCORP",
    "IMPETRO", "JOEMAR", "K.P. KAUFFMAN", "KERR-MCGEE", "KT RESOURCES", "KTM OPERATING",
    "LARAMIE ENERGY", "MAGPIE OPERATING", "MOONRISE MIDSTREAM", "MOUNTAINWEST PIPELINE",
    "MULTI-CHEM", "NGL CRUDE", "NGL WATER SOLUTIONS", "NOBLE ENERGY", "NORTH FORK ENERGY", "NUSTAR LOGISTICS",
    "OGRIS OPERATING", "ONEOK", "OVERLAND PASS PIPELINE", "OWN RESOURCES", "P.O.&G.",
    "PDC ENERGY", "PLAINS MARKETING", "PLATTE RIVER MIDSTREAM", "POLARIS PRODUCTION",
    "PRAIRIE OPERATING", "PRODUCED WATER RECYCLE", "QB ENERGY", "RAMPIKE RESOURCES",
    "RENEGADE OIL", "REP PROCESSING", "ROCKIES EXPRESS PIPELINE", "ROCKY MOUNTAIN MIDSTREAM",
    "ROCKY MOUNTAIN NATURAL GAS", "SCOUT ENERGY", "SELECT WATER SOLUTIONS",
    "SHELDON KYE ENERGY", "SILVER MOUNTAIN ENERGY", "SIMCOE", "SPELLBOUND ENERGY",
    "STRACHAN EXPLORATION", "SUMMIT DJ", "SUMMIT MIDSTREAM", "SUNCOR ENERGY",
    "SUPERIOR OILFIELD", "TALLGRASS", "TEP ROCKY MOUNTAIN", "TRANSCOLORADO GAS",
    "TUMBLEWEED MIDSTREAM", "TWIN EAGLE TERMINALS", "UGC MIDSTREAM", "UTAH GAS",
    "VERDAD RESOURCES", "WES DJ", "WES WATTENBERG", "WESTERN OPERATING", "WEXPRO",
    "WIEPKING-FULLERTON", "WILLIAMS FIELD SERVICES", "WILLIAMS FRONT RANGE",
    "WILLIAMS GILCREST", "ZEN MIDSTREAM",
]

# Fuel retail and bulk fuel distribution companies observed in the feed.
FUEL_RETAIL_COMPANIES = [
    "7-ELEVEN", "APRO, LLC", "UNITED PACIFIC", "BUC-EE", "BYERS PETROLEUM", "CIRCLE K",
    "CST METRO", "FEATHER PETROLEUM", "GPM SOUTHEAST", "KUM & GO", "LOVE'S TRAVEL",
    "MAVERIK", "MINI MART", "MURPHY OIL USA", "QUIKTRIP", "RHINEHART OIL", "SEELEY OIL",
    "STINKER STORES", "STUB'S GAS", "SUNOCO RETAIL", "VALLEY FUEL", "FARM GAS",
    "POLAR SERVICE CENTERS", "ELLA'S DISCOUNT MART",
]
FUEL_RETAIL_KW = re.compile(
    r"\b(FUEL(ING)? STATIONS?|GAS STATIONS?|SERVICE STATIONS?|GASOLINE DISPENS\w*|GDF|"
    r"GASOLINE STATIONS?|FUEL CENTERS?|FUEL STOP|TRAVEL (STOP|CENTER|PLAZA)|TRUCK STOP|"
    r"CONVENIENCE STORE|C-STORE|UNLEADED|RETAIL (FUEL|GASOLINE)|FUEL DISPENS\w*|"
    r"GASOLINE (UST|AST|STORAGE|TANK)S?|(UST|AST)S? ?[-:]? ?GASOLINE|MOTOR VEHICLE FUEL\w*|"
    r"VEHICLE FUELING|FUEL ISLAND|FUEL FACILITY|FUEL KIOSK|USTS?|BULK FUEL|REFINED FUEL|"
    r"PETROL\w+ PRODUCTS BULK)\b"
)

# Not oil and gas even though the text says "gas": renewable natural gas,
# biogas, landfill gas, helium, industrial gases.
OG_EXCLUDE = re.compile(
    r"\b(RNG|RENEWABLE NATURAL GAS|BIOGAS|BIO-GAS|DIGESTER|LANDFILL|HELIUM|DAIRY)\b"
)

OG_KW = re.compile(
    r"\b(WELL ?PADS?|WELL ?HEADS?|WELL ?SITES?|WELL PRODUCTION|OIL (&|AND) GAS|OIL/GAS|O&G|OILFIELD|"
    r"OIL FIELD|GAS (PROCESSING )?PLANT|NATURAL GAS (PROCESSING|COMPRESS\w*|GATHERING|TREATING|"
    r"PRODUCTION|TRANSMISSION|LIQUIDS|DEHY\w*|BOOSTER|STORAGE FIELD)|COMPRESSOR STATIONS?|"
    r"COMP\.? STA(TION)?|C\.?S\.?$|BOOSTER STATION|MIDSTREAM|GATHERING|PIPELINE|"
    r"TANK BATTER(Y|IES)|E&P|E & P|EXPLORATION|"
    r"CRUDE|CONDENSATE|PRODUCED WATER|PUMP ?JACKS?|PUMPING UNITS?|"
    r"GLYCOL|DEHYDRAT\w+|DEHY|TEG|ENCLOSED COMBUST\w+|ECD|WELLS?|CPF|CENTRAL PRODUCTION|"
    r"HYDROCARBON (LIQUID )?LOAD ?OUT|LACT|FRAC\w*|FLOWBACK|PIGGING|PIG (LAUNCHER|RECEIVER)|"
    r"AMINE|NGL|VAPOR RECOVERY (UNIT|TOWER)|VRU|VRT|PNEUMATIC (CONTROLLER|PUMP)S?|"
    r"SALT ?WATER DISPOSAL|SWD|WATER DISPOSAL|INJECTION (FACILITY|WELL)|"
    r"DRILLING|COMPLETIONS?|REFINERY|GAS LIFT|LIFT GAS|"
    r"OIL (STORAGE )?TANKS?|OIL TERMINAL|OIL COMPLEX)\b"
)

AGG_COMPANIES = [
    "ASPHALT", "AGGREGATE", "GRAVEL", "READY MIX", "READY-MIX", "READYMIX", "REDI-MIX",
    "REDIMIX", "CONCRETE", "CRUSHING", "PAVING", "QUARR", "MATERIALS", "CEMENT", "CEMEX",
    "HOLCIM", "AMRIZE", "MARTIN MARIETTA", "OLDCASTLE", "BURNCO", "SUNROC", "PETE LIEN",
    "ALBERT FREI", "L. G. EVERIST", "KILGORE COMPANIES", "CONNELL RESOURCES",
    "ELAM CONSTRUCTION", "COULSON EXCAVATING", "MCATEE CONSTRUCTION", "W.W. CLYDE",
    "SCHMIDT CONSTRUCTION", "KELLEY TRUCKING", "KELLEY CONTRACTING", "ROCK & RAIL",
    "ROCK TRAN", "QUIKRETE", "US MIX", "SAND COMPANY", "SAND, LLC", "PROPPANTS",
    "LINDSAY PRECAST", "FORTERRA", "ROCLA", "ARCOSA", "CO SAND", "GCC ", "LYMAN-RICHEY",
    "HOLLIDAY ROCK", "GLACIER ROCK", "COLORADO LAVA", "POZZOLAN", "BV MINING",
    "MILL IRON MINING", "A-1 CHIPSEAL", "ROAD & BRIDGE", "SOUTHWAY CONSTRUCTION",
    "SCHOFIELD EXCAVATION", "FLASHFILL",
]
# company names that contain an aggregate word but are manufacturers
AGG_NOT = ["FUJIFILM", "OWENS CORNING", "MILL ROCK PACKAGING"]
AGG_KW = re.compile(
    r"\b(ASPHALT|HMA|HOT MIX|CONCRETE|BATCH PLANTS?|READY ?-?MIX|REDI-?MIX|CRUSH\w*|SCREENS?|"
    r"SCREENING|AGGREGATES?|GRAVEL|SAND (AND|&) GRAVEL|QUARR(Y|IES)|PITS?|PUG ?MILL|"
    r"WASH PLANT|CEMENT|ROCK (PIT|QUARRY|PLANT)|PRECAST|SAND MINE|FRAC SAND|MINERAL PROCESSING)\b"
)


def norm(s):
    return re.sub(r"\s+", " ", (s or "").replace("\r", " ").replace("\n", " ")).strip()


def classify(company, facility_name, source_text):
    """Return (sector, rule_that_fired)."""
    co = norm(company).upper()
    fac = norm(facility_name).upper()
    src = norm(source_text).upper()
    text = " | ".join([co, fac, src])
    for op in OG_OPERATORS:
        if op in co:
            return "oil_and_gas", "operator name: " + op
    for fr in FUEL_RETAIL_COMPANIES:
        if fr in co:
            return "fuel_retail", "fuel retailer name: " + fr
    m = FUEL_RETAIL_KW.search(text)
    if m:
        return "fuel_retail", "keyword: " + m.group(0)
    if not OG_EXCLUDE.search(text):
        m = OG_KW.search(text)
        if m:
            # aggregate companies own "pits" and "wells" rarely; let company-level
            # aggregate names win over weak single-word hits
            weak = m.group(0) in ("WELLS", "WELL", "COMPLETION", "COMPLETIONS", "PIPELINE", "EXPLORATION", "GATHERING",
                                  "DRILLING", "AMINE", "FRAC", "DEHY", "TEG", "LACT", "ECD",
                                  "CPF", "VRU", "VRT", "NGL", "SWD", "CRUDE", "CONDENSATE",
                                  "GLYCOL")
            if not (weak and any(a in co for a in AGG_COMPANIES)):
                return "oil_and_gas", "keyword: " + m.group(0)
    for a in AGG_COMPANIES:
        if a in co and not any(x in co for x in AGG_NOT):
            return "aggregate_concrete_asphalt", "company name: " + a.strip()
    m = AGG_KW.search(fac + " | " + src)
    if m and not any(x in co for x in AGG_NOT):
        return "aggregate_concrete_asphalt", "keyword: " + m.group(0)
    return "other", ""


# --------------------------------------------------------------------------
# Facility string: "<name>, <address>, <COUNTY>, COLORADO, <zip>"
# Name and address can each contain commas. The name is at most 40 characters
# in the source system (padded or cut to 40 on many rows).
# --------------------------------------------------------------------------
ADDR_START = re.compile(
    r"^(\d+[A-Z]?\s+[A-Z0-9#]|\d+\s*$|-?\d{2,3}\.\d+|LATLON|LAT\b|N ?\d{2}\.\d+|"
    r"SEC(TION|T)?\.?\s*\d|S\d+\b|[NS][EW]/?4?\b|[NS][EW][NS][EW]\b|[NSEW]/2|LOT \d|T\d+[NS]\b|"
    r"P\.?O\.? BOX|HWY|HIGHWAY|I-\d+|US \d+|CR \d+|COUNTY ROAD|WCR|MILE|MM \d|INTERSECTION|"
    r"\d+\s*(DEG|°))", re.I)
NON_COUNTY = ("PORTABLE SOURCE", "PORT. IN STORAGE", "OUT-OF-STATE", "INDIAN LANDS")


def parse_facility(raw):
    """Return dict(facility_name, site_address, county, zip, parse) from the packed string."""
    out = {"facility_name": "", "site_address": "", "county": "", "zip": "", "parse": "blank"}
    if raw is None or not raw.strip():
        return out
    parts = raw.split(", ")
    if len(parts) < 4:
        out["parse"] = "unparsed"
        return out
    zip_raw = parts[-1].strip()
    state = parts[-2].strip().upper()
    county = parts[-3].strip()
    head = parts[:-3]
    if state != "COLORADO":
        # The address on these rows is an out-of-state company mailing address,
        # not the site. Keep the facility name only; raw string stays in facility_raw.
        out["facility_name"] = norm(head[0]) if head else ""
        out["parse"] = "out_of_state_mailing_address"
        return out
    z = zip_raw.rstrip("-").strip()
    if re.fullmatch(r"\d{5}(-\d{4})?", z) and not z.startswith("00000"):
        out["zip"] = z
    c = re.sub(r"\s*\(L\.D\.\)$", "", county, flags=re.I)  # (L.D.) = land development row
    out["county"] = "" if c.upper() in NON_COUNTY else c.title()
    if len(head) == 2:
        name, addr, how = head[0], head[1], "clean"
    elif len(head) == 1:
        name, addr, how = head[0], "", "no_address"
    else:
        # more than one candidate split: choose where name ends
        cands = []
        for i in range(1, len(head)):
            name_raw = ", ".join(head[:i])
            addr_raw = ", ".join(head[i:])
            cands.append((i, name_raw, addr_raw))
        pick = None
        # 1. name padded/cut to exactly 40 characters
        for i, n, a in cands:
            if len(n) == 40:
                pick = (n, a, "resolved_40char")
                break
        # 2. earliest split with a name <= 40 chars whose remainder starts like an address
        if pick is None:
            for i, n, a in cands:
                if len(n) <= 40 and ADDR_START.match(a.strip()) and not re.fullmatch(
                        r"[\d\- ]+", head[i].strip()) :
                    pick = (n, a, "resolved_addr_pattern")
                    break
        # 2b. lat/long pair as the last two pieces
        if pick is None and len(head) >= 3 and re.fullmatch(r"-?\d+\.\d+", head[-1].strip()) \
                and re.search(r"-?\d+\.\d+$", head[-2].strip()):
            pick = (", ".join(head[:-2]), ", ".join(head[-2:]), "resolved_latlon")
        # 3. latest split that keeps the name within 40 characters
        if pick is None:
            for i, n, a in reversed(cands):
                if len(n) <= 40:
                    pick = (n, a, "resolved_last_comma")
                    break
        # 4. fall back: first comma
        if pick is None:
            pick = (head[0], ", ".join(head[1:]), "ambiguous_first_comma")
        name, addr, how = pick
    out["facility_name"] = norm(name)
    out["site_address"] = norm(addr)
    out["parse"] = how
    return out


def iso_date(v):
    if not v:
        return ""
    return dt.datetime.fromisoformat(v).date().isoformat()


def fetch():
    """One GET, one retry after a pause, then stop. Uses curl so the proxy settings apply."""
    os.makedirs(RAW_DIR, exist_ok=True)
    for attempt in (1, 2):
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = os.path.join(RAW_DIR, "permit_status_raw_%s.json" % ts)
        r = subprocess.run(
            ["curl", "-sS", "-A", USER_AGENT, "-o", path, "-w", "%{http_code}", FEED_URL],
            capture_output=True, text=True)
        ok = r.returncode == 0 and r.stdout.strip() == "200"
        if ok:
            try:
                json.load(open(path, encoding="utf-8"))
                return path
            except ValueError:
                ok = False
        if os.path.exists(path):
            os.remove(path)
        if attempt == 1:
            print("fetch failed (%s %s); one retry in 30 s" % (r.stdout, r.stderr.strip()),
                  file=sys.stderr)
            time.sleep(30)
    sys.exit("fetch failed twice; stopping")


def raw_timestamp(path):
    m = re.search(r"(\d{8}T\d{6}Z)", os.path.basename(path))
    if not m:
        sys.exit("raw filename carries no UTC timestamp: " + path)
    t = dt.datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ")
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def build(raw_path):
    data = json.load(open(raw_path, encoding="utf-8"))
    if not isinstance(data, list) or not data:
        sys.exit("schema drift: feed is not a non-empty list")
    keys = set().union(*(r.keys() for r in data))
    if keys != EXPECTED_KEYS:
        sys.exit("schema drift: missing %s, new %s" % (
            sorted(EXPECTED_KEYS - keys), sorted(keys - EXPECTED_KEYS)))
    retrieved = raw_timestamp(raw_path)
    rows = []
    for r in data:
        for k in DROP_KEYS:
            r.pop(k, None)
        fac = parse_facility(r["facility"])
        src = norm(r["source"])
        m = re.search(r"AIRS#\s*([0-9A-Z]{3}-[0-9A-Z]{4})", src)
        airs = m.group(1) if m else ""
        desc = re.sub(r",?\s*AIRS#\s*[0-9A-Z\-]*\s*\]$", "", src)
        desc = norm(re.sub(r"^\[\s*", "", desc).rstrip("] "))
        rec = iso_date(r["Received"])
        sector, srule = classify(r["company"], fac["facility_name"] or norm(r["facility"]), desc)
        flag = "N" if sector == "oil_and_gas" else "Y"
        rows.append({
            "source": "APCD air permit status",
            "source_level": "State (Colorado)",
            "record_id": "%s-%s-%s" % (r["PER_ID"], r["POI_ID"], r["PLA_ID"]),
            "record_date": rec,
            "date_type": "received",
            "record_type": norm(r["serviceType"]),
            "company_name": norm(r["company"]),
            "company_role": "applicant",
            "site_address": fac["site_address"],
            "city": "",
            "county": fac["county"],
            "zip": fac["zip"],
            "description": desc[:500],
            "flag": flag,
            "flag_rule": "not oil and gas" if flag == "Y" else "",
            "source_url": PAGE_URL,
            "retrieved_at": retrieved,
            "facility_name": fac["facility_name"],
            "facility_raw": norm(r["facility"]),
            "facility_parse": fac["parse"],
            "permit_number": norm(r["permit"]),
            "airs_id": airs,
            "service_type_code": norm(r["SER_TYPE"]),
            "permit_issued_on": iso_date(r["permitIssuedOn"]),
            "in_date_scope": "Y" if rec >= SCOPE_START else "N",
            "sector": sector,
            "sector_rule": srule,
            "PER_ID": r["PER_ID"], "POI_ID": r["POI_ID"], "PLA_ID": r["PLA_ID"],
            "Address_ID": r["Address_ID"], "Own_ID": r["Own_ID"],
            "parser_version": PARSER_VERSION,
        })
    rows.sort(key=lambda x: (x["record_date"], x["record_id"]))
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
    print("feed rows %d, csv rows %d -> %s" % (len(data), len(rows), OUT_CSV))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="fetch a fresh copy of the feed")
    ap.add_argument("--raw", help="parse this raw file instead of the newest one")
    a = ap.parse_args()
    if a.fetch:
        raw = fetch()
    elif a.raw:
        raw = a.raw
    else:
        files = sorted(glob.glob(os.path.join(RAW_DIR, "permit_status_raw_*.json")))
        if not files:
            sys.exit("no raw file in %s; run with --fetch" % RAW_DIR)
        raw = files[-1]
    print("parsing", raw)
    build(raw)


if __name__ == "__main__":
    main()
