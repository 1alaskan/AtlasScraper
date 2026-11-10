"""Industrial planning and land-use agenda items from city Legistar systems (public web API) into the shared 17-column format.

Usage: python3 pull_legistar_planning_items.py <out folder>
Cities with a working public API when written (2026-11-10): Oakland, Hayward, San Leandro, Alameda. Fremont, Livermore, Berkeley, Union City
and Pleasanton returned a server error (no public API for those clients).
Scope: matters introduced 2024-01-01 onward whose title names an industrial use. Applicant, appellant and owner names are stripped from the
text; no person names are carried. These are meeting items, not permits: one row per agenda matter.
"""
import csv, json, sys, os, re, time, urllib.request, urllib.parse, datetime, collections
OUT = sys.argv[1]
CITIES = {"oakland": "Oakland", "hayward": "Hayward", "sanleandro": "San Leandro", "alameda": "Alameda"}
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
COLS = "source,source_level,record_id,record_date,date_type,record_type,company_name,company_role,site_address,city,county,zip,description,flag,flag_rule,source_url,retrieved_at".split(",")
IND = re.compile(r"manufactur|industrial|warehouse|fabricat|brewery|distiller|food processing|processing (?:facility|plant)|research and development|\bR&D\b|laborator|batch plant|recycling facility|"
                 r"data center|cold storage|truck terminal|advanced manufacturing|life science|biotech|semiconductor|battery|machine shop|production facility", re.I)
HARD = re.compile(r"manufactur|fabricat|brewery|distiller|processing (?:facility|plant)|batch plant|production facility|machine shop|semiconductor|battery", re.I)
LAND = re.compile(r"\bPLN\s?\d|use permit|conditional use|design review|site plan|planned development|rezon|general plan amendment|development agreement|variance|zoning (?:administrator|permit)|major development|entitlement", re.I)
STREET = re.compile(r"\b\d{2,6}(?:\s*(?:-|&|and)\s*\d{2,6})?\s+(?:[NSEW]\.?\s+)?(?:[A-Za-z0-9]+\.?\s+){1,3}(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Pkwy|Parkway|Cir|Circle)\b\.?", re.I)
PERSON = re.compile(r"\b(?:Applicants?|Appellants?|Owners?|Property Owners?|Representative|Contact)\s*:\s*[^.;|]{0,80}", re.I)
rows, stats = [], collections.OrderedDict()
for client, city in CITIES.items():
    skip, n = 0, 0
    while True:
        q = urllib.parse.urlencode({"$top": 1000, "$skip": skip, "$orderby": "MatterId", "$filter": "MatterIntroDate ge datetime'2024-01-01'"})
        d = json.load(urllib.request.urlopen("https://webapi.legistar.com/v1/%s/matters?%s" % (client, q), timeout=90))
        for x in d:
            n += 1
            title = re.sub(r"\s+", " ", (x.get("MatterTitle") or x.get("MatterName") or "")).strip()
            if not IND.search(title): continue
            land = bool(LAND.search(title))
            text = PERSON.sub("[name removed]", title)
            m = STREET.search(text)
            if land and HARD.search(title): flag, rule = "Y", "all concept and plan rows flagged: land-use item naming manufacturing, fabrication, processing or similar"
            elif land: flag, rule = "N", "not flagged: land-use item with an industrial-adjacent word only (warehouse, laboratory, R&D, data center, industrial zone)"
            else: flag, rule = "N", "not flagged: not a land-use item (contract, grant, ordinance or report that mentions an industrial word)"
            rows.append({"source": "%s Legistar agenda items" % city, "source_level": "County (Alameda, CA)", "record_id": "%s-%s" % (client, x.get("MatterFile") or x["MatterId"]),
                "record_date": (x.get("MatterIntroDate") or "")[:10], "date_type": "introduced", "record_type": (x.get("MatterTypeName") or "agenda item"), "company_name": "", "company_role": "unknown",
                "site_address": m.group(0).strip() if m else "", "city": city, "county": "Alameda", "zip": "", "description": text[:500], "flag": flag, "flag_rule": rule,
                "source_url": "https://%s.legistar.com/Legislation.aspx" % client, "retrieved_at": NOW, "status": x.get("MatterStatusName") or ""})
        if len(d) < 1000: break
        skip += 1000; time.sleep(1)
    stats[city] = n
with open(os.path.join(OUT, "scrape_legistar_planning_items.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS + ["status"]); w.writeheader(); w.writerows(rows)
print("matters read since 2024:", dict(stats)); print("rows kept", len(rows), "flagged", sum(r["flag"] == "Y" for r in rows), "with address", sum(bool(r["site_address"]) for r in rows))
print(collections.Counter((r["city"], r["flag"]) for r in rows))
for r in [r for r in rows if r["flag"] == "Y"][:40]: print("  ", r["record_date"], r["city"], "|", r["site_address"][:30], "|", r["description"][:150])
