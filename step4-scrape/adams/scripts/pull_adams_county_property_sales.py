#!/usr/bin/env python3
"""Pull Adams County Assessor Property Sales (ArcGIS Online table) for sales on commercial,
industrial or vacant commercial/industrial parcels, into the step 4 shared format.

Usage:  python3 pull_adams_county_property_sales.py [--since YYYY-MM-DD] [--fresh]

--since  saledt cursor (default 2024-01-01). For an incremental run pass the last record_date
         already held and de-duplicate on record_id downstream.
--fresh  ignore today's raw cache and refetch.

Joins (all on the assessor parcel number, parcelnb / PARCELNB):
  Property_Values   ACCTTYPE (Residential, Commercial, Industrial, Agricultural, Exempt, State
                    Assessed, Possessory, Producing Mine) and VACIMP (V vacant, I improved). This
                    is the county's land-use class; the Parcels layer itself carries no land use.
  Parcels           site address, city, zip, subdivision, and the parcel centroid (owner fields
                    are never requested).
  Zoning            county zoning polygon at the centroid: I-1/I-2/I-3 and C-x for unincorporated
                    parcels, the city name for parcels inside a city (the county layer carries no
                    city zoning).
  Property_Improvements  building descriptions (Distribution Warehouse, Indust Lght Manufacturing
                    and so on) for the commercial-industrial test.

Residential parcels (ACCTTYPE Residential) are left out entirely and counted. Agricultural,
Exempt and other non-residential, non-commercial parcels are kept only when the county zoning at
the centroid is industrial or commercial.
Raw pages are cached under raw/adams_county_property_sales/.
"""
import argparse, os, re, shutil, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc_common as cc

SALES = cc.ADAMS_HOST + "/Property_Sales/FeatureServer/0"
VALUES = cc.ADAMS_HOST + "/Property_Values/FeatureServer/0"
PARCELS = cc.ADAMS_HOST + "/Parcels/FeatureServer/0"
IMPROVEMENTS = cc.ADAMS_HOST + "/Property_Improvements/FeatureServer/0"
SLUG = "adams_county_property_sales"
SOURCE = "Adams County assessor property sales"
OUT = os.path.join(cc.ADAMS_DIR, "scrape_%s.csv" % SLUG)

SALES_FIELDS = ["OBJECTID", "accountno", "parcelnb", "recptno", "deedtype", "saledt", "grantor",
                "grantee", "docfee", "docdt", "pin", "salep"]
VALUES_FIELDS = ["PARCELNB", "ACCOUNTNO", "ACCTTYPE", "VACIMP", "LOTSIZE", "LOTMEASURE", "ACTTOTALVAL"]
PARCEL_FIELDS = ["PARCELNB", "PIN", "CONCATADDR1", "CONCATADDR2", "LOCCITY", "LOCZIP", "SUBNAME"]
IMPROV_FIELDS = ["parcelnb", "bltasdesc", "proptype", "yrblt", "sf"]

EXTRA_COLS = ["sale_price", "grantor", "grantee", "deed_type", "recording_date", "reception_number",
              "account_number", "parcel_number", "land_use", "vacant_or_improved", "lot_size",
              "lot_measure", "actual_total_value", "zoning", "zoning_class", "jurisdiction",
              "improvements", "industrial_use", "keep_reason", "subdivision", "latitude", "longitude",
              "parser_version"]

FLAG_PRICE = 2000000
KEEP_USE = {"Commercial", "Industrial"}
INDUSTRIAL_BLDG = re.compile(r"warehouse|manufactur|industrial|flex|distribution|cold storage|"
                             r"equipment|lumber|storage hanger|maintenance hanger|creamery|bulk oil|"
                             r"grain|laborator|computer cent|research|service garage|truck|"
                             r"prefab metal|quonset|hoop|transit", re.I)


