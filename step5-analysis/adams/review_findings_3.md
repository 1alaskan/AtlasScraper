# Review 3: cold spot check of the third Adams build (2026-10-31)

Scope: `adams_ranked_accounts.csv` (1,085 rows), `adams_evidence.csv` (5,938 rows), `adams_analysis_notes.md`, `v3_report.json`, joined to the raw Aurora, Thornton and Adams County permit files. Report only; nothing was changed.

## Verdict

The numbers in the notes agree with `v3_report.json` and with the files, the top-10 evidence lines trace to real evidence rows, and the people and em-dash rules hold. Two loader holds do not do what assumption 2 says they do, and neither one is fixed by this build:

1. Aurora intake and permit twins are only unflagged when the later record has a later date, and the raw scope_key keeps the intake's "SCOPE OF WORK INCLUDES" suffix. Same-day twins (55 scopes) and suffixed twins both pass: with the suffix stripped, 221 scopes carry a tier on two or more parent records, 50 of them tier A, 81 in the top 100 (rank 9, Medline, has two such pairs at 21 points each). Score effect is limited because only the best signal per source counts, but the repeat-month bonus and the "one scope counted once" claim in the notes are affected.
2. On the Adams County layer, "Other / Addition" passes the construction test through the word "addition" in the type-of-work field, so 8 equipment and electrical permits with no building word in the description score as tier A construction (22 points), one of them residential-prefixed (rank 171, "RES - UPGRADE THE GAS PRESSURE").

Both are worth a fourth pass of the loader before the list is used; they do not change ranks 1 to 8.

## Check 1: loader tiers

County permit evidence rows at tier A: 465 (Aurora 283, Adams County 125, Thornton 57).

- Aurora sub-permits (record_id not ending -000-00) at tier A: **0**. Hold works.
- Rows whose record_type, flag_rule_v2 or description (first 150 chars) match the small-work words: **7**. Four are false positives of the word test (a tenant improvement with a mezzanine and an exterior generator at rank 16; a TI that removes an interior fence at rank 172; "temp generator" and "generator" mentioned in passing at ranks 24 and 347). Three are real misses:
  - rank 289, PRCALT202501175, Thornton Commercial Alteration: "Interior-only alterations to an existing mercantile space in a shopping mall ... sports apparel and retail". Tier A at 18 points via the word "racking"; the commercial-use hold only reads the type fields, not the description.
  - rank 35, PREL202508588, Thornton Electrical: service and meter replacement, scored as a tier A alteration.
  - rank 120, PRCALT202603232, Thornton Commercial Alteration: replacing 7 air handling units, tier A.
- Adams County rows (BDP) at tier A with no building word in the description: **8**. All carry record_type "Other / Addition", "Core & Shell / Addition" or "Warehouse / Alteration" and flag_rule_v2 "tier A: non-residential construction with industrial word, no valuation in layer":
  - rank 51, BDP26-0173: vapor recovery unit at a compressor station (22 pts)
  - rank 85, BDP24-2945: overhead fans and outlets (22)
  - rank 171, BDP24-3805: "RES - UPGRADE THE GAS PRESSURE" (22)
  - rank 212, BDP25-3580: electrical for a 400HP electric compressor (22)
  - rank 244, BDP26-0102: Verizon communication tower (22)
  - rank 337, BDP25-1970: 125A subpanel and freezer cases (22)
  - rank 464, BDP24-2769: foundation for equipment (22)
  - rank 521, BDP26-1095: replacing shelving (9, possible match)
