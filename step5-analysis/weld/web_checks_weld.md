# Weld County web checks (top 60 ranked accounts)

Date of check: 2026-11-06. Rule applied: at most one WebSearch and one WebFetch per company, limited to what the company does at the ranked site and whether the site is in Weld County. No people, contact, LinkedIn or Atlas Copco lookups. Where the web turned up nothing, the level is `unknown` even when the pipeline's own permit record is explicit; the basis says so.

Counts: strong 15, moderate 10, weak 17, unknown 18.

## 1. Dict entries

```python
WEB_CHECKS_WELD = {
    'AGILENT TECHNOLOGIES US': ('strong', 'Pharmaceutical manufacturing (therapeutic nucleic acids: siRNA, antisense, CRISPR guide RNA) at the Frederick site, with a $725M manufacturing expansion under way; trade press (web check 2026-11-06).'),
    'SUNSET INDUSTRIAL PIT': ('weak', 'Sand and gravel pit operated by J-2 Contracting adjacent to Greeley city limits and 8th Street in Weld County, no plant described; state DRMS permit file M2023001 (web check 2026-11-06).'),
    'ASPHALT SPECIALTIES': ('weak', 'Family-owned heavy highway paving contractor; the ranked site is its Marcovich sand and gravel pit on US-85 and no asphalt plant at that site was confirmed; government vendor profile plus state air permit text (web check 2026-11-06).'),
    'USRL HUDSON': ('weak', 'Rail-served transload terminal at 2001 LCH Ave, Hudson, handling dry bulk, liquids and refined fuels (gasoline loading units); transload directory and job postings (web check 2026-11-06).'),
    'BOULDER SCIENTIFIC': ('strong', 'Specialty chemical and organometallic catalyst production plant at Specialty Place, Mead, one of the company two Colorado production sites; trade press plus state air permit naming catalyst manufacturing (web check 2026-11-06).'),
    'SCHLOSSER SIGNS': ('moderate', 'Designs, manufactures and installs commercial signs with in-house fabrication and a new paint booth, CNC router not confirmed on the web; company press release and Blue Book manufacturer listing (web check 2026-11-06).'),
    'RAPTOR MATERIALS': ('moderate', 'Sand, gravel and ready-mix concrete supplier; the Highway 66 site is its pit and ready-mix plant with screens on the air permit; Blue Book supplier profile plus state permits (web check 2026-11-06).'),
    'URSA MAJOR TECHNOLOGIES': ('strong', 'Rocket engine manufacturing, additive manufacturing and test at the 90-acre former Ball site at 19750 Weld County Road 7, Berthoud; trade press (BizWest) (web check 2026-11-06).'),
    'SVW FARMS': ('weak', 'Farm operator whose site is the Hunt Farms dirt mine south-east of Gilcrest, stripping topsoil and overburden for oil and gas reclamation with no processing equipment; state DRMS inspection M2021030 (web check 2026-11-06).'),
    'OLD SCHOOL INDUSTRIES': ('strong', 'Job machine shop in Dacono financing new DMG Mori and Brother CNC machining centers; NAICS machine-shop directory listing (web check 2026-11-06).'),
    'HIGH PLAINS STEEL SERVICES': ('strong', 'Structural steel fabricator and metal service center at 2055 Howard Smith Ave, Windsor, hiring fitter-welders and ironworkers; NAICS directory, job postings and Blue Book structural steel fabricator listing (web check 2026-11-06).'),
    'UNDERGROUND MANUFACTURING': ('unknown', 'No company page found; 2950 Colorful Ave is a 120,000 sq ft multi-tenant flex building with no tenants named, and only the state air permit says an HP Indigo 25K digital press is installed there (would be strong if confirmed); commercial listing (web check 2026-11-06).'),
    'QUANTUM JS CANNING': ('unknown', 'No web presence found under this name; the canning and chiller equipment in the UCC points to a beverage canning or co-packing line at Skyway Dr, Longmont, but the operator could not be confirmed (web check 2026-11-06).'),
    'CEA GREELY': ('weak', 'Dairy anaerobic digester producing renewable natural gas at Morwai and Longs Peak dairies, per the state air permit; no company web page found (web check 2026-11-06).'),
    'PERFORMANCE EQUIPMENT SALES': ('moderate', 'Heavy construction equipment sales and rental dealer with a service operation at 2114 E I-25 Frontage Rd, Erie (east of I-25, Weld side), financing a service truck with a Vanair compressor; NAICS directory and company site (web check 2026-11-06).'),
    '5507 DISTILLING': ('unknown', 'No page found under this name; the UCC collateral references distillation equipment on Fifth Street, Loveland (Larimer County) and 477 Distilling of Greeley opened a Loveland location in late 2025, so the Weld site is unconfirmed; trade press (web check 2026-11-06).'),
    'CANDO RAIL AND TERMINALS': ('weak', 'Rail transload terminal (former Savage Rail, acquired by Cando) at the Great Western Industrial Park, Windsor, handling drilling-related and agricultural products; company transload page (web check 2026-11-06).'),
    'BURNCO COLORADO': ('moderate', 'Ready-mix concrete and aggregates producer (Westminster HQ) with a Windsor terminal concrete batch plant at 31005 Great Western Drive per the state air permit; Blue Book profile (web check 2026-11-06).'),
    'LOUDWIRE DIESEL': ('unknown', 'No web presence found under this name; the UCC shows a screening plant and conveyor, which suggests aggregate work rather than a shop (web check 2026-11-06).'),
    'JIMS AUTOMOTIVE MACHINE SHOP': ('unknown', 'Search returned only an unrelated Jim\'s Automotive Service in Glenwood Springs; the Gill, CO engine machine shop with Haas CNC lathes in the UCC could not be confirmed on the web (would be strong if confirmed) (web check 2026-11-06).'),
    'PIONEER PRESS OF GREELEY': ('strong', 'Commercial printing plant at 2965 27th Ave, Greeley, with a state air permit for printing and a new Sharp production press; chamber directory listing (web check 2026-11-06).'),
    'BLACK LABEL SERVICES': ('moderate', 'Oil and gas pipeline and related structures construction contractor (about 88 staff) with its own fabrication yard at 629 Gyrfalcon Ct, Windsor, financing a CNC plasma table and press brake; NAICS directory (web check 2026-11-06).'),
    'SCOTTS MIRACLE GRO': ('moderate', 'Hyponex (Scotts) mulch and soil processing and bagging plant at County Road 39, Hudson, per the state air and water permits; web search found no page for this plant (web check 2026-11-06).'),
    'IMPACT EQUIPMENT RENTALS': ('unknown', 'No web page found; the repeated compressor filings read as a rental fleet rather than plant air, which would be weak if confirmed (web check 2026-11-06).'),
    'SWIFT BEEF': ('strong', 'JBS beef slaughter and processing plant at 800 N 8th Ave, Greeley; USDA FSIS inspected establishment record (web check 2026-11-06).'),
    'T AND T GRINDERS': ('unknown', 'No web presence found; the tub grinder and wheel loader in the UCC suggest a mobile grinding or mulch service in the Nunn area (web check 2026-11-06).'),
    'WASTE MANAGEMENT DISPOSAL SERVICES OF COLORADO': ('weak', 'North Weld Landfill, a sanitary landfill at 40000 County Road 25, Ault; Waste Management location page and Weld County news (web check 2026-11-06).'),
    'COLORADO SAND': ('weak', 'Keenesburg No. 2 sand mine, about 3 miles north-east of Keenesburg in Weld County, extraction with screening only; state DRMS inspection M2019058 (web check 2026-11-06).'),
    'STERICYCLE': ('weak', 'Medical waste treatment and transfer plant in Dacono (plant associate roles, listed on the Weld County commercial solid waste facility list); company careers page and county list (web check 2026-11-06).'),
    'AGFINITY': ('weak', 'Farm cooperative bulk fuel and propane plant at Lucerne (an EPA risk management plan facility), not a processing plant; EPA RMP facility record and state air permit (web check 2026-11-06).'),
    'JW FABRICATION': ('strong', 'Metal fabrication shop in Ault building metal products from drawings with welding machines, press brakes and machining tools; production welder-fabricator job posting (web check 2026-11-06).'),
    'DESIGNLOGIC': ('strong', 'Precision CNC milling and turning of industrial, heavy equipment and defense parts in Windsor; Thomasnet supplier profile (web check 2026-11-06).'),
    'TV DAIRY': ('weak', 'Dairy operation and dairy wholesaler at 7678 County Rd 17, Fort Lupton, about 28 staff; the chiller in the UCC is milk cooling; NAICS directory (web check 2026-11-06).'),
    'CUTTING EDGE STEEL': ('strong', 'Fabricated structural metal manufacturer and laser processor (AS9100D, ISO 9001) at 101 Miller Dr, Dacono, about 72 staff, adding a Trumpf machine and cobot welder; NAICS directory and manufacturer directory (web check 2026-11-06).'),
    'PNEU LINE SUPPLY': ('strong', 'Injection molder (Class 7 cleanroom) and assembler of plastic fluidic and pneumatic components for medical and industrial customers in Greeley, adding a Nissei 55 ton press; company capabilities page (web check 2026-11-06).'),
    'CNE CREATIVE ENTERPRISES': ('moderate', 'Product development and consulting firm in Greeley with light fabrication on site (metal bending machine, plastic sheet butt welder in the UCC); City of Greeley business news and NAICS directory (web check 2026-11-06).'),
    'ECLIPSE ENGINEERING': ('strong', 'Engineered seal manufacturer (spring-energized, rotary lip and wear ring seals, machined on CNC lathes) at 2540 S Main St, Erie, about 23 staff; NAICS directory and business listing, but Erie straddles Boulder and Weld and the county of this address was not confirmed (web check 2026-11-06).'),
    'LEGACY PIE': ('unknown', 'Pie bakery with two retail shops in Denver; the web does not place a production kitchen in Windsor, only the parent Colorado Cherry Company has a Windsor outpost; trade press (5280) (web check 2026-11-06).'),
    'ABSOLUTE COUNTERTOPS AND MORE': ('unknown', 'No page confirming the business was reachable (review site failed); the CNC sawjet and digital slab station in the UCC point to a stone countertop fabrication shop, which would be strong if confirmed at a Fort Lupton site (web check 2026-11-06).'),
    'HUNGENBERG PRODUCE': ('moderate', 'Carrot, cabbage and onion grower-packer in Greeley (about 4,000 acres) processing cello and baby carrots with on-site packing; produce trade press (web check 2026-11-06).'),
    'BIG THOMPSON COMPOST': ('unknown', 'No web presence found; the track crusher and stacker conveyor in the UCC suggest a compost or recycled-aggregate yard near Milliken, which would be weak if confirmed (web check 2026-11-06).'),
    'LIVE SHARP INDUSTRIES': ('unknown', 'No web presence found under this name at the I-25 Frontage Rd address; the UCC shows a CNC machining center (web check 2026-11-06).'),
    'BLACK EAGLE ENERGY SERVICES': ('strong', 'Blackeagle Energy Services fabrication shop in Berthoud building mechanical and structural equipment for energy, water and gas clients, hiring structural welders, with a state air permit for metal parts manufacturing at 230 Commerce Drive; job posting and trade press (web check 2026-11-06).'),
    'SCHOTT MANUFACTURING SOLUTIONS': ('unknown', 'No web page found for this name at Bruin Blvd, Frederick; the Haas UMC500 and rotary table in the UCC point to a CNC machine shop, which would be strong if confirmed (web check 2026-11-06).'),
    'UNATTACHED 8440 RASPBERRY WAY': ('unknown', 'No company attached; web shows only neighbouring lots in Raspberry Hill Business Park, Frederick, with no occupier named for lot 17 (web check 2026-11-06).'),
    'FOUR C SONS': ('unknown', 'No web presence found; the planter and feeder conveyor in the UCC suggest a farm with aggregate screening near La Salle (web check 2026-11-06).'),
    'ROCK AND RAIL': ('moderate', 'Rail transload terminal at 27486 Weld County Road 13 with a concrete mixing facility and, per the state air permit, an asphalt plant; company operations page (web check 2026-11-06).'),
    'J AND B MANUFACTURING': ('unknown', 'Web found only J&B Machine LLC, a job machine shop at 370 E 16th St, Greeley, which may or may not be the same business as J&B Manufacturing LLC (would be strong if the same); NAICS directory (web check 2026-11-06).'),
    'BAY STATE MILLING': ('strong', 'Flour mill and grain elevator at Platteville with shift miller and grain handler jobs; job postings and state air permit for milling and bagging (web check 2026-11-06).'),
    'IDENTITY PET NUTRITION': ('weak', 'Pet food brand headquarters and frozen product distribution in Windsor; products are co-manufactured in Ontario and Quebec, so no production on site; trade press (Pet Food Processing) (web check 2026-11-06).'),
    'KEIBON': ('unknown', 'No web presence found; the spray epoxy equipment and static mixers in the UCC suggest a coatings or lining contractor at W 29th St, Greeley (web check 2026-11-06).'),
    'WESTERN PROPPANTS': ('weak', 'Frac sand (proppant) supplier with a LaSalle rail terminal haul road on the state air permit; web returned only the trademark record, no plant confirmed (web check 2026-11-06).'),
    'AULT ASPHALT PLANT SITE': ('moderate', 'Connell Resources asphalt plant site per the state water permit (SIC 2951); the web confirms Connell operates asphalt facilities at its pits (Timnath file) but no page for the Ault site was found; state DRMS file (web check 2026-11-06).'),
    'WELD BESS STORAGE': ('weak', 'Battery energy storage construction site; Michels Power is the permittee and contractor, not the occupier, and the web did not confirm which Weld County BESS project this is; NextEra Weld Energy Storage page is a candidate only (web check 2026-11-06).'),
    'AURORA WATER NORTH CAMPUS': ('weak', 'City of Aurora water collector well field (Prairie Waters) near Fort Lupton; Velocity Constructors is the contractor, the City of Aurora is the owner; construction bid listing (web check 2026-11-06).'),
    'SUN MOUNTAIN': ('strong', 'Custom wood door manufacturing plant at 140 Commerce Drive, Berthoud, with a state air permit for wood sanding and coating; manufacturer facility record (BuildingClean) (web check 2026-11-06).'),
    'C SIMPSON FARMS': ('unknown', 'No web presence found; by name a farm, and the two Atlas Copco XAS-185 units in the UCC are towable compressors, not plant air (web check 2026-11-06).'),
    'COVENANT PLUMBING AND HEATING': ('weak', 'Plumbing and heating contractor based in Ault; the compressor in the UCC is part of a pipe-lining system, no shop production; Angi contractor listing (web check 2026-11-06).'),
    'EATON FIRE PROTECTION DISTRICT': ('weak', 'Public fire district in Eaton; the UCC is SCBA breathing-air equipment, not plant air; state local government record and station listing (web check 2026-11-06).'),
    'ARC COLORADO': ('unknown', 'Web shows an FFL licensee at 7040 County Road 20, Longmont, and a state water permit under SIC 3444 sheet metal, but the business pages failed to load and the product could not be confirmed (web check 2026-11-06).'),
}
```

