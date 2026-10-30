# Shared brief for the Adams County scrape agents (step 3)

Read this file, then `/home/claude/atlasscraper/.claude/skills/datasource-validator-scraper/SKILL.md` (follow it: route, robots and terms, sample, build, QA), then the rows for your sources in `/home/claude/atlasscraper/step1-discovery/compressed_air_demand_sources_adams_county.csv` (endpoints and key fields) and the matching sections of the step 2 group notes in `/home/claude/atlasscraper/step3-validation/adams/` (they record the field names that worked, the query quirks, and the noise filters that cut 90 percent of rows). Denver's source cards in `/home/claude/atlasscraper/step4-scrape/scrape_notes.md` (sections "Denver commercial construction permits" and "Denver concept and site plans") show the shape of a finished card.

## Scope

Sites in Adams County, Colorado. Records dated 2024-01-01 onward. Carry in 2023 construction permits that are still active (not finaled, not cancelled, not expired). For Aurora, Westminster and Arvada layers keep only the Adams County side (Aurora: County field = ADAMS on the development layer; the PropY > 1,695,150 Colfax-line cut on the permit layer, as the step 2 Aurora notes derived; say which you used). Commerce City and Thornton lie wholly in Adams (Thornton has a sliver in Weld; keep everything).

## Wide net: tag, do not drop

Keep every row in scope that is not plainly residential. Set `flag` to Y or N with the rule that fired in `flag_rule`. The only rows to leave out are those about private individuals (a permit whose applicant or owner field is a person's name: keep the row, blank the name, never write a person's name anywhere). Residential rows (single-family, duplex, townhome, residential roofing, fences, water heaters, HVAC replacements at homes, solar on homes) may be left out entirely, and the count left out must be reported.

Flag rules, carried from Denver (tier A is the higher-value industrial rows, tier B the wider net):

- **Permits.** Tier A: valuation 250,000 dollars or more AND (industrial zoning or industrial land use or an industrial or manufacturing word in the description or building use), class new building, addition, tenant finish, alteration or change of use. Where the layer carries no valuation (Adams County layer), tier A = non-residential new building, addition, tenant finish or change of use with an industrial, warehouse, manufacturing, plant, process, equipment, crane, tank, silo, compressor, dust collection, paint booth, boiler, generator or similar word in the description or building-use field. Tier B3a: 50,000 to 250,000 dollars on industrial or commercial-industrial property. Tier B3b: under 50,000 dollars (or no valuation) on industrial property, non-residential. Everything else in scope: flag N with `flag_rule` blank.
- **Planning, development and site-plan records.** Every row is flagged Y, rule `all planning and development cases`, and an extra column `industrial_use` = Y when the use, zoning or description says industrial, warehouse, manufacturing, distribution, flex or data center.
- **Property sales.** Flag Y when sale price is 2,000,000 dollars or more on a parcel whose land use or zoning is industrial or commercial-industrial (join to the Parcels layer for land use); rule `sale 2M+ on industrial or commercial-industrial parcel`. Everything else in scope: N.
- **Meeting items (PrimeGov, Legistar).** Flag Y when the title matches an incentive, agreement, rezoning, planned development, use by special review, site plan or plat for a non-residential project; rule names the word. N otherwise.

Report how many rows each rule flags.

## Output columns

One CSV per source, exactly these 17 columns first, in this order:

`source, source_level, record_id, record_date, date_type, record_type, company_name, company_role, site_address, city, county, zip, description, flag, flag_rule, source_url, retrieved_at`

- `source`: a short source name (for example `Adams County building permits`).
- `source_level`: `County (Adams)`.
- `record_date`: ISO `YYYY-MM-DD`; `date_type` says what the date is (filed, received, opened, applied, issued, entered, sale, agenda).
- `company_name`: the applicant, tenant, project name or grantee as the record gives it; blank when the record has none; never an individual.
- `company_role`: applicant, permittee, contractor, tenant, owner, grantee, project, or unknown.
- `county`: `Adams`. `city`: the record's city, or the jurisdiction name when the record has none.
- `description`: trimmed to 500 characters.
- `source_url`: a URL that reaches the record or the layer query.
- `retrieved_at`: ISO timestamp of the pull.
- Source-specific fields (valuation, square footage, zoning, land use, permit type, status, latitude, longitude, parcel number, use, sale price, grantor, grantee, folder name, and so on) go in extra columns after `retrieved_at`.
- Leave a field blank when the source does not carry it. No em dashes anywhere.

## Access rules

ArcGIS REST: documented `/query` endpoint, paged by OBJECTID or `resultOffset`, at most 2,000 rows a request, one request a second, user agent `step4-research-pull/1.0`. Cache raw JSON pages to `/home/claude/atlasscraper/step4-scrape/adams/raw/<source>/` (git-ignored; do not commit raw pages). Legistar and PrimeGov: their JSON APIs, read-only. Respect robots.txt. Do not pull anything behind a login, do not open browser-only portals (eTRAKiT, Accela, CityView, AMANDA, OpenGov, CommunityCore, Landmark Web). If a host refuses (403, Cloudflare, HTTP 500 on a query shape), record it, change the query shape only in documented ways (date-range pulls, one clause per request), and stop on repeated errors. Download nothing beyond the scope.

No form submissions, no accounts, no records requests, no contact with anyone. No Atlas Copco data. No personal names, phone numbers or emails anywhere.

## Files to write

- `/home/claude/atlasscraper/step4-scrape/adams/scrape_<source_slug>.csv` per source.
- `/home/claude/atlasscraper/step4-scrape/adams/scripts/pull_<source_slug>.py` per source: standard-library Python, resumable (`--since YYYY-MM-DD` for an incremental pull, `--fresh` to ignore the cache), writes the CSV from the cache so a rerun does not refetch.
- `/home/claude/atlasscraper/step4-scrape/adams/notes_<group>.md`: assumptions at the top, then one source card per source with: route and why cheaper routes did not apply, terms and robots findings, row counts (written, source's own count, left out and why), rows flagged per rule, null rates on company_name, site_address and record_date, date range and any monthly gaps, duplicates, fields carried, join key, refresh command, gotchas, what was not pulled.

QA before you report: every CSV starts with the exact 17 columns, `flag` is only Y or N, no description over 500 characters, no row dated before 2023-01-01, no person's name in company_name (spot check 50 rows), row counts match the source's own count for the same filter.

Report back in under 300 words: per source, rows written, flagged by rule, null rates, date range, anything blocked, and the file paths.
