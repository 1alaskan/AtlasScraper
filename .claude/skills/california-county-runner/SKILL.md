---
name: "california-county-runner"
description: "Run the compressed-air lead pipeline (discovery, validation, scrape, analysis) for one California county. Use when asked to run, replicate or re-run the pipeline for a California county, e.g. \"run Alameda County\"."
---

# California county runner

Runs the four-step lead pipeline for one California county and produces a ranked list of companies there with growing compressed-air demand. It is the California version of `colorado-county-runner`. Same four steps, same output formats, same points table.

The four steps, in this order: discovery, validation, scrape, analysis. Flag changes, re-rankings and tenant lookups are iterations inside analysis, not separate steps.

**Status of this skill: written 2026-11-10, before any California county had been run.** The Colorado skill was written after Denver proved the method. This one is a plan built from the California state discovery and the Colorado experience. Expect the first county to expose things it gets wrong. When that happens, finish the run, then propose edits to this skill and update the repo copy.

## Input

One county name, written below as `{COUNTY}`. File slug `{county}`: lowercase with underscores (`alameda`, `santa_clara`, `los_angeles`).

One agent never covers several counties. If no county is named, ask. Suggested order when Matthew has no preference: Alameda and Santa Clara first (Fremont, Newark, San Jose: his home territory and the densest manufacturing in the Bay Area), then San Joaquin, Sacramento, Los Angeles (very large: propose splitting by city group before starting), Orange, San Bernardino, Riverside, San Diego, Fresno, Kern.

## How California differs from Colorado. Read before starting.

- **No statewide air permit agency.** Air permits come from local air districts. A county belongs to one district (a few are split). The district is a source to discover and test in the county run, and its verdict is then reused for every other county in the same district. Known so far: South Coast AQMD (Los Angeles, Orange, and the urban parts of Riverside and San Bernardino), Bay Area AQMD (Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, and parts of Solano and Sonoma), San Joaquin Valley APCD (San Joaquin, Stanislaus, Merced, Madera, Fresno, Kings, Tulare, and the valley part of Kern). Confirm the district for `{COUNTY}` by loading the district's own page.
- **Incentive recipients are named.** California Competes and CAEATFA print the company and city at approval. There are no code names to decode.
- **CEQA.** Any project needing discretionary approval files documents with the State Clearinghouse (CEQAnet), with the city or county as lead agency. This has no Colorado equivalent.
- **Cities do the permitting.** Almost all industrial land is inside incorporated cities, each with its own building and planning portal. The county portal covers unincorporated land only. A county run here is mostly a set of city portals.
- **Records requests** fall under the California Public Records Act (CPRA), not CORA.
- **Hazardous materials** are regulated by local agencies (CUPAs) and surface through the CalEPA Regulated Site Portal.
- **No ground truth exists.** Colorado had 70 known projects to back-test against. California has none yet. See Step 2.
- **No statewide scrape exists yet and the v3 scripts are written for Colorado.** See the state foundation below.

## What is already done

- **National discovery** (in the Claude project "Atlas Lead Pipeline New").
- **California state discovery** (2026-11-10): 31 sources, `step1-discovery/compressed_air_demand_sources_california_state.csv` and `..._california_state_notes.md` in the repo. 12 verified, 19 partial. The notes list the open questions and the leads not chased.
- **The method**: the shared 17-column scrape format, the tier A and tier B flag rules, the county-layer loader (`v3_local.py`), the points table, the review step, the dashboard and the inventory page. All proven on Denver, Adams and Weld.

Nothing else. No California source has been validated, pulled or scored.

## Where things are

Work from the GitHub repo `1alaskan/AtlasScraper` (private). Paths are relative to the repo root. The run works from a cloud session with no computer linked.

1. If the repo is not cloned, attach it with `add_repo` (owner `1alaskan`, repo `AtlasScraper`, access `push`) and clone it with the command the tool returns. One clone, generous timeout.
2. Read `CLAUDE.md` and `step1-discovery/compressed_air_demand_sources_california_state_notes.md`.
3. Colorado sanity check before touching any script: `cd step5-analysis/v3/scripts && python3 build_v3.py ../../../step4-scrape ../.. --county denver --out <scratch folder>` (after `gunzip -k` on the two `.csv.gz` files under `step4-scrape/`) and `cmp` the outputs against `step5-analysis/v3/`. They must be identical.

California files go in California folders so nothing collides with Colorado:

