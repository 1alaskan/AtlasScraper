# Atlas lead pipeline

Compressed-air lead pipeline for Colorado counties (Atlas Copco IMPACT). Denver County is done; Adams, Arapahoe and Jefferson are next.

To run a county ("run Adams County"), load the `colorado-county-runner` skill. A copy lives at `.claude/skills/colorado-county-runner/SKILL.md` and uses repo-relative paths. The scrape step's agents follow `.claude/skills/datasource-validator-scraper/SKILL.md`. Both are copies of Matthew's account skills; when one changes, update the other so the two do not drift.

- `step4-scrape/`: statewide source pulls (UCC, registrations, OEDIT, water permits, APCD air permits, Mile High CRE) and their scripts. Two big v2 files are gzipped; `gunzip -k` them before the analysis step and never commit the unzipped copies.
- `step5-analysis/v3/scripts/`: the ranking pipeline. Run it with `python3 build_v3.py <step4 folder> <step5 folder> --county <name>`. Per-county settings are in `county_configs/`; `python3 build_zip_share.py <name>` makes the county's zip-share file. Do not touch the points table in `v3_config.py`.
- Everything runs in a cloud session with no computer linked: standard-library Python, and the Census geocoder, Census ZCTA file, data.colorado.gov and the portal hosts are all reachable from the cloud shell. Nothing depends on Matthew's Windows folder.
- Step 1 (discovery) and step 3 (validation) inputs, including ground truth and back-test notes, live in the Claude project "Atlas Lead Pipeline New". Read them with the Projects tool.
- Commit results and push to `main` at the end of each step.
- `streamlit_app.py` + `dashboard/`: the Streamlit site that shows each county's ranked list, evidence and notes. It reads `dashboard/counties.json`; after a county's analysis step, run `python3 dashboard/register_county.py ...` (see its docstring) and push. Streamlit Community Cloud redeploys from `main`. Keep `requirements.txt` to what the app needs.
