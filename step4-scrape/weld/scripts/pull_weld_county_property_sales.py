#!/usr/bin/env python3
"""Pull Weld County Assessor property sales (Sales_Point_open_data, county wide, every town)
into the step 4 shared format.

Usage:  python3 pull_weld_county_property_sales.py [--since YYYY-MM-DD] [--fresh]

--since  SALEDATE cursor (default 2024-01-01; any other value writes to
         scrape_<slug>_since_<date>.csv so the full file is kept). The default run also carries
         in 2023 sales on industrial parcels (land type Industrial, or an industrial occupancy
         or building description), marked carry_in = Y. For an incremental run pass the last
         record_date already held and de-duplicate on record_id downstream.
--fresh  ignore today's raw cache and refetch.

The layer carries the parties, price, deed, land type, property type, occupancy codes,
building description, size, acreage and situs address in one row, so no joins are needed.
It has no zip field (zip is left blank). Residential sales (SaleType Residential,
residential property types, residential occupancies, vacant residential lots) are left out
and counted. Grantor and grantee are kept only when they read as companies.
Raw pages are cached under raw/weld_county_property_sales/<since>_<UTC day>/.
"""
import argparse, os, re, shutil, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weld_agol_common as wc

LAYER = wc.SALES
SLUG = "weld_county_property_sales"
SOURCE = "Weld County assessor property sales"
OUT = os.path.join(wc.WELD_DIR, "scrape_%s.csv" % SLUG)

FIELDS = ["OBJECTID", "ValuationSale", "RECEPTIONNO", "ACCOUNTNO", "PARCELNO", "AccountsInSale",
          "SaleType", "SALEDATE", "SALEPRICE", "LANDTYPE", "LANDNETACRECOUNT", "PROPERTYTYPE",
          "BLTASDESCRIPTION", "TOTALIMPSF", "COMMERCIALSF", "BLTASYEARBUILT", "CLASSDESCRIPTION",
          "OCCCODE1", "OCCCODE2", "OCCCODE3", "OCCCODEDESCRIPTION1", "OCCCODEDESCRIPTION2",
          "OCCCODEDESCRIPTION3", "SUBDIVISIONNAME", "PROPERTYADDRESS", "PROPERTYCITY", "DEEDCODE",
          "GRANTOR", "GRANTEE", "NBHD"]

EXTRA_COLS = ["sale_price", "grantor", "grantee", "occupancy_code", "occupancy_description",
              "building_sf", "acreage", "parcel_number", "reception_number", "deed_code",
              "latitude", "longitude", "account_number", "accounts_in_sale", "sale_type",
              "land_type", "property_type", "building_description", "construction_class",
              "commercial_sf", "year_built", "subdivision", "neighborhood", "valuation_sale",
              "industrial_use", "carry_in", "bulk_lot_transfer", "parser_version"]

BULK_LOTS = 10   # a vacant, no-occupancy sale covering more than this many accounts is a
                 # subdivision lot transfer between developers: one row per reception

FLAG_PRICE = 2000000
FLAG_RULE = "sale 2M+ on industrial or commercial-industrial parcel"

RES_PROPERTY_TYPES = {"Residential", "Condo", "Duplex", "Triplex", "Townhouse", "Manufactured Hm",
                      "Multiple Unit"}
RES_LAND_TYPES = {"Residential", "Townhouse", "Duplex/Triplex", "Manufactured Hm", "Mfd Home Park",
                  "Multiple Unit"}
RES_OCC = re.compile(r"single family|townhouse|duplex|triplex|condominium|condo - |manufactured home|"
                     r"mobile home|mixed res|secondary single|ranch 1 story|apartment|multiple - |"
                     r"multiple residences|unit conversion|detached garage|purged mh|group care|"
                     r"home for the elderly|dormitory", re.I)
# Industrial occupancy and building descriptions (the assessor has no 'Manufacturing' occupancy
# code; manufacturing shows in BLTASDESCRIPTION as 'Indust Lght Manufacturing' and so on).
IND_OCC = re.compile(r"warehouse|indust|manufacturing|flex|distribution|equipment (building|storage)|"
                     r"comm shed - equipment|quonset|outdoor storage|creamery|grain elevator|"
                     r"maintenance hangar|storage hangar|salvage|material storage|laborator|^tank$|"
                     r"service garage|light commercial - manufacturing|truck", re.I)
NOT_IND = re.compile(r"mini warehouse|warehouse discount|warehouse showroom|mini-warehouse|"
                     r"manufactured home|mnfctrd|mobile home", re.I)

