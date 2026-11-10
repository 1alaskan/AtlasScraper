"""City of Hayward business licences (ArcGIS open data layer) into the shared 17-column format.

Usage: python3 pull_hayward_business_licenses.py <out folder>
Source: https://opendata.hayward-ca.gov/ -> Business Licenses (FeatureServer layer 0, public, no key). Layer last edited 2026-01-22 when pulled.
Scope: manufacturing NAICS (31-33) licences, any start date (the full set is the installed base); flag = Y when the licence started 2024-01-01
or later and is active. Rows whose name looks like a private individual are left out. The layer carries no owner or contact fields.
"""
import csv, json, sys, os, re, urllib.request, urllib.parse, datetime, collections
OUT = sys.argv[1]
U = "https://services3.arcgis.com/VRO5V8PH7DzSE6AU/arcgis/rest/services/Business_Licenses/FeatureServer/0/query"
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
COLS = "source,source_level,record_id,record_date,date_type,record_type,company_name,company_role,site_address,city,county,zip,description,flag,flag_rule,source_url,retrieved_at".split(",")
FIRST = set("james john robert michael william david richard joseph thomas charles daniel matthew anthony mark steven paul andrew kevin brian george jose juan carlos luis jorge miguel pedro manuel francisco antonio jesus maria rosa ana mary patricia jennifer linda".split())
feats, off = [], 0
while True:
    q = urllib.parse.urlencode({"where": "NAICS LIKE '31%' OR NAICS LIKE '32%' OR NAICS LIKE '33%'", "outFields": "*", "returnGeometry": "false", "orderByFields": "OBJECTID", "resultOffset": off, "resultRecordCount": 1000, "f": "json"})
    d = json.load(urllib.request.urlopen(U + "?" + q, timeout=60))
    fs = d.get("features", []); feats += [f["attributes"] for f in fs]
    if len(fs) < 1000: break
    off += 1000
def dt(ms):
    if ms in (None, "") or ms < 0: return ""
    return (datetime.datetime(1970, 1, 1) + datetime.timedelta(milliseconds=ms)).strftime("%Y-%m-%d")
rows, dropped = [], 0
for a in feats:
    name = (a.get("DBA") or "").strip(); t = re.findall(r"[A-Za-z']+", name)
    if not name or (2 <= len(t) <= 3 and t[0].lower() in FIRST and not re.search(r"\b(inc|llc|corp|co|company|mfg|manufactur\w*|machine\w*|foods?|products|industries)\b", name, re.I)):
        dropped += 1; continue
    if len(t) == 2 and (a.get("EmployeeCount") or 0) == 0 and not re.search(r"\b(inc|llc|corp|co|company|mfg|manufactur\w*|machine\w*|foods?|products|industries|cabinets?|facades?|doors?|steel|metal\w*|fabricat\w*|bakery|brewing)\b", name, re.I):
        dropped += 1; continue   # two-word name, no employees, no business or trade word: may be a sole proprietor's own name
    start, close = dt(a.get("StartDate")), dt(a.get("CloseDate")); active = (a.get("BusinessStatus") or "") == "Active"
    new = start >= "2024-01-01" and active
    rows.append({"source": "Hayward business licences", "source_level": "County (Alameda, CA)", "record_id": "HAY-BL-%s" % a["OBJECTID"], "record_date": start, "date_type": "licence start",
        "record_type": "business licence (%s)" % (a.get("BusinessType") or "").strip(), "company_name": name, "company_role": "permittee", "site_address": (a.get("BusAddress") or "").strip(),
        "city": (a.get("BusCity") or "").strip().title(), "county": "Alameda" if (a.get("BusCity") or "").strip().upper() == "HAYWARD" else "", "zip": (a.get("BusZip") or "")[:5],
        "description": ("NAICS %s %s; employees %s; status %s%s" % (a.get("NAICS") or "", a.get("NaicsDescription") or "", a.get("EmployeeCount"), a.get("BusinessStatus") or "", ("; closed " + close) if close else ""))[:500],
        "flag": "Y" if new else "N", "flag_rule": "A: manufacturing NAICS licence started 2024 or later, active" if new else "not flagged: started before 2024 or not active",
        "source_url": "https://opendata.hayward-ca.gov/", "retrieved_at": NOW, "naics": a.get("NAICS") or "", "employee_count": a.get("EmployeeCount"), "business_status": a.get("BusinessStatus") or ""})
with open(os.path.join(OUT, "scrape_hayward_business_licenses.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS + ["naics", "employee_count", "business_status"]); w.writeheader(); w.writerows(rows)
fl = [r for r in rows if r["flag"] == "Y"]
print("manufacturing licences", len(rows), "dropped as possible individuals", dropped, "flagged", len(fl), "outside Hayward address", sum(r["county"] == "" for r in rows))
print("null address", sum(not r["site_address"] for r in rows), "null date", sum(not r["record_date"] for r in rows), "date range", min(r["record_date"] for r in rows if r["record_date"]), max(r["record_date"] for r in rows))
print(collections.Counter(r["record_date"][:4] for r in fl), collections.Counter(r["naics"][:3] for r in fl).most_common(8))
for r in sorted(fl, key=lambda r: -(r["employee_count"] or 0))[:15]: print("  ", r["record_date"], r["company_name"][:38], "|", r["site_address"][:28], "|", r["description"][:80])
