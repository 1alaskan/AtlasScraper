---
name: "colorado-county-runner"
description: "Run the compressed-air lead pipeline (discovery, validation, scrape, analysis) for one Colorado county. Use when asked to run, replicate or re-run the pipeline for a county, e.g. \"run Adams County\"."
---

# Colorado county runner

Runs the four-step lead pipeline for one Colorado county and produces a ranked list of companies there with growing compressed-air demand. The pipeline was built and proven on Denver County. This skill repeats it for any other county without redoing the parts that are already statewide.

The four steps, in this order: discovery, validation, scrape, analysis. Flag changes, re-rankings and tenant lookups are iterations inside analysis, not separate steps.

## Input

One county name, written below as `{COUNTY}`. Use a lowercase slug with underscores for file names, written below as `{county}` (for example `adams`, `el_paso`).

If the request names several counties, run them one at a time, or one agent per county in parallel. Never let one agent cover several counties: portal vendors differ and cities inside a county often run their own permits.

If no county is named, ask which one. Suggested order when Matthew has no preference: Adams, Arapahoe, Jefferson first (they have known projects to check against), then Weld, El Paso, Larimer, Boulder and Broomfield.

## What is already done. Do not redo it.

- **National and Colorado discovery.** 257 sources were catalogued across national, state and Denver tiers. Only the county tier is new for each county.
- **Validation of 28 sources.** Nine earned a build verdict. Six of those are statewide: Colorado UCC filings, Secretary of State business registrations, OEDIT incentive approvals, state water permits, APCD air permit status feed, Mile High CRE. Their verdicts stand for every county.
- **The statewide scrape.** Those six sources are already pulled for all of Colorado, dated 2024-01-01 onward, in the shared 17-column format. A new county needs a filter on this data, not a new pull.
- **The scoring and matching logic.** The v3 analysis scripts hold the points table, name and address normalisers, entity resolution and stage rules.

What is new per county: its local sources (mostly permit and planning portals), a check on whether they are worth using, a pull of the ones that are, and an analysis run scoped to the county.

## Where things are

Work from the GitHub repo `1alaskan/AtlasScraper` (private), cloned to the session's working folder. It replaces the Windows folder on Matthew's computer. Paths below are relative to the repo root.