## 2. Flags

(a) Site may not be in Weld County
- 5507 DISTILLING (rank 16): UCC collateral is distillation equipment on Fifth Street, Loveland (Larimer County). Zip 80634 in the record is Greeley. Not confirmed either way.
- ECLIPSE ENGINEERING (rank 37): address 2540 S Main St, Erie 80516. Erie straddles Boulder and Weld counties and the county of this parcel was not confirmed.
- LEGACY PIE (rank 38): shops are in Denver; no production site in Windsor found on the web.
- (not a flag, for reference) PERFORMANCE EQUIPMENT SALES is at 2114 E I-25 Frontage Rd, Erie, east of I-25, which is the Weld side.

(b) Private individual's name rather than a business
- None in the top 60. JIM'S AUTOMOTIVE MACHINE SHOP, INC. and C. SIMPSON FARMS, LLC carry personal names but are registered entities.

(c) Ranked company looks like a contractor, lender or landlord rather than the occupier
- WELD BESS STORAGE (rank 54): permittee Michels Power Inc. is the EPC contractor. Occupier is the project owner; NextEra's Weld Energy Storage (100 MW, Weld County) is a candidate but the match was not confirmed (NextEra project page).
- AURORA WATER NORTH CAMPUS (rank 55): permittee Velocity Constructors Inc. is the contractor. Occupier is the City of Aurora (Aurora Water), per the ConstructConnect bid listing.
- SUNSET INDUSTRIAL PIT (rank 2) and ASPHALT SPECIALTIES (rank 3): both ranked companies are paving contractors, but each operates the pit at the ranked site itself, so no separate occupier.
- UNATTACHED 8440 RASPBERRY WAY (rank 45): no company; occupier unknown.

