#!/usr/bin/env python3
"""Step 4 pull: Colorado CDPHE WQCD permits spreadsheet -> scrape_state_water_permits.csv

Source page : https://cdphe.colorado.gov/clean-water-active-permits  ("This xls file ... (as of 08/07/26)")
Sheet       : https://docs.google.com/spreadsheets/d/1ZFnnmKQc6zCeiYLcEOcf43cnYb7nwA2Y
Route       : one bulk XLSX export (single request). No paging, no API.

Run (always with -I, the download is untrusted data):
    python3 -I pull_state_water_permits.py            # reuse cached download
    python3 -I pull_state_water_permits.py --refresh  # fetch a new copy first (one request)
    python3 -I pull_state_water_permits.py --since 2026-08-01   # incremental date cursor

Parser version is written to qa_state_water_permits.json. The script fails loudly if
the header row drifts from the columns it expects.
"""
import argparse, collections, csv, datetime as dt, hashlib, json, os, re, subprocess, sys

PARSER_VERSION = "1.1"
SHEET_ID = "1ZFnnmKQc6zCeiYLcEOcf43cnYb7nwA2Y"
EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
VIEW_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
USER_AGENT = "step4-research-pull/1.0"
SOURCE = "State water permits (WQCD)"
SOURCE_LEVEL = "State (Colorado)"
SNAPSHOT_AS_OF = "2026-08-07"   # stated on the CDPHE page; cross-checked against max IssuedDate
HERE = os.path.dirname(os.path.abspath(__file__))
DL_DIR = os.path.join(HERE, "download")
XLSX = os.path.join(DL_DIR, "wqcd_active_permits.xlsx")
META = os.path.join(DL_DIR, "fetch_meta.json")
OUT = os.path.join(HERE, "scrape_state_water_permits.csv")
QA = os.path.join(HERE, "qa_state_water_permits.json")

BASE_COLS = ["source", "source_level", "record_id", "record_date", "date_type", "record_type",
             "company_name", "company_role", "site_address", "city", "county", "zip",
             "description", "flag", "flag_rule", "source_url", "retrieved_at"]
EXTRA_COLS = ["permittee", "owner", "operator", "former_permittee", "company_name_basis",
              "permit_sector", "disturbed_acres", "total_acres", "construction_activity",
              "sic_code", "sic_description", "other_sic_codes", "activity_description",
              "permit_status", "issued_date", "effective_date", "expiration_date",
              "termination_date", "construction_start_date", "construction_end_date",
              "receiving_water", "stream_segment", "associated_potw", "previous_permit_id",
              "major_minor", "date_basis", "scope_basis", "latitude", "longitude", "snapshot_as_of"]

# Columns read from the sheet. The legal-contact name columns are read ONLY to test
# whether the permittee is the contact person (private individual); never written.
NEEDED = ["PermitSector", "GeneralPermitType", "PermitID", "PermitStatus", "ApplicationReceivedDate",
          "IssuedDate", "EffectiveDate", "ExpirationDate", "TerminationDate", "Permittee",
          "LegalFName", "LegalLName", "PropertyOwnerFName", "PropertyOwnerLName",
          "OperatorFName", "OperatorLName", "FormerPermittee", "FacilityName", "FacilityAddress1",
          "FacilityAddress2", "FacilityCity", "FacilityState", "FacilityZip", "FacilityCounty",
          "FacilityLatitude", "FacilityLongitude", "FacilitySICCode", "ReceivingWater",
          "StreamSegment", "SWConstructionActivity", "SWConstructionTotalAcres",
          "SWConstructionDisturbedAcres", "SWConstructionStartDate", "SWConstructionEndDate",
          "PermitSIC1", "PermitSIC2", "PermitSIC3", "PermitSIC4", "ActivityDescription",
          "AssociatedPOTW", "PreviousPermitID", "PropertyOwnerOrganization",
          "OperatorOrganization", "MajorMinor"]

