#!/usr/bin/env python3
"""County permit and planning layers for counties other than Denver.

Denver's two layers (scrape_denver_commercial_permits_v2.csv, scrape_denver_site_plans.csv) are read as they are. For another county
the config names its Step 3 permit files (LOCAL_PERMIT_FILES) and planning files (LOCAL_PLAN_FILES), pulled in the shared 17-column
format with the Step 3 flag rules, and this module maps each row onto the fields the Denver code expects, so the points table and the
rest of the method do not change. Added 2026-10-31 for the Adams County run (decision 1A); the Denver rebuild after the change was
compared byte for byte with the committed Denver output.

Mapping, permits:
  flag_tier       A for a Step 3 tier A rule; B for B3a and B3b; blank otherwise, with these holds (second review, 2026-10-31):
                  - low-value permit types and work (fences, signs, alarms, fire sprinklers, hoods, plan revisions, temporary uses, meters,
                    demolition, racking, generators, tanks, trailers, solar, poles, cameras, canopies, sheds, fuel storage) are held at B3b
                    whatever the Step 3 rule said, because the Denver table scores them as small permits (6 points), not as construction;
                  - Aurora sub-permits (record ids not ending -000-00: fire alarm, sprinkler, gas detection records that inherit the
                    parent's type and valuation) are held at B3b;
                  - Aurora intake and permit twins (the same normalised scope on two or more parent records, same day included) keep the
                    tier on the earliest record only; the others become unflagged support, so one scope is counted once;
                  - commercial, not industrial, use buildings (mercantile, business, hotel, assembly, educational, institutional, animal
                    shelter) are held at B3a, as is "Commercial Miscellaneous";
                  - on the Adams County layer, which has no valuation, tier A needs a construction permit type (tenant finish, warehouse,
                    core and shell, office, change in use) or, for "Other / New, Addition or Alteration", a construction word in the
                    description itself; and a description free of the small-equipment words above; everything else is B3b;
                  - rows at an apartment-style address are left out.
  flag_rule_v2    starts with "B3a " or "B3b " for tier B, as the Denver tier B script wrote it; the Step 3 rule follows.
  class           New Building, Addition or Alteration/Tenant Finish, from the permit type and type of work words. Denver's other
                  classes (Foundation Only, Phased Construction, New Non-Building Structure, Special Event, Change of Contractor) are
                  not produced.
  valuation       the layer's valuation where it carries one (Thornton, Aurora); blank for the Adams County layer.
  date_issued, final_date, cancel_date   issue date, certificate-of-occupancy or finaled date, and a cancel or expiry date, where the
                  layer carries them. The Adams County layer has a status but no status date: a finaled, closed or C of O status sets
                  final_date to the record date (the stage then reads operating and expanding rather than fit-out). A permit with no
                  final date is treated as not finaled (fit-out stage), as in Denver.
  parcel_class    blank (no assessor class on these layers); industrial_zoning = Y on every flagged row, because every Step 3 rule
                  requires industrial property, zoning or an industrial word. Denver's tier A test (industrial parcel class, or industrial
                  zoning with no parcel class) therefore passes for flagged rows. Address rows built from these layers get no parcel-class fit.
  zone_district   the zoning code where the layer carries one (Aurora); blank otherwise. neighborhood blank (the DIA cut never fires).

Mapping, planning and development cases:
  industrial_zoning   Y when the Step 3 industrial_use column is Y.
  _heavy              True when industrial_use is Y and the case is a site, development or planning case (not a liquor licence, a bare plat,
                      a residential subdivision or a pre-application); such rows score as sdp_heavy (12), the rest as sdp_imx (6).
  zone_district, status, record_type   as the layer gives them.
"""
import csv, os, re

LOW_VALUE = re.compile(r"\b(fences?|signs?|alarms?|fire sprinklers?|sprinklers?|hoods?|plan revisions?|temporary|temp meter|meters?|demoli\w*|demo|roof\w*|"
                       r"antennas?|awnings?|canop(?:y|ies)|pools?|solar|re-?roof\w*|siding|windows?|door replacement|grading|right of way|"
                       r"racking|racks?|pallet rack\w*|high piled|generators?|tanks?|tank battery|trailers?|poles?|cameras?|sheds?|cages?|"
                       r"fuel storage|fuel canopy|fireworks|scales?|retaining wall|light pole|well pump|monument|flagpole|dumpster|bollards?)\b", re.I)
