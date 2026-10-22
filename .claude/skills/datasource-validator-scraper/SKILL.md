---
name: datasource-validator-scraper
description: Validate whether a named data source actually carries the signal it's supposed to, then build the extraction that pulls it. Use this skill whenever someone has a specific source in hand and wants to test, sample, pull, scrape, extract, or ingest it - "can I scrape this", "does this dataset actually have what I need", "pull this permit portal", "write a scraper for", "check if this source is any good", "get this into a table" - and whenever a pipeline, target list, or model is about to be built on a source nobody has sampled yet. It covers access route selection, terms-of-service and robots checks, signal validation on a sample, the extraction itself, and output QA. It does not find sources; that's a separate job.
---

# Data Source Validator and Scraper

Two jobs in sequence, and the order matters: prove the source carries the signal on a small sample, then build the pull. Reversing them is how a week disappears into a scraper for a field that turns out to be 80% null.

Input is one named source. If nobody has named one yet, this is the wrong skill.

## Step 1: Find the cheapest access route

Most scraping jobs aren't scraping jobs. Check in this order and stop at the first that works:

1. **Bulk download** - a zip, CSV, or database dump. Agencies publish these far more often than their search UI suggests. Look for a "data" or "downloads" page separate from the search page.
2. **Documented API**
3. **Undocumented JSON endpoint** - open the portal, watch the network tab, and find what the search form actually calls. Portals built on Accela, Socrata, ArcGIS, and similar almost always have one, and it returns clean JSON instead of parsed HTML.
4. **Structured export** - a per-search CSV or XLSX button.
5. **HTML scrape** - last resort, most brittle.
6. **Records request** - when the data exists but isn't published. Draft the request text and hand it over for the person to send themselves.

Say which route you took and why the cheaper ones didn't work. Skipping straight to HTML when a JSON endpoint exists is the single most common waste in this work.

## Step 2: Check you're allowed to

Before pulling anything at volume:

- Read robots.txt and the terms of service. Public-record data is usually reusable, but the portal serving it still sets access rules.
- Don't pull anything behind a login, and don't work around blocks, rate limits, or captchas. A block is an answer. If a source is closed, fall back to a records request or drop it.
- Check for personal data. Permit and filing records often carry names, home addresses, and phone numbers of individuals. Take the fields needed for the business question and leave the rest unretrieved rather than collecting them and filtering later.
- Rate limit deliberately: a delay between requests, an identifying user agent, off-peak hours where volume is significant. Stop on repeated errors rather than retrying into a wall.

If any of this rules the source out, say so plainly and stop. A clear no here is worth more than a fragile yes.

## Step 3: Validate on a sample before building anything

Pull 50 to 200 records by hand or with a throwaway script. Then check, in this order:

- **Field presence** - does the field the question depends on exist, and what share of records actually populate it? A field that's present in the schema and null in practice is the most common dead end.
- **Join key quality** - is there a usable key (name, address, EIN, DUNS, NAICS, lat/long), and is it clean enough to match against the target list without heroic entity resolution?
- **Coverage** - check the sample against a set of known-true cases. If ten facilities are known to exist and the source has four, that's the real coverage number, not the one on the About page.
- **Timing** - for anything predictive, take known past outcomes and check when the source first showed them. A source that fires the same week the outcome lands is a scorekeeper, not a leading indicator. This is cheap to test and expensive to assume.
- **Freshness** - most recent record date versus stated update cadence. Portals go stale quietly.

Kill criteria, applied before any build work:

- Required field is mostly empty.
- No usable join key and the question is entity-level.
- Source moves at or after the outcome it was meant to predict.

Report these results whether or not the source passes. A documented no saves the next person the same sample.

## Step 4: Build the pull

Once it passes:

- **Cache raw responses** to disk before parsing. Re-parsing shouldn't mean re-fetching, and the raw copy is the only defence when the site changes and the parse silently starts returning garbage.
- **Make it resumable and incremental** - checkpoint progress, support a date or ID cursor so reruns fetch only what's new.
- **Record provenance per row** - source URL, retrieval timestamp, and the parser version. Without it you can't tell stale data from wrong data six months later.
- **Parse defensively** - expect missing fields and layout changes, fail loudly on schema drift rather than writing nulls.
- **Normalize at the edge** - consistent date formats, trimmed and case-folded names, standardized state and NAICS codes. Store the raw value alongside the normalized one.

Keep the script boring and readable. These break when the site changes, and the person fixing it in four months won't be looking at it fresh.

## Step 5: QA the output

Before handing anything over:

- Row count against what the portal's own result count claimed.
- Null rate per field, compared to the sample from Step 3.
- Duplicate rate and whether duplicates are genuine or a paging bug.
- Date range sanity: no future dates, no 1900s, no unexplained gaps.
- Spot-check 5 to 10 rows against the live page.

A paging bug that silently truncates at page one looks exactly like a small dataset. The row count check is what catches it.

## Step 6: Hand back

The data file, plus a short source card:

```
**Source:** [name, URL, access route used]
**Verdict:** [pass / fail, with the kill criterion if failed]
**Coverage:** [share of known-true cases found]
**Lead time:** [how far ahead of outcomes it fires, if tested]
**Fields:** [what's in the output, with null rates on the important ones]
**Join key:** [what it joins on, and match quality]
**Refresh:** [how to rerun, and how often it's worth it]
**Gotchas:** [what broke, what will break]
```

## Failure modes

- **Scraping HTML when a JSON endpoint was one network-tab look away.**
- **Building before sampling** - the whole reason Step 3 sits where it does.
- **Trusting the About page** on coverage and freshness instead of measuring both.
- **Silent truncation** - paging that stops at page one and looks like a complete pull.
- **Hoovering personal data** because it happened to be in the response.
- **No provenance** - a table with no source URL or timestamp can't be audited or refreshed.
- **Pushing through a block** - rate limits and captchas are a decision by the publisher, not an obstacle to route around.
