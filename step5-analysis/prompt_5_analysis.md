# Step 5: analysis, Denver County first

Written 2026-10-10 as a handoff from the Step 4 scrape chat. Run this in a fresh chat inside the "Atlas Lead Pipeline New" project, with Matthew's computer linked and the folder `Agent Analysit Flow` connected.

## Where things stand

- Step 4 pulled eight sources into one shared format: 773,565 rows, 8,199 flagged.
- Read these first: `step4-scrape/scrape_notes.md` (assumptions, source cards, decisions at the end), then the "Bottom line" sections of `step3-validation/backtest_batch1_notes.md` and `backtest_batch2_notes.md`.
- Main finding to keep in mind: no public source reliably beats the first press story for a new plant. These sources fire between announcement and opening, and for expansions at existing plants that press never covers. That window is still ahead of the compressor purchase.

## Where the data is

The project is nearly full. Work from the folder on Matthew's computer, not the project:

`C:\Users\spink\OneDrive\Desktop\Personal Projects\Agent Analysit Flow\step4-scrape\`

- `scrape_flagged.csv`: the 8,199 flagged rows in the shared 17 columns. Start here.
- One `scrape_<source>.csv` per source, with every row and that source's extra columns. The UCC and business registration files are in subfolders named after the files (173 MB and 184 MB). Ignore any `scrape_ucc_filings.csv` at the top level of the folder: it is a broken partial copy.
- `scripts\`: the pull scripts.

Stage the files into the cloud workspace and compute there with code. Do not page rows through the conversation.

## The job

Produce a ranked list of companies in Denver County with growing compressed-air demand, with the evidence behind each one. This is the first run of the analysis step. Denver comes first because it is the only county where all tiers overlap: six statewide sources plus two Denver sources. If the method works here, statewide is a re-run with a wider filter.

## Denver scope

- In scope: records whose site is in Denver County.
- Use `county` where the source carries it. Where it does not (UCC, business registrations), use the zip code against a Denver County zip list, and say which list you used.
- Step 3 found sites with Denver mailing addresses that sit in Adams, Arapahoe or Jefferson County. Mark those `county_basis = Denver mailing address, county unconfirmed`. Keep them in a separate section of the ranking. Do not drop them and do not guess.
- APCD: the county is wrong on 46 rows (company office in place of the site). The AIRS ID prefix 031 is Denver.
- Foreign business registrations rarely show a Colorado address. Keep those with no Colorado address out of the Denver ranking, but use them for name matching.

## How to work

1. **Resolve records to companies.** There is no shared ID. Normalise names (case, punctuation, Inc/LLC/Corp, "The") and addresses (street types, suite numbers, directionals). Keep the raw value next to the normalised one. Record every name variant and the legal entity names found.
2. **Attach address-only records.** Denver permits and site plans carry an address and sometimes a contractor, no tenant. Join them by address to UCC debtors, business registrations, water permits, APCD facilities and Mile High CRE. A contractor is not the account. Where no company can be attached, keep the address as its own candidate and say so.
3. **Reach into the full files.** Once a company or address is a candidate, pull all of its rows from every source, flagged or not. A blanket "all assets" UCC lien or an unflagged small permit still counts as supporting evidence for a company found elsewhere.
4. **OEDIT code names.** Do not decode from memory or guess. A match on county, industry and timing to a new registration or permit is "possible" at most, and must be labelled.
5. **Cut the known noise** (list below), and report how many rows each cut removed.
6. **Score and rank.** See below.
7. **Check against the ground truth.** See below.

## Known noise to cut or down-weight

- Denver permits in the DIA neighborhood (terminal and concourse tenant work): 194 of 509 flagged.
- Denver permits with zero valuation, and the last 90 days of the permit layer (issued permits only, so recent months are undercounted).
- UCC: SBA continuation filings (about 12,300 in May to July 2025), forklifts (Doosan), paving rollers ("pneumatic"), dry-cleaner boilers, "bottling" in a debtor's own name.
- UCC rows with `debtor_name_has_entity_token` = N: drop them. They may be individuals.
- Business registrations: about 1,000 bulk filings through one registered agent in February 2026.
- Water permits: wastewater plants, hauling and detention facilities caught by "Facility" or "Plant"; renewals (received date more than a year after issue date).
- OEDIT rows from minutes (`source_kind` = minutes): mostly non-industrial.
- Mile High CRE: extracted company names are mostly developers, brokers and contractors, not occupiers. Treat a CRE row as an address and a headline until the occupier is confirmed.

## Scoring

Keep it simple and readable. A points table, not a model. Matthew must be able to see why a company ranks where it does.

- **Signal strength.** Strongest: named production equipment in a UCC filing (a compressor most of all), an air permit for new emission units, a construction or site plan record for a production building. Weaker: a registration, a generic lien, a press mention.
- **Independent sources.** A company seen in three sources outranks one seen three times in one source.
- **Recency.** Weight the last 12 months most. Show the first and latest signal dates.
- **Stage.** Place each company on the timeline: planned, under construction, fit-out, buying equipment, operating and expanding. Fit-out and buying equipment are the best time to call.
- **Compressed-air fit.** Manufacturing, food and beverage, breweries and distilleries, metal and plastics, aerospace, electronics, pharma, wood products, auto body and similar score up. Offices, retail, housing and pure warehousing score down. Say what the fit judgment rests on.

State the points table at the top of the notes. Report how sensitive the top 25 is to it (which names change if recency or source count is weighted differently).

## Check against the ground truth

`step3-validation/ground_truth_projects.csv` holds 70 Colorado projects, 17 in Denver County (scope defined in the batch 1 notes). Report how many of the 17 appear in the ranking, at what rank, and why the misses were missed. The Step 3 corrections to the ground truth have not been applied, so list any that affect this check. Do not tune the scoring to the 17 and then report that as accuracy. If you adjust the scoring after seeing the result, say so.

## Accela (Denver trade permits)

Decision made: no automated collection and no agent browsing of the Accela site. In this run, only produce `accela_lookup_list.csv`: up to 25 addresses or company names where a hand lookup by Matthew would settle who the tenant is or whether trade work has started. One line each on what the lookup would settle.

## Ground rules (carried over)

- Work from the scraped files. Do not re-scrape. If a file looks wrong, report it.
- Do not use any Atlas Copco internal data.
- No contacts and no personal data. No people's names, phone numbers, emails or home addresses in any output. Contacts come later from ZoomInfo.
- Do not submit any records request or contact any agency, vendor or company.
- Never fill a gap with a guess. Label every join as confirmed (exact name plus address, or a document tying them) or possible.
- Web lookups are allowed only to confirm what a specific top-ranked company makes or whether a site is in Denver County. Respect robots.txt and site terms. Say which rows were checked this way.
- State any assumption at the top of the notes.
- Do not use em dashes.

## Deliverables

Save to the folder on Matthew's computer under `step5-analysis\` (beside `step4-scrape`):

- `denver_ranked_accounts.csv`: one row per company or unattached address. Columns: `rank, company_name, name_variants, site_address, zip, county_basis, stage, score, sources_count, sources, first_signal_date, latest_signal_date, top_evidence, compressed_air_fit, match_confidence, in_ground_truth, next_step`.
- `denver_evidence.csv`: every source row behind every ranked company, in the shared 17 columns plus `rank`, `company_key` and `match_class` (confirmed or possible).
- `accela_lookup_list.csv`.
- `analysis_notes.md`: assumptions and the points table at the top, then method, noise cuts with counts, the ground-truth check, the sensitivity check, what the data could not show, and how to re-run statewide.

Then save `analysis_notes.md` and `denver_ranked_accounts.csv` to the project under `step5-analysis/` if they fit. If the project refuses the write, say so and leave them in the folder.

In the chat, report in plain language: how many companies were ranked, the top 10 with one line of evidence each, how many of the 17 ground-truth projects surfaced, what the sources could not tell you, and the three or four things Matthew needs to decide next.

## Known issues to carry forward

- The water permit snapshot is dated 2026-08-07. Nothing later exists.
- The APCD feed holds about six months. A monthly snapshot is scheduled from November 1.
- Denver permit and site plan layers have no description, project name or applicant.
- Business registrations show the current principal office, not the address at registration, and carry no dissolution date.
- OEDIT descriptions are paraphrased, not verbatim. One project can appear under two code names. Do not sum jobs across them.
- Parcel owner names were not retrieved. They could put an owner on most Denver permit rows if Matthew wants that, with individuals filtered out.