CO_COUNTIES = ["Adams", "Alamosa", "Arapahoe", "Archuleta", "Baca", "Bent", "Boulder", "Broomfield",
    "Chaffee", "Cheyenne", "Clear Creek", "Conejos", "Costilla", "Crowley", "Custer", "Delta", "Denver",
    "Dolores", "Douglas", "Eagle", "El Paso", "Elbert", "Fremont", "Garfield", "Gilpin", "Grand",
    "Gunnison", "Hinsdale", "Huerfano", "Jackson", "Jefferson", "Kiowa", "Kit Carson", "La Plata",
    "Lake", "Larimer", "Las Animas", "Lincoln", "Logan", "Mesa", "Mineral", "Moffat", "Montezuma",
    "Montrose", "Morgan", "Otero", "Ouray", "Park", "Phillips", "Pitkin", "Prowers", "Pueblo",
    "Rio Blanco", "Rio Grande", "Routt", "Saguache", "San Juan", "San Miguel", "Sedgwick", "Summit",
    "Teller", "Washington", "Weld", "Yuma"]
COUNTY_LOOKUP = {c.lower(): c for c in CO_COUNTIES}
COUNTY_LOOKUP["statewide"] = "Statewide"

# SIC description is NOT in the sheet. Derived from the standard SIC 2-digit major group title.
SIC_MAJOR = {
 "01": "Agricultural production, crops", "02": "Agricultural production, livestock", "07": "Agricultural services",
 "08": "Forestry", "09": "Fishing, hunting and trapping", "10": "Metal mining", "12": "Coal mining",
 "13": "Oil and gas extraction", "14": "Nonmetallic minerals mining, except fuels",
 "15": "General building contractors", "16": "Heavy construction, except building",
 "17": "Special trade contractors", "20": "Food and kindred products", "21": "Tobacco products",
 "22": "Textile mill products", "23": "Apparel and other textile products", "24": "Lumber and wood products",
 "25": "Furniture and fixtures", "26": "Paper and allied products", "27": "Printing and publishing",
 "28": "Chemicals and allied products", "29": "Petroleum and coal products",
 "30": "Rubber and miscellaneous plastics products", "31": "Leather and leather products",
 "32": "Stone, clay, glass and concrete products", "33": "Primary metal industries",
 "34": "Fabricated metal products", "35": "Industrial machinery and equipment",
 "36": "Electronic and other electric equipment", "37": "Transportation equipment",
 "38": "Instruments and related products", "39": "Miscellaneous manufacturing industries",
 "40": "Railroad transportation", "41": "Local and interurban passenger transit",
 "42": "Trucking and warehousing", "43": "U.S. Postal Service", "44": "Water transportation",
 "45": "Transportation by air", "46": "Pipelines, except natural gas", "47": "Transportation services",
 "48": "Communications", "49": "Electric, gas and sanitary services",
 "50": "Wholesale trade, durable goods", "51": "Wholesale trade, nondurable goods",
 "52": "Building materials and garden supplies", "53": "General merchandise stores", "54": "Food stores",
 "55": "Automotive dealers and service stations", "56": "Apparel and accessory stores",
 "57": "Furniture and homefurnishings stores", "58": "Eating and drinking places", "59": "Miscellaneous retail",
 "60": "Depository institutions", "61": "Nondepository institutions", "62": "Security and commodity brokers",
 "63": "Insurance carriers", "64": "Insurance agents, brokers and service", "65": "Real estate",
 "67": "Holding and other investment offices", "70": "Hotels and other lodging places",
 "72": "Personal services", "73": "Business services", "75": "Auto repair, services and parking",
 "76": "Miscellaneous repair services", "78": "Motion pictures", "79": "Amusement and recreation services",
 "80": "Health services", "81": "Legal services", "82": "Educational services", "83": "Social services",
 "84": "Museums, botanical and zoological gardens", "86": "Membership organizations",
 "87": "Engineering and management services", "88": "Private households", "89": "Services, not elsewhere classified",
 "91": "Executive, legislative and general government", "92": "Justice, public order and safety",
 "93": "Finance, taxation and monetary policy", "94": "Administration of human resources",
 "95": "Environmental quality and housing", "96": "Administration of economic programs",
 "97": "National security and international affairs", "99": "Nonclassifiable establishments",
}