- `step1-discovery/compressed_air_demand_sources_ca_{county}_county.csv` and `_notes.md`
- `step3-validation/california/` for state verdicts, `step3-validation/california/{county}/` for the county
- `step4-scrape/california/` for state pulls and scripts, `step4-scrape/california/{county}/` for the county
- `step5-analysis/california/{county}/`
- `step5-analysis/v3/scripts/county_configs/ca_{county}.py`

All California outputs live in the repo only. The Claude project is full; do not write to it. Commit and push to `main` at the end of each step. Stage files by name; never `git add -A`. Keep any file over 50 MB gzipped and git-ignore the unzipped copy.

Stage data into the working folder and compute there with code. Never page data rows through the conversation.

## Before starting

1. Check whether `step4-scrape/california/STATE_FOUNDATION.md` exists. If not, the state foundation below comes first.
2. Check whether this county already has files under any step folder. If so, resume from the last finished step and say so.
3. If the state pulls are more than about 60 days old, say so and ask before re-pulling.
4. Set up a task list: state foundation (if needed), the four steps, dashboard, inventory page, final check.

## State foundation (once, on the first California county run)

Colorado's county runs filter a statewide scrape that already exists. California needs the same base built once. Do it inside the first county run, in three parts, and write `step4-scrape/california/STATE_FOUNDATION.md` recording what was done, when, and each source's verdict. Later county runs read that file and skip this section.

**Part 1. Settle the open questions and validate the state candidates.** Each agent follows the `datasource-validator-scraper` skill. Candidates, with what must be settled first:

| Source | Settle first | Colorado counterpart |
|---|---|---|
| SMARTS stormwater CSVs (data.ca.gov) | Open both facility file headers: SIC code, NOI or processed date, operator, address | State water permits |
| California Competes agendas (GO-Biz) | None. Parse the agenda PDFs back to 2024 | OEDIT approvals, but named |
| CAEATFA STE agendas, staff reports, awards workbook | Open the workbook; check whether staff reports give a street address | none |
| Employment Training Panel packets | None. Parse agendas and packets back to 2024 | none |
| ABC Daily Data Export | Download once, confirm fields and manufacturer type codes | none (Colorado publishes issued licences only) |
| CEQAnet | Confirm the CSV export carries development type and description; read any terms | none |
| California UCC (bizfile bulk order) | Needs Matthew: a bizfile login to read the bulk order spec, price and whether collateral text is included. Do not automate the search screen | Colorado UCC |
| Secretary of State business entities (bizfile bulk) | Same login question | Business registrations |
| Cal/OSHA Pressure Vessel Registration Database | Read DIR's conditions of use. Until they are read and allow it, this is a manual lookup for top-ranked sites only | none |
| CalEPA Regulated Site Portal, EDD WARN, CEC awards, IBank bonds | Lower priority; test if budget allows | various |

Verdict per source: build, park or drop, with basis. With no ground truth, the only bases available are `spot-checked only` and `inherited from Colorado counterpart + spot-checked`. Save to `step3-validation/california/validation_california_state_notes.md`.

**Part 2. Pull the build sources statewide**, dated 2024-01-01 onward, in the shared 17-column format (below), one CSV per source under `step4-scrape/california/`, with scripts and a `scrape_notes_california.md`. Wide net: tag, do not drop.

**Part 3. Make the v3 scripts state-aware.** They hardcode Colorado: the state code `CO` in `v3_signals.py`, `v3_resolve.py` and `v3_geocode.py`, the source labels in `v3_lib.py` and `report_v3.py`, state FIPS `08` in `build_zip_share.py`, and readers for the six Colorado files. Add a state setting (default Colorado) and California readers that map California rows onto the existing signal kinds. Rules:

- Do not change the points table (`v3_lib.PTS`) or `v3_config.py` word lists.
- After every edit, rebuild Denver, Adams and Weld into scratch folders and `cmp` against the stored outputs. All three must be byte for byte identical.
- Mappings that are safe by analogy: SMARTS Industrial General Permit enrolment or No Exposure Certification to `water_new`; SMARTS Construction General Permit with a manufacturing SIC or company-named site to `water_construction`; air district permit application for process equipment to `air_process`, minor or exempt to `air_apen`; UCC kinds unchanged if the bulk file carries collateral text; press to `press_name` and `press_addr`; city permits and plans through the county-layer loader as in Adams and Weld.
- Mappings that need Matthew before they score anything: California Competes and CAEATFA awards (candidate: `incentive_named` at 20, but that kind was defined for agreements naming the facility address, and these name the city), Employment Training Panel contracts, ABC pending manufacturer licences, CEQAnet filings, pressure vessel records. Until he decides, load them as evidence rows with zero points so they show in the evidence file and the sources column.

