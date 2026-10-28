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

## Adding new interviews between full rebuilds

The full build pipeline (sheet export, machine coding, venue matching) is not in this repository. To fold a small batch of new interviews into the live data:

1. Code the batch by hand into a JSON file in `tools/data/` (see `new-interviews-2026-10-28.json`: one row per interview with the refined dish category for each course, the debate answers, and any guilty pleasure or "bin it" answer that matches a published label). List the venues they name in a second file (see `new-venues-2026-10-28.json`): existing venue ids where the venue is already on the map, and new venues with an address or the place the guest named.
2. From the repository root:
   `python3 tools/add_interviews.py tools/data/<interviews>.json`
   `python3 tools/add_venues.py tools/data/<venues>.json tools/data/<interviews>.json <path to ukpostcodes.csv>`
   `python3 tools/refresh_static.py && python3 tools/build_intel.py && python3 tools/build_pages.py && python3 tools/build_nav.py`
   Run each step once per batch: the first two add to the existing counts. `add_venues.py` needs the dwyl UK postcode file (github.com/dwyl/uk-postcodes-latitude-longitude-complete-csv) to place exact UK addresses.

`add_interviews.py` recovers each quarter's counts exactly from the published shares, adds the new answers, and reruns the two-proportion test, so movers and clear flags stay correct. `refresh_static.py` rewrites every figure that is written into the static pages (home, insights, for business, how it works, partner pages, footer dates and `dm-fresh.js`); the 2026 report pages keep their edition figures on purpose. Counts that the data files do not hold (debates, home course cards) live in `tools/data/static-counts.json`.
