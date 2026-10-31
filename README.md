# Dream Menu website

The files for www.dream-menu.com. Vercel deploys this repository: anything merged to `main` goes live.

- Public pages and the venue map sit at the top level.
- The partner area, report sections and partner data are protected by `middleware.js`, which checks the `DM_PASSWORD` environment variable set in Vercel. The password is not stored here.
- `dm-data.js`, `dm-cat.js` and `dm-labels.js` hold the venue data, the refined dish categories and the plain labels with parent groups.
- `partner-data.js` holds the partner briefing data; `partner/render.js` draws the briefing, insights and one-pager from it, and `partner/downloads.js` builds the CSV downloads in the browser.

## Navigation

The header menus (including the "I'm a..." audience menu), the footer links, search and the Explore page all come from one list in `tools/build_nav.py`. To add or rename a page or section, edit that list and run `python3 tools/build_nav.py` from the repository root. `nav.js` makes the menus work; `nav-data.js` is generated, so don't edit it by hand. The `tools/` folder is not deployed.

## Analysis pages and data freshness

- `/analysis` (public) and `/intelligence` (partner, locked) are built from the site's own data files. After a data refresh run, from the repository root:
  `python3 tools/build_intel.py && python3 tools/build_pages.py && python3 tools/build_nav.py`
  `build_intel.py` writes `analysis-data.js` (headline analysis only, nothing about quarterly movement) and `partner/intel-data.js` (behind sign-in). The charts are drawn by `analysis.js` and `partner/intel.js` using the small chart toolkit in `dmviz.js` / `dmviz.css`; every chart has a table view, a CSV download and a link.
- `dm-fresh.js` loads on every page. It adds a "Data to ... · Updated ..." line under each visual or block of figures, a "Last updated" chip under the page title and a data status panel in the footer. When a dataset is refreshed, change its dates in the `SETS` list at the top of that file.

## Case studies

`/case-studies` is the Dream Menu Insight Series (locked behind the partner sign-in since 29 October 2026): a library page and fifteen reports, built by `tools/build_case_studies.py` with the chart kit in `tools/cs_kit.py` and the styles and behaviour in `case.css` and `case.js` (shell copied from `restaurant-mot.html`). No. 01 is Gordon's night-out briefing set as a page; Nos. 02 to 11 are provisional samples whose figures are read from the live data files (`partner-data.js`, `analysis-data.js`, `dm-data.js`, `awards.js`, `tools/data/static-counts.json`, `tools/data/look-ahead-2026-scores.json`), so rerun the script after each data refresh, then `tools/build_nav.py`. Nos. 12 to 15 are trend and forecast reports: their projections come from `project()` in `cs_kit.py` (a recency-weighted, damped trend with a widening planning range), and No. 15 also reads hand-coded "more of" answers from `tools/data/positive-trends-2026.json`, which needs updating by hand as new answers arrive. Chart colours (indigo, amber, teal) were checked with the dataviz palette validator in light and dark mode.

## Awards between full rebuilds

`tools/update_awards.py` applies a small JSON of new award editions to `awards.js` (new ranked lists for places already on the map, swapped records, new places) and recomputes counts and tiers; `refresh_static.py` then carries the counts into the pages. See `tools/data/awards-update-2026-10-29.json`.

## Adding new interviews between full rebuilds

The full build pipeline (sheet export, machine coding, venue matching) is not in this repository. To fold a small batch of new interviews into the live data:

1. Code the batch by hand into a JSON file in `tools/data/` (see `new-interviews-2026-10-28.json`: one row per interview with the refined dish category for each course, the debate answers, and any guilty pleasure or "bin it" answer that matches a published label). List the venues they name in a second file (see `new-venues-2026-10-28.json`): existing venue ids where the venue is already on the map, and new venues with an address or the place the guest named.
2. From the repository root:
   `python3 tools/add_interviews.py tools/data/<interviews>.json`
   `python3 tools/add_venues.py tools/data/<venues>.json tools/data/<interviews>.json <path to ukpostcodes.csv>`
   `python3 tools/refresh_static.py && python3 tools/build_intel.py && python3 tools/build_pages.py && python3 tools/build_case_studies.py && python3 tools/build_press.py && python3 tools/build_briefing_extras.py && python3 tools/build_venue_pages.py && python3 tools/build_quarterly.py && python3 tools/build_alert.py && python3 tools/build_nav.py`
   Run each step once per batch: the first two add to the existing counts. `add_venues.py` needs the dwyl UK postcode file (github.com/dwyl/uk-postcodes-latitude-longitude-complete-csv) to place exact UK addresses.