If Part 3 turns out larger than a config split, stop and set out the options in a table.

## Step 1: Discovery (county tier only)

Run one discovery agent with this prompt. Fill `{COUNTY}`, name the county's air district, and paste any lines about the county or its cities from the state notes. Keep the prompt loose: no fixed column list and no requirement to match other inventories.

```
ROLE
You are a data source discovery agent. You find and verify sources. You do not scrape or build.

OBJECTIVE
Find every local data source in {COUNTY} County, California that could help identify individual facilities with growing compressed air demand. Local tier = published by the county, any city inside it, the regional air district, the local hazardous materials agency (CUPA), special districts, local utilities, ports and airports, local EDOs, local press. Skip state and federal sources; those are covered elsewhere. If you run into one, note it in one line and move on.

CONTEXT
- Unit of interest: the facility (physical site), not the parent company.
- Growing demand looks like: new plant, expansion, new production line, added shift, new process equipment, or any new pneumatic-heavy process.
- Useful signals fire before a compressor purchase, ideally 3 to 24 months ahead.
- The causal chain, roughly: announcement or rumor > hiring and utility requests > incentive award or land purchase > environmental review, permits and site selection > capex approval > contractor selection > compressor purchase. Every link leaves a paper trail somewhere.
- Think widely. Direct signals, correlates, proxies, odd sources nobody in sales would think of.

FIRST STEP
Map the jurisdictions. List every incorporated city in the county with meaningful industrial land and which body handles building permits and planning for each. In California nearly all industrial land is inside cities with their own portals; the county covers unincorporated areas only. Also name the air district, the CUPA, the electric utility or utilities (investor-owned, municipal, or community choice), and the wastewater agencies with industrial pretreatment programs.

STARTING POINTS (unverified, not a checklist, go beyond them)
{PASTE LINES FOR THIS COUNTY FROM THE STATE NOTES FILE}
Common local source types:
- City and county building, mechanical, electrical and plumbing permits. Look for valuation, square footage, service size, equipment descriptions. Many California cities publish these as open data.
- Planning cases: conditional use permits, design review, site plans, zoning administrator and planning commission items. CEQA documents posted by the lead agency.
- Air district: permit applications received, authorities to construct, public notices, facility lookup tools.
- City council and board of supervisors agendas and packets; development agreements; local incentive or fee deferral programs.
- Assessor and recorder: industrial sales, new business property accounts (check what is public).
- Utilities and districts: municipal utility board items, new service or substation items, industrial pretreatment permit lists, water and sewer capacity fees.
- Fire department and CUPA: plan review, hazardous materials permits.
- City business licence or business tax registries (many are open data with start dates and addresses).
- Port and airport commission leases, where relevant.
- Local EDO announcements, local business press.
- City and county open data portals and GIS layers.

APPROACH
Your call. Follow leads where they go. Favor breadth first, then depth on the promising ones.

ONE HARD REQUIREMENT
Verify every source by actually loading it. Confirm it exists, how fresh the latest record is, how it is accessed, whether it needs a login, whether it blocks automated access, and whether its terms allow commercial use. Note the portal vendor (Accela, Tyler EnerGov, eTRAKiT, Socrata, ArcGIS, OpenGov, Legistar, Granicus, Laserfiche, OnBase and so on); that decides the scraper later. If you cannot confirm something, say so. Do not list from memory.

OUTPUT
A full inventory, ranked by how useful you judge each source to be for finding facilities early. For each source include at minimum: name, publisher, jurisdiction covered, URL, what it tells you, how it can be linked to a specific facility, how early it fires, access method, portal vendor, cost, and verified yes/no. Add whatever other fields you find useful.

Also a notes file covering: the jurisdiction map; what you rejected and why; gaps; whether a California Public Records Act request could unlock anything not published (draft it, do not send it); two or three real recent examples of industrial projects visible in these sources; anything surprising.

Save as a CSV plus a notes markdown file, with the county name in both filenames.

BOUNDARIES
Do not submit forms, create accounts, file records requests, or bulk download data. Draft requests and hand them back.
```

Two lessons carried from Colorado: the county portal is never complete, and a portal that holds only residential work is not a candidate. A source with no real industrial example is not a candidate.

## Step 2: Validation

Only test sources that could fire before press, resolve to a facility, are free and reachable, and keep dated history. List the rest as not tested, with the reason.

There is no ground truth, so build a small seed set first: the named California Competes and CAEATFA awards located in `{COUNTY}` since 2024 (from the state pulls). These are real, dated projects. Label them `incentive-seeded` and say plainly that they are biased toward large, incentivized projects.

