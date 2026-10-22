# Step 4: scrape notes

Run 2026-10-10. Six agents ran in parallel, each following the `datasource-validator-scraper` skill. All eight sources were pulled in full for their scope. Nothing was blocked on a data route. The Accela terms check came back unclear.

## Assumptions (read first)

1. **Private individuals are left out, and the rules are imperfect.** UCC: only debtors typed as organisations were retrieved; pattern rules then removed 8,206 debtor rows where a person's name was typed into the organisation field. An estimated 1,000 to 1,500 rows (about 0.5%) may still be an individual. The column `debtor_name_has_entity_token` = N marks the 12,289 rows with no business word, so Step 5 can drop them for zero risk. Water permits: 54 rows left out where the permittee is the contact person's own name. Denver permits: 30 contractor names that look like individuals were blanked on 105 rows (rows kept).
2. **UCC liens.** Hospital liens are left out entirely (they are records about patients). Other statutory liens are kept with the free text withheld, because it names people, injuries and home addresses. This goes beyond the brief. Needs Matthew's confirmation.
3. **UCC amendments inherit from the original filing.** Continuations and terminations carry no debtor or collateral of their own, so those fields come from the master filing. Columns `debtor_source`, `collateral_source` and `secured_party_source` say which.
4. **Flag word lists were widened from the brief's examples.** UCC and business registration lists are in their cards. Business registrations also carry `flag_narrow` for Step 3's original eight-word list. Bare "press" was not used for UCC. Fixture boilerplate (boiler, furnace and similar inside real-estate fixture language) is ignored.
5. **"Company-named facility" (water permits) is a word-list rule** defined in this run: a business or plant word in the facility name, and no housing, road or utility word. It is loose on "Facility" and "Plant".
6. **Denver permit location, neighborhood and zoning are mostly joined in**, not native. 53% of permits have no point or neighborhood in the layer, and the layer has no zoning field. Values come from the assessor parcel layer and the zoning and neighborhood polygons, by schedule number. Zoning is today's zoning, not zoning on the record date.
7. **APCD has no date cut.** The whole feed is kept, with `in_date_scope` = N on the 472 rows received before 2024. Oil and gas is classed mainly by an operator-name list built from the feed.
8. **OEDIT text is paraphrased.** The site blocks shell requests, so pages were read through the web fetch tool, which summarises. Numbers were re-checked on 10 of 29 months and agreed. Descriptions are not verbatim. Code names were not decoded.
9. **OEDIT "every row is Y" includes non-industrial items.** 39 rows come from minutes (Enterprise Zone projects, film credits, tourism). Filter on `source_kind` or `program` downstream.
10. **Mile High CRE has no terms page.** robots.txt allows everything. That was read as no prohibition. Only headline, short excerpt and extracted facts are stored, never article bodies. Company names are a headline-pattern guess and are 80% blank.
11. **Business registration addresses are the current principal office**, not the address at registration. Home-as-office addresses of small LLCs are kept as public business addresses.
12. **Ground-truth corrections from Step 3 are still not applied.** Nothing in this step depends on them.

## Results at a glance

| Source | File | Rows | Source's own count | Flagged Y | Date range |
|---|---|---|---|---|---|
| Colorado UCC filings | scrape_ucc_filings.csv | 239,822 (195,617 filings) | 348,510 filings fetched; 152,825 had no organisation debtor | 901 | 2024-01-01 to 2026-10-08 |
| Colorado business registrations | scrape_business_registrations.csv | 515,382 | 515,382 | 2,211 (1,217 on the narrow list) | 2024-01-01 to 2026-11-01 |
| Denver commercial construction permits | scrape_denver_commercial_permits.csv | 6,108 | 6,108 | 509 | 2024-01-02 to 2026-10-07 |
| Denver concept and site plans | scrape_denver_site_plans.csv | 1,348 | 1,348 | 1,348 | 2024-01-03 to 2026-10-08 |
| OEDIT EDC approvals | scrape_oedit_approvals.csv | 139 | 96 code-named projects, in line with Step 3's rate | 139 | 2024-01-18 to 2026-09-17 |
| State water permits (WQCD) | scrape_state_water_permits.csv | 6,687 | 6,741 in scope, minus 54 individuals | 2,893 | 2024-01-02 to 2026-08-06 |
| APCD air permit status | scrape_apcd_permit_status.csv | 1,995 | 1,995 | 1,064 | 2009-07-23 to 2026-09-11 |
| Mile High CRE | scrape_mile_high_cre.csv | 1,957 | 1,957 | 160 | 2024-01-02 to 2026-10-08 |
| **All sources** | scrape_flagged.csv | | | **9,225** | |

Checked after the agents finished: every file starts with the exact 17 shared columns, `flag` is only Y or N, no description exceeds 500 characters, and row counts match the agents' reports.

## Things that will bite Step 5

- **Flag volume is uneven.** Water permits (2,893) and Denver site plans (1,348) are 46% of the flagged file. The 5-acre rule alone flags 1,711 water rows, mostly housing, pipelines and highways.
- **Denver layers carry no description.** The permit layer has no work description and the site plan layer has no project name or applicant. Those rows are an address, a class, a valuation and a contractor. The parcel owner name was deliberately not retrieved.
- **DIA is 194 of the 509 flagged Denver permits**, mostly terminal tenant work.
- **Denver permit layer holds issued permits only**, so the last two to three months are undercounted.
- **UCC noise:** about 12,300 SBA continuation filings in May to July 2025. Remaining false positives in flagged rows include paving rollers ("pneumatic"), Doosan forklifts and dry-cleaner boilers. Flag matching ran on full collateral text, so the word may sit past the 500-character cut.
- **Business registrations:** only 24% of foreign entities show a Colorado address. February 2026 has about 1,000 bulk filings through one registered agent. No dissolution date exists in the dataset, only current status.
- **APCD county is wrong on 46 rows** (company office address in place of the site). The AIRS ID prefix is more reliable. `permit_issued_on` is an old original issue date, not the current action.
- **OEDIT:** one project often appears under two code names (one per programme). Do not sum jobs across them. The `notes` column marks these.
- **Water permits:** a received date is not always a first application (311 rows are renewals or modifications). For construction rows the permittee is usually the contractor and the facility is often a code name.
- **No shared id between sources.** Joins go by normalised name and address.

---

# Source cards

