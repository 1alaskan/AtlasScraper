#!/usr/bin/env python3
"""Step 5 v3, part 3: scoring. The points table is fixed (v3_lib.PTS). Three scale factors exist only for the
sensitivity check: recency, the independent-source bonus, and tier B points."""
import re
from collections import Counter, defaultdict

from v3_lib import *
import v3_config as C

BASE = dict(rec=1.0, src=1.0, b=1.0)


def base_pts(e, P):
    p = PTS[e["kind"]] + e.get("bonus", 0)
    if e["kind"] in TIER_B_KINDS:
        p *= P["b"]
    return p


def eff_pts(e, P):
    p = base_pts(e, P)
    return p if e["cls"] == "confirmed" else p / 2.0


def stage_of(a):
    """-> (label, points)"""
    best = ("unknown", 0, "")
    equip_months, recent, older = set(), False, False
    cands = []
    for e in a.sigs:
        if not e["flagged"]:
            continue
        if e["kind"] in ("ucc_compressor", "ucc_machinery", "ucc_b1a"):
            if e["cls"] != "confirmed":
                continue
            equip_months.add(e["date"][:7])
            if e["date"] >= D12:
                recent = True
                cands.append(("buying equipment", STAGE_PTS["buying equipment"], ""))
            else:
                older = True
                cands.append(("operating and expanding", STAGE_PTS["operating and expanding"], ""))
        elif e.get("stage"):
            pts = STAGE_PTS[e["stage"]]
            tag = ""
            if e.get("small") and pts > SMALL_PERMIT_STAGE_CAP:
                pts = SMALL_PERMIT_STAGE_CAP
                tag = " (permit under $50k)"
            cands.append((e["stage"], pts, tag))
    if cands:
        best = max(cands, key=lambda c: (c[1], -STAGE_ORDER.index(c[0]), c[2] == ""))
    label, pts, tag = best
    if label == "buying equipment" and older and len(equip_months) >= 2:
        return ("buying equipment (repeat buyer; operating and expanding)", pts)
    if label == "unknown":
        kinds = set(e["kind"] for e in a.sigs if e["flagged"])
        if kinds & {"ucc_weak"}:
            return ("unknown (equipment filing not production-specific)", 0)
        if kinds & {"ucc_b1b", "ucc_b1c"}:
            return ("unknown (blanket or vague lien only)", 0)
        if kinds & {"ucc_compressor", "ucc_machinery", "ucc_b1a"}:
            return ("unknown (equipment filing is a possible match only)", 0)
        return ("unknown (registration or press mention only)", 0)
    return (label + tag, pts)


def parcel_fit(pc):
    if re.search(r"FOOD PROCESSING|FACTORY|MEAT PACKING|PRINTING PLANT", pc):
        return ("strong", "assessor class is %s; occupier not identified" % pc.title())
    if "WAREHOUSE" in pc:
        return ("unknown", "industrial warehouse parcel; could be production or storage, occupier not identified")
    if re.search(r"AUTO SERVICE|CAR WASH|SERVICE STATION", pc):
        return ("moderate", "auto, tyre, concrete, print or similar trade by parcel class (%s)" % pc.title())
    if re.search(r"RESIDENTIAL|SFR|HOTEL|MOTEL|SCHOOL|CHURCH|JAIL|STADIUM|ENTERTAINMENT|BOARDING|CONDOMINIUM", pc):
        return ("weak", "assessor class is %s" % pc.title())
    return ("unknown", "industrially zoned site; use and occupier not identified (assessor class %s)" % (pc.title() or "blank"))