- **Five or more seed projects in the county:** back-test each candidate source against them. For each, find whether the source holds a record belonging to the project and when it first existed, compared with the award date and, where a quick search finds one, the earliest press date. Report coverage, how many records came before the award, noise from a one or two month sample, the matching field, and what was blocked. Basis label: `back-tested (incentive-seeded)`.
- **Fewer than five:** inherit by source type from the Colorado verdicts (a commercial permit layer or site plan layer starts from build; recorded plans, property sales and pending-licence lists start from park or drop) and spot-check 50 to 200 recent records for dated, address-level industrial work and the share of rows that are not industrial. Basis label: `inherited + spot-checked` or `spot-checked only`.

One verdict per tested source: build, park or drop, with a one-line reason and the basis. Never present an inherited verdict as a tested one. A wrong match is worse than a miss; keep uncertain matches in a separate "possible" class. Lead time means months before the award or press, never months before a compressor purchase.

The air district is validated here the first time a county in that district is run. Record its verdict in `STATE_FOUNDATION.md` under the district name so later counties in the district inherit it.

Save as `step3-validation/california/{county}/validation_{county}_notes.md` and `validation_{county}_matches.csv`.

## Step 3: Scrape (county build sources only)

Pull only this county's build-verdict sources. One agent per portal platform, in parallel where there are several, each following `datasource-validator-scraper`: access route, robots.txt and terms, sample, pull, QA.

Scope: sites in `{COUNTY}` County, records dated 2024-01-01 onward, plus still-active 2023 construction permits. Wide net: keep every row in scope and set `flag` to Y or N with the rule in `flag_rule`. Leave out only rows about private individuals.

One CSV per source with exactly these columns, in this order:

`source, source_level, record_id, record_date, date_type, record_type, company_name, company_role, site_address, city, county, zip, description, flag, flag_rule, source_url, retrieved_at`

- `source_level`: `County ({COUNTY}, CA)`; for the air district, `Regional (<district name>)`.
- `record_date` in ISO format; `date_type` says what it is (filed, received, opened, approved, published).
- `company_role`: applicant, permittee, contractor, tenant, owner, or unknown.
- `description` trimmed to 500 characters. Source-specific fields go in extra columns after `retrieved_at`. Blank where the source has nothing.

Flag rules: copy the tier A and tier B rules recorded in `step4-scrape/scrape_notes.md` and the Step 4b notes. Tier A is higher-value permits on industrial land, tier B the wider net below that, and every concept or site plan row is flagged. California zoning names differ by city, so record in the notes which zone codes were treated as industrial for each city. Report rows flagged per rule.

Browser-only portals (Accela and similar): no automated collection and no agent browsing. Terms check only; treat as a manual lookup source.

Save as `step4-scrape/california/{county}/scrape_{source}.csv`, `scrape_flagged_{county}.csv`, `scrape_notes_{county}.md` (assumptions, one card per source with route, row counts, rows flagged per rule, null rates on company name, address and date, date range, what broke, how to rerun), and scripts under `scripts/`.

## Step 4: Analysis

Use the v3 scripts with the state setting from the foundation. Do not rewrite the pipeline and do not change the points table: one table scores every county in both states.

County config `county_configs/ca_{county}.py`, copied from `_template.py`:

