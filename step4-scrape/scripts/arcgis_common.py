"""Shared helpers for the two Denver ArcGIS pulls (agent2, step 4).

Boring on purpose: paged queries with a raw cache on disk, a point-in-polygon
join in plain Python (no shapely needed), and CSV helpers.
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

HOST = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services"
UA = "step4-research-pull/1.0"
PAUSE = 1.0          # seconds between requests
MAX_ERRORS = 3       # stop after this many consecutive failures
PARSER_VERSION = "agent2-1.0"

COMMON_COLS = ["source", "source_level", "record_id", "record_date", "date_type",
               "record_type", "company_name", "company_role", "site_address", "city",
               "county", "zip", "description", "flag", "flag_rule", "source_url",
               "retrieved_at"]

ZONING_LAYER = HOST + "/ODC_ZONE_ZONING_A/FeatureServer/209"
NBHD_LAYER = HOST + "/ODC_ADMN_NEIGHBORHOOD_A/FeatureServer"  # layer id resolved at run time


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_json(url, params, max_errors=MAX_ERRORS, backoff=5, post=False):
    """GET with identifying UA, pause, and a hard stop on repeated errors."""
    full = url + "?" + urllib.parse.urlencode(params)
    errors = 0
    while True:
        try:
            if post:
                req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(),
                                             headers={"User-Agent": UA})
            else:
                req = urllib.request.Request(full, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read().decode("utf-8")
            data = json.loads(body)
            if "error" in data:
                raise RuntimeError("ArcGIS error: %s" % data["error"])
            time.sleep(PAUSE)
            return data, body
        except Exception as e:  # noqa
            errors += 1
            print("  request failed (%d/%d): %s" % (errors, max_errors, e), file=sys.stderr)
            if errors >= max_errors:
                raise SystemExit("Stopping after repeated errors on %s" % url)
            time.sleep(backoff * errors)


def source_count(layer_url, where):
    data, _ = http_json(layer_url + "/query", {"where": where, "returnCountOnly": "true", "f": "json"})
    return data["count"]


def fetch_all(layer_url, where, out_fields, cache_dir, page_size=1000, geometry=True,
              extra=None, order="OBJECTID"):
    """Page through a layer. Each raw page is written to cache_dir before parsing.
    A page already on disk is reused (resume). Returns (features, fetched_at_by_page)."""
    os.makedirs(cache_dir, exist_ok=True)
    feats, offset, page = [], 0, 0
    while True:
        path = os.path.join(cache_dir, "page_%04d.json" % page)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                wrapped = json.load(f)
        else:
            params = {"where": where, "outFields": ",".join(out_fields), "orderByFields": order,
                      "resultOffset": offset, "resultRecordCount": page_size,
                      "returnGeometry": "true" if geometry else "false", "outSR": 4326, "f": "json"}
            if extra:
                params.update(extra)
            data, _ = http_json(layer_url + "/query", params)
            wrapped = {"fetched_at": now_iso(), "layer": layer_url, "params": params, "response": data}
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(wrapped, f)
            os.replace(tmp, path)
        got = wrapped["response"].get("features", [])
        for g in got:
            g["_fetched_at"] = wrapped["fetched_at"]
        feats.extend(got)
        print("  %s page %d: %d rows (total %d)" % (os.path.basename(cache_dir), page, len(got), len(feats)))
        if not got or not wrapped["response"].get("exceededTransferLimit"):
            break
        offset += len(got)
        page += 1
    return feats


def require_fields(layer_url, wanted):
    """Fail loudly on schema drift."""
    meta, _ = http_json(layer_url, {"f": "json"})
    have = {f["name"] for f in meta["fields"]}
    missing = [w for w in wanted if w not in have]
    if missing:
        raise SystemExit("Schema drift on %s: missing fields %s" % (layer_url, missing))
    return meta


def ms_to_date(ms):
    if ms is None:
        return ""
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


def clean(s, limit=None):
    if s is None:
        return ""
    s = re.sub(r"\s+", " ", str(s)).strip()
    return s[:limit] if limit else s


# ---------- point in polygon (ESRI rings, even-odd rule) ----------

class PolyIndex:
    def __init__(self, features):
        self.items = []
        for f in features:
            rings = (f.get("geometry") or {}).get("rings") or []
            if not rings:
                continue
            xs = [p[0] for r in rings for p in r]
            ys = [p[1] for r in rings for p in r]
            self.items.append((min(xs), min(ys), max(xs), max(ys), rings, f["attributes"]))

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


def load_zoning(cache_root):
    feats = fetch_all(ZONING_LAYER, "1=1",
                      ["OBJECTID", "ZONE_DISTRICT", "ZONE_DIST_TYPE", "ZONE_DESCRIPTION"],
                      os.path.join(cache_root, "zoning"), page_size=500,
                      extra={"geometryPrecision": 6})
    n = source_count(ZONING_LAYER, "1=1")
    if len(feats) != n:
        raise SystemExit("Zoning layer: got %d polygons, source says %d" % (len(feats), n))
    return PolyIndex(feats)


def load_neighborhoods(cache_root):
    svc, _ = http_json(NBHD_LAYER, {"f": "json"})
    lid = svc["layers"][0]["id"]
    layer = "%s/%d" % (NBHD_LAYER, lid)
    feats = fetch_all(layer, "1=1", ["NBHD_NAME"], os.path.join(cache_root, "neighborhoods"),
                      page_size=200, extra={"geometryPrecision": 6})
    n = source_count(layer, "1=1")
    if len(feats) != n:
        raise SystemExit("Neighborhood layer: got %d polygons, source says %d" % (len(feats), n))
    return PolyIndex(feats)


PARCEL_LAYER = HOST + "/ODC_PROP_PARCELS_A/FeatureServer/245"
# Owner name and owner mailing address fields are deliberately NOT requested (may be individuals).
PARCEL_FIELDS = ["SCHEDNUM", "ZONE_10", "SITUS_ZIP", "D_CLASS_CN", "SITUS_X_COORD", "SITUS_Y_COORD"]


def load_parcels(schednums, cache_root, batch=150):
    # Attributes only, by POST. Do NOT ask for returnCentroid: it makes each query take 30-60 s
    # and produces 504/400 errors. The situs point (state plane feet) is converted locally.
    """Look up parcels by schedule number. Returns {SCHEDNUM: {attrs..., 'x':, 'y':}} (situs point, lon/lat)."""
    cache_dir = os.path.join(cache_root, "parcels")
    os.makedirs(cache_dir, exist_ok=True)
    require_fields(PARCEL_LAYER, PARCEL_FIELDS)
    nums = sorted({s for s in schednums if re.fullmatch(r"[0-9A-Za-z]+", s or "")})
    out = {}
    for i in range(0, len(nums), batch):
        chunk = nums[i:i + batch]
        path = os.path.join(cache_dir, "batch_%04d.json" % (i // batch))
        wrapped = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                wrapped = json.load(f)
            if wrapped.get("schednums") != chunk:
                wrapped = None
        if wrapped is None:
            params = {"where": "SCHEDNUM IN (%s)" % ",".join("'%s'" % c for c in chunk),
                      "outFields": ",".join(PARCEL_FIELDS), "returnGeometry": "false", "f": "json"}
            data, _ = http_json(PARCEL_LAYER + "/query", params, post=True)
            if data.get("exceededTransferLimit"):
                raise SystemExit("Parcel batch exceeded transfer limit; lower the batch size")
            wrapped = {"fetched_at": now_iso(), "schednums": chunk, "response": data}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(wrapped, f)
        for ft in wrapped["response"].get("features", []):
            a = dict(ft["attributes"])
            a["x"] = a["y"] = None
            if a.get("SITUS_X_COORD") and a.get("SITUS_Y_COORD"):
                a["x"], a["y"] = stateplane_co_central_to_lonlat(a["SITUS_X_COORD"], a["SITUS_Y_COORD"])
            out.setdefault(a["SCHEDNUM"], a)
        if True:
            print("  parcels batch %d/%d (matched so far %d)" % (i // batch + 1, (len(nums) - 1) // batch + 1, len(out)))
    return out


def in_denver_bbox(x, y):
    return x is not None and y is not None and -105.4 < x < -104.5 and 39.5 < y < 40.0


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL, extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def is_industrial_zone(district, dist_type):
    """Denver Zoning Code I-A, I-B, I-MX-n, M-IMX-n; Former Chapter 59 I-0, I-1, I-2 (with waivers)."""
    d = (district or "").upper().strip()
    t = (dist_type or "").lower()
    return t.startswith("industrial") or d.startswith("I-") or d.startswith("M-IMX")


def stateplane_co_central_to_lonlat(x_ft, y_ft):
    """EPSG:2877 (NAD83(HARN) Colorado Central, US survey feet) to lon/lat degrees.
    Lambert conformal conic inverse on GRS80. Good to about a metre, which is plenty for
    a zoning or neighborhood polygon lookup. No datum shift applied."""
    import math
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
    return math.degrees(theta / n + lon0), math.degrees(lat)