NON_PLANT_DESC = re.compile(r"mercantile|retail|restaurant|hotel|church|school|daycare|clinic|dental|medical office|car wash|carwash|gas station|convenience|"
                            r"well pad|oil and gas pad|tank battery|wellsite|well site|multi.?family|apartment|townhome|clubhouse", re.I)
COMMERCIAL_USE = re.compile(r"mercantile|business use|hotel|assembly|educational|institutional|animal shelter|commercial miscellaneous|daycare|church|school", re.I)
ADAMS_CONSTRUCTION = re.compile(r"tenant finish|warehouse|core\s*&\s*shell|core and shell|office|addition|change in use|manufactur|industrial|plant|"
                                r"building|sq\.? ?ft|square f|suite|shell|factory|process", re.I)
CONSTRUCTION_DESC = re.compile(r"tenant finish|tenant improvement|build.?out|new building|new \d[\d,]* ?(?:sq|sf|square|unit|bay|building)|addition|sq\.? ?ft|square f|remodel|interior|"
                               r"core\s*(?:&|and)\s*shell|shell building|mezzanine|production|manufactur|process|clean ?room|expansion|new facility|"
                               r"ground.?up|new construction|new warehouse|new office|compressor|instrument air|air skid|process equipment|production line", re.I)
APT = re.compile(r"\b(apt|apartment)\b\.?\s*#?\s*[A-Z0-9-]+", re.I)
NEW_WORDS = re.compile(r"\bnew\b|core\s*&\s*shell|core and shell|new construction|shell building|use building\b", re.I)
ADD_WORDS = re.compile(r"\baddition\b|\badd\b", re.I)
PLAN_SKIP = re.compile(r"liquor|marijuana|residential|single.?family|pre-?application|presubmittal|conceptual review\b.*\bresidential|"
                       r"vacation|variance|sign|temporary|fence|alarm|animal shelter|cell tower|telecom|antenna|parking|landscap", re.I)
PLAN_HEAVY = re.compile(r"site plan|development plan|development permit|planning project|planning case|commercial new|industrial|"
                        r"pud|use by special review|conditional use|rezone|conceptual|concept", re.I)


def _blank(keys, r):
    for k in keys:
        r.setdefault(k, "")
    return r


def _tier(rule):
    u = rule.lower()
    if u.startswith("tier a") or "250k+" in u or u.startswith("a:"):
        return "A", rule
    if "b3a" in u or "50k to 250k" in u:
        return "B", "B3a " + rule
    if "b3b" in u or "under 50k" in u:
        return "B", "B3b " + rule
    return "", rule


def _class(r):
    words = " ".join([r.get("record_type", ""), r.get("permit_type", ""), r.get("type_of_work", ""), r.get("permit_subtype", ""), r.get("class_of_work", "")])
    if ADD_WORDS.search(words):
        return "Addition"
    if NEW_WORDS.search(words) and not re.search(r"tenant|alteration|remodel|improvement|revision", words, re.I):
        return "New Building"
    return "Alteration/Tenant Finish"


def _cancel(r):
    st = (r.get("status", "") or "").lower()
    if re.search(r"expired|cancel|void|withdrawn|denied", st):
        return r.get("date_expiration", "") or r.get("status_date", "") or r["record_date"]
    return ""


def _final(r):
    st = (r.get("status", "") or "").lower()
    d = r.get("co_date", "") or r.get("final_date", "")
    if d:
        return d[:10]
    if re.search(r"final|c of o|closed", st) and not re.search(r"expired", st):
        return r.get("status_date", "")[:10] or r.get("date_issued", "")[:10] or r.get("issue_date", "")[:10] or r["record_date"][:10]
    return ""