- **Scope.** County name, county FIPS (state FIPS is 06), and a zip-share file from the Census 2020 ZCTA-to-county file. Use the source's county field where it has one; otherwise zip share and the Census geocoder for zips that straddle the line.
- **Mailing cities.** `MAIL_CITIES` wholly inside the county, `SPLIT_CITIES` that straddle it. California mailing city names often differ from the legal city (unincorporated communities, postal names); mark those `mailing address, county unconfirmed` and keep them in a separate section.
- **County layers.** `LOCAL_LAYERS = True` with the city permit files in `LOCAL_PERMIT_FILES` and the planning files in `LOCAL_PLAN_FILES`. First-pass rule: build once without the county layers, once with them, and report both counts.
- **Local noise cuts.** Airports, ports, military bases, universities, large retail districts, film studios, and in some counties cannabis cultivation and oilfield services. Report rows removed per cut.
- **Person-named entities.** Registered entities named after a private individual are left out of ranked listings (Matthew's standing decision from Adams).
- **Entity merges and overrides.** Only ones backed by a document or an exact name plus address.
- **Seed list.** The incentive-seeded projects from Step 2 go in `GROUND_TRUTH`, labelled as seeds.

Run: zip share, build, verify, report, as in the scripts' README, writing to `step5-analysis/california/{county}/`.

The pressure vessel database is used here by hand only: for the top 25 ranked sites, look up the address and note how many air tanks are registered, their size and year built, in `next_step`. Skip this if DIR's terms were not cleared in the foundation.

Web lookups are allowed only to confirm what a specific top-ranked company makes or whether a site is in the county. Say which rows were checked.

**Check the result.** Report how many seed projects appear in the ranking and at what rank, and say that this is a weak check because the seeds also feed the scoring if incentives are scored. Read the top 25 by eye and report what share look like real plants or shops. Then have a separate review agent that has not seen the build audit the outputs against this skill and the raw data, including the loader's tiers on a sample (sub-permits, plan revisions, fire sprinklers, racking, generators, solar, EV chargers, demolitions and commercial-use buildings must not score as construction permits).

Save under `step5-analysis/california/{county}/`: `{county}_ranked_accounts.csv` (columns: `rank, company_name, name_variants, site_address, zip, county_basis, stage, score, sources_count, sources, first_signal_date, latest_signal_date, top_evidence, compressed_air_fit, match_confidence, in_ground_truth, next_step`), `{county}_evidence.csv`, `{county}_manual_lookup_list.csv` if a browser-only portal exists, and `{county}_analysis_notes.md` (assumptions and the points table at the top, then method, noise cuts with counts, the check, and what the data could not show).

## After analysis: dashboard and inventory page

1. **Dashboard.** Register the county with `python3 dashboard/register_county.py ...` (see its docstring) so it appears on the Streamlit site, labelled with the state so California and Colorado counties are distinguishable. Push.
2. **Inventory page.** Standing permission: update the "Compressed Air Source Inventory" artifact without asking. Write `step1-discovery/inventory_update_ca_{county}.csv`, read the whole page, add one object per county source to `const DATA=[...]` with the existing fields, and republish to the same link. On the first California run, also add the 31 state rows with level `State (California)` and their foundation verdicts, and make sure the level filter can separate the two states. Add only; never touch existing rows. Check the script parses and the counts add up, then look at the rendered page. If the page cannot be found or the publish is refused, leave the record file and tell Matthew.

## Stop and ask

Run everything through without waiting for approval between steps. Stop only for:

- The bizfile login question for UCC and business entity bulk data.
- Any signal mapping listed as needing Matthew in the foundation, before it scores points.
- A source's terms on automated access are ambiguous. Report what they say and offer options in a table.
- Using parcel owner names or any dataset carrying personal names.
- Any script edit after which Denver, Adams or Weld no longer rebuilds byte for byte.
- Re-pulling state sources.
- Anything that would be sent, submitted or deleted.

If Matthew is not there to answer, finish everything that does not depend on the decision, set the decision out, and stop.

## Ground rules

- Query the real data. Do not estimate from a source's description.
- Respect robots.txt and site terms. If a route is blocked, report it and stop. No workarounds through direct requests, caches, mirrors or third-party scrapers.
- Do not submit any records request, create any account, or contact any agency, vendor or company. Draft requests and hand them back. A records request from an Atlas Copco address is itself a public record.
- Do not use any Atlas Copco internal data.
- No personal data. No people's names, phone numbers, emails or home addresses in any output. Drop UCC rows where the debtor may be an individual. Contacts come later from ZoomInfo.
- Never fill a gap with a guess. Label every join as confirmed or possible.
- State every assumption at the top of the notes for that step.
- If budget runs out partway, say exactly which sources, date ranges or steps were not finished.
- Do not use em dashes in any output.

## What to tell Matthew at the end

Short, direct, numbers first, options in a table when there is a decision. No step-by-step recap.

- On the first run: which state sources earned a build verdict, which are parked on a decision of his, and whether Colorado still rebuilds identically.
- Local sources found, tested, build verdicts, and on what basis.
- Rows the county pull added and how many were flagged.
- Accounts ranked, and the top 10 with one line of evidence each.
- The check: seed projects found and at what rank, with the caveat that seeds are incentive-biased.
- That the dashboard and inventory page were updated.
- What the sources could not show.
- The three or four decisions he needs to make next.

## What to expect

- The first California county is several times the work of a Colorado county because it carries the state foundation. Say so up front and offer to split it: foundation in one session, county in the next.
- California lists will lean on incentives, stormwater enrolments, city permits and the air district. Until the UCC question is settled there is no machinery-lien signal, which was the strongest feed in Colorado. Say so in every report until it changes.
- No public source reliably beats the first press story for a brand-new plant. These sources fire between announcement and opening, and for expansions at existing plants that press never covers.
- Most rows in any county list are unconfirmed. Say how many are solid, not just how long the list is.
