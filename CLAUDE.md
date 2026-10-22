# Atlas lead pipeline

Compressed-air lead pipeline for Colorado counties (Atlas Copco IMPACT). Denver County is done; Adams, Arapahoe and Jefferson are next.

To run a county ("run Adams County"), load the `colorado-county-runner` skill. A copy lives at `.claude/skills/colorado-county-runner/SKILL.md` and uses repo-relative paths.

- `step4-scrape/`: statewide source pulls (UCC, registrations, OEDIT, water permits, APCD air permits, Mile High CRE) and their scripts. Two big v2 files are gzipped; `gunzip -k` them before the analysis step and never commit the unzipped copies.
- `step5-analysis/v3/scripts/`: the ranking pipeline. Run it with `python3 build_v3.py <step4 folder> <step5 folder> --county <name>`. Per-county settings are in `county_configs/`. Do not touch the points table in `v3_config.py`.
- Step 1 (discovery) and step 3 (validation) inputs, including ground truth and back-test notes, live in the Claude project "Atlas Lead Pipeline New". Read them with the Projects tool.
- Commit results and push to `main` at the end of each step.