## 3. Sources used (one line per company)

- AGILENT TECHNOLOGIES US: searched "Agilent Technologies Frederick Colorado 7051 Eagle Blvd manufacturing"; settled by Trade & Industry Development article on the $725M Frederick expansion.
- SUNSET INDUSTRIAL PIT: searched "J-2 Contracting Company Greeley Sunset Industrial Pit"; settled by DRMS permit file M2023001 (Exhibit G).
- ASPHALT SPECIALTIES: searched "Asphalt Specialties Co 4125 US-85 Fort Lupton Weld County"; Levelset page was a dead end; settled by Govly vendor profile plus the pipeline's air permit text.
- USRL HUDSON: searched "USRL Hudson Colorado gasoline transloading rail terminal"; settled by Commtrex transload listing for 2001 LCH Ave.
- BOULDER SCIENTIFIC: searched "Boulder Scientific Company Mead Colorado Specialty Place chemical manufacturing"; Powder & Bulk Solids article confirms the Mead production plant.
- SCHLOSSER SIGNS: searched "Schlosser Signs Windsor Colorado Great Western Drive sign manufacturing"; Blue Book page gone, company site blocked (provenance), settled by PR Newswire 20-year release.
- RAPTOR MATERIALS: searched "Raptor Materials LLC Platteville Highway 66 concrete"; settled by Blue Book supplier profile.
- URSA MAJOR TECHNOLOGIES: searched "Ursa Major Technologies Berthoud 19750 County Road 7 rocket engine manufacturing"; settled by BizWest article on the Berthoud purchase.
- SVW FARMS: searched "SVW Farms LLLP Hunt dirt mine Platteville Weld County"; settled by DRMS inspection M2021030.
- OLD SCHOOL INDUSTRIES: searched "Old School Industries Dacono Colorado CNC machining"; settled by NAICS list machine shop listing.
- HIGH PLAINS STEEL SERVICES: searched "High Plains Steel Services Windsor Colorado 2055 Howard Smith Ave structural steel fabrication"; settled by NAICS list profile plus fitter-welder and ironworker job titles.
- UNDERGROUND MANUFACTURING: searched the name with HP Indigo and with Colorful Avenue; Vert packaging article and CommercialCafe listing for 2950 Colorful Ave did not name the operator.
- QUANTUM JS CANNING: searched the name twice (with address and quoted); nothing relevant.
- CEA GREELY: searched the name twice with digester terms; nothing beyond generic digester articles.
- PERFORMANCE EQUIPMENT SALES: searched the quoted name; settled by NAICS list profile (2114 E I-25 Frontage Rd, Erie) and pequipment.com results.
- 5507 DISTILLING: searched the name; only 477 Distilling results; MeetingsMags article on 477's Loveland location did not name the entity.
- CANDO RAIL AND TERMINALS: searched "Cando Rail Terminals Windsor Colorado Savage transloading"; settled by Savage/Cando Greeley-Windsor transload page.
- BURNCO COLORADO: searched "BURNCO Colorado Windsor 31005 Great Western Drive concrete plant"; settled by Blue Book profile.
- LOUDWIRE DIESEL: searched twice; nothing relevant.
- JIMS AUTOMOTIVE MACHINE SHOP: searched "Jim's Automotive Machine Shop Gilcrest Colorado"; mechanicnet page was a different Jim's in Glenwood Springs; Superpages Gilcrest list did not include it.
- PIONEER PRESS OF GREELEY: searched the name with address; settled by Fort Collins Chamber printers listing.
- BLACK LABEL SERVICES: searched the name with address; settled by NAICS list profile (pipeline construction, 88 staff).
- SCOTTS MIRACLE GRO: searched twice for the Hudson plant; only product pages; level from the pipeline's permit text.
- IMPACT EQUIPMENT RENTALS: searched twice; nothing relevant.
- SWIFT BEEF: searched "Swift Beef Company JBS Greeley 800 N 8th Ave"; settled by USDA FSIS establishment page.
- T AND T GRINDERS: searched the quoted name with Nunn; nothing relevant.
- WASTE MANAGEMENT DISPOSAL SERVICES OF COLORADO: searched "North Weld Landfill Waste Management 40000 County Road 25 Ault"; settled by WM location page and Weld County news titles.
- COLORADO SAND: searched "Colorado Sand Company Keenesburg mine County Road 59"; settled by DRMS inspection M2019058.
- STERICYCLE: searched twice; settled by Stericycle careers Dacono plant associate posting and Weld County solid waste facility list.
- AGFINITY: searched "Agfinity Lucerne bulk plant"; settled by EPA RMP facility record (Lucerne Plant).
- JW FABRICATION: searched the quoted name with Ault; settled by EnergyHire production welder-fabricator posting.
- DESIGNLOGIC: searched "DesignLogic Inc Windsor Colorado CNC machining"; settled by Thomasnet profile.
- TV DAIRY: searched the quoted name with Fort Lupton; settled by NAICS list profile.
- CUTTING EDGE STEEL: searched the quoted name with Dacono; settled by NAICS list profile (101 Miller Dr, NAICS 332312).
- PNEU LINE SUPPLY: searched "Pneu Line Supply Greeley 2881 31st Ave injection molding"; settled by pneulinesupply.com capabilities page.
- CNE CREATIVE ENTERPRISES: searched the quoted name with Greeley; settled by City of Greeley business news page.
- ECLIPSE ENGINEERING: searched twice; Mapquest gave the seals description, NAICS list gave 2540 S Main St, Erie.
- LEGACY PIE: searched the quoted name with Windsor; 5280 article places shops in Denver only.
- ABSOLUTE COUNTERTOPS AND MORE: searched the quoted name with Fort Lupton; Trustburn page failed to load.
- HUNGENBERG PRODUCE: searched "Hungenberg Produce Greeley Colorado carrots packing"; settled by AndNowUKnow expansion article.
- BIG THOMPSON COMPOST: searched the quoted name with Milliken; nothing relevant.
- LIVE SHARP INDUSTRIES: searched the quoted name with Longmont; nothing relevant.
- BLACK EAGLE ENERGY SERVICES: searched "Blackeagle Energy Services Berthoud 230 Commerce Drive fabrication"; settled by EnergyHire structural welder posting.
- SCHOTT MANUFACTURING SOLUTIONS: searched the quoted name with Frederick; Express Employment job page had expired.
- UNATTACHED 8440 RASPBERRY WAY: searched the address with Raspberry Hill Business Park lot 17; only neighbouring lot listings.
- FOUR C SONS: searched the quoted name with La Salle; nothing relevant.
- ROCK AND RAIL: searched "Rock & Rail LLC Highway 34 asphalt plant Johnstown"; settled by rockandrail.com Highway 34 terminal page.
- J AND B MANUFACTURING: searched the quoted name with Greeley and Swiss lathe; NAICS list page for J&B Machine LLC (different name).
- BAY STATE MILLING: searched "Bay State Milling Platteville Colorado 400 Platte St mill"; settled by Shift Miller Platteville job posting titles.
- IDENTITY PET NUTRITION: searched the quoted name with Windsor; BizWest paywalled, settled by Pet Food Processing relocation article.
- KEIBON: searched twice; nothing relevant.
- WESTERN PROPPANTS: searched "Western Proppants LaSalle Colorado terminal sand"; only the Justia trademark record was specific.
- AULT ASPHALT PLANT SITE: searched "Connell Resources Ault asphalt plant Ryland Ave"; DRMS revision M1999050 described the Timnath pit (Larimer) with an asphalt facility, not the Ault site.
- WELD BESS STORAGE: searched "Weld BESS battery storage Michels Power Weld County"; NextEra Weld Energy Storage project page (candidate only).
- AURORA WATER NORTH CAMPUS: searched "Aurora Water North Campus Fort Lupton County Road 8 Velocity Constructors"; settled by ConstructConnect radial collector well listing (owner City of Aurora).
- SUN MOUNTAIN: searched "Sun Mountain Inc Berthoud 140 Commerce Rd custom doors manufacturing"; settled by BuildingClean facility record.
- C SIMPSON FARMS: searched the quoted name with Ault; nothing relevant.
- COVENANT PLUMBING AND HEATING: searched the quoted name with Ault; settled by Angi contractor listing titles.
- EATON FIRE PROTECTION DISTRICT: searched the quoted name; settled by state auditor local government record and station listings.
- ARC COLORADO: searched "ARC Colorado Inc 7040 County Road 20 Longmont fabricated metal"; OpenGovUS and GunMade pages failed to load.

