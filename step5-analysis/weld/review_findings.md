# Weld County analysis: independent review findings

Reviewed 2026-11-06 against `.claude/skills/colorado-county-runner/SKILL.md` (Step 4, Check the result, Ground rules), the `v3_local.py` loader docstring, `county_configs/weld.py`, the raw Step 4 files and the ground-truth extract. All checks were run with Python on the full files; samples are stated where a sample was used.

**Verdict: fail** (one blocker: a known project is misplaced and the miss is explained wrongly; the rest is should-fix or notes). The scoring arithmetic, scope lookups, web-check application, personal-data scan and em-dash scan all pass.

## Findings

### 1. Blocker. Hirsh Precision (ground truth C35) sits in the county-unconfirmed tail although the Weld permit layer places it, and the notes explain the miss wrongly

- Rank 326, `Hirsh Precision Products, Inc.`, score 73.0, `county_basis = Weld mailing address, county unconfirmed (Census geocoder could not place it)`. Its evidence is three tier A UCC machinery filings at 4300 Godding Hollow Pkwy, Frederick: 20242018080 (2024-02-27, 25 points), 20252111475 (2025-10-21, Okuma Multus lathe, 25), 20262024967 (2026-03-16, Okuma Multus lathe, 25), plus seven support rows. A score of 73.0 ties ranks 4 and 5 of the main section.
- Rank 159, `Unattached address (possible occupier: HIRSH PRECISION PRODUCTS, INC.)`, 4300 GODDING HOLLOW PKWY, `county_basis = Weld permit layer (Weld only)`. Its three Frederick permit rows (BLDG23-0114, 26TMP-000631, BLDG26-0419) carry `company_name = HIRSH PRECISION PRODUCTS INC`, `company_role = occupant`, same street address.
- That is an exact name plus exact address on a county document, which the Ground rules define as a confirmed join. The build kept the two as separate rows, left the company in the unconfirmed section because the Census geocoder returned "no match" for the address (cache: `4300 Godding Hollow Pkwy, Frederick, CO 80504 -> no match`), and did not use the permit layer as the county basis for the company, although the Mile High CRE path does exactly that (`address is in the Weld permit or site plan layer`).
- `weld_analysis_notes.md` says rank 326 is "a 2025 registration row" and that "the plant opened in October 2023, before the window, so only trailing records remain". Both statements are wrong: the row is built on UCC rows, and the 2024 to 2026 machinery liens are tier A signals inside the window. The ground-truth check therefore reports a hit at rank 326 that the data supports at about rank 4.

### 2. Should fix. Loader gives tier A (construction points) to commercial-use and non-building permits on the Frederick layer

Every Frederick permit row in `run3_webchecks/weld_evidence_v3.csv` was checked (236 rows: 27 tier A, 185 tier B, 24 unflagged). The holds work for signs (45 rows, none above 6 points), electrical (31), mechanical (16), plumbing (2), roofing (11), solar (5), demolition (2), plug and abandon (5), temporary structures (6), racking (BLDG23-2722, BLDG24-1085, 26TMP-000910 held), a trailer (BLDG26-0274 held) and fuel tanks (BLDG24-0463 held). These tier A rows violate the rule:

| record_id | record_type | description (first 100 chars) | tier | points | rank |
|---|---|---|---|---|---|
| BLDG24-0462 | Commercial New Construction Permit | 10,630 sf core and shell commercial retail building including structural, mechanical, plumbing, & el | A | 22 | 125 |
| BLDG24-0039 | Commercial New Construction Permit | 9,234 sf core and shell commercial retail building including structural, mechanical, plumbing, & ele | A | 22 | 163 |
| BLDG26-0559 | Commercial Alteration Permit | xterior / interior tenant improvement, T.I., of an existing mixed-use core and shell building for me(rcantile use) | A | 18 | 97 |
| BLDG24-1007 | Commercial Addition Permit | Dream Weaver 21H-N268 - Install additional facilities at existing oil and gas location. | A | 22 | 126 |

Borderline, listed for a decision: BLDG25-0121 (office and lab tenant finish for Halleck & Willard, an engineering firm, zoning C-C, A 18, rank 114); BLDG25-0393 (tenant remodel with offices, reception and a lab, zoning DT, A 18, rank 140); BLDG24-0927 (1,216 sq ft printer room tenant finish, A 18, rank 108).

