# Independent review of the Adams County step 4 outputs

Reviewed 2026-10-31 by a review agent that had not seen the build. Scope: `adams_ranked_accounts.csv`, `adams_evidence.csv`, `adams_manual_lookup_list.csv`, `adams_analysis_notes.md` and `v3_report.json` in this folder, checked against the skill (`.claude/skills/colorado-county-runner/SKILL.md`, Step 4 and Ground rules), the county config, `v3_lib.py`, `v3_config.py`, `v3_score.py` and the raw statewide files in `step4-scrape/`. All checks were run with my own scripts; nothing was changed.

## Verdict

The data files are sound. Every evidence row traces to its raw record, every score re-adds, the scope basis holds on every sampled row, the ground-truth column matches the config, and there are no phone numbers, emails, apartment addresses or em dashes. No blocking defect.

The notes file has six factual slips that should be fixed before the result is reported, the largest being a wrong SIC code in the top-10 line for D-A Packaging and an unfinished sentence about the web checks that hides the fact that 11 of the final top 50 were never searched. Severity summary:

- Blocking: none.
- Should fix (notes text only): 6 items, listed under checks 8, 6 and 5.
- Note: 7 items (layout inheritance, method caveats, one latent config risk).

## Check 1: columns

What I did: read the header rows of the three CSV files.

Found: `adams_ranked_accounts.csv` has exactly the 17 columns the skill lists, in order. `adams_evidence.csv` starts with the 17 shared columns followed by `rank`, `company_key`, `match_class`, and then three more columns not named in the skill: `flag_tier`, `flag_rule_v2`, `points`. This is the same layout as `step5-analysis/v3/denver_evidence_v3.csv`, and `verify_v3.py` depends on the `points` column, so it is inherited, not new. `adams_ranked_accounts_v3.csv` (the raw build output, kept in the folder) carries three extra columns (`tier`, `rank_step5`, `rank_step5b`); the copy under the skill's name does not.

Severity: note. The skill wording says "plus rank, company_key and match_class"; the three extra evidence columns are useful and match Denver. Either amend the skill wording or accept the drift knowingly.

## Check 2: traceability

What I did: sampled 60 evidence rows at random (seed 20261031) and looked each up by `source` and `record_id` in the raw statewide file, comparing `record_date`, `company_name` and `site_address`. Then ran the same join on all 525 rows.

Found: 60 of 60 found; all 525 found. `record_date` and `company_name` match the raw row exactly in every case. `site_address` differs in 24 of the 60 sampled rows and 193 of the 525, and in every one of those the evidence value is "withheld (see source record)" under the home-address rule the notes describe (assumption 10; 85 ranked rows and 193 evidence rows withheld). No other address differences. The evidence file does not carry `debtor_seq`; 7 UCC record_ids in the raw file have more than one debtor with different names, but in each case the evidence row's `company_name` identifies the debtor, so the row is still traceable by record_id plus name.

Severity: note (no defect). Consider adding `debtor_seq` to the evidence file so a UCC row is traceable by key alone.

## Check 3: scope

What I did: sampled 40 ranked rows from the Adams section (seed 7; county_basis not starting "Adams mailing address" or "OEDIT") and tested each basis against the evidence rows, `adams_zip_share.json`, `geocode_cache.json` and the raw APCD file (for AIRS prefixes).

Found: 40 of 40 consistent. Zip-basis rows (12) all cite a zip with Census share of 0.99 or more that appears in the row's own evidence. Geocoder-basis rows (8) all cite a split zip (share between 0.10 and 0.99) or a press address; the four whose address is not withheld are in the cache as Adams County. County-field rows (9) each have a water permit row with county Adams. AIRS rows (11) each have an APCD row whose AIRS ID starts 001. Six sampled rows carry evidence from another city or county (ranks 19, 55, 57, 62, 112, 162); in five of them the outside rows are support rows for a head office or another plant, marked "possible" and "support" in `top_evidence`, so they are explained. Rank 162 is a registration with mailing city Hudson (a Weld County town, zip 80642 at 29 percent Adams) placed in Adams by the geocoder on an address the file withholds; that is the documented method, but it cannot be re-checked from the output.

Severity: note.

## Check 4: arithmetic

What I did: ran `verify_v3.py` on the folder. Then independently parsed the "Points:" text at the end of `top_evidence` for 30 random rows (seed 99) and for all 228 rows, re-adding signal + sources + recency + stage + fit and re-adding the per-source parts against the signal figure.

Found: `verify_v3.py` output: "ranked rows 228, evidence rows 525, problems: 0", exit 0. My re-add: 30 of 30 sampled rows match `score` to the cent; all 228 match; per-source parts sum to the stated signal on every row; scores are sorted descending within each of the three sections. `sources_count` equals the number of distinct sources with points in the evidence on every row.

