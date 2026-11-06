#!/usr/bin/env python3
"""Step 5 v3, part 1: scope test and noise cuts. Turns the Step 4 flagged rows (tier A and tier B) into signals.

Every cut is counted in the order it is applied. No flag is changed and nothing is re-scraped.
"""
import csv, os, re
from collections import Counter, defaultdict

from v3_lib import *
import v3_config as C


def shared(r):
    return {c: r.get(c, "") for c in SHARED}


class Cuts:
    """Ordered cut counts: (source, step, rows)."""
    def __init__(self):
        self.rows = []
        self.ix = {}

    def add(self, source, step, n=1):
        k = (source, step)
        if k not in self.ix:
            self.ix[k] = len(self.rows)
            self.rows.append([source, step, 0])
        self.rows[self.ix[k]][2] += n

    def declare(self, source, steps):
        for s in steps:
            self.add(source, s, 0)


# --------------------------------------------------------------------------- scope for UCC and registration rows
def scope_pre(r, state, zshare):
    """-> ("in", section, basis) | ("out", reason) | ("geo", query, zip, city, share)"""
    if state != "CO":
        return ("out", "no Colorado address")
    zp = r["zip"][:5]
    city = r["city"].strip().upper().rstrip(",")
    sh = zshare.get(zp)
    if sh is not None and sh >= 0.99:
        return ("in", "denver", "zip %s is in %s (Census 2020 ZCTA file)" % (zp, C.COUNTY_FULL))
    if sh is None and city not in C.MAIL_CITIES:
        return ("out", "zip not in %s and mailing city not %s" % (C.COUNTY, C.COUNTY))
    if sh is not None and sh < 0.10 and city not in C.MAIL_CITIES:
        return ("out", "zip under 10%% %s and mailing city not %s" % (C.COUNTY, C.COUNTY))
    if not addr_key(r["site_address"]):
        if city in C.MAIL_CITIES:
            return ("in", "unconfirmed", C.COUNTY + " mailing address, county unconfirmed (no street address to check)")
        return ("out", "split zip, no street address")
    q = "%s, %s, CO %s" % (re.sub(r"\s+", " ", r["site_address"]).strip(), r["city"].strip(), zp)
    return ("geo", q, zp, city, sh)


def scope_final(pre, gcache):
    if pre[0] != "geo":
        return pre
    _, q, zp, city, sh = pre
    res = gcache.get(q, "error")
    if res == C.COUNTY_FULL:
        why = "zip %s is split" % zp if sh is not None else "zip %s is not a %s zip" % (zp, C.COUNTY)
        return ("in", "denver", "Census geocoder places the address in %s (%s)" % (C.COUNTY_FULL, why))
    if res in ("no match", "error"):
        if city in C.MAIL_CITIES or (sh is not None and sh >= 0.5):
            return ("in", "unconfirmed", C.COUNTY + " mailing address, county unconfirmed (Census geocoder could not place it)")
        return ("out", "geocoder could not place it; mailing city not %s" % C.COUNTY)
    if city in C.MAIL_CITIES:
        return ("in", "unconfirmed", C.COUNTY + " mailing address, county unconfirmed (Census geocoder places it in %s)" % res)
    return ("out", "geocoder places it in %s; mailing city not %s" % (res, C.COUNTY))


# --------------------------------------------------------------------------- UCC
TRADE_DEBTOR = re.compile(r"construct|landscap|communicat|oilfield|chipseal|striping|excavat|asphalt|paving|brothers", re.I)


