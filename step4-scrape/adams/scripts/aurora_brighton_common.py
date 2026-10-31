"""Shared helpers for the Adams County `aurora_brighton` scrape group (step 4).

Standard library only. Paged ArcGIS and Legistar fetches with a raw JSON cache on
disk, a point-in-polygon join for Aurora zoning, state plane to lon/lat, and the
CSV writer with the 17 common columns first.
"""
import csv, json, math, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

UA = "step4-research-pull/1.0"
PAUSE = 1.0
MAX_ERRORS = 3
PARSER_VERSION = "aurora_brighton-1.0"

HERE = os.path.dirname(os.path.abspath(__file__))
ADAMS_DIR = os.path.dirname(HERE)
RAW_ROOT = os.path.join(ADAMS_DIR, "raw")

AURORA = "https://ags.auroragov.org/aurora/rest/services/OpenData/MapServer"
ZONING_LAYER = AURORA + "/20"
COLFAX_Y = 1695150.0   # Colorado Central state plane feet; north of this line is Adams County

COMMON_COLS = ["source", "source_level", "record_id", "record_date", "date_type",
               "record_type", "company_name", "company_role", "site_address", "city",
               "county", "zip", "description", "flag", "flag_rule", "source_url",
               "retrieved_at"]

INDUSTRIAL_WORDS = re.compile(
    r"\b(INDUSTRIAL|WAREHOUSE|WAREHOUSING|MANUFACTUR\w*|PLANT|PROCESS\w*|EQUIPMENT|CRANE|CRANES|"
    r"TANKS?|SILOS?|COMPRESS\w*|DUST COLLECT\w*|PAINT BOOTH|SPRAY BOOTH|BOILERS?|GENERATORS?|"
    r"DISTRIBUTION|LOGISTICS|FACTORY|FABRICAT\w*|COLD STORAGE|DATA CENTER|RACKING|"
    r"CONVEYORS?|FORKLIFT|MEZZANINE|LOADING DOCK|DOCK DOORS?|TRUCK|FLEX|MACHINE SHOP|MACHINERY|"
    r"BREWERY|BREWING|FOOD PRODUCTION|COMMISSARY|BOTTLING|PACKAGING|CNC|WELDING|FUEL STORAGE|"
    r"HAZARDOUS|HIGH PILED|CLEAN ?ROOM|LAB(ORATORY)?|SUBSTATION|FULFILLMENT|SORTATION|"
    r"CROSS[- ]?DOCK|SPEC BUILDING|SHELL BUILDING)\b", re.I)