One traceability gap: `first_signal_date` on ranks 8, 16, 20 and 55 is earlier than any evidence row for that rank. The cause is the listing cap of five support rows per source per account (132 support rows not listed, as the notes say), so the earliest dated support row is not in the evidence file. The skill describes the evidence file as "every source row behind every ranked row".

Severity: note (inherited from the Denver method and disclosed in the notes); worth raising with Matthew as a method question.

## Check 5: points table

What I did: compared every row of the table in `adams_analysis_notes.md` with `PTS` in `v3_lib.py` and the bonuses in `v3_lib.py` and `v3_score.py`.

Found: every point value matches (30/30/25/25/22/20/18/12/12/12/12/8/8/8/8/6/6/6/6/5/5/4/4/3/3/2), as do the million bonus (+3), repeat rule (3 per extra month at 12 or more, max 9), source bonus (8 per extra signal source max 24, 3 per support source max 6), recency (15/8), stage points (12/12/8/8/4) and fit points (15/6/-15). Possible matches at half is `eff_pts`. The one rule in the code that the notes omit is `SMALL_PERMIT_STAGE_CAP = 4` (a permit under $50k adds at most 4 stage points), which cannot fire in Adams because there is no permit layer.

Severity: note (no mismatch).

## Check 6: ground truth

What I did: for every `in_ground_truth` that starts "yes", checked that the project code exists in `GROUND_TRUTH` in `adams.py` and that an alias appears in `company_name` or `name_variants`, or a listed address key appears in the row's or its evidence rows' addresses. Then scanned every "no" row for an alias or address hit that was missed. Then compared the notes' table of hits with the file and with `v3_report.json`.

