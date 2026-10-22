#!/usr/bin/env python3
"""Step 5c: fold the tenant candidates into the ranking as possible occupiers and write the v3b files.

Usage: python3 apply_tenants_v3b.py <v3 folder>      (reads <v3>/step5c/tenant_candidates_v3.csv; writes into <v3>/)
Only same-street-address matches are used. Signal, source, recency and stage points do not change (neither source is in the
points table). Only the fit class changes, under the v3 fit rules, where the name settles what the site is. The calls are
listed in FIT below so they can be read and changed.
"""
import csv, os, re, sys
V3 = sys.argv[1]
sys.path.insert(0, os.path.join(V3, "scripts"))
from v3_lib import addr_key, FIT_PTS, g
csv.field_size_limit(10 ** 9)
SRC = {"EPA FRS": "EPA Facility Registry (no date; may have moved)", "Denver business licences": "Denver active business licence"}
# address key -> (fit level or None to leave as is, fit text, name to show or None)
FIT = {
    "3939 KEARNEY": ("strong", "EPA lists a commercial printer here (NAICS 323113); not confirmed", "Adams McClure"),
    "1630 35": ("moderate", "EPA lists a ready-mix concrete plant here (NAICS 327320); modest air demand; not confirmed", "Mountain Cement Co"),
    "2763 BLAKE": (None, "EPA lists a pump maker here, but that company's current stormwater permit is in Commerce City; probably moved", None),
    "11100 E 45": ("strong", "EPA lists a metal finishing and equipment maker here (NAICS 332813); matches the name v3 found; not confirmed", "Mile High Equipment Co"),
    "14135 E 42": ("strong", "EPA lists a sign manufacturer here (NAICS 339950); not confirmed", "Jones Sign Co Inc"),
    "1245 S INCA": ("strong", "EPA lists two commercial printers here (NAICS 323111); not confirmed", "Scott Printing Co"),
    "3440 WALNUT": ("strong", "EPA lists a wood products maker here (NAICS 321918); not confirmed", "Walnut St Woodworks Inc"),
    "3625 E 48": (None, "city food licence at this address since 2024; type of operation not known", "Moodswing"),
    "5500 E PACIFIC": ("moderate", "city licence: wholesale food commissary kitchen; modest air demand", "Olive & Finch"),
    "3490 PARK": ("weak", "city licences show a convenience store", "7-Eleven #39849"),
    "18309 E 65": ("moderate", "city licence: motor vehicle repair garage; small shop air", "Christian Brothers Automotive Green Valley Ranch"),
    "2000 BROADWAY": ("moderate", "city licence: tyre and motor vehicle repair garage; small shop air", "Big O Tires"),
    "6171 E EVANS": ("moderate", "city licence: tyre and motor vehicle repair garage; small shop air", "Discount Tire"),
    "4475 E 50": ("weak", "EPA lists a refrigerated warehouse here (NAICS 49312): refrigeration, little process air", "Americold Denver plant"),
    "5440 ROSLYN": ("weak", "EPA lists a City and County of Denver asphalt yard here; city facility", "City and County of Denver, Roslyn yard"),
    "6090 E 39": ("weak", "city licence: wholesale food held by a food-recovery charity", "We Don't Waste"),
    "4600 E 48": ("weak", "city licence: food service at a charity", "Denver Rescue Mission"),
    "1812 35": ("weak", "city licence: events venue", "Non Plus Ultra"),
    "3530 CHESTNUT": ("weak", "city licence: wine business", "Chestnut Cellars"),
    "4080 GLOBEVILLE": ("weak", "EPA lists a petroleum wholesaler here (NAICS 425120); bulk fuel", "Colorado Petroleum, Inc"),
}
PAT = re.compile(r"; fit (-?[\d.]+)\s*$")

def rd(p):
    return list(csv.DictReader(open(p, newline="", encoding="utf-8")))