Blocked or failed pages: schlossersigns.com (permission not granted), trustburn.com, gunmade.com, opengovus.com (client errors), jobs.expresspros.com (expired posting).
# Weld County incentive agreement holders: compressed-air fit web check (2026-11-06)

## Fit dict

```python
WELD_INCENTIVE_WEBCHECK = {
    'NORTH AMERICAN MACHINES OF COLORADO TRULOG SIDING': ('strong', 'TruLog makes roll-formed steel log-look, board-and-batten and lap siding (building-product manufacturing, metal forming); trade directory confirms the product and lists LaSalle CO, the Niobrara Blvd site is the new Project Hawthorn plant per the county agreement and 2026 site plan, manufacturing there is inferred not confirmed; trade directory (web check 2026-11-06).'),
    'OWENS BROCKWAY GLASS CONTAINER': ('strong', 'O-I glass container plant (Plant 28) at 11133 Eastman Park Dr, Windsor, makes glass bottles and jars; Town of Windsor manufacturer list and EPA GHGRP facility record (web check 2026-11-06).'),
    'MOTHERLOAD CO PACKING': ('strong', 'Motherlode Co-Packing, sauce and condiment co-packer (BBQ and hot sauces, dressings, salsa, drink mixes) with contract manufacturing and private label at 560 Dahlia St, Hudson; trade directory (web check 2026-11-06).'),
    'US ENGINEERING METALWORKS': ('strong', 'U.S. Engineering Metalworks runs prefabrication plants in Colorado and Kansas making piping, plumbing, steel and sheet metal assemblies, about 300,000 sq ft expanding to 500,000 by 2027; company site confirms the Colorado fab plant, Johnstown address comes from the county agreement; company site (web check 2026-11-06).'),
    'ECOMOD': ('strong', 'EcoMod builds modular housing, dormitories and portable data centers from steel framing and upcycled container chassis at its Hudson CO plant, primary NAICS 332311 prefabricated metal buildings; federal contractor record (web check 2026-11-06).'),
    'SCOTTS COMPANY HYPONEX': ('moderate', 'Scotts Miracle-Gro / Hyponex plant in Brighton with production, field, warehouse, machine operator and heavy equipment roles; Hyponex is the Scotts soil and mulch brand, so a growing media bagging and blending plant, product line at the site inferred from job postings not stated; job postings (web check 2026-11-06).'),
    'CHARM INDUSTRIAL': ('strong', 'Charm Industrial Miniforge in Fort Lupton: biomass pyrolysis operations, bio-oil gasification and ironmaking R&D, with pyrolyzer operator and fabricator roles; pilot-scale chemical processing, team planned at 25+; company blog and job postings (web check 2026-11-06).'),
    'K2D COLORADO PREMIUM FOODS': ('strong', 'Colorado Premium 175,000 sq ft sous vide protein processing plant at 2400 W 29th St, Greeley, with raw processing, searing and par-fry lines, opened Feb 2024; trade press (web check 2026-11-06).'),
    'NORFOLK IRON AND METAL': ('strong', 'Norfolk Iron & Metal (NIM Group) metal processing center at 31825 Great Western Dr, Windsor: cut-to-length line and hydraulic leveler shearing aluminum, stainless, coated and cold-rolled sheet, a processing-only plant supplying NIM Group; press release and Town of Windsor manufacturer list (web check 2026-11-06).'),
    'SPHERE RENEWABLES': ('moderate', 'Sphere Renewables, component manufacturer and distributor for wind, solar and storage projects, 43,000 sq ft headquarters with a production shop floor on WCR 8 in Fort Lupton; product assembled on site not named; trade press and job posting (web check 2026-11-06).'),
    'BAE SYSTEMS SPACE AND MISSION SYSTEMS': ('strong', 'BAE Systems Space & Mission Systems bought the 130,000 sq ft former Danfoss building at 4120 Specialty Place (unincorporated Weld, east of Longmont) in Oct 2026 for $30M as an advanced manufacturing and integration plant for space hardware and sensor systems; retrofit and equipment buying now, production early 2028; regional news (web check 2026-11-06).'),
    'COLORADO STUD': ('unknown', 'Not confirmed in two lookups; Lone Tree Lane in Nunn is a small industrial yard and warehouse park off US 85 serving oil and gas users, no page names Colorado Stud Company or its product; property listings (web check 2026-11-06).'),
    'GG COLORADO II': ('unknown', 'Not confirmed in two lookups; no page ties GG Colorado II LLC to a business or product at Great Western Industrial Park Lot 15, Windsor, the name reads as a holding or project entity; web search (web check 2026-11-06).'),
    'MICROVAST ENERGY': ('weak', 'Microvast bought the former Hexcel building at 31815 Great Western Dr, Windsor in July 2023 for an energy storage plant that never ramped; a 31,562 sq ft suite in the 99,536 sq ft building is now listed for lease with no tenant named, so Microvast appears gone; trade press and CBRE listing (web check 2026-11-06).'),
    'AIRXCEL AQUA HOT HEATING SYSTEMS': ('strong', 'Aqua-Hot (Airxcel) makes hydronic RV and specialty vehicle heating systems, moved to a new Frederick building with expanded manufacturing space in Oct 2023; Miller Drive address from the county agreement and 2023 tenant finish permit; trade press (web check 2026-11-06).'),
}
```

