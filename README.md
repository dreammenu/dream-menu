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