rk = rd(os.path.join(V3, "denver_ranked_accounts_v3.csv"))
ev = rd(os.path.join(V3, "denver_evidence_v3.csv"))
cand = [c for c in rd(os.path.join(V3, "step5c", "tenant_candidates_v3.csv")) if c["match"] == "same street address"]
by = {}
for c in cand:
    by.setdefault(c["rank"], []).append(c)
added, changed = [], 0
for x in rk:
    x["rank_v3"] = x["rank"]
    x["tenant_source"] = ""
    cs = by.get(x["rank"])
    if not cs:
        continue
    k = addr_key(x["site_address"])
    level, text, name = FIT[k]
    srcs = sorted(set(SRC[c["source"]] for c in cs))
    x["tenant_source"] = "; ".join(srcs)
    old_occ = x["company_name"].split("possible occupier: ")[1].rstrip(")") if "possible occupier" in x["company_name"] else ""
    others = sorted(set(c["name"] for c in cs))
    note = "tenant candidates from %s: %s" % (" and ".join(srcs), "; ".join(others))
    if name:
        x["company_name"] = "Unattached address (possible occupier: %s)" % name
        x["match_confidence"] = "address confirmed; company possible"
        if old_occ and old_occ.upper()[:12] != name.upper()[:12]:
            note += " | v3 possible occupier from a registration or lien: " + old_occ
    x["name_variants"] = (x["name_variants"] + " | " if x["name_variants"] else "") + note
    if level:
        old = float(PAT.search(x["top_evidence"]).group(1))
        new = FIT_PTS[level]
        x["compressed_air_fit"] = "%s: %s" % (level, text)
        x["top_evidence"] = PAT.sub("; fit %s" % g(new), x["top_evidence"])
        x["score"] = "%.1f" % (float(x["score"]) - old + new)
        changed += old != new
    else:
        x["compressed_air_fit"] = x["compressed_air_fit"] + " | " + text
    x["next_step"] = ("Low priority: the possible occupier is not a plant" if level == "weak" else
                      "Tenant not identified; the possible occupier is not confirmed" if name else "Tenant not identified")
    for c in cs:
        added.append(dict(source=SRC[c["source"]].split(" (")[0], source_level="Federal" if c["source"] == "EPA FRS" else "County (Denver)", record_id=c["record_id"], record_date="",
                          date_type="", record_type=c["detail"].split(";")[0], company_name=c["name"], company_role="possible occupier", site_address=c["address_in_source"], city="Denver",
                          county="Denver", zip=x["zip"], description=c["detail"], flag="", flag_rule="", source_url="", retrieved_at="2026-10-11", rank=x["rank"],
                          company_key="A:" + k, match_class="possible", flag_tier="", flag_rule_v2="", points="0"))

def section(x):
    b = x["county_basis"]
    return 2 if b.startswith("OEDIT") else 1 if b.startswith("Denver mailing") else 0

order = sorted(range(len(rk)), key=lambda i: (section(rk[i]), -float(rk[i]["score"]), i))
newrank = {}
out = []
for n, i in enumerate(order, 1):
    newrank[rk[i]["rank"]] = n
    rk[i]["rank"] = n
    out.append(rk[i])
cols = [c for c in out[0].keys() if c not in ("rank_v3", "tenant_source")] + ["rank_v3", "tenant_source"]
with open(os.path.join(V3, "denver_ranked_accounts_v3b.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
for e in ev + added:
    e["rank"] = newrank[str(e["rank"])]
allev = sorted(ev + added, key=lambda e: e["rank"])
with open(os.path.join(V3, "denver_evidence_v3b.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(ev[0].keys())); w.writeheader(); w.writerows(allev)
print("rows %d; addresses given a tenant candidate %d; fit class changed %d; evidence rows added %d" % (len(out), len(by), changed, len(added)))
for x in out:
    if x["tenant_source"]:
        print("%3d (was %3s) %5s  %s | %s" % (x["rank"], x["rank_v3"], x["score"], x["company_name"][:70], x["compressed_air_fit"][:40]))
