#!/usr/bin/env python3
"""Pull Denver "Active Business Licenses" (open data, ArcGIS REST), TYPE = Business only.

Usage: python3 pull_denver_business_licenses.py [out.csv]
Layer: https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_active_business_licenses/FeatureServer/42
Paged by OBJECTID, 2,000 a page, one request a second. The individual-licence layers are not touched.
"""
import csv, json, sys, time, urllib.parse, urllib.request
B = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_active_business_licenses/FeatureServer/42/query"
F = ["OBJECTID", "BFN", "LICENSE_TYPE", "LICENSE_SUB_TYPE", "LICENSE_STATUS", "ENTITY_NAME", "TRADE_NAME", "Application_Date", "Expiration_Date", "ADDRESS", "ZIP", "PRIMARY_ADDRESS_FLAG", "TYPE", "AddressNoUnit"]

def get(params):
    req = urllib.request.Request(B + "?" + urllib.parse.urlencode(params), headers={"User-Agent": "step5c-research-pull/1.0"})
    return json.load(urllib.request.urlopen(req, timeout=60))

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "denver_business_licenses.csv"
    want = get({"where": "TYPE='Business'", "returnCountOnly": "true", "f": "json"})["count"]
    rows, last = [], 0
    while True:
        d = get({"where": "TYPE='Business' AND OBJECTID>%d" % last, "outFields": ",".join(F), "orderByFields": "OBJECTID", "resultRecordCount": 2000, "returnGeometry": "false", "f": "json"})
        fs = d.get("features", [])
        if not fs:
            break
        for f in fs:
            a = f["attributes"]
            for k in ("Application_Date", "Expiration_Date"):
                a[k] = time.strftime("%Y-%m-%d", time.gmtime(a[k] / 1000)) if a.get(k) else ""
            rows.append(a)
        last = fs[-1]["attributes"]["OBJECTID"]
        time.sleep(1.0)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=F); w.writeheader(); w.writerows(rows)
    print("source count %d, rows written %d" % (want, len(rows)))
    if want != len(rows):
        sys.exit("count mismatch")

if __name__ == "__main__":
    main()