Cause: `COMMERCIAL_USE` in `v3_local.py` is tested against the permit type fields only, and the Frederick layer carries the use (retail, mercantile, dental) in the description. Assumption 3 of the notes says commercial-use buildings are held at B3a; for these rows they were not. The 23 other tier A rows are construction permits with an industrial word (Agilent manufacturing building and tank farm, Meadowlark Optics expansion, PEMB warehouses, core-and-shell fit-outs at industrial zoning).

### 3. Should fix. The Frederick layer names the occupant on 129 permit rows and the build does not read it

`v3_resolve.py` names an address from county permit rows only when `company_role` is `tenant`, `applicant` or `project`. The Frederick scraper writes `occupant` (129 rows) and `tenant` (87 rows). Result: 35 ranked address rows whose own permit rows name the occupant are shown as `no company attached` or named from a weaker source. Examples: rank 124 (5964 IRIS PKWY, permit BLDG24-0554 names MEADOWLARK OPTICS on an 8,877 GSF manufacturing expansion), 254 (7700 MILLER DR, FRONT RANGE TOOLING & MOLDING, INC.), 214 (4109 BRUIN BLVD, CO PAVEMENT SOLUTIONS), 299 (5681 IRIS PKWY, SMITH POWER PRODUCTS), 187 (7990 E I-25 FRONTAGE RD, METAL SALES), 200 and 252 (QUANTUM CANNING), 261 (TORO ROBOTICS/OWL OFFROAD), 159 (HIRSH PRECISION PRODUCTS INC, see finding 1). The notes' "15 addresses named from county permit rows" counts the `tenant` rows only. Either the scrape step should write `tenant` or the resolver's role list should include `occupant`; both are a one-line change but a method decision.

### 4. Should fix. Side-list match labels call address-only joins "confirmed"

`weld_side_list_matches.csv`: 45 rows. 30 carry `confirmed: exact address (occupier may differ)`. The Ground rules reserve "confirmed" for an exact name plus address or a document tying them; an address-only match is "possible". Ten checked by hand: ranks 1, 326 (exact name, correct), 14 (Microvast and The Bar S U sales at 31815 Great Western Dr against Schlosser Signs, address only), 68 and 92 (450 N Front St against Texas Farm Products and J.D. Heiskell, address only), 137 (Backbone Properties against Backbone Fiber Systems, address only), 67 (Alter Trading, address only and one lead-word row), 241 (two sales against an unattached address), 325 (exact name, correct), 332: `FLIGHT 405 LLC, 3000 AIRPORT DR UNIT 405` against `Flight Fabrication & Iron LLC, 3000 Airport Drive, Unit 203`, labelled exact address although the units differ. The lead-word rows (Black Knight 24 LLC against three "Black ..." companies at ranks 26, 33, 52; Pathfinder Properties against Pathfinder Pressure Testing, rank 93) carry no evidence of a tie and could be dropped.

### 5. Should fix. 5507 Distilling (rank 8) stays in the main section at strong fit after the web check placed its equipment in Larimer County

The config's `WEB_DROPS` entry and `web_checks_weld.md` (line 26, fit `unknown`, and line 77) record that the UCC collateral text puts the distillation equipment on Fifth Street, Loveland. The ranked row still reads `county_basis = zip 80634 is in Weld County`, `compressed_air_fit = strong`, `match_confidence = confirmed`, with the finding only in `next_step`. The method's mailing-address rule puts such a row in the unconfirmed section. The notes (assumption 6) say the scripts were left unchanged on purpose; the row is still mislabelled for a reader of the CSV.

### 6. Should fix. Split-city rows kept as "Weld mailing address, county unconfirmed"

