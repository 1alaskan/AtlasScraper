#!/usr/bin/env python3
"""County permit and planning layers for counties other than Denver.

Denver's two layers (scrape_denver_commercial_permits_v2.csv, scrape_denver_site_plans.csv) are read as they are. For another county
the config names its Step 3 permit files (LOCAL_PERMIT_FILES) and planning files (LOCAL_PLAN_FILES), pulled in the shared 17-column
format with the Step 3 flag rules, and this module maps each row onto the fields the Denver code expects, so the points table and the
rest of the method do not change. Added 2026-10-31 for the Adams County run (decision 1A); the Denver rebuild after the change was
compared byte for byte with the committed Denver output.

Mapping, permits:
  flag_tier       A for a Step 3 tier A rule; B for B3a and B3b; blank otherwise. Low-value permit types (fences, signs, alarms, fire
                  sprinklers, hoods, plan revisions, temporary uses, meters, demolition) are held at B3b whatever the Step 3 rule said,
                  because the Denver table scores them as small permits (6 points), not as construction.
  flag_rule_v2    starts with "B3a " or "B3b " for tier B, as the Denver tier B script wrote it; the Step 3 rule follows.
  class           New Building, Addition or Alteration/Tenant Finish, from the permit type and type of work words. Denver's other
                  classes (Foundation Only, Phased Construction, New Non-Building Structure, Special Event, Change of Contractor) are
                  not produced.
  valuation       the layer's valuation where it carries one (Thornton, Aurora); blank for the Adams County layer.
  date_issued, final_date, cancel_date   issue date, certificate-of-occupancy or finaled date, and a cancel or expiry date, where the
                  layer carries them; blank otherwise. A permit with no final date is treated as not finaled (fit-out stage), as in Denver.
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

LOW_VALUE = re.compile(r"\b(fence|sign|alarm|fire sprinkler|sprinkler|hood|plan revision|temporary|temp meter|meter|demolition|demo|roof|"
                       r"antenna|awning|canopy|pool|solar|re-?roof|siding|window|door replacement|grading|right of way)\b", re.I)
NEW_WORDS = re.compile(r"\bnew\b|core\s*&\s*shell|core and shell|new construction|shell building|use building\b", re.I)
ADD_WORDS = re.compile(r"\baddition\b|\badd\b", re.I)
PLAN_SKIP = re.compile(r"liquor|marijuana|residential|single.?family|pre-?application|presubmittal|conceptual review\b.*\bresidential|"
                       r"vacation|variance|sign|temporary", re.I)
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
        return r.get("status_date", "")[:10] or r.get("date_issued", "")[:10] or r.get("issue_date", "")[:10]
    return ""


def load_permits(s4, files):
    out = []
    for f in files:
        with open(os.path.join(s4, f), newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                r = dict(r)
                tier, rule = ("", r.get("flag_rule", ""))
                if r.get("flag") == "Y":
                    tier, rule = _tier(r.get("flag_rule", ""))
                    words = " ".join([r.get("record_type", ""), r.get("type_of_work", ""), r.get("permit_subtype", ""), r.get("permit_type", "")])
                    if tier == "A" and LOW_VALUE.search(words) and not re.search(r"warehouse|factory|manufactur|plant|core|shell|tenant", words, re.I):
                        tier, rule = "B", "B3b " + rule + " (held at B3b: low-value permit type)"
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
                r["_heavy"] = bool(ind and PLAN_HEAVY.search(rt) and not PLAN_SKIP.search(r.get("record_type", "")))
                r["zone_district"] = r.get("zoning_district", "") or r.get("exist_zone", "") or ""
                r["status"] = r.get("status", "") or ""
                out.append(r)
    return out
