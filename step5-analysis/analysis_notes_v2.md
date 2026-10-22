# Step 5b: Denver ranking re-run with tier B flags

## Update 2026-10-11 (current files)

`denver_ranked_accounts_v2.csv` and `denver_evidence_v2.csv` now reflect a second re-run with three changes. Where the sections below give different numbers, this section is current.

1. **Equipment words run on the full collateral text.** `step4-scrape\scripts\pull_ucc_fulltext_b1a.py` fetched the collateral rows for the 27,736 unflagged initial filings longer than 500 characters (185 requests to the state's open data API) and applied the same words and guards. **It added 10 rows statewide and one in Denver.** Equipment-word rows: 66 (was 56). The 500-character cut was a much smaller gap than I said it was: Step 4 had already matched the heavy machinery words on full text, and most long filings are boilerplate.
2. **Equipment-word signal raised from 25 to 30.**
3. **A permit under $50k can add at most 4 stage points** (was up to 12). Its 6 signal points are unchanged.

Result: 743 rows (688 Denver, 42 county unconfirmed, 13 OEDIT). 384 are new. 78 Denver rows score 50 or more. 39 existing rows changed score.

**Top 25 changes against the first re-run:** Hearth Baking rises from 30 to 14 and Copeland Enterprises from 41 to 21. Big Metal Additive and Native Foods drop to 26 and 27 on unchanged scores. The top 13 are unchanged.

**New named companies:**

| Rank | Company | Score | Note |
|---|---|---|---|
| 14 | Hearth Baking LLC | 72 | Gas deck oven, December 2025 |
| 21 | Copeland Enterprises, Inc. | 68 | Planetary mixer beside a 30 HP gas package. What it makes is not confirmed |
| 34 | Radical Botanicals, LLC | 65 | New from the full-text pull: distillation system, June 2024, 44 Cook St Ste 100. An office address; not confirmed as the production site |
| 45 | Direct Polymers LLC | 61 | Granulator, January 2025 |
| 46 | Bakery Four L.L.C. | 61 | Electric roaster, October 2025 |
| 69 | Sleeping Giant Brewing | 53 | Can filler, February 2024. Wording may describe an auction |
| 88 | Northwest Confections Colorado | 48 | Blanket lien plus a permit at its address |

**Small permits:** the 138 addresses resting on one permit under $50k now score mostly in the 10s (87) and 20s (34). The highest sits at rank 125. Before the cap they clustered at 33 to 39.

**The 17 projects:** still 7. Direct Polymers 45 (was 57), Elemental Bakery 225 (was 255), PepsiCo 1, SRM 10 by address. The three address-only rows moved down with the cap: Maybell 304, BrewDog 555, Vinyl plant 588.

**Sensitivity to tier B points:** halved, 3 of the top 25 change (Hearth Baking, Copeland and 2401 W 6th Ave leave). Doubled, 7 change (Radical Botanicals, Direct Polymers, Bakery Four, Sleeping Giant and three address rows enter).

**Not added:** "bread", "beer" and Geneva Capital. They were offered and not asked for.

---


Run 2026-10-10, after the Step 4b re-flag and Matthew's four decisions. Files: `denver_ranked_accounts_v2.csv` (742 rows), `denver_evidence_v2.csv`, `scripts\rerank_step5b.py`, `rerank_counts.json`. The Step 5 files are untouched. Read `analysis_notes.md` first; this file covers only what changed.

## Decisions applied

1. **Trimmed registration words.** Bakery, coatings, foods, foundry, machine and machines dropped. Tier B registrations: 815 statewide (was 1,804).
2. **Small permits flag on industrial zoning or parcel class.** Tier B small permits: 328 (was 164).
3. **Points:** equipment word 25, lender lien 8, blanket lien 8, registration 3, permit of $50k or more 12, smaller permit 6.
4. **Merchant-cash liens dropped.** A blanket lien held by a known receivables funder no longer flags. 21 rows removed statewide, including the Goldspot row.

Tier B after the decisions: 364 UCC rows, 815 registrations, 476 Denver permits. The Step 4 `_v2` files and `scrape_flagged_v2.csv` (9,854 rows) were rewritten to match.

## Assumptions (read first)

1. **This is an incremental re-run, not a rebuild.** The Step 5 scripts were never saved. The 359 Step 5 rows keep their evidence, and their points were read back from the "Points:" text in `top_evidence` (all 359 parsed and summed to their scores). Tier B rows were then added on top. New rows were scoped, joined and scored with the Step 5 rules as written in `analysis_notes.md`.
2. **Within a source the best signal counts.** A tier B row raises a source's points only if it beats what the account already had there. Repeat points (+3 a month, max 9) apply only to new rows and only to signals of 12 or more.
3. **A tier B company at an existing unattached address is listed as a possible occupier at half points.** It is not promoted to the account, as in Step 5.
4. **A tier B permit at an unattached address scores in full. Joined to a named company by street address it is "possible" and scores half,** unless the suite matches.
5. **Denver test for new companies:** zip 99% or more in Denver is in. Split zips went through the Census geocoder (55 addresses: 39 Denver, 11 Adams, 4 Jefferson, 1 Arapahoe). Addresses placed outside Denver sit in the unconfirmed section. Zips under 10% Denver with a non-Denver city are left out.
6. **Fit for new rows uses the Step 5 order:** equipment named in a filing, a lien held by a machinery maker, a maker word in the name (labelled "not confirmed"), trade words, weak words. For new unattached addresses: food-processing, factory, meat-packing and printing-plant parcels are strong, warehouses unknown, auto garages and car washes moderate, housing, hotel, school and similar weak, anything else on industrial zoning unknown.
7. **Stage for a permit follows Step 5:** alteration not finaled or finaled in the last six months is fit-out; a new building not finaled is under construction; otherwise operating and expanding. This applies to zero-valuation permits too. See the caution below.
8. **A registration at 3 points earns no recency points,** because Step 5 gives recency only to rows worth 4 or more. The same holds for a small permit joined at half points.
9. **Home-address rule as in Step 5.** 83 new company rows show "withheld".
10. **Web checks:** five searches on the top new named companies, titles only. No agency or company contacted. No Atlas Copco data.

## Result

- **742 rows** (was 359): 687 in Denver County, 42 county unconfirmed, 13 OEDIT code names.
- **383 new rows:** 139 companies and 244 unattached addresses.
- **63 existing rows gained tier B evidence;** 44 of them changed score. No existing row lost points.
- **80 Denver rows score 50 or more** (was 62).
- New rows by where they came from: 54 UCC rows and 96 registrations made the 139 companies; 350 permits made the 244 addresses; 120 permits joined existing rows.

### Top 25

| Rank | Was | Company or address | Site | Stage | Score |
|---|---|---|---|---|---|
| 1 | 1 | PepsiCo Beverages North America, High Point plant | 19300 E 72nd Ave | fit-out | 126.5 |
| 2 | 3 | King Soopers, Inc. | 60 Yuma St | fit-out | 107.0 |
| 3 | 2 | Conagra Foods Packaged Foods | 4735 Florence St | fit-out | 96.0 |
| 4 | 4 | Quality Linings & Painting | 8250 E 40th Ave | operating and expanding | 89.0 |
| 5 | 6 | Nestle Purina Petcare | 4555 York St | fit-out | 89.0 |
| 6 | 5 | Dawn Food Products | 4500 Lipan St | operating and expanding | 83.0 |
| 7 | 7 | Safeway milk plant | 4301 N Forest St | fit-out | 83.0 |
| 8 | 27 | Lakin Tire West | 3750 N Nome St | fit-out | 78.5 |
| 9 | 8 | Cargill | 4545 Madison St | operating and expanding | 78.0 |
| 10 | 9 | Colorado Truckwashing | 5150 Brighton Blvd | buying equipment | 77.0 |
| 11 | 10 | Titan Fittings | 11795 E 45th Ave | buying equipment | 76.0 |
| 12 | 18 | Blazy Susan | 10660 E 51st Ave | buying equipment | 75.0 |
| 13 | 36 | 2401 W 6th Ave LLC | 2401 W 6th Ave | operating and expanding | 73.5 |
| 14 | 11 | Frito Lay | 11645 E 37th Ave | fit-out | 71.5 |
| 15 | 12 | Amcor Rigid Packaging | 4990 N Ironton St | under construction | 70.5 |
| 16 | 13 | CO-Innovate | withheld | buying equipment | 70.0 |
| 17 | 41 | Unattached address | 3939 N Kearney St | fit-out | 69.0 |
| 18 | 14 | Unattached address | 95 S Tejon St | fit-out | 68.0 |
| 19 | 15 | Unattached address | 4460 N Madison St | under construction | 68.0 |
| 20 | 16 | Unattached address | 3100 N Brighton Blvd 1200 | fit-out | 67.5 |
| 21 | 17 | Pacific Air | 2550 W 2nd Ave Unit 110 | buying equipment | 67.0 |
| 22 | 19 | R B Machine | withheld | buying equipment | 67.0 |
| 23 | 20 | Custom Stone | 4398 Broadway, Unit A | buying equipment | 67.0 |
| 24 | 21 | Big Metal Additive | withheld | buying equipment | 67.0 |
| 25 | 22 | Native Foods | 4823 Lima St | buying equipment | 67.0 |

The top seven are the same seven as before. Three rows entered the top 25 (Lakin Tire, 2401 W 6th Ave LLC, 3939 N Kearney St), each on a tier B permit joined by address. Intertech Plastics, Starko Gear and Never Summer dropped to 26 to 28 on the same 67 points; nothing about them changed.

### New named companies worth a look

| Rank | Company | Score | What the record shows |
|---|---|---|---|
| 30 | Hearth Baking LLC | 67.0 | Financed a gas deck oven, December 2025. Search titles show a bakery opening a second Denver location |
| 41 | Copeland Enterprises, Inc. | 63.0 | Two 2025-26 filings naming a planetary mixer beside a 30 HP LeRoi gas package. What it makes is not confirmed; could be oil-field kit |
| 57 | Direct Polymers LLC | 56.0 | Granulator filing, January 2025. Ground-truth project X06 |
| 58 | Bakery Four L.L.C. | 56.0 | Electric roaster on an equipment contract, October 2025. Search titles show a Berkeley bakery planning an expansion |
| 72 | Northwest Confections Colorado | 52.0 | Blanket lien January 2026 plus a permit at 2670 S Delaware St. Not confirmed |
| 93 | Sleeping Giant Brewing | 48.0 | 40-head can filler, February 2024. A contract brewer. The collateral reads "Bulk Bid for Lots", which may be an auction; check before calling |
| 170 | Seattle Fish Co | 38.0 | Lien held by Multivac (packaging machines), January 2026, collateral in an attachment |

12 of the top 100 rows are new. The rest of the new rows sit lower: 135 score in the 10s, 110 in the 20s, 97 in the 30s.

## Check against the ground truth

**7 of 17 Denver projects now appear, up from 2. Four are by name or were already in. Three are by address only and rank low.**

| Project | Step 5 | Now | How |
|---|---|---|---|
| D01 PepsiCo | 1, 113 | 1, 192 | Unchanged |
| D14 SRM Concrete | 9 | 10 | Address only, on the truck wash row. Unchanged |
| X06 Direct Polymers (NextRun) | not ranked | 57 | Name. Granulator filing |
| D11 Elemental Bakery | not ranked | 255 | Name and suite. Blanket lien, 31 points |
| D15 Maybell Quantum | not ranked | 205 | Address only: unattached address 3821 N Steele St 1411, two small permits |
| D07 BrewDog Denver | not ranked | 548 | Address only: 3950 Wynkoop St 100, two $0 permits from early 2024, 14 points |
| D13 Vinyl Me Please plant | not ranked | 576 | Address only: 4201 N Brighton Blvd, one $0 permit from 2024, 14 points |
| D09 Cheetah Coalition | not ranked | not ranked | Its only flag was the merchant-cash lien, dropped by decision 4 |
| D10 Rebel Bread | not ranked | not ranked | "Bread" is not a listed word |
| D06 Full Frame Beer | not ranked | not ranked | "Beer" is not a listed word |
| D02, D03, D04, D08, D12, X12, X13 | not ranked | not ranked | No usable record, as before |

Read this honestly: only Direct Polymers lands where a rep would see it. Elemental is real but at rank 255. The three address-only rows are among 244 unattached addresses and nothing on the row names the tenant. The scoring was not tuned to the 17. The zoning-only permit rule was chosen knowing it would reach those three addresses, so those three are not independent evidence that the rule works.

## Sensitivity of the top 25 to the tier B points

- **Tier B points halved:** 1 of 25 changes. Intertech Plastics returns, 2401 W 6th Ave LLC leaves.
- **Tier B points doubled:** 9 of 25 change. In: Hearth Baking, Copeland Enterprises, Direct Polymers, Bakery Four, Sleeping Giant, Acme Manufacturing, Electric Equipment & Engineering, and the addresses 5590 N Joliet St and 2323 W Mulberry Pl. Out: CO-Innovate, Pacific Air, R B Machine, Custom Stone, Big Metal Additive, Native Foods and three unattached addresses.

At the agreed points tier B barely moves the top 25. It mostly lengthens the list.

## Cautions

- **138 of the 244 new addresses rest on one permit under $50k.** Step 5's stage rule gives an open alteration permit 12 points for fit-out whatever its value, so a $0 permit can score 6 for the signal and 12 for the stage. These rows cluster at 33 to 39 points. If that reads too generous, cap the stage points for permits under $50k.
- **95 new company rows are a registration and nothing else,** scoring 3 plus fit. They are in the list for joins later, not as leads.
- **Blanket liens filed through an agent hide the lender.** About 60 of the 258 blanket-lien rows statewide name CHTD, CSC or CT Corporation as secured party. Some of those are fintech or cash-advance lenders that the funder list cannot see.
- **Two rows are one company:** "Mountain Packaging LLC" (rank 122) and "Mountain Packaging Est. 2007" (rank 174) did not merge because the names differ.
- **The equipment-word rule still reads only the first 500 characters** of collateral text.

## Not done

- **The Accela lookup list was not rebuilt.** `accela_lookup_list.csv` is the Step 5 version.
- **The four Step 5 sensitivity runs** (recency and source bonus) were not repeated. Only the tier B points were varied.
- **No web check beyond five searches.** Copeland Enterprises and Northwest Confections are unconfirmed.
- **The project copy was not updated.** The project is full; the v2 files are in this folder only.

## Re-running

`python3 scripts\rerank_step5b.py <step4-scrape folder> <step5-analysis folder>`. It needs the Step 5 ranked and evidence files in place and the Step 4 `_v2` files. `--bscale 0.5` scales the tier B points. About 20 seconds once `geocode_cache.json` holds the split-zip lookups.
