# Step 4b: re-flag notes

Run 2026-10-10 on the full Step 4 files in this folder. Nothing was re-scraped and the Step 5 ranking was not re-run. Script: `scripts/reflag_step4b.py`. Counts: `reflag_counts.json`.

## Assumptions (read first)

1. **UCC words were matched on the first 500 characters only.** Step 4 matched tier A on the full collateral text, then cut `description` at 500. The full text is not on disk. 36,623 of the 103,270 initial UCC filings have longer text, so rule B1a undercounts. Lenders whose form opens with boilerplate (Verdant, Wells Fargo Vendor) hide the equipment past the cut. Fixing this means running the B1a word list inside `pull_ucc_filings.py` at the next scrape.
2. **Tier B UCC rules apply only to initial UCC financing statements.** Farm-product statements, tax liens and statutory liens are left out.
3. **No tier B flag on a UCC debtor with no business word in its name** (`debtor_name_has_entity_token` = N), for all three UCC rules, not only B1c. The brief asked for this on B1c only.
4. **"Vague" collateral means one of three things:** blank; a blanket lien whose text opens with "all assets", "all personal property" or an inventory-equipment-accounts list; or a pointer to an exhibit, schedule or attachment with no itemised equipment. "All equipment under contract number X" is not counted as vague.
5. **The equipment lender list is my reading of the tier A secured parties.** A lender is kept with 2 or more tier A rows and either a machinery maker, dealer or captive arm, or 20% or more of its own initial filings being tier A. The 20% line is my choice. Lists are in the script and below.
6. **SBA initial filings and sales of future receivables are left out of B1c.** A merchant cash advance reads like a blanket lien but signals cash strain. This guard is by wording and does not catch every funder.
7. **B1c drops trade and retail names** (roofing, construction, supply, store, auto and similar), plural "tools" and "machinery", because those were dealers and contractors.
8. **"Industrial parcel class" leaves out 12 assessor classes** that carry the INDUSTRIAL prefix but are churches, schools, meeting halls, recreation, convenience stores, auto dealers, vets and similar. Auto service garages, car washes, warehouses, factories and food plants stay in. Both counts are given below.
9. **Industrial zoning for B3a is I-A, I-B, I-MX and M-IMX only.** Old-code I-0, I-1 and I-2 (12 permits) are not included.
10. **Blank valuation (6 permits) is not flagged.** Special events and change of contractor are left out of B3a as well as B3b.
11. **"Denver" for UCC and registrations means a Denver, CO mailing city.** Step 5's zip and geocoder test was not repeated.
12. **Home-address rule is applied in `scrape_flagged_v2.csv` to tier B UCC and registration rows.** 1,014 of 2,190 show "withheld". The `_v2` source files keep the address as Step 4 stored it. Tier A rows are untouched.
13. **Sample judgments are from the record alone** (name, collateral text, parcel class). No web checks.
14. **No Atlas Copco data, no contact with anyone, no records requests. Step 3 corrections not applied.**

## Rows added

Tier A is unchanged in every file (checked row by row: 0 mismatches, every tier A row is `flag_v2` = Y).

| Source | Tier A | Tier B added | Ratio | Tier B in Denver |
|---|---|---|---|---|
| Colorado UCC filings | 901 | 386 | 0.4x | 62 |
| Colorado business registrations | 2,211 | 1,804 | 0.8x | 258 |
| Denver commercial permits | 509 | 312 | 0.6x | 312 |
| **scrape_flagged_v2.csv** | 8,199 | 2,502 | | |

No rule passed 3x its source's tier A count. Two rules were tightened anyway, on precision; both versions are below.

| Rule | Rows statewide | Denver | Notes |
|---|---|---|---|
| B1a process-equipment word | 56 | 7 | 155 before guards |
| B1b vague lien + equipment lender | 53 | 8 | 1,177 with the broad lender list |
| B1c blanket lien + maker word | 280 | 48 | 343 before guards |
| B2a domestic entity + narrow word | 1,804 | 258 | 2,161 before the status and agent-address cuts |
| B3a $50k or more, industrial property | 148 | 148 | 235 with every INDUSTRIAL parcel class |
| B3b under $50k, industrial parcel | 164 | 164 | 250 with every INDUSTRIAL parcel class; 77 are zero valuation |

Five UCC rows fired two rules. 40 of the 386 UCC rows have an out-of-state debtor address.

### B1a guards

Words hit, after guards: shredder 12, oven 7, dust collector 6, dryer 5, mixer 5, roaster 5, filler 4, spray booth 3, grinder 2, labeler 2, mill 2, vacuum pump 2, and one each of capper, granulator, palletizer, still, Elgi. Kiln, extruder, sandblast, powder coat, air dryer, fermenter, brewhouse, canning line, Kaeser, Sullair, Gardner Denver and Quincy were already tier A words, so they add nothing. Chicago Pneumatic, Boge, CompAir, FS-Curtis and Sullivan-Palatek matched no unflagged row.