# ---- flag rule 3 word lists (final lists, also stated in the source card) ----
COMPANY_WORDS = ["Inc", "LLC", "Corp", "Corporation", "Co.", "Company", "Manufacturing", "Mfg", "Plant",
    "Facility", "Factory", "Brewery", "Brewing", "Distillery", "Foods", "Dairy", "Bottling",
    "Industries", "Industrial", "Technologies", "Aerospace", "Semiconductor", "Pharma", "Mill",
    "Foundry", "Fabrication", "Steel", "Precast", "Energy", "Solar", "Battery", "Data Center",
    "Distribution Center", "Warehouse", "Logistics", "Laboratories"]
EXCLUDE_WORDS = ["subdivision", "subdivisions", "filing", "homes", "residences", "residence",
    "apartments", "apartment", "townhomes", "townhome", "estates", "ranch", "village", "road",
    "street", "highway", "interstate", "bridge", "pipeline", "waterline", "sewer", "school",
    "church", "park", "trail"]

ACRE_SKIP_TAGS = {"residential", "pipeline", "highway", "nonstructural"}


def _wre(word):
    if word == "Co.":
        # "Co." with the period (any case), or a bare mixed-case "Co" as the last word.
        return None
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(word).replace(r"\ ", r"\s+") + r"(?![A-Za-z0-9])", re.I)
COMPANY_RES = [(w, _wre(w)) for w in COMPANY_WORDS if w != "Co."]
CO_DOT_RE = re.compile(r"(?<![A-Za-z0-9])co\.(?![A-Za-z0-9])", re.I)
CO_END_RE = re.compile(r"(?<![A-Za-z0-9])Co$")           # case-sensitive: avoids state code "CO"
EXCLUDE_RES = [(w, _wre(w)) for w in EXCLUDE_WORDS]

def company_named(name):
    """Return (bool, matched company words, matched exclusion words)."""
    if not name:
        return False, [], []
    hits = [w for w, rx in COMPANY_RES if rx.search(name)]
    if CO_DOT_RE.search(name) or CO_END_RE.search(name.strip()):
        hits.append("Co.")
    excl = [w for w, rx in EXCLUDE_RES if rx.search(name)]
    return (bool(hits) and not excl), hits, excl

# ---- field cleaners ----
WS = re.compile(r"\s+")
def txt(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, (dt.datetime, dt.date, dt.time)):
        return ""
    s = WS.sub(" ", str(v)).strip()
    return "" if s in ("#N/A", "#VALUE!", "#REF!") else s

EXCEL_EPOCH = dt.datetime(1899, 12, 30)
def to_date(v):
    """datetime, Excel serial number, or m/d/Y or Y-m-d string -> date; else None."""
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, (int, float)) and 20000 < v < 80000:
        return (EXCEL_EPOCH + dt.timedelta(days=float(v))).date()
    if isinstance(v, str):
        s = v.strip()
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"):
            try:
                return dt.datetime.strptime(s, fmt).date()
            except ValueError:
                pass
    return None

def iso(d):
    return d.isoformat() if d else ""