- Mile High CRE address rows at ranks 346 (6425 Byrd Drive, Loveland), 349 (3841 Vander Meer Drive, Loveland) and 348 (1171 West Dillon Rd, Boulder; the former Lowe's in Louisville) are Larimer and Boulder County sites. The geocoder had no match and `v3_signals.py` keeps a no-match press row as unconfirmed whatever the city. The config says split-city rows are placed by zip share and geocoder only. Rank 345 (6196 East Bridge Street, Brighton) is kept the same way; that one may well be in Weld but has no basis.
- Ranks 328 to 344 include 13 UCC and registration rows with city Longmont, Johnstown or Windsor labelled "Weld mailing address". They are kept because the zip share is 0.5 or more (code design, consistent with other counties), but the label names a Weld mailing address the row does not have. Reword the basis for split cities.

### 7. Note. Eclipse Engineering (rank 21)

`county_basis` says the Census geocoder places 2540 S Main St, Erie in Weld County, and the cache confirms it. The fit text and notes assumption 7 say the county was not confirmed. The geocoder result is the stronger statement; the two should agree.

### 8. Note. Stage label "permit under $50k" on a layer with no valuation

59 rows read `fit-out (permit under $50k)` and 19 `operating and expanding (permit under $50k)`. The Frederick layer carries no valuation; the label comes from the B3b hold. Say "small permit (held at B3b)" or similar.

### 9. Note. Agilent's own permits attached as "possible" at half points

Rank 1 shows permit rows at 11 and 9 points (22 and 18 halved) with `match_class = possible`, although the permit rows carry `company_name = Agilent`, the parcel owner is Agilent and the descriptions name Agilent. A document tie exists. Rank 1 does not move.

### 10. Note. The other misses, checked in the raw files

- C34 Colorado Premium: no scoreable record. The state water row COPB90825 has no address or county. UCC rows 20242004182 and 20242005959 (2024-01, FOMACO injector and brine mixer at 2035 2nd Ave, Greeley) are production machinery but were not flagged in Step 4; a flag-word gap upstream, not an analysis defect. The 2023-07 incentive agreement is in the side list.
- C36 Sphere Renewables: the Fort Lupton case SPR26-002 names the company but has no address and was dropped with the other 66 address-less planning rows; UCC rows at 13516 County Road 8 (20252077678, 20262068284) are unflagged. The build could have attached the case by name to those rows; the notes say so.
- X27 Microvast: nothing after 2024 in any scoreable source. Correct as reported.
- X26 (rank 1) and X28 (ranks 68 and 92) are marked correctly.

### 11. Note. Manual lookup list

24 rows. Rank 14 (Schlosser Signs) is listed for "what the company makes" although the web check settled it; rank 21 is listed with a withheld address, which a hand lookup cannot use.

## What was checked and passed

- Loader tiers: all 236 Frederick rows reviewed; the holds listed in the docstring fire for signs, trade permits, roofing, solar, demolition, plug and abandon, temporary structures, racking, trailers and fuel tanks (none above 6 points). Sign permits stack only through the repeat rule (best row plus 3 per extra month, max 9).
- Scope: every ranked row, not a sample. 55 geocoder-basis rows re-queried against the cache with the raw address: 55 Weld. 74 zip-basis rows: zip share 1.0 and the zip on a confirmed row. 34 water-county rows: a confirmed water row with county Weld. 43 AIRS rows: 80 confirmed APCD evidence rows carry AIRS prefix 123 (one, Ursa Major, has county field Larimer and AIRS 123; the AIRS and permit number WE agree on Weld). 119 layer-basis rows have a Weld layer row.
- Points: signal, source bonus, fit points and total recomputed from the evidence `points` for all 357 rows, 0 mismatches; `sources_count` matches on all rows; ordering by section then score has no violations.
- Web checks: 42 of 42 `WEB_CHECKS` keys landed on a ranked row with the stated level; the 17 `WEB_NOT_CONFIRMED_V3` names keep the pipeline fit.
- Ground-truth marks: X26, X28 and C35 marked where the names appear; no other row marked.
- Personal data: no emails, phone numbers or person-shaped names in `company_name`, `name_variants`, `top_evidence`, `next_step` (ranked) or `company_name`, `description` (evidence); the only two-word capitalised hits are brands (John Deere, Christian Brothers Automotive). UCC debtor addresses are withheld.
- Em dashes: none in any CSV, MD or TXT under `step5-analysis/weld/` or `run3_webchecks/`.
- Points table and shared scripts: `git diff 35c4824..HEAD -- step5-analysis/v3/scripts` touches only `county_configs/weld.py`, `geocode_cache.json`, `weld_zip_share.json` and a label-tolerance change in `report_v3.py`; `v3_lib.PTS`, `v3_config.py`, `v3_local.py`, `v3_signals.py`, `v3_resolve.py` and `build_v3.py` are unchanged. Nothing in the config is tuned to the ground truth.
