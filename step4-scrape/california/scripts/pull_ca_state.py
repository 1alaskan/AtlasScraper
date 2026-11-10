"""California state-tier pulls into the shared 17-column format.

Usage: python3 pull_ca_state.py <raw folder> <out folder>
<raw folder> must hold files downloaded by hand-off commands in scrape_notes_california.md:
  smarts_industrial.csv, smarts_construction.csv  (data.ca.gov SMARTS dataset, direct file downloads; do not use /api/, robots.txt disallows it)
  abc.zip                                          (ABC Daily Data Export, CSV zip)
  caeatfa.xlsx                                     (CAEATFA STE awards workbook)
  cctc_awardees.json                               (California Competes awardee table, admin-ajax endpoint the page itself calls)
Scope: records dated 2024-01-01 onward (ABC: snapshot of manufacturer licence types, no application date in the export).
Wide net: every in-scope row is kept and tagged flag Y/N. Contact, certifier and other personal-name fields are never carried.
Names with no business or public-body word are blanked as possible private individuals (counted in the summary).
"""
import csv, sys, os, re, json, zipfile, io, html, datetime, collections
csv.field_size_limit(10**9)
RAW, OUT = sys.argv[1], sys.argv[2]
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
START = "2024-01-01"
COLS = "source,source_level,record_id,record_date,date_type,record_type,company_name,company_role,site_address,city,county,zip,description,flag,flag_rule,source_url,retrieved_at".split(",")
BIZ = re.compile(r"\b(inc|llc|l\.l\.c|corp|corporation|co|company|ltd|lp|llp|partners|partnership|group|holdings|trust|properties|industries|industrial|manufactur\w*|systems|technologies|technology|labs?|laborator\w*|foods?|brewing|brewery|winery|wines?|cellars|vineyards?|distill\w*|spirits|city|county|district|university|college|school|state|department|authority|agency|association|church|foundation|services|enterprises|energy|electric|pacific|california|usa|us|america\w*|international|global|logistics|construction|builders|homes|development|investments?|ventures|capital|realty|materials|aggregates|concrete|recycling|steel|metals?|plastics|packaging|pharma\w*|bio\w*|medical|aerospace|motors|automotive|tesla|caltrans|bart|port|airport|laboratory|center|centre|works|solutions|products|supply|farms?|ranch|dairy|estates?|machine\w*|machining|transport\w*|trucking|freight|express|tech|fabricat\w*|signs?|storage|auto|brands?|parcel|service|shop|dies|tool\w*|weld\w*|composites|adhesives|rebar|envelope|petrol\w*|dismantl\w*|waters|deco|crafts|cnc|art|press\w*|precision|engineering|design|studios?|coatings?|plating|printing|paper|box|glass|wood\w*|cabinet\w*|furniture|marble|granite|stone|tile|iron|aluminum|foundry|casting|molding|rubber|chemical\w*|paint|oil|gas|fuel|towing|recycl\w*|salvage|wreck\w*|parts|equipment|rentals?|marine|boat\w*|aviation|air|rail\w*|bus|lines|distribution|warehouse|cold|produce|packing|bakery|meat|seafood|coffee|tea|water|beverage|bottling|nursery|landscape|supplies|\d+)\b", re.I)
FIRST = set("james john robert michael william david richard joseph thomas tom charles chris christopher daniel dan matthew matt anthony tony mark donald don steven steve paul andrew andy joshua josh kenneth ken kevin brian george edward ed ronald ron timothy tim jason jeffrey jeff ryan jacob gary nicholas nick eric jonathan stephen larry justin scott brandon benjamin ben samuel sam gregory greg frank alexander alex raymond ray patrick jack dennis jerry tyler aaron jose juan carlos luis jorge miguel pedro manuel francisco antonio jesus ricardo roberto fernando javier sergio raul mario hector oscar ruben victor henry adam douglas doug nathan peter pete zachary kyle walter harold jeremy carl keith roger gerald terry sean arthur lawrence larry jim jimmy bill billy bob bobby mike joe dave rick rich dick trevis mary patricia jennifer linda elizabeth barbara susan jessica sarah karen nancy lisa betty margaret sandra ashley kimberly emily donna michelle carol amanda melissa deborah stephanie rebecca laura sharon cynthia kathleen amy shirley angela helen anna brenda pamela nicole maria rosa ana teresa gloria martha".split())
MFG_WORDS = re.compile(r"manufactur|production|fabricat|processing|assembly|brewing|foundry|semiconductor|battery|machin", re.I)
stats = collections.OrderedDict()