- Aurora parent records sharing a scope_key that both carry a tier (joined to the raw file by record_id; 3,248 parent evidence rows, 0 missing from the raw file): **55 scopes**, expected 0. All 55 are same-day pairs or triples; the loader's test is `record_date > first[scope]`, which never fires on them. 54 scopes are tier B pairs (B3b, 6 points each; three of them at rank 1, Kairus); 1 is tier A (rank 9, 25-2520588-000-00 and 25-2520783-000-00, both "MEDLINE AURORA AUTOSTORE TI", $3,780,000, 21 points each).
  The raw scope_key also misses twins whose intake record carries a "SCOPE OF WORK INCLUDES ..." suffix in the description (rank 9 again: 25-2538293-000-00 of 2025-06-20 and 25-2539278-000-00 of 2025-06-24, same $3,211,635, both 21 points). Stripping that suffix before comparing gives **221 scopes** with two or more tiered parent records, 50 of them with a tier A record, 81 in the top 100. The "counted once" hold therefore barely fires at all; the Step 3 scope_key is the cause, but the loader is the place to normalise it.

## Check 2: numbers in the notes

All of these agree with `v3_report.json` and recount from the files:

- 1,085 total; 1,064 Adams section; 232 companies, 832 addresses (file: 829 rows labelled "Unattached address" plus 3 Step 2 occupier rows, which the report counts as addresses); 13 county unconfirmed; 8 OEDIT code names (ranks 1078 to 1085).
- 174 of the 1,064 score 50 or more.
- Sources 711 / 258 / 73 / 22: the file has 711 / 258 / 73 / 18 / 4, so "22 on four" is 18 on four plus 4 on five (the report bins at 4). Wording, not a count error.
- Fit 162 / 11 / 850 / 41: matches (prefix of the fit text).
- Stage 456 / 213 / 164 / 136 / 17 / 78: matches (stage text without the parenthesis).
- Tier 357 / 545 / 183 and top 100 with tier A 96: match the report. They cannot be recounted from the evidence file's flag_tier column (that gives 341 / 545 / 242 and 97), because the evidence file also writes a tier on unflagged support rows that carry the raw flag Y, while the report counts flagged signals only. Definition, not an error, but worth one sentence in the notes.
- Geocoder: 163 addresses; 50 Adams, 62 Denver, 17 no match. Matches.
- 14 FRS names: `adams_frs_names.csv` has 14 rows and every registry name appears in that rank's next_step.
- 36 occupiers from permit rows: `resolve_counts.address_named_from_county_permit_rows` = 36. The ranked file does not separate these from the 142 "company possible" address rows, so the 36 could not be recounted independently.
- 66 rows with two or more sources and a strong fit: matches.
- Check table ranks: C22 1, C25 3 and 37, C24 4, D17 7 and 620, X15 24, C23 27, X16 29, D16 163, C18 166, X08 167, X05 223. All match `in_ground_truth`.
- Top 10 lines: rank 1 air permit 2025-11-06 (1 row, process manufacturing facility); rank 2 air permit 2024-08-06 (3 rows, stacks, not "two"; minor); rank 3 $3,000,000 tenant finish 2026-06-16 (26-2632310-000-00, valuation 3000000 in the raw file, 21 points); rank 4 $4.5M tenant finish (25-2563829-000-00, valuation 4500000, possible match at 10.5) and air permit 2025-10-21; rank 5 water permit 2025-10-15 (construction stormwater, Ardent Mills Commerce City); rank 8 three air rows 2025-03-25 (boiler, blending, methanol tank); rank 9 $3,211,635 tenant finish 2025-06-24 (25-2539278-000-00, valuation 3211635 in the raw file; the evidence file carries the date and description, and the ranked row's top_evidence carries the dollar figure). Note that this record is held at B3a as a commercial-use building and still scores 21 points on the $250k line, which the notes disclose as the method's rule, and that its intake twin 25-2538293-000-00 of 2025-06-20 also scores 21 (see check 1); rank 10 water permit SIC 2952 (2024-06-26, roofing shingle production).

## Check 3: people and em dashes

- Em dashes: 0 in each of the four files.
- Phone numbers and emails in company_name, next_step (ranked) and description (evidence): 0 and 0.
- "ROBERTO LOPEZ", "LIUFENGXIANG", "ZHANGYUHAO": in none of the four files.
- Ranked rows whose site_address matches \bAPT\b: 0.
