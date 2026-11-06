# Shared brief for the Weld County scrape agents (step 3)

Read this file, then `/home/claude/atlasscraper/.claude/skills/datasource-validator-scraper/SKILL.md` (follow it: route, robots and terms, sample, build, QA), then the rows for your sources in `/home/claude/atlasscraper/step1-discovery/compressed_air_demand_sources_weld_county.csv` (endpoints and key fields) and the matching sections of the step 2 group notes in `/home/claude/atlasscraper/step3-validation/weld/` (`notes_county.md`, `notes_tri_towns.md`, `notes_cities.md`: they record the endpoints, field names, query quirks and noise filters that worked). The Adams source cards in `/home/claude/atlasscraper/step4-scrape/adams/scrape_notes_adams.md` show the shape of a finished card, and the Adams scripts under `/home/claude/atlasscraper/step4-scrape/adams/scripts/` show the resumable-pull pattern (cache raw pages, write the CSV from the cache).

## Scope

Sites in Weld County, Colorado. Records dated 2024-01-01 onward. Carry in 2023 construction permits that are still active (not finaled, not cancelled, not expired). The one exception is the county incentive agreements: pull every agreement from 2022-01-01 onward, because an agreement precedes the equipment purchase by years and the 2022 and 2023 agreements are still inside their phase windows. For the Longmont, Erie, Brighton, Thornton and Northglenn slices nothing is pulled in this step. Frederick, Greeley and Fort Lupton lie wholly in Weld. Windsor is a manual download source (Matthew's decision 2026-11-06): do not pull it.

## Wide net: tag, do not drop

Keep every row in scope that is not plainly residential. Set `flag` to Y or N with the rule that fired in `flag_rule`. The only rows to leave out are those about private individuals (a record whose applicant, owner, grantor or grantee field is a person's name: keep the row, blank the name, never write a person's name anywhere). Residential rows (single-family, duplex, townhome, residential roofing, fences, water heaters, HVAC replacements at homes, solar on homes, residential parcel sales) may be left out entirely, and the count left out must be reported.

Flag rules, carried from Denver and Adams (tier A is the higher-value industrial rows, tier B the wider net):

- **Permits (Frederick).** Tier A: valuation 250,000 dollars or more AND (industrial zoning or industrial land use or an industrial or manufacturing word in the description or building use), class new building, addition, tenant finish, alteration or change of use. Where the layer carries no valuation, tier A = non-residential new building, addition, tenant finish or change of use with an industrial, warehouse, manufacturing, plant, process, equipment, crane, tank, silo, compressor, dust collection, paint booth, boiler, generator, piping, lab or similar word in the description or building-use field. Tier B3a: 50,000 to 250,000 dollars on industrial or commercial-industrial property. Tier B3b: under 50,000 dollars (or no valuation) on industrial property, non-residential. Everything else in scope: flag N with `flag_rule` blank. Sub-permits (electrical, mechanical, plumbing, fire sprinkler, racking, signs, demolition, generators, trailers) keep their own `record_type` so the analysis loader can tell them from construction permits.
- **Planning, development and site-plan records (Weld planning cases, Weld SPR, Frederick development applications, Greeley TRAKiT projects, Fort Lupton planning).** Every row is flagged Y, rule `all planning and development cases`, and an extra column `industrial_use` = Y when the use, zoning or description says industrial, warehouse, manufacturing, distribution, flex, data center, processing, plant, compressor station or oil and gas facility (not a well pad).
- **Property sales (Weld assessor).** Flag Y when sale price is 2,000,000 dollars or more on a parcel whose occupancy code, land use or zoning is industrial or commercial-industrial; rule `sale 2M+ on industrial or commercial-industrial parcel`. Everything else in scope: N. Leave out residential-occupancy sales entirely and count them.
- **County incentive agreements (Laserfiche).** Every Tax Incentive Agreement row is flagged Y, rule `county tax incentive agreement`. Other commissioner records are not pulled.
- **Personal property accounts (Weld assessor ownership table).** This is a resolver snapshot, not a signal: flag N on every row, rule blank; keep only accounts whose business or owner name is a company (blank any individual).

Report how many rows each rule flags.

## Output columns

One CSV per source, exactly these 17 columns first, in this order:

`source, source_level, record_id, record_date, date_type, record_type, company_name, company_role, site_address, city, county, zip, description, flag, flag_rule, source_url, retrieved_at`

- `source`: a short source name (for example `Weld County incentive agreements`).
- `source_level`: `County (Weld)`.
- `record_date`: ISO `YYYY-MM-DD`; `date_type` says what the date is (filed, received, opened, applied, issued, recorded, hearing, sale, snapshot). A snapshot layer with no date of its own gets the retrieval date and `date_type` = `snapshot`.
- `company_name`: the applicant, tenant, project name, taxpayer or grantee as the record gives it; blank when the record has none; never an individual.
- `company_role`: applicant, permittee, contractor, tenant, owner, grantee, taxpayer, project, or unknown.
- `county`: `Weld`. `city`: the record's city, or the jurisdiction name when the record has none (`Unincorporated Weld County` for county layers with no city).
- `description`: trimmed to 500 characters; scrub planner names, emails and phone numbers.
- `source_url`: a URL that reaches the record or the layer query.
- `retrieved_at`: ISO timestamp of the pull.
- Source-specific fields (valuation, square footage, zoning, land use, permit type, status, latitude, longitude, parcel number, use, sale price, grantor, grantee, occupancy, acreage, document id, phase caps, and so on) go in extra columns after `retrieved_at`.
- Leave a field blank when the source does not carry it. No em dashes anywhere.

## Access rules

ArcGIS REST: documented `/query` endpoint, paged by OBJECTID or `resultOffset`, at most 2,000 rows a request, one request a second, user agent `step4-research-pull/1.0`. Frederick's server needs `DATE 'YYYY-MM-DD'` literals. Laserfiche WebLink: the JSON services step 2 used (session cookie from one GET, SearchService field search on the Commissioner Records template, DocumentService OCR text per page), read-only, one request a second, OCR every page of each agreement (the agreement is not always on page 2). Cache raw JSON and OCR text to `/home/claude/atlasscraper/step4-scrape/weld/raw/<source>/` (git-ignored; do not commit raw pages). Respect robots.txt. Do not pull anything behind a login, do not open browser-only portals (Accela Citizen Access, the Accela Public Portal, eTRAKiT, CommunityCore, Citizenserve). If a host refuses (403, Cloudflare, Akamai, HTTP 500 on a query shape), record it, change the query shape only in documented ways (date-range pulls, one clause per request), and stop on repeated errors. Download nothing beyond the scope.

No form submissions, no accounts, no records requests, no contact with anyone. No Atlas Copco data. No personal names, phone numbers or emails anywhere.

## Files to write

- `/home/claude/atlasscraper/step4-scrape/weld/scrape_<source_slug>.csv` per source.
- `/home/claude/atlasscraper/step4-scrape/weld/scripts/pull_<source_slug>.py` per source: standard-library Python, resumable (`--since YYYY-MM-DD` for an incremental pull, `--fresh` to ignore the cache), writes the CSV from the cache so a rerun does not refetch. Snapshot sources append rows never seen before and never delete.
- `/home/claude/atlasscraper/step4-scrape/weld/notes_<group>.md`: assumptions at the top, then one source card per source with: route and why cheaper routes did not apply, terms and robots findings (quote the Weld AGOL `licenseInfo` where it applies), row counts (written, source's own count, left out and why), rows flagged per rule, null rates on company_name, site_address and record_date, date range and any monthly gaps, duplicates, fields carried, join key, refresh command, gotchas, what was not pulled.

Write files with the Write tool, not shell heredocs. Do not commit to git.

QA before you report: every CSV starts with the exact 17 columns, `flag` is only Y or N, no description over 500 characters, no row dated before 2022-01-01 (2023-01-01 for everything but the agreements), no person's name in company_name (spot check 50 rows), row counts match the source's own count for the same filter.

Report back in under 300 words: per source, rows written, flagged by rule, null rates, date range, anything blocked, and the file paths.
