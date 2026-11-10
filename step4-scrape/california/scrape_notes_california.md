# California state pulls: notes

Run 2026-11-10. Part of the state foundation in the `california-county-runner` skill. Status and open items are in `STATE_FOUNDATION.md`.

## Assumptions

- Scope: records dated 2024-01-01 onward. ABC is a snapshot with no application date.
- Wide net: every in-scope row kept and tagged. Contact, certifier and planner name fields in the sources are never carried into the outputs.
- A company name is blanked as a possible private individual only when it has two or three words, no business word, and starts with a common first name. This is a rough filter: 79 names blanked in the industrial stormwater file, 141 owners in the construction file, 1 in ABC. Person-named businesses can still be present; the analysis step must apply the person-named rule again.
- Flag rules here are first-pass rules written for California. They follow the Colorado tier A idea (manufacturing SIC, industrial construction, named awards) but have not been compared row by row with the Colorado rules.

## Access notes

- data.ca.gov: robots.txt disallows `/api/`. The files are fetched from their direct download links (which redirect to signed storage URLs; use `curl -L`). One metadata call to the CKAN API was made before robots.txt was read; do not repeat it. Take the file links from the dataset web page.
- California Competes awardee table: fetched from the `admin-ajax.php` endpoint that the public page itself calls. robots.txt allows that path. The request needs the nonce printed in the page, so load the page first.
- CEQAnet: `Search?County=<name>&StartRange=&EndRange=&OutputFormat=CSV`. robots.txt allows it. File is Windows-1252 encoded.
- ETP: robots.txt sets a 10-second crawl delay. Not pulled yet.

## Source cards

| Source | File | Rows | Flagged | Date range | Company name blank | Address blank |
|---|---|---|---|---|---|---|
| SMARTS industrial stormwater | scrape_smarts_industrial.csv | 5,811 | 3,513 | 2024-01 to 2026-10 | 81 | 3 |
| SMARTS construction stormwater | scrape_smarts_construction.csv | 12,681 | 825 | 2024-01-03 to 2026-10-30 | 150 | 16 |
| California Competes awards | scrape_calcompetes_awards.csv | 58 | 47 | 2024-04-25 to 2026-06-18 | 0 | 58 (city only) |
| CAEATFA STE awards | scrape_caeatfa_ste_awards.csv | 65 | 65 | 2024-07-16 to 2025-12-09 | 0 | 65 |
| ABC manufacturer licences | scrape_abc_manufacturer_licences.csv | 3,905 | 2,440 | issued 2024-01-02 to 2026-11-05; applications undated | 0 | 7 |

Exact counts per flag rule are in `pull_summary.json`.

What each one turned out to hold:

- **SMARTS industrial.** 38 columns including operator, facility address, latitude and longitude, primary SIC code, status and NOI processed date. Statewide, 1,029 new manufacturing-SIC enrolments and 2,484 new manufacturing-SIC No Exposure Certifications since 2024. This settles the open question from discovery: the file is exactly the new-industrial-site feed it was expected to be.
- **SMARTS construction.** 80 columns including owner, developer, site address, disturbed acreage, planned start and completion dates, and yes/no columns for residential, commercial and industrial. 825 enrolments marked industrial since 2024.
- **California Competes.** The awardee table holds all 1,244 awards since 2014 with company, cities, industry, net new employees, investment, credit, approval date and a link to the agreement. Only 58 fall in 2024 to mid-2026. The 2026-12-02 agenda items are not in it yet.
- **CAEATFA.** The workbook has street addresses only for older awards. All 65 awards approved since 2024 have a blank address, so these resolve to city and county only. The workbook stops at 2025-12-09: the 15 applications on the 2026-09-15 agenda are missing and need the agenda PDF parsed.
- **ABC.** The export has no application date, so a pending application can only be dated by diffing daily snapshots or reading the daily new-applications reports. 539 pending manufacturer applications statewide. 1,464 application records have status active rather than pending; what that means was not confirmed, so they are kept and not flagged.

## How to rerun

1. Download the two SMARTS facility CSVs, `DailyExport-CSV.zip`, `salesandtax.xlsx` and the awardee table JSON into one folder under the names listed in `scripts/pull_ca_state.py`.
2. `python3 scripts/pull_ca_state.py <raw folder> step4-scrape/california` (needs `openpyxl` for the workbook; everything else is standard library).

## Foundation status

See `STATE_FOUNDATION.md` (written 2026-11-10 after the v3 adapter was built and the three Colorado counties were confirmed unchanged).