def money(v):
    if v is None:
        return ""
    return "%d" % v if float(v).is_integer() else "%.2f" % v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    day = cc.now_iso()[:10].replace("-", "")
    root = os.path.join(cc.RAW_ROOT, SLUG)
    cache = os.path.join(root, "sales_%s_%s" % (a.since, day))
    ref = os.path.join(root, "reference_%s" % day)
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)
        shutil.rmtree(ref, ignore_errors=True)

    where = "saledt >= DATE '%s'" % a.since
    cc.require_fields(SALES, SALES_FIELDS)
    cc.require_fields(VALUES, VALUES_FIELDS)
    cc.require_fields(PARCELS, PARCEL_FIELDS)
    cc.require_fields(IMPROVEMENTS, IMPROV_FIELDS)
    n_source = cc.source_count(SALES, where)
    print("source count for filter:", n_source)
    sales = cc.fetch_all(SALES, where, SALES_FIELDS, cache, geometry=False)
    if len(sales) != n_source:
        raise SystemExit("ROW COUNT MISMATCH against source: %d fetched, %d expected" % (len(sales), n_source))

    # Land-use spine: the whole Property_Values table (one row per account), parcel number keyed.
    n_values = cc.source_count(VALUES, "1=1")
    values = cc.fetch_all(VALUES, "1=1", VALUES_FIELDS, os.path.join(ref, "property_values"), geometry=False)
    if len(values) != n_values:
        raise SystemExit("Property_Values: got %d rows, source says %d" % (len(values), n_values))
    use_by_parcel = {}
    for f in values:
        at = f["attributes"]
        pn = cc.clean(at.get("PARCELNB"))
        # a parcel with several accounts: prefer the non-residential account's class
        cur = use_by_parcel.get(pn)
        if cur is None or (cur["ACCTTYPE"] == "Residential" and at.get("ACCTTYPE") != "Residential"):
            use_by_parcel[pn] = at

    # First cut by land use class.
    residential, candidates, left_out = 0, [], Counter()
    for f in sales:
        pn = cc.clean(f["attributes"].get("parcelnb"))
        v = use_by_parcel.get(pn)
        use = cc.clean(v.get("ACCTTYPE")) if v else ""
        if use == "Residential":
            residential += 1
            continue
        candidates.append((f, v, use))
    print("sales on residential parcels left out:", residential)

    # Parcel address and centroid, then county zoning at the centroid, for every candidate.
    zoning = cc.load_county_zoning(ref)
    parcels = cc.fetch_by_keys(PARCELS, "PARCELNB", [cc.clean(f["attributes"].get("parcelnb")) for f, _, _ in candidates],
                               PARCEL_FIELDS, os.path.join(ref, "parcels"), batch=100,
                               extra={"returnCentroid": "true"})
    kept = []
    for f, v, use in candidates:
        pn = cc.clean(f["attributes"].get("parcelnb"))
        p = (parcels.get(pn) or [None])[0]
        z = zoning.find(p.get("_cx"), p.get("_cy")) if p else None
        zone = cc.clean(z.get("ZONE_")) if z else ""
        juris = cc.clean(z.get("CITY_NAME")) if z else ""
        zclass = cc.county_zone_class(zone) if juris == "Unincorporated" else ""
        if use in KEEP_USE:
            reason = "land use %s" % use.lower()
        elif zclass:
            reason = "county zoning %s (%s)" % (zone, zclass)
        else:
            left_out[use or "(no assessor account)"] += 1
            continue
        kept.append((f, v, use, p, zone, zclass, juris, reason))
    print("non-residential sales left out by land use (no commercial or industrial zoning):", left_out.most_common())

    improv = cc.fetch_by_keys(IMPROVEMENTS, "parcelnb", [cc.clean(f["attributes"].get("parcelnb")) for f, *_ in kept],
                              IMPROV_FIELDS, os.path.join(ref, "improvements"), batch=100)

    rows, blank_grantee, blank_grantor, rules = [], 0, 0, Counter()
    for f, v, use, p, zone, zclass, juris, reason in kept:
        at = f["attributes"]
        pn = cc.clean(at.get("parcelnb"))
        grantee = cc.clean(at.get("grantee"))
        grantor = cc.clean(at.get("grantor"))
        if grantee and cc.looks_like_individual_party(grantee):
            grantee, blank_grantee = "", blank_grantee + 1
        if grantor and cc.looks_like_individual_party(grantor):
            grantor, blank_grantor = "", blank_grantor + 1
        bldgs = []
        for b in improv.get(pn, []):
            d = cc.clean(b.get("bltasdesc"))
            if d:
                bldgs.append("%s%s%s" % (d, " %s sf" % b["sf"] if b.get("sf") else "",
                                         " (%s)" % b["yrblt"] if b.get("yrblt") else ""))
        bldg_text = "; ".join(bldgs)
        industrial = (use == "Industrial" or zclass == "industrial" or bool(INDUSTRIAL_BLDG.search(bldg_text)))
        price = at.get("salep")
        flag, rule = "N", ""
        if price is not None and price >= FLAG_PRICE and industrial:
            flag, rule = "Y", "sale 2M+ on industrial or commercial-industrial parcel"
        rules[rule] += 1
        addr = cc.clean(p.get("CONCATADDR1")) if p else ""
        addr2 = cc.clean(p.get("CONCATADDR2")) if p else ""
        city = cc.clean(p.get("LOCCITY")) if p else ""
        if not city and addr2:
            city = re.sub(r"\s+CO$", "", addr2, flags=re.I)
        if not city:
            city = juris or ""
        city = "Unincorporated Adams County" if city.lower() in ("unincorporated", "unincorporated adams county") else city.title()
        vac = cc.clean(v.get("VACIMP")) if v else ""
        desc = "%s deed, %s%s, land use %s%s%s" % (
            cc.clean(at.get("deedtype")) or "unknown", "$" + money(price) if price is not None else "no price",
            "" if not grantor else " from " + grantor, use or "unknown",
            {"V": " (vacant)", "I": " (improved)"}.get(vac, ""), "; buildings: " + bldg_text if bldg_text else "")
        rid = cc.clean(at.get("recptno")) or "%s-%s" % (pn, cc.ms_to_date(at.get("saledt")))
        rows.append({
            "source": SOURCE, "source_level": cc.SOURCE_LEVEL, "record_id": "%s/%s" % (rid, pn),
            "record_date": cc.ms_to_date(at.get("saledt")), "date_type": "sale",
            "record_type": "property sale (%s)" % (cc.clean(at.get("deedtype")) or "deed"),
            "company_name": grantee, "company_role": "grantee" if grantee else "unknown",
            "site_address": addr, "city": city, "county": cc.COUNTY,
            "zip": (cc.clean(p.get("LOCZIP"))[:5] if p else ""),
            "description": cc.clean(desc, 500), "flag": flag, "flag_rule": rule,
            "source_url": cc.layer_query_url(SALES, "recptno='%s' AND parcelnb='%s'" % (cc.clean(at.get("recptno")), pn)),
            "retrieved_at": f["_fetched_at"],
            "sale_price": money(price), "grantor": grantor, "grantee": grantee,
            "deed_type": cc.clean(at.get("deedtype")), "recording_date": cc.ms_to_date(at.get("docdt")),
            "reception_number": cc.clean(at.get("recptno")), "account_number": cc.clean(at.get("accountno")),
            "parcel_number": pn, "land_use": use, "vacant_or_improved": {"V": "vacant", "I": "improved"}.get(vac, ""),
            "lot_size": "" if not v or v.get("LOTSIZE") is None else "%g" % v["LOTSIZE"],
            "lot_measure": cc.clean(v.get("LOTMEASURE")) if v else "",
            "actual_total_value": "" if not v or v.get("ACTTOTALVAL") is None else "%d" % v["ACTTOTALVAL"],
            "zoning": zone if juris == "Unincorporated" else "", "zoning_class": zclass,
            "jurisdiction": juris, "improvements": bldg_text[:500], "industrial_use": "Y" if industrial else "N",
            "keep_reason": reason, "subdivision": cc.clean(p.get("SUBNAME")) if p else "",
            "latitude": "%.6f" % p["_cy"] if p and p.get("_cy") else "",
            "longitude": "%.6f" % p["_cx"] if p and p.get("_cx") else "",
            "parser_version": cc.PARSER_VERSION})
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    cc.write_csv(OUT, cc.COMMON_COLS + EXTRA_COLS, rows)
    print("rows written: %d of %d sales in the source filter" % (len(rows), n_source))
    print("grantee names blanked as individuals: %d; grantor names blanked: %d" % (blank_grantee, blank_grantor))
    print("flag rules:", rules.most_common())
    print("keep reasons:", Counter(r["keep_reason"] for r in rows).most_common())


if __name__ == "__main__":
    main()