# Server-side clause for the 2023 carry-ins (the local test below is the one that decides).
CARRY_IN_SQL = ("LANDTYPE = 'Industrial' OR OCCCODEDESCRIPTION1 LIKE '%Warehouse%' OR "
                "OCCCODEDESCRIPTION1 LIKE '%Equipment%' OR OCCCODEDESCRIPTION1 LIKE '%Quonset%' OR "
                "OCCCODEDESCRIPTION1 LIKE '%Outdoor Storage%' OR OCCCODEDESCRIPTION1 LIKE '%Salvage%' OR "
                "OCCCODEDESCRIPTION1 LIKE '%Creamery%' OR OCCCODEDESCRIPTION1 LIKE '%Grain Elevator%' OR "
                "OCCCODEDESCRIPTION1 LIKE '%Hangar%' OR OCCCODEDESCRIPTION1 = 'Tank' OR "
                "OCCCODEDESCRIPTION2 LIKE '%Warehouse%' OR OCCCODEDESCRIPTION3 LIKE '%Warehouse%' OR "
                "BLTASDESCRIPTION LIKE '%Indust%' OR BLTASDESCRIPTION LIKE '%Manufacturing%' OR "
                "BLTASDESCRIPTION LIKE '%Warehouse%' OR BLTASDESCRIPTION LIKE '%Flex%' OR "
                "BLTASDESCRIPTION LIKE '%Laborator%' OR BLTASDESCRIPTION LIKE '%Service Garage%' OR "
                "BLTASDESCRIPTION LIKE '%Equipment%' OR BLTASDESCRIPTION LIKE '%Quonset%' OR "
                "BLTASDESCRIPTION LIKE '%Hangar%'")


def is_industrial_text(s):
    s = wc.clean(s)
    return bool(s) and not NOT_IND.search(s) and bool(IND_OCC.search(s))


def industrial_parcel(at):
    """Land type Industrial, or an industrial primary occupancy or building description. The
    secondary occupancies count only when the primary one is not residential: a farmhouse with
    an 'Equipment Building' outbuilding is a house, not a plant."""
    if wc.clean(at.get("LANDTYPE")) == "Industrial":
        return True
    occ1 = wc.clean(at.get("OCCCODEDESCRIPTION1"))
    if is_industrial_text(occ1) or is_industrial_text(at.get("BLTASDESCRIPTION")):
        return True
    if occ1 and RES_OCC.search(occ1):
        return False
    for k in ("OCCCODEDESCRIPTION2", "OCCCODEDESCRIPTION3"):
        if is_industrial_text(at.get(k)):
            return True
    return False


def is_residential(at, industrial):
    """Plainly residential: left out and counted. An industrial signal on the row keeps it."""
    if industrial:
        return False
    st = wc.clean(at.get("SaleType"))
    pt = wc.clean(at.get("PROPERTYTYPE"))
    lt = wc.clean(at.get("LANDTYPE"))
    occ = wc.clean(at.get("OCCCODEDESCRIPTION1"))
    if st == "Residential":
        return True
    if pt in RES_PROPERTY_TYPES and st != "Commercial":
        return True
    if occ and RES_OCC.search(occ) and st != "Commercial":
        return True
    if not pt and lt in RES_LAND_TYPES:          # vacant residential lot
        return True
    return False


