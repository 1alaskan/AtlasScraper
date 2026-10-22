#!/usr/bin/env python3
"""Census geocoder lookups for split-zip addresses, cached and resumable.

Web use is limited to https://geocoding.geo.census.gov (address -> county). One lookup a second.
The cache key is "street address, city, CO zip". A run that hits the time budget saves what it has and
asks to be run again; nothing already looked up is fetched twice.
"""
import json, os, sys, time, urllib.parse, urllib.request

from v3_lib import load_json, save_json

URL = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress?"


class Incomplete(Exception):
    pass


def lookup(q):
    url = URL + urllib.parse.urlencode({"address": q, "benchmark": "Public_AR_Current", "vintage": "Current_Current", "format": "json"})
    res = "error"
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "step5-research/1.0"})
            j = json.load(urllib.request.urlopen(req, timeout=30))
            m = j["result"]["addressMatches"]
            res = m[0]["geographies"]["Counties"][0]["NAME"] if m else "no match"
            break
        except Exception:
            res = "error"
            time.sleep(3)
    return res


def geocode_all(queries, cache_path, budget_seconds=150, offline=False, log=print):
    """Fill the cache for every query. Raises Incomplete when the time budget runs out (run again to continue)."""
    cache = load_json(cache_path, {}) or {}
    todo = [q for q in queries if q not in cache or cache[q] == "error"]
    if offline:
        if todo:
            log("geocoder: offline, %d addresses not in the cache are treated as 'could not place'" % len(todo))
        return cache
    if todo:
        log("geocoder: %d addresses to look up (%d already cached)" % (len(todo), len(queries) - len(todo)))
    t0 = time.time()
    done = 0
    for q in todo:
        if time.time() - t0 > budget_seconds:
            save_json(cache_path, cache)
            raise Incomplete("geocoder: %d of %d looked up, time budget reached. Run the same command again to continue." % (done, len(todo)))
        cache[q] = lookup(q)
        done += 1
        if done % 10 == 0:
            save_json(cache_path, cache)
        time.sleep(1.0)
    if todo:
        save_json(cache_path, cache)
    return cache
