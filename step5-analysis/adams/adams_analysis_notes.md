# Step 4 (analysis), Adams County: notes

Run 2026-10-31 with the v3 scripts (`step5-analysis/v3/scripts/build_v3.py --county adams`), one pass from the Step 4 statewide files and the Step 3 county pulls, tier A and tier B rows scored together under the fixed points table. Nothing was re-scraped, no flag was changed, and the points table was not touched. This is the second build of the day: the first (statewide sources only, 228 rows, kept in `pre_loader/`) was reviewed and reported; Matthew then approved the county-layer loader (decision 1A), dropped PrimeGov (2C) and the three person-named LLCs (3), and this build followed.

Files in this folder: `adams_ranked_accounts.csv` (1,086 rows), `adams_evidence.csv` (6,360 source rows behind them), `adams_manual_lookup_list.csv` (25 addresses or names for a hand lookup), `adams_frs_names.csv` (19 unattached addresses with an EPA facility registry name), `v3_report.json` (every count in this note), the raw build outputs (`adams_*_v3.csv`, `rank_changes_v3.csv`), the web-check inputs and results (`webcheck_*`), the review findings of the first build (`review_findings.md`) and of this one (`review_findings_2.md`), and the build logs. The county config is `v3/scripts/county_configs/adams.py`; the county-layer loader is `v3/scripts/v3_local.py`.

## Assumptions (read first)

