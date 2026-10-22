#!/usr/bin/env python3
"""Step 5b: re-run the Denver ranking with the Step 4b tier B flags scored in.

Usage: python3 rerank_step5b.py <step4-scrape folder> <step5-analysis folder> [--out <folder>] [--bscale 1.0]

The Step 5 scripts were not saved, so this is an incremental re-run:
  * the 359 Step 5 rows keep their evidence and their points (read back from the "Points:" text in top_evidence);
  * tier B rows are added to them where the name or address matches;
  * tier B rows that match nothing become new rows, scoped, scored and ranked with the Step 5 rules as written
    in analysis_notes.md.
Reads  step5: denver_ranked_accounts.csv, denver_evidence.csv
       step4: the three _v2 files and the other source files.
Writes denver_ranked_accounts_v2.csv, denver_evidence_v2.csv, rerank_counts.json, geocode_cache.json.
Web use: the Census geocoder only, to settle the county of an address in a split zip (as in Step 5).
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reflag_step4b as R
csv.field_size_limit(10 ** 9)

RUN = "2026-10-10"; D12 = "2025-10-10"; D24 = "2024-10-10"; D6 = "2026-04-10"
BPTS = {"B1a": 30, "B1b": 8, "B1c": 8, "B2a": 3, "B3a": 12, "B3b": 6}      # agreed 2026-10-10; B1a raised from 25 to 30 on 2026-10-11
SMALL_PERMIT_STAGE_CAP = 4   # 2026-10-11: a permit under $50k (B3b) can add at most 4 stage points, whatever its status
SHORT = {"State water permits (WQCD)": "State water permits"}
UCC, REG, PER, SDP, WAT, AIR = ("Colorado UCC filings", "Colorado business registrations", "Denver commercial construction permits",
                                "Denver concept and site plans", "State water permits (WQCD)", "APCD air permit status")
SHARED = R.SHARED

def nk(s):
    s = re.sub(r",\s*(?:Dissolved|Delinquent|Noncompliant|Withdrawn|Converted|Merged)\b.*$", "", s, flags=re.I).upper()
    s = re.sub(r"\(.*?\)", " ", s)
    s = s.replace("&", " AND ")
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\b(?:THE|INC|INCORPORATED|LLC|L L C|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|LP|LLP|LLLP|PC|PLLC|DBA)\b", " ", s)
    t = s.split(); out = []
    for w in t:
        if len(w) == 1 and out and len(out[-1]) <= 3 and out[-1].isalpha() and w.isalpha() and getattr(nk, "_j", False):
            out[-1] += w
        else:
            out.append(w)
        nk._j = (len(w) == 1 and w.isalpha())
    nk._j = False
    return " ".join(out)

def unit_of(a):
    a = a.upper().replace(",", " ").replace(".", " ")
    m = re.search(r"(?:\b(?:STE|SUITE|UNIT|APT|BLDG|BUILDING|BAY|SPC|SPACE|RM|ROOM)\b\s*#?\s*|#\s*)([A-Z0-9-]+)", a)
    if m and m.group(1) not in ("UNIT", "SUITE"):
        return m.group(1)
    m = re.search(r"\b(?:ST|AVE|BLVD|RD|DR|LN|CT|PL|WAY|PKWY|CIR|HWY)\s+([A-Z]?\d+[A-Z]?|[A-Z])(?:\s|$)", a)
    return m.group(1) if m else ""

def rec_pts(d):
    return 15 if d >= D12 else 8 if d >= D24 else 0

# ---- fit for NEW rows (Step 5 order: machinery named in a UCC filing, maker word in the name, trade words, weak words)
FIT_STRONG = re.compile(r"\b(manufactur\w*|mfg|machining|machine|fabricat\w*|brew\w*|distill\w*|baker\w*|baking|foods|roast\w*|plastics|metals?|"
                        r"tool|tooling|packaging|woodwork\w*|cabinet\w*|millwork|foundry|composites|aerospace|robotics|semiconductors?|"
                        r"chocolate\w*|confection\w*|creamery|tortill\w*|winery|cidery|molding|castings?|forge|extrusions?|stamping|plating)\b", re.I)
FIT_MOD = re.compile(r"\b(auto\w*|tire|tyre|concrete|print\w*|coatings|welding|collision|body\s+shop|truck\w*)\b", re.I)
FIT_WEAK = re.compile(r"\b(office|energy|solar|software|technolog\w+|systems|holdings?|properties|realty|apartments?|housing|logistics|hospitality|"
                      r"restaurant|hotel|consulting|capital|investments?|ventures|media|marketing|studio|clinic|dental|medical|school|church)\b", re.I)
VENDORS = re.compile(r"MAZAK|TRUMPF|MULTIVAC|METHODS MACHINE|HARTWIG|PRODUCTIVITY INC|CNC ASSOCIATES|STAR CNC|YAMAZEN|FANUC|YASKAWA|REISER|MITSUI SEIKI|MARUKA|HAITIAN|GROB")

def fit_company(name, rules, sp):
    w = FIT_WEAK.search(name)
    b1a = [r for r in rules if r.startswith("B1a")]
    if b1a:
        return ("strong: finances process equipment in a UCC filing (%s)" % b1a[0].rsplit(": ", 1)[1], 15)
    if any(r.startswith("B1b") for r in rules) and VENDORS.search(sp):
        return ("strong: equipment lien held by a machinery maker or dealer; not confirmed", 15)
    m = FIT_STRONG.search(name)
    if m and not w:
        return ("strong: name suggests manufacturing or processing (%s); not confirmed" % m.group(1).title(), 15)
    m2 = FIT_MOD.search(name)
    if m2 and not w:
        return ("moderate: auto, tyre, concrete, print or similar trade by name (%s)" % m2.group(1).title(), 6)
    if w:
        return ("weak: name suggests office, energy, software, retail, housing or logistics (%s)" % w.group(1).title(), -15)
    return ("unknown: nothing in the records says what the company makes", 0)

def fit_parcel(pc, zone):
    if re.search(r"FOOD PROCESSING|FACTORY|MEAT PACKING|PRINTING PLANT", pc):
        return ("strong: assessor class is %s" % pc.title(), 15)
    if "WAREHOUSE" in pc:
        return ("unknown: industrial warehouse parcel; could be production or storage", 0)
    if re.search(r"AUTO SERVICE|CAR WASH|SERVICE STATION", pc):
        return ("moderate: auto, tyre, concrete, print or similar trade by parcel class (%s)" % pc.title(), 6)
    if re.search(r"RESIDENTIAL|SFR|HOTEL|SCHOOL|CHURCH|JAIL|STADIUM|ENTERTAINMENT|BOARDING|CONDOMINIUM", pc):
        return ("weak: assessor class is %s" % pc.title(), -15)
    return ("unknown: industrially zoned site; use and occupier not identified (assessor class %s)" % (pc.title() or "blank"), 0)

def permit_stage(r):
    if r.get("cancel_date"):
        return ("unknown (permit cancelled)", 0)
    c = r["class"]; fin = r.get("final_date", "")
    if c in ("New Building", "Addition", "Foundation Only/Excavation", "Phased Construction"):
        return ("under construction", 8) if not fin else ("operating and expanding", 8)
    if not fin or fin >= D6:
        return ("fit-out", 12)
    return ("operating and expanding", 8)

class Acct:
    def __init__(s):
        s.per = {}; s.rows = []; s.names = set(); s.addrs = set(); s.new = False; s.added = []; s.occ = []
        s.rec = 0; s.stage = ("", 0); s.fit = ("", 0); s.old = None; s.section = "denver"; s.first = ""; s.latest = ""
    def add(s, src, pts, date, cls, text, row, rule, repeat_ok=False):
        eff = pts if cls == "confirmed" else pts / 2.0
        k = SHORT.get(src, src); b, rp = s.per.get(k, (0.0, 0.0)); changed = False
        if eff > b:
            s.per[k] = (eff, rp); changed = True
        elif repeat_ok and eff >= 12 and rp < 9 and date[:7] not in s.__dict__.setdefault("months_" + k, set()):
            s.per[k] = (b, rp + 3); changed = True
        s.__dict__.setdefault("months_" + k, set()).add(date[:7])
        if eff >= 4:
            s.rec = max(s.rec, rec_pts(date))
        if date:
            s.first = min(s.first or date, date); s.latest = max(s.latest, date)
        s.added.append(dict(src=src, pts=pts, eff=eff, date=date, cls=cls, text=text, row=row, rule=rule, changed=changed))
    def src_bonus(s):
        v = [b for b, _ in s.per.values() if b > 0]
        sig = [x for x in v if x >= 5]; sup = [x for x in v if x < 5]
        if sig:
            return min(24, 8 * (len(sig) - 1)) + min(6, 3 * len(sup))
        return min(6, 3 * len(sup)) if len(sup) >= 2 else 0
    def signal(s):
        return sum(b + rp for b, rp in s.per.values())
    def score(s):
        return s.signal() + s.src_bonus() + s.rec + s.stage[1] + s.fit[1]
    def points_text(s):
        parts = "; ".join("%s: %s%s" % (k, ("%g" % b), ("+%g repeat" % rp if rp else "")) for k, (b, rp) in s.per.items() if b + rp > 0)
        return "Points: signal %g (%s); sources %d; recency %d; stage %d; fit %d" % (s.signal(), parts, s.src_bonus(), s.rec, s.stage[1], s.fit[1])

def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    S4, S5 = a[0], a[1]
    OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else S5
    bscale = float(sys.argv[sys.argv.index("--bscale") + 1]) if "--bscale" in sys.argv else 1.0
    bp = {k: v * bscale for k, v in BPTS.items()}
    zshare = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "denver_zip_share.json")))
    gpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geocode_cache.json")
    gcache = json.load(open(gpath)) if os.path.exists(gpath) else {}
    C = Counter()

    # ---------------- existing accounts
    ranked = list(csv.DictReader(open(os.path.join(S5, "denver_ranked_accounts.csv"), newline="", encoding="utf-8-sig")))
    evid = list(csv.DictReader(open(os.path.join(S5, "denver_evidence.csv"), newline="", encoding="utf-8-sig")))
    pat = re.compile(r"Points: signal ([\d.]+) \((.*?)\); sources (\d+); recency (\d+); stage (\d+); fit (-?\d+)\s*$")
    accts = []; by_rank = {}
    for x in ranked:
        A = Acct(); A.old = x; m = pat.search(x["top_evidence"])
        for part in m.group(2).split("; "):
            k, v = part.rsplit(": ", 1); mm = re.match(r"([\d.]+)(?:\+(\d+) repeat)?", v); A.per[k] = (float(mm.group(1)), float(mm.group(2) or 0))
        A.rec = int(m.group(4)); A.stage = (x["stage"], int(m.group(5))); A.fit = (x["compressed_air_fit"], int(m.group(6)))
        A.first, A.latest = x["first_signal_date"], x["latest_signal_date"]
        cb = x["county_basis"]
        A.section = "oedit" if cb.startswith("OEDIT") else "unconfirmed" if cb.startswith("Denver mailing address") else "denver"
        A.unatt = x["company_name"].startswith("Unattached address")
        if not A.unatt and A.section != "oedit":
            for n in [x["company_name"]] + [v for v in x["name_variants"].split(" | ") if v]:
                k = nk(n)
                if len(k) >= 6: A.names.add(k)
        k = R.addr_key(x["site_address"])
        if k: A.addrs.add(k)
        A.unit = unit_of(x["site_address"])
        accts.append(A); by_rank[x["rank"]] = A
    need_addr = defaultdict(list)       # (source, record_id) -> account, for rows whose address is withheld in the evidence file
    for e in evid:
        A = by_rank.get(e["rank"])
        if not A: continue
        A.rows.append(e)
        if e["match_class"] == "confirmed" and e["source"] in (UCC, REG, WAT, AIR) and not A.unatt and A.section != "oedit":
            k = nk(e["company_name"])
            if len(k) >= 6: A.names.add(k)
        if e["match_class"] == "confirmed":
            k = R.addr_key(e["site_address"])
            if k: A.addrs.add(k)
            elif e["site_address"].startswith("withheld") and e["source"] in (UCC, REG):
                need_addr[(e["source"], e["record_id"], nk(e["company_name"]))].append(A)
    name_ix = defaultdict(list); addr_ix = defaultdict(list)

    # ---------------- step 4 files: tier B rows, and address recovery for withheld evidence rows
    def rd(p):
        return csv.DictReader(open(os.path.join(S4, p), newline="", encoding="utf-8-sig"))
    uccB, regB, perB = [], [], []
    for r in rd("scrape_ucc_filings/scrape_ucc_filings_v2.csv"):
        t = (UCC, r["record_id"], nk(r["company_name"]))
        if t in need_addr:
            k = R.addr_key(r["site_address"])
            for A in need_addr[t]:
                if k: A.addrs.add(k)
        if r["flag_tier"] == "B": uccB.append(r)
    for r in rd("scrape_business_registrations/scrape_business_registrations_v2.csv"):
        t = (REG, r["record_id"], nk(r["company_name"]))
        if t in need_addr:
            k = R.addr_key(r["site_address"])
            for A in need_addr[t]:
                if k: A.addrs.add(k)
        if r["flag_tier"] == "B": regB.append(r)
    permits = list(rd("scrape_denver_commercial_permits_v2.csv"))
    perB = [r for r in permits if r["flag_tier"] == "B"]
    for A in accts:
        for k in A.names: name_ix[k].append(A)
        for k in A.addrs: addr_ix[k].append(A)
    C["tierB_ucc_statewide"], C["tierB_reg_statewide"], C["tierB_permits"] = len(uccB), len(regB), len(perB)

    # ---------------- scope test for a UCC / registration row
    def geocode(addr, city, zp):
        q = "%s, %s, CO %s" % (addr, city, zp)
        if q in gcache: return gcache[q]
        url = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress?" + urllib.parse.urlencode(
            {"address": q, "benchmark": "Public_AR_Current", "vintage": "Current_Current", "format": "json"})
        res = ""
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "step5-research/1.0"})
                j = json.load(urllib.request.urlopen(req, timeout=30))
                m = j["result"]["addressMatches"]
                res = m[0]["geographies"]["Counties"][0]["NAME"] if m else "no match"
                break
            except Exception as ex:
                res = "error"; time.sleep(3)
        gcache[q] = res; json.dump(gcache, open(gpath, "w")); time.sleep(1.0)
        return res
    def scope(r, state):
        """-> (section, county_basis) or None"""
        zp = r["zip"][:5]; city = r["city"].strip().upper(); sh = zshare.get(zp)
        if state != "CO": return None
        if sh is None:
            return None
        if sh >= 0.99:
            return ("denver", "zip %s is in Denver County (Census 2020 ZCTA file)" % zp)
        if sh < 0.10 and city != "DENVER":
            return None
        if not R.addr_key(r["site_address"]):
            return ("unconfirmed", "Denver mailing address, county unconfirmed (no street address to check)") if city == "DENVER" else None
        g = geocode(re.sub(r"\s+", " ", r["site_address"]), r["city"].strip(), zp)
        if g == "Denver County":
            return ("denver", "Census geocoder places the address in Denver County (zip %s is split)" % zp)
        if g in ("no match", "error"):
            return ("unconfirmed", "Denver mailing address, county unconfirmed (Census geocoder could not place it)") if city == "DENVER" or sh >= 0.5 else None
        return ("unconfirmed", "Denver mailing address, county unconfirmed (Census geocoder places it in %s)" % g) if city == "DENVER" else None

    # ---------------- tier B UCC and registration rows
    snip = {}
    hp = os.path.join(S4, "scrape_ucc_filings", "ucc_b1a_fulltext_hits.csv")
    if os.path.exists(hp):
        for h in csv.DictReader(open(hp, newline="", encoding="utf-8")): snip[(h["record_id"], h["debtor_seq"])] = h["snippet"]
    newco = {}        # name key -> Acct
    def describe(r, src, rules):
        ids = [x.split(" ", 1)[0] for x in rules]
        if src == UCC:
            sp = r.get("secured_party", "")[:60]
            return "UCC %s initial filing [tier B %s], secured party %s: %s" % (r["record_date"], "+".join(ids), sp or "not given", ((snip.get((r["record_id"], r.get("debtor_seq", "")), "") if "full collateral text" in r["flag_rule_v2"] else "") or r["description"])[:130] or "no collateral text")
        return "Registered in Colorado %s (%s) [tier B B2a]; status %s; name word: %s" % (r["record_date"], r["record_type"], r.get("entity_status", ""), rules[0].rsplit(": ", 1)[1])
    for src, rows in ((UCC, uccB), (REG, regB)):
        for r in rows:
            rules = r["flag_rule_v2"].split("; "); pts = max(bp[x.split(" ", 1)[0]] for x in rules)
            k = nk(r["company_name"]); ak = R.addr_key(r["site_address"]); state = r.get("debtor_state", r.get("principal_state", ""))
            text = describe(r, src, rules)
            hit = name_ix.get(k, []) if len(k) >= 6 else []
            if hit:
                for A in hit[:1]:
                    cls = "confirmed" if ak and ak in A.addrs else "possible"
                    if cls == "possible" and state != "CO": C["skip_name_match_out_of_state"] += 1; continue
                    A.add(src, pts, r["record_date"], cls, text + ("" if cls == "confirmed" else " [same name, different address: possible match]"), r, r["flag_rule_v2"])
                    if any(x.startswith("B1a") for x in rules) and cls == "confirmed":
                        st = ("buying equipment", 12) if r["record_date"] >= D12 else ("operating and expanding", 8)
                        if st[1] > A.stage[1]: A.stage = st
                    C["attach_existing_by_name_" + src[:12]] += 1
                continue
            sc = scope(r, state)
            if not sc:
                C["out_of_scope_" + src[:12]] += 1; continue
            hitA = [A for A in addr_ix.get(ak, []) if A.old is not None] if ak else []
            un = [A for A in hitA if A.unatt]
            if un:                                   # a flagged company at an unattached address: possible occupier, half points
                A = un[0]; u1, u2 = unit_of(r["site_address"]), A.unit
                if not (u1 and u2 and u1 != u2):
                    A.add(src, pts, r["record_date"], "possible", text + " [%s has this address: possible occupier]" % r["company_name"], r, r["flag_rule_v2"])
                    A.occ.append(r["company_name"]); C["attach_unattached_as_occupier_" + src[:12]] += 1
                    continue
            A = newco.get(k)
            if not A:
                A = Acct(); A.new = True; A.unatt = False; A.name = r["company_name"]; A.names.add(k); A.raw_addr = r["site_address"]; A.zip = r["zip"][:5]
                A.city = r["city"]; A.section, A.basis = sc; A.rules = []; A.sp = ""; A.unit = unit_of(r["site_address"]); A.variants = set()
                newco[k] = A
            if ak: A.addrs.add(ak)
            A.variants.add(r["company_name"]); A.rules += rules; A.sp += " " + R.norm_party(r.get("secured_party", ""))
            A.add(src, pts, r["record_date"], "confirmed", text, r, r["flag_rule_v2"], repeat_ok=True)
            if any(x.startswith("B1a") for x in rules):
                st = ("buying equipment", 12) if r["record_date"] >= D12 else ("operating and expanding", 8)
                if st[1] > A.stage[1] or (st[1] == 12 and A.stage[0] != "buying equipment"): A.stage = st
            C["new_company_rows_" + src[:12]] += 1
    new_addr_ix = defaultdict(list)
    for A in newco.values():
        for k in A.addrs: new_addr_ix[k].append(A)

    # ---------------- tier B permits
    newaddr = {}
    def ptext(r, how=""):
        return "Denver permit %s [tier B %s]: %s, $%s, received %s, %s; parcel class %s, zone %s%s" % (
            r["record_id"], r["flag_rule_v2"][:3], r["class"], "{:,.0f}".format(float(r["valuation"] or 0)), r["record_date"],
            ("cancelled" if r["cancel_date"] else "finaled " + r["final_date"] if r["final_date"] else "not finaled"), r["parcel_class"] or "blank", r["zone_district"], how)
    for r in perB:
        rid = r["flag_rule_v2"][:3]; pts = bp[rid]; ak = R.addr_key(r["site_address"]); u = unit_of(r["site_address"])
        if r["cancel_date"]: C["permit_cancelled_skipped"] += 1; continue
        if not ak: C["permit_no_address"] += 1; continue
        ex = addr_ix.get(ak, []); un = [A for A in ex if A.unatt]; co = [A for A in ex if not A.unatt]
        tgt = None; cls = "confirmed"; how = ""
        if un:
            tgt = un[0]; C["permit_to_existing_unattached"] += 1
        elif co:
            pick = [A for A in co if u and A.unit == u] or ([A for A in co if not (u and A.unit and A.unit != u)] if len(co) == 1 else [])
            if pick:
                tgt = pick[0]; cls = "confirmed" if (u and tgt.unit == u) else "possible"; how = "" if cls == "confirmed" else " [joined by street address only] [possible match]"
                C["permit_to_existing_company"] += 1
        if not tgt:
            nc = [A for A in new_addr_ix.get(ak, []) if not (u and A.unit and A.unit != u)]
            if len(nc) == 1:
                tgt = nc[0]; cls = "confirmed" if (u and tgt.unit == u) else "possible"; how = "" if cls == "confirmed" else " [joined by street address only] [possible match]"
                C["permit_to_new_company"] += 1
        if not tgt:
            tgt = newaddr.get(ak)
            if not tgt:
                tgt = Acct(); tgt.new = True; tgt.unatt = True; tgt.name = "Unattached address (no company attached)"; tgt.raw_addr = r["site_address"]; tgt.zip = r["zip"]
                tgt.section = "denver"; tgt.basis = "Denver permit layer (Denver only)"; tgt.addrs.add(ak); tgt.unit = u; tgt.pcs = []; newaddr[ak] = tgt
            C["permit_to_new_unattached"] += 1
        if tgt.new and tgt.unatt: tgt.pcs.append((r["parcel_class"], r["zone_district"]))
        tgt.add(PER, pts, r["record_date"], cls, ptext(r, how), r, r["flag_rule_v2"], repeat_ok=tgt.new)
        st = permit_stage(r)
        if rid == "B3b" and st[1] > SMALL_PERMIT_STAGE_CAP:
            st = (st[0] + " (permit under $50k)", SMALL_PERMIT_STAGE_CAP)
        if st[1] > tgt.stage[1] and (cls == "confirmed" or tgt.stage[1] == 0 or st[1] > tgt.stage[1]): tgt.stage = st

    # ---------------- reach into the full files for NEW rows (supporting evidence, Step 5 values)
    nn = {k: A for k, A in newco.items()}
    na = defaultdict(list)
    for A in list(newco.values()) + list(newaddr.values()):
        for k in A.addrs: na[k].append(A)
    seen = set((d["src"], d["row"]["record_id"]) for A in list(newco.values()) + list(newaddr.values()) for d in A.added)
    for r in rd("scrape_ucc_filings/scrape_ucc_filings_v2.csv"):
        if r["transaction_type"] != "Initial Filing" or "|ucc|" not in r["filing_type_raw"] or r["flag_v2"] == "Y": continue
        A = nn.get(nk(r["company_name"]))
        if A and (UCC, r["record_id"]) not in seen:
            ak = R.addr_key(r["site_address"]); cls = "confirmed" if ak in A.addrs else "possible"
            A.add(UCC, 4, r["record_date"], cls, "UCC %s initial filing, secured party %s: %s (support: generic or blanket lien)" % (r["record_date"], r["secured_party"][:50] or "not given", r["description"][:80] or "no collateral text"), r, "")
    for r in rd("scrape_business_registrations/scrape_business_registrations_v2.csv"):
        A = nn.get(nk(r["company_name"]))
        if A and (REG, r["record_id"]) not in seen:
            ak = R.addr_key(r["site_address"]); cls = "confirmed" if ak in A.addrs else "possible"
            A.add(REG, 6 if r["flag"] == "Y" else 3, r["record_date"], cls, "Registered in Colorado %s (%s); status %s (%s)" % (r["record_date"], r["record_type"], r["entity_status"], "flagged in Step 4" if r["flag"] == "Y" else "support: unflagged registration"), r, r.get("flag_rule", ""))
    for r in permits:
        if r["flag_v2"] == "Y" or r["cancel_date"] or r["class"] in ("Special Event", "Change of Contractor"): continue
        ak = R.addr_key(r["site_address"]); u = unit_of(r["site_address"])
        for A in na.get(ak, []):
            if A.unatt:
                A.add(PER, 6, r["record_date"], "possible", "Denver permit %s at this address: %s, $%s, received %s, parcel class %s (unflagged) [possible match]" % (r["record_id"], r["class"], r["valuation"], r["record_date"], r["parcel_class"]), r, "")
            elif not (u and A.unit and A.unit != u):
                A.add(PER, 6, r["record_date"], "possible", "Denver permit %s at the company's address: %s, $%s, received %s (unflagged) [possible match]" % (r["record_id"], r["class"], r["valuation"], r["record_date"]), r, "")
    for r in rd("scrape_denver_site_plans.csv"):
        ak = R.addr_key(r["site_address"])
        for A in na.get(ak, []):
            A.add(SDP, 4, r["record_date"], "possible", "Denver %s %s at this address, opened %s, status %s, zone %s (support) [possible match]" % (r["record_type"], r["record_id"], r["record_date"], r.get("status", ""), r.get("zone_district", "")), r, r["flag_rule"])
    for fn, src in (("scrape_state_water_permits.csv", WAT), ("scrape_apcd_permit_status.csv", AIR)):
        for r in rd(fn):
            A = nn.get(nk(r["company_name"])) or nn.get(nk(r.get("facility_name", "") or "~"))
            if A:
                A.add(src, 2, r["record_date"], "possible", "%s row %s, %s (not a scoring signal in Step 5; support only) [possible match]" % (src, r["record_id"], r["record_date"]), r, r["flag_rule"])

    # ---------------- home-address rule, fit and stage for new rows
    site_keys = set()
    for fn in ("scrape_denver_commercial_permits.csv", "scrape_denver_site_plans.csv", "scrape_state_water_permits.csv", "scrape_apcd_permit_status.csv", "scrape_mile_high_cre.csv"):
        for r in rd(fn):
            k = R.addr_key(r["site_address"])
            if k: site_keys.add(k)
    shared = defaultdict(set)
    for A in newco.values():
        for k in A.addrs: shared[(k, A.zip)].add(next(iter(A.names)))
    for A in accts:
        if not A.unatt:
            for k in A.addrs: shared[(k, A.old["zip"])].add(A.old["company_name"])
    WH = "withheld (not confirmed as a business premises; see source record)"
    for A in newco.values():
        k = R.addr_key(A.raw_addr)
        ok = bool(R.HAS_UNIT.search(A.raw_addr)) or k in site_keys or len(shared.get((k, A.zip), ())) >= 2
        A.show_addr = A.raw_addr if (ok and k) else WH
        A.fit = fit_company(A.name, A.rules, A.sp)
        if A.stage[1] == 0:
            A.stage = ("unknown (registration only)" if all(x.startswith("B2a") for x in A.rules) else "unknown (blanket or vague lien only)", 0)
    for A in newaddr.values():
        A.show_addr = A.raw_addr
        pc = Counter(A.pcs).most_common(1)[0][0]
        A.fit = fit_parcel(pc[0], pc[1])
    for A in accts:
        if A.occ and A.old["company_name"] == "Unattached address (no company attached)":
            A.newname = "Unattached address (possible occupier: %s)" % A.occ[0]

    # ---------------- rank
    def nextstep(A):
        if A.section == "unconfirmed": return "Confirm the county with the assessor before treating this as a Denver account; if it is yours, qualify by phone"
        if A.unatt: return "Hand lookup of this address in Denver Accela to name the tenant and see whether trade permits are open"
        if A.fit[1] < 0: return "Low priority: use looks like office, retail, storage or data centre"
        if A.stage[0].startswith("buying equipment"): return "Call now: financing production equipment in the last 12 months; ask what air the new line needs"
        if A.stage[0] == "fit-out": return "Call now: build-out permit open; ask who is specifying compressed air. Accela lookup shows whether mechanical permits are issued"
        if A.signal() < 12: return "Qualify first: one weak signal only"
        return "Existing plant with a recent permit or equipment signal: ask about capacity additions and compressor age"
    allA = accts + list(newco.values()) + list(newaddr.values())
    order = {"denver": 0, "unconfirmed": 1, "oedit": 2}
    allA.sort(key=lambda A: (order[A.section], -A.score(), int(A.old["rank"]) if A.old else 10 ** 6))
    cols = list(ranked[0].keys()) + ["rank_before", "score_before", "tier_b_points_added", "tier"]
    out_rows = []; old2new = {}
    for i, A in enumerate(allA, 1):
        A.rank = i
        if A.old:
            x = dict(A.old); old2new[x["rank"]] = i
            btxt = [d["text"] for d in A.added]
            ev = x["top_evidence"].rsplit(" || Points:", 1)[0]
            if btxt: ev += " || " + " || ".join(btxt[:3])
            x["top_evidence"] = ev + " || " + A.points_text()
            delta = A.score() - float(x["score"])
            x.update(rank_before=x["rank"], score_before=x["score"], rank=i, score="%.1f" % A.score(), stage=A.stage[0], tier_b_points_added="%g" % delta,
                     tier="A+B" if A.added else "A", first_signal_date=A.first, latest_signal_date=A.latest)
            if getattr(A, "newname", ""): x["company_name"] = A.newname
            if A.added:
                srcs = set(x["sources"].split("; ")) | set(d["src"] for d in A.added); x["sources"] = "; ".join(sorted(srcs)); x["sources_count"] = len(srcs)
                if any(d["cls"] == "possible" for d in A.added) and x["match_confidence"] == "confirmed": x["match_confidence"] = "possible for some rows (see evidence file)"
                if x["next_step"].startswith("Qualify first") or x["next_step"].startswith("Early"): x["next_step"] = nextstep(A) if not A.unatt else x["next_step"]
        else:
            best = sorted(A.added, key=lambda d: (-d["eff"], d["date"]), reverse=False)
            srcs = sorted(set(d["src"] for d in A.added))
            x = dict(rank=i, company_name=A.name, name_variants=" | ".join(sorted(v for v in getattr(A, "variants", set()) if v != A.name)), site_address=A.show_addr, zip=A.zip,
                     county_basis=A.basis, stage=A.stage[0], score="%.1f" % A.score(), sources_count=len(srcs), sources="; ".join(srcs), first_signal_date=A.first,
                     latest_signal_date=A.latest, top_evidence=" || ".join(d["text"] for d in best[:3]) + " || " + A.points_text(), compressed_air_fit=A.fit[0],
                     match_confidence=("address confirmed; company not attached" if A.unatt else "possible for some rows (see evidence file)" if any(d["cls"] == "possible" for d in A.added) else "confirmed"),
                     in_ground_truth="no", next_step=nextstep(A), rank_before="", score_before="", tier_b_points_added="%g" % A.score(), tier="B")
        out_rows.append((A, x))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "denver_ranked_accounts_v2.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for A, x in out_rows: w.writerow(x)
    ecols = list(evid[0].keys()) + ["flag_tier", "flag_rule_v2", "points_full", "added_in"]
    with open(os.path.join(OUT, "denver_evidence_v2.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ecols); w.writeheader()
        for e in evid:
            if e["rank"] in old2new:
                x = dict(e); x["rank"] = old2new[e["rank"]]; x.update(flag_tier="A" if e["flag"] == "Y" else "", flag_rule_v2=e["flag_rule"], points_full="", added_in="step5"); w.writerow(x)
        for A, _ in out_rows:
            key = ("A:" + next(iter(A.addrs))) if A.unatt and A.new else ("N:" + next(iter(A.names))) if A.new else (A.rows[0]["company_key"] if A.rows else "")
            for d in A.added:
                r = d["row"]; x = {c: r.get(c, "") for c in SHARED}
                if d["src"] in (UCC, REG):
                    k = R.addr_key(x["site_address"])
                    if not (R.HAS_UNIT.search(x["site_address"]) or k in site_keys or len(shared.get((k, x["zip"][:5]), ())) >= 2): x["site_address"] = "withheld (see source record)"
                x.update(rank=A.rank, company_key=key, match_class=d["cls"], flag_tier=r.get("flag_tier", ""), flag_rule_v2=d["rule"], points_full="%g" % d["pts"], added_in="step5b")
                w.writerow(x)
    C["accounts_before"] = len(accts); C["new_company_rows"] = len(newco); C["new_unattached_rows"] = len(newaddr); C["accounts_after"] = len(allA)
    C["existing_rows_with_tier_b"] = sum(1 for A in accts if A.added); C["existing_rows_score_changed"] = sum(1 for A in accts if abs(A.score() - float(A.old["score"])) > 0.01)
    for sec in order: C["section_" + sec] = sum(1 for A in allA if A.section == sec)
    C["geocoder_lookups_cached"] = len(gcache)
    C.update({"geocode_" + v: n for v, n in Counter(gcache.values()).items()})
    json.dump(dict(C), open(os.path.join(OUT, "rerank_counts.json"), "w"), indent=1, sort_keys=True)
    for k in sorted(C): print(k, C[k])

if __name__ == "__main__":
    main()
