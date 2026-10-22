# Step 5 (v2): Denver ranking, full rebuild

Written 2026-10-11. Run this in a fresh chat inside the "Atlas Lead Pipeline New" project, with Matthew's computer linked and the folder `Agent Analysit Flow` connected.

## Where things stand

- Step 4 scraped eight Colorado sources. Step 4b added a second, wider flag tier (tier B) to three of them.
- Step 5 has been run twice: once on tier A only (359 rows), then an incremental re-run that layered tier B on top (743 rows). The second run read the first run's points back from text because the first run's scripts were never saved. This run replaces both with one clean build.
- Read these first, in this order:
  1. `step5-analysis\analysis_notes.md`: the method, noise cuts, points table and fit rules. This is the specification.
  2. `step5-analysis\analysis_notes_v2.md`: what tier B changed, the decisions made, the cautions.
  3. `step4-scrape\reflag_notes.md`: the tier B rules and their precision.
  4. `step4-scrape\scrape_notes.md`: source cards and gotchas.

## Where the data is

The project is full. Work from the folder on Matthew's computer:

`C:\Users\spink\OneDrive\Desktop\Personal Projects\Agent Analysit Flow\`

- `step4-scrape\scrape_flagged_v2.csv`: 9,864 flagged rows from all eight sources, with `flag_tier` (A or B) and `flag_rule_v2`. Start here.
- `step4-scrape\scrape_ucc_filings\scrape_ucc_filings_v2.csv`, `step4-scrape\scrape_business_registrations\scrape_business_registrations_v2.csv`, `step4-scrape\scrape_denver_commercial_permits_v2.csv`: full files with `flag_v2`, `flag_tier`, `flag_rule_v2`.
- The other five source files in `step4-scrape\` are unchanged (tier A only).
- `step4-scrape\scrape_ucc_filings\ucc_b1a_fulltext_hits.csv`: snippets for equipment words found past the 500-character cut.
- `step5-analysis\scripts\`: `rerank_step5b.py` (the incremental re-run), `denver_zip_share.json` (share of each zip inside Denver County), `geocode_cache.json` (55 addresses already checked). Reuse the zip file and the cache.
- `step5-analysis\denver_ranked_accounts.csv` and `denver_ranked_accounts_v2.csv`: the two earlier rankings. Use them only for the comparison at the end.

The shell on the computer can run Python and reach the Census geocoder. A single command is limited to about three minutes and background jobs do not survive, so make long steps resumable.

## The job

Rebuild the Denver County ranking from the Step 4 files in one pass, scoring tier A and tier B rows together under the rules below. Save the scripts. Do not re-scrape and do not change any flag.

## Scope, resolution and noise cuts

Follow `analysis_notes.md` as written: the Denver scope test (county field, AIRS prefix 031, zip share, then the Census geocoder for split zips), name and address normalisation, the confirmed and possible join classes, the reach into the full files, and every noise cut in its table. Report the count each cut removes, as before.

Carry these forward from the tier B run:

- A flagged company at an unattached address is a possible occupier at half points. It is not promoted to the account.
- A permit at an unattached address scores in full. Joined to a named company by street address it is possible and scores half, unless the suite matches.
- Tier B never applies to a UCC debtor with no business word in its name.
- The Step 5 cut for flagged permits whose parcel class is not industrial applies to tier A permits only. Tier B permits flagged on industrial zoning stay in, with fit set by parcel class.

## Points table (fixed; do not retune)

Possible matches score half. Within one source only the best signal counts, plus 3 points for each further month with a signal of 12 or more in that source (maximum 9).

| Signal | Points |
|---|---|
| UCC filing naming an air compressor or compressed-air system (tier A) | 30 |
| UCC filing with a tier B process-equipment word (B1a) | 30 |
| UCC filing naming production machinery (tier A) | 25 |
| Air permit application, modification or approval for process units | 25 |
| Denver permit, new building or addition, industrial property, $250k or more (+3 if $1M or more) | 22 |
| Construction stormwater permit with a manufacturing SIC or company-named facility | 20 |
| Denver permit, alteration or tenant finish, industrial property, $250k or more (+3 if $1M or more) | 18 |
| Denver permit, $50k to $250k, industrial property (B3a) | 12 |
| Air permit APEN-only or exempt; new industrial stormwater or no-exposure certification; concept or site plan on I-A or I-B zoning | 12 |
| UCC flagged word without production machinery; towable compressor; press story naming the company | 8 |
| Vague lien held by an equipment lender (B1b); blanket lien on a maker (B1c) | 8 |
| Flagged tier A registration; concept or site plan on industrial mixed-use zoning; Denver permit under $50k on industrial property (B3b); unflagged permit at the company's address | 6 |
| Press story naming only the address; OEDIT code-name approval | 5 |
| Generic or blanket UCC lien; other site plan at the address | 4 |
| Tier B registration (B2a); unflagged registration | 3 |
| Air or water row cut as noise | 2 |

- **Independent sources:** +8 for each source beyond the first with a signal of 5 or more (maximum 24); +3 for each source with support only (maximum 6).
- **Recency** (latest row worth 4 points or more, run date 2026-10-11): +15 within 12 months, +8 within 24 months.
- **Stage:** buying equipment +12; fit-out +12; under construction +8; operating and expanding +8; planned +4; unknown 0. **A permit under $50k adds at most 4 stage points, whatever its status.**
- **Compressed-air fit:** strong +15; moderate +6; unknown 0; weak -15. Use the fit rules and their order from both notes files.

Stage and fit rules are in `analysis_notes.md`. Print each row's own points breakdown at the end of `top_evidence`, as before.

## Fix while rebuilding

- Merge name variants of one company at one address (for example "Mountain Packaging LLC" and "Mountain Packaging Est. 2007").
- A blanket lien filed through an agent (CHTD, CSC, CT Corporation, Financial Agent Services) hides the lender. Keep the 8 points but mark the row "lender not named" in the evidence text.
- Keep the web checks from the first run as they are (the list is in `analysis_notes.md`). Add checks only for named companies in the new top 50 that have none. Say which.

## Check against the ground truth

17 Denver projects, list and aliases in `analysis_notes.md` and `step3-validation/ground_truth_projects.csv`. Report rank for each, split into matched by name and matched by address only. The earlier results were 2 of 17 (tier A) and 7 of 17 (with tier B: 4 by name or already in, 3 by address only). Do not tune to the 17. If anything is adjusted after seeing the result, say so.

## Accela

Out of scope for this run. Do not produce a lookup list, do not browse the site, and do not write "look this up in Accela" as a next step. For an unattached address the next step is "tenant not identified".

## Ground rules (carried over)

- No Atlas Copco internal data. No contact with any agency, vendor or company. No records requests.
- No people's names, phone numbers, emails or home addresses in any output. Keep the home-address rule: show a street address only when it has a suite or unit, appears in a site-based source, or is shared by two or more businesses.
- Web lookups only to confirm what a top-ranked company makes or which county an address is in.
- Label every join confirmed or possible. Never fill a gap with a guess.
- State every assumption at the top of the notes. If something cannot be finished, say exactly what.
- Do not use em dashes.

## Deliverables

Save to `step5-analysis\v3\` on the computer:

- `denver_ranked_accounts_v3.csv`: the Step 5 columns plus `tier` (A, B, or A+B), `rank_step5` and `rank_step5b` for comparison.
- `denver_evidence_v3.csv`: every source row behind every ranked row, shared 17 columns plus `rank`, `company_key`, `match_class`, `flag_tier`, `flag_rule_v2`, `points`.
- `analysis_notes_v3.md`: assumptions and the points table first, then the cut counts, the result, the ground-truth check, a sensitivity check (recency doubled and removed, source bonus doubled and removed, tier B points halved and doubled), what the data could not show, and how to re-run for another county.
- `scripts\`: every script, runnable end to end from the Step 4 files with one documented command.

In the chat, report in plain language: how many rows were ranked, the top 15 with one line of evidence each, every row whose rank moved more than 10 places against the tier B run and why, the 17-project result, and the decisions Matthew needs to make next.
