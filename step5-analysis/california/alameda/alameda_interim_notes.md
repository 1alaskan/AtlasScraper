# Alameda County: interim evidence stack (not a ranking)

Built 2026-11-10 from California state sources only. File: `alameda_interim_evidence_stack.csv`.

**What this is not.** It is not the v3 ranking. It has no points, no stage, no compressed-air fit test, no noise cuts, no geocoding, no review. It groups flagged rows by company name key (or by address where there is no name) and counts distinct sources. No city permit, planning or air district data is in it, and no machinery-lien data exists for California yet.

**Inputs.** 847 Alameda County rows from six state sources, 283 flagged: industrial stormwater 117, CEQA 63, ABC 61, construction stormwater 31, CAEATFA 6, California Competes 5.

**Result.** 193 grouped rows. 6 have two sources, 187 have one. 10 carry a named incentive award.

Two-source rows: Atomic Machines (Emeryville), Lam Research (Fremont), Fuse Energy Technologies (San Leandro), Anthro Energy (Alameda), Del Cielo Brewing (Livermore), The Gold Bar Spirits Company (Alameda).

**Known weaknesses.** Award rows have no street address, so an award and a stormwater row for the same company join only when the names match exactly after normalising. Multi-site awards (Skydio, Sparkz, Atomic Machines) are listed although the Alameda County share is unknown. CEQA rows have no company name. Person-named businesses have not been removed beyond the rough filter in the pull. Nothing here has been checked against the web.