Found: all 10 "yes" values resolve (ranks 1, 9, 70, 72, 84, 114 by name and address; 124, 187, 190, 215 by address only; rank 215's C24 address matches once the N prefix is dropped as `addr_key` does). No "no" row carries an alias or ground-truth address. The notes' table of eight projects and their ranks (1, 9 and 215, 70, 72, 84 and 124, 114, 187, 190) matches the file and the report exactly.

One slip: the notes say "8 of the 17 appear in the ranking, 5 by name and address and 3 by address only". The notes' own table, the file and the report show 6 by name and address (C22, C24, C18, X08, D17, D16) and 2 by address only (C25, X05).

Severity: should fix (one sentence in the notes).

## Check 7: people rules

What I did: scanned `company_name`, `name_variants`, `site_address` and `top_evidence` in the ranked file and `company_name`, `description` and `site_address` in the evidence file for email patterns, phone patterns, apartment or PO-box or PMB words, debtor names without an entity or business word, secured-party names that look like individuals, and company names of two to four plain words with no entity or trade word.

Found: 0 emails, 0 phone numbers, 0 apartment-style addresses, 0 UCC debtor rows without an entity token, 0 secured parties that read as individuals (the one hit is a filing service). Three UCC descriptions contain "[contact detail removed]" where the scraper already redacted the secured party's contact line. Three entity names are built from what look like personal names, all registered LLCs and all with the address withheld or the row marked possible only: rank 82 (a three-word Spanish given-and-surname LLC, UCC welder filing, address withheld), and ranks 219 and 220 (two run-together romanised names plus "MR LLC", delinquent 2026 registrations named as possible occupiers of two logistics parks). The one plain-word name flagged by the pattern, rank 111 ("CW E..."), is a powder-coating shop on an air permit, not a person.

Severity: note. The names are the legal entity names of registered businesses, which the skill allows; rank 82 is the one to look at by eye, since an LLC named after an individual with a withheld address and one welder lien is close to the line the skill draws.

## Check 8: numbers in the notes

What I did: checked 34 figures in `adams_analysis_notes.md` against `v3_report.json`, the three CSV files, the config and the raw files.

Confirmed (28): 228 ranked rows; 525 evidence rows; 25 manual rows; 19,264 county-pull rows and 8,122 flagged (sum of the nine `step4-scrape/adams/` pulls, excluding the derived `scrape_flagged_adams.csv` and the snapshot copy); 178 geocoded addresses and the split 59/62/9/9/9/5/1/1/23; 18 county unconfirmed; 85 withheld; the web-check split 31 usable (17 strong, 6 moderate, 8 weak) and 19 not confirmed, matching `WEB_CHECKS` and `WEB_NOT_CONFIRMED_V3`; 202 Adams (191 companies, 11 addresses); 76 at 50 or more; sources 148/43/7/4; fit 144/10/29/19; stage 88/17/12/85; tier 156/68/4 and 90 tier A in the top 100; 132 support rows not listed; 11 unattached addresses; 8 OEDIT rows at 221 to 228; every row of the noise-cut table (all 48 counts identical to the report); top-25 fit split 21/3/1 and 10 withheld; City of Westminster at rank 88 and Metro Water Recovery at rank 114 both weak after the web check; 133 ranked rows with a street address and 50 with a county permit at the same address key (I reproduced 133 and 50 with `addr_key` against the three permit pulls); sensitivity counts 1/9/4/2/2/2; the "0 flagged rows removed by the airport cut" claim (the one space-port row, COR900211, is unflagged); the top-10 evidence lines for ranks 1, 2, 3, 4, 6, 7, 9 and 10.

Wrong or inconsistent (6):

1. Top-10 line for rank 5, D-A Packaging: "water permit SIC 2992". The only water row behind the account (COR900402) carries SIC 1311, Oil and gas extraction, and its description says blender and packager of lubricants. There is no SIC 2992 row for this company in the raw water file. Should fix.
2. "The top 10 is the same set under every variant except the source-bonus ones." The report's `sensitivity` has `top10_same: false` for "tier B points doubled" as well. Should fix.
3. "no unattached address reached 40 in this run (the highest is 25)". The highest unattached-address score in the file is 24.0 (rank 124 is a named company, not an unattached address). Should fix.
4. "about 40 rows combine two or more sources with a strong fit". The count is 33. Should fix (or say "about 30").
5. "5 by name and address and 3 by address only" (see check 6): 6 and 2. Should fix.
6. Assumption 7 and the Result section describe the web check as covering "the 50 named companies in the first ranked list's top 50". That is true of the first pass (`webcheck_input_top50.json`), but the web checks moved the list, and the report's `top50_named_without_web_check` shows that 11 named companies in the final top 50 were never searched: ranks 40 to 50 (Precision Casting Prototypes, 4283929 Delaware, Pit 14, Optimized Distribution Partners, Air Squared, Wanco, Per Revolution Machining, Orion Environmental, NOA Brands America, Albert Frei and Sons, Rocky Mountain Arsenal). The notes should say so, since the skill asks that web-checked rows be named. Should fix.

Two more things I could not verify from the local files and flag as unverified: the claim that OEDIT "Project Split is RK Industries by the state's own release" (the raw OEDIT row has an empty `real_company`; the notes attribute it to ground truth C25, which lives in the Project, not on disk), and the PrimeGov robots.txt date.

Also the Review section at the end of the notes is a placeholder ("its findings and what was fixed are recorded at the end of this note") with nothing after it. It needs to be filled in once this review is acted on.

## Check 9: em dashes

What I did: counted U+2014 and U+2013 in the five output files.

Found: 0 em dashes and 0 en dashes in all five files. `verify_v3.py` also checks the two CSVs.

Severity: none.

## Check 10: manual lookup list

What I did: counted rows, and matched each row's rank and `site_address` to the ranked file.

Found: 25 rows, the maximum allowed. Every row's rank and address match the ranked file exactly (22 unattached or county-unconfirmed addresses, 3 named top-15 companies whose product is unconfirmed on the web). The rank 1 entry is named "KAIRUS INC." where the ranked file shows the PMI display name; harmless, since the address matches. The `what_to_check` text names Accela, eTRAKiT, CityView and AMANDA; the ranked file's `next_step` column does not name Accela, which is what `verify_v3.py` enforces.

Severity: none.

## Other observations (notes, not defects in the files)

- Rank 8, Valhalla Industries (score 73.5, three 30-point "compressor" rows): the visible collateral is a Kubota tractor with trencher and plow, a Vermeer D8X12 directional drill, and a generic equipment schedule. The 30 points come from Step 4 flag words (Kaeser, Atlas Copco) that sit in collateral text not shown in the evidence description, and the towable-compressor cut did not fire because no model number is visible. The notes already say to treat it with care; the score is honest to the table. Worth telling Matthew plainly that rank 8 is a utility contractor, not a plant.
- Latent config risk: `WAT_AIRPORT` in `adams.py` includes `aircraft` and `airlines?`. Applied to the water permit name and address, it would have cut Univair Aircraft Corp (COR900003, SIC 3728, aluminum fabricator, a genuine compressed-air user) had the renewal-wave cut not removed that row first. For a re-run with the renewal wave handled differently, or for the next county, the word `aircraft` in an airport cut will remove aircraft parts makers.
- Rank 131 (an ophthalmic surgery society, 6 points for the name word "plastic") and ranks 219 and 220 are the kind of noise the method lets through at the bottom; they do not affect the usable part of the list.
- The notes' top-10 line for rank 2 says the water row is a construction stormwater permit; the evidence has one COR400000 row (2025-10-15) and two COR900000 rows from the 2024 renewal wave, so that is accurate.