`add_interviews.py` recovers each quarter's counts exactly from the published shares, adds the new answers, and reruns the two-proportion test, so movers and clear flags stay correct. `refresh_static.py` rewrites every figure that is written into the static pages (home, insights, for business, how it works, partner pages, footer dates and `dm-fresh.js`); the 2026 report pages keep their edition figures on purpose. Counts that the data files do not hold (debates, home course cards) live in `tools/data/static-counts.json`.

## Added 30 October 2026

- **Home market tabs** are Glasgow, Edinburgh, Rest of Scotland and Beyond Scotland (built in `refresh_static.py` from each venue's dishes in `dm-cat.js`), so no tab repeats Glasgow. Each dish shows its share and an index chip (×1.5 = named 1.5 times as often as across all markets) where it is named at least 5 times (8 in a thin market) at three or more venues.
- **Place labels**: venues the geocoder labelled "Seafield" are relabelled Leith (EH6) or Portobello (EH15) on every refresh.
- **Water debate**: "Scottish tap water" answers count as Tap.
- **For business**: the evidence cards and the Work with us section (email, enquiry form that opens the visitor's own mail app, free sample) are generated by `refresh_static.py` between `<!--fb-cards-->` and `<!--fb-contact-->` markers.
- **Free sample report**: `/case-studies/guests-and-critics` is public (`PUBLIC` in `middleware.js`, `FREE` in `build_case_studies.py`, `PUBLIC` in `build_nav.py`, robots and sitemap). Every other report stays locked.
- **Sign-in preview**: `/login?next=...` shows what the locked page holds, from `nav-data.js` and `case-previews.js` (report titles, questions and chapter names only, no figures).
- **Press kit**: `/press`, built by `tools/build_press.py` from the live data.
- **Partner briefing**: `tools/build_briefing_extras.py` writes `partner/briefing-extra.js` (locked) for three new sections: what changed since the last briefing (against the newest snapshot in `tools/data/briefing-snapshots/`; it saves a new one each run), the trend scorecard (score out of 10) and By Dunns range (indicative grouping, to be matched to Dunns' own category list). `/intelligence` now shows scores out of 10.

## Added 30 October 2026, later: UK-wide

- **Positioning**: the site is UK-wide. The home page has a Coverage section (venue mentions by nation, each marked Deep or Early signal: deep = 30+ guests and 300+ venue mentions) and five market tabs: Glasgow, Edinburgh, Rest of Scotland, Rest of UK, Outside the UK.
- **Venue pages** `/venue/<slug>` (every venue named at least twice) and **dish pages** `/trends/<slug>` plus the `/trends` index: `tools/build_venue_pages.py`. Quotes appear on a venue page only if they name the venue. The same script writes `badge.svg`, the `/badge` page and `rank-data.js` (the slim data file `/rankings` now loads), and updates the sitemap. It also writes `partner/dish-moves.js` (quarterly shares, clear-move test, 95% range and trend score per dish; behind sign-in), which `/dish-move.js` uses to fill the "Is it rising?" card on each dish page for signed-in partners.
- **State of the Menu** `/quarterly` (and `quarterly/<yyyy-qn>.html`), the opt-in **guest menus** page `/menus` (built only once `tools/data/guest-menus.json` has entries) and the **email sign-up** boxes (`<!--signup-->` markers): `tools/build_quarterly.py`. Set the Google Form in `tools/data/signup.json`; until then the box opens an email.
- **Take part** embeds the Dream Menu Google Form.
- **Partner alert**: `tools/build_alert.py` writes `tools/data/alerts/<date>.txt/.html`; Claude drafts it in Gmail for Gordon to send.
- **Testimonials** on /for-business come from `tools/data/testimonials.json` (hidden while empty; real quotes with permission only).
- Structured data: Organization and WebSite on the home page, Dataset on how-it-works, Restaurant on venue pages, Article on dish pages.
