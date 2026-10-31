#!/usr/bin/env python3
"""Pull Thornton building permits (CityView mirrored to ArcGIS Enterprise) into the step 4 format.

Usage:  python3 pull_thornton_building_permits.py [--since YYYY-MM-DD] [--fresh] [--no-zip-fill]

Scope: non-residential permits (BuildingUse COM or SCH) entered on or after --since
(default 2024-01-01), plus non-residential permits entered in 2023 whose Status is still
active (not closed, finaled, expired, denied, file-closed or in warranty).
Residential permits (BuildingUse RES) and Right of Way permits (BuildingUse null: no
description, valuation or work type, mostly homeowner driveway and sidewalk cuts) are
left out and counted.

Query shape: this server answers ORed clauses with an HTML 500 page, so every request is
a date range ANDed with one BuildingUse clause (COM, SCH), and the status filter for 2023
is applied client-side. Pages of 2,000 ordered by OBJECTID, one request a second.

--since  DateEntered cursor (default 2024-01-01). The 2023 active carry-in is always included
         unless --since is later than 2024-01-01, in which case only the window is pulled and
         the result should be de-duplicated on record_id against the earlier file.
--fresh  ignore today's raw cache and refetch.
--no-zip-fill  skip the one supporting query to the Addresses layer that fills missing zips.
Raw pages are cached under ../raw/thornton_building_permits/<window>_<UTC day>/.
"""
import argparse, os, re, shutil, sys
from collections import Counter
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import thornton_common as tc

LAYER = tc.HOST + "/Permits/MapServer/1"
ADDR_LAYER = tc.HOST + "/Permits/MapServer/0"
SOURCE = "Thornton building permits"
SLUG = "thornton_building_permits"
OUT = os.path.join(tc.ADAMS_DIR, "scrape_%s.csv" % SLUG)

# EnteredBy (staff), Contact* (applicant mailing address), LEGALDESC, LOT, BLOCK and the
# always-empty Name and Comments fields are deliberately not requested.
FIELDS = ["OBJECTID", "PermitNumber", "Type", "WorkClass", "Status", "DateEntered", "DateIssued",
          "DateExpiration", "TotalValuation", "TotalSquareFeet", "Description", "BuildingUse",
          "TypeOfWork", "ADDRKEY", "ADDRESS", "UNT", "CITY", "ZIP", "LEGALOWNER", "PIN", "ADCO_PIN",
          "Subdivision", "URA", "CO_DATE", "BUS_NAME", "COMM_TYPE", "NOTES"]

EXTRA_COLS = ["permit_type", "type_of_work", "work_class", "building_use", "status", "date_issued",
              "date_expiration", "co_date", "valuation", "square_feet", "bus_name", "legal_owner",
              "comm_type", "notes", "unit", "parcel_pin", "adco_pin", "subdivision", "ura",
              "address_key", "zip_source", "industrial_word", "industrial_word_field", "address_points", "latitude",
              "longitude", "parser_version"]

ACTIVE_STATUS = {"Open", "Under Review", "In Plan Check", "Pending", "Permit(s) Issued", "Reactivated",
                 "Returned for Correction", "Submittals Incomplete", "Waiting for Payment",
                 "Final Processing", "Waiting for Submittals"}
CONSTRUCTION_TYPES = {"Commercial New", "Commercial Addition", "Commercial Alteration"}
NON_BUILDING_WORK = {"Re-Roof", "Antenna/Cell Tower", "Siding", "Window Replacement", "Structural Repair"}