### Colorado UCC filings
**Source:** Colorado Department of State UCC data on the Colorado Information Marketplace (data.colorado.gov, Socrata). Four tables, confirmed from each table's `/api/views/<id>.json` metadata: `wffy-3uut` = filing, `8upq-58vz` = debtor, `4am6-w6u4` = collateral, `ap62-sav4` = secured party. They join on `fileid`. Route used: documented SODA API, CSV endpoint, keyset paging on each table's id column, 50,000 rows a page, 1.2 s pause, user agent `step4-research-pull/1.0`. A bulk export (`/api/views/<id>/rows.csv`) exists but cannot leave out personal columns or individual rows, so the API with `$select` and `$where` was the cheapest route that respects the personal-data rule.
**Verdict:** pass
**Terms and robots:** robots.txt (read 2026-10-10) sets `Crawl-delay: 1` and disallows faceted `/browse` queries, `/OData.svc/`, `/api/odata/`, `/login`, `/tiles/` and a few others. `/resource/` and `/api/views/` are not disallowed. Terms of Service at data.colorado.gov/terms: data is provided with no warranty and used at own risk; applications that use the data must carry the State's disclaimer text ("The data made available here has been modified for use from its original source, which is the State of Colorado. ..."); the State may change or discontinue feeds. No ban on automated access. Dataset licence in the metadata: Public Domain. Nothing behind a login was touched.
**Rows:** 239,822 rows written, covering 195,617 filings. The source's own count for filingdate >= 2024-01-01 is 348,510 filing rows, and all 348,510 were fetched (the whole filing table, 2,601,911 rows, matches `count(*)`). Of those, 152,825 were left out because they have no organisation debtor (84,107 initial filings, 68,500 amendments, 218 corrections), and 68 are repeated filing numbers in the source. Supporting tables also match their `count(*)`: organisation debtors 956,150, organisation secured parties 2,045,451, collateral 1,709,826. The API has no join, so the 195,617 figure cannot be checked against a single source count. Step 3's estimate of about 2,800 organisation-debtor initial filings a month compares with 3,130 a month here (103,270 initial UCC financing statement rows over 33 months).
**Date range:** 2024-01-01 to 2026-10-08. No monthly gaps. Lowest month 4,779 filings (2025-02). May to July 2025 are high (11,110, 11,873 and 8,769 filings) because the U.S. Small Business Administration filed about 12,300 continuations in May and June 2025 alone (2020 pandemic loans reaching their five-year mark). That is real, not a paging fault.
**Flagged:** 901 rows flagged Y, all on initial UCC financing statements (about 27 a month). By the first word named in flag_rule: cnc 189, compressor 156, conveyor 104, boiler 42, robot 41, machining center 40, lathe 33, pneumatic 33, haas 29, chiller 22, trumpf 22, welder 20, milling machine 17, press brake 17, doosan 17, furnace 11, okuma 10, injection mold 10, bottling 10, laser cutter 10, packaging machine 9, dmg mori 8, mazak 6, atlas copco 5, paint booth 5, plasma cutter 4, ingersoll rand 4, amada 4, compressed air 3, waterjet 3, then ones and twos. The full per-word table (rows, first, only) is in `summary_ucc_filings.md`. Any-position counts worth knowing: compressor 158, atlas copco 23, sullair 10, ingersoll rand 6, kaeser 4, gardner denver 2, quincy 1. Bare `press` was not used at all (only press brake, stamping press, hydraulic press, punch press), so it flags 0 rows on its own.
**Null rates:** company_name 0%, site_address 0.01%, record_date 0%. Also: description 15.1% blank (the filing has no collateral row, usually because the collateral is in an attachment the dataset does not carry), secured_party 9.8% blank (individual or missing secured party).
**Duplicates:** 20,287 record_ids appear on more than one row (44,205 extra rows). All genuine: a filing with several organisation debtors gets one row per debtor, numbered by `debtor_seq`. The pair (record_id, debtor_seq) is unique, 0 duplicates. The source itself repeats 68 filing rows (same filing number on two fileids); those were skipped. Not a paging bug: page totals equal the source counts.
**Fields:** secured_party (organisation names, joined with "; ", cut at 300 characters), debtor_state, filing_type_raw (transaction type | filing type | document type), debtor_seq, transaction_type, master_document_id (the original file number an amendment belongs to), lapse_date, financial_statement_type, fileid, debtor_country, debtor_org_type, debtor_jurisdiction, debtor_description, debtor_record_status, debtor_source, collateral_source, secured_party_source (own = from this filing; master = inherited from the original filing), collateral_category, collateral_county (the county the collateral table gives for farm products; it is not the debtor's county, so `county` is left blank), collateral_text_len, boilerplate_suppressed, debtor_name_has_entity_token.
**Join key:** debtor organisation name plus address, city, state and zip. Names are free text as typed by the filer (mixed case, punctuation, "Inc" and "Inc." variants), so matching needs normalising. There is no entity id that links to the business registry (`organizationid` is optional and mostly empty). 87.8% of rows have a Colorado debtor address. Amendments link to their original through master_document_id.
**Refresh:** `python3 pull_ucc_filings.py` (fetch then build) or `--build` to rebuild from the cache. The cache resumes from the last id, so a rerun fetches only new rows, but it will not see changes to old rows; delete `raw/ucc_*` for a clean pull (about 15 minutes, 1.2 GB of raw pages). The source is updated often (latest filing date was two days before the pull). Weekly or monthly is enough.
**Gotchas:**
- Amendments, continuations and terminations carry no debtor, collateral or secured party rows of their own unless they change them. They inherit from the original filing through master_document_id. That forced a pull of the whole filing, organisation debtor, organisation secured party and collateral tables, not only 2024 onward.
- The debtor table has no person or organisation marker other than which name field is filled, and some filers type a person's name into the organisation field (sovereign-citizen style filings, sole proprietors, practitioners). Pattern rules left out 8,206 such debtor rows (counts per rule are in the summary; an amendment's inherited debtor is counted once per amendment). The rules are not complete: in a sample of rows with no business word in the name, roughly 1 in 8 still looked like a person, which suggests on the order of 1,000 to 1,500 rows (about 0.5%) may still be an individual. The column `debtor_name_has_entity_token` = N marks the 12,289 rows where no business word was found, so Step 5 can drop them all if zero risk is wanted.
- The exclusion rules will also have removed some real businesses that trade under a person's name (for example a name of the form given name plus surname with no business word).
- Collateral free text on hospital liens and "other statutory" liens names patients, injuries and home addresses. Hospital lien filings were left out entirely (377 debtor rows). For other statutory liens (15,163 rows) the free text is withheld and the description says so. Social-security-number patterns in any collateral text are replaced with "[redacted]".
- Collateral text on ordinary UCC filings can still mention a person (a guarantor, a signer). It was not scanned for names.
- Soft words boiler, furnace, chiller, compressor, conveyor and pneumatic are ignored when the text also has two or more real-estate fixture markers (plumbing, elevators, carpet, air conditioning and so on). That suppressed 35 word hits; they are listed in `boilerplate_suppressed`.
- Known false positives that remain: "pneumatic roller" (paving equipment), Doosan forklifts and excavators, "bottling" inside a debtor's own name, boilers at dry cleaners, conveyors on aggregate and farm equipment. "Quincy" only counts when "compressor", "air" or a Quincy model prefix follows within 60 characters, because Quincy Ave is a Denver-area street (88 rows mention it).
- Flags are thin because much collateral text is "all assets" wording or sits in attachments. 15.2% of initial UCC financing statements with an organisation debtor have no collateral text at all.
- Matching runs on the full collateral text; `description` is cut at 500 characters, so a flagged word may not be visible in the description.
- The source filing table is not strictly unique on fileid or on filing number (68 repeats in scope).
**Assumptions:**
- Organisation debtor = `organizationname` filled and `lastname` and `firstname` both empty. No row has both an organisation name and a last name. Individual debtor rows were never requested, and no name fields were in the `$select`.
- Secured parties: same rule; secured party addresses were not requested. A filing whose secured parties are all individuals has a blank secured_party.
- record_id = `transactionid` (the Secretary of State's filing number), record_type = `documenttype`.
- For an amendment, debtors are the organisation debtors on its own fileid if it has any, otherwise those on the original filing. Debtor rows with action "delete only" are ignored; debtors later made inactive are kept, with debtor_record_status showing it.
- Flag = transaction type "Initial Filing" plus a word match in the collateral category or free text. Up to three matched words are listed in flag_rule in list order.
- Repeated debtor name plus address within one filing is written once.
- Correction and filing-officer-correction documents are kept as in-scope filing types.
**Not pulled:** nothing missing for 2024-01-01 to 2026-10-08. By design: individual debtors, hospital lien filings, probable individuals in the organisation field, secured party addresses and individual secured party names. Attachment images are not in the dataset.


---

### Colorado business registrations
**Source:** Business Entities in Colorado, dataset `4ykn-tg5h`, Colorado Department of State on data.colorado.gov (Socrata). Route used: documented SODA API, CSV endpoint, `$select` of 13 columns, `$where entityformdate >= '2024-01-01'`, keyset paging on `entityid`, 50,000 rows a page, 1.2 s pause, user agent `step4-research-pull/1.0`. The bulk export of the whole table was not used because it would bring 3.1 million rows and the registered agents' personal names and addresses.
**Verdict:** pass
**Terms and robots:** same portal as the UCC card. robots.txt: `Crawl-delay: 1`; `/resource/` and `/api/views/` not disallowed. Terms of Service (data.colorado.gov/terms): no warranty, use at own risk, applications using the data must show the State's disclaimer, feeds may change. Dataset licence: Public Domain.
**Rows:** 515,382 written. Source `count(*)` for the same filter: 515,382. No entity has a blank formation date. Step 3 expected about 20,000 a month; the real figure is about 15,500 a month (range 12,764 to 21,315).
**Date range:** 2024-01-01 to 2026-11-01. No monthly gaps (October 2026 is a part month, 4,361 rows). One row is dated in the future: entity 20268078805, a domestic LLC with formation date 2026-11-01, which is a delayed effective date in the source. It was kept as the source gives it.
**Flagged:** 2,211 rows flagged Y on the wide word list (about 67 a month). `flag_narrow` = Y on 1,217 rows (about 37 a month, in line with Step 3's 40). Rows per matched word, wide list, a row with several words counted under each: technologies 385, energy 374, systems 261, solar 198, technology 164, industries 105, industrial 86, space 59, processing 52, manufacturing 44, food 41, metal 41, pharma 34, steel 33, materials 32, foods 25, precision 25, concrete 24, bioscience 22, coatings 20, robotics 20, aerospace 19, automation 19, chemical 17, beverage 15, packaging 14, electronics 14, fabrication 14, tool 13, mill 12, brewing 10, forge 10, machine 9, plastics 8, distilling 8, foundry 7, lumber 6, distillery 5, brewery 3, biotech 3, composites 3, mfg 3, battery 2, semiconductor 2, polymer 1, manufacturer 1, fabricators 1. Monthly counts are in `summary_business_registrations.md`.
**Null rates:** company_name 0%, site_address 0.83%, record_date 0%. City and zip 0.83% blank.
**Duplicates:** 0 on record_id.
**Fields:** entity_status, entity_type, jurisdiction_of_formation, principal_state, principal_country, is_foreign, flag_narrow, agent_organization_name. The dataset has no dissolution, withdrawal or status-change date, only the current status, so the status is kept and no date is given.
**Join key:** entity name plus principal office address, city, state and zip. entityid is the Secretary of State's id and is stable, but nothing in the UCC tables carries it reliably. Names are clean (official registered names).
**Refresh:** `python3 pull_business_registrations.py` (fetch then build) or `--build`. About one minute for a full pull (79 MB raw). Because status and address are current values, a clean pull (delete `raw/biz/`) is better than an incremental one. Monthly is enough.
**Gotchas:**
- The address is the CURRENT principal office, not the address at registration. Status is also current.
- Many small LLCs give a home as the principal office. It is the entity's public business address and was kept. This is for Matthew to decide: if home addresses of small domestic LLCs should not be held, drop site_address for domestic rows, or keep only foreign and flagged rows.
- Foreign entities: only 24% (8,805 of 36,279) have a Colorado principal address. The rest show an out-of-state head office, so the row does not say where in Colorado the company will operate.
- February to September 2026 show more foreign registrations than before (1,165 to 2,187 a month against about 950 earlier). In February 2026 about 1,000 of the 2,187 came through one agent, Colorado Registered Agents Inc. That looks like bulk filings by a registered-agent service, not an industrial wave.
- Wide-list words such as technologies, systems, energy, solar and space pull in software, consulting, rooftop solar installers and property names. Expect low precision; the flag is a net, not a verdict.
- 11 rows have a foreign entity type but jurisdiction CO. They count as foreign because the rule uses the type prefix.
**Assumptions:**
- Foreign = entity type starts with "F" (FLLC, FPC, FNC, FO, FLP, FLLP, FLLLP, FCOOP, FLCA, FLPA). Jurisdiction of formation agrees on all but 11 rows.
- record_date = `entityformdate`, taken as the date formed in or registered with Colorado. For foreign entities this behaves as the Colorado registration date (the dates are all recent).
- Word matching uses word boundaries, is case-insensitive, and allows simple plurals (machine/machines, metal/metals, tool/tools/tooling, mill/mills/milling, pharma/pharmaceutical, biotech/biotechnology, forge/forging and similar). Up to three matched words are listed in flag_rule in list order.
- Narrow list = manufacturing, industries, technologies, energy, foods, brewing, aerospace, systems, exact words.
- The dataset holds entities only. Trade names and sole-proprietor records are a separate dataset and were not touched, so no entity type was left out. Entity types GP (general partnership, 111 rows) and UNA (unincorporated nonprofit association, 39 rows) were kept as entities.
- Agent first, middle and last name, suffix and all agent addresses were never requested. Mailing address was not requested either. The agent organisation name is kept.
- source_url is the SODA query for the entity id.
**Not pulled:** nothing missing for 2024-01-01 onward. By design: registered agent personal names and addresses, mailing addresses.


---

### Denver commercial construction permits
**Source:** City and County of Denver open data layer "Commercial Construction Permits" (a daily extract of COMMCON permits from the City's Accela database). `https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_DEV_COMMERCIALCONSTPERMIT_P/FeatureServer/317`. Route: the documented ArcGIS REST query API, paged by OBJECTID, 1,000 rows a page (layer maximum 2,000), 7 requests. A bulk file download from the catalog page on denvergov.org was not used because that host refuses automated fetches; the API is the layer's own published interface and returns the same data. Three reference layers on the same host were joined in: zoning polygons (`ODC_ZONE_ZONING_A/FeatureServer/209`, 3,777 polygons), statistical neighborhoods (`ODC_ADMN_NEIGHBORHOOD_A/FeatureServer/13`, 78 polygons) and assessor parcels (`ODC_PROP_PARCELS_A/FeatureServer/245`, looked up by schedule number, owner fields not requested).
**Verdict:** pass, with one structural limit: no owner or tenant and no work description, so the only company on a row is the contractor.
**Terms and robots:** `services1.arcgis.com/robots.txt` does not exist (HTTP 403 "Invalid URL"), so no crawl rules are stated. The ArcGIS item (id 4e2cf20443e14710bbb4311126a4362c) is shared "public" and its licence field is a "USE CONSTRAINTS" liability disclaimer: data provided as is, no warranty, used at the user's sole risk, user indemnifies the City, "NOT FOR ENGINEERING PURPOSES". It sets no limit on automated access, bulk download or commercial reuse. The Denver Open Data Catalog licence page on denvergov.org could not be read (the fetch tool was refused by robots rules on that host, and no other route was tried); from memory only, the catalog has historically been CC BY 3.0, which would require attribution to the City. Requests were paced at one per second with user agent `step4-research-pull/1.0`.
**Rows:** 6,108 written; the source's own `returnCountOnly` for `DATE_RECEIVED >= 2024-01-01` is 6,108. No rows left out.
**Date range:** 2024-01-02 to 2026-10-07 (date received). Every month present, 151 to 291 a month through July 2026 (about 185 a month, matching Step 3's 190). August 2026 (100), September 2026 (78) and October 2026 (11) are low because the layer only carries permits that have been issued: recently received applications appear once they are issued. No future dates.
**Flagged:** 509 Y of 6,108. `valuation >= 250k + industrial zoning`: 133 (I-B 40, I-A 24, I-MX-8 23, I-MX-5 15, M-IMX-12 15, I-MX-3 5, I-MX-12 4, I-0 4, M-IMX-8 2, M-IMX-5 1). `valuation >= 250k + industrial neighborhood`: 376 (DIA 194, Gateway - Green Valley Ranch 39, Five Points 36, Sun Valley 25, Central Park 18, Lincoln Park 13, Elyria Swansea 10, Globeville 8, Montbello 6, Northeast Park Hill 4, Baker 4, Regis 3, Ruby Hill 3, Sunnyside 2, Clayton 2, College View - South Platte 2, Athmar Park 2, Cole 2, Overland 2, Chaffee Park 1). Zoning is named first when both conditions hold; every industrially zoned permit over the threshold also sat in a listed neighborhood, so the neighborhood rule alone would flag the same 509. Final neighborhood list (layer spelling): Elyria Swansea, Globeville, Northeast Park Hill, Montbello, Central Park, DIA, Gateway - Green Valley Ranch, Sun Valley, Valverde, Athmar Park, Baker, Overland, College View - South Platte, Ruby Hill, Lincoln Park, Five Points, Sunnyside, Chaffee Park, Regis, Cole, Clayton ("Stapleton" is also accepted but does not occur). Industrial zoning means zone type Industrial or Industrial Mixed Use, or district starting I- or M-IMX. By class the flagged rows are 305 alteration/tenant finish, 117 new building, 24 repair/replace, 22 non-building structure, 20 special event, 21 other.
**Null rates:** company_name 1.8% (112 rows: 7 with no contractor in the source, 105 blanked as private individuals), site_address 0.1%, record_date 0%. Also: description 100% blank (the layer has no work description field), zip 31.0%, valuation blank 0.1% and zero on a further 28%, neighborhood 4.0%, zone_district 3.8%, latitude/longitude 3.8%.
**Duplicates:** 0 on record_id.
**Fields:** valuation, date_issued, final_date, cancel_date, class, contractor, neighborhood, neighborhood_source, zone_district, zone_dist_type, zone_description, zoning_source, industrial_zoning (Y/N), parcel_class (assessor use class, for example INDUSTRIAL-WAREHOUSE), schedule_number, location_detail (building/floor/suite), units, permit_fee, log_number, co_required, date_co_issued, exempt_code, stat_code_1 to 3, latitude, longitude, location_source, parser_version.
**Join key:** site_address (Denver house number, direction, street, type, then unit, with no comma before the unit) and schedule_number (13-digit assessor parcel number, present on all but 2 rows; 2,081 of 2,234 distinct numbers matched the parcel layer). Latitude/longitude on 96%. Contractor name is upper case free text with variants (for example "TURNER CONSTRUCTION CO ATTN: TAX DEPT."). There is no owner or tenant name, so matching to a target company has to go through address or parcel.
**Refresh:** `python3 pull_denver_commercial_permits.py` (about 1 minute; add `--since YYYY-MM-DD` for an incremental pull and de-duplicate on record_id; `--fresh` to ignore the same-day cache). The layer is refreshed daily; weekly or monthly is enough. Re-pull the last 90 days each time because permits appear only when issued and valuation, final date and cancel date change afterwards.
**Gotchas:** (1) 53% of rows (3,254) have no point geometry and no neighborhood in the layer; before July 2025 it is about 85%. The flag rule cannot work from the layer alone, so location, neighborhood and zoning for those rows come from the assessor parcel matched on schedule number (situs point converted from state plane feet in the script). (2) Asking the parcel layer for `returnCentroid` makes each query take 30 to 60 seconds and return 504 and 400 errors; the script asks for attributes only. A GET with 100 schedule numbers is too long (404), so lookups go by POST. (3) Issued permits only, so the latest two months are always undercounted. (4) Valuation is 0 on 28% of rows (airport and fee-exempt work, change of contractor, special events), so those can never flag. (5) DIA is 194 of the 509 flags and is mostly terminal and concourse tenant work, with Hensel Phelps the top contractor overall (327 rows); it will need down-weighting. (6) The layer name says DEV and the layer id (317) could change if the City republishes; the script checks field names and stops on schema drift.
**Assumptions:** dates are stored as midnight UTC and converted in UTC; city and county are set to Denver for every row because the layer is Denver only (a handful of mountain park addresses such as Red Rocks are City property outside the city limits); zip comes from the parcel's situs zip, not the permit; zoning is today's zoning at the point, not zoning on the permit date; a parcel situs point stands in for the permit location where the permit has no point; a contractor is treated as a private individual only when the name is two or three plain words with no business term (30 distinct names, for example "LASTNAME FIRSTNAME M" and "HOME OWNER"), and those rows are kept with the name blanked; `record_type` is the permit class because every permit in the layer is type COMMCON.
**Not pulled:** nothing in scope is missing from the layer for 2024-01-01 to 2026-10-07. Not in this layer at all: permits received but not yet issued, residential permits, and trade permits (mechanical, electrical, plumbing), which sit in Accela and are on hold (see accela_terms.md). Parcel owner names were deliberately not retrieved; they would give a property-owner company name for most rows if Matthew wants them, with individuals filtered out.


---

### Denver concept and site plans
**Source:** City and County of Denver ArcGIS layer "SDPConceptDynamic" (concept reviews and site development plan records from the City's Accela system, published by Community Planning and Development for a public dashboard). `https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/SDPConceptDynamic/FeatureServer/0`. Route: the ArcGIS REST query API, paged by OBJECTID, 2 requests. No bulk download exists for this layer; it is not a catalogued open data set with a download page. Zoning was added by a point-in-polygon join to `ODC_ZONE_ZONING_A/FeatureServer/209` on the same host.
**Verdict:** pass as an early signal of where projects are starting; weak for naming companies, because the layer carries no applicant, owner, project name or description.
**Terms and robots:** `services1.arcgis.com/robots.txt` does not exist (HTTP 403 "Invalid URL"). The ArcGIS item (id ba809992051745918b0e07ecb77ec468) is shared "public", owned by a City staff account rather than the City's main open data account, tagged CPD, described as "Data for making dynamic dashboard with SDP data". Its licence field is the City's standard liability disclaimer (as is, no warranty, sole risk, indemnity, "NOT FOR ENGINEERING PURPOSES") with no limit on automated access or reuse. It is not listed under the Open Data Catalog tag, so the catalog licence may not formally cover it. Denver's website terms could not be read (fetch refused by robots rules on denvergov.org). Paced at one request per second with an identifying user agent.
**Rows:** 1,348 written; the source's own `returnCountOnly` for `FILE_OPEN_DATE >= 2024-01-01` is 1,348.
**Date range:** 2024-01-03 to 2026-10-08 (date opened). Every month present, 26 to 62 a month, about 41 a month (Step 3 saw about 34). No future dates, no gaps.
**Flagged:** 1,348 Y, all under `all concept and site plan applications`. By type: Concept Review 680, SDP Modification 304, Standard SDP 279, SDP Amendment 39, Site Development Plan Review 31, Other 13, Adjacent Jurisdiction Referral 1, Horizontal Infrastructure/Landscape SDP 1. For ranking, the extra column `industrial_zoning` is Y on 164 rows (I-B 43, I-MX-5 29, I-MX-3 23, M-IMX-12 23, I-A 22, I-MX-12 10, M-IMX-5 5, I-MX-8 4, I-2 3, M-IMX-8 2).
**Null rates:** company_name 100% (not carried), site_address 3.8%, record_date 0%. Also: description 100% blank (the NOTES field is empty on every record), zip 36.6%, neighborhood 7.3%, zone_district 7.3%, latitude/longitude 5.4%.
**Duplicates:** 1 record_id appears twice (2026-CONCEPT-0000141, two identical features in the source with different OBJECTIDs). Genuine source duplicate, not a paging bug; both rows kept so the count matches the source.
**Fields:** status, status_date, record_type_group (Concept Plan, Formal SDP, Modification, Amendment), parent_record_id (the PROJMSTR project master number that ties a concept to its later site plans), active_flag, neighborhood, zone_district, zone_dist_type, zone_description, industrial_zoning, latitude, longitude, match_method, match_score (the City's own geocoding method and score), parser_version.
**Join key:** site_address and latitude/longitude. Address format is inconsistent (some with street type, some without, a few blank), and the City's match_score shows which locations are approximate (parcel or site plan centroids). parent_record_id links related applications. The record_id can be looked up by hand in the City's e-permits portal for applicant and project detail; that was not done here.
**Refresh:** `python3 pull_denver_site_plans.py` (a few seconds; `--since` for incremental, `--fresh` to ignore the same-day cache). The layer was last edited 2026-10-09 and appears to update daily. Monthly is enough; re-pull everything each time because status changes on old records.
**Gotchas:** (1) No company and no description: the signal is "a project opened at this address", nothing more. (2) The layer is a staff-owned dashboard feed, not a catalogued open data set, so it can be renamed or withdrawn without notice. (3) Residential and mixed use projects dominate (zone type Commercial Mixed Use 834, Residential 288); industrial zoning is about 12% of rows. (4) Staff contact fields (project manager, phone, email) exist in the layer and were not requested.
**Assumptions:** dates converted in UTC; city set to Denver on every row (the layer has Denver, DENVER or blank) and county to Denver; zip trimmed to five digits; zoning is today's zoning at the point; `record_type` uses APPLICATION_TYPE and the coarser Record_Type is kept as an extra.
**Not pulled:** nothing in scope is missing for 2024-01-03 to 2026-10-08. Applicant, owner and project names are not in this layer; they exist only in Accela, which is on hold.


---

### OEDIT EDC approvals
**Source:** Colorado Office of Economic Development and International Trade, Economic Development Commission (EDC). Monthly posts "<Month> <Year>: EDC Approved Job Growth Incentive Tax Credit and Strategic Fund Projects" at https://oedit.colorado.gov/news/<month>-<year>-edc-approved-job-growth-incentive-tax-credit-and-strategic-fund-projects, plus EDC minutes (published Google Docs linked from https://oedit.colorado.gov/about/colorado-economic-development-commission and its archive page) for months with no post and for special meetings. Access route: WebFetch tool, page by page. No bulk file, API, JSON endpoint or export exists, and shell requests get HTTP 403, so the HTML could not be scripted.
**Verdict:** pass (small, clean, high value), with the caveat that text fields are a model's paraphrase of the page, not verbatim.
**Terms and robots:** robots.txt fetched through WebFetch: Drupal default, disallows /search/, /admin/, /user/ and similar; /news/, /category/ and /about/ are allowed. No terms-of-use page is linked; the footer links a Privacy Notice (read: nothing on automated access or reuse; cites CORA, public records open for inspection) and the state General Notices. 46 OEDIT page fetches and 9 Google Docs fetches in total, sequential.
**Rows:** 139 (100 from posts, 39 from minutes). Posts: 29 of 33 months had a post; 96 project headings, 100 rows after splitting four projects that carry two programmes. This matches the per-page "total projects" count in every month. The source has no overall count to compare with.
**Date range:** 2024-01-18 to 2026-09-17, every month has rows. October 2026 meeting (expected 2026-10-15) had not happened at pull time.
**Flagged:** 139 Y, all under `all EDC approvals`. 39 of these are minutes rows that are mostly not industrial (17 Enterprise Zone contribution projects, 7 film credits, 3 Stanley Film Center amendments and so on); filter on `source_kind` or `program` downstream.
**Null rates:** company_name 0%, site_address 100% (source carries none), record_date 0%. county 32% blank, jobs 32%, incentive_amount 17%, average_wage 35%, capital_investment 90%. Post rows alone: county blank on 12 of 100, and 15 more carry only the wage comparison county.
**Duplicates:** 0 on record_id. Same project can appear twice by design: two programmes in one month (Bobcat, Kiwi, Lattice, Papercrane) or a JGITC name plus a refundable credit name (Kelly/Carbon, Rey/Oxygen, Ladybug/Fluorine, Electron/Neon, Mercury/Sodium, Laser/Magnesium). The `notes` column says so; do not sum jobs across these.
**Fields:** code_name, real_company, program, jobs, average_wage, incentive_amount, capital_investment, other_states_considered, date_basis, source_kind, county_basis, post_date, notes.
**Join key:** code name + county + industry description; no company name (only ProCaps Laboratories is named in a post). Minutes rows carry real organisation names. Join quality to other sources is low until Step 5 decodes the code names.
**Refresh:** monthly, after the third Thursday. See pull_oedit_approvals.md. About 2 fetches a month.
**Gotchas:** WebFetch returns a summary, so descriptions are paraphrased and a field can be missed: the first-pass prompt reported "county not stated" for projects whose only county is the wage comparison county (found on re-fetch in 7 projects). Posts are sometimes dated one or two days before the meeting. The posts print "requested" and "recommended" amounts; they do not always say the final approved figure. Page errors exist (Kiwi per-job figure, Cobra job count, August 2024 post text mentioning the April meeting). Minutes post two to three months late.
**Assumptions:** (1) record_date is the regular meeting date for that month taken from the EDC page and archive lists, date_basis = meeting; the post date is kept in post_date. (2) Every project in a monthly post was approved at that month's regular meeting. (3) county is filled from the page even when it is only the wage benchmark or "under consideration"; county_basis says which. (4) company_name is "Project <heading>" as the page heading gives it. (5) incentive_amount is the "up to" maximum or the recommended award in dollars. (6) For minutes months, only items awarding something to a named project or organisation were kept; removals, policy changes, boundary amendments, suspension exceptions and grant batches with no recipients were left out and are listed in oedit_month_log.csv. One owner-only business (a Rural Jump-Start item) was left out as near-personal. (7) retrieved_at is one timestamp for the session (fetches ran 17:38Z to 17:56Z on 2026-10-10).
**Not pulled:** October 2026 (meeting not yet held). Special meeting 2026-07-27 (agenda only, no minutes). For the 29 post months, items approved at the meeting but not listed in the post (Enterprise Zone, film, Rural Jump-Start, Advanced Industries and similar) were not pulled; they are in the minutes, which exist through June 2026. Four boundary-amendment and similar admin items in the minutes months were left out on purpose.


---

### State water permits (WQCD)

**Source:** Colorado CDPHE Water Quality Control Division, "Active CDPS permits and certifications" spreadsheet. Linked from https://cdphe.colorado.gov/clean-water-active-permits ("This xls file will automatically download to your computer. (as of 08/07/26)"). Google Sheet id `1ZFnnmKQc6zCeiYLcEOcf43cnYb7nwA2Y`. Route used: bulk download, one request to the standard export link `https://docs.google.com/spreadsheets/d/1ZFnnmKQc6zCeiYLcEOcf43cnYb7nwA2Y/export?format=xlsx` (HTTP 200, 26,191,749 bytes, fetched 2026-10-10 17:38 UTC). This is the cheapest route, so no API or scrape was needed. The sheet's query endpoint (gviz) was tried for spot checks only; it exposes just the first 2,621 rows, so it is not a usable pull route.

**Verdict:** pass

**Terms and robots:**
- CDPHE page: no terms, licence or disclaimer attached to the spreadsheet. The agency publishes it for public download. The page points to the records center only for documents not found online. No records request was made.
- `docs.google.com/robots.txt` (saved as `robots_docs_google.txt`): `User-agent: *`, `Crawl-delay: 1`, `Allow: /spreadsheet` (prefix covers `/spreadsheets/d/.../export`), then `Disallow: /`. The export path is allowed. Requests made to docs.google.com: 1 download plus 11 small spot-check queries, at least 1.5 s apart, user agent `step4-research-pull/1.0`.
- `cdphe.colorado.gov/robots.txt` returned HTTP 403 to the shell request (not retried). The page itself was read once through WebFetch. Nothing was scraped from cdphe.colorado.gov.

**Snapshot:** stated on the page as 2026-08-07. Confirmed in the data: latest IssuedDate is 2026-08-06, latest valid received date 2026-08-06. The file is unchanged since Step 3 (same 27,550 rows). docProps created date 2026-08-17. No refresh has been published in the two months since, so 2026-08-07 to 2026-10-10 is not covered by this source.

**Tabs and layout:** one tab, `PermitExtractData`, 27,550 data rows plus one header row, 281 columns (filter range A1:JM27551). Header is row 1, no title rows. Columns: permit block (PermitSector, GeneralPermitType, PermitID, PermitStatus, ApplicationReceivedDate, IssuedDate, EffectiveDate, ExpirationDate, TerminationDate, FeeCategory, Permittee), then about 20 contact blocks of 10 to 11 columns each (Legal, FacilityContact, Billing, DMR, Stormwater, MS4, Biosolids, Engineering, PropertyOwner, Consultant, Environmental, Inspection, Other, Pretreatment, Compliance, Reuse, Operator, CollectionsOperator, Reg85: organization, first name, last name, title, address, phone, email), facility block (FacilityName, address, city, state, zip, county, lat, long, SIC), water block (ImmediateWater, ReceivingWater, StreamSegment, MajorRiverBasin), construction block (SWConstructionActivity, TotalAcres, DisturbedAcres, StartDate, EndDate), PermitSIC1 to 4, ActivityDescription, 12 outfall lat/long pairs, AssociatedPOTW, PreviousPermitID, MajorMinor.

**Rows:** 6,687 written. Source count for the same filter: 6,741 rows in date scope (6,731 with a valid received date from 2024-01-01 to the snapshot, including one stored as text, plus 10 fallback rows; see Assumptions), minus 54 rows left out as private individuals = 6,687. Matches.

**Date range:** 2024-01-02 to 2026-08-06. No empty months. Monthly counts, all permit types: 2024: 209, 199, 199, 211, 346, 605, 468, 191, 195, 207, 131, 175. 2025: 179, 136, 233, 178, 173, 175, 160, 173, 155, 239, 179, 155. 2026: 214, 238, 184, 214, 207, 187, 169, then 3 for 1 to 6 August. The May to July 2024 bump is the industrial stormwater general permit (COR900000) renewal: 172, 449 and 249 re-applications in those months. Construction stormwater (COR400000) alone runs 98 to 185 a month, in line with Step 3's 157 to 186.

**Share by permit type:** COR400000 construction stormwater 4,308 (64.4%); COR900000 industrial stormwater 955 (14.3%); COG080000 construction dewatering 652 (9.8%); CONOX000 no exposure exclusion 356 (5.3%); COG317000 short-term remediation 116 (1.7%); CO individual permit 52 (0.8%); COG604000 hydrostatic testing 38; COE reuse user 37; COPB pretreatment billing 28; COG608000 well development 27; COG500000 sand and gravel 24; R-factor waiver 24; COBMP biosolids user 19; COG591000 domestic 18; COE reuse treater 6; COX631000 5; COG318000 5; COP pretreatment 5; COG641000 4; COG590000 4; one each of COX634000, COG607000, COR070000, COG860000.
Status: Effective 4,696; Terminated 1,559; Admin continued 379; Pending 38; Expired 14; Withdrawn 1. The file does carry terminated permits.

**Flagged:** 2,893 of 6,687 (43.3%).
- Rule 1, disturbed acres >= 5: 1,874 rows.
- Rule 2, manufacturing SIC 2000 to 3999 (any SIC on the row): 656 rows.
- Rule 3, company-named facility: 872 rows.
- Overlap: acres only 1,711; name only 384; SIC only 298; name + SIC 337; acres + name 142; acres + SIC 12; all three 9.
- Rule 1 alone accounts for 1,711 rows, which is 25.6% of all rows and 59% of flagged rows. Of those, 505 are Residential, 360 Commercial, 275 Pipeline, 155 NonStructural, 154 Highway. For reference, rows at other thresholds: >= 10 acres 1,189; >= 20 acres 656; >= 50 acres 252. The rule was not changed.
- Rule 3 word hits: LLC 190, Facility 162, Plant 153, Inc 131, Solar 48, Company 29, Co. 28, Technologies 25, Energy 22, Foods 16, Warehouse 15, Corp 15, Industrial 13, Dairy 11, Logistics 10, Manufacturing 10, Precast 9, Corporation 9, Aerospace 8, Industries 7, Distribution Center 6, Steel 5, Brewery 5, Mfg 4, Mill 4, Fabrication 4, Foundry 3, Pharma 3, Factory 3, Battery 3, Brewing 2, Bottling 2, Data Center 1, Laboratories 1. "Facility" and "Plant" pull in wastewater and water treatment plants, hauling facilities and detention facilities.
- Rule 3 final lists. Company words (whole word, any case): Inc, LLC, Corp, Corporation, Co. (with the period, or a mixed-case "Co" as the last word, so the state code CO does not match), Company, Manufacturing, Mfg, Plant, Facility, Factory, Brewery, Brewing, Distillery, Foods, Dairy, Bottling, Industries, Industrial, Technologies, Aerospace, Semiconductor, Pharma, Mill, Foundry, Fabrication, Steel, Precast, Energy, Solar, Battery, Data Center, Distribution Center, Warehouse, Logistics, Laboratories. Exclusion words (whole word, any case, any one blocks the rule): subdivision(s), filing, homes, residence(s), apartment(s), townhome(s), estates, ranch, village, road, street, highway, interstate, bridge, pipeline, waterline, sewer, school, church, park, trail. "Corporation" and the singular forms were added to the assigned lists. "filing" is matched as a bare word, not only "filing no.".

**Null rates:** company_name 0.0%; site_address 0.9% (58); record_date 0.0%. Others: city 1.2%, county 0.8%, zip 1.6%, sic_code 1.6%, latitude/longitude 0.9%, permittee 0.0%, owner 36.0% (the source only fills it for construction stormwater), operator 98.5%, disturbed_acres 35.6% (construction stormwater only; 4,306 of 4,332 construction rows have it), receiving_water 85.9%, activity_description 82.3%.

**Duplicates:** 0 on record_id (PermitID is unique in the sheet).

**Fields:** permittee, owner (PropertyOwnerOrganization), operator (OperatorOrganization), former_permittee, company_name_basis, permit_sector, disturbed_acres, total_acres, construction_activity, sic_code, sic_description, other_sic_codes, activity_description, permit_status, issued_date, effective_date, expiration_date, termination_date, construction_start_date, construction_end_date, receiving_water, stream_segment, associated_potw, previous_permit_id, major_minor, date_basis, latitude, longitude, snapshot_as_of.

**Join key:** facility name plus site address, city, zip; latitude and longitude on 99% of rows (good for a spatial join to parcels or other permit sources). Permittee and owner names are free text with no entity ID, so name joins need normalisation (for example "Entegris", "Entegris Inc", "Entegris, Inc."). For construction stormwater the permittee is usually the general contractor and the facility name is a project name (for example "Project Manitou", permittee Whiting-Turner), so the end user is often only in `owner` or has to be resolved from the address. `previous_permit_id` links renewals.

**Known Step 3 rows:**
- Entegris: 3 rows in scope. COR900168 (industrial stormwater, 2024-06-06, flagged on SIC 3080), COR424204 (Entegris Gas Main Installation Ph 1, permittee Colorado Springs Utilities, 1.33 acres, not flagged), COR901696 (industrial stormwater, 2025-03-28, no SIC in the sheet, not flagged). The plant construction certification COR421280 ("Entegris, Inc.", permittee The Weitz Company) was received 2023-09-20, so it is before the 2024 cut and not in the output.
- Pepsi / CB Manufacturing: 3 rows in scope. COR901708 (Pepsi Beverages North America - High Point, permittee CB Manufacturing Company, Inc, 2025-10-07, flagged SIC 2086), COR900475 (Pepsi Cola Bottling Group, flagged), COR427808 (Project Mustang - E 69th Avenue, owner match on Pepsi, 4.84 acres, not flagged). The PepsiCo Highpoint construction rows (COR418089, COG080583, Gray Construction) were received in 2022 and are not in the output.
- Sphere: 0 rows in scope. The only match in the whole sheet is COR420530 "Sphere Renewables", received 2023-05-31, before the cut.
- Heiskell / TFP: 1 row in scope. COR423433 "J.D. Heiskell & Co.", permittee The Weitz Company, Platteville, received 2024-04-01, 6.33 acres, SIC 3999, flagged on all three rules. No facility or permittee name contains "TFP".
- Manitou: 6 rows in scope. COR430035 "Project Manitou", permittee The Whiting-Turner Contracting Company, Colorado Springs, received 2026-03-11, 58 acres, SIC 2086, flagged on acres and SIC. The other five are City of Manitou Springs public works.

**Spot check:** 92 in-scope rows that the live sheet's query endpoint exposes (reuse, individual, domestic, pretreatment types) were compared field by field (received date, permittee, status, facility name, city) with the output: 0 mismatches, 0 missing. Eight further rows were checked by hand against the downloaded workbook.

**Refresh:** `python3 -I pull_state_water_permits.py --refresh` (one request, about one minute to parse). `--since YYYY-MM-DD` is the date cursor. Only worth rerunning when the "as of" date on the CDPHE page changes. It has not changed in two months, so check monthly. Raw download is cached in `download/`; `qa_state_water_permits.json` records parser version, file hash and counters; `qa_state_water_permits.py` reruns the QA.

**Gotchas:**
- The sheet is hand-maintained and some rows are column-shifted (mostly COPB pretreatment and COE reuse rows): contact names, phones and emails sit in facility, water and construction columns. The parser validates each field by shape (county against the 64 Colorado counties, 5-digit zip, lat/long inside Colorado, 4-digit SIC, numeric acres) and blanks what fails: 35 county values, 31 lat/long values, 6 addresses in scope. A header change stops the script with a schema-drift error.
- 27 COPB rows have no facility name; company_name is then the permittee (`company_name_basis` says so) and the treatment works name from the county column goes to `associated_potw`. In 16 COPB rows the SIC code sits in the state column and is read from there (this is what flags Avery Brewing, SIC 2082).
- Some construction start and end dates are stored as Excel serial numbers and are converted.
- A received date is not always a first application. 311 rows have a received date more than a year after the issue date (renewals and modifications of older permits). Use `issued_date` and `previous_permit_id` to tell new from renewed.
- `sic_code` is FacilitySICCode when valid, otherwise the first valid PermitSIC. A few rows carry different facility and permit SICs (Entegris COR900168: facility 1311, permit 3080); rule 2 checks all of them and `other_sic_codes` keeps the rest.
- Construction stormwater SIC codes are mostly contractor codes (15xx, 16xx), so rule 2 seldom fires there (46 rows).
- "Active permits" is a misnomer: 61% of the sheet is terminated permits.

**Assumptions:**
- Date fallback: 10 rows in scope had no usable received date: 8 had the text `2025-12-80`, 1 had a future received date (2026-10-25, COPB90813) and 1 was blank. They use the issue date, `date_type` = approved, with the reason in `date_basis`. One of the 10 was then left out as a private individual, so 9 are in the output. No row needed the effective date. One received date stored as the text `4/8/2024` parses cleanly and is treated as received. 983 sheet rows have no valid received date in total; nearly all are biosolids users with older issue dates and fall outside the window. 37 rows have no date of any kind and are left out.
- Personal data rule: a row is left out when the permittee text is the legal contact's own first and last name (either order), or the same first and last name with a middle name or initial added and no business word. 54 rows left out (51 construction stormwater, 2 R-factor waivers, 1 individual permit; 43 are Residential activity, mostly single lots, though a few are large: 82, 25 and 14 acres). The same test blanks `owner` on 27 rows and `operator` on 1 row where the organisation field holds the contact person's name. Contact names were compared in memory and never written. 5 rows were kept as ambiguous (all permittee "Taylor Kohrs", a contractor's trade name). No contact name, phone, email, title or mailing address column is in the output. Facility names that contain a person's name with a company permittee (for example "Smith Residence" built by an LLC) are kept.
- `sic_description` is not in the sheet. It is the standard SIC 2-digit major group title, derived from `sic_code` by a lookup table in the script.
- `source_url` is the sheet's view URL for every row; the sheet has no per-row link.
- `retrieved_at` is the download time.
- Rule 3 is applied to the facility name, or to the permittee where the facility name is blank (27 COPB rows; the flag_rule text says so).
- `record_type` is the sheet's GeneralPermitType text; only the case of "COE-Reuse User/Treater" was normalised.

**Not pulled:**
- Anything after the 2026-08-07 snapshot (2026-08-07 to 2026-10-10): the agency has not republished.
- 3,192 rows received before 2024-01-01 but issued or effective in 2024 or later. 3,050 are construction stormwater certifications re-issued on 2024-04-01 when the general permit renewed, with received dates from 2016 to 2023. These are out of scope under the received-date rule; they include the 2023 Entegris and Sphere Renewables rows.
- 54 private-individual rows (IDs listed in `qa_state_water_permits.json`).
- Contact blocks and outfall coordinates.


---

### APCD air permit status

**Source:** Colorado Department of Public Health and Environment, Air Pollution Control Division, "Air permit status" page, https://apcdweb.dphe.state.co.us/PermitStatus/ . Access route: the undocumented JSON endpoint the page's own script calls, `https://apcdweb.dphe.state.co.us/PermitStatusAPI/api/vResultsAPIs`. One GET returns the whole table (1,172,102 bytes, 1,995 rows) with no paging and no parameters. Cheaper routes did not apply: there is no bulk download and no documented API; the page has no export button. Fetched once on 2026-10-10 17:38:39 UTC with user agent `step4-research-pull/1.0`; HTTP 200 on the first try, no retry needed. The companion counties list (`.../api/vResultsCounties`) returned HTTP 500 ("An error has occurred") on one try; it was not needed and was not retried.

**Verdict:** pass.

**Terms and robots:** `https://apcdweb.dphe.state.co.us/robots.txt` returns 404 (no robots file), same as in Step 3. The public page was fetched once and read in full: it carries no terms of use, disclaimer, login or data-use language. Its only text about the data is "Your permit application will appear if it underwent any processing in the last six months", plus an invitation to contact the permit engineer, and a "(c) 2018 State of Colorado" footer. The CDPHE data access and APENs pages link to no terms for this tool. The State's General Notices page (colorado.gov/general-notices) is a privacy policy and says nothing on automated access or reuse. Nothing read prohibits this use; nothing explicitly grants it either.

**Rows:** 1,995 written against a feed length of 1,995 (the feed is the source's own count; there is no filter). Step 3 saw 2,002 rows on 2026-10-09; the difference of 7 is the six-month window rolling.

**Date range:** record_date (Received) 2009-07-23 to 2026-09-11. No future dates. By year: 2009: 1, 2010: 2, 2011: 3, 2013: 3, 2015: 4, 2017: 1, 2018: 5, 2019: 13, 2020: 24, 2021: 112, 2022: 141, 2023: 163, 2024: 257, 2025: 678, 2026: 588. `in_date_scope` = Y on 1,523 rows (received 2024-01-01 or later), N on 472. Last 18 months by month: 2025-04: 69, 05: 79, 06: 64, 07: 31, 08: 60, 09: 58, 10: 67, 11: 39, 12: 52, 2026-01: 51, 02: 60, 03: 82, 04: 67, 05: 92, 06: 75, 07: 87, 08: 53, 09: 21. No empty month. September 2026 is partial (latest received date is 2026-09-11, a month before the pull, so there is an entry lag of roughly four weeks). These counts are NOT the true number of applications received per month: they are only the applications that were still being processed in the last six months, so older months are thinned.

**Flagged:** 1,064 rows flagged Y, all under the single rule `not oil and gas`; 931 flagged N (oil and gas). In date scope: 787 Y, 736 N. Sector tag: oil_and_gas 931 (46.7%), other 541 (27.1%), aggregate_concrete_asphalt 337 (16.9%), fuel_retail 186 (9.3%). Step 3's keyword classing gave 49% / 29% / 15% / 7% on 2,002 rows. Differences: (1) oil and gas is 2 points lower because this rule works mainly from an operator-name list built from the feed and drops loose keywords that misfired (for example "production facility" hit an aggregates quarry and a biochar plant, "separator" hit a scrap-metal yard), and it excludes dairy biogas / renewable natural gas, landfill gas and helium; (2) fuel retail is 2 points higher because it includes named chains whose rows carry no fuel keyword, bare "USTs" rows, and bulk fuel distribution plants; (3) aggregate is 2 points higher because of a longer company-name list (Holcim, Oldcastle, Martin Marietta, Raptor Materials and so on match by name even when the row is just a generator).

Hand check of a seeded random 60 rows (seed 20261010): 30 flagged Y, 0 were oil and gas (0/30 error); 30 flagged N, all 30 were oil and gas (0/30 error). A 0 in 30 result only bounds the error rate at roughly under 10%, it does not prove zero. Known judgment calls outside that sample are listed under Assumptions.

**Null rates:** company_name 0.0%; site_address 2.7% (53 rows: 25 with a blank facility string, 28 where the address in the feed is an out-of-state company mailing address and was deliberately not used as a site); record_date 0.0%. Also: county 6.9% blank (portable sources, out-of-state rows, blank facility), zip 6.5% blank, city 100% blank (the feed has no city), airs_id 0.05% (1 row), description 0.25% (5 rows).

**Duplicates:** 0 on record_id. record_id is `PER_ID-POI_ID-PLA_ID`. PER_ID alone (and the permit number) repeats on 2 permits, each listed against two facilities: 95MF1040 (Colowyo Coal, two mine sites) and 14DE1486 (one multi-point permit shown under both United Airlines and Frontier Airlines at DIA). These are genuine, not a paging bug, so the facility id PLA_ID was added to the key. POI_ID is 0 on every row.

**Fields:** facility_name, facility_raw, facility_parse, permit_number, airs_id, service_type_code (SER_TYPE), permit_issued_on, in_date_scope, sector, sector_rule, PER_ID, POI_ID, PLA_ID, Address_ID, Own_ID, parser_version. Dropped on purpose: engineer, engineerEmail, engineerPhone (staff contact data; checked that no email string appears in the CSV) and Status (blank on all rows). The raw JSON cache, which still contains the engineer fields, stays in this agent directory only and will not be saved to the project.

serviceType counts: To Be Determined 606; Final Approval 469; FA, Modification 238; Permit Exempt, APEN Only 220; Initial Application 189; Permit Exempt, APEN Exempt 99; IA, Modification 87; FA, Transfer Plant Ownership 51; APEN ONLY, Transfer of Ownersh 14; IA, Transfer Plant Ownership 11; FA, Company Name Change 11.

Facility string parse: 1,782 rows (89.3%) parsed cleanly as exactly name, address, county, state, zip. 160 rows (8.0%) had extra commas in the name or address and were resolved by rule (49 by the 40-character name width, 104 by an address-start pattern, 7 by last comma); all 160 were read by eye and look right. 28 rows (1.4%) carry an out-of-state mailing address (name kept, address left blank). 25 rows (1.3%) have a blank facility string. So 10.7% did not parse on the simple split, and 2.7% end with no site address.

Step 3 known rows, all present:
- CB Manufacturing Company, Inc. (the PepsiCo site): 19300 E 72nd Ave, Denver 80249, AIRS 031-2567, permit 22DE0598, received 2022-10-12, Final Approval. in_date_scope N.
- Vartega Inc.: 5675 Pecos St, Adams 80221, AIRS 001-2306, permit 23AD0398, received 2023-04-04, To Be Determined. in_date_scope N.
- Pretred, Inc.: 6550 N Denali St, Adams 80019, AIRS 001-2359, permit 26AD0189, received 2025-10-21, Final Approval.
- Ursa Major Technologies: 19750 County Road 7, Berthoud, AIRS 123-A2D2, permit 26WE0154, received 2025-09-29, To Be Determined.
- TFP Nutrition (Texas Farm Products Company): 450 N Front St, Weld 80651, AIRS 123-0182, permit 06WE0240, received 2023-06-20, Final Approval. in_date_scope N. Only this one row is present; the 2023-12-26 modification noted in Step 3 came from the OnBase records viewer, not this feed.
- Entegris Inc. (Rockrimmon): 544 Ute Valley Trail, El Paso 80919, AIRS 041-2210, permit 23EP0544, received 2024-12-16, IA Modification.
All six are flagged Y, sector other.

**Join key:** company_name plus site_address/zip for matching to other sources (a location is present on 97% of rows; for oil and gas it is usually section-township-range or lat/long rather than a street, 850 of 931 rows, while non oil and gas rows mostly carry a street address). airs_id (99.95% filled) and permit_number join to the other APCD sources (records viewer, in-progress dashboard, facilities layer). Company names are legal names in mixed spellings ("UCH - MEMORIAL HOSPITAL" and "UCH-MEMORIAL HOSPITAL"), so name joins need normalising. The applicant can be a shell or contract manufacturer rather than the brand (CB Manufacturing for PepsiCo; "855400, LLC" for a Pueblo tissue plant), which is why the address matters.

**Refresh:** `python3 -I pull_apcd_permit_status.py --fetch` does one GET (one retry after 30 s, then stops), saves `raw/permit_status_raw_<UTC>.json`, and rewrites the CSV. Without `--fetch` it reparses the newest raw file. DECISION FOR MATTHEW: the feed holds only applications processed in the last six months and has no archive, so history only exists if the feed is saved on a schedule. Weekly would be ample (about 50 to 90 new applications a month); monthly is the minimum that loses nothing given the six-month window. No schedule has been set up.

**Gotchas:**
- Rolling window, not an archive. A row disappears once its application has had no processing for six months. Row counts will move day to day (2,002 yesterday, 1,995 today).
- `permit_issued_on` is the ORIGINAL issue date of an old permit, not the date of the current action. It is filled on 268 rows and every value is between 1996 and 2009. Do not read it as "this application was approved on".
- `county` is wrong on some rows because the feed pairs a facility with a company office address. 46 rows have a county that disagrees with the county prefix of their own AIRS ID (for example DCP and WES compressor stations in Weld County shown with Denver or Greeley office addresses and county "DENVER"; CoorsTek North Table Mountain shown as Mesa). Trust the AIRS prefix over the county column for those.
- 155 rows are portable sources (AIRS prefix 777, county given as "PORTABLE SOURCE"); their address is a yard or a lat/long, and county is left blank.
- The feed appends "(L.D.)" to the county on 17 land-development rows; this is stripped. "INDIAN LANDS" (1 row) and "OUT-OF-STATE" are blanked.
- Facility names are cut at 40 characters in the source system, so some end mid-word.
- No city anywhere in the feed. Zip is "00000" on rows located by lat/long (blanked).
- The same permit can appear once per emission point as separate permit numbers; one plant often has several rows (Cargill, Raptor Materials, PDC pads). Count facilities by airs_id, not rows.
- One connection reset was seen in Step 3; none today. The counties endpoint is returning 500.
- Step 1 noted this is a legacy app that may be retired as APCD moves to e-filing. The script stops with a "schema drift" error if the field list changes.

**Assumptions:**
- record_date is Received; time part is always midnight and was dropped.
- company_role is "applicant" for every row, including ownership transfers and name changes.
- "Oil and gas" covers upstream operators, midstream and pipelines, crude terminals, the Suncor refinery and its products terminal, and oilfield service companies (Halliburton, American Cementing, Multi-Chem, Select Water, NGL Water, Produced Water Recycle, Superior Oilfield). Rows from those companies are flagged N even when the equipment is generic (for example Halliburton's Fort Lupton cement batch plant).
- Not counted as oil and gas, so flagged Y: fuel retail and bulk fuel distribution (CHS, Rhinehart Oil, Seeley Oil, Murphy Oil USA, Byers Petroleum, Feather Petroleum, Stub's Gas & Oil and the chains), dairy biogas and renewable natural gas plants (CEA, Greengas, Platte River Biogas), landfill gas, a helium plant, the Pawnee Waste E&P landfill, gas-fired power plants, and rail transload terminals (Cando, USRL Hudson) except one Cando row for fracking-fluid tanks. Black Eagle Energy Services is flagged Y because its row is a metal parts manufacturing shop in Berthoud. ARC McClane Canyon is a coal mine (Y).
- Operator-name list used (built from this feed): 1876 Resources, American Cementing, Anschutz Exploration, Bargath, Bayswater, Beeman Oil & Gas, Bison IV / Bison Oil & Gas, BNL (Enterprise), Bonanza Creek, Chaco Energy, Chevron, Citation Oil & Gas, Civitas, Colorado Interstate Gas, Covalence DJ, Crestone Peak, D90 Energy, DCP Operating, Desert Eagle Operating, Divide Creek Gathering, Dunamis Energy, Elevation Midstream, Enterprise Gas Processing, ET Crude Terminals, Evergreen Natural Resources, Extraction Oil & Gas, Fulcrum Energy Operating, Fundare, Grand Mesa Operating, Green Natural Gas Ventures, Halliburton, HighPoint Operating, Hilcorp, Impetro, Joemar, K.P. Kauffman, Kerr-McGee, KT Resources, KTM Operating, Laramie Energy, Magpie Operating, Moonrise Midstream, MountainWest Pipeline, Multi-Chem, NGL Crude Terminals, NGL Water Solutions, Noble Energy, North Fork Energy, NuStar Logistics, Ogris Operating, ONEOK, Overland Pass Pipeline, OWN Resources, P.O.&G. Operating, PDC Energy, Plains Marketing, Platte River Midstream, Polaris Production, Prairie Operating, Produced Water Recycle, QB Energy, Rampike Resources, Renegade Oil & Gas, REP Processing, Rockies Express Pipeline, Rocky Mountain Midstream, Rocky Mountain Natural Gas, Scout Energy, Select Water Solutions, Sheldon Kye Energy, Silver Mountain Energy, Simcoe, Spellbound Energy, Strachan Exploration, Summit DJ, Summit Midstream, Suncor Energy, Superior Oilfield Services, Tallgrass, TEP Rocky Mountain, TransColorado Gas Transmission, Tumbleweed Midstream, Twin Eagle Terminals, UGC Midstream, Utah Gas, Verdad Resources, WES DJ / WES Wattenberg, Western Operating, Wexpro, Wiepking-Fullerton, Williams (Field Services, Front Range, Gilcrest), Zen Midstream. 929 of the 931 oil and gas rows are caught by name; 2 by keyword (Helena Resources crude tanks, Cando fracking-fluid tanks). A new operator that appears in a later pull will only be caught if its row text hits a keyword, so the list needs a look at each refresh.
- The sector tag is a triage aid. "aggregate_concrete_asphalt" is driven mostly by company name, so it includes generators and haul roads at those companies. Owens Corning (roofing and asphalt plant), Fujifilm Electronic Materials and Mill Rock Packaging were forced to "other" because their names contain aggregate words. Denver Brick and Westlake Royal Roofing remain under aggregate on a keyword and are arguably manufacturers.
- Out-of-state addresses are treated as mailing addresses, not sites.
- The spot check of 8 random rows compared the CSV with the saved raw response from the same fetch, not with a second live call, because the brief said to fetch once. All 8 matched on company, date, permit number, service type and facility parse.

**Not pulled:** nothing within the feed. Outside it: any application that left the six-month processing window before 2026-10-10 is not in this source at all, for every received date (2024-01-01 to about 2026-04 is only partly covered; the missing share cannot be measured from the feed). The counties lookup endpoint was not pulled (HTTP 500).


---

### Mile High CRE

**Source:** Mile High CRE, https://milehighcre.com (Colorado commercial real estate news, WordPress). Route used: the site's WordPress REST API, `/wp-json/wp/v2/posts?after=2024-01-01T00:00:00&per_page=100&orderby=date&order=asc`, 20 pages, 2.5 s pause, user agent `step4-research-pull/1.0 (research; contact ...)`. Chosen because it is the cheapest allowed route: 20 requests for the whole site against about 200 for the paged RSS feeds, it carries a total count (`X-WP-Total`), and it gives the same title, excerpt and categories the feed publishes. No bulk download exists. No article pages were fetched. All shell requests succeeded; WebFetch was not used.

**Verdict:** pass as a tagged news feed (complete, exact count match, dates clean). Weak as an entity source: company and street address are filled on a minority of rows by conservative rules, so treat it as a lead list to read, not a join table.

**Terms and robots:** Read on 2026-10-10.
- robots.txt (HTTP 200, 173 bytes): "User-agent: * / Disallow:" with an empty Disallow, plus a sitemap line. Nothing is disallowed for a generic agent: feeds, category pages, article pages and `/wp-json/` are all open. No crawl-delay.
- Terms of use: none found. The footer links only About, Contact, Submit News, Media Kit, Editorial Calendar and Ad Specs; the page sitemap lists 12 pages and none is a terms page; `/terms/`, `/terms-of-use/` and `/terms-and-conditions/` return 404.
- Privacy policy (last updated November 01, 2023): a template notice about what the site collects from visitors. It does not mention scraping, bots, crawlers, automated access or data mining.
- Copyright: the footer says "© 2026 All Rights Reserved." No republication licence or notice beyond that. Because of it, the output keeps the headline, the short excerpt and extracted facts only, never the article body.
- Decision: robots allows the paths and the terms are silent, so proceeded politely. Not unclear, but the absence of a terms page is itself an assumption worth a human glance before any commercial reuse of the text.

**Rows:** 1,957 written. The API's own count for the same filter (`after=2024-01-01`, `X-WP-Total`) was 1,957 at the pull and 1,957 on a recheck after the pull. Industrial category: 160 rows against the API's own count of 160 for `categories=26`.

**Date range:** 2024-01-02 to 2026-10-08 (publish date, site local time). No gaps: every month from 2024-01 to 2026-10 has posts (40 to 72 a month; October 2026 is a part month with 16). No future dates, nothing before 2024-01-01.

Monthly counts, all posts / industrial category:
2024: Jan 72/9, Feb 66/5, Mar 60/4, Apr 72/3, May 66/4, Jun 55/2, Jul 61/7, Aug 68/8, Sep 56/2, Oct 71/5, Nov 60/7, Dec 53/5
2025: Jan 64/8, Feb 51/4, Mar 65/8, Apr 61/5, May 61/1, Jun 46/1, Jul 64/4, Aug 60/7, Sep 64/4, Oct 62/6, Nov 51/3, Dec 43/4
2026: Jan 58/8, Feb 54/2, Mar 65/8, Apr 61/3, May 40/5, Jun 58/8, Jul 52/3, Aug 53/5, Sep 48/1, Oct (to the 8th) 16/1

Against Step 3's industrial counts: June 2026 8 (Step 3: 8), July 2026 3 (3), August 2026 5 (5), September 2026 1 (1). All four match. The three Step 3 headlines are present and flagged Y: "Target Opens $367M Food Distribution Center in Thornton" (2026-06-04; company Target, 15450 Washington St, Thornton), "California Aerospace and Defense Company Opens Arvada Facility" (2026-08-24; company blank by rule because the headline subject is a description, city Arvada), "Terra CO2 Breaks Ground on New Golden HQ and R&D Facility" (2026-08-11; company Terra CO2, 1341 Avery St, Golden).

**Flagged:** 160 Y, all `industrial category`. 1,797 N.

**Null rates:** company_name 80.2% blank, site_address 75.2% blank, record_date 0% blank. Also city 32.2% blank, county 62.2% blank (filled only for Denver), zip 99.5% blank. Within the 160 industrial rows: company_name 70.0% blank, site_address about 56% blank, city about 13% blank. company_role: unknown on 1,946 rows, contractor 5, tenant 4, applicant 2.

**Duplicates:** 0 on record_id (WordPress post id).

**Fields:** `categories` (all category names on the post, `; ` separated), `extraction_basis` (title, excerpt, content, none: where site_address came from; if there is no address, where the city came from; `title` if only a company was found), `addresses_all` (every street address the regex found in title, excerpt or body, with the adjacent city when one follows), `parser_version`. Bylines are not kept.

**Join key:** company_name (headline subject) and site_address + city. Quality is modest. Addresses that are present look clean (number, street, type) and are good for an address join against permits. Company names are short trade names from headlines ("Pinkard", "JHL", "Wold"), so they need fuzzy matching, and many are developers, brokers, lenders and architects, not occupiers. The industrial-category rows are the useful subset.

**Refresh:** `python3 pull_mile_high_cre.py` (incremental: reads the newest date in `raw/posts.jsonl` and asks only for later posts, then rebuilds the CSV). `--full` refetches from 2024-01-01 (21 requests, about a minute). `--parse-only` rebuilds the CSV from the cache with no network. Weekly is enough: the site posts about 2 to 3 items a working day and 3 to 8 industrial items a month.

**Gotchas:**
- The incremental cursor picks up new posts only. Edits to old posts (changed titles or categories) and deletions are only caught by `--full`.
- REST `date` is site local time (Mountain). The RSS `pubDate` is UTC, so a late-afternoon post shows one day later in the feed than in this file.
- The excerpt is WordPress's automatic first 55 words or so, so an address that appears lower in the article is only reachable through the body text. The script requests the body so the address regex can run, then throws it away: the cache (`raw/posts.jsonl`) holds only id, date, link, title, category ids, excerpt and the addresses found. This means a regex change to body-address extraction needs `--full`.
- `extraction_basis = content` (148 rows) is lower confidence: the one address in the body can be a sales gallery, a leasing office or a head office. Example seen: "Pre-Leasing Underway at Tempo Nine Mile Station" is in Aurora but the body's only address is in Centennial. When the body has two or more distinct addresses, site_address is left blank and they are all in `addresses_all`.
- City can be the wrong one when a headline carries a place in a property or company name. The excerpt-nearest rule fixed the case found ("The Inverness Denver", really Englewood), but others will exist. Neighborhood names (Cherry Creek, RiNo, LoHi) are not cities, so an address with only a neighborhood near it is left out of site_address and appears only in `addresses_all`.
- Company extraction is a headline pattern (`<Company> <verb> ...`). It cannot tell a developer from an occupier, and a few non-companies will remain (venues, agencies, the odd product or person name). Headlines that lead with a description ("California Aerospace and Defense Company Opens...", "UK-Based Oxford Ionics Opens...") are left blank on purpose even when the excerpt names the firm.
- Round-up posts ("Mile High Transactions Report", CHFA award lists) name many properties: read `addresses_all`, not site_address.
- If the site adds a terms page or a robots Disallow, recheck before the next pull.

**Assumptions:**
- No terms page means no stated prohibition. The "All Rights Reserved" footer was read as a copyright notice on the text, handled by not storing article bodies.
- Running an address regex over the body in memory, and keeping only the address, counts as an "extracted fact" and not as storing article text.
- Posts in people categories (Movers and Shakers, CRE People, Profiles, Mile High Climber, Q&A) and posts whose excerpt opens with a "By <name>" byline (contributed articles) are kept as rows with the headline only: no excerpt, no company, no address. 275 rows are headline-only for these reasons. Some headlines in the people categories name a person in a professional role ("X Named President of Y"); these are published business news, so the rows were kept, but drop the people categories downstream if that is not wanted. Excerpts on ordinary news posts can also quote a named executive.
- Only one FLAG rule was asked for (industrial category). Data-centre, life-science and energy posts outside that category are N; the `categories` column lets a later step widen the rule (Data Centers, Life Sciences, Energy, Aviation, Technology).
- county is filled only when city is Denver. Other cities are left blank because several Front Range cities span counties.
- company_role defaults to unknown. tenant needs a lease verb in the headline and the excerpt showing the company signing or occupying; contractor needs a construction-firm name plus a build verb; applicant needs "Proposes", "Submits" or "Files".
- Hand check of 20 random rows plus 20 rows with a company or address, done three times while tightening the rules. On the final pass: addresses taken from title or excerpt were right in every case checked; body-only addresses were right in roughly two of three; cities were right except the firm-home-base and property-name cases noted above, which the rules now mostly exclude; company names were real organisations in the final list of 273 distinct names apart from a handful of venues and acronyms. Earlier passes had clear errors ("Grand" from "Grand Opening", landlords tagged as tenants), which were removed.

**Not pulled:** Nothing missing for 2024-01-01 to 2026-10-08, all categories. Not attempted: article pages (not needed), comments, tags, authors, the `open-positions` and gallery post types, and anything before 2024-01-01.


---

# Accela terms finding (Denver trade permits, on hold)

No search was run and no records were collected.

## Denver Accela Citizen Access: what the terms say about automated access

Read-only check, done 2026-10-10. No search was run on the Accela site and no permit records were collected. This is a summary of what the documents say, not legal advice.

## Bottom line

**Unclear, leaning "do not scrape without asking".** Nothing I could read expressly permits automated collection from `aca-prod.accela.com/DENVER/`, and nothing I could read expressly forbids it either. The two documents most likely to settle it (the Denver portal's own disclaimer, and the City and County of Denver website terms of use) could not be read today. Accela's general website terms, if they reach the portal, license content for "informational, non-commercial use" only, which does not fit a sales prospecting pipeline. The source should stay on hold until Matthew gets an answer from one of the routes listed at the end.

## Documents

### 1. Denver Accela Citizen Access portal: on-page terms or "general disclaimer"

- URL: `https://aca-prod.accela.com/DENVER/Default.aspx` (one fetch of the landing page with the WebFetch tool, 2026-10-10). A second landing URL, `/DENVER/Welcome.aspx`, returned a fetch error and was not retried.
- What came back: the page content delivered to the fetch tool had no terms, disclaimer, privacy or Accela links and no disclaimer text. The portal is a script-driven page, so the footer and any disclaimer are probably rendered in the browser and were not visible to the tool.
- Could not be read: any "General Disclaimer" or terms shown in the footer, at registration or at login. Accela Citizen Access portals commonly show an agency-written disclaimer on the registration screen; whether Denver's does, and what it says, is not established.
- Bearing on automated access: unknown.

### 2. robots.txt on the Accela host

- URL: `https://aca-prod.accela.com/robots.txt` (one shell request, 2026-10-10 18:01 UTC; the WebFetch tool returned a fetch error on the same URL).
- Result: HTTP 404, "File or directory not found". The host publishes no robots.txt.
- Bearing: no crawl rules are stated either way. The absence of a robots file is not permission; it only means the site terms are the controlling document.

### 3. Accela, Inc. website Terms of Use

- URL: `https://www.accela.com/terms-of-use/` (read 2026-10-10 through the WebFetch tool, which summarises and quotes; I did not see the raw page). Titled "Accela, Inc. - Terms and Conditions of Use", "Revised January 16, 2020".
- Scope: the "Site" is defined as web pages at accela.com and pages reachable directly or indirectly from its home page. Citizen Access portals and agency-hosted services are not mentioned. Whether `aca-prod.accela.com` (a subdomain of accela.com) falls inside "the Site" is not stated.
- Operative phrases:
  - Content licence: "a limited, nonexclusive license for informational, non-commercial use of such content".
  - "you are not permitted to modify, distribute, publish, transmit, or create derivative works" from Site material "for any commercial purposes".
  - "Any rights not expressly granted herein by Accela are reserved to Accela."
  - "Accela may monitor activity on this Site to ensure that you and other users comply with these Terms."
  - Accela "may terminate or block your access to this Site or any portion thereof" at its discretion.
  - Unauthorized access to password-restricted portions "will be prosecuted to the fullest extent of applicable laws."
- No clause mentions robots, spiders, crawlers, scraping, data mining, bulk collection or systematic retrieval.
- Bearing: no explicit anti-bot clause, but the only licence granted is for non-commercial, informational use, with everything else reserved. If these terms apply to the portal, commercial reuse of scraped content is outside the licence. Permit records themselves are City public records, not Accela content, which is a further reason the scope is unclear.

### 4. Accela Privacy Policy

- URL: `https://www.accela.com/privacy-policy/` (read 2026-10-10 via WebFetch). States it "was updated on or about June 25, 2023".
- Says nothing about bots, scraping or automated access, and does not name Citizen Access.
- Relevant point: for data its government customers put into the platform, Accela says "we function as a service provider" and that requests about that data should go to "the relevant customer directly". In other words Accela treats the City as the party that decides about its data.

### 5. Accela Developer Portal Terms of Use (the sanctioned API route, for contrast)

- URL: `https://developer.accela.com/TermsOfUse` (read 2026-10-10 via WebFetch). "Effective October 1, 2017".
- Covers the Accela developer resources and API, not the public portal pages.
- Operative phrases: call volumes may be limited, "as specified by Accela in writing"; no access "if You are Our direct competitor" without consent; no attempt to "gain unauthorized access to the Developer Resources"; applications may not be commercially distributed unless an agreement with Accela allows it.
- No scraping clause. In practice the Accela API needs an app registration, and access to an agency's data is switched on by that agency, so this route also runs through the City.

### 6. Other Accela legal pages

- `https://www.accela.com/terms-of-service/`, `https://www.accela.com/legal/` and `https://developer.accela.com/docs/construct-termsOfUse.html` returned fetch errors (pages may not exist at those addresses). Not read. Accela's customer subscription terms bind the City as customer, not members of the public, and I did not find a public "Citizen Access terms" document.

### 7. City and County of Denver website Terms of Use and Privacy and Security policy

- URLs: `https://www.denvergov.org/Terms-of-Use` and `https://denvergov.org/Privacy-Security` (located by web search, 2026-10-10).
- **Could not be read.** The WebFetch tool refused denvergov.org with a robots-disallowed error on three URLs (the Terms of Use page, a Technology Services terms URL, and `denvergov.org/opendata/termsofuse`). Per the ground rules I did not try another route (no shell fetch, no mirror, no cache).
- Worth noting on its own terms: denvergov.org tells automated fetchers to stay out of at least these pages. That is a signal about the City's general stance on bots on its main website, though it is a different host from the Accela portal.
- Bearing: unknown until someone reads the page in a browser. Look for clauses on automated or systematic retrieval, commercial use, and whether the terms extend to third-party hosted City services such as e-permits.

### 8. Denver open data licence (contrast)

- The Denver Open Data Catalog licence page on denvergov.org could not be read today (same robots refusal). From memory only, and not verified today, the catalog has historically been published under Creative Commons Attribution 3.0.
- What I did read (2026-10-10, ArcGIS Online item metadata for the two layers pulled in this step, items `4e2cf20443e14710bbb4311126a4362c` and `ba809992051745918b0e07ecb77ec468`): both are shared with access "public" and carry a "USE CONSTRAINTS" statement. It is a liability disclaimer: data is provided "AS IS WITHOUT WARRANTY OF ANY KIND", is used "only at the user's sole risk", the user agrees to "indemnify and hold harmless the City and County of Denver", and "NOT FOR ENGINEERING PURPOSES." It places no limit on automated access, bulk download or commercial reuse.
- The ArcGIS host (`services1.arcgis.com`) serves no robots.txt (the request returns HTTP 403 "Invalid URL"), and the open data hub home page (`opendata-geospatialdenver.hub.arcgis.com`) states no licence on the page itself.
- Contrast: the open data layers are published for reuse through a query API with only a warranty disclaimer attached. The Accela portal is a transactional web application with no published data licence that I could find. The commercial construction permit layer is itself described by the City as a daily extract "from the Accela database", so the City already publishes part of the Accela data through the open route.

## What could not be read

| Document | Why |
|---|---|
| Denver ACA portal footer or registration disclaimer | Script-rendered page; nothing visible to the fetch tool; no searching or logging in allowed |
| denvergov.org Terms of Use | WebFetch refused: robots disallowed |
| denvergov.org Privacy and Security | Not attempted after the host-level robots refusal |
| Denver Open Data Catalog licence page | WebFetch refused: robots disallowed |
| accela.com/terms-of-service, accela.com/legal, developer.accela.com construct terms page | Fetch errors |

## Conclusion

- **Allowed?** Not established. No document read grants permission for automated or bulk collection from the portal.
- **Not allowed?** Not established either. No document read contains an anti-scraping, anti-bot or rate clause that clearly covers the portal. Accela's website terms limit use to "informational, non-commercial use" if they apply.
- **Status: unclear. Keep the source on hold.**

## What Matthew would need to ask or decide

1. Open `https://www.denvergov.org/Terms-of-Use` and the e-permits portal footer and registration screen in a browser and read them (five minutes). If either prohibits automated or commercial use, the answer is no and the question closes.
2. If the terms are silent, ask Denver Community Planning and Development (or Technology Services) one question: is there a sanctioned bulk route for trade permit data (mechanical, electrical, plumbing), such as an open data layer, a scheduled extract, or Accela API access? The City already publishes commercial construction, residential construction and site plan extracts from Accela as open data, so adding trade permits may be a small request. A Colorado Open Records Act request for a periodic extract is the formal fallback. I did not contact anyone or draft a request.
3. Decide whether a commercial prospecting use is acceptable to Atlas Copco's own compliance people even where a site's terms are silent. That is a company call, not something the documents answer.
4. Until then, use what is already open: the commercial construction permit layer pulled in this step comes from the same Accela database and carries valuation, class, contractor and parcel number.

---

# Not pulled

- **Denver trade permits (Accela):** on hold by design. Terms check only.
- **State water permits, 2026-08-07 to 2026-10-10:** not in the source. The agency's snapshot is still dated 2026-08-07.
- **State water permits received before 2024 but issued or effective in 2024 or later:** 3,192 rows, out of scope under the received-date rule. 3,050 are construction certifications re-issued on 2024-04-01. They include the 2023 Entegris and Sphere Renewables construction rows.
- **APCD applications that left the six-month window before 2026-10-10:** not recoverable from the feed. Coverage of 2024-01 to about 2026-04 is partial and the missing share cannot be measured.
- **OEDIT October 2026:** meeting is on 2026-10-15. The 2026-07-27 special meeting has an agenda but no minutes yet. For the 29 months with a post, items that appear only in minutes (Enterprise Zone, film, Rural Jump-Start, Advanced Industries) were not read.
- **Denver permits received but not yet issued:** not in the layer.
- **Mile High CRE:** article bodies, tags and bylines not stored. Nothing before 2024.
- **Denver website terms and open data licence text:** the fetch tool was refused on those denvergov.org pages, so they were not read.

# Files and what was saved where

**The project ran out of room.** It holds about 2.0M units of text and had about 1.57M free. The full flagged file alone used all of it. So the project holds a reduced set, and the full set was delivered as downloads in the Step 4 chat.

Saved to the project under `step4-scrape/`:

- `scrape_flagged.csv`: all 9,225 flagged rows, all 17 columns, but with `description` cut to 120 characters to fit. The download copy has the full 500.
- `scrape_oedit_approvals.csv`: complete (139 rows).
- `scrape_notes.md`: this file.
- Pull scripts for every source (`pull_*.py`, plus the shared helpers `soda_fetch.py` and `arcgis_common.py`, and `pull_oedit_approvals.md`), and the monthly summaries for UCC and business registrations.

Not saved to the project (too large), delivered as downloads only:

- `scrape_ucc_filings.csv` (173 MB), `scrape_business_registrations.csv` (184 MB). Splitting by year would not help: one year of either is far larger than the whole project.
- `scrape_denver_commercial_permits.csv`, `scrape_denver_site_plans.csv`, `scrape_state_water_permits.csv`, `scrape_apcd_permit_status.csv`, `scrape_mile_high_cre.csv` (13 MB together).

Raw caches (including the APCD raw JSON, which still holds staff contact fields) stay in the Step 4 cloud workspace only and will be lost when that session ends. Every pull can be rerun from its script.

# Decisions after the run (2026-10-10)

- **Accela (Denver trade permits):** no scrape. Use it by hand, in a browser, for specific addresses that the other sources surface. Reading Denver's terms and emailing the city about a bulk route stay optional.
- **UCC liens:** confirmed. Hospital liens stay out; other statutory liens stay in with free text withheld.
- **APCD history:** a scheduled task, "APCD monthly snapshot", runs on the 1st of each month at 8:55am Pacific and saves a dated CSV to `step4-scrape\apcd_snapshots\` on Matthew's computer. It needs that computer on with the Claude desktop app open.
- **Where the full data lives:** `C:\Users\spink\OneDrive\Desktop\Personal Projects\Agent Analysit Flow\step4-scrape\` on Matthew's computer. It holds every source CSV in full, the full flagged file (500-character descriptions), the scripts and the notes. The UCC and business registration CSVs are in subfolders named after the files.
- **Water permit acreage rule changed (option D).** The 5-acre rule no longer fires when every project-type tag is residential, pipeline, highway or non-structural. Acreage-flagged rows fell from 1,874 to 671. Rows tagged commercial, oil and gas, or "other" still flag.
- **2023 water permits carried in (option C).** Construction stormwater permits received in 2023 that are still active (Effective, Admin continued or Pending) and pass the flag rule are now included: 127 rows, marked in the new `scope_basis` column. Sphere Renewables is back in. The 2023 Entegris construction permit is not, because it was terminated on 2026-07-01.
- **Project copy of `scrape_flagged.csv` is now the full file** (500-character descriptions). The smaller flagged set fits, so the earlier 120-character cut no longer applies.
- **Resulting counts (these replace the figures earlier in this file):** state water permits 6,814 rows, 1,867 flagged (was 6,687 and 2,893). `scrape_flagged.csv` is now 8,199 rows (was 9,225). Earliest water permit record_date is now 2023-01-10.