CORP_SUFFIX = re.compile(r"\b(?<![-/])(LLC|L\.L\.C\.|INC\.?|INCORPORATED|CORP\.?|CORPORATION|CO\.|COMPANY|"
                         r"LTD\.?|LIMITED|LP|L\.P\.|LLP|PLC|GMBH|HOLDINGS|GROUP|PARTNERS|ENTERPRISES|"
                         r"INDUSTRIES|LOGISTICS|PROPERTIES|AUTHORITY|DISTRICT|"
                         r"BANK|CHURCH|SCHOOL|ASSOCIATION|ASSOCIATES|SERVICES|SYSTEMS|"
                         r"TECHNOLOGIES|SOLUTIONS|BREWING|SUPPLY|USA|INTERNATIONAL)\b", re.I)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_json(url, params=None, max_errors=MAX_ERRORS, backoff=5):
    """GET with identifying UA, a pause, and a hard stop on repeated errors.
    A 403 (Cloudflare) is raised as HttpRefused so the caller can change the query shape
    in a documented way instead of hammering."""
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    errors = 0
    while True:
        try:
            req = urllib.request.Request(full, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read().decode("utf-8")
            data = json.loads(body)
            if isinstance(data, dict) and "error" in data:
                raise RuntimeError("ArcGIS error: %s" % data["error"])
            time.sleep(PAUSE)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 403:
                time.sleep(PAUSE)
                raise HttpRefused("HTTP 403 on %s" % full[:200])
            errors += 1
            print("  request failed (%d/%d): %s" % (errors, max_errors, e), file=sys.stderr)
        except Exception as e:  # noqa
            errors += 1
            print("  request failed (%d/%d): %s" % (errors, max_errors, e), file=sys.stderr)
        if errors >= max_errors:
            raise SystemExit("Stopping after repeated errors on %s" % url)
        time.sleep(backoff * errors)


class HttpRefused(Exception):
    pass


def cached(path, fetch):
    """Return the JSON at path, or call fetch() and store {"fetched_at", "response"}."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    data = fetch()
    wrapped = {"fetched_at": now_iso(), "response": data}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(wrapped, f)
    os.replace(tmp, path)
    return wrapped


def arcgis_count(layer_url, where):
    return http_json(layer_url + "/query", {"where": where, "returnCountOnly": "true", "f": "json"})["count"]


def arcgis_fetch(layer_url, where, out_fields, cache_dir, tag, page_size=2000, geometry=True, out_sr=None):
    """Page one where clause with resultOffset. Each page cached as <tag>_pNNNN.json."""
    feats, offset, page = [], 0, 0
    while True:
        path = os.path.join(cache_dir, "%s_p%04d.json" % (tag, page))

        def fetch(offset=offset):
            params = {"where": where, "outFields": ",".join(out_fields), "orderByFields": "OBJECTID",
                      "resultOffset": offset, "resultRecordCount": page_size,
                      "returnGeometry": "true" if geometry else "false", "f": "json"}
            if out_sr:
                params["outSR"] = out_sr
            return http_json(layer_url + "/query", params)
        wrapped = cached(path, fetch)
        got = wrapped["response"].get("features", [])
        for g in got:
            g["_fetched_at"] = wrapped["fetched_at"]
        feats.extend(got)
        print("  %s page %d: %d rows (total %d)" % (tag, page, len(got), len(feats)))
        if not got or not wrapped["response"].get("exceededTransferLimit"):
            break
        offset += len(got)
        page += 1
    return feats


def require_fields(layer_url, wanted):
    meta = http_json(layer_url, {"f": "json"})
    have = {f["name"] for f in meta["fields"]}
    missing = [w for w in wanted if w not in have]
    if missing:
        raise SystemExit("Schema drift on %s: missing fields %s" % (layer_url, missing))
    return meta


def month_ranges(start, end):
    """Yield (a, b) ISO date pairs covering [start, end) one calendar month at a time."""
    y, m = int(start[:4]), int(start[5:7])
    while True:
        a = "%04d-%02d-01" % (y, m)
        y2, m2 = (y + 1, 1) if m == 12 else (y, m + 1)
        b = "%04d-%02d-01" % (y2, m2)
        if a >= end:
            return
        yield a, min(b, end)
        y, m = y2, m2


def ms_to_date(ms):
    if ms is None:
        return ""
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


def clean(s, limit=None):
    if s is None:
        return ""
    s = re.sub(r"\s+", " ", str(s)).replace("-", "-").replace("-", "-").strip()
    return s[:limit] if limit else s


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL, extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def looks_like_person(name):
    """True when a name is two or three plain words with no business term."""
    n = clean(name)
    if not n or CORP_SUFFIX.search(n) or re.search(r"\d", n):
        return False
    words = re.findall(r"[A-Za-z'\-]+", n)
    return 2 <= len(words) <= 3 and len(words) == len(n.split())


def sqft_from_text(text):
    """Largest square-footage figure in a description, as an int string, else blank."""
    best = 0
    for m in re.finditer(r"([\d,]{3,})\s*(?:-|\s)?\s*(SQ\.?\s*FT\.?|SF\b|SQUARE\s+F(?:OO|EE)T|S\.F\.)", text or "", re.I):
        try:
            v = int(m.group(1).replace(",", ""))
        except ValueError:
            continue
        best = max(best, v)
    return str(best) if best else ""


# ---------- geometry ----------

class PolyIndex:
    """Point in polygon over ESRI rings (even-odd). Overlay districts (APZ, BAFB) are
    tried last so a base zoning district wins where polygons stack."""
    OVERLAY = ("APZ", "BAFB", "BAFB APZ")

    def __init__(self, features):
        base, overlay = [], []
        for f in features:
            rings = (f.get("geometry") or {}).get("rings") or []
            if not rings:
                continue
            xs = [p[0] for r in rings for p in r]
            ys = [p[1] for r in rings for p in r]
            item = (min(xs), min(ys), max(xs), max(ys), rings, f["attributes"])
            (overlay if clean(f["attributes"].get("DISTRICT_ID")) in self.OVERLAY else base).append(item)
        self.items = base + overlay

    @staticmethod
    def _in_rings(x, y, rings):
        inside = False
        for ring in rings:
            n = len(ring)
            j = n - 1
            for i in range(n):
                xi, yi = ring[i][0], ring[i][1]
                xj, yj = ring[j][0], ring[j][1]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
        return inside

    def find(self, x, y):
        for (x0, y0, x1, y1, rings, attrs) in self.items:
            if x0 <= x <= x1 and y0 <= y <= y1 and self._in_rings(x, y, rings):
                return attrs
        return None


def load_aurora_zoning(cache_dir):
    """Aurora zoning polygons (layer 20) in the service's own state plane feet, so PropX/PropY
    on the permit and development layers can be tested directly."""
    fields = ["OBJECTID", "DISTRICT_ID", "Dist_Name", "NAME"]
    require_fields(ZONING_LAYER, fields)
    feats = arcgis_fetch(ZONING_LAYER, "1=1", fields, cache_dir, "zoning", page_size=500, geometry=True)
    n = arcgis_count(ZONING_LAYER, "1=1")
    if len(feats) != n:
        raise SystemExit("Zoning layer: got %d polygons, source says %d" % (len(feats), n))
    return PolyIndex(feats)


INDUSTRIAL_DISTRICTS = {"I-1", "I-2", "AD"}    # Business/Tech, Industrial, Airport District (DIA-area parks)
COMM_INDUSTRIAL_DISTRICTS = {"MU-A"}           # Mixed Use Airport


def zoning_class(district_id):
    d = clean(district_id).upper()
    if d in INDUSTRIAL_DISTRICTS:
        return "industrial"
    if d in COMM_INDUSTRIAL_DISTRICTS:
        return "commercial-industrial"
    return ""


def stateplane_to_lonlat(x_ft, y_ft):
    """EPSG:2232 / 102654 (NAD83 Colorado Central, US survey feet) to lon/lat degrees.
    Lambert conformal conic inverse on GRS80; good to about a metre."""
    a, f = 6378137.0, 1 / 298.257222101
    e = math.sqrt(2 * f - f * f)
    ft = 1200.0 / 3937.0
    lat1, lat2, lat0, lon0 = map(math.radians, (39.75, 38.45, 37.0 + 50.0 / 60.0, -105.5))
    fe, fn = 3000000.0 * ft, 1000000.0 * ft

    def m(lat):
        return math.cos(lat) / math.sqrt(1 - (e * math.sin(lat)) ** 2)

    def t(lat):
        s = e * math.sin(lat)
        return math.tan(math.pi / 4 - lat / 2) / ((1 - s) / (1 + s)) ** (e / 2)

    n = (math.log(m(lat1)) - math.log(m(lat2))) / (math.log(t(lat1)) - math.log(t(lat2)))
    F = m(lat1) / (n * t(lat1) ** n)
    r0 = a * F * t(lat0) ** n
    dx, dy = x_ft * ft - fe, r0 - (y_ft * ft - fn)
    r = math.copysign(math.hypot(dx, dy), n)
    tt = (r / (a * F)) ** (1 / n)
    theta = math.atan2(dx, dy)
    lat = math.pi / 2 - 2 * math.atan(tt)
    for _ in range(8):
        s = e * math.sin(lat)
        lat = math.pi / 2 - 2 * math.atan(tt * ((1 - s) / (1 + s)) ** (e / 2))
    return round(math.degrees(theta / n + lon0), 6), round(math.degrees(lat), 6)


def summarize(rows, name_col="company_name"):
    """Counts for the notes: flags per rule, null rates, date range, monthly counts."""
    from collections import Counter
    n = len(rows)
    rules = Counter(r["flag_rule"] for r in rows if r["flag"] == "Y")
    nulls = {c: sum(1 for r in rows if not r[c]) for c in (name_col, "site_address", "record_date")}
    months = Counter(r["record_date"][:7] for r in rows if r["record_date"])
    dates = sorted(r["record_date"] for r in rows if r["record_date"])
    dup = n - len({r["record_id"] for r in rows})
    return {"rows": n, "flagged": sum(rules.values()), "rules": dict(rules), "nulls": nulls,
            "date_min": dates[0] if dates else "", "date_max": dates[-1] if dates else "",
            "months": dict(sorted(months.items())), "dup_record_id": dup}
