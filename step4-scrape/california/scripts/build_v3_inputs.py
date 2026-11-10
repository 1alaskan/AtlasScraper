"""Reshape the California state pulls into the input files build_v3.py reads, for one county.

Usage: python3 build_v3_inputs.py <county name as in the data, e.g. Alameda> <slug, e.g. alameda> "<CITY 1|CITY 2|...>"
Writes step4-scrape/california/v3_inputs/<slug>/ :
  scrape_state_water_permits.csv   SMARTS industrial + construction rows, statewide, in the water-permit shape
  ca_incentive_awards.csv          California Competes and CAEATFA awards whose every named city is in the county (scored; two in-county cities are listed under the first)
  ca_incentive_awards_multisite.csv  awards that name the county and somewhere else (NOT read by the build; side list)
  header-only files for the Colorado sources that have no California counterpart yet (UCC, registrations, air, press, OEDIT)
Mapping (the points table is untouched):
  SMARTS Notice of Intent / No Exposure Certification -> record_type "CA IGP ..." / "CA NEC ..." -> water_new
  SMARTS Construction General Permit                    -> record_type "CA CGP ..."               -> water_construction, only when the row is
      marked industrial AND company-named (owner name carries a maker word, or the site name repeats a distinctive word of the owner name
      and the owner is not a developer, utility or public body). Everything else is cut by the build as "flagged on acreage alone".
"""
import csv, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); CA = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(CA, "..", "..", "step5-analysis", "v3", "scripts"))
os.environ.setdefault("V3_COUNTY", "denver")
import v3_config as C0
from v3_lib import SHARED, FILES, UCC, REG, AIR, CRE, OED, WAT
COUNTY, SLUG, CITIES = sys.argv[1], sys.argv[2], set(c.strip().upper() for c in sys.argv[3].split("|"))
OUT = os.path.join(CA, "v3_inputs", SLUG); os.makedirs(os.path.join(OUT, "scrape_ucc_filings"), exist_ok=True); os.makedirs(os.path.join(OUT, "scrape_business_registrations"), exist_ok=True)
DEV = re.compile(r"partners|properties|property|realty|real estate|development|developers|investors|investments?|holdings|capital|logistics|prologis|industrial (?:partners|owner|venture)|"
                 r"\bREIT\b|land co|city of|county|district|state of|university|caltrans|pacific gas|pg&e|edison|utility|utilities|school|college|authority|agency|department|"
                 r"construction|builders|contractors?|homes|housing|apartments|\bBART\b|port of|airport|national laborator|\bDOE\b|\bNNSA\b|sanitary|water", re.I)
STOP = set("THE AND INC LLC CORP COMPANY CO LTD LP OF CALIFORNIA USA US AMERICA NORTH SOUTH EAST WEST BAY AREA SITE PROJECT FACILITY PLANT PHASE BUILDING".split())

def rd(name):
    with open(os.path.join(CA, "scrape_%s.csv" % name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

WCOLS = SHARED + ["permittee", "sic_code", "other_sic_codes", "sic_description", "issued_date", "permit_status"]
rows, n = [], {"ind": 0, "con": 0, "con_named": 0, "skipped_blank_name": 0}
for r in rd("smarts_industrial"):
    if not r["company_name"].strip(): n["skipped_blank_name"] += 1; continue
    m = re.search(r"SIC (\d{4})-([^;]*)", r["description"])
    o = {c: r.get(c, "") for c in SHARED}
    o["record_type"] = ("CA NEC - No Exposure Certification" if "Exposure" in r["record_type"] else "CA IGP - Industrial General Permit Notice of Intent")
    o.update(permittee="", sic_code=r.get("primary_sic", ""), other_sic_codes="", sic_description=(m.group(2).strip() if m else ""), issued_date="", permit_status=r.get("status", ""))
    rows.append(o); n["ind"] += 1
for r in rd("smarts_construction"):
    if not r["company_name"].strip(): n["skipped_blank_name"] += 1; continue
    o = {c: r.get(c, "") for c in SHARED}
    o["record_type"] = "CA CGP - Construction General Permit"
    if r["flag"] == "Y":
        owner = r["company_name"]; site = (re.search(r"Site: ([^;]*)", r["description"]) or [None, ""])[1]
        ot = set(t for t in re.findall(r"[A-Z]{5,}", owner.upper()) if t not in STOP)
        named = bool(C0.FIT_STRONG.search(owner)) or (bool(ot & set(re.findall(r"[A-Z]{5,}", site.upper()))) and not DEV.search(owner))
        if named and not DEV.search(owner):
            o["flag_rule"] = r["flag_rule"] + "; company-named facility"; n["con_named"] += 1
    o.update(permittee="", sic_code="", other_sic_codes="", sic_description="", issued_date="", permit_status=r.get("status", ""))
    rows.append(o); n["con"] += 1
with open(os.path.join(OUT, FILES[WAT]), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, WCOLS); w.writeheader(); w.writerows(rows)

ICOLS = SHARED + ["phase_1_cap"]
single, multi = [], []
for name, label in (("calcompetes_awards", "California Competes"), ("caeatfa_ste_awards", "CAEATFA")):
    for r in rd(name):
        if r["flag"] != "Y": continue
        parts = [p.strip() for p in re.split(r";|,| and ", r["city"]) if p.strip()]
        inside = [p for p in parts if p.upper() in CITIES]
        if not inside: continue
        o = {c: r.get(c, "") for c in SHARED}; o["phase_1_cap"] = ""
        o["record_type"] = label + " award"
        if len(inside) == len(parts):
            if len(set(p.upper() for p in parts)) > 1:
                o["description"] = ("[award names %s, all in %s County; listed under the first] " % (" and ".join(parts), COUNTY) + o["description"])[:500]
            o["county"] = COUNTY; o["city"] = parts[0]; single.append(o)
        else:
            o["county"] = COUNTY if len(inside) == len(parts) else ""; multi.append(o)
for fn, data in (("ca_incentive_awards.csv", single), ("ca_incentive_awards_multisite.csv", multi)):
    with open(os.path.join(OUT, fn), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ICOLS); w.writeheader(); w.writerows(data)
for src, cols in ((UCC, ["flag_v2"]), (REG, ["flag_v2"]), (AIR, ["flag"]), (CRE, ["flag"]), (OED, ["flag"])):
    with open(os.path.join(OUT, FILES[src]), "w", newline="", encoding="utf-8") as f:
        f.write(",".join(SHARED + cols) + "\n")
print(n, "awards scored", len(single), "multi-site side list", len(multi))
for o in single + multi: print("  ", "S" if o in single else "M", o["record_date"], o["company_name"], "|", o["city"])
