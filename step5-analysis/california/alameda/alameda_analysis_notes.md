# Alameda County, California: analysis notes (first pass, state sources only)

Built 2026-11-10 with the v3 scripts. Files: `alameda_ranked_accounts.csv` (116 rows), `alameda_evidence.csv` (172 rows), and the raw build outputs `ca_alameda_*_v3.csv` and `v3_report.json`.

## Assumptions

1. **Only two kinds of source are scored**: California stormwater enrolments (SMARTS industrial and construction) and named state incentive awards (California Competes, CAEATFA). California has no machinery-lien, business-registration, air-permit, city-permit, planning or press layer in this build. Colorado's strongest signals came from exactly those missing layers.
2. **The points table is the Colorado table, unchanged.** New industrial stormwater enrolment or no-exposure certification 12, construction stormwater with a company-named facility 20, named incentive award 20, plus the usual sources, recency, stage and fit points.
3. **Incentive awards are scored at 20 (Matthew, 2026-11-10)** although they name the city and not the street address. Awards naming a city outside the county as well (Skydio, Sparkz, Atomic Machines) are not scored; they are in `step4-scrape/california/v3_inputs/alameda/ca_incentive_awards_multisite.csv`.
4. **Construction rows count only when marked industrial and company-named.** The rule is in `step4-scrape/california/scripts/build_v3_inputs.py`: owner name carries a maker word, or the site name repeats a distinctive word of the owner name, and the owner is not a developer, utility or public body.
5. Scope uses the county field in the stormwater files and the city in the award records. All Alameda County cities sit wholly inside the county, so no geocoding was needed.
6. Run-date constants are the Colorado ones (run date 2026-10-11), so recency points are comparable across counties and slightly stale for rows processed after that date.
7. Not applied in this pass: person-named entity review, web checks, EPA registry naming (there are no address-only rows), CEQA rows, ABC rows, the multi-site awards.

## Result

- 148 flagged stormwater rows in the county, 26 cut as construction flagged on acreage alone, 122 kept. 8 award rows kept.
- 116 companies ranked. 3 carry two sources (Lam Research, Fuse Energy Technologies, R. Torre & Company). 113 carry one.
- **The list is flat.** 48 rows score exactly 50, 31 score 43 and 21 score 35. Within those bands the order is by date only. With one signal per company the table cannot separate a semiconductor tool maker from a sign shop. Treat it as three recency bands, not 116 ranks.
- Self-check (`verify_v3.py`): 0 problems.

## The check

There is no ground truth. The incentive seeds cannot test a list that scores them. Reading the top 25 by eye: about 21 look like real plants or shops (Lam Research, Fuse Energy, Quanta, Teledyne ETM, Walters & Wolf, Elite Ready Mix, Thermionics, California Cereal Products, Garner Heat Treat, Advanced Grinding, ACCO Engineered Systems, Nitricity, CalPortland and others). The rest are small or doubtful (a sign franchise, a puzzle maker, a print shop, a taqueria coded as food manufacturing). Many of the real ones are small machine shops.

One cross-check that worked without being scored: ACCO Engineered Systems enrolled at 1111 Aladdin Avenue, San Leandro in July 2026, the same address as the "1111 Aladdin Avenue Manufacturing Project" CEQA filing received in June 2026.

**No independent review agent was run on this pass**, which the skill calls for. Do that before anyone calls from this list.

## What the data could not show

- Award-only companies rank near the bottom (Bright Machines 88, Tandem PV 112, Nextracker 113, Noon Energy 116) because nothing in the award record feeds the fit rule, so they score "unknown" fit. A $62.9M manufacturing investment ranks below a taqueria. The award's industry text would fix this, but using it is a rule change and needs a decision.
- A stormwater enrolment says a site is operating or about to. It does not say the site is growing. Change of operator at an existing plant looks the same as a new plant.
- Some source addresses are wrong in the state file (Voxel Energy carries a Seattle zip, Walters & Wolf a Brentwood zip). They are shown as filed.
- Nothing here sees expansions inside an existing building, which is what city permits and the air district list would show.

## Superseded

`alameda_interim_evidence_stack.csv` and `alameda_interim_notes.md` were the unscored first look. This ranking replaces them.
