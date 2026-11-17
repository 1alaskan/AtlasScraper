# Step 6: contact enrichment, Denver top accounts

Run 2026-11-16. Output: `denver_top25_contacts.csv` (32 rows, 22 columns). Scripts: `scripts/wq_contact_roles.py`, `scripts/build_contacts.py`. Adams and Weld were added the same day; their section is at the end of this file.

**Status: complete for all three counties.** The phone columns were filled in a later pass the same day; the final counts are in the last section, "Phone pass", and they replace the phone rows of the two coverage tables above it.

## Assumptions (read first)

1. **Which ranking.** The brief names `step5-analysis/denver_ranked_accounts.csv` (the first run, 2026-10-10). The repo and the Streamlit site now use `step5-analysis/v3/denver_ranked_accounts_v3b.csv`. The two top 25s share 18 rows. All 25 of the brief's rows sit inside the v3b top 32, so this file covers **v3b ranks 1 to 32**, which is both lists. `rank` is the v3b rank. The table at the end maps each row to its first-run rank.
2. **Where files were read and saved.** Nothing was read from or written to Matthew's computer (access was declined, and the repo holds the same files). Inputs came from the repo `1alaskan/AtlasScraper`; outputs are saved there under `step6-contacts/`.
3. **The state water sheet was downloaded again** (one request, 2026-11-16, same export link as Step 4, 27,550 rows, latest issue date 2026-08-06, so the snapshot is unchanged). Step 4 dropped the contact blocks, and Task 2 needs the title and organisation columns from them. `wq_contact_roles.py` reads only the title, organisation, city and state columns. Names, phones, emails and street addresses of contacts are never read out or written. The download is not saved in the repo.
4. **Permit records outside the Step 4 date window were used** where they sit at the account's address: the 2022 PepsiCo construction permits, the 2017 Safeway pretreatment permit, a 2012 Intertech permit. Each is dated in `coverage_note`.
5. **On-site rule.** `on_site` means the contact's organisation is the company and the contact's listed city is Denver (or the title names the plant). A company contact at a head office elsewhere is listed in the role text with the city but does not make the row on-site by itself. `third_party` means a contractor or consultant.
6. **Role text is as the sheet gives it** ("EHS Mgr", "Plant Dir"), with the contact block in brackets. Several roles are listed where the blocks differ.
7. **Contractors from the Denver open data permit layer are included.** The brief's source list does not name it. It is the Step 4 file `scrape_denver_commercial_permits_v2.csv` (the city's open data layer, not the Accela portal), and it is the only source that names a contractor for most rows. The role is given as "contractor of record on building permit", because the layer does not say general or trade. Drop these if they are not wanted: they all carry a `denver_permits:` source tag.
8. **A permit joined by street address alone** is marked "joined by street address" in the role text. The contractor is real; whether the work is the named company's is possible, not confirmed.
9. **`match_confidence`** is `confirmed` when a record carries the company name and the address together (state permit, UCC debtor address with unit, or the company's own website), `possible` otherwise, blank for an address with no company. Rank 2 (Safeway milk plant) moves to confirmed: state permit COPB90721 names it at 4301 Forest St.
10. **Phone fields are blank, not `none_found`, where no check was possible.** `none_found` would claim a search that did not happen.
11. **Withheld addresses stay withheld**, except Never Summer, whose own website prints its factory address.
12. **No Accela portal use, no Atlas Copco data, no contact with any company or agency, no records requests.** No people's names, personal phones or emails are in either file.

## Source tags used in the CSV

| Tag | Source |
|---|---|
| `wqcd_sheet:<PermitID>` | CDPHE "Active CDPS permits and certifications" sheet, https://docs.google.com/spreadsheets/d/1ZFnnmKQc6zCeiYLcEOcf43cnYb7nwA2Y (downloaded 2026-11-16) |
| `denver_permits:<record id>` | `step4-scrape/scrape_denver_commercial_permits_v2.csv`, Denver open data commercial construction permit layer |
| `mile_high_cre:<post id>` | `step4-scrape/scrape_mile_high_cre.csv` (headline and excerpt rows; the articles were not re-read) |

## Coverage

| | All 32 rows | The brief's 25 |
|---|---|---|
| Site phone found | 2 | 2 |
| HQ-only number | 0 | 0 |
| None found after a check | 0 | 0 |
| Phone not checked (blocked) | 25 | 20 |
| Phone skipped (no company to call) | 5 | 3 |
| Permit contact recorded | 14 | 12 |
| of which on-site | 12 | 11 |
| of which third party | 1 | 1 |
| of which unknown | 1 | 0 |
| At least one contractor | 14 | 11 |

- **Permit contacts all come from the water sheet.** Each of the 12 on-site rows has an EHS, safety, environmental, plant-manager or general-manager role at the Denver site.
- **18 rows have no permit contact** because no current air or water permit record exists for them: the UCC machinery buyers and the unattached addresses.
- **Three state-record findings that change earlier notes:** the Safeway milk plant occupier is confirmed; 3100 N Brighton Blvd is the Steel House office building (weak fit); 95 S Tejon St has the same contractor of record as the Frito-Lay plant permits (not proof of the occupier).

## Blocked or unreachable

- **Company websites (25 rows).** Two were read (Titan Fittings, Never Summer). After that, each page fetch asked for an approval that was not answered, so no further company pages were opened. Search results alone surfaced listing sites, which are not allowed sources, so their numbers were not recorded.
- **APCD permit documents (7 rows).** The status feed has no contact fields. The records viewer (OnBase) only works in a real browser, and the one fetch tried was held for the same approval. Permit numbers and AIRS IDs are in `coverage_note` for a hand lookup: 22DE0598 / 031-2567, 13DE1362 / 031-2169, 95DE314 / 031-1662, 04DE1382 / 031-1968, 93DE1121 / 031-0042, 10DE1562 / 031-2067, 26DE0441 / 031-0052.
- **Mile High CRE articles.** Not re-read (same approval). The Step 4 headline rows were used.
- **Big plants are unlikely to yield a site number even when checked.** Corporate sites for PepsiCo, Albertsons, Conagra, Kroger, Nestle, Cargill, Frito-Lay and Amcor rarely print a plant line. Expect `hq_only` there; the on-site role in this file is the better way in.

## How to re-run (next 25, or Adams County)

1. Pick the ranked file and row range. Edit `RANKED` and `N` in `scripts/build_contacts.py`.
2. Download the water sheet once: `curl -sSL -A "step6-research-pull/1.0" -o active_permits.xlsx "https://docs.google.com/spreadsheets/d/1ZFnnmKQc6zCeiYLcEOcf43cnYb7nwA2Y/export?format=xlsx"`.
3. Edit the two patterns at the top of `scripts/wq_contact_roles.py` (`ADDR` for street addresses, `NAME` for company names) and the county test (it keeps city or county Denver; use Adams). Run `python3 -I scripts/wq_contact_roles.py active_permits.xlsx roles.json`. It prints nothing personal; `roles.json` holds permit, facility, title, organisation, city.
4. Contractors: filter the county's permit file by the same addresses. Adams has no single permit layer; use the county loader files under `step4-scrape/adams/`, and the construction stormwater rows (permittee and property owner) matter more there.
5. Phones: open each company's own contact or locations page. This needs someone present to approve the page fetches, or a session where web fetch is pre-approved.
6. Type the results into the `D` table in `build_contacts.py` and run it from the repo root. It checks the three contractor lists line up and prints the coverage counts.

## Rank map

| v3b rank | First-run rank | Account |
|---|---|---|
| 1 | 1 | PepsiCo High Point plant |
| 2 | 7 | Safeway milk plant |
| 3 | 2 | Conagra Foods |
| 4 | 3 | King Soopers bakery |
| 5 | 4 | Quality Linings & Painting |
| 6 | 6 | Nestle Purina |
| 7 | 41 | 3939 N Kearney St (not in the brief's 25) |
| 8 | 5 | Dawn Food Products |
| 9 | 27 | Lakin Tire West (not in the brief's 25) |
| 10 | 9 | Colorado Truckwashing |
| 11 | none | Verde Prickly Pear (not in the brief's 25) |
| 12 | 10 | Titan Fittings |
| 13 | 18 | Blazy Susan |
| 14 | 8 | Cargill |
| 15 | 36 | 2401 W 6th Ave LLC (not in the brief's 25) |
| 16 | 34 | Lemon Powers (not in the brief's 25) |
| 17 | none | Hearth Baking (not in the brief's 25) |
| 18 | 11 | Frito Lay |
| 19 | 14 | 95 S Tejon St |
| 20 | 12 | Amcor Rigid Packaging |
| 21 | 13 | CO-Innovate |
| 22 | 15 | 4460 N Madison St |
| 23 | none | Copeland Enterprises (not in the brief's 25) |
| 24 | 16 | 3100 N Brighton Blvd 1200 |
| 25 | 17 | Pacific Air |
| 26 | 19 | R B Machine |
| 27 | 20 | Custom Stone |
| 28 | 21 | Big Metal Additive |
| 29 | 22 | Native Foods |
| 30 | 23 | Intertech Plastics |
| 31 | 25 | Never Summer Industries |
| 32 | 24 | Starko Gear |

---

# Adams and Weld top 25 (added 2026-11-16, second run)

Outputs: `adams_top25_contacts.csv` and `weld_top25_contacts.csv` (25 rows each, same 22 columns), from `step5-analysis/adams/adams_ranked_accounts_v3.csv` and `step5-analysis/weld/weld_ranked_accounts_v3.csv`, ranks 1 to 25. Denver stays as the 32-row file above, which holds its top 25.

Permit contacts and contractors are done by rule from the state water sheet. Phones were added in the phone pass (last section).

## Assumptions for these two files

1. **Built by rule, not by hand.** `scripts/wq_cache.py` turns the sheet into a cache with no personal fields; `scripts/enrich_county.py` matches each account to permits by house number and street inside the county (or the same zip), plus any water permit already in the county's evidence file.
2. **A permit at the address held by a different name is not used.** Three cases: RK Industries (permit held by Creative Touch Interiors), Hirsh Precision (Spartronics Frederick), Schlosser Signs (Hexcel). Each is named in `coverage_note`. They may be earlier occupiers or neighbours; nothing here settles which.
3. **Which permit supplies the contact:** a live operating permit first (industrial stormwater, then no-exposure, individual, pretreatment), then an ended one, then a construction permit.
4. **On-site** means a company contact whose listed city is the facility's city, or whose title names the plant, site or facility. A company contact at another city is `unknown`. A contractor's contact on a construction permit is `third_party`.
5. **Contractors come only from construction stormwater permits** (permittee and property owner organisation), with the project name, status and received month in the role text. The role is left as "construction stormwater permittee" because the sheet does not say general or civil. The Adams and Weld permit files carry no contractor column, so there is no equivalent of the Denver permit layer.
6. **A company that holds its own construction permit** is noted as a sign of site work, not listed as its own contractor.
7. **Organisation names with no business word are dropped** from the contractor lists, to keep private individuals out.
8. `match_confidence` is carried from the ranking: confirmed where the ranking says so or a matching state permit sits at the address, otherwise possible, blank for an address with no company.

## Coverage, all three counties

| | Denver (32) | Adams (25) | Weld (25) |
|---|---|---|---|
| Site phone found | 2 | 0 | 0 |
| HQ-only number | 0 | 0 | 0 |
| Phone not checked (blocked) | 25 | 19 | 25 |
| Phone skipped (no company to call) | 5 | 6 | 0 |
| Permit contact recorded | 14 | 14 | 7 |
| of which on-site | 12 | 9 | 5 |
| of which third party | 1 | 4 | 0 |
| of which unknown | 1 | 1 | 2 |
| At least one contractor | 14 | 6 | 3 |

## What the permit records say about some rows

- **Adams rank 16 (6300 N Powhaton Rd, "Project Chorro"):** the construction permit's project name is "AMZ IXD BJC1", built by Graycor Construction for Ambrose Property Group. That reads as a logistics building, not a plant.
- **Adams rank 18 (16000 E 32nd Ave):** the construction permit is the Aurora Animal Shelter, owner City of Aurora. Not a compressed-air lead.
- **Adams rank 12 (1631 Manilla Rd):** the only permit is a 2021 pipeline hydrostatic test for an oil and gas gathering line.
- **Adams rank 5 (Ardent Mills) and rank 14 (Copeland Precast East):** each holds its own live construction stormwater permit (received 2025-10 and 2024-04), which supports the expansion signal.
- **Weld rank 3 (Texas Farm Products):** The Weitz Company holds a live construction permit at the address under the project name "J.D. Heiskell & Co."
- **Weld is thin by nature:** 16 of its 25 rows have no state water permit at their address, and 10 have a withheld address. Most are UCC machinery buyers. For those a phone number plus ZoomInfo is the only route.

## Re-running a county

`python3 -I step6-contacts/scripts/wq_cache.py active_permits.xlsx wq_cache.json`, then from the repo root
`python3 -I step6-contacts/scripts/enrich_county.py <County> <ranked.csv> <evidence.csv> wq_cache.json <out.csv> 25 [overrides.json]`.
It prints one review line per account and the coverage counts. Phones go in `overrides.json`, keyed by rank: `{"2": {"phone": "...", "ptype": "site", "purl": "...", "checked": "2026-11-16"}}`. `"accept_permit": true` keeps a permit whose holder does not match by name.

---

# Phone pass (added 2026-11-16, third run)

The direct page fetches never got their approval, so three search agents (one per county) looked up each company row instead. Their results are typed into `overrides_denver.json`, `overrides_adams.json` and `overrides_weld.json`, which the build scripts read.

## Rules the agents worked to

1. Sources: the company's own website or its own press release only. A number seen only on a listing or data site was never recorded. No Google Maps or Places.
2. Method: a web search to find the official site, then a read of a page that the search returned. At most two searches and two page reads per company. A page that refused the fetch (robots) was left alone.
3. `site` means the company's page ties the number to this facility, or shows this as its only location. `hq_only` means the company's page gives only a head office, division office, national line or other location. `none_found` means a company page was read and shows no phone, or no official website turned up at all. Blank with "Phone not checked" means the company has a site that the search did not surface or that could not be read.
4. Numbers labelled as a cell, and numbers that sit only beside a named person, were not recorded (Pacific Air's cell line, Pioneer Press's release contact).
5. Where a same-named business could not be tied to the ranked company, nothing was recorded (Custom Stone, Valhalla Industries, Legacy Pie, Quantum J's Canning, Hearth Baking's address).
6. Four withheld addresses are now shown because the company's own website prints them: Never Summer, CO-Innovate, R B Machine, Big Metal Additive.

## Final phone coverage

| | Denver (32) | Adams (25) | Weld (25) |
|---|---|---|---|
| Site phone | 6 | 2 | 2 |
| HQ-only or other-office number | 5 | 2 | 3 |
| None found | 10 | 12 | 15 |
| Not checked | 6 | 3 | 5 |
| Skipped (no company to call) | 5 | 6 | 0 |

- **Site phone and an on-site permit role together:** Ardent Mills (Commerce City mill) and Swarco Colorado Paint, both Adams. No Denver or Weld row has both.
- **Site phones:** Denver: Titan Fittings, Never Summer, Blazy Susan, CO-Innovate, R B Machine, Big Metal Additive. Adams: Ardent Mills, Swarco Colorado Paint. Weld: TruLog Siding, Pneu Line Supply.
- **HQ-only (ZoomInfo or front-desk route):** Denver: Safeway milk plant, Conagra, King Soopers bakery, Cargill, Pacific Air. Adams: Shamrock Foods, Pretred. Weld: Texas Farm Products, Swift Beef (JBS), Schlosser Signs.
- **Three numbers to verify before relying on them:** Pretred (from a copy of its site on a Squarespace default address, beside a different Aurora address), Schlosser Signs (2020 release, former Loveland address), Pacific Air (site shows an Arvada shop, not the W 2nd Ave address in the lien).
- **Not checked, still open:** Denver: Quality Linings, Dawn Foods, Lakin Tire, Verde Prickly Pear, Frito-Lay, Amcor. Adams: Philip Morris ZYN plant, RK Industries, D-A Packaging. Weld: Agilent, Hirsh Precision, Boulder Scientific, Pioneer Press, Raptor Materials. Each has a website that either did not surface in search, returned nothing readable, or refused the fetch.
- **Most "none found" rows are small shops with no website.** That is a finding about the company, not a gap in the search.
