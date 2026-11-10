# California state sources: validation notes (first pass, 2026-11-10)

Basis for every verdict below is `spot-checked only`. There is no California ground truth, and no back-test has been run. Lead time is not measured for any source.

| Source | Verdict | Reason |
|---|---|---|
| SMARTS industrial stormwater | build | Dated, address-level, SIC-coded, weekly, no use restrictions. 117 flagged rows in Alameda County since 2024, read by eye: machine shops, heat treaters, instrument makers, food plants. |
| SMARTS construction stormwater | build | Dated, address-level, industrial marker. 31 flagged in Alameda County; includes non-plants (a utility yard, a national laboratory, a truck charging depot), so it needs the same owner and SIC style filtering Colorado's construction permits needed. |
| California Competes awards | build | Named, dated, small volume (58 since 2024). City only, multi-site awards common. |
| CAEATFA STE awards | build | Named, dated, equipment dollars and share purchased. No street address for recent awards; workbook lags the board by months. |
| CEQAnet | build (per county) | Dated, described, export works. Applicant is not in the export, so rows attach by address or parcel only. |
| ABC manufacturer licences | park | No application date in the export. Becomes build once daily snapshots are being diffed. |
| Employment Training Panel | not tested | Not pulled this session. |
| California UCC, business entities | not tested | Needs a bizfile login (Matthew). |
| Pressure vessel database | not tested | Terms unread; manual lookups only until they are. |

Seed projects for county validation come from the two award files. Alameda County has 11 distinct awarded companies since 2024, enough for the incentive-seeded back-test in the skill.