Guards used, in the script as named patterns:
- Fixture boilerplate (Step 4's rule, unchanged).
- Kitchen context: oven, mixer, blender, grinder, filler, roaster and dryer are dropped at a restaurant-type debtor or beside fryers, dishwashers and similar, unless the name says bakery, foods or similar. Convenience-store ovens (warmer, ventless, rapid cook) are dropped.
- Dryer: laundry, hair, grain and car-wash dryers.
- Mixer: mixer trucks, drilling-fluid mixers (Vermeer), grout and feed mixers, audio mixers. This was the largest false group (35 hits down to 5).
- Grinder: stump, tub, coffee, feed and floor grinders (22 down to 2).
- Mill: only a typed mill (roller, hammer, ball and similar) or a model code followed by "mill". Bare "mill" hit surnames, place names and asphalt milling (22 down to 2).
- Still: only pot, column or similar stills and distillation equipment. Bare "still" is an everyday word.
- Blender and filler: typed forms only (ribbon blender, can filler).
- Shredder: paper and crop shredders. Vacuum pump: dental, medical, septic. Nitrogen generator: lab instrument sets. Dust collector: floor-grinding kits.
- Farm, construction, trucking, government and trust names are dropped for mixer, grinder, mill, shredder, dryer, vacuum pump and dust collector.

### B1b lender list

Narrow list (delivered): CNC Associates, Star CNC Machine Tool, TRUMPF, Methods Machine Tools, Productivity Inc, Hartwig, Multivac, Robert Reiser, Yamazen, Mitsui Seiki, Maruka USA, Absolute Haitian, GROB Systems, Mazak, FANUC America, Yaskawa America, SMT Finance, American Packaging Capital, Hansen Metallurgical, Sumitomo Mitsui Finance & Leasing, Machinery Finance Resources, Manufacturers Capital, Wildcat Funding, Verdant Commercial Capital, UniFi Equipment Finance, m2 Equipment Finance, Five Lakes Financial, Noreast Capital, Landmark Financial.

Rows by lender: Mazak 19, Verdant 19, Multivac 6, TRUMPF 4, Five Lakes 2, and one each for Landmark, Noreast and UniFi. Most machinery vendors itemise their collateral, so they have no vague liens and add nothing here.

Broad list (run with `--broad-lenders`, not delivered) adds U.S. Bank Equipment Finance, Key Equipment Finance, Wells Fargo Equipment Finance, Wells Fargo Vendor Financial, Siemens Financial, KLC, Ailco, Customers Commercial Finance, Allegiant, Stearns Bank Equipment Finance, Northland, Navitas, Oakmont, Blue Bridge, Western Equipment Finance, Marlin, Highland Capital, Geneva Capital, De Lage Landen, GreatAmerica, North Star Leasing, LEAF, Targeted Lending and Commercial Capital. It gives 1,177 rows: LEAF 431, U.S. Bank 234, Geneva 197, Navitas 76. A read of 12 rows per lender showed dentists, school districts, a law firm, a botanic garden, churches and restaurants. Geneva Capital is the exception worth a look: its blank liens include several machine shops.

Left out of both: banks, the SBA, filing agents (CSC, CT Corporation, CHTD, Financial Agent Services, Secured Lender Solutions), Colorado Enterprise Fund and other loan funds, construction, farm and truck lenders (Wagner, John Deere, Faris, CNH, Commercial Credit Group, Keystone, Trans Lease, North Mill), and Alliance Laundry, Cardinal Health, Zimmer and Canon.

### B1c words

Top words: foods 27, manufacturing 25, precision 17, brewing 15, welding 15, bakery 13, metals 11, packaging 11, plastics 11, metal 10. Added to the brief's list as "similar": distillery, baking, roastery, mfg, machining, fabricators, millwork, cabinets, cabinetry, foundry, castings, molding, bottling, composites, welding, winery, cidery, creamery, tortilleria, confections, chocolate, candy, extrusion, stamping, plating, forge.

### B2a registrations

Words: bakery 421, fabrication 316, foods 221, manufacturing 202, coatings 146, machine or machines 128, foundry 74, aerospace 50, brewing 45, robotics 42, packaging 35, roasters 35, machining 33, mfg 16, then under 10 each. Left out: 172 withdrawn, dissolved, converted or merged; 185 at an address and suite with 10 or more registrations since 2024. Kept: 362 Delinquent and 77 Noncompliant entities, which the brief did not exclude.

## Sample read (50 random tier B rows per source, seed 20261010)

| Source | Looks like a production site | Unclear | No |
|---|---|---|---|
| UCC filings | 34 | 7 | 9 |
| Business registrations | 6 | 10 | 34 |
| Denver permits | 35 on warehouse, factory or food-plant parcels | 6 | 9 |

- **UCC.** By rule: B1c 27 of 37, B1a 6 of 11, B1b 1 of 2. Most yes rows are small makers: bakeries, roasters, cabinet shops, small fabricators. Misses were a floor-coatings franchise, an auto shop, a clinical lab, a tool retailer, a pizza kitchen, an art restorer, a farm and an oil-field vapour unit.
- **Registrations.** The six were fabrication (4), a distillery and an additive-manufacturing firm. 16 of the 50 were bakeries, all home or retail by name. Coatings (6) were all floor and paint contractors. "Machine" gave gaming, sewing and vending. "Foundry" gave an electrician and a fashion label.
- **Permits.** The layer has no tenant or description, so "production" cannot be read. 35 sit on warehouse, factory or food-processing parcels. The nine misses were offices and shops inside I-MX zoning, two car washes, an auto garage and the Botanic Gardens greenhouse.

## The 17 Denver projects

Matching as in Step 5: normalised name, and address reduced to number, direction and street. An address-only match is listed but not counted.

| Project | Before (Step 5 ranking) | After: has a `flag_v2` = Y row | Source and rule |
|---|---|---|---|
| D01 PepsiCo | yes | yes, tier A | Air permit, water permits, five permits at 19301 E 70th (address) |
| D02 Swire Coca-Cola (cancelled) | no | tier A row only for the old York St plant | 2024 stormwater renewal, cut in Step 5. Unchanged |
| D03 4 Noses Brewing | no | no | No row of its own. Opened 2023 |
| D04 Wilding Brands Canworks | no | no | One seller-financed lien reading "See attachment"; the rest are amendments and receivables liens |
| D06 Full Frame Beer | no | no | 2024 domestic registration. "Beer" is not on the narrow list |
| D07 BrewDog Denver | no | no | Two $0 permits at 3950 Wynkoop. Parcel class is restaurant, zoning I-MX-12 |
| D08 Monolith Brewing | no | no | No row of its own. Opened 2023 |
| D09 Cheetah Coalition | no | **yes, tier B** | UCC B1c: Goldspot Brewing Company, 4970 Lowell Blvd, blanket lien 2024-10-30. See the caution below |
| D10 Rebel Bread | no | no | Blanket lien 2025-04-01, but "bread" is not a listed word. Its $149k permit is at another suite on a shopping-centre parcel |
| D11 Elemental Bakery | no | **yes, tier B** | UCC B1c: blanket lien 2024-12-13, name and suite match, five days before the planned opening |
| D12 Azure Printed Homes | no | no | Los Angeles address. Lien points to an exhibit, lender is a housing authority |
| D13 Vinyl Me Please plant | no | no | One $0 permit at 4201 N Brighton. Parcel class is vacant land, zoning I-MX-8 |
| D14 SRM Concrete | yes | yes, tier A | Concept review at 5150 N Brighton (address) |
| D15 Maybell Quantum | no | no | Permits of $1 and $32k at 3821 N Steele. Parcel class is retail, zoning I-MX-5 |
| X06 NextRun hub (Direct Polymers) | no | **yes, tier B** | UCC B1a: granulator, 2025-01-10, debtor at 3601 E 44th Ave |
| X12 Crazy Shirts | no | no | Opened 2023. Only a 2024 exhibit lien on the building owner |
| X13 Sara Gabriel | no | no | Opened 2023. A 2026 account lien only |

**Result: 5 of 17, up from 2.** That is below the 9 to 11 the handoff expected. No rule looks too loose on this evidence; the rules are narrower than the misses.

Three things to know about the 5:

1. **One guard was corrected after the first check, and it moved the count from 4 to 5.** The blanket-lien test was cancelled by the phrase "the following" anywhere in the opening text, which wrongly dropped liens that begin "All assets now owned or hereafter acquired ... the following subcategories". I narrowed it to "the following equipment, goods, items, property". That added 25 B1c rows statewide, one of them Goldspot. I found the fault by looking at a ground-truth miss, so treat that fifth project with that in mind.
2. **The Goldspot lien is from a merchant-cash funder** (The LCF Group), three months before the commissary launch. It is a blanket lien on a brewer, so the rule fired as written, but it is more likely a sign of tight cash than of new capacity.
3. **A false name match was set aside.** "CB CO Manufacturing LLC" (a 2024 domestic registration in Denver, tier B) matched the PepsiCo alias and is not PepsiCo.

Step 3 corrections that touch this result, none applied: Direct Polymers' debtor address is 3601 E 44th Ave, not the 3600 E 45th Ave in Step 3. The Vinyl plant and Maybell matches rest on the Step 3 best-guess addresses.

**What would reach the other misses, not applied:**

- **Zoning on its own for small permits.** BrewDog, Maybell and the Vinyl plant all have zero or nominal permits on I-MX zoning where the assessor class is restaurant, retail or vacant land. Letting B3b fire on industrial zoning or parcel class would add 164 permits (103 at zero valuation) and reach all three by address. Address-only matches score half in Step 5. This would bring the count to 8.
- **"Bread" and "beer" as maker words** would reach Rebel Bread and Full Frame Beer. I did not add them, because I only know they matter from the answer key.
- Nothing in these files reaches 4 Noses, Monolith, Crazy Shirts, Sara Gabriel (all 2023), Wilding, Azure or Swire.

## Not done

- **UCC B1a on full collateral text.** Not possible without the raw Step 4 cache or a re-scrape. Source: Colorado UCC filings, rule B1a.
- **County test for tier B UCC and registration rows.** Denver counts use mailing city.
- **Web checks on the samples.** Judged from the record.
- Everything else in the handoff was completed.

## Files

- `scrape_ucc_filings\scrape_ucc_filings_v2.csv`, `scrape_business_registrations\scrape_business_registrations_v2.csv`, `scrape_denver_commercial_permits_v2.csv`: the Step 4 files with `flag_v2`, `flag_tier`, `flag_rule_v2` added. Same rows, same order.
- `scrape_flagged_v2.csv`: 10,701 rows. The 17 shared columns plus `flag_tier` and `flag_rule_v2`. All eight sources.
- `scripts\reflag_step4b.py`: `python3 reflag_step4b.py <this folder>`. Options: `--broad-lenders`, `--strict-parcel`, `--out <folder>`. About one minute.
- `scripts\reflag_step4b_check.py`: the 17-project check. It holds the project names and addresses; the flagging script does not.
- `reflag_counts.json`: every count above.

## Decisions for Matthew before Step 5 is re-run

1. **Which tier B rules to keep.** On the sample: B1c and B3a/B3b look worth keeping. B1a is small and mixed. B1b narrow adds 53 rows, half of them Verdant blanks that looked weak. B2a is 12% useful as written.
2. **Trim B2a to the words that worked.** Dropping bakery, coatings, foods, foundry, machine and machines leaves 814 rows and removes most of the noise seen.
3. **Whether B3b should fire on zoning alone** (+164 permits; reaches three more known projects by address).
4. **How many points tier B earns.** Step 5 gives a blanket lien 4 points as support and a flagged registration 6. A starting point: B1a at the tier A machinery level (25) since it names equipment; B1b 8; B1c 8; B2a 3; B3a 12; B3b 6. All address-only joins still halve.
5. **Whether receivables-funder liens should count at all** (the Goldspot case).
6. **Whether to add Geneva Capital to the lender list** (197 blank liens, several on machine shops).
7. **Whether to re-run the UCC pull so B1a sees the full text.**

---

## Decisions applied after the first run (2026-10-10)

The files in this folder now reflect four decisions. The sections above describe the first run and are kept for the record.

1. **Registration words trimmed.** Bakery, coatings, foods, foundry, machine and machines dropped from B2a. Rows: 815 (was 1,804). Denver: 99.
2. **B3b fires on industrial zoning or parcel class.** Rows: 328 (was 164). B3a unchanged at 148.
3. **Receivables and merchant-cash funders dropped from B1c** by secured-party name (list in the script, `FUNDER`). B1c rows: 258 (was 280). The Goldspot row is out, so the 17-project count on flags alone is 4 by name plus 3 by address.
4. **SBA guard fixed** to catch a misspelt "Small Busines Administration" (one row).

Current counts: UCC tier B 364 (B1a 56, B1b 53, B1c 258), registrations 815, permits 476. `scrape_flagged_v2.csv` has 9,854 rows. The Step 5 re-run is in `step5-analysis\analysis_notes_v2.md`.

## Full collateral text for the equipment words (2026-10-11)

`scripts\pull_ucc_fulltext_b1a.py` fetched the collateral rows for the 27,736 unflagged initial UCC filings with text over 500 characters and ran the B1a words and guards on the whole text. Hits are in `scrape_ucc_filings\ucc_b1a_fulltext_hits.csv` (30 rows: the matched words and a 220-character snippet; the full text is not stored). `reflag_step4b.py` reads that file when it is there.

Effect: B1a rows 66 (was 56), 8 of them matched past character 500. UCC tier B 374. `scrape_flagged_v2.csv` has 9,864 rows. Assumption 1 and the "Not done" item on full text above no longer apply. After a new scrape, run the pull script again before the re-flag.
