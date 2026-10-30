# Shared brief for the Adams County validation agents (step 2, back-test)

Read this whole file, then the discovery CSV rows for your sources:
`/home/claude/atlasscraper/step1-discovery/compressed_air_demand_sources_adams_county.csv` (28 columns, incl. `url`, `key_fields`, `verification_notes`, `recommended_next_step`) and section 8 of `..._adams_county_notes.md`.

## Purpose

Decide which Adams County local sources are worth pulling, by testing them against known projects. Adams County has 17 known projects in the ground truth (plus 4 whose county is Adams or a neighbour), so the method is a **back-test**, as in Denver's step 3 (batch 1 and 2 notes in the Claude project; their rules are summarised here).

## Ground truth

`/home/claude/atlasscraper/step3-validation/adams/ground_truth_adams_extract.csv`: one row per project with `project_id`, company, address, city, `earliest_press_date`, `earliest_press_basis`, other dated milestones, cautions. The earliest press date is the earliest rumor, press mention or announcement that is not labelled UNVERIFIED; rows marked FALLBACK use a weaker date (say so when you use them). X11 AMP has no usable press date. The four "possible Adams only" rows (X02, X03, X09, X23) are tested but reported separately.

## Rules carried from Denver

1. **Match classes.** `confirmed` = the entity or the site is tied by something exact: company name plus site address, exact address plus suite, or a document naming both. `possible` = right company but another address, a generic record at the address with no name, a differing legal name with no document tying it, or a near-miss address. `none` = searched, nothing. A wrong match is worse than a miss: when unsure, use `possible`.
2. **Record date** = the record's own date (filed, applied, opened, received), not when it became visible. Say which date field you used.
3. **Lead time** = (record date minus earliest press date) in days / 30.44, in months. Negative = source fired first. Lead time means months before or after the first press story. It does NOT mean months before a compressor purchase, and no write-up may say that.
4. **Window.** A record counts if dated from 36 months before press to 12 months after the project's latest milestone. Older or later records go in notes, not in the count. For an expansion at a plant that already existed, an in-window record is `possible` at most unless it names the project.
5. **Noise sample.** For each build-candidate source, count records opened in one or two sample months (use September 2025 and March 2026), and estimate the share that are plainly not industrial (housing, roofing, signs, retail, schools, roads). Query the real layer; do not estimate from a description.
6. **Join quality.** Say which field did the matching (address, applicant name, description text, parcel) and whether the layer carries any company name at all.
7. **Verdicts:** `build`, `park` or `drop`, one line of reason each, and a `basis` label: `back-tested`. Paid sources, press feeds, undated snapshots, context data and browser-only portals are NOT tested: list them as "not tested" with the reason.
8. **Browser-only portals (Accela, eTRAKiT, CityView, AMANDA, Landmark).** No automated collection and no agent browsing of them. Do the terms check only (robots.txt, any terms or disclaimer page) and report what the terms say in a few lines. Treat them as manual lookup sources.

## How to query

ArcGIS REST layers: use the documented `/query` endpoint with `where`, `outFields=*`, `f=json`, `resultRecordCount` and `resultOffset` paging, at most 2,000 rows a request, one request a second, user agent `step3-research-validation/1.0`. Prefer `returnCountOnly=true` for counts. Use python3 `urllib` or `curl` from the shell; the hosts were reachable at discovery. If a host refuses (403, Cloudflare), record that and stop; never work around it. Search by street number plus street name (addresses are inconsistently formatted: try `LIKE '%9410%HEINZ%'` style patterns on every address field and on description or applicant fields), and by company name words on any name, applicant, owner or description field. Legistar and PrimeGov have JSON APIs (see the discovery notes); use them read-only. Download nothing in bulk beyond what the test needs.

## Boundaries

No form submissions, no accounts, no records requests, no contact with anyone. No personal names in any output (applicant fields can hold individuals: write "individual" instead). No Atlas Copco data. No em dashes anywhere in the output. Query the real data; never fill a gap with a guess.

## Output

Write two files for your group, replacing `<group>` with your group name:

1. `/home/claude/atlasscraper/step3-validation/adams/matches_<group>.csv` with exactly these columns:
   `project_id, company_short, source_name, source_rank, match_class, record_id, record_date, date_field, matched_on, record_summary, press_date, press_date_basis, lead_months, in_window, notes`
   One row per project per source tested (including `none` rows). Several records for one project: one row per record that matters, the earliest first.
2. `/home/claude/atlasscraper/step3-validation/adams/notes_<group>.md` with: the sources tested and their endpoints; the assumptions you made; one section per source with coverage (confirmed, possible, of N), lead-time list, noise sample counts, join quality, access notes, and the verdict line `**Verdict: build|park|drop** (back-tested). reason`; sources not tested and why; terms findings for the browser-only portals in your group; corrections the test suggests to the ground truth (do not apply them); what was not finished.

Report back in under 300 words: verdict per source with coverage and before-press count, anything blocked, and the two file paths.