- `step4-scrape/`: one `scrape_<source>.csv` per source, `scrape_flagged_v2.csv`, `scrape_notes.md`, and `scripts/` with the pull scripts. The two large statewide files are stored gzipped (GitHub's 100 MB limit): `scrape_ucc_filings/scrape_ucc_filings_v2.csv.gz` and `scrape_business_registrations/scrape_business_registrations_v2.csv.gz`. Before the analysis step run `gunzip -k` on both. The unzipped copies are git-ignored; never commit them. The `.zip` files at the top of `step4-scrape/` hold the older v1 files and are not used.
- `step5-analysis/v3/scripts/`: the analysis pipeline (`build_v3.py`, `v3_lib.py`, `v3_config.py`, `v3_signals.py`, `v3_resolve.py`, `v3_score.py`, `v3_geocode.py`, `verify_v3.py`, `report_v3.py`) and `county_configs/` (one file per county). Denver outputs are in `step5-analysis/v3/`.
- `frs_filtered.csv` and `frs_filter.py`: the EPA facility registry file used to name unattached addresses.

Not in the repo: `step1-discovery/` and `step3-validation/` (state notes, ground truth, back-test notes). They live in the Claude project "Atlas Lead Pipeline New". In a session attached to that project read them with the Projects tool (`project_read` with a path such as `step3-validation/ground_truth_overlay.csv`). If the session is not attached to the project, ask Matthew to attach it or upload the files. Save new step 1 and step 3 outputs under `step1-discovery/` and `step3-validation/{county}/` in the repo and also write them to the project when it is attached.

Commit and push results to the repo at the end of each step so nothing is lost when the session ends. Stage the files by name; never `git add -A` after unzipping the large files.

Stage files into the working folder and compute there with code. Never page data rows through the conversation and never paste data into the chat. Never read a whole large project file into the conversation when it can be saved to disk first.

If the repo is not attached, attach it with the add_repo tool. If a computer is linked and the repo is missing files, the local folder is `C:\Users\spink\OneDrive\Desktop\Personal Projects\Agent Analysit Flow\`, which the repo was copied from.

## Before starting

1. Read `step4-scrape/scrape_notes.md` and the "Bottom line" sections of `step3-validation/backtest_batch1_notes.md` and `backtest_batch2_notes.md`.
2. Check whether this county already has files under any step folder. If it does, resume from the last finished step and say so. Do not overwrite a finished step unless asked.
3. Check the age of the statewide scrape files. If they are more than about 60 days old, say so and ask whether to re-pull with the scripts in `step4-scrape/scripts/` before the analysis step. Do not re-pull without asking.
4. Set up a task list with the four steps, the inventory page update, and the final check.

## Step 1: Discovery (county tier only)

Run one discovery agent with the prompt below. Fill `{COUNTY}` and paste in the lines about this county from `step1-discovery/compressed_air_demand_sources_colorado_state_notes.md` as starting points. Keep the prompt loose. Do not add a fixed column list, a signal type list, or a requirement to match the national or state inventory columns. Matthew merges inventories himself later.

```
ROLE
You are a data source discovery agent. You find and verify sources. You do not scrape or build.

OBJECTIVE
Find every local data source in {COUNTY} County, Colorado that could help identify individual facilities with growing compressed air demand. Local tier = published by the county, any city or town inside it, special districts, local utilities, local EDOs, local press. Skip state and federal sources; those are covered elsewhere. If you run into one, note it in one line and move on.

CONTEXT
- Unit of interest: the facility (physical site), not the parent company.
- Growing demand looks like: new plant, expansion, new production line, added shift, new process equipment, or any new pneumatic-heavy process.
- Useful signals fire before a compressor purchase, ideally 3 to 24 months ahead.
- The causal chain, roughly: announcement or rumor > hiring and utility requests > incentive award or land purchase > permits and site selection > capex approval > contractor selection > compressor purchase. Every link leaves a paper trail somewhere.
- Think widely. Direct signals, correlates, proxies, odd sources nobody in sales would think of.

FIRST STEP
Map the jurisdictions. List every incorporated city and town in the county with meaningful industrial land, and which body handles permits and planning for each. Unincorporated areas go to the county. Many cities run their own portals. Do not assume the county portal covers them.

STARTING POINTS (unverified, not a checklist, go beyond them)
{PASTE THE LINES FOR THIS COUNTY FROM THE STATE NOTES FILE}
Common local source types:
- Building, mechanical, electrical, and plumbing permits. Look for valuation, square footage, service size, equipment descriptions.
- Land use and development review cases: site plans, rezonings, special use permits, minor amendments at existing plants.
- Planning commission, county commissioner, and city council agendas, packets, and minutes.
- Local incentives: tax rebates, personal property tax refunds, fee waivers, urban renewal and TIF agreements.
- Assessor and recorder: industrial sales, deeds, new personal property accounts.
- Local utilities and special districts: water and sewer taps, industrial pretreatment permits, electric co-op and municipal utility board minutes.
- Fire department: plan review, hazmat and operational permits.
- Local liquor and marijuana licensing hearings.
- Local EDO and chamber announcements, local business press.
- City and county open data portals and GIS layers.

APPROACH
Your call. Follow leads where they go. If a source points to another source, chase it. Favor breadth first, then depth on the promising ones.

ONE HARD REQUIREMENT
Verify every source by actually loading it. Confirm it exists, how fresh the latest record is, how it is accessed, whether it needs a login, whether it blocks automated access, and whether its terms allow commercial use. Note the portal vendor (Accela, Tyler EnerGov, eTRAKiT, SmartGov, Laserfiche, Socrata, ArcGIS and so on); that decides the scraper later. If you cannot confirm something, say so. Do not list from memory.

OUTPUT
A full inventory, ranked by how useful you judge each source to be for finding facilities early. For each source include at minimum: name, publisher, jurisdiction covered, URL, what it tells you, how it can be linked to a specific facility, how early it fires, access method, portal vendor, cost, and verified yes/no. Add whatever other fields you find useful. Structure it however fits what you find.

Also include a notes file covering:
- The jurisdiction map from the first step.
- What you considered and rejected, and why.
- Gaps: jurisdictions or chain links with nothing usable.
- Whether a CORA request could unlock anything not published. Draft it, do not send it.
- Two or three real recent examples of industrial projects visible in these sources, as proof the signal is there.
- Anything surprising.

Save as a CSV plus a notes markdown file, with the county name in both filenames.

BOUNDARIES
Do not submit forms, create accounts, file records requests, or bulk download data. Draft requests and hand them back.
```

Save as `step1-discovery/compressed_air_demand_sources_{county}_county.csv` and `..._{county}_county_notes.md`.

Two things the Denver run taught:

- The main way a county run fails is treating the county portal as complete. The jurisdiction map exists to stop that.
- A portal can exist and hold nothing but residential roofing permits. The "real recent examples" requirement filters those out. A source with no industrial example is not a candidate.

## Step 2: Validation

Decide which of the new county sources are worth pulling. Only test sources that pass four tests: the source could fire before press, it resolves to a facility, it is free and reachable, and it keeps dated history. Paid sources, press feeds, undated snapshots and context data are not candidates. List them as not tested, with the reason.

Pick the method by how many known projects the county has. Count them in `step3-validation/ground_truth_overlay.csv` (use its cleaned county column, joined on `project_id` to `ground_truth_projects.csv` and `ground_truth_projects_overflow.csv`, treated as one set of 70).

**Five or more known projects in the county: back-test.** For each candidate source and each in-county project, find whether the source holds a record that belongs to the project and when that record first existed. Compare to the project's earliest press date (the earliest rumor, press mention or announcement in `ground_truth_milestones.csv`, skipping rows labelled UNVERIFIED). Report coverage split by incentivized versus not, how many matches fired before press, noise from a one or two month sample, which field did the matching, and what was blocked.

**Fewer than five: inherit and spot-check.** Most counties land here. Do both:

- Inherit by source type. A commercial construction permit layer or a concept and site plan layer of the same kind as Denver's starts from Denver's build verdict. A recorded-plan layer, property sales layer or pending-licence list starts from Denver's park or drop verdict.
- Spot-check on real data. Pull a sample of 50 to 200 recent records. Confirm the source carries dated, address-level records for industrial work, find two or three real industrial projects in it, and measure the share of rows that are not industrial at all.

Give each tested source one verdict: build, park or drop, with a one-line reason. Label the basis of every verdict as `back-tested`, `inherited + spot-checked`, or `spot-checked only`. Never present an inherited verdict as a tested one.

Matching rules, carried from Denver: a wrong match is worse than a miss, so keep uncertain matches in a separate "possible" class. Lead time here means months before press. It does not mean months before a compressor purchase, and no write-up may claim that.

Save as `step3-validation/{county}/validation_{county}_notes.md` and `validation_{county}_matches.csv`. List any corrections the test suggests to the ground truth, without applying them.

If no county source earns a build verdict, say so plainly and carry on. The county runs on the six statewide sources alone.

## Step 3: Scrape (county build sources only)

Pull only this county's build-verdict sources. One agent per portal platform, in parallel where there are several. Each agent follows the `datasource-validator-scraper` skill if it is available: confirm the access route, check robots.txt and terms, sample, build the pull, then QA.

Scope: sites in `{COUNTY}` County, records dated 2024-01-01 onward. Carry in still-active 2023 construction permits.

**Wide net: tag, do not drop.** Keep every row in scope. Set `flag` to Y or N with the rule that fired in `flag_rule`. The only rows to leave out are those about private individuals.

Write one CSV per source with exactly these columns, in this order:

`source, source_level, record_id, record_date, date_type, record_type, company_name, company_role, site_address, city, county, zip, description, flag, flag_rule, source_url, retrieved_at`

- `source_level`: `County ({COUNTY})`.
- `record_date`: ISO format. `date_type` says what the date is (filed, received, opened, approved, published).
- `company_role`: applicant, permittee, contractor, tenant, owner, or unknown.
- `description`: trimmed to 500 characters.
- Source-specific fields (valuation, square footage, zoning) go in extra columns after `retrieved_at`.
- Leave a field blank when the source does not carry it.

Flag rules for local permit and plan sources. Copy the tier A and tier B rules that the Denver sources use, as recorded in `scrape_notes.md` and the Step 4b notes in `step4-scrape/`. In outline: tier A is higher-value permits on industrial land, tier B is the wider net below that, and every concept or site plan row is flagged. Report how many rows each rule flags.

**Browser-only portals (Accela and similar).** No automated collection and no agent browsing. Do the terms check only, report what the terms say, and treat the portal as a manual lookup source. This matches the decision Matthew made for Denver trade permits.

Save as `step4-scrape/{county}/scrape_{source}.csv`, `scrape_flagged_{county}.csv` (the flag = Y rows from the county sources), `scrape_notes_{county}.md` (assumptions, one source card per source with route, row counts, rows flagged per rule, null rates on company name, address and date, date range, what broke, how to rerun), and the pull scripts under `step4-scrape/{county}/scripts/`.

## Step 4: Analysis

Use the v3 scripts. Do not rewrite the pipeline and do not change the points table for this county. The same table must score every county so the lists can be compared and stacked.

### County config split: done

The v3 scripts now take the county as an argument (`--county <name>`). Everything Denver-specific lives in `step5-analysis/v3/scripts/county_configs/denver.py`; the points table, word lists, normalisers and fit rules stay in `v3_config.py`. The Denver rebuild after the split was checked byte for byte against the earlier output (ranked file, evidence file, rank changes and report all identical). Do not change `v3_config.py` or the points table for a new county. If a county needs a rule the config cannot express, stop and ask.

### County config for `{COUNTY}`

Copy `county_configs/_template.py` to `county_configs/{county}.py` and fill it in (see `county_configs/README.md`). It carries:

- **Scope test.** `COUNTY`, `COUNTY_FULL`, `AIRS_PREFIX` (the county's FIPS code, e.g. Adams 001, Denver 031) and a `{county}_zip_share.json` file in the scripts folder (share of each zip inside the county, from the Census 2020 ZCTA-to-county file; build it before the first run). Use `county` where the source carries it. Where it does not (UCC, business registrations), use zip codes from the Census ZCTA-to-county file, and the Census geocoder for zips that straddle county lines. Say which files were used. For APCD, the county field can hold the company office in place of the site, so check it against the AIRS ID county prefix on a sample.
- **Mailing-address trap.** Sites whose mailing city suggests one county but which sit in another are common around Denver. Mark them `county_basis = mailing address, county unconfirmed` and keep them in a separate section. Do not drop them and do not guess.
- **County sources.** `LOCAL_LAYERS = False` until this county has build-verdict local sources with a loader. The v3 code only reads Denver's permit and site plan layers; a new county's local sources need a loader added first, which is a code change to propose to Matthew, not to improvise.
- **Local noise cuts.** `WAT_AIRPORT` and `WAT_AIRPORT_SIC` for the water permit cut. Whatever this county's data shows, such as an airport, a military base, a university campus or a large retail district. Report how many rows each cut removes.
- **Entity merges and overrides.** `KNOWN_TIES`, `STEP3_OCCUPIERS`, `WEB_CHECKS*`, `WEB_DROPS`. Only ones backed by a document or an exact name plus address.
- **Ground-truth list.** `GROUND_TRUTH`. The known projects in this county from the overlay file. It may be empty.

### Run

```
cd step5-analysis/v3/scripts
python3 build_v3.py ../../../step4-scrape ../.. --county {county} --out ../../{county}
python3 verify_v3.py ../../{county}
python3 report_v3.py ../../{county}
```

The build writes `{county}_ranked_accounts_v3.csv` and `{county}_evidence_v3.csv`; copy them to the names listed below. The Census geocoder step is resumable: if it stops with exit code 3, run the same command again. If the shell cannot reach geocoder.census.gov, run with `--offline`, say so, and treat uncached addresses as could-not-place.

The method inside the scripts, for reference:

1. Scope records to the county.
2. Cut known noise and report counts per cut.
3. Resolve records to companies by normalised name and address, keeping raw values and every name variant.
4. Attach address-only records (permits, site plans) to companies by address. A contractor is not the account. Where no company can be attached, keep the address as its own candidate.
5. Once a company or address is a candidate, pull all its rows from every source, flagged or not.
6. Score tier A and tier B signals together under the fixed points table, then rank.
7. Name unattached addresses scoring 40 or more by joining the EPA facility registry file in the folder, plus a local business licence dataset if the county or its cities publish one. Parcel owner names need Matthew's sign-off first.
8. Run the self-check script.

Web lookups are allowed only to confirm what a specific top-ranked company makes or whether a site is in the county. Say which rows were checked this way. OEDIT code names are never decoded from memory: a match on county, industry and timing is "possible" at most.

### Check the result

- If the county has known projects, report how many appear in the ranking, at what rank, and why the misses were missed. Do not tune anything to the known projects and then report that as accuracy.
- If it has none, say that the list is unchecked. Then read the top 25 by eye and report what share look like real plants or shops.
- Have a separate review agent, one that has not seen the build, audit the outputs against this skill and the raw data before reporting.

Save under `step5-analysis/{county}/`: `{county}_ranked_accounts.csv` (columns: `rank, company_name, name_variants, site_address, zip, county_basis, stage, score, sources_count, sources, first_signal_date, latest_signal_date, top_evidence, compressed_air_fit, match_confidence, in_ground_truth, next_step`), `{county}_evidence.csv` (every source row behind every ranked row, in the shared 17 columns plus `rank`, `company_key` and `match_class`), `{county}_manual_lookup_list.csv` (up to 25 addresses or names where a hand lookup would settle who the tenant is, only if the county has a browser-only permit portal), and `{county}_analysis_notes.md` (assumptions and the points table at the top, then method, noise cuts with counts, the check, and what the data could not show).

## Last step: update the inventory page

Matthew keeps one page, "Compressed Air Source Inventory", that lists every source found in discovery with its level and verdict. Each county run adds its sources to that page and republishes it. This is standing permission from Matthew: do it without asking.

1. **Write the record file.** Save `step1-discovery/inventory_update_{county}.csv`: one row per county source found, with its level as `County ({COUNTY})`, discovery score, whether it was tested, verdict, basis of the verdict, and whether it is in use.
2. **Find the page.** List Matthew's artifacts and pick the one titled "Compressed Air Source Inventory". Read the whole page (the full `index.html`, not a truncated preview) and work from that saved file.
3. **Add the rows.** The sources live in one array in the page script, `const DATA=[...]`. Each source is an object with these fields: `file, tier, rank, name, publisher, url, family, signal, tells, gran, lead, cadence, access, cost, score, verified, caveats, tested, use, why`. Add one object per county source with the same fields, filled from the discovery inventory and the validation verdicts:
   - `file`: `County`. Look at how the Denver rows carry the county name and do the same for `{COUNTY}`.
   - `rank`: the rank within this county's inventory.
   - `verified`: `yes` or `partial`, from the discovery check.
   - `tested`: blank if not tested. Otherwise the basis and verdict, such as `Back-tested: build` or `Inherited + spot-checked: park`.
   - `use`: `Y` only for a build verdict. Otherwise `N`.
   - `why`: for every `N`, the reason in one line (the test result, or why it was not tested).
4. **Make the county visible.** The level chip must show the county name, and there must be a way to filter to one county. If the page only has National, State and County buttons, add a county dropdown that appears when County is selected. Keep the existing look and filters.
5. **Update the words.** The footer states how many sources were back-tested and when discovery ran. Update those numbers and add the date of this county's discovery run.
6. **Do not touch existing rows.** Add only. If this county is already on the page from an earlier run, replace that county's rows and leave every other row as it is.
7. **Republish to the same link.** Pass the page's existing URL so it updates in place. Never publish a second copy.
8. **Check it.** Confirm the script parses, the row count equals the old count plus the new rows, and the counts at the top of the page add up. Then look at the rendered page.

If the page cannot be found, or the publish is refused, leave the record file in place and tell Matthew. Do not create a new page in its place.

The page holds data sources only. Lead lists stay in the spreadsheets under `step5-analysis/{county}/` and do not go on this page.

## Stop and ask

Run the four steps and the inventory page update through without waiting for approval between them. Stop only for these:

- A source's terms on automated access are ambiguous. Report what they say and offer the options in a table.
- Using parcel owner names or any dataset that carries personal names.
- Re-pulling the statewide sources.
- Any edit to the v3 scripts or `v3_config.py` changes the Denver rebuild: rerun `--county denver` into a scratch folder and compare with `step5-analysis/v3/` before going on.
- Anything that would be sent, submitted or deleted.

If Matthew is not there to answer, finish everything that does not depend on the decision, set the decision out, and stop.

## Ground rules

- Query the real data. Do not estimate from a source's description.
- Respect robots.txt and site terms. If a route is blocked, report it and stop. Do not work around it with direct requests, caches or mirrors.
- Do not submit any records request, create any account, or contact any agency, vendor or company. Draft requests and hand them back.
- Do not use any Atlas Copco internal data.
- No personal data. No people's names, phone numbers, emails or home addresses in any output. Drop UCC rows where the debtor may be an individual. Contacts come later from ZoomInfo.
- Never fill a gap with a guess. Label every join as confirmed (exact name plus address, or a document tying them) or possible.
- State every assumption at the top of the notes for that step.
- If budget runs out partway, say exactly which sources, date ranges or steps were not finished so the next run can pick up there.
- Do not use em dashes in any output.

## What to tell Matthew at the end

He prefers short, direct, numbers-first reports, with options in a table when there is a decision. Lead with the result. No step-by-step recap.

- How many local sources were found, how many tested, how many earned a build verdict, and on what basis.
- How many rows the county pull added, and how many were flagged.
- How many accounts were ranked, and the top 10 with one line of evidence each.
- The check: known projects found and at what rank, or a plain statement that the county had none to check against.
- That the inventory page was updated, and how many sources it now lists.
- What the sources could not show.
- The three or four decisions he needs to make next.

## What to expect, so the result is read correctly

- No public source reliably beats the first press story for a brand-new plant. These sources fire between announcement and opening, and for expansions at existing plants that press never covers. That window is still ahead of the compressor purchase.
- A county with no usable permit portal gets a list built from machinery liens, registrations and state permits only. Rural counties may return a handful of rows or none. That is a real result, not a failure. Report it as it is.
- Most rows in any county list are unconfirmed. In Denver, 707 ranked rows came down to a small number of leads worth a call. Say how many rows in this county's list are solid, not just how long the list is.