## Flags

- MICROVAST ENERGY: company appears to have left the site. The 31815 Great Western Dr building is on the market for lease (CBRE) with no tenant named, and the 2023 ESS plant plan never ramped. Treat the address as a vacancy, not a Microvast account.
- GG COLORADO II: name is a holding or project entity (UCC secured party Ares Capital), not a recognizable operator. Occupier at Great Western Industrial Park Lot 15 unconfirmed.
- COLORADO STUD: occupier and product unconfirmed; Lone Tree Lane in Nunn is a yard-and-warehouse park. UCC with First Advantage Bank covers fixtures, which fits a small operator, but nothing says what it does.
- NORTH AMERICAN MACHINES OF COLORADO / TRULOG SIDING: product confirmed, site not. Directory lists LaSalle CO; the Niobrara Blvd site is the new Project Hawthorn plant (2026 site plan review). The company website fetch (trulogsiding.com) was blocked by a permission timeout.
- BAE SYSTEMS: site is in unincorporated Weld County (mailing address Longmont). Production not until early 2028; equipment procurement is underway now, which is the compressed-air buying window.
- SCOTTS / HYPONEX and SPHERE RENEWABLES: site confirmed, specific product line at the site not stated on any page.
- No site was found to be outside Weld County. No landlord, lender or contractor was ranked in place of an occupier except GG Colorado II, which may be one.

