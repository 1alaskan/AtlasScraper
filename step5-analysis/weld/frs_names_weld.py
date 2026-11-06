#!/usr/bin/env python3
"""Name the unattached Weld addresses scoring 40 or more from the EPA facility registry (frs_filtered.csv, method step 7).

Join: county WELD (or WELD COUNTY) and the same house number plus street name (street type and direction words dropped). The registry
name goes into a new `weld_frs_names.csv` and is appended to `next_step` on the ranked row; a registry record can be a former occupant,
so it is a lead, not a confirmation. Registry records whose facility name reads as a person are left out. Parcel owner names are not used.

Usage: python3 frs_names_weld.py <v3 output folder> <repo root>   (rewrites <out>/weld_ranked_accounts_v3.csv in place, writes weld_frs_names.csv beside it)
"""
import csv, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v3", "scripts"))


def akey(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", (s or "").upper())
    s = re.sub(r"\b(COUNTY ROAD|CR|WCR|WELD COUNTY ROAD)\b", "CR", s)
    s = re.sub(r"\b(STREET|ST|AVENUE|AVE|DRIVE|DR|ROAD|RD|BOULEVARD|BLVD|PARKWAY|PKWY|PLACE|PL|COURT|CT|LANE|LN|HIGHWAY|HWY|CIRCLE|CIR|WAY|NORTH|N|SOUTH|S|EAST|E|WEST|W)\b", " ", s)
    s = re.sub(r"\b(SUITE|STE|UNIT|BLDG|BUILDING)\b.*$", "", s)
    m = re.match(r"\s*(\d+)\s+([A-Z0-9 ]+)", s)
    return (m.group(1) + " " + re.sub(r"\s+", " ", m.group(2)).strip()) if m else ""


PERSON = re.compile(r"^[A-Z][A-Z'-]+,? [A-Z][A-Z'-]+( [A-Z]\.?)?$")
BIZ = re.compile(r"\b(LLC|INC|CORP|CO|COMPANY|LTD|LP|LLP|LLLP|FARMS?|RANCH|DAIRY|ENERGY|OIL|GAS|RESOURCES|OPERATING|PETROLEUM|MIDSTREAM|SERVICES|INDUSTRIES|MANUFACTURING|PRODUCTS|FOODS|BREWING|SYSTEMS|TECHNOLOGIES|PLANT|FACILITY|STATION|TERMINAL|PIT|MINE|CENTER|DISTRICT|CITY|TOWN|COUNTY|SCHOOL|HOSPITAL|AIRPORT)\b")


def main():
    out, root = sys.argv[1], sys.argv[2]
    frs = {}
    for r in csv.DictReader(open(os.path.join(root, "frs_filtered.csv"))):
        if r["state"] != "CO" or not r["county"].upper().startswith("WELD"):
            continue
        k = akey(r["street"])
        if not k:
            continue
        nm = r["facility_name"].strip()
        if PERSON.match(nm) and not BIZ.search(nm):
            continue
        frs.setdefault(k, []).append(r)
    path = os.path.join(out, "weld_ranked_accounts_v3.csv")
    rows = list(csv.DictReader(open(path)))
    cols = list(rows[0].keys())
    named = []
    for r in rows:
        if not r["company_name"].startswith("Unattached address"):
            continue
        try:
            if float(r["score"]) < 40:
                continue
        except ValueError:
            continue
        hits = frs.get(akey(r["site_address"]), [])
        if not hits:
            continue
        names = sorted(set(h["facility_name"].strip() for h in hits))
        naics = sorted(set(h["naics_primary"] for h in hits if h["naics_primary"]))
        note = "EPA facility registry at this address: %s%s (may be a former occupant)" % ("; ".join(names)[:200], (" [NAICS %s]" % ", ".join(naics)) if naics else "")
        if note not in r["next_step"]:
            r["next_step"] = (r["next_step"] + " || " if r["next_step"] else "") + note
        named.append(dict(rank=r["rank"], site_address=r["site_address"], zip=r["zip"], epa_registry_facility_names="; ".join(names), naics_primary=", ".join(naics), ranked_row_label=r["company_name"][:80]))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    with open(os.path.join(out, "weld_frs_names.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rank", "site_address", "zip", "epa_registry_facility_names", "naics_primary", "ranked_row_label"]); w.writeheader(); w.writerows(named)
    unatt = sum(1 for r in rows if r["company_name"].startswith("Unattached address") and float(r["score"] or 0) >= 40)
    print("unattached addresses scoring 40+: %d; named from the registry: %d" % (unatt, len(named)))
    for n in named:
        print("  rank %s %s -> %s" % (n["rank"], n["site_address"], n["epa_registry_facility_names"][:70]))


if __name__ == "__main__":
    main()
