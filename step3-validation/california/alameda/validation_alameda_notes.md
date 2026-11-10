# Alameda County: local source validation (2026-11-10)

Basis for every verdict is `spot-checked only`: each source was pulled or queried and read. No back-test was run. The incentive seeds (11 companies) were not used, because no local source reached the point of being worth testing against them.

| Source | Verdict | Reason |
|---|---|---|
| Hayward business licences | park | Dated and address-level with NAICS and employee counts, but the newest start date is 2024-01-31. 9 flagged rows, all tiny (0 to 10 employees). Kept as an installed-base list. |
| Legistar agenda items (Oakland, Hayward, San Leandro, Alameda) | drop | 8,188 matters since 2024 gave 5 flagged rows, 2 of them false. Same outcome as meeting-item sources in Colorado. |
| Fremont Development Activity layer | park | Right content (industrial square feet by project) but frozen at May 2023. Becomes build if the current Excel table can be obtained. |
| Berkeley business licences | drop | No date field. |
| BAAQMD applications received | not tested | robots.txt disallows the table's query URLs. Manual lookup. |
| Fremont, San Leandro, Oakland permit portals | not tested | Accela, browser-only. Manual lookup. |
| Fremont AgencyCounter | not tested | Private vendor map; terms not found. |
| Newark, Union City, Livermore, Pleasanton, Dublin, Emeryville, Albany, Piedmont, county planning | not tested | City sites refused the shell (Fremont, San Leandro, Livermore, Newark, Union City) or were not explored. |

## Bottom line

No local source earned a build verdict. Alameda runs on the state sources alone for now. The permit and planning layer that separated companies in Denver, Adams and Weld exists here but sits behind browser-only portals and city websites that refuse automated requests.

## Side list

`step5-analysis/california/alameda/alameda_side_list_hayward_licences.csv`: ranked Hayward companies matched to a Hayward licence (2 of 13 matched: Columbus Manufacturing, 231 employees; RW Metal Spinning, 3).

## What would change this

1. A person with a browser downloading two things: Fremont's Development Activity Table (Excel) and the BAAQMD applications table. Both are public and both are refused to the shell.
2. Public records requests to Fremont, San Leandro and Hayward for commercial and industrial building permits since 2024, and to BAAQMD for applications received. Not drafted.
3. A decision to score CEQA filings, which is the one planning-type source that covers every city in the county and is already pulled (63 flagged rows).
