# Independent review of the Adams County step 4 outputs (second build, county layers)

Reviewed 2026-10-31 by a review agent that had not seen the build. Scope: `adams_ranked_accounts.csv`, `adams_evidence.csv`, `adams_manual_lookup_list.csv`, `adams_frs_names.csv`, `adams_analysis_notes.md` and `v3_report.json`, checked against the skill (Step 4 and Ground rules), the loader `v3/scripts/v3_local.py`, the county config, the points table in `v3_lib.py` and the raw files in `step4-scrape/` and `step4-scrape/adams/`. All checks were run with my own scripts in a scratch folder; nothing in this folder was changed. The first build's review (`review_findings.md`) is not repeated.

## Verdict

The files are internally sound: every evidence row traces to its raw record by `record_id` with matching date, name and address; every score re-adds; the scope basis holds on every sampled row; the ground-truth column matches the config; no phone numbers, emails or em dashes.

The loader's mapping of the county permit layers is not sound, and that is what the ranking now rests on. Three leaks let non-construction permits score as 18- to 25-point construction permits: (1) the low-value hold in `v3_local.py` tests singular words, so Aurora's "Plan Revisions" and Thornton's "Fire Sprinklers" pass (32 and 8 permits); (2) Aurora's fire alarm, sprinkler and gas-detection sub-permits (`-000-01` to `-000-28`) inherit the parent building's record type and valuation and score 22 or 25 (166 permits, in 44 ranks, the best permit signal in 21 of them, including rank 1 and rank 10); (3) the Adams County layer has no valuation column and no permit-type detail beyond "Other / New", so 97 of its 247 tier A permits are trailers, racking, generators, fences, demolitions and fireworks stands scored 18 or 22 (69 ranks, the best permit signal in 67). Separately, the Aurora permit descriptions name the occupant on most of the 20 unattached addresses in the manual lookup list (rank 10 is the city's animal shelter, rank 48 is a Flying J truck stop, rank 37 is a city lift station), and the notes say the tenant is not named in any source.

- Blocking: 1 (check 3: the loader scores non-construction permits as construction; reaches the top 10).
- Should fix: 9 (checks 3, 4, 7, 8, 10).
- Note: 8.

## Check 1: columns

What I did: read the header rows of the four CSV files.

Found: the ranked file has exactly the 17 columns the skill lists, in order. The evidence file has the 17 shared columns, then `rank`, `company_key`, `match_class`, then the same three extras as Denver and the first build (`flag_tier`, `flag_rule_v2`, `points`). The manual list and FRS file have their own 7 and 6 columns.

Severity: note (inherited layout; same as the first review).

## Check 2: traceability

What I did: sampled 80 evidence rows at random (seed 20261031): 45 from county sources and 35 from the six statewide sources. Looked each up in the raw file named by `source`, by `record_id`, and compared `record_date`, `company_name` and `site_address` (withheld addresses excepted). Then ran the same join on all 6,360 rows.

Found: 80 of 80 found and matching on all three fields. All 6,360 rows join: 0 not found, 0 mismatches. 193 evidence rows carry "withheld (see source record)" under the home-address rule. The Adams County permit and planning layers carry duplicate `record_id`s in the raw files (31 and 247); the evidence file has no duplicate (rank, source, record_id), so each permit appears once per rank.

Severity: none.

## Check 3: loader mapping

What I did: re-implemented the tier and class rules from the loader's docstring and code, applied them to the raw rows of 40 random county permit evidence rows (seed 7) and compared with `flag_tier`, `flag_rule_v2` and `points`. Then scanned the whole population of tier A permit rows by permit type words and, for the Adams County layer, by description; compared the raw tier A set with the evidence; and measured how often the leaked rows are the best signal in their source or add repeat months.

Found, on the 40 sampled rows: tier and class agree with the loader rules on 40 of 40, so the code does what the docstring says, with two rows where a $350k refrigeration unit and a $567k mechanical permit score 18 as alterations (arguable, noted below). No raw tier A permit lost its tier without a reason: of 1,018 raw tier A permits, 994 are in the evidence as tier A, 22 are held at B3b (fire alarm, fire sprinkler singular, solar PV, a cell tower, a canopy, a meter pedestal; all correct) and 2 were cut as cancelled.