def classify_ucc_a(r):
    """Tier A UCC row that is in scope and has a business word in the debtor name -> (cut label or None, kind, note)."""
    rule = r["flag_rule"].split(":", 1)[-1].lower()
    words = [w.strip() for w in rule.split(",")]
    text = r["description"]
    both = rule + " | " + text
    name = r["company_name"]
    sp = r.get("secured_party", "")
    if C.UCC_PHARM_COPIER.search(sp):
        return ("ADDED: pharmacy and copier blanket liens where the flag word sits in boilerplate (Cardinal Health, Canon)", None, "")
    if C.UCC_PAVING.search(text) and not C.UCC_AIR.search(text):
        return ("paving and road-milling equipment ('pneumatic' rollers, Wirtgen milling machines)", None, "")
    if C.UCC_FORKLIFT.search(text) and not re.search(r"cnc|machining|lathe|robot|conveyor belt|air compressor", text, re.I):
        return ("forklifts and other lift or earthmoving equipment (Doosan, 'pneumatic' tyre)", None, "")
    if (set(words) & {"doosan", "pneumatic"}) and not (set(words) - {"doosan", "pneumatic"}):
        return ("forklifts and other lift or earthmoving equipment (Doosan, 'pneumatic' tyre)", None, "")
    if C.UCC_LAUNDRY.search(both + " " + name + " " + sp):
        return ("dry-cleaner and laundry boilers", None, "")
    if words == ["bottling"] and not re.search(r"bottling\s+(?:line|equipment|machine)", text, re.I):
        return ("'bottling' only in a debtor's own name (blanket liens)", None, "")
    if C.UCC_RESTAURANT.search(text) or (C.UCC_RESTAURANT_NAME.search(name) and not re.search(r"cnc|machining|lathe", both, re.I)):
        return (None, "ucc_weak", "restaurant, commissary-kitchen or survey equipment")
    has_air = any(C.UCC_AIR.search(w) for w in words)
    if has_air:
        if C.UCC_TOWABLE.search(text) or C.UCC_TOWABLE_LENDER.search(sp) or (TRADE_DEBTOR.search(name) and not C.UCC_MACH.search(both)):
            return (None, "ucc_weak", "towable construction compressor")
        return (None, "ucc_compressor", "")
    if C.UCC_MACH.search(both):
        return (None, "ucc_machinery", "")
    return (None, "ucc_weak", "flagged word without production machinery")


def ucc_word(r):
    return r["flag_rule"].split(":", 1)[-1].strip()


def mach_word(r):
    """First production-machinery word, for the fit text."""
    for w in [x.strip() for x in r["flag_rule"].split(":", 1)[-1].split(",")]:
        if C.UCC_MACH.search(w):
            return w
    m = C.UCC_MACH.search(r["description"])
    return m.group(0).lower() if m else ""


def load_flagged_big(S4, cuts):
    """One pass over the two large files: flagged rows, and the count of registrations per address and suite."""
    ucc, reg = [], []
    agent_count = Counter()
    for r in reader(S4, UCC):
        if r["flag_v2"] == "Y":
            ucc.append(r)
    for r in reader(S4, REG):
        for k in agent_keys(r) + (building_key(r),):
            if k:
                agent_count[k] += 1
        if r["flag_v2"] == "Y":
            reg.append(r)
    return ucc, reg, agent_count


def geocode_needs(ucc, reg, cre_rows, zshare, layer_keys):
    need = []
    for r in ucc:
        if r["debtor_name_has_entity_token"] != "Y":
            continue
        p = scope_pre(r, r["debtor_state"], zshare)
        if p[0] == "geo":
            need.append(p[1])
    for r in reg:
        p = scope_pre(r, r["principal_state"], zshare)
        if p[0] == "geo":
            need.append(p[1])
    for r in cre_rows:
        if r["flag"] == "Y" and r["city"].strip().upper() in C.CITY_OK and addr_key(r["site_address"]) and addr_key(r["site_address"]) not in layer_keys:
            need.append(cre_query(r))
    seen = set()
    out = []
    for q in need:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


def fit_sic(r):
    """Manufacturing SIC for the fit rule: the facility's own code when it is 2000-3999; another code on the row only when the
    main code is not a transport, wholesale or retail code (40-59). A distribution centre with one food code is not a plant."""
    main = r.get("sic_code", "").strip()
    if main.isdigit() and 2000 <= int(main) <= 3999:
        return main
    if main[:1] in ("4", "5"):
        return ""
    for x in re.split(r"[/;, ]+", r.get("other_sic_codes", "")):
        if x.isdigit() and 2000 <= int(x) <= 3999:
            return x
    return ""


def cre_query(r):
    return "%s, %s, CO" % (re.sub(r"\s+", " ", r["site_address"]).strip(), r["city"].strip().title() or C.COUNTY)


def sig(src, r, kind, tier, text, **kw):
    s = dict(src=src, rid=r["record_id"], date=r["record_date"], kind=kind, tier=tier, rule=r.get("flag_rule_v2") or r.get("flag_rule", ""),
             text=text, row=shared(r), addr=r["site_address"], ak=addr_key(r["site_address"]), unit=unit_of(r["site_address"]),
             zip=r["zip"][:5], city=r["city"].strip(), names=[], grade="", stage=None, small=False, bonus=0, flagged=True,
             section="denver", basis="", info={})
    s.update(kw)
    return s