def occ_codes(at):
    codes, descs = [], []
    for i in (1, 2, 3):
        c, d = at.get("OCCCODE%d" % i), wc.clean(at.get("OCCCODEDESCRIPTION%d" % i))
        if c is not None and c != "":
            codes.append("%d" % c if float(c).is_integer() else "%g" % c)
        if d and d not in descs:
            descs.append(d)
    return "; ".join(codes), "; ".join(descs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2024-01-01")
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    out = OUT if a.since == "2024-01-01" else OUT.replace(".csv", "_since_%s.csv" % a.since)
    day = wc.today().replace("-", "")
    cache = os.path.join(wc.RAW_ROOT, SLUG, "%s_%s" % (a.since, day))
    if a.fresh:
        shutil.rmtree(cache, ignore_errors=True)

    wc.require_fields(LAYER, FIELDS)
    where = "SALEDATE >= DATE '%s'" % a.since
    n_source = wc.source_count(LAYER, where)
    print("source count for filter:", n_source)
    feats = wc.fetch_all(LAYER, where, FIELDS, os.path.join(cache, "sales"), geometry=True)
    if len(feats) != n_source:
        raise SystemExit("ROW COUNT MISMATCH against source: %d fetched, %d expected" % (len(feats), n_source))
    n_carry_source, carry = 0, []
    if a.since <= "2024-01-01":
        cwhere = ("SALEDATE >= DATE '2023-01-01' AND SALEDATE < DATE '%s' AND (%s)" % (a.since, CARRY_IN_SQL))
        n_carry_source = wc.source_count(LAYER, cwhere)
        print("source count for 2023 carry-in filter:", n_carry_source)
        carry = wc.fetch_all(LAYER, cwhere, FIELDS, os.path.join(cache, "carry_in_2023"), geometry=True)
        if len(carry) != n_carry_source:
            raise SystemExit("ROW COUNT MISMATCH on carry-ins: %d fetched, %d expected" % (len(carry), n_carry_source))
        for f in carry:
            f["_carry"] = True

    rows, residential, carry_dropped, blank_grantee, blank_grantor, rules = [], Counter(), 0, 0, 0, Counter()
    ids = Counter()
    for f in feats + carry:
        at = f["attributes"]
        industrial = industrial_parcel(at)
        if f.get("_carry") and not industrial:
            carry_dropped += 1                # server LIKE matched a non-industrial string
            continue
        if is_residential(at, industrial):
            residential[wc.clean(at.get("PROPERTYTYPE")) or ("vacant " + (wc.clean(at.get("LANDTYPE")) or "lot"))] += 1
            continue
        grantee, b = wc.company_or_blank(at.get("GRANTEE"))
        blank_grantee += b
        grantor, b = wc.company_or_blank(at.get("GRANTOR"))
        blank_grantor += b
        price = at.get("SALEPRICE")
        flag, rule = "N", ""
        if price is not None and price >= FLAG_PRICE and industrial:
            flag, rule = "Y", FLAG_RULE
        rules[rule] += 1
        codes, descs = occ_codes(at)
        rec = wc.clean(at.get("RECEPTIONNO"))
        acct = wc.clean(at.get("ACCOUNTNO"))
        rid = "%s/%s" % (rec or "OBJECTID-%s" % at.get("OBJECTID"), acct)
        ids[rid] += 1
        lt, pt, st = wc.clean(at.get("LANDTYPE")), wc.clean(at.get("PROPERTYTYPE")), wc.clean(at.get("SaleType"))
        bld = wc.clean(at.get("BLTASDESCRIPTION"))
        parts = ["%s deed, %s" % (wc.clean(at.get("DEEDCODE")) or "unknown", ("$" + wc.money(price)) if price is not None else "no price")]
        if grantor:
            parts[0] += " from " + grantor
        parts.append("sale type %s" % (st or "unknown"))
        if lt:
            parts.append("land type %s" % lt)
        if pt:
            parts.append("property type %s" % pt)
        if descs:
            parts.append("occupancy %s" % descs)
        if bld:
            parts.append("building %s" % bld)
        if at.get("TOTALIMPSF"):
            parts.append("%s sf" % wc.num(at.get("TOTALIMPSF"), "%.0f"))
        if at.get("LANDNETACRECOUNT"):
            parts.append("%s ac" % wc.num(at.get("LANDNETACRECOUNT"), "%.2f"))
        if at.get("BLTASYEARBUILT"):
            parts.append("built %s" % at.get("BLTASYEARBUILT"))
        if at.get("AccountsInSale") and at.get("AccountsInSale") > 1:
            parts.append("%d accounts in sale" % at.get("AccountsInSale"))
        g = f.get("geometry") or {}
        rows.append({
            "source": SOURCE, "source_level": wc.SOURCE_LEVEL, "record_id": rid,
            "record_date": wc.ms_to_date(at.get("SALEDATE")), "date_type": "sale",
            "record_type": "property sale",
            "company_name": grantee, "company_role": "grantee" if grantee else "unknown",
            "site_address": wc.clean(at.get("PROPERTYADDRESS")), "city": wc.weld_city(at.get("PROPERTYCITY")),
            "county": wc.COUNTY, "zip": "",
            "description": wc.clean("; ".join(parts), 500), "flag": flag, "flag_rule": rule,
            "source_url": wc.layer_query_url(LAYER, "RECEPTIONNO='%s' AND ACCOUNTNO='%s'" % (rec, acct)),
            "retrieved_at": f["_fetched_at"],
            "sale_price": wc.money(price), "grantor": grantor, "grantee": grantee,
            "occupancy_code": codes, "occupancy_description": descs,
            "building_sf": wc.num(at.get("TOTALIMPSF"), "%.0f"), "acreage": wc.num(at.get("LANDNETACRECOUNT"), "%.4f"),
            "parcel_number": wc.clean(at.get("PARCELNO")), "reception_number": rec,
            "deed_code": wc.clean(at.get("DEEDCODE")),
            "latitude": "%.6f" % g["y"] if g.get("y") is not None else "",
            "longitude": "%.6f" % g["x"] if g.get("x") is not None else "",
            "account_number": acct, "accounts_in_sale": wc.num(at.get("AccountsInSale"), "%d"),
            "sale_type": st, "land_type": lt, "property_type": pt, "building_description": bld,
            "construction_class": wc.clean(at.get("CLASSDESCRIPTION")),
            "commercial_sf": wc.num(at.get("COMMERCIALSF"), "%.0f"), "year_built": wc.num(at.get("BLTASYEARBUILT"), "%d"),
            "subdivision": wc.clean(at.get("SUBDIVISIONNAME")), "neighborhood": wc.clean(at.get("NBHD")),
            "valuation_sale": wc.clean(at.get("ValuationSale")),
            "industrial_use": "Y" if industrial else "N", "carry_in": "Y" if f.get("_carry") else "N",
            "bulk_lot_transfer": "N", "parser_version": wc.PARSER_VERSION})

    # Collapse bulk subdivision lot transfers (vacant, no occupancy, many accounts on one
    # reception) to one row per reception so 40 developer-to-developer deeds do not become
    # 8,000 rows. The collapsed row keeps the lot count, the subdivision and the land types.
    groups = {}
    for r in rows:
        if not r["property_type"] and not r["occupancy_description"]:
            groups.setdefault(r["reception_number"], []).append(r)
    bulk_rows, bulk_receptions = 0, 0
    collapsed = []
    for r in rows:
        grp = groups.get(r["reception_number"]) if r["reception_number"] else None
        if grp and len(grp) > BULK_LOTS:
            if r is grp[0]:
                bulk_receptions += 1
                r = dict(r)
                lts = Counter(x["land_type"] or "unknown" for x in grp)
                subs = Counter(x["subdivision"] for x in grp if x["subdivision"])
                acres = sum(float(x["acreage"]) for x in grp if x["acreage"])
                r["record_id"] = "%s/BULK" % r["reception_number"]
                r["record_type"] = "property sale (bulk lot transfer)"
                r["site_address"] = ""
                r["accounts_in_sale"] = "%d" % len(grp)
                r["acreage"] = "%.4f" % acres if acres else ""
                r["parcel_number"] = "; ".join(x["parcel_number"] for x in grp[:5]) + (" and %d more" % (len(grp) - 5) if len(grp) > 5 else "")
                r["bulk_lot_transfer"] = "Y"
                r["industrial_use"] = "Y" if any(x["industrial_use"] == "Y" for x in grp) else "N"
                if r["industrial_use"] == "Y" and r["sale_price"] and float(r["sale_price"]) >= FLAG_PRICE:
                    r["flag"], r["flag_rule"] = "Y", FLAG_RULE
                r["description"] = wc.clean("bulk transfer of %d accounts in one deed (%s); %s; land types %s; %s" % (
                    len(grp), r["description"].split(";")[0], "subdivision " + "; ".join(k for k, _ in subs.most_common(3)) if subs else "unplatted",
                    ", ".join("%s %d" % (k, v) for k, v in lts.most_common()), "%.2f ac in all" % acres if acres else "acreage not given"), 500)
                r["source_url"] = wc.layer_query_url(LAYER, "RECEPTIONNO='%s'" % r["reception_number"])
                collapsed.append(r)
            bulk_rows += 1
            continue
        collapsed.append(r)
    rules = Counter(r["flag_rule"] for r in collapsed)
    print("bulk lot transfers: %d rows collapsed into %d reception rows" % (bulk_rows, bulk_receptions))
    rows = collapsed
    rows.sort(key=lambda r: (r["record_date"], r["record_id"]))
    wc.write_csv(out, wc.COMMON_COLS + EXTRA_COLS, rows)
    print("rows written: %d of %d sales in the source filter (+ %d carry-in candidates, %d dropped as not industrial)"
          % (len(rows), n_source, n_carry_source, carry_dropped))
    print("residential sales left out: %d  %s" % (sum(residential.values()), residential.most_common()))
    print("grantee names blanked (whole or part) as individuals: %d; grantor: %d" % (blank_grantee, blank_grantor))
    print("flag rules:", rules.most_common())
    print("industrial_use:", Counter(r["industrial_use"] for r in rows))
    print("carry-ins written:", sum(1 for r in rows if r["carry_in"] == "Y"))
    dups = {k: v for k, v in ids.items() if v > 1}
    print("duplicate record_ids:", len(dups), list(dups.items())[:5])


if __name__ == "__main__":
    main()