Found, on the population:

1. **Plural type names escape the hold.** `LOW_VALUE` is anchored with `\b` after singular words, so "Plan Revisions" and "Fire Sprinklers" do not match. 32 Aurora "Plan Revisions" permits (valuation 250k+ carried from the plan) score 18 or 21 as alterations in ranks 1, 12, 13, 15, 52, 56, 58, 82, 83, 102, 338; 8 Thornton "Fire Sprinklers" permits ($260k to $10.5M) score 18 (or 10.5 as possible) in ranks 104, 111, 164, 165, 166, 186. In ranks 12, 52, 56, 58, 82, 83 and 102 the plan revisions add 1 to 3 repeat months (3 points each). Also "Warehouse / Demolish" (4 Adams County permits) is not caught: "demolish" matches neither "demolition" nor "demo\b", and "warehouse" exempts it anyway; ranks 106 and 198 are unattached addresses whose only tier A signal is a demolition permit (scores 59 and 52).
2. **Aurora sub-permits inherit the parent's type and valuation.** Aurora numbers a building's trade permits `-000-01` onward under the parent's record type ("Commercial Building Permit: Factory Use Building") and valuation. 166 such sub-permits are tier A in the evidence: 71 fire alarm, 45 fire sprinkler, 50 other (gas detection, "Other, not listed"). They sit in 44 ranks, are the best Aurora signal in 21 (the parent `-000-00` row is absent or tier B3b because the intake copy's valuation is a $1 placeholder), add 116 repeat months across 42 ranks, and are the latest signal row in 13. Rank 1's cited "$206M new building received 2026-10-14" is sub-permit `-000-28`, "GAS DETECTION SYSTEM"; none of the 36 tier A Aurora rows behind rank 1 is the main building permit. Rank 10's "$31.3M new building received 2026-08-12" is sub-permit `-000-01`, "AURORA ANIMAL SHELTER | FIRE ALARM".
3. **The Adams County layer scores every flagged permit as construction.** The layer has no valuation column (all 247 distinct tier A permits in the evidence have none; the task's count) and its record type is mostly "Other / New" or "Other / Alteration". Reading the descriptions, 97 tier A rows in 69 ranks are trailers (14), pallet and storage racking (37), generators (12), fences (4), demolitions (9), fireworks stands (3), security camera poles, EV chargers, retaining walls, antennas, a picnic shelter and a guard booth, scored 22 or 18 (9 or 11 as possible); in 67 of the 69 ranks that row is the best Adams County permit signal. Examples: rank 6 Copeland Precast's top permit is BDP26-1384, a temporary office trailer, scored 22 as a new building (the real precast plant permit BDP24-0520 is also there); rank 8 Vartega's permits are pallet racking and spec-suite finishes.
4. **Non-production occupancies pass the tier A test.** With no parcel class, Denver's `NOT_PRODUCTION_PARCEL` test cannot fire, so Aurora "Mercantile Use Building" (17 permits), "Business Use Building" (19) and "Hotel Building" (2) on AD or I-1 zoning score 22 or 25 as new buildings: rank 10 (animal shelter), 45, 58, 102, 119, 160 (hotel), 175, 213, 246, 322, 336, 424, 437, 481. The Step 3 Aurora notes warned that AD zoning covers the DIA hotels and fuel stations; rank 48 (Flying J travel centre) is in the top 50.
5. **Aurora intake and permit twins are both counted.** The Step 3 notes say every Aurora scope appears twice (Online Building Folder intake plus the Limited or Commercial permit) and that step 5 should count one per `scope_key`. The loader keeps both; where the twins fall in different months they add a repeat month: 38 ranks, 50 extra months.
6. **Finaled Adams County permits are shown and staged as not finaled.** The layer carries a status ("Case Finaled", "C of O Issued", "Closed") but no date; `_final` needs a date and returns blank, so 73 finaled or C of O permits in 65 ranks read "not finaled" in `top_evidence` and take the fit-out or under-construction stage (rank 6's BDP24-0520, C of O issued, is one). The docstring and notes assumption 2 say the Adams layer carries neither status.
7. Racking (45 Aurora, 6 Thornton), electrical (32), mechanical (18) and fuel-storage (7) permits at 250k+ also score 18 as alterations. Racking is a warehouse fit-out, not a compressed-air signal; the others are arguable and left as a note.

Severity: blocking for items 1 to 3 (they put non-construction permits in the top 10 and the top 100, and the points table is being applied to rows it was not written for); should fix for 4, 5 and 6; note for 7. Suggested direction, for Matthew to decide: strip the `\b` after the plural-prone words or match on stems, hold Aurora sub-permits (record_id not ending `-000-00`) and intake copies at B3b, count one per `scope_key`, hold Adams County "Other / *" permits whose description names a trailer, rack, generator, fence, demolition, sign or similar, treat Mercantile, Business and Hotel use buildings the way Denver treats non-production parcel classes, and map the Adams County finaled statuses to `record_date`.

## Check 4: arithmetic

What I did: ran `verify_v3.py` on the folder. Then parsed the "Points:" text at the end of `top_evidence` for 40 random rows (seed 99) and for all 1,086 rows, re-added signal + sources + recency + stage + fit against `score`, and re-added the per-source parts against the signal figure.

Found: `verify_v3.py`: "ranked rows 1086, evidence rows 6360, problems: 0", exit 0. 40 of 40 sampled rows re-add to `score` exactly; all 1,086 do; per-source parts sum to the signal on every row.

Two text defects in the breakdown: the per-source labels say "Denver commercial construction permits" (776 rows) and "Denver concept and site plans" (258 rows) while the `sources` column says "Adams County, Thornton and Aurora building permits" and the planning label. And 301 rows show Adams County permits as "$0" (for example "New Building, $0, received 2026-06-08") where the layer has no valuation; the notes say blank, the file says zero.

Severity: should fix (labels and "$0" wording; arithmetic itself is clean).

## Check 5: scope

What I did: sampled 40 Adams-section rows (seed 5; basis not "Adams mailing address" or "OEDIT") and tested each basis against the evidence rows, `adams_zip_share.json`, `geocode_cache.json`, the raw APCD `airs_id` and the raw water `county`. Then scanned all 6,360 evidence rows for a county other than Adams or a city outside the county and looked for an explanation word (possible, support, same name different address, noise, renewal).

Found: 40 of 40 consistent. Permit-layer and site-plan-layer bases (24 rows) each have a confirmed county-layer row with county Adams; zip bases (7) cite a zip with share 0.9999 or 1.0 that appears in the row; county-field (4) and AIRS (1) rows have the matching raw value; geocoder rows (2) cite split zips (0.28, 0.29) and the cache says Adams County or the address is withheld. Across the file, 95 evidence rows carry an outside county or city; 89 are marked possible or support (head offices, other plants, statewide registrations). The 6 unexplained are 4 Mile High CRE press rows whose source county says Denver (ranks 93, 962, 1076, 1078; two of them are placed by the geocoder, two are in the unconfirmed section) and one Hudson registration (rank 836, zip 80642 split, geocoder basis, address withheld). Rank 1078 (7800 S Fairplay St, a Dove Valley address in Arapahoe County) is labelled "Adams mailing address, county unconfirmed" although its mailing city is Denver; it scores 5 and sits in the unconfirmed section, so harmless, but the label is wrong.

Severity: note.

## Check 6: ground truth

What I did: for every `in_ground_truth` starting "yes", checked that the project code is in `GROUND_TRUTH` and that an alias appears in `company_name` or `name_variants`, or a listed address key matches the row's or its evidence rows' addresses. Scanned every other row for a missed alias or address. Compared the notes' hits table with the file and `v3_report.json`.

Found: 13 "yes" rows, all resolve (ranks 1, 3, 8, 67, 218, 222 by name and address; 25 by name; 4, 21, 34 by occupier name and address; 47, 268, 685 by address only). No "no" row carries an alias or ground-truth address. The notes' table of 11 projects and ranks (1, 3, 4 and 47, 8 and 685, 21, 25, 34, 67, 218, 222, 268) matches the file and the report exactly.

Two slips in the notes: "7 by name and address" should be 6 by name and address plus 1 by name only (C23 Solid Power has no address match). And three of the 11 hits (RK Industries, Kiosk, Izzio) are address rows whose names come from `STEP3_OCCUPIERS` in the config, written from Step 2 knowledge of the same projects; the address hit is real, the name hit is circular, and the notes should say so in the check rather than only in assumption 10.

Severity: should fix (one sentence); note (circularity).

## Check 7: people rules

What I did: scanned `company_name`, `name_variants`, `site_address`, `top_evidence` and `next_step` in the ranked file and `company_name`, `site_address` and `description` in the evidence file for phone patterns, email patterns, apartment or PO-box addresses, two-word names with no entity or trade word, and "applicant: First Last" patterns. Checked the three `PERSON_NAMED` keys (full key and first token) against every output file.

Found: 0 phone numbers, 0 emails, 0 of the three `PERSON_NAMED` keys (neither the full key nor its first token appears anywhere). 1 apartment-style address: rank 993, "663 W 91ST AVE APT 204", an unattached address row built from a Thornton plumbing permit for a boiler swap at an apartment complex (score 10). The two-word name scan returned 61 candidates, all businesses or facility names on inspection (Forge Nano, Garrett Companies, Frei Hatchery, Montes Trucking and the like); the one to look at by eye is a water-permit facility name at rank 751 that reads like a person's first and last name (SIC 5812, eating and drinking place, an unflagged support row with the permittee being a contractor). Thornton descriptions carry "[name removed]" where the scraper redacted a name; nothing leaked.

Severity: should fix (drop or strip rank 993's unit; the skill says no apartment-style addresses); note (rank 751).

## Check 8: numbers in the notes

What I did: checked 58 figures in `adams_analysis_notes.md` against `v3_report.json`, the CSV files, the config and the raw files.

Confirmed (49): 1,086 rows; 6,360 evidence rows; 25 manual rows; 19 FRS rows; 13,131 permit-layer rows and 3,653 planning rows (sums of the raw files); 296 flagged deeds and 74 flagged Legistar items; geocoder 163 and the split 50/62/9/9/9/5/1/1/17; 13 unconfirmed; 81 withheld; 36 cancelled permits (2 + 34) and 14 with no address; 2,776 and 169 planning cuts; 0 flagged water rows by the airport cut; web checks 31 (17/6/8) and 19 not confirmed, and 19 named top-50 rows without a web page; 833 address rows; 698 support rows not listed; 255 unattached addresses at 40 or more and 19 with a registry name; 1,065 Adams (232 companies, 833 addresses); 228 at 50 or more; sources 712/259/72/22; fit 162/11/851/41; stage 491/164/160/155/17/78; tier 452/459/175 and 97 of the top 100 with tier A; all 64 rows of the noise-cut table (identical to the report); sensitivity 3/3/4/8/4/6 and "top 10 the same only under tier B halved"; 66 rows with two or more sources and a strong fit; 18 strong fits in the top 25; run date 2026-10-11; OEDIT ranks 1079 to 1086; the first build's 525, 11 and 0; the ground-truth ranks (check 6); the top-10 dates and figures for ranks 2, 3 ($4.5M tenant finish, raw valuation 4,500,000), 4, 5, 6 (SIC 3272, 33,110 sf), 9 (three air rows 2025-03-25) and the $206M and $31.3M valuations.

Wrong or misleading (9):

1. Top-10 line, rank 10: "tenant not named in any source". The Aurora descriptions behind the row say "AURORA ANIMAL SHELTER" on 15 of 16 rows and "CONSTRUCTION TRAILER FOR NEW AURORA ANIMAL SHELTER" on the rest. It is the city's animal shelter, a Business Use Building permit, not an industrial tenant. Should fix (and reconsider whether it belongs in the top 10 at all).
2. Top-10 line, rank 8 Vartega: "the county permit for a 30,000 sq ft expansion". No evidence row for rank 8 carries 30,000 sq ft; the Adams County permits are pallet racking (BDP26-1374, the top permit signal), storage racking and spec-suite tenant finishes at the Pecos Logistics Park, all possible matches. Should fix.
3. Top-10 line, rank 1: "Aurora permits for a $206M new building received 2026-10-14". The 2026-10-14 row is a gas-detection sub-permit; the main building permit is not in the file. Should fix the wording.
4. Top-10 line, rank 6: the top permit signal is a temporary office trailer scored as a $0 new building; the precast plant permit (C of O issued) reads "not finaled". Should fix with check 3.
5. "7 are unattached addresses with an unknown fit" in the top 25: 6 are unattached; the seventh unknown fit is rank 13, Amazon DEN41. Should fix.
6. "7 by name and address" in the ground-truth check: 6, plus 1 by name only (check 6). Should fix.
7. Assumption 2: "Permit types that are fences, signs, alarms, fire sprinklers, hoods, plan revisions ... are held at B3b whatever Step 3 said". Not true for plurals or sub-permits (check 3). Should fix.
8. Assumption 2: "Thornton's closed and expired statuses are mapped to final and cancel dates, the other two layers carry neither". The Adams County layer carries a status (Case Finaled, C of O Issued, Closed) that the loader does not use. Should fix.
9. "What the data could not show: three of the four permit layers carry no applicant; Thornton's description is the exception." Aurora's description names the occupant as a prefix on most rows (Medline, Amazon BJC1 / Project Chorro, Safilo, FedEx, Chadwell Supply, T-Mobile, WIC, QTS, Global Furniture, Alliance Door, GlassFab, Novelty Lights on the manual list alone). Should fix together with check 10.

Unverifiable from the files: assumption 11's "2 registration rows cut" (the report's cuts list only the 1 UCC row; the registrations are dropped in the resolve step without a count); the first build's rank moves for CEMCO and Boise Cascade (taken from the first review).

Severity: should fix (items 1 to 9 are notes text; items 1 to 4 also depend on check 3).

## Check 9: em dashes

What I did: counted U+2014 and U+2013 in all six files.

Found: 0 and 0 in every file.

Severity: none.

## Check 10: manual lookup list and FRS names

What I did: counted rows; matched each manual row's rank and `site_address` to the ranked file; for each FRS row checked the rank exists, the address matches and every registry name appears in that rank's `next_step`; scanned both files for a person's name; then read the permit descriptions behind each manual-list address.

Found: 25 manual rows (the maximum); every rank and address matches the ranked file exactly. 19 FRS rows; every rank exists, every address matches, every registry name is in `next_step`; no person's name (one DBA is a hair-products brand). But the list's `why` says "tenant not identified" on 20 unattached addresses, and the Aurora or Thornton descriptions behind them already name the occupant on at least 15: rank 10 Aurora Animal Shelter (city), 12 Medline, 15 Amazon BJC1 (Project Chorro), 23 Safilo, 24 Aero 70 (spec park), 26 FedEx, 27 Chadwell Supply at Denali Logistics Park, 37 City of Aurora I-70 stormwater lift station, 38 T-Mobile, 45 WIC (Western Industrial Contractors), 47 QTS / RKMC2, 48 Flying J Travel Center, 51 Novelty Lights / Bibbeo, 52 Global Furniture, 56 Alliance Door, 57 GlassFab. Five of them (10, 37, 38, 48 and the Aero 70 shell) are not industrial tenants at all. The list sends Matthew to a portal for names that are already in the evidence file's `description` column.

Severity: should fix (rewrite `why` from the descriptions, drop the municipal and retail sites, and consider a description-prefix parse for Aurora as the next loader step; the notes' "what the data could not show" should change with it).

## Other observations

- Rank 501 and similar: Adams County "PRE - Conceptual Review" cases score 12 as heavy-industrial site plans although the docstring says pre-applications are excluded; `PLAN_SKIP` tests for "pre-application" and does not match "PRE - Conceptual Review". Note.
- `WAT_AIRPORT` still carries `aircraft` and `airlines?` (first review's latent risk); the one aircraft-parts maker is cut by the renewal wave first, so no effect in this build. Note.
- The Review section at the end of the notes still points to this file for what was fixed; it needs filling once the fixes are made.
