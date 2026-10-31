# Step 4 (analysis), Adams County: notes

Run 2026-10-31 with the v3 scripts (`step5-analysis/v3/scripts/build_v3.py --county adams`), one pass from the Step 4 statewide files, tier A and tier B rows scored together under the fixed points table. Nothing was re-scraped, no flag was changed, and the points table was not touched.

Files in this folder: `adams_ranked_accounts.csv` (228 rows), `adams_evidence.csv` (525 source rows behind them), `adams_manual_lookup_list.csv` (25 addresses or names for a hand lookup), `v3_report.json` (every count in this note), the raw build outputs (`adams_*_v3.csv`, `rank_changes_v3.csv`), the web-check inputs and results (`webcheck_*`), and the build logs. The county config is `v3/scripts/county_configs/adams.py`.

## Assumptions (read first)

1. **The ranking uses the six statewide sources only.** UCC filings, business registrations, OEDIT approvals, state water permits, APCD air permits and Mile High CRE, scoped to Adams County. The nine county pulls from Step 3 (`step4-scrape/adams/`, 19,264 rows, 8,122 flagged) are not read by the v3 code, which loads Denver's permit and site plan layers only (`LOCAL_LAYERS = False`). A loader for them is a code change for Matthew to approve, not something improvised here; what it would add is measured below under "What the county pulls would add".
2. **Adams scope, in this order:** county field in a water permit; AIRS prefix 001 in an air permit; for UCC and registration rows, the zip (99 percent or more of the ZCTA inside Adams County, from `adams_zip_share.json`, built 2026-10-30 from the Census 2020 ZCTA-to-county file with the same formula as Denver's); then the Census geocoder for a split zip. 178 addresses went through the geocoder: 59 Adams, 62 Denver, 9 Arapahoe, 9 Broomfield, 9 Weld, 5 Jefferson, 1 Boulder, 1 Morgan, 23 no match. The Denver placements are the mailing-address trap in reverse: Denver-mailing zips 80216, 80221 and 80229 reach into unincorporated Adams, so each street address was placed individually.
3. **Mailing cities.** Adams County has no city of its own name, so the v3 mailing-city tests use two sets in the county config: `MAIL_CITIES` (Commerce City, Brighton, Thornton, Northglenn, Federal Heights, Bennett, Lochbuie, Henderson, Strasburg, Watkins, Dupont, Eastlake, and the "unincorporated Adams" spellings), which behave as "Denver" does in the Denver build, and `SPLIT_CITIES` (Aurora, Arvada, Westminster, Denver, Broomfield), whose rows are placed by zip share and geocoder only. This needed a small extension to `v3_config.py`, `v3_signals.py` and `v3_resolve.py` (defaults keep the old behaviour); the Denver rebuild after the change was compared byte for byte with the committed Denver outputs and was identical.
4. **Mailing-address trap.** 18 rows sit in the "county unconfirmed" section (`county_basis` starts "Adams mailing address, county unconfirmed"): an Adams mailing city with no street address, or one the geocoder could not place or placed elsewhere. They are listed, not dropped, and not guessed.
5. **Run date for recency is the scripts' fixed 2026-10-11** (`v3_lib.RUN`), 20 days before this run. Twelve months back is 2025-10-11, 24 months is 2024-10-11. Left as the method has it so the counties compare; the effect is at most a handful of rows near the 12- and 24-month edges.
6. **Local noise cuts.** The Denver DIA cut is replaced by an Adams airport cut (Colorado Air and Space Port, Front Range, airline and aircraft words, SIC 4512, 4513, 4581). It removed 0 flagged water rows: the one space-port row in the Adams water file was never flagged. No other county cut was added; the method's own cuts (schools, housing, roads, utilities, fuel stations, generators) did the work.
7. **Web checks.** The 50 named companies in the first ranked list's top 50 (built before the Kairus tie and the checks themselves) were searched on 2026-10-30, two searches each, for what they make and whether the site is in Adams County. 31 returned a usable page and set the fit line (17 strong, 6 moderate, 8 weak); 19 could not be confirmed and keep the fit the records give them. No site was shown to be outside the county, so nothing was dropped. The checks moved rows, so the final top 50 holds 30 named companies that were never searched (19 unconfirmed from the first pass and 11 that rose into ranks 40 to 50); `v3_report.json` lists them under `top50_named_without_web_check`. Two to watch: Claremont Foods (its production site is unconfirmed; press placed an earlier plant in Boulder County) and Kelley Trucking (HQ in Jefferson County; the Adams record is a gravel pit).
8. **One Step 2 tie.** Kairus Inc at 25315 E 48th Ave is the Philip Morris (PMI U.S.) ZYN plant: the Step 2 back-test found Kairus as grantee of the 148-acre parcel, as the company on the Adams County incentive agreement of 2024-07-09, and as the operator on the state water permit (SIC 2131, chewing and smoking tobacco), with Aurora's permits at the address filed as "Project Waterfall". Recorded in `KNOWN_TIES`; the row is displayed under the PMI name with Kairus kept as the entity.
9. **Ground truth.** The 17 Adams projects from the Step 3 overlay plus the four "Adams or a neighbour" overflow projects are in `GROUND_TRUTH`. They are used only to report hits after ranking. Nothing was tuned to them.
10. **Everything else is the Denver v3 method unchanged:** join classes, which side holds an address, agent-suite rule, name merges, repeat months, source bonus, stage, fit order, home-address rule (85 rows show "withheld"), evidence file layout, and the people rules. See `step5-analysis/v3/analysis_notes_v3.md` assumptions 7 to 26.
11. **No Atlas Copco data. No contact with any agency, vendor or company. No records requests. No browser-only portal opened.** Web use: the Census geocoder and the 50 company searches. The Step 2 ground-truth corrections are not applied.

## Points table (fixed, not retuned; identical to Denver)

Possible matches score half. Within one source only the best signal counts, plus 3 points for each further month with a signal of 12 or more in that source (maximum 9).

| Signal | Points |
|---|---|
| UCC filing naming an air compressor or compressed-air system (tier A) | 30 |
| UCC filing with a tier B process-equipment word (B1a) | 30 |
| UCC filing naming production machinery (tier A) | 25 |
| Air permit application, modification or approval for process units | 25 |
| County permit, new building or addition, industrial property, $250k or more (+3 if $1M or more) [no loader for Adams yet] | 22 |
| Construction stormwater permit with a manufacturing SIC or company-named facility | 20 |
| County permit, alteration or tenant finish, industrial property, $250k or more (+3 if $1M or more) [no loader yet] | 18 |
| County permit, $50k to $250k, industrial property (B3a) [no loader yet] | 12 |
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

1. Scope records to Adams County (assumptions 2 to 4).
2. Cut known noise; counts below.
3. Resolve records to companies by normalised name and address, keeping raw values and name variants.
4. Attach address-only records (press addresses; no county permit layers yet) to companies by address. Where no company attaches, the address is its own candidate (11 rows).
5. Pull every row for a candidate from every source, flagged or not (132 support rows, listed up to five per source per account).
6. Score tier A and B signals together under the table; rank.
7. Name unattached addresses scoring 40 or more by the EPA facility registry file: no unattached address reached 40 in this run (the highest is 24), so none was named this way. Parcel owner names were not used.
8. Run `verify_v3.py` (0 problems) and the independent review (below).

## Noise cuts and counts

Rows removed at each step, in the order applied. The Denver permit and site plan steps are omitted (0 rows for Adams).

| Source | Step | Rows |
|---|---|---|
| Colorado UCC filings, tier A | flagged rows statewide | 901 |
| Colorado UCC filings, tier A | outside Adams scope (state, zip, mailing city, geocoder) | 820 |
| Colorado UCC filings, tier A | rows kept as signals | 61 |
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

228 ranked rows: 202 in the Adams section (191 companies and 11 unattached addresses), 18 county unconfirmed, 8 OEDIT code names. 76 of the 202 score 50 or more. By number of sources: 148 rows rest on one source, 43 on two, 7 on three, 4 on four. Fit: 144 strong, 10 moderate, 29 unknown, 19 weak. Stage: 88 operating and expanding, 17 buying equipment, 12 under construction, 85 unknown. Tier: 156 tier A only, 68 tier B only, 4 both; in the top 100, 90 are tier A.

Top 10 with one line of evidence each:

1. Philip Morris International, PMI U.S. ZYN plant (Kairus Inc), 25315 E 48th Ave, Aurora. Air permit application 2025-11-06 for a process manufacturing facility at the address; water permit SIC 2131; UCC filings; the Step 2 tie.
2. Ardent Mills, 4545 E 64th Ave, Commerce City. Facility-wide air permit 2025-02-11 and a construction stormwater permit; the company describes an equipment update and capacity expansion completing end of 2026.
3. Forge Nano, 12300 Grant St #110, Thornton. Air permit and water permit (SIC 3569); builds coating equipment on site.
4. TruStile Doors, 1111 E 71st St (Denver mailing, Adams site). UCC, air and water permits; MDF door factory.
5. D-A Packaging, 9155 Boston St, Henderson. Three air permit rows 2025-03-25 (boiler, blending, methanol tank), industrial stormwater permit at the address (facility name Crystal Packaging, SIC 1311 on the row), UCC; the SIC 2992 fit line comes from the state file's other-SIC field.
6. S and W Precision Machining, Commerce City (address withheld). Repeat UCC machinery filings; CNC job shop.
7. Quikrete Denver, 2660 W 64th Ave. Facility-wide air permit 2026-07-14, water permit SIC 3299, UCC.
8. Valhalla Industries (address withheld). UCC machinery filings; nothing on the web; collateral reads as a mobile contractor, so treat with care.
9. Pretred, 6550 N Denali St, Aurora. Air permit 2025-10-21 for the tire recycling plant, water permit, press; ground-truth C24.
10. Ward Precision Manufacturing (address withheld). Repeat UCC machining-centre filings.

How many are solid: of the top 25 in the Adams section, 21 carry a strong fit, 3 moderate, 1 unknown, and 10 show a withheld address (UCC-only shops whose filing address may be a home). Read by eye, 20 of the 25 look like real plants or production shops; the other five are a wastewater plant (City of Westminster, rank 6 in the first pass, now carrying a weak fit after the web check), a mobile contractor (Valhalla), a construction contractor (Western Industrial Contractors), a tire shop and a company with nothing in the records about what it makes (AGOV Underground). Across the whole list, 33 rows combine two or more sources with a strong fit; that is the set worth a call. The rest is one lien or one permit each.

Sensitivity of the top 25 (from `v3_report.json`): doubling recency changes 1 row; removing it changes 9; doubling or removing the source bonus changes 4 and 2; halving or doubling tier B points changes 2 each. The top 10 is the same set under every variant except the source-bonus ones and tier B doubled.

## The check against known projects

The county has 17 known projects (plus four whose county is Adams or a neighbour). 8 of the 17 appear in the ranking, 6 by name and address and 2 by address only:

| Project | Rank | How | Why that rank |
|---|---|---|---|
| C22 Philip Morris ZYN | 1 | name and address (Kairus tie) | air permit, water permit, UCC, press |
| C24 Pretred | 9 (and an unattached row at 215) | name and address | air permit, water permit, press |
| C18 CEMCO | 70 | name and address | water permit at 9410 Heinz Way |
| X08 Boise Cascade door shop | 72 | name and address | water permit at 11011 E 104th Ave |
| D17 Vartega | 84 (and 124) | name and address | air permit at 5675 Pecos St; a second company at the address |
| D16 Metro Water Recovery | 114 | name and address | water and air rows, now weak fit after the web check (public utility) |
| C25 RK Industries | 187 | address only (17450 E 32nd Pl, a possible occupier named) | one press row; the new 3301 Lewiston St site is only in the county pulls |
| X05 Santa Monica Seafood | 190 | address only (1101 E 126th Ave) | one press row |

The nine misses, and why: C19 Prost Brewing (its UCC filings carry a Loveland and a Denver 80211 debtor address, and none was flagged; nothing at 351 W 104th Ave in any statewide file); C20 Amprius (its Colorado registration at Brighton was flagged but the entity is withdrawn, which the method cuts, correctly for a cancelled project); C21 VSK Energy (no record in any file; the project never filed anything); C23 Solid Power (the SP2 water permit at 14902 Grant St is a renewal received four years after issue, which the method cuts; its UCC filings sit at the Louisville HQ); D05 Craft Beverage Warehouse (registration at Longmont, since withdrawn; UCC at the Milwaukee HQ); X04 Wanderment, X11 AMP, X15 Izzio and X16 Kiosk (nothing in the statewide files at their sites; Izzio's only row is an undated pretreatment billing line). Every one of the nine except VSK and AMP was found by a county source in Step 2 (Thornton permits for Solid Power, Izzio and Kiosk; county permits for Craft Beverage; Brighton Legistar for Amprius; PrimeGov for Prost). That is the case for the loader.

The four "Adams or a neighbour" projects: none appears, and Step 2 settled three of them outside Adams (Cerebral in Arapahoe, Curated Barrel and Stay Tuned in Jefferson); Creation Technologies (Adams, Westminster) has no statewide row.

## What the county pulls would add

Cross-check only, no scoring change: of the 133 ranked rows with a street address, 50 have a permit in one of the three county permit pulls at the same address, 26 of them a tier A permit (for example Ardent Mills' rail unload building 2025-10-22, Forge Nano's warehouse renovation 2024-03-11, PMI's "Project Waterfall" core and shell 2024-10-21, Copeland Precast's new 33,110 sq ft precast plant, Coors Distributing's 69,000 sq ft addition); 11 have a planning or development case and 14 a flagged property sale. Conversely the Step 2 back-test found county records for 12 of the 17 known projects, against 8 here, with the Thornton layers firing 2 to 15 months before press. A loader would also add the 11-row unattached-address class that Denver has 391 of, and the fit-out stage.

Loader proposal (not implemented): read `step4-scrape/adams/scrape_*_building_permits.csv` as the permit layer (map `flag_rule` tiers to `permit_new`, `permit_alt`, `permit_b3a`, `permit_b3b`; `industrial_zoning` from the zoning columns; valuation where present) and the four planning files as the site-plan layer (`sdp_heavy` where `industrial_use` = Y on heavy industrial zoning, `sdp_imx` otherwise), then set `LOCAL_LAYERS = True` for Adams. The points table does not change. Denver would be rerun and compared before merging.

## What the data could not show

- Which tenant is behind a county permit: three of the four permit layers carry no applicant. The manual lookup list has the 25 addresses where a hand lookup in Accela, eTRAKiT, CityView or AMANDA would settle it.
- Anything before the first press story for a brand-new plant: as in Denver, the statewide sources fire between announcement and opening and for expansions at existing plants.
- Small tenants (Wanderment, Craft Beverage) and companies whose filings carry an HQ address elsewhere (Solid Power, Prost): the statewide sources place the company, not the plant.
- The OEDIT code names (8 rows, 221 to 228): Project Split is RK Industries by the state's own release (ground truth C25), the rest are undecoded and stay "possible" at most.
- PrimeGov agenda items, blocked by robots.txt since 2026-10-08; it was the source that named the Kairus, Prost, PFG, Ardent Mills and NTT agreements in Step 2.

## Review

An independent review agent that had not seen the build audited these outputs against the skill and the raw Step 4 files (`review_findings.md`). It traced all 525 evidence rows back to the raw statewide records (dates and names exact; the only differences are the documented withheld addresses), re-added every score on all 228 rows, checked 40 scope bases against the evidence, the zip-share file, the geocode cache and the raw AIRS IDs, compared the points table with the code, and scanned every output for personal names, phone numbers, emails, apartment addresses and em dashes. Verdict: no blocking defect.

Fixed in this note after the review: the D-A Packaging evidence line (the water row's own SIC is 1311; the 2992 fit comes from the other-SIC field), the sensitivity sentence (tier B doubled also changes the top 10), the highest unattached-address score (24, not 25), the count of rows with two or more sources and a strong fit (33, not about 40), the split of ground-truth hits (6 by name and address, 2 by address only), and the web-check wording (30 named companies in the final top 50 were never searched).

Left as they are and disclosed: the evidence file carries three extra columns (flag_tier, flag_rule_v2, points) as Denver's does, and no debtor_seq; `first_signal_date` on ranks 8, 16, 20 and 55 comes from support rows the five-per-source listing cap left out of the evidence file; three LLCs named after individuals appear under their registered names (ranks 82, 219, 220; addresses withheld or possible only); rank 8 Valhalla Industries scores 73.5 on a trencher and directional drill filing whose compressor flag word sits past the 500-character cut, which is why its web check is empty and its fit line should be read with the "mobile contractor" caution above; the Adams airport cut contains the word "aircraft" and would cut an aircraft-parts maker's construction permit if no earlier cut fired (none was affected in this run); and the Project Split decode and the PrimeGov agreement date rest on the state release and the Step 2 notes, not on files in this folder.
