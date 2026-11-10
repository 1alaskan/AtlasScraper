"""Alameda County slice of the California state pulls, the CEQAnet county export in the shared format,
and an interim evidence stack (NOT the v3 ranking: no points, no stage, no fit rules).

Usage: python3 build_alameda_slice.py <ceqa_alameda.csv> <repo root>
ceqa_alameda.csv = https://ceqanet.lci.ca.gov/Search?County=Alameda&StartRange=2024-01-01&EndRange=<today>&OutputFormat=CSV
"""
import csv, sys, os, re, collections, datetime
CEQA, ROOT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(ROOT, "step5-analysis/v3/scripts"))
S4 = os.path.join(ROOT, "step4-scrape/california"); OUT = os.path.join(S4, "alameda"); S5 = os.path.join(ROOT, "step5-analysis/california/alameda")
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
COLS = "source,source_level,record_id,record_date,date_type,record_type,company_name,company_role,site_address,city,county,zip,description,flag,flag_rule,source_url,retrieved_at".split(",")
CITIES = ["Alameda", "Albany", "Berkeley", "Dublin", "Emeryville", "Fremont", "Hayward", "Livermore", "Newark", "Oakland", "Piedmont", "Pleasanton", "San Leandro", "Union City", "Castro Valley", "San Lorenzo", "Sunol", "Ashland", "Cherryland", "Fairview"]
CITY_RE = re.compile(r"\b(%s)\b" % "|".join(CITIES), re.I)

# ---- CEQAnet
KW = re.compile(r"manufactur|industrial|warehouse|research and development|\bR&D\b|laborator|processing|fabricat|assembly|production facility|batch plant|recycl|data center|cold storage|distribution", re.I)
HARD = re.compile(r"manufactur|fabricat|processing plant|production facility|batch plant|assembly", re.I)
rows = []
for r in csv.DictReader(open(CEQA, encoding="cp1252", errors="replace", newline="")):
    cities = (r.get("Cities") or "").strip(); counties = (r.get("Counties") or "").strip()
    if counties != "Alameda" and not (CITY_RE.search(cities) and "," not in counties): continue
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", r.get("Received") or "")
    d = "%s-%02d-%02d" % (m.group(3), int(m.group(1)), int(m.group(2))) if m else ""
    dev = (r.get("NOC Development Type") or "").strip(); text = " ".join([r.get("Project Title") or "", r.get("Document Description") or ""])
    ind = "ndustrial (" in dev or dev.startswith("Industrial")
    if not (ind or KW.search(text)): continue
    if ind: flag, rule = "Y", "all concept and plan rows flagged: CEQA document with Industrial development type"
    elif HARD.search(text): flag, rule = "Y", "all concept and plan rows flagged: CEQA document, description names manufacturing, fabrication, processing or assembly"
    else: flag, rule = "N", "not flagged: industrial-adjacent keyword only (warehouse, R&D, laboratory, recycling, data center, distribution)"
    rows.append({"source": "CEQAnet (State Clearinghouse)", "source_level": "State (California)", "record_id": "%s/%s" % (r["SCH Number"], r["Document Type"].strip()), "record_date": d, "date_type": "received",
        "record_type": "CEQA " + r["Document Type"].strip(), "company_name": "", "company_role": "unknown", "site_address": re.sub(r"\s+", " ", r.get("Location Cross Streets") or "").strip()[:120],
        "city": cities, "county": "Alameda", "zip": (r.get("Location Zip Code") or "").strip()[:5],
        "description": re.sub(r"\s+", " ", "%s. %s" % (r.get("Project Title") or "", r.get("Document Description") or "")).strip()[:500], "flag": flag, "flag_rule": rule,
        "source_url": "https://ceqanet.lci.ca.gov/" + r["SCH Number"], "retrieved_at": NOW, "lead_agency": (r.get("Lead Agency Title") or "").strip(), "development_type": dev[:200], "parcel": (r.get("Location Parcel Number") or "").strip()[:80]})