def to_float(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except ValueError:
            return None
    return None

def sic4(v):
    f = to_float(v)
    if f is not None and f.is_integer() and 100 <= f <= 9999:
        return f"{int(f):04d}"
    return ""

def zip5(v):
    s = txt(v)
    m = re.fullmatch(r"(\d{5})(-\d{4})?", s)
    if m and m.group(1) != "00000":
        return m.group(1)
    return ""

def norm_name(s):
    return re.sub(r"[^a-z ]", "", WS.sub(" ", s.lower().replace(",", " ").replace(".", " "))).strip()

def is_individual(permittee, fname, lname):
    """Plainly a private individual: the permittee text is exactly the legal contact's own
    first + last name (either order). The contact names are compared and discarded."""
    p, f, l = norm_name(permittee), norm_name(fname), norm_name(lname)
    if not p or not f or not l:
        return False
    if p in (f"{f} {l}", f"{l} {f}"):
        return True
    # same person written with or without a middle name or initial ("Ann B Lee" vs "Ann Lee")
    pt, ft, lt = p.split(), f.split(), l.split()
    return (2 <= len(pt) <= 4 and pt[0] == ft[0] and pt[-1] == lt[-1]
            and not BUSINESS_HINT.search(permittee) and not COMPANY_ANY.search(permittee))

BUSINESS_HINT = re.compile(r"\b(llc|l l c|inc|corp|corporation|co|company|ltd|lp|llp|pllc|city|county|town|"
    r"district|dept|department|state|university|college|school|construction|contractors?|builders?|homes|"
    r"properties|development|developers?|group|partners|services?|association|trust|farms?|ranch|"
    r"excavating|excavation|enterprises|holdings|investments|ventures|authority|utilities|water|"
    r"sanitation|cdot|usa|us|of|and sons|sons|bros|brothers|dairy|feeders|cattle|land|concrete|paving|"
    r"homebuilders|companies|civil|oil|gas|energy|resources|materials|gravel|sand|church|hoa|"
    r"metro|metropolitan|management|realty|estate|capital|foundation|club|coop|cooperative)\b", re.I)

COMPANY_ANY = re.compile(r"\b(manufacturing|mfg|industries|industrial|technologies|storage|unlimited|"
    r"marietta|systems|solutions|international|associates|engineering|electric|plumbing|roofing|"
    r"landscaping|trucking|transport|logistics|recycling|equipment|supply|foods|brewing|brewery)\b", re.I)

def fetch():
    os.makedirs(DL_DIR, exist_ok=True)
    tmp = XLSX + ".part"
    cmd = ["curl", "-sSL", "--fail", "-A", USER_AGENT, "-o", tmp, "-w", "%{http_code} %{size_download}", EXPORT_URL]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.startswith("200"):
        sys.exit(f"download failed (not retrying): rc={res.returncode} {res.stdout} {res.stderr}")
    with open(tmp, "rb") as fh:
        if fh.read(2) != b"PK":
            sys.exit("download is not an xlsx (possibly a login or block page); stopping")
    os.replace(tmp, XLSX)
    json.dump({"url": EXPORT_URL, "retrieved_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "curl": res.stdout}, open(META, "w"))

def retrieved_at():
    if os.path.exists(META):
        return json.load(open(META))["retrieved_at"]
    return dt.datetime.fromtimestamp(os.path.getmtime(XLSX), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="download a new copy of the sheet first")
    ap.add_argument("--since", default="2024-01-01", help="date cursor: keep record_date >= this")
    ap.add_argument("--today", default=dt.date.today().isoformat())
    a = ap.parse_args()
    since = dt.date.fromisoformat(a.since)
    carry_from = since.replace(year=since.year - 1)
    today = dt.date.fromisoformat(a.today)
    if a.refresh or not os.path.exists(XLSX):
        fetch()
    import warnings
    warnings.simplefilter("ignore")
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    tabs = {}
    ws = wb[wb.sheetnames[0]]
    it = ws.iter_rows(values_only=True)
    header = [txt(h) for h in next(it)]
    missing = [c for c in NEEDED if c not in header]
    if missing:
        sys.exit(f"SCHEMA DRIFT: expected columns missing from sheet: {missing}")
    H = {h: i for i, h in enumerate(header)}
    rat = retrieved_at()
    qa = collections.Counter()
    out_rows, excluded_ids, ambiguous_ids = [], [], []
    first_names = collections.Counter()
    staged = []
    n_src = 0
    for r in it:
        if r is None or all(v is None for v in r[:10]):
            continue
        n_src += 1
        g = lambda c: r[H[c]] if H[c] < len(r) else None
        fn = txt(g("LegalFName"))
        if fn:
            first_names[fn.lower().split(" ")[0]] += 1
        # ---- date selection ----
        raw_recv = g("ApplicationReceivedDate")
        recv = to_date(raw_recv)
        issued, eff = to_date(g("IssuedDate")), to_date(g("EffectiveDate"))
        basis, note = "", ""
        if recv and recv > today:
            note = f" (received date in sheet is in the future: {recv.isoformat()})"
            qa["received_future_fallback"] += 1
            recv = None
        elif recv is None and txt(raw_recv):
            note = f" (received date in sheet is not a valid date: {txt(raw_recv)})"
            qa["received_invalid_fallback"] += 1
        if recv:
            rec_date, basis, dtype = recv, "received", "received"
        elif issued:
            rec_date, basis, dtype = issued, "issued" + note, "approved"
        elif eff:
            rec_date, basis, dtype = eff, "effective" + note, "approved"
        else:
            qa["no_usable_date"] += 1
            continue
        if recv is None:
            qa["src_rows_without_received_date"] += 1
        carry = False
        if rec_date < since:
            if recv and ((issued and issued >= since) or (eff and eff >= since)):
                qa["not_pulled_received_before_since_but_issued_after"] += 1
            # Decision 2026-10-10 (option C): carry in permits received in the year before the
            # cursor; they are kept later only if still-active construction permits that flag.
            if recv and carry_from <= recv < since:
                carry = True
            else:
                continue
        if rec_date > today:
            qa["dropped_future_fallback_date"] += 1
            continue
        staged.append((r, rec_date, basis, dtype, carry))
    wb.close()
    tabs[wb.sheetnames[0]] = n_src
    common_first = {n for n, c in first_names.items() if c >= 5 and len(n) > 2}

    for r, rec_date, basis, dtype, carry in staged:
        g = lambda c: r[H[c]] if H[c] < len(r) else None
        permittee = txt(g("Permittee"))
        # ---- personal data rule ----
        if is_individual(permittee, txt(g("LegalFName")), txt(g("LegalLName"))):
            qa["excluded_private_individual"] += 1
            qa["excluded_individual_type:" + txt(g("GeneralPermitType"))[:9]] += 1
            excluded_ids.append(txt(g("PermitID")))
            continue
        toks = norm_name(permittee).split()
        ambiguous = (2 <= len(toks) <= 3 and not BUSINESS_HINT.search(permittee) and not COMPANY_ANY.search(permittee)
                     and toks[0] in common_first and not re.search(r"\d", permittee))
        if ambiguous:
            qa["kept_ambiguous_possible_individual"] += 1
            ambiguous_ids.append(txt(g("PermitID")))
        ptype = txt(g("GeneralPermitType"))
        ptype = {"coe-reuse user": "COE-Reuse user", "coe-reuse treater": "COE-Reuse treater"}.get(ptype.lower(), ptype)
        owner, operator = txt(g("PropertyOwnerOrganization")), txt(g("OperatorOrganization"))
        if owner and is_individual(owner, txt(g("PropertyOwnerFName")), txt(g("PropertyOwnerLName"))):
            owner = ""; qa["owner_blanked_is_a_person"] += 1
        if operator and is_individual(operator, txt(g("OperatorFName")), txt(g("OperatorLName"))):
            operator = ""; qa["operator_blanked_is_a_person"] += 1
        facility = txt(g("FacilityName"))
        company, cbasis = (facility, "facility") if facility else (permittee, "permittee (facility name blank)")
        if not facility:
            qa["facility_blank_used_permittee"] += 1
        # ---- location (validated: some rows in the sheet are column-shifted) ----
        state_raw = g("FacilityState")
        addr = ", ".join(x for x in (txt(g("FacilityAddress1")), txt(g("FacilityAddress2"))) if x)
        city = txt(g("FacilityCity"))
        if re.search(r"@|\d{3}-\d{3}-\d{4}", addr + " " + city):
            addr, city = "", ""; qa["blanked_shifted_address"] += 1
        county_raw = txt(g("FacilityCounty"))
        potw = txt(g("AssociatedPOTW"))
        if isinstance(g("AssociatedPOTW"), (int, float)) or re.search(r"@|\d{3}-\d{3}-\d{4}", potw):
            potw = ""
        parts = [p.strip() for p in re.split(r"[,/&;]| and ", county_raw) if p.strip()]
        if parts and all(re.sub(r"\s+county$", "", p.lower()) in COUNTY_LOOKUP for p in parts):
            county = ", ".join(COUNTY_LOOKUP[re.sub(r"\s+county$", "", p.lower())] for p in parts)
        else:
            county = ""
            if county_raw:
                qa["county_not_a_colorado_county_blanked"] += 1
                if ptype.startswith("COPB") and not potw and not re.search(r"@|\d{3}-\d{3}-\d{4}", county_raw):
                    potw = county_raw      # in COPB rows this column holds the receiving treatment works
        lat, lon = to_float(g("FacilityLatitude")), to_float(g("FacilityLongitude"))
        if lat is not None and lon is not None and lon > 0:
            lon = -lon
        if not (lat is not None and lon is not None and 36.5 <= lat <= 41.5 and -109.5 <= lon <= -101.5):
            if lat is not None or lon is not None or txt(g("FacilityLatitude")):
                qa["latlon_invalid_blanked"] += 1
            lat = lon = None
        # ---- SIC ----
        sic_all = []
        for c in ("FacilitySICCode", "PermitSIC1", "PermitSIC2", "PermitSIC3", "PermitSIC4"):
            s = sic4(g(c))
            if s and s not in sic_all:
                sic_all.append(s)
        if ptype.startswith("COPB") and not isinstance(state_raw, str):
            s = sic4(state_raw)            # shifted COPB rows carry the primary SIC in the state column
            if s:
                sic_all = [s] + [x for x in sic_all if x != s]; qa["sic_from_shifted_state_column"] += 1
        sic = sic_all[0] if sic_all else ""
        sic_desc = SIC_MAJOR.get(sic[:2], "") if sic else ""
        # ---- construction fields ----
        is_csw = ptype.startswith("COR400000") or ptype.startswith("Rwaiver")
        dist = to_float(g("SWConstructionDisturbedAcres")) if is_csw else None
        total = to_float(g("SWConstructionTotalAcres")) if is_csw else None
        if is_csw and dist is None and txt(g("SWConstructionDisturbedAcres")):
            qa["disturbed_acres_non_numeric_blanked"] += 1
        act = txt(g("SWConstructionActivity")) if is_csw else ""
        cstart = to_date(g("SWConstructionStartDate")) if is_csw else None
        cend = to_date(g("SWConstructionEndDate")) if is_csw else None
        recw = g("ReceivingWater")
        recw = txt(recw) if isinstance(recw, str) and not re.search(r"@|\d{3}-\d{3}-\d{4}", recw) else ""
        seg = txt(g("StreamSegment"))
        seg = seg if re.fullmatch(r"CO[A-Za-z0-9_.\- ,/]{3,40}", seg) else ""
        actdesc = txt(g("ActivityDescription"))
        if re.search(r"@|\d{3}-\d{3}-\d{4}", actdesc):
            actdesc = ""
        # ---- flag ----
        rules = []
        # Decision 2026-10-10 (option D): the acreage rule does not fire when every project-type
        # tag is residential, pipeline, highway or non-structural.
        tags = [t.strip().lower().replace("-", "") for t in act.split("other:")[0].split(",") if t.strip()]
        has_other = "other:" in act or "other" in tags
        acre_skip = bool(tags) and not has_other and all(t in ACRE_SKIP_TAGS for t in tags)
        if dist is not None and dist >= 5:
            if acre_skip:
                qa["acres_rule_skipped_by_project_type"] += 1
            else:
                rules.append(f"acres >= 5 ({dist:g})")
        mfg = [s for s in sic_all if 2000 <= int(s) <= 3999]
        if mfg:
            rules.append(f"manufacturing SIC ({'/'.join(mfg)})")
        cn, hits, excl = company_named(company)
        if cn:
            rules.append("company-named facility" + ("" if facility else " (permittee name; facility name blank)")
                         + f" [{', '.join(hits)}]")
        # ---- description ----
        d = [ptype, f"Facility: {facility}" if facility else "", f"Permittee: {permittee}" if permittee else "",
             f"Activity: {act}" if act else "", f"Disturbed acres: {dist:g}" if dist is not None else "",
             (f"SIC {sic}" + (f" ({sic_desc})" if sic_desc else "")) if sic else "", actdesc]
        desc = WS.sub(" ", "; ".join(x for x in d if x)).strip()[:500]
        status = txt(g("PermitStatus"))
        status = {"admin continued": "Admin continued", "pending": "Pending"}.get(status.lower(), status)
        if carry:
            if not (ptype.startswith("COR400000") and status in ("Effective", "Admin continued", "Pending") and rules):
                continue
            qa["carried_prior_year_active_construction_flagged"] += 1
        sector = txt(g("PermitSector"))
        sector = "Commerce and industry" if sector.lower() == "commerce and industry" else sector
        mm = txt(g("MajorMinor"))
        row = {
            "source": SOURCE, "source_level": SOURCE_LEVEL, "record_id": txt(g("PermitID")),
            "record_date": rec_date.isoformat(), "date_type": dtype, "record_type": ptype,
            "company_name": company, "company_role": "permittee", "site_address": addr, "city": city,
            "county": county, "zip": zip5(g("FacilityZip")), "description": desc,
            "flag": "Y" if rules else "N", "flag_rule": "; ".join(rules), "source_url": VIEW_URL,
            "retrieved_at": rat,
            "permittee": permittee, "owner": owner,
            "operator": operator, "former_permittee": txt(g("FormerPermittee")),
            "company_name_basis": cbasis, "permit_sector": sector,
            "disturbed_acres": f"{dist:g}" if dist is not None else "",
            "total_acres": f"{total:g}" if total is not None else "", "construction_activity": act,
            "sic_code": sic, "sic_description": sic_desc, "other_sic_codes": "/".join(sic_all[1:]),
            "activity_description": actdesc, "permit_status": status,
            "issued_date": iso(to_date(g("IssuedDate"))), "effective_date": iso(to_date(g("EffectiveDate"))),
            "expiration_date": iso(to_date(g("ExpirationDate"))),
            "termination_date": iso(to_date(g("TerminationDate"))),
            "construction_start_date": iso(cstart), "construction_end_date": iso(cend),
            "receiving_water": recw, "stream_segment": seg, "associated_potw": potw,
            "previous_permit_id": txt(g("PreviousPermitID")) if isinstance(g("PreviousPermitID"), str) else "",
            "major_minor": mm if mm in ("Major", "Minor") else "", "date_basis": basis,
            "scope_basis": ("received in prior year; active construction permit that flags" if carry
                            else "record date on or after cursor"),
            "latitude": f"{lat:.6f}" if lat is not None else "", "longitude": f"{lon:.6f}" if lon is not None else "",
            "snapshot_as_of": SNAPSHOT_AS_OF,
        }
        out_rows.append(row)
    out_rows.sort(key=lambda x: (x["record_date"], x["record_id"]))
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=BASE_COLS + EXTRA_COLS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(out_rows)
    sha = hashlib.sha256(open(XLSX, "rb").read()).hexdigest()
    json.dump({"parser_version": PARSER_VERSION, "xlsx_sha256": sha, "xlsx_bytes": os.path.getsize(XLSX),
               "retrieved_at": rat, "tabs_rows": tabs, "n_columns": len(header), "since": a.since,
               "rows_in_date_scope": len(staged), "rows_written": len(out_rows), "counters": dict(qa),
               "excluded_individual_permit_ids": excluded_ids, "ambiguous_kept_permit_ids": ambiguous_ids},
              open(QA, "w"), indent=1)
    print(f"source rows {n_src}; in date scope {len(staged)}; written {len(out_rows)} -> {OUT}")
    for k, v in sorted(qa.items()):
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