def clean(s):
    s = html.unescape((s or "").replace("\n", " ")).strip()
    return "" if s in ("NA", "NaN", "N/A") else re.sub(r"\s+", " ", s)

def name_ok(n, st, key):
    t = re.findall(r"[A-Za-z']+", n or "")
    if n and not BIZ.search(n) and 2 <= len(t) <= 3 and t[0].lower() in FIRST:
        st[key] = st.get(key, 0) + 1
        return ""
    return n

def write(name, rows, extra):
    path = os.path.join(OUT, "scrape_%s.csv" % name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(COLS + extra)
        for r in rows: w.writerow([r.get(c, "") for c in COLS + extra])
    return path

def summarize(name, rows, st):
    st["rows"] = len(rows); st["flag_Y"] = sum(r["flag"] == "Y" for r in rows)
    st["by_rule"] = dict(collections.Counter(r["flag_rule"] for r in rows).most_common())
    for k in ("company_name", "site_address", "record_date"):
        st["null_" + k] = sum(not r.get(k) for r in rows)
    d = sorted(r["record_date"] for r in rows if r.get("record_date"))
    st["date_range"] = [d[0], d[-1]] if d else []
    stats[name] = st

def sic2(s):
    m = re.match(r"\s*(\d{4})", s or ""); return m.group(1) if m else ""

# ---- SMARTS industrial
rows, st = [], {}
with open(os.path.join(RAW, "smarts_industrial.csv"), encoding="utf-8-sig", errors="replace", newline="") as f:
    for r in csv.DictReader(f):
        d = clean(r["NOI_PROCESSED_DATE"])[:10]
        if d < START: continue
        sic = sic2(r["PRIMARY_SIC"]); nec = "NEC" in r["WDID"]
        mfg = sic[:2].isdigit() and 20 <= int(sic[:2]) <= 39
        if mfg and not nec: flag, rule = "Y", "A: new Industrial General Permit enrolment, manufacturing SIC 20-39"
        elif mfg: flag, rule = "Y", "A: new No Exposure Certification, manufacturing SIC 20-39"
        else: flag, rule = "N", "not flagged: non-manufacturing SIC (%s)" % (sic[:2] or "blank")
        rows.append({"source": "California SMARTS industrial stormwater", "source_level": "State (California)", "record_id": clean(r["WDID"]) or r["APP_ID"],
            "record_date": d, "date_type": "processed", "record_type": "No Exposure Certification" if nec else "Notice of Intent",
            "company_name": name_ok(clean(r["OPERATOR_NAME"]), st, "names_blanked"), "company_role": "permittee",
            "site_address": clean(r["FACILITY_ADDRESS"]), "city": clean(r["FACILITY_CITY"]), "county": clean(r["FACILITY_COUNTY"]) or clean(r["COUNTY"]), "zip": clean(r["FACILITY_ZIP"])[:5],
            "description": ("Facility: %s; SIC %s; status %s; size %s %s" % (clean(r["FACILITY_NAME"]) if BIZ.search(r["FACILITY_NAME"] or "") else "", clean(r["PRIMARY_SIC"]), clean(r["STATUS"]), clean(r["FACILITY_TOTAL_SIZE"]), clean(r["FACILITY_TOTAL_SIZE_UNIT"])))[:500],
            "flag": flag, "flag_rule": rule, "source_url": "https://data.ca.gov/dataset/stormwater-regulatory-including-enforcement-actions-information-and-water-quality-results", "retrieved_at": NOW,
            "primary_sic": sic, "status": clean(r["STATUS"]), "terminated_date": clean(r["NOT_EFFECTIVE_DATE"])[:10], "latitude": clean(r["FACILITY_LATITUDE"]), "longitude": clean(r["FACILITY_LONGITUDE"])})
summarize("smarts_industrial", rows, st); write("smarts_industrial", rows, ["primary_sic", "status", "terminated_date", "latitude", "longitude"])

# ---- SMARTS construction
rows, st = [], {}
with open(os.path.join(RAW, "smarts_construction.csv"), encoding="utf-8-sig", errors="replace", newline="") as f:
    for r in csv.DictReader(f):
        d = clean(r["NOI_PROCESSED_DATE"])[:10]
        if d < START: continue
        ind, com, res = r["CONSTRUCTION_INDUSTRIAL"] == "Y", r["CONSTRUCTION_COMMERTIAL"] == "Y", r["CONSTRUCTION_RESIDENTIAL"] == "Y"
        if ind: flag, rule = "Y", "A: construction stormwater enrolment marked industrial"
        elif com and not res: flag, rule = "N", "not flagged: commercial only"
        elif res: flag, rule = "N", "not flagged: residential"
        else: flag, rule = "N", "not flagged: linear, utility, transportation or other"
        owner = name_ok(clean(r["OWNER_NAME"]), st, "names_blanked")
        site = clean(r["SITE_NAME"])
        rows.append({"source": "California SMARTS construction stormwater", "source_level": "State (California)", "record_id": clean(r["WDID"]) or r["APP_ID"],
            "record_date": d, "date_type": "processed", "record_type": "Construction General Permit " + clean(r["TYPE_OF_CONSTRUCTION"]),
            "company_name": owner, "company_role": "owner", "site_address": clean(r["SITE_ADDRESS"]), "city": clean(r["SITE_CITY"]), "county": clean(r["SITE_COUNTY"]) or clean(r["COUNTY"]), "zip": clean(r["SITE_ZIP"])[:5],
            "description": ("Site: %s; status %s; disturbed %s acres; start %s; complete %s" % (site if owner else "", clean(r["STATUS"]), clean(r["SITE_TOTAL_DISTURBED_ACREAGE"]), clean(r["CONSTRUCTION_COMMENCEMENT_DATE"])[:10], clean(r["COMPLETE_PROJECT_DATE"])[:10]))[:500],
            "flag": flag, "flag_rule": rule, "source_url": "https://data.ca.gov/dataset/stormwater-regulatory-including-enforcement-actions-information-and-water-quality-results", "retrieved_at": NOW,
            "developer_name": name_ok(clean(r["DEVELOPER_NAME"]), st, "developer_names_blanked"), "status": clean(r["STATUS"]), "disturbed_acres": clean(r["SITE_TOTAL_DISTURBED_ACREAGE"]),
            "construction_start": clean(r["CONSTRUCTION_COMMENCEMENT_DATE"])[:10], "latitude": clean(r["SITE_LATITUDE"]), "longitude": clean(r["SITE_LONGITUDE"])})
summarize("smarts_construction", rows, st); write("smarts_construction", rows, ["developer_name", "status", "disturbed_acres", "construction_start", "latitude", "longitude"])

# ---- California Competes
rows, st = [], {}
for x in json.load(open(os.path.join(RAW, "cctc_awardees.json"))):
    v = x["value"]; d = clean(v["dateagreementapprovedyyyymmdd"]).replace("/", "-")
    if d < START: continue
    ind = clean(v["industry"]); m = re.search(r'href="([^"]+)"', v.get("downloadlink") or "")
    mfg = bool(MFG_WORDS.search(ind))
    rows.append({"source": "California Competes Tax Credit awards", "source_level": "State (California)", "record_id": str(v.get("___id___", "")), "record_date": d, "date_type": "approved",
        "record_type": "tax credit agreement", "company_name": clean(v["name"]), "company_role": "applicant", "site_address": "", "city": clean(v["primarylocations"]), "county": "", "zip": "",
        "description": ("Industry: %s; net new full-time employees %s; investment %s; credit %s%s" % (ind, clean(v["netincreaseoffulltimeemployees"]), clean(v["investments"]), clean(v["amountoftaxcredit"]), ("; recaptured " + clean(v["amountrecaptured"])) if clean(v["amountrecaptured"]) else ""))[:500],
        "flag": "Y" if mfg else "N", "flag_rule": "A: named award, industry text names manufacturing or production" if mfg else "not flagged: industry text does not name manufacturing",
        "source_url": ("https:" + m.group(1)) if m and m.group(1).startswith("//") else (m.group(1) if m else "https://business.ca.gov/awardee-list/"), "retrieved_at": NOW,
        "industry": ind, "net_new_employees": clean(v["netincreaseoffulltimeemployees"]), "investment": clean(v["investments"]), "credit": clean(v["amountoftaxcredit"])})
summarize("calcompetes_awards", rows, st); write("calcompetes_awards", rows, ["industry", "net_new_employees", "investment", "credit"])

# ---- CAEATFA
import openpyxl
rows, st = [], {}
ws = openpyxl.load_workbook(os.path.join(RAW, "caeatfa.xlsx"), read_only=True, data_only=True)["Apps Approved"]
hdr = None
for r in ws.iter_rows(values_only=True):
    if hdr is None:
        if r and "App. No." in [str(c).strip() for c in r if c]: hdr = [re.sub(r"\s+", " ", str(c or "")).strip() for c in r]
        continue
    rec = dict(zip(hdr, r)); app = clean(str(rec.get("App. No.") or ""))
    if not re.match(r"\d\d-SM\d+", app): continue
    da = rec.get("Date Approved"); d = da.strftime("%Y-%m-%d") if hasattr(da, "strftime") else clean(str(da or ""))[:10]
    if d < START: continue
    g = lambda k: clean(str(rec.get(k) if rec.get(k) is not None else ""))
    qp = g("Qualified Property Amount Approved"); pct = g("% Reported")
    addr = g("Project Address 1")
    rows.append({"source": "CAEATFA Sales and Use Tax Exclusion awards", "source_level": "State (California)", "record_id": app, "record_date": d, "date_type": "approved", "record_type": g("Project Type"),
        "company_name": g("Applicant Name"), "company_role": "applicant", "site_address": addr, "city": g("City"), "county": g("Primary County") or g("County"), "zip": (re.findall(r"\b9\d{4}\b", addr) or [""])[-1],
        "description": ("Use of proceeds: %s; qualified property approved $%s; reported purchased $%s; share reported %s; status %s" % (g("Use of Proceeds"), qp, g("Qualified Property Amount Reported"), pct[:6], g("Project Status")))[:500],
        "flag": "Y", "flag_rule": "A: named equipment tax exclusion award", "source_url": "https://www.treasurer.ca.gov/sites/default/files/caeatfa/salesandtax.xlsx", "retrieved_at": NOW,
        "qualified_property_approved": qp, "qualified_property_reported": g("Qualified Property Amount Reported"), "share_reported": pct, "project_status": g("Project Status"),
        "more_addresses": " | ".join(x for x in (g("Project Address 2"), g("Project Address 3"), g("Project Address 4")) if x and not x.isdigit())})
summarize("caeatfa_ste_awards", rows, st); write("caeatfa_ste_awards", rows, ["qualified_property_approved", "qualified_property_reported", "share_reported", "project_status", "more_addresses"])

# ---- ABC (snapshot)
TYPES = {"01": "Beer manufacturer", "02": "Winegrower", "03": "Brandy manufacturer", "04": "Distilled spirits manufacturer", "06": "Still", "22": "Wine blender", "23": "Small beer manufacturer", "74": "Craft distiller"}
rows, st = [], {}
z = zipfile.ZipFile(os.path.join(RAW, "abc.zip"))
with z.open(z.namelist()[0]) as f:
    t = io.TextIOWrapper(f, encoding="latin-1"); stamp = next(t); rd = csv.DictReader(t); rd.fieldnames = [x.strip() for x in rd.fieldnames]
    for r in rd:
        ty = r["License Type"].strip()
        if ty not in TYPES: continue
        app = r["Lic or App"].strip() == "APP"; d = ""
        try: d = datetime.datetime.strptime((r["Type Orig Iss Date"] or "").strip().title(), "%d-%b-%Y").strftime("%Y-%m-%d")
        except ValueError: d = ""
        if not app and d < START: continue
        pend = app and r["Type Status"].strip() == "PEND"
        if pend: flag, rule = "Y", "A: pending licence application, manufacturer type"
        elif app: flag, rule = "N", "not flagged: application record with status %s (meaning of a non-pending application record not confirmed)" % r["Type Status"].strip().lower()
        else: flag, rule = "Y", "B: manufacturer licence first issued 2024 or later"
        rows.append({"source": "California ABC licence export", "source_level": "State (California)", "record_id": r["File Number"].strip() + "-" + ty, "record_date": d, "date_type": "original issue" if d else "",
            "record_type": "%s %s (%s)" % (ty, TYPES[ty], "application" if app else "licence"), "company_name": name_ok(clean(r["Primary Name"]), st, "names_blanked"), "company_role": "applicant" if app else "permittee",
            "site_address": clean(r["Prem Addr 1"] + " " + r["Prem Addr 2"]), "city": clean(r["Prem City"]).title(), "county": clean(r["Prem County"]).title(), "zip": clean(r["Prem Zip"])[:5],
            "description": ("DBA: %s; status %s; snapshot %s" % (clean(r["DBA Name"]), r["Type Status"].strip(), clean(stamp).strip('"')))[:500],
            "flag": flag, "flag_rule": rule, "source_url": "https://www.abc.ca.gov/licensing/licensing-reports", "retrieved_at": NOW, "type_status": r["Type Status"].strip()})
rows = [r for r in rows if r["company_name"]]
summarize("abc_manufacturer_licences", rows, st); write("abc_manufacturer_licences", rows, ["type_status"])
json.dump(stats, open(os.path.join(OUT, "pull_summary.json"), "w"), indent=1)
for k, v in stats.items(): print(k, json.dumps(v)[:900])
