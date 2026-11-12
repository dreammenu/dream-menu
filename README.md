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
  `python3 tools/build_intel.py && python3 tools/build_trends.py && python3 tools/build_benchmarks.py && python3 tools/build_drinks.py && python3 tools/build_partner.py && python3 tools/build_pages.py && python3 tools/build_nav.py`
  `build_intel.py` writes `analysis-data.js` (headline analysis only, nothing about quarterly movement) and `partner/intel-data.js` (behind sign-in). The charts are drawn by `analysis.js` and `partner/intel.js` using the small chart toolkit in `dmviz.js` / `dmviz.css`; every chart has a table view, a CSV download and a link.
- `dm-fresh.js` loads on every page. It adds a "Data to ... · Updated ..." line under each visual or block of figures, a "Last updated" chip under the page title and a data status panel in the footer. When a dataset is refreshed, change its dates in the `SETS` list at the top of that file.

## Case studies

`/case-studies` is the Dream Menu Insight Series (locked behind the partner sign-in since 29 October 2026): a library page and fifteen reports, built by `tools/build_case_studies.py` with the chart kit in `tools/cs_kit.py` and the styles and behaviour in `case.css` and `case.js` (shell copied from `restaurant-mot.html`). No. 01 is Gordon's night-out briefing set as a page; Nos. 02 to 11 are provisional samples whose figures are read from the live data files (`partner-data.js`, `analysis-data.js`, `dm-data.js`, `awards.js`, `tools/data/static-counts.json`, `tools/data/look-ahead-2026-scores.json`), so rerun the script after each data refresh, then `tools/build_nav.py`. Nos. 12 to 15 are trend and forecast reports: their projections come from `project()` in `cs_kit.py` (a recency-weighted, damped trend with a widening planning range), and No. 15 also reads hand-coded "more of" answers from `tools/data/positive-trends-2026.json`, which needs updating by hand as new answers arrive. Chart colours (indigo, amber, teal) were checked with the dataviz palette validator in light and dark mode.

## Awards between full rebuilds

`tools/update_awards.py` applies a small JSON of new award editions to `awards.js` (new ranked lists for places already on the map, swapped records, new places) and recomputes counts and tiers; `refresh_static.py` then carries the counts into the pages. Awards from other lists (AA Rosettes, National Restaurant Awards, bar and steak lists, Scottish trade awards) live in `tools/data/other-awards.json`; the hand-checked venue links are in `other-awards-links.json` (with a list of rejected look-alikes), and `build_other_awards.py` writes `other-awards.js`. See `tools/data/awards-update-2026-10-29.json`.

## Adding new interviews between full rebuilds

The full build pipeline (sheet export, machine coding, venue matching) is not in this repository. To fold a small batch of new interviews into the live data:

1. Code the batch by hand into a JSON file in `tools/data/` (see `new-interviews-2026-10-28.json`: one row per interview with the refined dish category for each course, the debate answers, and any guilty pleasure or "bin it" answer that matches a published label). List the venues they name in a second file (see `new-venues-2026-10-28.json`): existing venue ids where the venue is already on the map, and new venues with an address or the place the guest named.
2. From the repository root:
   `python3 tools/add_interviews.py tools/data/<interviews>.json`
   `python3 tools/add_venues.py tools/data/<venues>.json tools/data/<interviews>.json <path to ukpostcodes.csv>`
   `python3 tools/refresh_static.py && python3 tools/build_other_awards.py && python3 tools/build_intel.py && python3 tools/build_trends.py && python3 tools/build_benchmarks.py && python3 tools/build_drinks.py && python3 tools/build_partner.py && python3 tools/build_pages.py && python3 tools/build_case_studies.py && python3 tools/build_press.py && python3 tools/build_briefing_extras.py && python3 tools/build_venue_pages.py && python3 tools/build_quarterly.py && python3 tools/build_alert.py && python3 tools/build_nav.py`
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

## Added 11 November 2026: shares, not volumes

Markets have very different numbers of answers (Glasgow holds most venue mentions), so comparisons between places are shown as percentages, not counts: the home market tabs (dish chips "vs x%" and "Most-named venues" as a share of that market's mentions), the /analysis city chart (cells show the share of the market's mentions, coloured against the share everywhere), dish pages ("By market": share here vs all markets) and the press kit facts. Raw counts stay in tooltips and CSV downloads. Keep new comparisons in the same form.

## Added 11 November 2026: the menu over time

`tools/build_trends.py` (run after `build_intel.py`, before `build_pages.py`) writes `trend-public.js` (course level only) and `partner/trend-data.js` (behind sign-in); `trend-charts.js` draws both. Public /analysis gains sections D to F (how much each course changed against chance, whether guests converge on favourites, life-cycle mix and steady staples). Partner /intelligence gains sections 9 to 13 (written findings, churn and where the share went, life-cycle board and then-vs-now, menu shape by quarter, projections for clear movers, staples). Food courses only, as the drink questions changed on 23 August 2026. Chance baselines use a fixed random seed, so reruns give the same numbers. Palette slots 4 and 5 (`--v-s4`, `--v-s5`) were added to `dmviz.css` and validated in light and dark.

## Added 11 November 2026, later: one analysis page and outside benchmarks