1. **Sources.** The six statewide sources (UCC filings, business registrations, OEDIT approvals, state water permits, APCD air permits, Mile High CRE) scoped to Adams County, plus seven of the nine Step 3 county pulls read as the county's permit layer (Adams County, Thornton and Aurora building permits: 13,131 rows) and planning layer (Adams County planning cases, Thornton development projects, Aurora development applications, Commerce City active development: 3,653 rows). Not read: the property sales file (no slot in the method; its 296 flagged deeds stay in `step4-scrape/adams/`) and Brighton Legistar (meeting items; no slot). PrimeGov was dropped by decision after its robots.txt blocked the pull.
2. **The loader (`v3_local.py`) maps the county rows onto the fields the Denver code expects; the points table is unchanged.** Tier A rows from Step 3 score as Denver tier A permits (new building 22, alteration 18, +3 at $1M); B3a 12; B3b 6. Permit types that are fences, signs, alarms, fire sprinklers, hoods, plan revisions, temporary uses, meters or demolition are held at B3b whatever Step 3 said, because the table scores them as small permits. The class (New Building, Addition, Alteration/Tenant Finish) comes from the permit type and type-of-work words. Valuation is carried where the layer has it (Thornton, Aurora) and blank for the Adams County layer, whose tier A rows therefore score as construction permits without the $1M bonus. A permit with no final date is not finaled (fit-out stage), as in Denver; Thornton's closed and expired statuses are mapped to final and cancel dates, the other two layers carry neither. Every flagged permit row is treated as sitting on industrial property (every Step 3 rule requires industrial property, zoning or an industrial word), so Denver's tier A parcel test passes; no assessor parcel class exists on these layers, so address rows get no parcel-class fit. Planning rows with `industrial_use` = Y on a site, development or planning case score as heavy-industrial site plans (12); other industrial rows as industrial mixed-use (6); the rest (2,776 rows, housing and liquor dominate) are support only.
3. **Adams scope, in this order:** county field in a water permit; AIRS prefix 001 in an air permit; the county layers (all rows are Adams County by construction; Aurora's rows were cut to the Adams side in Step 3); for UCC and registration rows, the zip (99 percent or more of the ZCTA inside Adams County, from `adams_zip_share.json`, built 2026-10-30 from the Census 2020 ZCTA-to-county file with the same formula as Denver's); then the Census geocoder for a split zip. 163 addresses went through the geocoder: 50 Adams, 62 Denver, 9 Arapahoe, 9 Broomfield, 9 Weld, 5 Jefferson, 1 Boulder, 1 Morgan, 17 no match. The Denver placements are the mailing-address trap in reverse: Denver-mailing zips 80216, 80221 and 80229 reach into unincorporated Adams, so each street address was placed individually.
4. **Mailing cities.** Adams County has no city of its own name, so the v3 mailing-city tests use two sets in the county config: `MAIL_CITIES` (Commerce City, Brighton, Thornton, Northglenn, Federal Heights, Bennett, Lochbuie, Henderson, Strasburg, Watkins, Dupont, Eastlake, and the "unincorporated Adams" spellings), which behave as "Denver" does in the Denver build, and `SPLIT_CITIES` (Aurora, Arvada, Westminster, Denver, Broomfield), whose rows are placed by zip share and geocoder only. This needed a small extension to `v3_config.py`, `v3_signals.py` and `v3_resolve.py` (defaults keep the old behaviour).
5. **Script changes and the Denver check.** Three edits were made to the shared scripts for this county: the mailing-city sets (assumption 4), the county-layer loader hooks (`LOCAL_PERMIT_FILES`, `LOCAL_PLAN_FILES`, labels, the `_heavy` flag, county names in the permit texts), and a `PERSON_NAMED` drop list. Every default reproduces the Denver behaviour: after each edit `--county denver` was rebuilt into a scratch folder and compared byte for byte with the committed Denver outputs (ranked file, evidence file, rank changes and report), identical each time, last on 2026-10-31. `verify_v3.py` now groups county permit and planning files as one layer each for the source bonus, which is how the build counts them.
6. **Mailing-address trap.** 13 rows sit in the "county unconfirmed" section (`county_basis` starts "Adams mailing address, county unconfirmed"): an Adams mailing city with no street address, or one the geocoder could not place or placed elsewhere. They are listed, not dropped, and not guessed.
7. **Run date for recency is the scripts' fixed 2026-10-11** (`v3_lib.RUN`), 20 days before this run. Left as the method has it so the counties compare; the effect is at most a handful of rows near the 12- and 24-month edges.
8. **Local noise cuts.** The Denver DIA cut is replaced by an Adams airport cut (Colorado Air and Space Port, Front Range, airline and aircraft words, SIC 4512, 4513, 4581). It removed 0 flagged water rows. No other county cut was added; the method's own cuts did the work. The county permit cuts removed 36 cancelled permits and 14 rows with no usable street address; the planning cut set 2,776 non-industrial rows to support and dropped 169 with no address.
9. **Web checks.** The 50 named companies in the first ranked list's top 50 (built before the Kairus tie and the checks themselves) were searched on 2026-10-30, two searches each, for what they make and whether the site is in Adams County. 31 returned a usable page and set the fit line (17 strong, 6 moderate, 8 weak); 19 could not be confirmed and keep the fit the records give them. No site was shown to be outside the county, so nothing was dropped. In this build the top 50 holds 19 named companies without a usable web page (`top50_named_without_web_check` in `v3_report.json`); the address rows that the county layers added were not searched. Two to watch: Claremont Foods (its production site is unconfirmed; press placed an earlier plant in Boulder County) and Kelley Trucking (HQ in Jefferson County; the Adams record is a gravel pit).
10. **Step 2 ties and occupiers.** Kairus Inc at 25315 E 48th Ave is the Philip Morris (PMI U.S.) ZYN plant: the Step 2 back-test found Kairus as grantee of the 148-acre parcel, as the company on the Adams County incentive agreement of 2024-07-09, and as the operator on the state water permit (SIC 2131, chewing and smoking tobacco), with Aurora's permits at the address filed as "Project Waterfall". Recorded in `KNOWN_TIES`; the row is displayed under the PMI name with Kairus kept as the entity. Three address rows carry an occupier named in Step 2 permit descriptions (`STEP3_OCCUPIERS`): RK Industries at 3301 N Lewiston St (Aurora permits filed under that name, including the 2026 crane foundation), Kiosk Information Systems at 251 E 126th Ave and Izzio Artisan Bakery at 15107 Grant St (Thornton permits name the tenant). The row stays an address row; only its label and fit come from Step 2.
11. **Person-named entities.** Three registered entities named after private individuals (one UCC debtor, two possible occupiers from registrations) are left out of every listing by Matthew's decision (`PERSON_NAMED` in the county config; 1 UCC row and 2 registration rows cut).
12. **EPA facility registry names.** Of the 255 unattached addresses scoring 40 or more, 19 match a facility in `frs_filtered.csv` (Adams County, same house number and street); the registry name is added to `next_step` and listed in `adams_frs_names.csv`. A registry record can be a former occupant (Milgard at 17450 E 32nd Pl, now an RK Mission Critical site), so it is a lead, not a confirmation. One registry record carrying a person's name was left out. Parcel owner names were not used.
13. **Ground truth.** The 17 Adams projects from the Step 3 overlay plus the four "Adams or a neighbour" overflow projects are in `GROUND_TRUTH`, with the addresses Step 2 confirmed (Kiosk's 251 E 126th Ave was added). They are used only to report hits after ranking. Nothing was tuned to them.
14. **Everything else is the Denver v3 method unchanged:** join classes, which side holds an address, agent-suite rule, name merges, repeat months, source bonus, stage, fit order, home-address rule (81 rows show "withheld"), evidence file layout (county rows keep their own source name in the `source` column), and the people rules. See `step5-analysis/v3/analysis_notes_v3.md` assumptions 7 to 26.
15. **No Atlas Copco data. No contact with any agency, vendor or company. No records requests. No browser-only portal opened.** Web use: the Census geocoder and the 50 company searches of 2026-10-30. The Step 2 ground-truth corrections are not applied beyond the addresses noted.

## Points table (fixed, not retuned; identical to Denver)

Possible matches score half. Within one source only the best signal counts, plus 3 points for each further month with a signal of 12 or more in that source (maximum 9).

| Signal | Points |
|---|---|
| UCC filing naming an air compressor or compressed-air system (tier A) | 30 |
| UCC filing with a tier B process-equipment word (B1a) | 30 |
| UCC filing naming production machinery (tier A) | 25 |
| Air permit application, modification or approval for process units | 25 |
| County permit (Adams County, Thornton or Aurora layer), new building or addition, industrial property, $250k or more (+3 if $1M or more)  | 22 |
| Construction stormwater permit with a manufacturing SIC or company-named facility | 20 |
| County permit (Adams County, Thornton or Aurora layer), alteration or tenant finish, industrial property, $250k or more (+3 if $1M or more)  | 18 |
| County permit (Adams County, Thornton or Aurora layer), $50k to $250k, industrial property (B3a)  | 12 |
| Air permit APEN-only or exempt; new industrial stormwater or no-exposure certification; concept or site plan on heavy industrial zoning | 12 |
| UCC flagged word without production machinery; towable compressor; press story naming the company | 8 |
| Vague lien held by an equipment lender (B1b); blanket lien on a maker (B1c) | 8 |
| Flagged tier A registration; site plan on industrial mixed-use zoning; permit under $50k on industrial property (B3b); unflagged permit at the company's address | 6 |
| Press story naming only the address; OEDIT code-name approval | 5 |
| Generic or blanket UCC lien; other site plan at the address | 4 |
| Tier B registration (B2a); unflagged registration | 3 |
| Air or water row cut as noise | 2 |

Independent sources: +8 for each source beyond the first with a signal of 5 or more (maximum 24); +3 for each support-only source (maximum 6). Recency: +15 within 12 months, +8 within 24. Stage: buying equipment +12; fit-out +12; under construction +8; operating and expanding +8; planned +4. Fit: strong +15; moderate +6; weak -15. `verify_v3.py` recomputes every score from the evidence file: 0 problems.

## Method

1. Scope records to Adams County (assumptions 3 to 6).
2. Cut known noise; counts below.
3. Resolve records to companies by normalised name and address, keeping raw values and name variants.
4. Attach address-only records (county permits, planning cases, press addresses) to companies by address; a contractor is not the account. Where no company attaches, the address is its own candidate (833 rows).
5. Pull every row for a candidate from every source, flagged or not (698 support rows beyond the five-per-source listing cap are not listed).
6. Score tier A and B signals together under the table; rank.
7. Name unattached addresses scoring 40 or more by the EPA facility registry (assumption 12: 19 of 255). Parcel owner names were not used.
8. Run `verify_v3.py` (0 problems) and the independent review (below).

## Noise cuts and counts

Rows removed at each step, in the order applied.

| Source | Step | Rows |
|---|---|---|
| Colorado UCC filings, tier A | flagged rows statewide | 901 |
| Colorado UCC filings, tier A | outside Adams scope (state, zip, mailing city, geocoder) | 820 |
| Colorado UCC filings, tier A | entity named after a private individual (left out by decision) | 1 |
| Colorado UCC filings, tier A | rows kept as signals | 60 |
| Colorado UCC filings, tier A | debtor name has no business word (may be an individual) | 3 |
| Colorado UCC filings, tier A | paving and road-milling equipment ('pneumatic' rollers, Wirtgen milling machines) | 9 |
| Colorado UCC filings, tier A | kept at the weak tier (8 points): restaurant, commissary-kitchen or survey equipment | 1 |
| Colorado UCC filings, tier A | forklifts and other lift or earthmoving equipment (Doosan, 'pneumatic' tyre) | 8 |
| Colorado UCC filings, tier A | kept at the weak tier (8 points): towable construction compressor | 6 |
| Colorado UCC filings, tier A | kept at the weak tier (8 points): flagged word without production machinery | 1 |
| Colorado UCC filings, tier B | flagged rows statewide | 374 |
| Colorado UCC filings, tier B | outside Adams scope (state, zip, mailing city, geocoder) | 355 |
| Colorado UCC filings, tier B | rows kept as signals | 19 |
| Colorado business registrations, tier A | flagged rows statewide | 2211 |
| Colorado business registrations, tier A | no Colorado address (foreign entity showing an out-of-state head office); kept for name matching only | 1707 |
| Colorado business registrations, tier A | Colorado address outside Adams scope | 491 |
| Colorado business registrations, tier A | entity since withdrawn, dissolved, converted or merged | 1 |
| Colorado business registrations, tier A | rows kept as signals | 12 |
| Colorado business registrations, tier B | flagged rows statewide | 815 |
| Colorado business registrations, tier B | Colorado address outside Adams scope | 669 |
| Colorado business registrations, tier B | rows kept as signals | 55 |
| Colorado business registrations, tier B | no Colorado address (foreign entity showing an out-of-state head office); kept for name matching only | 90 |
| Colorado business registrations, tier B | registered-agent or virtual-office address (10 or more 2024-26 registrations at the same address and suite) | 1 |
| Adams County, Thornton and Aurora building permits, tier A | flagged rows | 1001 |
| Adams County, Thornton and Aurora building permits, tier A | zero-valuation permits in the full layer (never flagged in tier A; listed for the record) | 74 |
| Adams County, Thornton and Aurora building permits, tier A | flagged rows in the DIA neighborhood (all) | 0 |
| Adams County, Thornton and Aurora building permits, tier A | rows kept as signals | 999 |
| Adams County, Thornton and Aurora building permits, tier A | ADDED in v3: permit cancelled, with no change-of-contractor record carrying the work on | 2 |
| Adams County, Thornton and Aurora building permits, tier A | of the kept rows, received in the last 90 days (kept at full weight; the layer undercounts this window) | 78 |
| Adams County, Thornton and Aurora building permits, tier B | flagged rows | 3098 |
| Adams County, Thornton and Aurora building permits, tier B | rows kept as signals (B3b, under $50k) | 2512 |
| Adams County, Thornton and Aurora building permits, tier B | no usable street address | 14 |
| Adams County, Thornton and Aurora building permits, tier B | rows kept as signals (B3a, $50k to $250k) | 538 |
| Adams County, Thornton and Aurora building permits, tier B | permit cancelled | 34 |
| Adams County, Thornton, Aurora and Commerce City planning cases | flagged rows (every row is flagged) | 3653 |
| Adams County, Thornton, Aurora and Commerce City planning cases | rows kept as signals | 708 |
| Adams County, Thornton, Aurora and Commerce City planning cases | not industrially zoned (housing and mixed use dominate); kept as supporting evidence by address | 2776 |
| Adams County, Thornton, Aurora and Commerce City planning cases | no usable street address | 169 |
| State water permits (WQCD) | flagged rows statewide | 1867 |
| State water permits (WQCD) | flagged rows with county Adams | 263 |
| State water permits (WQCD) | flagged rows with a Adams mailing city but another county in the source (left out: the source states the county) | 28 |
| State water permits (WQCD) | flagged on acreage alone (no manufacturing SIC, no company-named facility): schools, parks, housing, roads, pipelines | 98 |
| State water permits (WQCD) | transit, public works, retail and contractor-coded sites with no manufacturing SIC | 27 |
| State water permits (WQCD) | rows kept as signals | 36 |
| State water permits (WQCD) | industrial stormwater general-permit renewal wave, May to July 2024 (existing plants re-applying; kept as identity and SIC evidence) | 80 |
| State water permits (WQCD) | wastewater plants, hauling and detention or water-quality facilities | 2 |
| State water permits (WQCD) | renewals (received more than a year after issue) | 20 |
| APCD air permit status | flagged rows statewide (not oil and gas) | 1064 |
| APCD air permit status | rows whose county column says Adams but AIRS prefix is not 001 (left out; office address in place of the site) | 9 |
| APCD air permit status | flagged rows with AIRS prefix 001 (Adams) | 110 |
| APCD air permit status | rows kept as signals | 60 |
| APCD air permit status | no street address for the site | 3 |
| APCD air permit status | fuel stations and bulk fuel | 27 |
| APCD air permit status | emergency generators and fire pumps only (data centres, telecom, hotels, city buildings) | 16 |
| APCD air permit status | hospitals, crematories, prisons, utilities, airport and city facilities, data centres, land development | 4 |
| Mile High CRE | flagged rows statewide (industrial category) | 160 |
| Mile High CRE | flagged rows with city in Adams County or a split city | 91 |
| Mile High CRE | rows kept as address signals | 24 |
| Mile High CRE | no single street address (market reports, portfolio sales, round-ups) | 45 |
| Mile High CRE | split-city mailing address that the Census geocoder places outside Adams County | 22 |
| OEDIT EDC approvals | flagged rows (every row is flagged) | 139 |
| OEDIT EDC approvals | no Adams County or Metro Adams reference | 92 |
| OEDIT EDC approvals | rows kept as code-name candidates | 8 |
| OEDIT EDC approvals | rows from minutes (mostly non-industrial) | 39 |

## Result

1,086 ranked rows: 1,065 in the Adams section (232 companies and 833 unattached addresses), 13 county unconfirmed, 8 OEDIT code names. 228 of the 1,065 score 50 or more. By number of sources: 712 rows rest on one source, 259 on two, 72 on three, 22 on four. Fit: 162 strong, 11 moderate, 851 unknown (almost all address rows, which have no parcel class to read a fit from), 41 weak. Stage: 491 fit-out, 164 planned, 160 operating and expanding, 155 under construction, 17 buying equipment, 78 unknown. Tier: 452 tier A only, 459 tier B only, 175 both; in the top 100, 97 carry tier A.

Top 10 with one line of evidence each:

1. Philip Morris International, PMI U.S. ZYN plant (Kairus Inc), 25315 E 48th Ave, Aurora. Aurora permits for a $206M new building received 2026-10-14 and the 2024 core and shell, an air permit application 2025-11-06 for the process plant, water permit SIC 2131, UCC; five sources.
2. Forge Nano, 12300 Grant St #110, Thornton. Air permit stack 2024-08-06, water permit SIC 3569, Thornton permits; builds coating equipment on site.
3. Pretred, 6550 N Denali St, Aurora. Air permit 2025-10-21 for the tire recycling plant, a $4.5M Aurora tenant finish, water permit, press; ground truth C24.
4. RK Industries, 3301 N Lewiston St, Aurora (occupier from Step 2). $3M Aurora tenant finish 2026-06-16 plus the crane foundation and other permits; ground truth C25.
5. Ardent Mills, 4545 E 64th Ave, Commerce City. Facility-wide air permit 2025-02-11, construction stormwater permit, county permit for the rail unload building; expansion completing end of 2026.
6. Copeland Precast East, 35582 E 56th Ave, Watkins. Construction stormwater permit 2024-04-27 (SIC 3272) and the county permit for a new 33,110 sq ft precast plant.
7. TruStile Doors, 1111 E 71st St (Denver mailing, Adams site). UCC, air and water permits, county permits; MDF door factory.
8. Vartega, 5675 Pecos St. Air permit and the county permit for a 30,000 sq ft expansion; ground truth D17.
9. D-A Packaging, 9155 Boston St, Henderson. Three air permit rows 2025-03-25, industrial stormwater permit, UCC, county permit; five sources.
10. Unattached address, 16000 E 32nd Ave, Aurora. $31.3M new building received 2026-08-12 on industrial zoning; tenant not named in any source (manual lookup list).

How many are solid: of the top 25 in the Adams section, 18 carry a strong fit and 7 are unattached addresses with an unknown fit (new buildings and large tenant finishes on industrial zoning whose tenant no source names); 1 shows a withheld address. Read by eye, 18 of the 25 look like real plants or production shops; the other 7 are the unnamed sites, which are worth a hand lookup before a call. Across the whole list, 66 rows combine two or more sources with a strong fit; that is the set worth a call. The 833 address rows are where the county layers put the new buildings and fit-outs: 255 of them score 40 or more, and most need a tenant lookup.

Sensitivity of the top 25 (from `v3_report.json`): doubling or removing recency changes 3 rows; doubling or removing the source bonus changes 4 and 8; halving or doubling tier B points changes 4 and 6. The top 10 is the same set only under tier B halved; the county layers put several address rows and named plants within a few points of each other, so the order near rank 10 is not firm.

## The check against known projects

The county has 17 known projects (plus four whose county is Adams or a neighbour). 11 of the 17 appear in the ranking: 7 by name and address, 3 as an address row carrying a Step 2 occupier name, 1 by address only.

| Project | Rank | How | Why that rank |
|---|---|---|---|
| C22 Philip Morris ZYN | 1 | name and address (Kairus tie) | permits, air, water, UCC, press |
| C24 Pretred | 3 | name and address | air permit, tenant finish, water, press |
| C25 RK Industries | 4 (and 47) | occupier name and address | $3M tenant finish, crane foundation and other Aurora permits |
| D17 Vartega | 8 (and 685) | name and address | air permit, 30k sq ft expansion permit |
| X16 Kiosk Information Systems | 21 | occupier name and address | Thornton new-building permits at 251 E 126th Ave |
| C23 Solid Power | 25 | name | SP2 water permit (renewal, cut as a signal but kept as identity) plus Thornton permits at 14902 Grant St |
| X15 Izzio Bakery | 34 | occupier name and address | Thornton permits at 15107 Grant St |
| D16 Metro Water Recovery | 67 | name and address | water, air, county permits; weak fit (public utility) |
| C18 CEMCO | 218 | name and address | water permit at 9410 Heinz Way; no permit yet in the county layers for the new plant |
| X08 Boise Cascade door shop | 222 | name and address | water permit at 11011 E 104th Ave |
| X05 Santa Monica Seafood | 268 | address only | one press row and a Thornton permit |

The six misses: C19 Prost Brewing (Northglenn has no machine-readable layer; its UCC filings carry a Loveland and a Denver 80211 debtor address, none flagged); C20 Amprius and C21 VSK Energy (cancelled; Amprius' registration is withdrawn, which the method cuts, and the Brighton layers are not in the loader); D05 Craft Beverage Warehouse (the county permit at 5925 Washington St is under the variant name "Craft Labeling" and the ground truth has no address for it); X04 Wanderment (no permit at 800 E 64th Ave in any file); X11 AMP (no address and no press date). The four "Adams or a neighbour" projects: none appears; Step 2 settled three of them outside Adams and Creation Technologies has no row in any file.

Against the first build (statewide sources only, 8 of 17), the county layers added Kiosk, Izzio and Solid Power, lifted RK Industries from an address-only row at rank 187 to rank 4 and Vartega from 84 to 8, and moved CEMCO and Boise Cascade down (their one water permit each is now outranked by hundreds of permit-backed sites).

## What the county layers added

6,360 evidence rows against 525 in the first build; 833 address rows against 11; 255 unattached addresses scoring 40 or more against 0. Thornton's permit descriptions supplied the tenant for three known projects that no statewide source carried. The cost is the unknown-fit mass: 851 rows have no fit because the county layers carry no assessor class, and 19 registry names and the 25-row manual lookup list are the only tenant evidence for the unnamed sites. The property sales (296 flagged deeds, CEMCO and RK among them) and Brighton Legistar (74 flagged items, Amprius among them) are pulled but have no slot in the method; a deed-to-address join would be the next loader step.

## What the data could not show

- Which tenant is behind most county permits: three of the four permit layers carry no applicant; Thornton's description is the exception. The manual lookup list has the 25 addresses where a hand lookup in Accela, eTRAKiT, CityView or AMANDA would settle it.
- A fit for address rows: no parcel class on the county layers, so 851 rows show "unknown".
- Anything before the first press story for a brand-new plant: the sources fire between announcement and opening and for expansions at existing plants.
- Small tenants (Wanderment, Craft Beverage) and companies whose filings carry an HQ address elsewhere (Prost).
- The OEDIT code names (8 rows, 1079 to 1086): Project Split is RK Industries by the state's own release (ground truth C25), the rest are undecoded and stay "possible" at most.
- PrimeGov agenda items, dropped: the county's incentive record (Kairus, Prost, PFG, Ardent Mills, NTT agreements in Step 2) is no longer read.

## Review

The first build (statewide sources only) was audited by an independent review agent (`review_findings.md`): every evidence row traced to raw records, every score re-added, no blocking defect; six count errors in that build's notes were fixed. This build was audited the same way (`review_findings_2.md`); what it found and what was fixed is recorded there and summarised at the end of this note.
