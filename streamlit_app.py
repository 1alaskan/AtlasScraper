"""Atlas lead pipeline: ranked compressed-air accounts by Colorado county.

Reads dashboard/counties.json (one entry per finished county run) and shows
the ranked account list, the evidence behind each account, and the run notes.
Register a new county with dashboard/register_county.py and push to main.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "dashboard" / "counties.json"

st.set_page_config(
    page_title="Atlas lead pipeline",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

RANKED_COLS = [
    "rank", "company_name", "site_address", "zip", "score", "tier", "stage",
    "sources_count", "latest_signal_date", "first_signal_date", "match_confidence",
    "compressed_air_fit", "next_step", "in_ground_truth",
]
EVIDENCE_COLS = [
    "source", "record_date", "record_type", "company_name", "company_role",
    "site_address", "city", "zip", "description", "flag_tier", "points",
    "record_id", "source_url",
]


# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_registry() -> list[dict]:
    if not REGISTRY.exists():
        return []
    reg = json.loads(REGISTRY.read_text())
    return sorted(reg.get("counties", []), key=lambda c: c.get("run_date", ""), reverse=True)


@st.cache_data(show_spinner="Loading ranked accounts…")
def load_ranked(path: str) -> pd.DataFrame:
    df = pd.read_csv(ROOT / path, dtype=str, keep_default_na=False)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").astype("Int64")
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["sources_count"] = pd.to_numeric(df.get("sources_count", 0), errors="coerce").astype("Int64")
    for c in ("first_signal_date", "latest_signal_date"):
        if c in df:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    df["gt_hit"] = df["in_ground_truth"].str.startswith("yes") if "in_ground_truth" in df else False
    return df


@st.cache_data(show_spinner="Loading evidence…")
def load_evidence(path: str) -> pd.DataFrame:
    df = pd.read_csv(ROOT / path, dtype=str, keep_default_na=False)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").astype("Int64")
    df["points"] = pd.to_numeric(df.get("points", 0), errors="coerce")
    df["record_date"] = pd.to_datetime(df["record_date"], errors="coerce").dt.date
    return df


@st.cache_data(show_spinner=False)
def load_text(path: str) -> str:
    p = ROOT / path
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else f"_{path} not found_"


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# ----------------------------------------------------------------------------
# Sidebar: county + filters
# ----------------------------------------------------------------------------
counties = load_registry()
if not counties:
    st.error("No counties registered. Run `dashboard/register_county.py` and push.")
    st.stop()

st.sidebar.title("Atlas lead pipeline")
names = [c["name"] for c in counties]
chosen = st.sidebar.selectbox("County", names, index=0)
county = next(c for c in counties if c["name"] == chosen)
st.sidebar.caption(f"Ranking {county.get('version', '')} · built {county.get('run_date', '?')}")

ranked = load_ranked(county["ranked"])
evidence = load_evidence(county["evidence"])

st.sidebar.divider()
st.sidebar.subheader("Filters")
q = st.sidebar.text_input("Search name / address / evidence", placeholder="e.g. Pepsi, 72nd Ave, dairy")

tiers = sorted(ranked["tier"].unique().tolist())
sel_tiers = st.sidebar.multiselect("Tier", tiers, default=tiers,
                                   help="A = strong-signal sources; B = wider flags; A+B = both")

stages = sorted(ranked["stage"].unique().tolist())
sel_stages = st.sidebar.multiselect("Stage", stages, default=stages)

confs = sorted(ranked["match_confidence"].unique().tolist())
sel_conf = st.sidebar.multiselect("Match confidence", confs, default=confs)

smin, smax = float(ranked["score"].min()), float(ranked["score"].max())
score_floor = st.sidebar.slider("Minimum score", min_value=float(int(smin)), max_value=float(int(smax)),
                                value=float(int(smin)), step=1.0)

all_sources = sorted({s.strip() for row in ranked["sources"] for s in row.split(";") if s.strip()})
sel_sources = st.sidebar.multiselect("Must include source", all_sources, default=[])

named_only = st.sidebar.checkbox("Named companies only", value=False,
                                 help="Hide rows that are an address with no company attached")
gt_only = st.sidebar.checkbox("Ground-truth hits only", value=False)
top_n = st.sidebar.number_input("Show top N (0 = all)", min_value=0, max_value=5000, value=0, step=25)

# apply filters
f = ranked.copy()
f = f[f["tier"].isin(sel_tiers) & f["stage"].isin(sel_stages) & f["match_confidence"].isin(sel_conf)]
f = f[f["score"] >= score_floor]
if sel_sources:
    f = f[f["sources"].apply(lambda s: all(src in s for src in sel_sources))]
if named_only:
    f = f[~f["match_confidence"].str.contains("not attached|code name", regex=True)]
if gt_only:
    f = f[f["gt_hit"]]
if q:
    ql = q.lower()
    hay = (f["company_name"] + " | " + f["name_variants"] + " | " + f["site_address"] + " | "
           + f["top_evidence"] + " | " + f["compressed_air_fit"] + " | " + f["zip"]).str.lower()
    f = f[hay.str.contains(ql, regex=False)]
f = f.sort_values("rank")
if top_n:
    f = f.head(int(top_n))

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.title(f"{county['name']}: ranked accounts")
st.caption("Companies and sites with signals of growing compressed-air demand. "
           "Score is the fixed v3 points table; nothing here uses Atlas Copco data.")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Accounts shown", f"{len(f):,}", help=f"of {len(ranked):,} ranked")
k2.metric("Tier A or A+B", f"{int(f['tier'].isin(['A', 'A+B']).sum()):,}")
k3.metric("Named companies", f"{int((~f['match_confidence'].str.contains('not attached|code name', regex=True)).sum()):,}")
k4.metric("Latest signal", str(f["latest_signal_date"].max()) if len(f) else "—")
k5.metric("Ground-truth hits", f"{int(f['gt_hit'].sum())} / {int(ranked['gt_hit'].sum())}")

tab_list, tab_detail, tab_evidence, tab_notes, tab_compare = st.tabs(
    ["Ranked list", "Account detail", "Evidence", "Run notes", "Across counties"]
)

# ----------------------------------------------------------------------------
# Ranked list
# ----------------------------------------------------------------------------
with tab_list:
    st.download_button("Download filtered list (CSV)", csv_bytes(f.drop(columns=["gt_hit"])),
                       file_name=f"{county['slug']}_ranked_filtered.csv", mime="text/csv")
    show = f[RANKED_COLS].rename(columns={
        "company_name": "Company / site", "site_address": "Address", "sources_count": "Src",
        "latest_signal_date": "Latest signal", "first_signal_date": "First signal",
        "match_confidence": "Confidence", "compressed_air_fit": "Air fit",
        "next_step": "Next step", "in_ground_truth": "Ground truth",
    })
    event = st.dataframe(
        show,
        width="stretch",
        hide_index=True,
        height=620,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "rank": st.column_config.NumberColumn("#", width="small"),
            "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=float(smax), format="%.0f"),
            "tier": st.column_config.TextColumn("Tier", width="small"),
            "zip": st.column_config.TextColumn("ZIP", width="small"),
            "Src": st.column_config.NumberColumn("Src", width="small"),
            "Air fit": st.column_config.TextColumn("Air fit", width="large"),
            "Next step": st.column_config.TextColumn("Next step", width="large"),
        },
    )
    picked = event.selection.rows if event and event.selection else []
    if picked:
        st.session_state["picked_rank"] = int(f.iloc[picked[0]]["rank"])
        st.info(f"Selected rank {st.session_state['picked_rank']}: open the **Account detail** tab.")
    else:
        st.caption("Click a row to pick an account, then open the Account detail tab.")

# ----------------------------------------------------------------------------
# Account detail
# ----------------------------------------------------------------------------
with tab_detail:
    options = f["rank"].tolist()
    if not options:
        st.warning("No accounts match the current filters.")
    else:
        labels = {int(r): f"#{int(r)} · {n}" for r, n in zip(f["rank"], f["company_name"])}
        default = st.session_state.get("picked_rank", int(options[0]))
        if default not in labels:
            default = int(options[0])
        rank_sel = st.selectbox("Account", options, index=options.index(default),
                                format_func=lambda r: labels[int(r)])
        row = ranked[ranked["rank"] == rank_sel].iloc[0]

        st.subheader(row["company_name"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score", f"{row['score']:.0f}")
        c2.metric("Tier", row["tier"])
        c3.metric("Stage", row["stage"].split(" (")[0])
        c4.metric("Sources", int(row["sources_count"]) if pd.notna(row["sources_count"]) else 0)

        left, right = st.columns([3, 2])
        with left:
            st.markdown(f"**Address:** {row['site_address']} {row['zip']}".strip())
            if row.get("name_variants"):
                st.markdown(f"**Also filed as:** {row['name_variants']}")
            st.markdown(f"**County basis:** {row['county_basis']}")
            st.markdown(f"**Match confidence:** {row['match_confidence']}")
            st.markdown(f"**Signal window:** {row['first_signal_date']} → {row['latest_signal_date']}")
            st.markdown(f"**Sources:** {row['sources']}")
            if row["in_ground_truth"] != "no":
                st.success(f"Ground truth: {row['in_ground_truth']}")
        with right:
            st.markdown("**Compressed-air fit**")
            st.write(row["compressed_air_fit"] or "—")
            st.markdown("**Next step**")
            st.write(row["next_step"] or "—")

        st.markdown("**Top evidence**")
        for item in [s.strip() for s in row["top_evidence"].split("||") if s.strip()]:
            if item.startswith("Points:"):
                st.caption(item)
            else:
                st.markdown(f"- {item}")

        st.markdown("**All source records behind this account**")
        ev = evidence[evidence["rank"] == rank_sel].sort_values(["points", "record_date"], ascending=[False, False])
        st.dataframe(
            ev[[c for c in EVIDENCE_COLS if c in ev.columns]],
            width="stretch", hide_index=True,
            column_config={"source_url": st.column_config.LinkColumn("Link", display_text="open")},
        )

# ----------------------------------------------------------------------------
# Evidence
# ----------------------------------------------------------------------------
with tab_evidence:
    st.caption("Every scraped record that attached to a ranked account, with its points and source link.")
    ev_all = evidence[evidence["rank"].isin(f["rank"])]
    srcs = sorted(ev_all["source"].unique().tolist())
    e1, e2, e3 = st.columns([2, 1, 1])
    sel_ev_src = e1.multiselect("Source", srcs, default=srcs)
    min_pts = e2.number_input("Min points", min_value=0.0, value=0.0, step=1.0)
    flagged_only = e3.checkbox("Flagged rows only", value=False)
    ev_f = ev_all[ev_all["source"].isin(sel_ev_src) & (ev_all["points"] >= min_pts)]
    if flagged_only and "flag" in ev_f:
        ev_f = ev_f[ev_f["flag"] == "Y"]
    st.write(f"{len(ev_f):,} records")
    st.download_button("Download evidence (CSV)", csv_bytes(ev_f),
                       file_name=f"{county['slug']}_evidence_filtered.csv", mime="text/csv")
    st.dataframe(
        ev_f[["rank"] + [c for c in EVIDENCE_COLS if c in ev_f.columns]].sort_values(["rank", "points"], ascending=[True, False]),
        width="stretch", hide_index=True, height=600,
        column_config={"source_url": st.column_config.LinkColumn("Link", display_text="open")},
    )
    st.markdown("**Records by source**")
    st.bar_chart(ev_all.groupby("source").size().sort_values(ascending=False), horizontal=True)

# ----------------------------------------------------------------------------
# Run notes
# ----------------------------------------------------------------------------
with tab_notes:
    note_files = [county["notes"], *county.get("extra_notes", [])]
    pick = st.radio("File", note_files, horizontal=True, format_func=lambda p: Path(p).name)
    st.markdown(load_text(pick))

# ----------------------------------------------------------------------------
# Across counties
# ----------------------------------------------------------------------------
with tab_compare:
    rows = []
    for c in counties:
        d = load_ranked(c["ranked"])
        named = ~d["match_confidence"].str.contains("not attached|code name", regex=True)
        rows.append({
            "County": c["name"], "Version": c.get("version", ""), "Built": c.get("run_date", ""),
            "Ranked": len(d), "Tier A": int((d["tier"] == "A").sum()), "Tier A+B": int((d["tier"] == "A+B").sum()),
            "Tier B": int((d["tier"] == "B").sum()), "Named companies": int(named.sum()),
            "Score ≥ 60": int((d["score"] >= 60).sum()), "Ground-truth hits": int(d["gt_hit"].sum()),
            "Latest signal": str(d["latest_signal_date"].max()),
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    st.markdown("**Top 25 across all counties**")
    frames = []
    for c in counties:
        d = load_ranked(c["ranked"]).copy()
        d.insert(0, "county", c["name"])
        frames.append(d)
    allr = pd.concat(frames).sort_values("score", ascending=False).head(25)
    st.dataframe(allr[["county", "rank", "company_name", "site_address", "score", "tier", "stage", "latest_signal_date"]],
                 width="stretch", hide_index=True)

    st.markdown("**Score distribution**")
    bins = [-20, 0, 20, 40, 60, 80, 100, 200]
    labels_b = ["<0", "0–19", "20–39", "40–59", "60–79", "80–99", "100+"]
    hist = {}
    for c in counties:
        d = load_ranked(c["ranked"])
        hist[c["name"]] = pd.cut(d["score"], bins=bins, labels=labels_b, right=False).value_counts().reindex(labels_b)
    st.bar_chart(pd.DataFrame(hist))
