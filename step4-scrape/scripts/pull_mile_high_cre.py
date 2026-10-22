#!/usr/bin/env python3
"""Mile High CRE (milehighcre.com) pull. Step 4, agent 6.

Route: WordPress REST API  /wp-json/wp/v2/posts  (robots.txt: "User-agent: * / Disallow:" (empty), no
terms-of-use page exists, privacy policy silent on automated access; checked 2026-10-10).

What is kept: post id, publish date, link, title, category ids, the API excerpt, and facts extracted by
rule (street addresses, Colorado city, zip, headline company). Full article text is requested so the address
regex can run over it, but it is discarded in memory: it is NOT written to the cache or the CSV.

Resumable / incremental: posts are fetched oldest first (order=asc) with an `after` date cursor, appended to
raw/posts.jsonl (one stripped post per line). A rerun reads the newest cached date and only asks for posts
after it. Use --full to refetch from 2024-01-01. Use --parse-only to rebuild the CSV from the cache.

Usage:  python3 pull_mile_high_cre.py [--full] [--parse-only]
"""
import csv, html, json, os, re, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
CACHE = os.path.join(RAW, "posts.jsonl")
CATS = os.path.join(RAW, "categories.json")
OUT = os.path.join(HERE, "scrape_mile_high_cre.csv")
BASE = "https://milehighcre.com/wp-json/wp/v2"
UA = "step4-research-pull/1.0 (research; contact spinkmt@gmail.com)"
START = "2024-01-01T00:00:00"
PAUSE = 2.5
PARSER_VERSION = "mhcre-1.0"
INDUSTRIAL_ID = 26
# Posts in these categories are about named people (hires, promotions, profiles): keep the row and the
# headline, drop the excerpt, extract no company.
PEOPLE_SLUGS = {"movers-and-shakers", "cre-people", "profiles", "mile-high-climber", "q-a"}

COLS = ["source", "source_level", "record_id", "record_date", "date_type", "record_type", "company_name",
        "company_role", "site_address", "city", "county", "zip", "description", "flag", "flag_rule",
        "source_url", "retrieved_at",
        "categories", "extraction_basis", "addresses_all", "parser_version"]

# ---------------------------------------------------------------- network
_err = 0


def get(url):
    """One polite GET. Returns (json, headers). Stops the run on two 429/5xx in a row."""
    global _err
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            hdr = {k.lower(): v for k, v in r.headers.items()}
        _err = 0
        time.sleep(PAUSE)
        return json.loads(body), hdr
    except urllib.error.HTTPError as e:
        if e.code == 429 or e.code >= 500:
            _err += 1
            if _err >= 2:
                sys.exit(f"STOP: two {e.code}-class errors in a row at {url}")
            time.sleep(30)
            return get(url)
        sys.exit(f"STOP: HTTP {e.code} at {url} (not retried by another route)")