- **One page.** `/analysis` now holds every analysis. Chapters 1 to 8 are open to all; chapters 9 to 16 (momentum, confidence ranges, trend wall, dish heat, projections, segments, opportunity score, operator pulse) show a short preview until partner sign-in, then draw in place. Partner data still comes only from `/partner/*.js`, which `middleware.js` refuses without the sign-in cookie, so nothing partner-only reaches a signed-out browser. `/intelligence` redirects to `/analysis` (vercel.json) and `intelligence.html` is a redirect stub. The page is written by `tools/build_pages.py`; the method text is `tools/data/analysis-method.html`.
- **How we compare** (chapter 8): `tools/build_benchmarks.py` keeps each outside figure with its publisher, date, link and what it measures, reads the matching Dream Menu figure live, and writes `bench-public.js` (comparisons using figures already public) and `partner/bench-data.js` (all, including dish and drink movement). Verdicts are agrees, challenges or context. Outside figures are never merged into Dream Menu data. Refresh the outside figures by editing the BENCH entries when a new edition is published (YouGov, Food Standards Scotland, NIQ Hospitality Market Monitor and Business Confidence Survey, ONS CPI, Tastewise, Lumina, Diageo and AG Barr results).

## Added 11 November 2026, afternoon: simpler navigation, drinks restart, who answers

- **Navigation.** Five short header menus (Trends, Places, Analysis & reports, For venues, Partners) listing 17 pages in all, with no sub-lists; the "I'm a..." menu left the header (the home page "Where do you want to start?" band and /explore still do that job). Groups, placement and the menu list are GROUPS, PLACE and MENU in `tools/build_nav.py`. Every other page stays on /explore, in the footer and in search.
- **Drinks, restarted** (analysis chapter 8): `tools/build_drinks.py` builds `drinks-new.js` from the soft and alcoholic drink questions asked since 23 Aug 2026 (`tools/data/drinks-new-series.json` plus later `new-interviews-*.json` batches). Baseline shares with 95% ranges; movement is tested once two quarters each hold 100 answers.
- **Who answers** panel in the analysis method section (respondent groups, UK mentions by nation), written by `build_pages.py`.
- The analysis now has 17 chapters: 1 to 9 open, 10 to 17 for partners.

## Added 12 November 2026: partner area and Work with us

- `/partner` is written by `tools/build_partner.py` (run after `build_intel.py`): this quarter's clear movers, top opportunity scores and operator mood from the data; tools sorted by job (sales, buying and range, marketing, strategy); the partnership term as a timeline worked out from today's date; data downloads; terms and sponsorship folded away. The table markup is kept so `partner/downloads.js` still binds to it. `refresh_static.py` no longer edits partner.html.
- The same script writes the "Ways to work with us" block on `/for-business`: one route each for suppliers and brands, investors and consultants, venues, and press.
- Header menu "Partners" is now "Work with us" (Ways to work with us, Press kit, Partner area). The footer mirrors the header menus; the full page list stays on /explore.

## 12 November 2026: home page and direct recommendations

* `tools/build_home.py` (run after refresh_static, build_trends, build_drinks and build_benchmarks; before build_nav) writes the home "This quarter" band: three findings from Dream Menu data with a "What to do" line each, plus one outside check kept visibly separate. It also fixes the home section order (hero, numbers, this quarter, start here, courses, places, debates, comfort and fatigue, map, coverage, partners, sign-up) and carries the source note.
* Guilty pleasures and Bin it now show shares of all interviews, not counts. Benchmark texts for matcha, Dubai chocolate and loaded food are shares too.
* Every analysis chapter has a "Use it to" line saying what decision it supports (`DO` in build_pages.py; chapter 5's line follows the data).
* Header groups renamed: Food trends, Where to eat, Analysis & reports, For venues, Work with us.

## 12 November 2026: "How to read this" notes on every chart

* Each chart has a small, closed-by-default "How to read this" note under its title: what it shows, how to read it, one caution. One shared component (`.vinfo` in brand.css).
* Where the notes live: analysis charts in `INFO` in dmviz.js (keyed by card id; a new card without an entry simply shows no note); case-study exhibits in `KIND_INFO` in tools/cs_kit.py (picked by chart type, override with `info=`); the Who answers panels in build_pages.py; the dish page partner chart in dish-move.js; the map place panel in map.html; everything else (home, insights, briefing, operator pulse, one-pager, venue pages) in `RULES` in tools/build_info.py.
* Run tools/build_info.py after build_home.py and before build_nav.py. refresh_static.py strips the notes from the files it edits so its patterns still match; build_info.py puts them back.

## 12 November 2026: the analysis as a story, editorial charts, wayfinding, partner passwords

* /analysis is now seven parts in order: the short version, what guests want, what is changing, where it differs, the reality check, what to do (four readers), the partner briefing, then folded reference charts. Section order and wording live in tools/build_pages.py (PARTS, DO, _ROLES, the chap() calls). Old anchors still work.
* Charts kept in the main flow carry a finding as the headline (`claim:` on each V.card call), what is measured beneath, and reading notes folded away. Charts moved to Reference: top-five share, mentions concentration, life-cycle board, then-and-now, trend wall, dish heat, course mix. A page can place any chart with `<div data-card="chart-id">`.
* One chart style everywhere (rule and gold tab above, source and tools at the foot): the "editorial" block in dmviz.css and "editorial-ex" in case.css.
* nav.js adds, on every page: a header that hides on the way down and returns on the way up, an "On this page" bar that follows the reader and marks the current section, breadcrumbs taken from the menu, one next step above the footer, and a back-to-top button. Styles: "wayfind" block in brand.css.
* Individual partner passwords: `python3 tools/partner_passwords.py add "Name"` prints a new password once; `revoke "Name"` stops it; `list` shows who has one. Only slow hashes are stored (tools/data/partner-keys.json and the marked block in middleware.js). The main password (DM_PASSWORD in Vercel) is untouched and keeps working. Commit and push after any change.