def load_permits(s4, files, desc_use_hold=False):
    out = []
    for f in files:
        rows = []
        with open(os.path.join(s4, f), newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                rows.append(dict(r))
        aurora = any(r.get("scope_key") for r in rows[:50])
        no_val = not any((r.get("valuation") or "").strip() for r in rows[:200])
        # Aurora: the earliest parent record per scope keeps the tier; later (or same-day, higher-numbered) twins become support.
        # The scope key is normalised: the "SCOPE OF WORK INCLUDE(S)" tail, "ON HOLD" and the "11 622" style prefixes differ between the
        # intake and the permit record of the same job.
        def scope(r):
            k = (r.get("scope_key") or "").upper()
            k = re.sub(r"\s*SCOPE OF WORK.*$", "", k)
            k = re.sub(r"\s*ON HOLD\s*$", "", k)
            k = re.sub(r"\|\s*\d[\d ]*", "| ", k)
            return re.sub(r"\s+", " ", k).strip()
        first = {}
        if aurora:
            for r in rows:
                if r["record_id"].endswith("-000-00") and r.get("scope_key"):
                    k = scope(r)
                    key = (r["record_date"], r["record_id"])
                    if k not in first or key < first[k]:
                        first[k] = key
        for r in rows:
            if APT.search(r.get("site_address", "")):
                continue
            tier, rule = ("", r.get("flag_rule", ""))
            if r.get("flag") == "Y":
                tier, rule = _tier(r.get("flag_rule", ""))
                words = " ".join([r.get("record_type", ""), r.get("type_of_work", ""), r.get("permit_subtype", ""), r.get("permit_type", "")])
                desc = r.get("description", "")
                if aurora and not r["record_id"].endswith("-000-00"):
                    tier, rule = "B", "B3b " + rule + " (held at B3b: sub-permit of a parent folder)"
                elif aurora and r.get("scope_key") and first.get(scope(r)) and (r["record_date"], r["record_id"]) > first[scope(r)]:
                    tier, rule = "", rule + " (unflagged: later twin of an earlier record with the same scope)"
                elif tier in ("A", "B") and "B3b" not in rule and re.search(r"demoli|\bdemo\b|racking|pallet rack|high.?piled|deferred submittal", words + " " + desc[:120], re.I):
                    tier, rule = "B", "B3b " + rule + " (held at B3b: demolition, racking or a deferred submittal)"
                elif tier in ("A", "B") and "B3b" not in rule and LOW_VALUE.search(words) and not re.search(r"warehouse|factory|manufactur|plant|core|shell|tenant", words, re.I):
                    tier, rule = "B", "B3b " + rule + " (held at B3b: low-value permit type)"
                elif tier in ("A", "B") and "B3b" not in rule and LOW_VALUE.search(desc[:160]) and not CONSTRUCTION_DESC.search(desc[:200]):
                    tier, rule = "B", "B3b " + rule + " (held at B3b: low-value work in the description)"
                elif tier == "A" and COMMERCIAL_USE.search(words):
                    tier, rule = "B", "B3a " + rule + " (held at B3a: commercial, not industrial, use building)"
                elif tier == "A" and no_val and desc_use_hold and NON_PLANT_DESC.search(desc[:160]):
                    # Layers with no valuation and generic permit types (Frederick) carry the use only in the description.
                    # Added 2026-11-06 after the Weld review; on only where the county config sets LOCAL_DESC_USE_HOLD = True (Weld), so Adams and Denver are unchanged.
                    tier, rule = "B", "B3a " + rule + " (held at B3a: commercial use or well pad in the description, no valuation on the layer)"
                elif tier == "A" and no_val and not (ADAMS_CONSTRUCTION.search(re.sub(r"\bother\s*/\s*(new|addition|alteration)\b", "", words, flags=re.I)) or CONSTRUCTION_DESC.search(desc[:200])):
                    tier, rule = "B", "B3b " + rule + " (held at B3b: no valuation and no construction word)"
            r["flag_tier"] = tier
            r["flag_rule_v2"] = rule
            r["class"] = _class(r)
            r["valuation"] = (r.get("valuation", "") or "").replace("$", "").replace(",", "").strip()
            r["date_issued"] = (r.get("date_issued", "") or r.get("issue_date", "") or "")[:10]
            r["final_date"] = _final(r)
            r["cancel_date"] = _cancel(r)
            r["parcel_class"] = ""
            r["industrial_zoning"] = "Y" if r.get("flag") == "Y" else "N"
            r["zone_district"] = r.get("zoning_district", "") or ""
            r["neighborhood"] = ""
            out.append(_blank(["status"], r))
    return out


def load_plans(s4, files):
    out = []
    for f in files:
        with open(os.path.join(s4, f), newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                r = dict(r)
                ind = r.get("industrial_use", "") == "Y" and r.get("residential", "") != "Y"
                rt = r.get("record_type", "") + " " + r.get("description", "")[:80]
                r["industrial_zoning"] = "Y" if ind else "N"
                r["_heavy"] = bool(ind and PLAN_HEAVY.search(rt) and not PLAN_SKIP.search(r.get("record_type", "") + " " + r.get("description", "")[:120]))
                r["zone_district"] = r.get("zoning_district", "") or r.get("exist_zone", "") or ""
                r["status"] = r.get("status", "") or ""
                out.append(r)
    return out