# Industrial or manufacturing words (brief tier A list plus the process words that fired in the
# Thornton back-test: nitrogen, argon, racking, high-piled storage, fabrication).
INDUSTRIAL = re.compile(
    r"\b(industrial|warehous\w*|manufactur(e|es|ing|er|ers)|plant|"
    r"process (equipment|piping|water|gas|air|line|lines|area|room|skid)|processing (plant|facility|line|equipment|area|room)|"
    r"(food|meat|dairy|beverage|chemical|metal) processing|manufacturing process|"
    r"(process|production|manufacturing|industrial|mechanical|lab|laboratory|packaging|bakery|refrigeration|"
    r"compressed air|owner[- ]furnished|owner|heavy|machine|machinery|shop|plant|welding|cnc) equipment|"
    r"cranes?|tanks?|silos?|compressors?|compressed air|dust collect\w*|paint booths?|spray booths?|booth|"
    r"boilers?|generators?|distribution|logistics|fabricat(ion|ing|or|ors)|machin(e|ing|ery) shop|machining|"
    r"welding|cnc|production|racking|racks|high[- ]pile[d]?|nitrogen|argon|oxygen|hydrogen|cold storage|"
    r"freezers?|refrigerat\w*|laboratory|lab|clean ?room|data cent(er|re)|flex|bakery|brewery|brewing|"
    r"bottling|packaging|conveyors?|loading docks?|dock doors?|batter(y|ies)|kilns?|foundry|extrusion|"
    r"injection mold\w*|hazardous materials?|chemical|solvent|storage/warehouse)\b", re.I)
# TypeOfWork values that are industrial on their own.
INDUSTRIAL_WORK = {"High Piled Storage", "Tank (including generator tanks)", "Hazardous Material",
                   "Generator Commercial", "Boiler", "Refrigeration Unit", "Storage/Warehouse"}


def industrial_hit(at):
    """Return (word, field) for the first industrial word found, searching the fields in a
    fixed order so the rule can say where the evidence came from."""
    tow = tc.clean(at.get("TypeOfWork"))
    if tow in INDUSTRIAL_WORK:
        return tow, "type_of_work"
    for field, key in (("description", "Description"), ("type_of_work", "TypeOfWork"),
                       ("bus_name", "BUS_NAME"), ("comm_type", "COMM_TYPE"),
                       ("legal_owner", "LEGALOWNER"), ("subdivision", "Subdivision"), ("notes", "NOTES")):
        m = INDUSTRIAL.search(tc.clean(at.get(key)))
        if m:
            return m.group(0).lower(), field
    return "", ""


def flag_row(at):
    """Brief tier A / B rules for a permit layer that carries valuation but no zoning or land
    use: the industrial test is a word in the description, work type, business name, owner,
    subdivision or notes."""
    word, field = industrial_hit(at)
    if not word:
        return "N", "", "", ""
    val = at.get("TotalValuation")
    val = float(val) if val is not None else None
    ptype = tc.clean(at.get("Type"))
    tow = tc.clean(at.get("TypeOfWork"))
    evidence = "industrial word '%s' in %s" % (word, field)
    if val is not None and val >= 250000:
        if ptype in CONSTRUCTION_TYPES and tow not in NON_BUILDING_WORK:
            return "Y", "A: valuation 250k+ + %s + %s" % (evidence, ptype), word, field
        return "Y", "A: valuation 250k+ + %s + %s (trade or accessory permit)" % (evidence, ptype), word, field
    if val is not None and val >= 50000:
        return "Y", "B3a: valuation 50k to 250k + %s" % evidence, word, field
    return "Y", "B3b: valuation under 50k or none + %s" % evidence, word, field


