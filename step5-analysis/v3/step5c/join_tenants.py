#!/usr/bin/env python3
"""Step 5c: try to name the tenant at unattached Denver addresses scoring 40 or more.

Usage: python3 join_tenants.py <v3 folder> <step4-scrape folder> <frs_filtered.csv> <denver_business_licenses.csv> [--min 40]
Joins by the v3 address key (house number + S/W/E prefix + street name) and zip. A second, weaker tier lists EPA
facilities within 75 m of the permit point whose address differs. Every name found is a possible occupier, not confirmed.
"""
import csv, math, os, sys
from collections import defaultdict
sys.path.insert(0, os.path.join(sys.argv[1], "scripts"))
from v3_lib import addr_key, unit_of, nk
csv.field_size_limit(10 ** 9)
V3, S4, FRS, LIC = sys.argv[1:5]
MIN = float(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 40.0
SKIP_LIC = {"Residential Rental Property", "Short Term Rental", "Parking Lot, Garage", "Swimming Pool", "Valet Location License", "Pedal Cab Company"}

def rd(p):
    return list(csv.DictReader(open(p, newline="", encoding="utf-8-sig")))

rk = [x for x in rd(os.path.join(V3, "denver_ranked_accounts_v3.csv"))
      if x["company_name"].startswith("Unattached") and not x["county_basis"].startswith("Denver mailing") and float(x["score"]) >= MIN]
pts = {}
for fn in ("scrape_denver_commercial_permits_v2.csv", "scrape_denver_site_plans.csv"):
    for r in rd(os.path.join(S4, fn)):
        k = addr_key(r["site_address"])
        try:
            if k and k not in pts and r.get("latitude") and float(r["latitude"]):
                pts[k] = (float(r["latitude"]), float(r["longitude"]))
        except ValueError:
            pass
frs = [x for x in rd(FRS) if x["state"] == "CO" and (x["county"].upper().startswith("DENVER") or x["city"].upper() == "DENVER" or x["zip"][:3] == "802")]
frs_ix = defaultdict(list)
for x in frs:
    frs_ix[addr_key(x["street"])].append(x)
lic_ix = defaultdict(list)
for x in rd(LIC):
    if x["LICENSE_TYPE"] not in SKIP_LIC:
        lic_ix[addr_key(x["ADDRESS"])].append(x)

def dist(a, b):
    return 111320 * math.hypot(a[0] - b[0], (a[1] - b[1]) * math.cos(math.radians(a[0])))

out = []
for x in rk:
    k = addr_key(x["site_address"]); u = unit_of(x["site_address"]); z = x["zip"][:5]
    base = dict(rank=x["rank"], score=x["score"], site_address=x["site_address"], zip=z, stage=x["stage"], fit_before=x["compressed_air_fit"].split(":")[0],
                possible_occupier_v3=x["company_name"].split("possible occupier: ")[1].rstrip(")") if "possible occupier" in x["company_name"] else "")
    hits = []
    for f in frs_ix.get(k, []):
        if z and f["zip"][:5] and f["zip"][:5] != z:
            continue
        hits.append(dict(source="EPA FRS", name=f["facility_name"], detail="NAICS %s (all: %s)" % (f["naics_primary"], f["naics_all"]), record_id=f["frs_id"],
                         address_in_source=f["street"], match="same street address"))
    for l in lic_ix.get(k, []):
        if z and l["ZIP"][:5] and l["ZIP"][:5] != z:
            continue
        lu = unit_of(l["ADDRESS"])
        m = "same street address, same unit" if (u and lu == u) else "same street address, different unit" if (u and lu and lu != u) else "same street address"
        nm = l["TRADE_NAME"] or l["ENTITY_NAME"]
        hits.append(dict(source="Denver business licences", name=nm, detail="%s%s; applied %s; expires %s" % (l["LICENSE_TYPE"], "" if l["LICENSE_SUB_TYPE"] in ("NA", "", None) else " / " + l["LICENSE_SUB_TYPE"], l["Application_Date"] or "n/a", l["Expiration_Date"] or "n/a"),
                         record_id=l["BFN"], address_in_source=l["ADDRESS"].strip(), match=m))
    if k in pts:
        for f in frs:
            try:
                p = (float(f["lat"]), float(f["lon"]))
            except ValueError:
                continue
            d = dist(pts[k], p)
            if d <= 75 and addr_key(f["street"]) != k:
                hits.append(dict(source="EPA FRS", name=f["facility_name"], detail="NAICS %s; %d m from the permit point" % (f["naics_primary"], d), record_id=f["frs_id"],
                                 address_in_source=f["street"], match="nearby, different address (weak)"))
    if not hits:
        out.append(dict(base, source="", name="", detail="", record_id="", address_in_source="", match="no match"))
    for h in hits:
        out.append(dict(base, **h))
cols = ["rank", "score", "site_address", "zip", "stage", "fit_before", "possible_occupier_v3", "match", "source", "name", "detail", "record_id", "address_in_source"]
with open("tenant_candidates_v3.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
print("addresses", len(rk), "| FRS rows in Denver scope", len(frs), "| licence rows used", sum(len(v) for v in lic_ix.values()))