def build_signals(S4, zshare, geocoder):
    """geocoder(list of queries) -> cache dict. Returns the lists and lookups used by v3_resolve."""
    cuts = Cuts()
    out = dict(named=[], address=[], naming=[], oedit=[], drops=[])

    if C.LOCAL_LAYERS and C.LOCAL_PERMIT_FILES is not None:
        import v3_local
        permits = v3_local.load_permits(S4, C.LOCAL_PERMIT_FILES, getattr(C, "LOCAL_DESC_USE_HOLD", False))
        sdp = v3_local.load_plans(S4, C.LOCAL_PLAN_FILES or [])
    else:
        permits = read_all(S4, PER) if C.LOCAL_LAYERS else []
        sdp = read_all(S4, SDP) if C.LOCAL_LAYERS else []
    water = read_all(S4, WAT)
    air = read_all(S4, AIR)
    cre = read_all(S4, CRE)
    oedit = read_all(S4, OED)
    layer_keys = set(addr_key(r["site_address"]) for r in permits) | set(addr_key(r["site_address"]) for r in sdp)
    layer_keys.discard("")
    out.update(permits=permits, sdp=sdp, water=water, air=air, cre=cre, layer_keys=layer_keys)

    ucc, reg, agent_count = load_flagged_big(S4, cuts)
    out["agent_count"] = agent_count
    out["geocode_needed"] = geocode_needs(ucc, reg, cre, zshare, layer_keys)
    gcache = geocoder(out["geocode_needed"])
    out["gcache"] = gcache

    snip = {}
    hp = os.path.join(S4, B1A_HITS)
    if os.path.exists(hp):
        with open(hp, newline="", encoding="utf-8-sig") as f:
            for h in csv.DictReader(f):
                snip[(h["record_id"], h["debtor_seq"])] = h["snippet"]

    # ------------------------------------------------------------------ UCC
    for tier in ("A", "B"):
        rows = [r for r in ucc if r["flag_tier"] == tier]
        src = "Colorado UCC filings, tier %s" % tier
        cuts.add(src, "flagged rows statewide", len(rows))
        for r in rows:
            sc = scope_final(scope_pre(r, r["debtor_state"], zshare), gcache)
            if sc[0] == "out":
                cuts.add(src, "outside %s scope (state, zip, mailing city, geocoder)" % C.COUNTY)
                continue
            if r["debtor_name_has_entity_token"] != "Y":
                cuts.add(src, "debtor name has no business word (may be an individual)")
                continue
            if nk(r["company_name"]) in C.PERSON_NAMED:
                cuts.add(src, "entity named after a private individual (left out by decision)")
                continue
            if r["transaction_type"] != "Initial Filing":
                cuts.add(src, "SBA continuation or other amendment (flags sit on initial filings only)")
                continue
            section, basis = sc[1], sc[2]
            agent = is_agent_address(r, agent_count)
            if agent:
                section = "unconfirmed"
                basis = C.COUNTY + " mailing address, county unconfirmed (address on file is a registered-agent or virtual-office suite; operating site unknown)"
            sp = r.get("secured_party", "")
            if tier == "A":
                cut, kind, note = classify_ucc_a(r)
                if cut:
                    cuts.add(src, cut)
                    continue
                if nk(r["company_name"]) in C.WEB_DROPS:
                    cuts.add(src, "dropped after the first run's web check (site is outside %s)" % C.COUNTY_FULL)
                    out["drops"].append((r["company_name"], C.WEB_DROPS[nk(r["company_name"])]))
                    continue
                word = ucc_word(r)
                if kind == "ucc_weak":
                    cuts.add(src, "kept at the weak tier (8 points): %s" % note)
                    text = "UCC %s: %s | %s (weak tier: %s)" % (r["record_date"], word, r["description"][:110], note)
                    grade = "weak"
                else:
                    text = "UCC %s: %s | %s" % (r["record_date"], word, r["description"][:110])
                    grade = "equipment"
                s = sig(UCC, r, kind, "A", text, grade=grade, section=section, basis=basis, seq=r["debtor_seq"],
                        names=[r["company_name"]], info=dict(sp=norm_party(sp), mach=mach_word(r) if kind != "ucc_weak" else "", note=note, agent=agent))
            else:
                rules = r["flag_rule_v2"].split("; ")
                ids = [x.split(" ", 1)[0] for x in rules]
                best = max(ids, key=lambda i: PTS["ucc_" + i.lower()])
                kind = "ucc_" + best.lower()
                desc = (snip.get((r["record_id"], r.get("debtor_seq", "")), "") if "full collateral text" in r["flag_rule_v2"] else "") or r["description"]
                lender = sp[:60] or "not given"
                hidden = ""
                if "B1c" in ids and C.AGENT_LENDER.search(sp):
                    hidden = " [lender not named: filed through an agent]"
                text = "UCC %s initial filing [tier B %s], secured party %s%s: %s" % (r["record_date"], "+".join(ids), lender, hidden, desc[:120] or "no collateral text")
                word = rules[ids.index(best)].rsplit(": ", 1)[-1]
                s = sig(UCC, r, kind, "B", text, grade="equipment" if kind == "ucc_b1a" else "weak", section=section, basis=basis, seq=r["debtor_seq"],
                        names=[r["company_name"]], info=dict(sp=norm_party(sp), mach=word if kind == "ucc_b1a" else "", word=word, agent=agent, hidden=bool(hidden)))
            cuts.add(src, "rows kept as signals")
            out["named"].append(s)

    # ------------------------------------------------------------------ registrations
    for tier in ("A", "B"):
        rows = [r for r in reg if r["flag_tier"] == tier]
        src = "Colorado business registrations, tier %s" % tier
        cuts.add(src, "flagged rows statewide", len(rows))
        for r in rows:
            if r["principal_state"] != "CO":
                cuts.add(src, "no Colorado address (foreign entity showing an out-of-state head office); kept for name matching only")
                continue
            sc = scope_final(scope_pre(r, "CO", zshare), gcache)
            if sc[0] == "out":
                cuts.add(src, "Colorado address outside %s scope" % C.COUNTY)
                continue
            if r["record_date"][:7] == "2026-02" and r.get("agent_organization_name", "").strip().lower() == "colorado registered agents inc":
                cuts.add(src, "February 2026 bulk filings through Colorado Registered Agents Inc")
                continue
            if is_agent_address(r, agent_count):
                cuts.add(src, "registered-agent or virtual-office address (10 or more 2024-26 registrations at the same address and suite)")
                continue
            if re.search(r"withdrawn|dissolved|converted|merged", r["entity_status"], re.I):
                cuts.add(src, "entity since withdrawn, dissolved, converted or merged")
                continue
            if nk(r["company_name"]) in C.PERSON_NAMED:
                cuts.add(src, "entity named after a private individual (left out by decision)")
                continue
            word = (r["flag_rule_v2"] or r["flag_rule"]).rsplit(": ", 1)[-1]
            if tier == "A":
                text = "Registered in Colorado %s (%s, %s); status %s; name word: %s" % (r["record_date"], r["record_type"], r.get("jurisdiction_of_formation", ""), r["entity_status"], word)
                kind = "reg_a"
            else:
                text = "Registered in Colorado %s (%s) [tier B B2a]; status %s; name word: %s" % (r["record_date"], r["record_type"], r["entity_status"], word)
                kind = "reg_b"
            cuts.add(src, "rows kept as signals")
            out["named"].append(sig(REG, r, kind, tier, text, grade="weak", section=sc[1], basis=sc[2], seq="", names=[r["company_name"]], info=dict(word=word)))

    # ------------------------------------------------------------------ Denver permits
    def ptext(r, tag=""):
        st = "cancelled " + r["cancel_date"] if r["cancel_date"] else ("finaled " + r["final_date"] if r["final_date"] else "not finaled")
        if r.get("_carried"):
            st += " (carried on under change-of-contractor record %s)" % r["_carried"]
        val = money(r["valuation"]) if (r["valuation"].strip() or C.LOCAL_PERMIT_FILES is None) else "no valuation"
        return "%s permit %s%s: %s, %s, received %s, issued %s, %s; parcel class %s, zone %s" % (
            C.COUNTY, r["record_id"], tag, r["class"], val, r["record_date"], r["date_issued"] or "n/a", st, r["parcel_class"] or "blank", r["zone_district"] or "blank")

    def permit_stage(r):
        fin = r.get("final_date", "")
        if r["class"] in C.NEW_CLASSES:
            return "under construction" if not fin else "operating and expanding"
        if not fin or fin >= D6:
            return "fit-out"
        return "operating and expanding"

    # A permit marked cancelled whose work carried on under a change-of-contractor record (same address, same valuation) is not cancelled.
    coc = defaultdict(list)
    for r in permits:
        if r["class"] == "Change of Contractor" and not r["cancel_date"]:
            coc[(addr_key(r["site_address"]), r["valuation"])].append(r)

    def really_cancelled(r):
        if not r["cancel_date"]:
            return False
        nxt = coc.get((addr_key(r["site_address"]), r["valuation"]))
        if nxt:
            r["final_date"] = max(x["final_date"] for x in nxt)
            r["cancel_date"] = ""
            r["_carried"] = nxt[0]["record_id"]
            return False
        return True

    srcA, srcB = C.PERMIT_LABEL + ", tier A", C.PERMIT_LABEL + ", tier B"
    A = [r for r in permits if r["flag_tier"] == "A"]
    cuts.add(srcA, "flagged rows", len(A))
    cuts.add(srcA, "zero-valuation permits in the full layer (never flagged in tier A; listed for the record)", sum(1 for r in permits if fnum(r["valuation"]) == 0))
    cuts.add(srcA, "flagged rows in the DIA neighborhood (all)", sum(1 for r in A if r["neighborhood"] == "DIA"))
    recent90 = 0
    for r in A:
        if r["neighborhood"] == "DIA" and (r["zone_district"] == "DIA" or re.search(r"\bpe[nñ]a\b", r["site_address"], re.I)):
            cuts.add(srcA, "DIA neighborhood on airport zoning or Pena Blvd (terminal and concourse tenant work)")
            continue
        if r["class"] in C.SKIP_CLASSES:
            cuts.add(srcA, "special events and change-of-contractor records")
            continue
        pc = r["parcel_class"]
        ip = pc.startswith("INDUSTRIAL") and not C.NOT_PRODUCTION_PARCEL.search(pc)
        iz = r["industrial_zoning"] == "Y"
        if not (ip or (iz and (pc == "" or pc.startswith("VACANT LAND")))):
            cuts.add(srcA, "assessor parcel class is not industrial (office, retail, housing, restaurant, hotel, stadium and similar), or no industrial zoning and no industrial parcel class")
            continue
        if really_cancelled(r):
            cuts.add(srcA, "ADDED in v3: permit cancelled, with no change-of-contractor record carrying the work on")
            continue
        if not addr_key(r["site_address"]):
            cuts.add(srcA, "no usable street address")
            continue
        if r["record_date"] >= "2026-07-13":
            recent90 += 1
        kind = "permit_new" if r["class"] in C.NEW_CLASSES else "permit_alt"
        v = fnum(r["valuation"]) or 0
        cuts.add(srcA, "rows kept as signals")
        out["address"].append(sig(PER, r, kind, "A", ptext(r), grade="address", stage=permit_stage(r), bonus=MILLION_BONUS if v >= 1e6 else 0,
                                  info=dict(pc=pc, zone=r["zone_district"], val=v, cls=r["class"])))
    cuts.add(srcA, "of the kept rows, received in the last 90 days (kept at full weight; the layer undercounts this window)", recent90)

    B = [r for r in permits if r["flag_tier"] == "B"]
    cuts.add(srcB, "flagged rows", len(B))
    for r in B:
        if really_cancelled(r):
            cuts.add(srcB, "permit cancelled")
            continue
        if not addr_key(r["site_address"]):
            cuts.add(srcB, "no usable street address")
            continue
        rid = r["flag_rule_v2"][:3]
        v = fnum(r["valuation"]) or 0
        bonus = 0
        if rid == "B3a" and v >= 250000:
            # Step 4b's B3a has no ceiling. A tier B permit of $250k or more belongs on the table's $250k lines (22 or 18, +3 at $1M).
            kind = "permit_new" if r["class"] in C.NEW_CLASSES else "permit_alt"
            bonus = MILLION_BONUS if v >= 1e6 else 0
            cuts.add(srcB, "rows kept as signals (B3a, $250k or more: scored on the table's $250k lines)")
        else:
            kind = "permit_b3a" if rid == "B3a" else "permit_b3b"
            cuts.add(srcB, "rows kept as signals (%s)" % ("B3a, $50k to $250k" if rid == "B3a" else "B3b, under $50k"))
        out["address"].append(sig(PER, r, kind, "B", ptext(r, " [tier B %s]" % rid), grade="address", stage=permit_stage(r), small=(rid == "B3b"), bonus=bonus,
                                  info=dict(pc=r["parcel_class"], zone=r["zone_district"], val=v, cls=r["class"])))

    # ------------------------------------------------------------------ site plans
    src = C.PLAN_LABEL
    cuts.add(src, "flagged rows (every row is flagged)", len(sdp))
    for r in sdp:
        if r["industrial_zoning"] != "Y":
            cuts.add(src, "not industrially zoned (housing and mixed use dominate); kept as supporting evidence by address")
            continue
        if not addr_key(r["site_address"]):
            cuts.add(src, "no usable street address")
            continue
        heavy = r["_heavy"] if "_heavy" in r else bool(re.match(r"^I-[AB]\b", r["zone_district"]))
        kind = "sdp_heavy" if heavy else "sdp_imx"
        text = "%s %s %s opened %s, status %s, zone %s%s" % (C.COUNTY, r["record_type"], r["record_id"], r["record_date"], r.get("status", ""), r["zone_district"], "" if heavy else " (industrial mixed use)")
        cuts.add(src, "rows kept as signals")
        out["address"].append(sig(SDP, r, kind, "A", text, grade="address", stage="planned", info=dict(zone=r["zone_district"])))

    # ------------------------------------------------------------------ water permits
    src = "State water permits (WQCD)"
    fl = [r for r in water if r["flag"] == "Y"]
    cuts.add(src, "flagged rows statewide", len(fl))
    den = [r for r in fl if r["county"].strip().upper() == C.COUNTY_UP]
    cuts.add(src, "flagged rows with county %s" % C.COUNTY, len(den))
    cuts.add(src, "flagged rows with a %s mailing city but another county in the source (left out: the source states the county)" % C.COUNTY,
             sum(1 for r in fl if r["city"].strip().upper() in C.MAIL_CITIES and r["county"].strip().upper() not in (C.COUNTY_UP, "")))
    kept_water = set()
    for r in den:
        rt = r["record_type"]
        sic = r.get("sic_code", "")
        sics = [x for x in re.split(r"[/;, ]+", sic + "/" + r.get("other_sic_codes", "")) if x]
        mfg = [x for x in sics if x.isdigit() and 2000 <= int(x) <= 3999]
        nm = r["company_name"] + " " + r.get("permittee", "")
        construction = rt.startswith(C.CONSTRUCTION_WATER)
        named_fac = "company-named facility" in r["flag_rule"]
        if rt.startswith("COR900000") and "2024-05-01" <= r["record_date"] <= "2024-07-31":
            cuts.add(src, "industrial stormwater general-permit renewal wave, May to July 2024 (existing plants re-applying; kept as identity and SIC evidence)")
            continue
        iss = r.get("issued_date", "")
        if iss and r["record_date"] > iss and (int(r["record_date"][:4]) - int(iss[:4])) * 12 + int(r["record_date"][5:7]) - int(iss[5:7]) > 12:
            cuts.add(src, "renewals (received more than a year after issue)")
            continue
        if C.WAT_WASTE.search(nm) or sic in ("4952", "4953", "4212"):
            cuts.add(src, "wastewater plants, hauling and detention or water-quality facilities")
            continue
        if C.WAT_AIRPORT.search(nm + " " + r["site_address"]) or sic in C.WAT_AIRPORT_SIC:
            cuts.add(src, "airport construction and airline facilities at DEN (same reason as the DIA permit cut)")
            continue
        if C.WAT_PORTABLE.search(r["site_address"] + " " + r["city"]):
            cuts.add(src, "portable plants with no fixed site")
            continue
        if construction and not mfg and not named_fac:
            cuts.add(src, "flagged on acreage alone (no manufacturing SIC, no company-named facility): schools, parks, housing, roads, pipelines")
            continue
        s2 = sic[:2]
        if (not mfg and s2 in ("15", "16", "17", "41", "49", "52", "53", "54", "55", "56", "57", "58", "59", "65", "82", "91", "92", "95")) or C.WAT_RETAIL_NAME.search(r["company_name"]):
            cuts.add(src, "transit, public works, retail and contractor-coded sites with no manufacturing SIC")
            continue
        kind = "water_construction" if construction else "water_new"
        text = "Water permit %s (%s) received %s: facility %s, permittee %s, SIC %s %s, status %s" % (
            r["record_id"], rt.split("-")[0].strip(), r["record_date"], r["company_name"], r.get("permittee", ""), sic or "none", r.get("sic_description", ""), r.get("permit_status", ""))
        names = [r["company_name"]] + ([r["permittee"]] if (not construction and r.get("permittee")) else [])
        cuts.add(src, "rows kept as signals")
        kept_water.add(r["record_id"])
        out["named"].append(sig(WAT, r, kind, "A", text, grade="operator", stage="under construction" if construction else "operating and expanding",
                                basis="county field in state water permit record", seq="", names=names, info=dict(sic=fit_sic(r), sic_desc=r.get("sic_description", ""))))
    # naming rows: every Denver County water row that names an operator (kept or not), for assumption 5 and for the SIC evidence
    for r in water:
        if r["county"].strip().upper() != C.COUNTY_UP or r["record_id"] in kept_water:
            continue
        rt = r["record_type"]
        construction = rt.startswith(C.CONSTRUCTION_WATER)
        sics = [x for x in re.split(r"[/;, ]+", r.get("sic_code", "") + "/" + r.get("other_sic_codes", "")) if x]
        mfg = [x for x in sics if x.isdigit() and 2000 <= int(x) <= 3999]
        text = "Water permit row %s (%s) received %s: facility %s, permittee %s, SIC %s, status %s (cut as noise or not flagged; support only)" % (
            r["record_id"], rt.split("-")[0].strip(), r["record_date"], r["company_name"], r.get("permittee", ""), r.get("sic_code", "") or "none", r.get("permit_status", ""))
        names = [r["company_name"]] + ([r["permittee"]] if (not construction and r.get("permittee")) else [])
        s = sig(WAT, r, "noise", "A" if r["flag"] == "Y" else "", text, grade="operator" if not construction else "project", flagged=False,
                basis="county field in state water permit record", seq="", names=names, info=dict(sic="" if construction else fit_sic(r), sic_desc=r.get("sic_description", ""), construction=construction))
        out["naming"].append(s)

    # ------------------------------------------------------------------ air permits
    src = "APCD air permit status"
    fl = [r for r in air if r["flag"] == "Y"]
    cuts.add(src, "flagged rows statewide (not oil and gas)", len(fl))
    cuts.add(src, "rows whose county column says %s but AIRS prefix is not %s (left out; office address in place of the site)" % (C.COUNTY, C.AIRS_PREFIX),
             sum(1 for r in fl if r["county"].strip().upper() == C.COUNTY_UP and not r["airs_id"].startswith(C.AIRS_PREFIX)))
    den = [r for r in fl if r["airs_id"].startswith(C.AIRS_PREFIX)]
    cuts.add(src, "flagged rows with AIRS prefix %s (%s)" % (C.AIRS_PREFIX, C.COUNTY), len(den))
    for r in den:
        d = r["description"]
        nm = r["company_name"]
        cut = None
        if r.get("sector") == "fuel_retail":
            cut = "fuel stations and bulk fuel"
        elif (C.AIR_GENERATOR.search(d) or not d.strip()) and not re.search(r"paint|plating|batch|baking|bakery|manufactur|dynamom|grain|sugar|silo|boiler", d, re.I):
            cut = "emergency generators and fire pumps only (data centres, telecom, hotels, city buildings)"
        elif C.AIR_INSTITUTION.search(nm + " " + d):
            cut = "hospitals, crematories, prisons, utilities, airport and city facilities, data centres, land development"
        elif not addr_key(r["site_address"]):
            cut = "no street address for the site"
        if cut:
            cuts.add(src, cut)
            text = "Air permit row %s (%s) received %s: %s; AIRS %s (cut as noise: %s; support only)" % (r.get("permit_number", ""), r["record_type"], r["record_date"], d[:70], r["airs_id"], cut.split(" (")[0])
            out["naming"].append(sig(AIR, r, "noise", "A", text, grade="operator", flagged=False, basis="AIRS ID prefix %s (%s) in air permit record" % (C.AIRS_PREFIX, C.COUNTY), seq="",
                                     names=[nm], info=dict(datacentre=bool(re.search(r"data cent|coresite|iron mountain|intelishift", nm + " " + d, re.I)))))
            continue
        apen = bool(C.AIR_APEN.search(r["record_type"]))
        kind = "air_apen" if apen else "air_process"
        old = " (received before 2024; still in the six-month processing window)" if r["record_date"] < "2024-01-01" else ""
        text = "Air permit %s (%s) received %s%s: %s; AIRS %s" % (r.get("permit_number", ""), r["record_type"], r["record_date"], old, d[:80], r["airs_id"])
        cuts.add(src, "rows kept as signals")
        out["named"].append(sig(AIR, r, kind, "A", text, grade="operator", stage="operating and expanding", basis="AIRS ID prefix %s (%s) in air permit record" % (C.AIRS_PREFIX, C.COUNTY), seq="",
                                names=[nm], info=dict(moderate=bool(C.AIR_MODERATE.search(d + " " + nm)), desc=d)))

    # ------------------------------------------------------------------ Mile High CRE
    src = "Mile High CRE"
    fl = [r for r in cre if r["flag"] == "Y"]
    cuts.add(src, "flagged rows statewide (industrial category)", len(fl))
    den = [r for r in fl if r["city"].strip().upper() in C.CITY_OK]
    cuts.add(src, "flagged rows with city %s" % (C.COUNTY if not C.SPLIT_CITIES else "in " + C.COUNTY_FULL + " or a split city"), len(den))
    for r in den:
        ak = addr_key(r["site_address"])
        if not ak:
            cuts.add(src, "no single street address (market reports, portfolio sales, round-ups)")
            continue
        if nk(r["company_name"]) in C.WEB_DROPS:
            cuts.add(src, "dropped after the first run's web check (site is outside %s)" % C.COUNTY_FULL)
            continue
        if ak in layer_keys:
            section, basis = "denver", "address is in the %s permit or site plan layer (%s only)" % (C.COUNTY, C.COUNTY)
        else:
            res = gcache.get(cre_query(r), "error")
            if res == C.COUNTY_FULL:
                section, basis = "denver", "Census geocoder places the address in %s (press address, no zip in the source)" % C.COUNTY_FULL
            elif res in ("no match", "error"):
                section, basis = "unconfirmed", C.COUNTY + " mailing address, county unconfirmed (Census geocoder found no match for the press address)"
            elif r["city"].strip().upper() in C.SPLIT_CITIES:
                cuts.add(src, "split-city mailing address that the Census geocoder places outside %s" % C.COUNTY_FULL)
                continue
            else:
                section, basis = "unconfirmed", C.COUNTY + " mailing address, county unconfirmed (Census geocoder places it in %s)" % res
        head = r["description"].split(" | ")[0]
        text = "Mile High CRE %s names this address: %s" % (r["record_date"], head[:110])
        cuts.add(src, "rows kept as address signals")
        out["address"].append(sig(CRE, r, "press_addr", "A", text, grade="address", section=section, basis=basis, info={}))

    # ------------------------------------------------------------------ OEDIT
    src = "OEDIT EDC approvals"
    cuts.add(src, "flagged rows (every row is flagged)", len(oedit))
    for r in oedit:
        if r.get("source_kind") == "minutes":
            cuts.add(src, "rows from minutes (mostly non-industrial)")
            continue
        blob = " ".join([r.get("county", ""), r.get("description", ""), r.get("notes", "")])
        if not re.search(re.escape(C.COUNTY.lower()), blob, re.I):
            cuts.add(src, "no %s or Metro %s reference" % (C.COUNTY_FULL, C.COUNTY))
            continue
        cb = r.get("county_basis", "")
        if r.get("county", "").strip().lower() == C.COUNTY_FULL.lower():
            basis = "OEDIT post: " + (cb or "stated")
        else:
            basis = "OEDIT post: Metro %s under consideration" % C.COUNTY if re.search(r"under consideration|considered|metro " + re.escape(C.COUNTY.lower()), blob, re.I) else "OEDIT post: wage benchmark only"
        if cb == "wage benchmark only" and r.get("county", "").strip().lower() == C.COUNTY_FULL.lower():
            basis = "OEDIT post: wage benchmark only"
        jobs = (" jobs %s" % r["jobs"]) if r.get("jobs") else ""
        twin = (" [%s]" % r["notes"][:60]) if re.search(r"same (?:project|company)", r.get("notes", "") + r.get("description", ""), re.I) else ""
        text = "OEDIT %s %s: %s;%s%s" % (r["record_date"], r.get("program", ""), r["description"][:150], jobs, twin)
        cuts.add(src, "rows kept as code-name candidates")
        out["oedit"].append(sig(OED, r, "oedit", "A", text, grade="oedit", stage="planned", section="oedit", basis=basis, names=[r["company_name"]]))

    out["cuts"] = cuts.rows
    return out
