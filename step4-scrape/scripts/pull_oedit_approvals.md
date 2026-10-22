# pull_oedit_approvals: how the OEDIT EDC approvals pull was done and how to rerun it

No shell script fetches this source. oedit.colorado.gov returns HTTP 403 to shell clients, so every page is read with the WebFetch tool, one page at a time, and the result is cached by hand under `raw/`. `build_oedit_csv.py` (no network) turns the transcribed rows into `scrape_oedit_approvals.csv` and `oedit_month_log.csv`.

## URLs

- Monthly post: `https://oedit.colorado.gov/news/<month>-<year>-edc-approved-job-growth-incentive-tax-credit-and-strategic-fund-projects` (month in full lower case, for example `september-2026`). Works for every month with a post, including Feb and Mar 2024 whose titles say "Feb 2024" and "Mar 2024".
- Index pages: `https://oedit.colorado.gov/news` (30 per page, `?page=N`) and `https://oedit.colorado.gov/category/projects-approved-for-incentives`.
- EDC page with current-year agendas and minutes (published Google Docs): `https://oedit.colorado.gov/about/colorado-economic-development-commission`
- Minutes archive for 2024 and 2025: `https://oedit.colorado.gov/about/economic-development-commission/edc-archives`
- Robots: `https://oedit.colorado.gov/robots.txt` (Drupal default; `/news/`, `/category/` and `/about/` are not disallowed; `/search/` is).

## Fetch prompt A (monthly post, first pass)

> Exhaustive structured extraction, compact format. Line 1: page title. Line 2: published/post date shown on the page; and the EDC meeting date if a specific day is stated (else "meeting day not stated"). Then ONE LINE per approved project or item on the page (every single one, no omissions, in page order, including Strategic Fund, CHIPS, Rural Jump-Start, film, award modifications or any other programme), with fields separated by " | " in this exact order: code_name | real_company (only if the page names it) | county_or_counties | city (only if stated as the site) | industry and project description (as complete as possible, close to the page's wording) | net_new_jobs | average_annual_wage | incentive_programme | incentive_amount | incentive_term | capital_investment | other_states_or_countries_considered. Use exact figures as written, no rounding. Write "not stated" where a value is absent. Last line: total count of projects.

## Fetch prompt B (second pass, audit wording; use this one first next time, it reports counties better)

> I am auditing numbers. Go through this page section by section. For each project heading, report as a numbered list: the heading exactly as written; every Colorado county or city named anywhere in that section and in what role (site under consideration, local incentive partner, CHIPS zone, or only the county used for the average annual wage percentage comparison); the number of net new jobs; the average annual wage in dollars; which incentive (tax credit, Strategic Fund, refund certificate, CHIPS, other); the dollar amount of the incentive approved or recommended; the number of months of the incentive; any capital investment dollar figure; which other states are competing. Copy numbers digit for digit. If a number is missing say "absent". Then state how many project headings there are in total.

## Fetch prompt M (minutes, for months with no post and for special meetings)

> These are Colorado Economic Development Commission meeting minutes. Line 1: the document title and meeting date. Then ONE LINE for every item the Commission voted to APPROVE that grants or modifies an incentive, award, grant, tax credit or programme participation for a project, company or organisation (...programme list...). No omissions; in document order. Skip only approval of minutes/agenda and budget housekeeping. Fields separated by " | ": project code name or item name | real company or organisation (only if the minutes name it) | county | city | description | net_new_jobs | average_annual_wage | incentive_programme | incentive_amount | incentive_term | capital_investment | other_states | vote result. Exact figures. "not stated" where absent. Omit staff and commissioner names. Last line: total count, and whether any code-named JGITC or Strategic Fund job growth items appear.

## Rerun (monthly, after the third Thursday)

1. WebFetch the new month's post URL with prompt B. Pause between fetches. If the fetch errors, there is probably no post: open the EDC page, find that meeting's minutes link and WebFetch it with prompt M (minutes post two to three months late).
2. Save the output as `raw/<YYYY-MM>_post_fetchB.txt` (or `_minutes_fetchM.txt`) with the URL and time at the top.
3. Add one `P(...)` line per project per programme (or `M(...)` for minutes items) to `build_oedit_csv.py`, add the meeting date to `MEET` and the post date to `POST_DATE`.
4. Run `python3 build_oedit_csv.py`. It asserts unique record_id values.
5. Re-fetch at least one month with the other prompt and compare the numbers.

Do not make shell requests to oedit.colorado.gov and do not use caches or mirrors.