# ---------------------------------------------------------------- text helpers
def clean(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s or "", flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


STREET_TYPES = (r"Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Way|Parkway|Pkwy|Place|Pl|Court|Ct|"
                r"Lane|Ln|Circle|Cir|Highway|Hwy|Trail|Terrace|Loop|Plaza|Mall|Row|Pike|Freeway|Turnpike")
NAMEWORD = r"(?:[A-Z][A-Za-z'’\-]+|\d{1,3}(?:st|nd|rd|th)|St\.|Mt\.|Ft\.)"
ADDR_RE = re.compile(
    r"(?<![\$\d,\.\-])\b(\d{1,5}(?:\s?[-–]\s?\d{1,5})?)\s+"              # house number (or range)
    r"((?:(?:N|S|E|W|NE|NW|SE|SW)\.?\s+|(?:North|South|East|West)\s+)?"    # optional direction
    r"(?:" + NAMEWORD + r"\s+){1,4}?"                                      # 1 to 4 name words
    r"(?:" + STREET_TYPES + r")\b\.?"
    r"|(?:(?:N|S|E|W)\.?\s+|(?:North|South|East|West)\s+)?Broadway\b)"     # "1801 Broadway"
    r"(?:,?\s+(?:Suite|Ste\.?|Unit|Building|Bldg\.?)\s+[A-Za-z0-9\-]+)?"
)
BAD_ADDR_WORDS = re.compile(r"\b(?:Square|Million|Billion|Percent|Acres?|Units?|Feet|Foot|Year|Years|Phase|"
                            r"Class|Top|Under|Fortune|Inc|Best|Fastest|Days?|Months?|Weeks?|People|Employees|"
                            r"Jobs|Homes|Apartments|Rooms|Beds|Stories|Story)\b")

# Colorado municipalities (and a few well-known unincorporated places). Not exhaustive.
CITIES = """Denver;Colorado Springs;Aurora;Fort Collins;Lakewood;Thornton;Arvada;Westminster;Pueblo;Greeley;
Centennial;Boulder;Longmont;Castle Rock;Loveland;Broomfield;Grand Junction;Commerce City;Parker;Littleton;
Brighton;Windsor;Northglenn;Englewood;Wheat Ridge;Erie;Lafayette;Fountain;Evans;Louisville;Montrose;Golden;
Johnstown;Durango;Firestone;Frederick;Canon City;Cañon City;Greenwood Village;Superior;Lone Tree;Federal Heights;
Sterling;Castle Pines;Fruita;Steamboat Springs;Fort Morgan;Berthoud;Timnath;Wellington;Severance;Milliken;
Glenwood Springs;Alamosa;Rifle;Gypsum;Trinidad;Woodland Park;Edgewater;Sheridan;Cherry Hills Village;Lochbuie;
Dacono;Fort Lupton;Eagle;Avon;Vail;Aspen;Breckenridge;Frisco;Silverthorne;Dillon;Keystone;Telluride;
Crested Butte;Gunnison;Salida;Buena Vista;Leadville;Craig;Cortez;Lamar;La Junta;Monument;Manitou Springs;
Palmer Lake;Estes Park;Lyons;Niwot;Nederland;Mead;Platteville;Hudson;Keenesburg;Bennett;Watkins;Strasburg;
Elizabeth;Kiowa;Larkspur;Sedalia;Morrison;Evergreen;Conifer;Idaho Springs;Georgetown;Black Hawk;Central City;
Winter Park;Fraser;Granby;Kremmling;Carbondale;Basalt;Snowmass Village;New Castle;Silt;Parachute;Palisade;
Delta;Pagosa Springs;Bayfield;Ignacio;Walsenburg;Florence;Burlington;Limon;Yuma;Wray;Brush;Eaton;Ault;
Pierce;Nunn;LaSalle;Kersey;Gilcrest;Glendale;Lakeside;Mountain View;Bow Mar;Columbine Valley;Foxfield;
Highlands Ranch;Ken Caryl;Pueblo West;Security-Widefield;Falcon;Black Forest;Henderson;Dove Valley;Meridian;
Inverness;Interlocken;Gunbarrel;Green Valley Ranch;Lone Tree;Edwards;Minturn;Mt. Crested Butte;Ouray;Ridgway;
Silverton;Meeker;Rangely;Hayden;Oak Creek;Walden;Julesburg;Holyoke;Akron;Hugo;Cheyenne Wells;Springfield;
Rocky Ford;Las Animas;Monte Vista;Del Norte;Creede;Lake City;Fairplay;Alma;Bailey;Cripple Creek;Victor;
Westcliffe;Penrose;Fowler;Ordway;Eads;Byers;Deer Trail;Roxborough;Castle Pines North;Loveland;Wiggins"""
CITIES = sorted({c.strip() for c in CITIES.replace("\n", "").split(";") if c.strip()}, key=len, reverse=True)
# Names that are also surnames, first names or ordinary words: need extra context to count as a city.
AMBIG = {"Golden", "Parker", "Superior", "Sterling", "Eagle", "Rifle", "Silt", "Dillon", "Evans", "Frederick",
         "Windsor", "Mead", "Lyons", "Erie", "Johnstown", "Fountain", "Centennial", "Aurora", "Brighton",
         "Avon", "Craig", "Delta", "Florence", "Victor", "Hudson", "Bennett", "Elizabeth", "Frisco",
         "Meridian", "Inverness", "Falcon", "Henderson", "Keystone", "Lafayette", "Louisville", "Glendale",
         "Lakeside", "Mountain View", "Sheridan", "Springfield", "Burlington", "Fraser", "Bailey", "Hugo",
         "Akron", "Alma", "Pierce", "Brush", "Eaton", "Yuma", "Wellington", "Trinidad", "Monument", "Basalt",
         "Walden", "Hayden", "Marble", "Thornton", "Morrison", "Watkins", "Edwards", "Fowler", "Ordway",
         "Westminster", "Lakewood", "Englewood", "Loveland", "Montrose", "Severance", "Evergreen", "Kiowa",
         "Limon", "Vail", "Aspen", "Boulder", "Pueblo", "Durango", "Gypsum", "Salida", "Cortez", "Lamar",
         "Georgetown", "Platteville", "Palisade", "Ouray", "Victor", "Penrose", "Byers", "Wiggins", "Ault"}
CITY_RE = re.compile(r"(?<![A-Za-z])(" + "|".join(re.escape(c) for c in CITIES) + r")(?![A-Za-z])")
# after-word that turns the match into something that is not the city
NOT_CITY_AFTER = re.compile(r"^\s+(?:Triangle|Court|Street|St\b|Avenue|Ave\b|Boulevard|Blvd|Road|Rd\b|Drive|"
                            r"Parkway|Way\b|Bank|University|Health|County|Group|Partners|Properties|Capital|"
                            r"Construction|Companies|Realty|Development Co|Investments|Building Systems|"
                            r"Station|Airport|Mall|Creek|Peak|Canyon|Pass\b|Valley|Lane|Place|Plaza|Tower)")
CTX_BEFORE = re.compile(r"(?:\b(?:in|In|to|at|near|of|from|outside|across|throughout|downtown|Downtown|"
                        r"north|south|east|west|northeast|northwest|southeast|southwest|suburban|and|or)\s+|[,/]\s*)$")
CTX_AFTER = re.compile(r"^(?:,\s*(?:Colo|CO\b|Colorado)|[’']s\b|-based|\s+(?:HQ|Headquarters|Facility|Campus|"
                       r"Office|Site|Property|Project|Building|Center|Community|Location|Store|Warehouse|"
                       r"Industrial|Retail|Apartment|Apartments|Multifamily|Hotel|Hospital|Clinic|Plant|"
                       r"Land|Parcel|Portfolio|Shopping|Business Park|Development|Branch|Restaurant|"
                       r"City Council|Planning|Urban Renewal|Market|Submarket|Expansion))")


FIRM_BASE = re.compile(r"(?:offices?|headquartered|headquarters|based|locations|firm|company|branch(?:es)?)\s+"
                       r"(?:located\s+)?in\s+(?:downtown\s+)?(?:[A-Z][a-z]+(?:,| and| or)\s+){0,3}$")


def find_cities(text, strict):
    """Colorado city names in text, in order. strict=True: ambiguous names need place-like context."""
    out = []
    for m in CITY_RE.finditer(text):
        c = m.group(1)
        after = text[m.end():m.end() + 40]
        before = text[max(0, m.start() - 20):m.start()]
        if NOT_CITY_AFTER.match(after):
            continue
        if c in AMBIG and strict and not (CTX_BEFORE.search(before) or CTX_AFTER.match(after)):
            continue
        # a firm's home base ("Golden-based", "with an office in Fort Collins") is not the site
        if strict and (after.startswith("-based") or FIRM_BASE.search(text[max(0, m.start() - 45):m.start()])):
            continue
        out.append((m.start(), "Cañon City" if c == "Canon City" else c))
    return out


def find_addresses(text):
    """[(pos, address, city_after, zip_after)] for every street address in text."""
    out = []
    for m in ADDR_RE.finditer(text):
        a = re.sub(r"\s+", " ", m.group(0)).strip(" .,")
        if BAD_ADDR_WORDS.search(m.group(2)):
            continue
        num = m.group(1)
        # a bare 4-digit 20xx/19xx number right after a month or "in"/"since" is a year, not a house number
        pre = text[max(0, m.start() - 14):m.start()]
        if re.fullmatch(r"(19|20)\d\d", num) and re.search(
                r"(?:\b(?:in|In|since|Since|by|By|early|late|mid|during|through|until|of|for|and)\s|[,\-–]\s?|"
                r"\b(?:Q[1-4]|January|February|March|April|May|June|July|August|September|October|November|"
                r"December|Jan\.|Feb\.|Aug\.|Sept\.|Oct\.|Nov\.|Dec\.)\s(?:\d{1,2},\s)?)$", pre):
            continue
        tail = text[m.end():m.end() + 90]
        tc = find_cities(tail, strict=False)
        city = tc[0][1] if tc and tc[0][0] <= 60 else ""
        z = re.search(r"\b(?:CO|Colo\.?|Colorado)\s+(8[01]\d{3})\b", tail)
        out.append((m.start(), a, city, z.group(1) if z else ""))
    return out


VERBS = (r"Opens|Breaks Ground|Leases|Signs|Inks|Acquires|Purchases|Buys|Sells|Completes|Expands|Relocates|"
         r"Moves|Announces|Unveils|Begins|Starts|Celebrates|Tops Out|Secures|Closes|Lands|Selects|Launches|"
         r"Plans|Proposes|Submits|Files|Delivers|Hires|Names|Promotes|Welcomes|Appoints|Adds|Arranges|"
         r"Brokers|Finances|Wraps|Finishes|Debuts|Establishes|Picks|"
         r"Chooses|Wins|Awarded|Receives|Breaks|Kicks Off|Commences|Doubles|Grows|Invests|Brings|Nears")
CO_RE = re.compile(r"^(?P<co>[A-Z0-9][^,:;|?!“”\"]{1,60}?)\s+(?P<verb>" + VERBS + r")\b(?P<rest>.*)$")
GENERIC_LAST = {"company", "firm", "developer", "developers", "manufacturer", "retailer", "maker", "startup",
                "provider", "brand", "chain", "giant", "builder", "team", "project", "building", "tower",
                "campus", "center", "centre", "community", "apartments", "complex", "development", "park",
                "district", "portfolio", "property", "site", "plaza", "hotel", "hospital", "school", "station",
                "market", "sector", "industry", "council", "voters", "officials", "leaders", "investors",
                "investor", "buyer", "owner", "tenant", "tenants", "sales", "rents", "vacancy", "construction",
                "report", "study", "survey", "colorado", "homes", "lofts", "flats", "residences", "crossing",
                "marketplace", "mall", "shops", "square", "commons", "village", "ranch", "facility", "office",
                "warehouse", "store", "restaurant", "concept", "operator", "group's", "program", "initiative",
                "partnership", "venture", "landlord", "lender", "outlook", "activity", "demand", "pipeline",
                "bottler", "bookstore", "racing", "agency", "franchise", "bar", "housing",
                "families", "block", "shop", "destination", "high-rise", "hall", "cutting", "technicians",
                "expansion", "renovation", "headquarters", "hq", "care", "eatery", "bakeshop", "committee",
                "course", "gardens", "club", "suites", "spa", "resort", "dual-hotel", "garden", "paseo",
                "farm", "north", "creek", "show", "leisure", "pickleball", "studio", "foundation's",
                "city", "county", "state", "town", "neighborhood", "corridor", "airport", "library", "museum",
                "church", "clinic", "terminal", "stadium", "arena", "bridge", "line", "street", "avenue"}
LOWER_OK = {"and", "of", "the", "&", "for", "de", "at", "on", "in", "by"}


def headline_company(title, city_names, excerpt=""):
    """Subject organisation of the headline, or ''. Deliberately conservative."""
    m = CO_RE.match(title)
    if not m:
        return "", ""
    co, verb, rest = m.group("co").strip(), m.group("verb"), m.group("rest")
    words = co.split()
    if not (1 <= len(words) <= 5):
        return "", ""
    # property names, descriptions and people are not companies
    if words[0][0].isdigit() or re.search(
            r"\b(?:in|at|on|for|by|of)\b|[’']s?\s|-(?:Based|Key|Focused|Themed|Efficient|Nominated|Performing|"
            r"Inclusive|Unit|Acre|Story|Owned|Use|Rise|Hotel|Leasing)\b|\b(?:Phase|Approves|Officially|Proudly|"
            r"Orchestrates|Sign|First|Newest|Largest|Chef|Polis|Affordable|Luxury|Historic)\b", co):
        if not re.match(r"^(?:Bank of|Academy of|University of|City of|Town of|State of|Habitat for)\b", co):
            return "", ""
    if co in {"CRE", "AP", "Completion", "Coworking", "Campaign", "Elements", "Madeline", "Lucero", "ACT",
              "HOST", "ENR", "Ribbon Cutting", "Pre-Leasing"}:
        return "", ""
    if re.search(r"[\$%]|\d{4}|\bSF\b|\bQ[1-4]\b|\b(?:Acre|Unit|Story|Million|Billion)\b", co):
        return "", ""
    if words[-1].lower().strip("’'s") in GENERIC_LAST or words[-1].lower() in GENERIC_LAST:
        return "", ""
    if words[0].lower() in {"new", "a", "an", "the", "how", "why", "what", "when", "where", "this", "these",
                            "former", "historic", "local", "first", "more", "two", "three", "four", "five",
                            "six", "report", "study", "construction", "developer", "developers", "ground",
                            "work", "city", "town", "state", "national", "global", "major", "top", "one", "mayor", "gov.",
                            "governor", "sen.", "senator", "rep.", "grand", "fortune", "united", "colorado", "denver"}:
        return "", ""
    for w in words:
        if w[0].islower() and w.lower() not in LOWER_OK:
            return "", ""
    if " and " in f" {co} " and len(words) > 4:      # "A and B ..." joint subjects: ambiguous
        return "", ""
    if co in city_names or co in {"Colorado", "Denver Metro", "Metro Denver", "Front Range", "Northern Colorado",
                                  "Downtown Denver", "RiNo", "LoDo", "Cherry Creek", "DIA", "DTC"}:
        return "", ""
    low = f"{verb} {rest}".lower()
    role = "unknown"
    if (verb in {"Leases", "Signs", "Inks"} and re.search(r"\b(?:leases|lease)\b", low)
            and not re.search(r"\bto\b", rest)
            and re.search(re.escape(co) + r".{0,120}?\b(?:has signed|has leased|signed a|has inked|will lease|"
                          r"is leasing|will occupy|will relocate|is relocating|has relocated)\b", excerpt)
            and not re.search(re.escape(co) + r".{0,120}?\bannounced that\b", excerpt)):
        role = "tenant"   # headline says the company leased, and the excerpt has it signing or occupying
    elif verb in {"Proposes", "Submits", "Files"}:
        role = "applicant"
    elif re.search(r"\b(?:Construction|Constructors|Builders|Contractors|Contracting)\b", co) and verb in {
            "Completes", "Breaks Ground", "Breaks", "Tops Out", "Begins", "Starts", "Wraps", "Finishes",
            "Delivers", "Commences", "Kicks Off", "Selected", "Awarded", "Wins"}:
        role = "contractor"
    return co, role


# ---------------------------------------------------------------- fetch
def load_cache():
    posts = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            for line in f:
                p = json.loads(line)
                posts[p["id"]] = p
    return posts


def strip_post(p, fetched_at):
    """Keep id/date/link/title/categories/excerpt; replace full content by the facts extracted from it."""
    body = clean(p.get("content", {}).get("rendered", ""))
    return {
        "id": p["id"], "date": p["date"], "link": p["link"],
        "title": clean(p["title"]["rendered"]), "categories": p.get("categories", []),
        "excerpt": clean(p["excerpt"]["rendered"]),
        "content_addresses": [[a, c, z] for _, a, c, z in find_addresses(body)],
        "content_chars": len(body), "fetched_at": fetched_at,
    }


def fetch(full=False):
    os.makedirs(RAW, exist_ok=True)
    cats, _ = get(f"{BASE}/categories?per_page=100&_fields=id,name,slug,count")
    json.dump(cats, open(CATS, "w"), indent=0)
    posts = {} if full else load_cache()
    after = max([p["date"] for p in posts.values()], default=START) if posts else START
    if full and os.path.exists(CACHE):
        os.rename(CACHE, CACHE + ".bak")
    page, total = 1, None
    with open(CACHE, "a", encoding="utf-8") as out:
        while True:
            url = (f"{BASE}/posts?after={after}&per_page=100&page={page}&orderby=date&order=asc"
                   "&_fields=id,date,link,title,categories,excerpt,content")
            data, hdr = get(url)
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if total is None:
                total = int(hdr.get("x-wp-total", 0))
                pages = int(hdr.get("x-wp-totalpages", 0))
                print(f"after={after}: source reports {total} posts in {pages} pages")
            for p in data:
                s = strip_post(p, now)
                posts[s["id"]] = s
                out.write(json.dumps(s, ensure_ascii=False) + "\n")
            out.flush()
            print(f"  page {page}: {len(data)} posts")
            if page >= pages or not data:
                break
            page += 1
    return posts, total


# ---------------------------------------------------------------- build CSV
def build(posts):
    cats = {c["id"]: c for c in json.load(open(CATS))}
    city_names = set(CITIES)
    rows = []
    for p in sorted(posts.values(), key=lambda x: (x["date"], x["id"])):
        if p["date"] < START:
            continue
        slugs = [cats[c]["slug"] for c in p["categories"] if c in cats]
        names = [html.unescape(cats[c]["name"]) for c in p["categories"] if c in cats]
        people = bool(PEOPLE_SLUGS & set(slugs))
        title, exc = p["title"], re.sub(r"\s*\[?(?:…|\.\.\.)\]?\s*$", "", p["excerpt"])
        if people or re.match(r"By\s+[A-Z]", exc):   # byline-led excerpt (contributed article): headline only
            exc = ""
        t_addr, e_addr = find_addresses(title), find_addresses(exc)
        c_addr = [(0, a, c, z) for a, c, z in p.get("content_addresses", [])] if not people else []
        t_city, e_city = find_cities(title, True), find_cities(exc, True)
        post_city = t_city[0][1] if t_city else (e_city[0][1] if e_city else "")
        addr = city = zc = ""
        basis = "none"
        for label, text, found in (("title", title, t_addr), ("excerpt", exc, e_addr)):
            for pos, a, ac, az in found:
                if not ac:
                    # no city right after the address: nearest city named in the same text (within 200
                    # characters), else the headline city, else the first excerpt city
                    near = sorted((abs(cp - pos), cn) for cp, cn in find_cities(text, True) if abs(cp - pos) <= 200)
                    ac = near[0][1] if near else post_city
                if ac:                      # Colorado context is required
                    addr, city, zc, basis = a, ac, az, label
                    break
            if addr:
                break
        if not addr:
            # body text: lower confidence (may be a sales office or a comparable property), so only use it
            # when the body names exactly one distinct address
            distinct = {a.lower(): (a, ac, az) for _, a, ac, az in c_addr}
            if len(distinct) == 1:
                a, ac, az = next(iter(distinct.values()))
                if ac or post_city:
                    addr, city, zc, basis = a, ac or post_city, az, "content"
        if not addr and post_city:
            city, basis = post_city, ("title" if t_city else "excerpt")
        company, role = ("", "") if people else headline_company(title, city_names, exc)
        if company and basis == "none":
            basis = "title"
        seen, all_addr = set(), []
        for _, a, ac, az in t_addr + e_addr + c_addr:
            if a.lower() not in seen:
                seen.add(a.lower())
                all_addr.append(a + (f", {ac}" if ac else ""))
        desc = title if not exc else f"{title} | {exc}"
        if len(desc) > 500:
            desc = desc[:499].rstrip() + "…"
        ind = INDUSTRIAL_ID in p["categories"]
        rows.append({
            "source": "Mile High CRE", "source_level": "State (Colorado)", "record_id": p["id"],
            "record_date": p["date"][:10], "date_type": "published", "record_type": "news post",
            "company_name": company, "company_role": role if company else "unknown",
            "site_address": addr, "city": city, "county": "Denver" if city == "Denver" else "", "zip": zc,
            "description": desc, "flag": "Y" if ind else "N",
            "flag_rule": "industrial category" if ind else "", "source_url": p["link"],
            "retrieved_at": p["fetched_at"], "categories": "; ".join(names), "extraction_basis": basis,
            "addresses_all": "; ".join(all_addr), "parser_version": PARSER_VERSION,
        })
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUT}")
    return rows


if __name__ == "__main__":
    if "--parse-only" in sys.argv:
        build(load_cache())
    else:
        posts, total = fetch(full="--full" in sys.argv)
        build(posts)