def fill_zips_from_addresses(rows, cache_dir):
    """One supporting query (POST, ADDRKEY IN (...)) to the Addresses with COs layer for the
    permit rows that lack a zip but carry an address key. Skipped when it would take more
    than two requests."""
    keys = sorted({r["address_key"] for r in rows if not r["zip"] and r["address_key"]})
    if not keys:
        print("zip fill: nothing to fill")
        return 0
    if len(keys) > 400:
        print("zip fill: %d keys would need more than two requests; skipped" % len(keys))
        return 0
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, "addresses_by_key.json")
    import json
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            wrapped = json.load(f)
    else:
        tc.require_fields(ADDR_LAYER, ["ADDRKEY_1", "ZIP", "ADDRESS"])
        found = {}
        for i in range(0, len(keys), 200):
            chunk = keys[i:i + 200]
            data = tc.http_json(ADDR_LAYER + "/query", {
                "where": "ADDRKEY_1 IN (%s)" % ",".join(chunk), "outFields": "ADDRKEY_1,ZIP,ADDRESS",
                "returnGeometry": "false", "f": "json"}, post=True)
            for ft in data.get("features", []):
                a = ft["attributes"]
                found.setdefault(str(a.get("ADDRKEY_1")), a)
        wrapped = {"fetched_at": tc.now_iso(), "keys": keys, "found": found}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(wrapped, f)
    filled = 0
    for r in rows:
        if not r["zip"] and r["address_key"] in wrapped["found"]:
            z = tc.clean(wrapped["found"][r["address_key"]].get("ZIP"))[:5]
            if z:
                r["zip"], r["zip_source"] = z, "addresses layer by ADDRKEY"
                filled += 1
    print("zip fill: %d of %d missing zips filled from the Addresses layer" % (filled, len(keys)))
    return filled


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--no-zip-fill", action="store_true")
    a = ap.parse_args()
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    raw_root = os.path.join(tc.RAW_ROOT, SLUG)
    tc.require_fields(LAYER, FIELDS)

    windows = []
    if a.since <= "2024-01-01":
        windows.append(("carry2023", "DateEntered >= TIMESTAMP '2023-01-01 00:00:00' AND DateEntered < TIMESTAMP '2024-01-01 00:00:00'"))
    windows.append(("since_" + a.since, "DateEntered >= TIMESTAMP '%s 00:00:00'" % a.since))

    source_counts, feats_by_window = {}, {}
    for wname, wwhere in windows:
        for bu in ("COM", "SCH"):
            where = "%s AND BuildingUse = '%s'" % (wwhere, bu)
            cache = os.path.join(raw_root, "%s_%s_%s" % (wname, bu, day))
            if a.fresh:
                shutil.rmtree(cache, ignore_errors=True)
            n = tc.source_count(LAYER, where)
            source_counts[(wname, bu)] = n
            print("source count %s %s: %d" % (wname, bu, n))
            feats = tc.fetch_all(LAYER, where, FIELDS, cache)
            if len(feats) != n:
                raise SystemExit("ROW COUNT MISMATCH for %s %s: fetched %d, source says %d" % (wname, bu, len(feats), n))
            feats_by_window.setdefault(wname, []).extend(feats)
        # Counts of what is left out, for the notes.
        for label, clause in (("RES", "BuildingUse = 'RES'"), ("ROW_null", "BuildingUse IS NULL")):
            source_counts[(wname, label)] = tc.source_count(LAYER, "%s AND %s" % (wwhere, clause))

    # One permit can sit on several address points (one per unit of a multi-tenant building);
    # keep one row per permit number, preferring the point with an address and no unit.
    by_permit, feature_total = {}, 0
    for wname, feats in feats_by_window.items():
        for f in feats:
            feature_total += 1
            at = f["attributes"]
            pn = tc.clean(at.get("PermitNumber"))
            key = (0 if tc.clean(at.get("ADDRESS")) else 1, 1 if tc.clean(at.get("UNT")) else 0, at.get("OBJECTID") or 0)
            if pn not in by_permit or key < by_permit[pn][0]:
                by_permit[pn] = (key, wname, f, by_permit.get(pn, (None, None, None, 0))[3] + 1)
            else:
                by_permit[pn] = (by_permit[pn][0], by_permit[pn][1], by_permit[pn][2], by_permit[pn][3] + 1)
    dup_points = sum(v[3] - 1 for v in by_permit.values())

    rows, blanked_owner, blanked_bus, dropped_2023 = [], 0, 0, Counter()
    for pn, (_, wname, f, npts) in by_permit.items():
        if True:
            at = f["attributes"]
            status = tc.clean(at.get("Status"))
            if wname == "carry2023" and status not in ACTIVE_STATUS:
                dropped_2023[status] += 1
                continue
            g = f.get("geometry") or {}
            x, y = g.get("x"), g.get("y")
            has_pt = isinstance(x, (int, float)) and isinstance(y, (int, float)) and -106 < x < -104 and 39 < y < 41
            owner, b1 = tc.entity_or_blank(at.get("LEGALOWNER"))
            bus, b2 = tc.entity_or_blank(at.get("BUS_NAME"), business_field=True)
            blanked_owner += b1
            blanked_bus += b2
            if bus:
                company, role = bus, "occupant"
            elif owner:
                company, role = owner, "owner"
            else:
                company, role = "", "unknown"
            flag, rule, word, field = flag_row(at)
            addr = tc.clean(at.get("ADDRESS"))
            rows.append({
                "source": SOURCE, "source_level": "County (Adams)", "record_id": pn,
                "record_date": tc.ms_to_date(at.get("DateEntered")), "date_type": "entered",
                "record_type": tc.clean(at.get("Type")),
                "company_name": company, "company_role": role,
                "site_address": addr, "city": tc.clean(at.get("CITY")).title() or "Thornton", "county": "Adams",
                "zip": tc.clean(at.get("ZIP"))[:5],
                "description": tc.scrub_text(at.get("Description"), 500),
                "flag": flag, "flag_rule": rule,
                "source_url": tc.layer_record_url(LAYER, "PermitNumber='%s'" % pn),
                "retrieved_at": f["_fetched_at"],
                "permit_type": tc.clean(at.get("Type")), "type_of_work": tc.clean(at.get("TypeOfWork")),
                "work_class": tc.clean(at.get("WorkClass")), "building_use": tc.clean(at.get("BuildingUse")),
                "status": status, "date_issued": tc.ms_to_date(at.get("DateIssued")),
                "date_expiration": tc.ms_to_date(at.get("DateExpiration")), "co_date": tc.ms_to_date(at.get("CO_DATE")),
                "valuation": tc.fmt_num(at.get("TotalValuation")), "square_feet": tc.fmt_num(at.get("TotalSquareFeet")),
                "bus_name": bus, "legal_owner": owner, "comm_type": tc.clean(at.get("COMM_TYPE")),
                "notes": tc.scrub_text(at.get("NOTES"), 150), "unit": tc.clean(at.get("UNT")),
                "parcel_pin": tc.clean(at.get("PIN")), "adco_pin": tc.clean(at.get("ADCO_PIN")),
                "subdivision": tc.clean(at.get("Subdivision")), "ura": tc.clean(at.get("URA")),
                "address_key": tc.fmt_num(at.get("ADDRKEY")), "zip_source": "permit" if tc.clean(at.get("ZIP")) else "",
                "industrial_word": word, "industrial_word_field": field,
                "address_points": str(npts),
                "latitude": "%.6f" % y if has_pt else "", "longitude": "%.6f" % x if has_pt else "",
                "parser_version": tc.PARSER_VERSION})
    # Free zip fill: another permit at the same street address.
    zip_by_addr = {}
    for r in rows:
        if r["zip"] and r["site_address"]:
            zip_by_addr.setdefault(r["site_address"].split(" UNIT ")[0].split(" STE ")[0], r["zip"])
    sibling_filled = 0
    for r in rows:
        if not r["zip"] and r["site_address"]:
            z = zip_by_addr.get(r["site_address"].split(" UNIT ")[0].split(" STE ")[0])
            if z:
                r["zip"], r["zip_source"], sibling_filled = z, "other permit at same address", sibling_filled + 1
    if not a.no_zip_fill:
        fill_zips_from_addresses(rows, os.path.join(raw_root, "addresses_%s" % day))
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    tc.write_csv(OUT, tc.COMMON_COLS + EXTRA_COLS, rows)

    print("rows written: %d" % len(rows))
    print("features fetched: %d; distinct permits: %d; extra address points for the same permit: %d" % (feature_total, len(by_permit), dup_points))
    print("zips filled from another permit at the same address: %d" % sibling_filled)
    print("source counts:", dict(source_counts))
    print("2023 rows left out by status (not active):", dict(dropped_2023))
    print("owner names blanked as individuals: %d; business names blanked: %d" % (blanked_owner, blanked_bus))
    print("flag rules:", Counter(r["flag_rule"].split(":")[0] for r in rows if r["flag"] == "Y"))


if __name__ == "__main__":
    main()