## Settling page per company

- NORTH AMERICAN MACHINES OF COLORADO / TRULOG SIDING: https://designandbuildwithmetal.com/supplier-directory/trulog (blocked: https://www.trulogsiding.com/)
- OWENS BROCKWAY GLASS CONTAINER INC: https://www.windsorco.gov/1352/Manufacturing
- MOTHERLOAD CO PACKING LLC: https://www.comanufacturers.com/products/motherlode-co-packing-comanufacturer-profile
- US ENGINEERING METALWORKS: https://www.usengineering.com/solutions/metalworks/manufacturing-facilities
- ECOMOD LLC: https://fed360.agency/contractors/ecomod-llc-SLWQQCUNEL38
- THE SCOTTS COMPANY LLC / HYPONEX CORPORATION: https://www.builtincolorado.com/job/plant-manager/11215200 and https://www.builtincolorado.com/job/office-operations-manager/9272657
- CHARM INDUSTRIAL INC: https://charmindustrial.com/blog/opening-our-colorado-miniforge-site
- K2D INC / COLORADO PREMIUM FOODS: https://www.businesswire.com/news/home/20240205212442/en/Colorado-Premium-Opens-New-175000-Square-Foot-Sous-Vide-Processing-Plant
- NORFOLK IRON AND METAL COMPANY: https://prnewswire.com/news-releases/nim-group-to-install-precision-cut-to-length-line-whydraulic-cassette-leveler-in-windsor-co-facility-301652906.html
- SPHERE RENEWABLES: https://bizwest.com/?p=376186 and https://www.jobtarget.com/jobs/jt-ckoeyq46u3/production-training-lead-fort-lupton-colorado
- BAE SYSTEMS SPACE AND MISSION SYSTEMS INC: https://www.kunc.org/news/2026-11-03/bae-buys-weld-county-danfoss-facility-for-30m
- COLORADO STUD COMPANY: unresolved; https://www.cushmanwakefield.com/en/united-states/properties/for-sale/warehousedistribution/co/nunn/1300-lone-tree-lane/s121276835s121276835-s (park context only)
- GG COLORADO II LLC: unresolved; web search for the exact name returned nothing relevant
- MICROVAST ENERGY INC: https://bizwest.com/?p=368173 and https://www.cbre.com/properties/properties-for-lease/industrial/details/US-SMPL-207999/warehouseindustrial-31815-great-western-drive-windsor-co-80550
- AIRXCEL INC / AQUA HOT HEATING SYSTEMS LLC: https://rv-pro.com/news/aqua-hot-celebrates-40th-anniversary/