with open(os.path.join(OUT, "scrape_ceqanet_alameda.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS + ["lead_agency", "development_type", "parcel"]); w.writeheader(); w.writerows(rows)
print("ceqanet rows", len(rows), "flag Y", sum(r["flag"] == "Y" for r in rows), collections.Counter(r["flag_rule"][:40] for r in rows))
ceqa = rows

# ---- county slice of the state pulls
allrows = []
for f in ["smarts_industrial", "smarts_construction", "calcompetes_awards", "caeatfa_ste_awards", "abc_manufacturer_licences"]:
    for r in csv.DictReader(open(os.path.join(S4, "scrape_%s.csv" % f), encoding="utf-8")):
        if f == "calcompetes_awards": ok = bool(CITY_RE.search(r["city"])) or "East Bay" in r["city"]
        elif f == "caeatfa_ste_awards": ok = "Alameda" in r["county"] or bool(CITY_RE.search(r["city"]))
        else: ok = r["county"].strip().lower() == "alameda"
        if ok:
            r = {c: r.get(c, "") for c in COLS}
            if f in ("calcompetes_awards", "caeatfa_ste_awards") and re.search(r"[;,]| and ", r["city"]): r["description"] = ("[multi-site award; share in Alameda County not stated] " + r["description"])[:500]
            allrows.append(r)
allrows += [{c: r[c] for c in COLS} for r in ceqa]
flagged = [r for r in allrows if r["flag"] == "Y"]
with open(os.path.join(OUT, "scrape_flagged_alameda_state_sources.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(flagged)
print("alameda rows", len(allrows), "flagged", len(flagged), collections.Counter(r["source"] for r in flagged))

# ---- interim evidence stack
from v3_lib import nk
def akey(a, city):
    a = re.sub(r"[^A-Z0-9 ]", " ", (a or "").upper()); a = re.sub(r"\b(STREET|ST|AVENUE|AVE|BOULEVARD|BLVD|ROAD|RD|DRIVE|DR|COURT|CT|WAY|LANE|LN|PARKWAY|PKWY|PLACE|PL|SUITE|STE|UNIT|BLDG|BUILDING)\b.*$", "", a)
    a = re.sub(r"\s+", " ", a).strip(); return (a + "|" + (city or "").upper().strip()) if re.match(r"\d", a) else ""
groups = collections.OrderedDict()
by_addr = {}
for r in flagged:
    k = nk(r["company_name"]) if r["company_name"] else ""
    a = akey(r["site_address"], r["city"])
    gk = k or ("ADDR:" + a if a else "")
    if not gk: continue
    if not k and a in by_addr: gk = by_addr[a]
    if k and a: by_addr.setdefault(a, gk)
    groups.setdefault(gk, []).append(r)
out = []
for gk, rs in groups.items():
    srcs = sorted(set(r["source"] for r in rs)); ds = sorted(r["record_date"] for r in rs if r["record_date"])
    best = sorted(rs, key=lambda r: (("CAEATFA" in r["source"]) * 3 + ("Competes" in r["source"]) * 2 + ("SMARTS industrial" in r["source"]), r["record_date"]), reverse=True)[0]
    addr = next((r for r in rs if r["site_address"]), rs[0])
    out.append({"company_name": next((r["company_name"] for r in rs if r["company_name"]), ""), "site_address": addr["site_address"], "city": addr["city"], "zip": addr["zip"],
        "sources_count": len(srcs), "sources": "; ".join(srcs), "records": len(rs), "first_signal_date": ds[0] if ds else "", "latest_signal_date": ds[-1] if ds else "",
        "has_incentive_award": "Y" if any("CAEATFA" in s or "Competes" in s for s in srcs) else "N", "top_evidence": ("%s %s: %s" % (best["record_date"], best["source"], best["description"]))[:300]})
out.sort(key=lambda r: (-r["sources_count"], r["has_incentive_award"] != "Y", r["latest_signal_date"] and -int(r["latest_signal_date"].replace("-", "")) or 0))
with open(os.path.join(S5, "alameda_interim_evidence_stack.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(out[0].keys())); w.writeheader(); w.writerows(out)
print("stack rows", len(out), collections.Counter(r["sources_count"] for r in out), "with award", sum(r["has_incentive_award"] == "Y" for r in out))
for r in out[:22]: print(r["sources_count"], r["has_incentive_award"], r["company_name"][:34], "|", r["site_address"][:28], r["city"][:14], "|", r["latest_signal_date"], "|", r["sources"][:90])