def fit_of(a):
    """-> (level, text). Order: web check; manufacturing SIC on a water permit; equipment named in a UCC filing; lien held by a
    machinery maker; kitchen or survey equipment; maker word in the name; process units on an air permit; trade word; weak word.
    A name that carries both a maker word and a weak word (Foundry Underwriting, Aerospace Software) is read as weak, as in the tier B run."""
    if a.kind == "oedit":
        return ("unknown", "code name only; nothing in the records says what the company makes")
    if a.kind == "address":
        if a.step3:
            return a.step3["fit"]
        for e in a.sigs:
            pr = e["info"].get("project", "") if e["src"] == WAT else ""
            if pr and (C.PROJECT_WEAK.search(pr) or (e["info"].get("activity", "").strip().lower() == "residential")):
                return ("weak", "a state stormwater permit at this address describes a housing, school, utility or solar project ('%s')" % pr[:60])
        pcs = Counter(e["info"].get("pc", "") for e in a.sigs if e["src"] == PER and e["flagged"])
        if pcs:
            return parcel_fit(pcs.most_common(1)[0][0])
        if any(e["src"] == SDP and e["flagged"] for e in a.sigs):
            return ("unknown", "industrially zoned site; use and occupier not identified")
        return ("unknown", "press mention of an industrial property; use and occupier not identified")
    for k in a.names:
        for table in (C.WEB_CHECKS_V3, C.WEB_CHECKS):
            if k in table:
                return table[k]
    conf = [e for e in a.sigs if e["cls"] == "confirmed"]
    for e in conf:
        if e["src"] == WAT and e["info"].get("sic"):
            return ("strong", "manufacturing SIC %s on a state water permit" % e["info"]["sic"])
    eq = [e for e in conf if e["kind"] in ("ucc_machinery", "ucc_compressor") and e["info"].get("mach")]
    if eq:
        e = max(eq, key=lambda e: e["date"])
        return ("strong", "finances production machinery in a UCC filing (%s)" % e["info"]["mach"])
    eq = [e for e in conf if e["kind"] == "ucc_b1a"]
    if eq:
        e = max(eq, key=lambda e: e["date"])
        return ("strong", "finances process equipment in a UCC filing (%s)" % e["info"].get("mach", ""))
    if any(e["kind"] == "ucc_b1b" and C.VENDORS.search(e["info"].get("sp", "")) for e in conf):
        return ("strong", "equipment lien held by a machinery maker or dealer; not confirmed")
    if any(e["kind"] == "ucc_weak" and e["info"].get("note", "").startswith("restaurant") for e in conf):
        return ("weak", "restaurant, commissary-kitchen or survey equipment in the filing; little process air")
    nm = list(a.names.values())
    weak = [C.FIT_WEAK.search(n) for n in nm]
    strong = [C.FIT_STRONG.search(n) for n, w in zip(nm, weak) if not w]
    strong = [m for m in strong if m]
    if strong:
        return ("strong", "name suggests manufacturing or processing (%s); not confirmed" % strong[0].group(1).title())
    airk = [e for e in conf if e["src"] == AIR and e["flagged"]]
    airp = [e for e in airk if e["kind"] == "air_process"]
    if airp:
        d = " ".join(e["info"].get("desc", "") for e in airp)
        if re.search(r"dynamom", d, re.I):
            return ("moderate", "engine or vehicle test cells on the air permit; modest air demand")
        if any(e["info"].get("moderate") for e in airp):
            return ("moderate", "concrete batch plant on the air permit; modest air demand")
        return ("strong", "process emission units on an air permit")
    mod = [C.FIT_MOD.search(n) for n, w in zip(nm, weak) if not w]
    mod = [m for m in mod if m]
    if mod:
        return ("moderate", "auto, tyre, concrete, print or similar trade by name (%s); small or intermittent air use likely" % mod[0].group(1).title())
    if any(e["src"] == AIR and e["info"].get("datacentre") for e in conf):
        return ("weak", "data centre (cooling and standby power, little process air)")
    weak = [w for w in weak if w]
    if weak:
        return ("weak", "name suggests office, energy, software, retail, housing or logistics (%s)" % weak[0].group(1).title())
    if any(re.search(r"paint|booth|plating|solvent|haps?\b|coating", e["info"].get("desc", ""), re.I) for e in airk):
        return ("strong", "process emission units on an air permit")
    cutair = [e for e in conf if e["src"] == AIR and not e["flagged"] and "cut as noise" in e["text"]]
    if cutair and not any(e["flagged"] and e["src"] in (UCC, WAT) for e in conf):
        why = re.search(r"cut as noise: ([^;)]+)", cutair[0]["text"])
        return ("weak", "the only state record is an air permit row cut as noise (%s)" % (why.group(1) if why else "generator or fuel"))
    return ("unknown", "nothing in the records says what the company makes")


def score(a, P=BASE):
    """-> dict(per, signal, sources, recency, stage, fit, total, ...). per[source] = (best, repeat)."""
    per = {}
    months = defaultdict(set)
    rows = []
    for e in a.sigs:
        ef = eff_pts(e, P)
        e["_eff"] = ef
        k = e["src"]
        if ef > per.get(k, (0.0, 0.0))[0]:
            per[k] = (ef, 0.0)
        if ef >= REPEAT_MIN and e["date"]:
            months[k].add(e["date"][:7])
    for k in list(per):
        n = len(months[k])
        rep = min(REPEAT_MAX, REPEAT_PTS * (n - 1)) if n > 1 else 0
        per[k] = (per[k][0], float(rep))
    vals = [b for b, _ in per.values() if b > 0]
    sig_n = sum(1 for v in vals if v >= SRC_SIGNAL_MIN)
    sup_n = sum(1 for v in vals if v < SRC_SIGNAL_MIN)
    if sig_n >= 1:
        bonus = min(SRC_BONUS_MAX, SRC_BONUS * (sig_n - 1)) + min(SUP_BONUS_MAX, SUP_BONUS * sup_n)
    else:
        bonus = min(SUP_BONUS_MAX, SUP_BONUS * max(0, sup_n - 1))
    bonus *= P["src"]
    dated = [e["date"] for e in a.sigs if e["_eff"] >= REC_MIN and e["date"]]
    latest = max(dated) if dated else ""
    rec = (REC_12 if latest >= D12 else REC_24 if latest >= D24 else 0) * P["rec"] if latest else 0
    st = stage_of(a)
    ft = fit_of(a)
    signal = sum(b + r for b, r in per.values())
    total = signal + bonus + rec + st[1] + FIT_PTS[ft[0]]
    alld = [e["date"] for e in a.sigs if e["date"]]
    return dict(per=per, signal=signal, sources=bonus, recency=rec, stage=st, fit=ft, total=total,
                first=min(dated) if dated else (min(alld) if alld else ""), latest=latest or (max(alld) if alld else ""))


def points_text(sc):
    order = sorted(sc["per"].items(), key=lambda kv: -(kv[1][0] + kv[1][1]))
    parts = "; ".join("%s: %s%s" % (C.SRC_LABEL.get(k, SHORT.get(k, k)), g(b), ("+%s repeat" % g(r)) if r else "") for k, (b, r) in order if b + r > 0)
    return "Points: signal %s (%s); sources %s; recency %s; stage %s; fit %s" % (
        g(sc["signal"]), parts, g(sc["sources"]), g(sc["recency"]), g(sc["stage"][1]), g(FIT_PTS[sc["fit"][0]]))
