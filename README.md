# Dream Menu website

The files for www.dream-menu.com. Vercel deploys this repository: anything merged to `main` goes live.

- Public pages and the venue map sit at the top level.
- The partner area, report sections and partner data are protected by `middleware.js`, which checks the `DM_PASSWORD` environment variable set in Vercel. The password is not stored here.
- `dm-data.js`, `dm-cat.js` and `dm-labels.js` hold the venue data, the refined dish categories and the plain labels with parent groups.
- `partner-data.js` holds the partner briefing data; `partner/render.js` draws the briefing, insights and one-pager from it, and `partner/downloads.js` builds the CSV downloads in the browser.

## Navigation

The header menus (including the "I'm a..." audience menu), the footer links, search and the Explore page all come from one list in `tools/build_nav.py`. To add or rename a page or section, edit that list and run `python3 tools/build_nav.py` from the repository root. `nav.js` makes the menus work; `nav-data.js` is generated, so don't edit it by hand. The `tools/` folder is not deployed.
