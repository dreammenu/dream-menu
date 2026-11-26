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
  `python3 tools/build_intel.py && python3 tools/build_trends.py && python3 tools/build_benchmarks.py && python3 tools/build_drinks.py && python3 tools/build_partner.py && python3 tools/build_pages.py && python3 tools/build_evidence.py && python3 tools/build_nav.py && python3 tools/build_gate.py`
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
   `python3 tools/refresh_static.py && python3 tools/build_other_awards.py && python3 tools/build_intel.py && python3 tools/build_trends.py && python3 tools/build_benchmarks.py && python3 tools/build_drinks.py && python3 tools/build_partner.py && python3 tools/build_pages.py && python3 tools/build_case_studies.py && python3 tools/build_press.py && python3 tools/build_briefing_extras.py && python3 tools/build_venue_pages.py && python3 tools/build_quarterly.py && python3 tools/build_alert.py && python3 tools/build_og.py && python3 tools/build_evidence.py && python3 tools/build_nav.py && python3 tools/build_gate.py`
   Since 17 November 2026, run `python3 tools/clean_venues.py` straight after `add_venues.py` (it folds any listed duplicate venues and tidies names; harmless when there is nothing to do), and `python3 tools/build_map_awards.py` after any change to `awards.js`.
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

## 13 November 2026: city guides

* tools/build_venue_pages.py now also writes /cities and one /city/<name> page for every city where guests have named at least 5 venues (15 today). Cities with 30 or more guests get the full guide (dream menu by course, most named, hidden gems, what the city names more than elsewhere, award holders, quotes); smaller ones are marked "Early signal". All figures are shares of the city's own mentions. Pages are added to sitemap.xml and the Where to eat menu.

## 13 November 2026: tools, neighbourhoods, digest, partner visits, faster map

* /menu-check and /my-dream-menu: written by tools/build_venue_pages.py, driven by tools.js and pick-data.js (public shares, staples and the city index only). Choices live in the page link, nothing is stored. Signed-in partners also see clear movement on food courses in the menu check.
* /area/<city>-<area>: neighbourhood guides for Glasgow and Edinburgh. Areas are groups of postcode districts (`AREAS` in build_venue_pages.py); only venues with a confirmed address count, and an area needs 8 venues to get a page.
* tools/build_digest.py (after build_home.py) writes the public email digest to tools/data/digest/. The weekly task drafts it in Gmail with no recipients.
* Partner visits: sign-in sets a plain `dm_who` label cookie (main, partner-02, ...), and nav.js sends one extra page view to Vercel Web Analytics under /_partner/<label>/<page> on partner pages. The weekly task reads those counts. `partner_passwords.py list` rewrites the middleware block.
* map.html loads awards.js after the map is usable (awInit / setFoot / the loader at the end of the boot block).
* The home page has a "Try it yourself" band (tools/build_home.py, section id "try").

## 13 November 2026 (later): analysis rebuilt around five questions; site trimmed

* /analysis answers five questions in order (what do guests want, what is changing, where does it differ, can we trust it, what should I do), then a four-section partner briefing and folded reference charts. 12 sections, down from 15; about a quarter shorter.
* New exhibits, modelled on trade practice: a demand mix per course (public; mix-public.js) in the manner of menu-tracker course analysis, and a category scorecard for buyers (partners; partner/category-data.js) that gives every food group a call: Grow, Defend, Trim, Core or Niche. Both are written by tools/build_pages.py (`MIX`, `CATS`, `_call`) and drawn in trend-charts.js (`demandMix`, `scorecard`). The life-cycle section is framed the way menu analysts frame adoption: emerging, growing, established, fading.
* Benchmarks show the agree / challenge / context board; the 18 detail cards are folded under "Every comparison, with sources".
* Retired or trimmed: /insights now redirects to /analysis (the file stays as the page template for build_pages.py); the home page lost the audience band, the coverage tiles and the map teaser (tools/build_home.py pops them); "From the kitchen" left the header menu (still on /explore and in search).
* Vercel Web Analytics is NOT enabled on the project (checked 13 Nov). Until it is switched on in the Vercel dashboard, the per-partner visit counts cannot be collected.

## 13 November 2026: one card style site-wide; menu audit pipeline

* brand.css "house" block gives every card and tile on the site the same look as the charts (rule and gold tab, no boxes). Venue pages link to their city guide.
* Menu audit: tools/data/menu-audit.json (venues' own published menus, each dish mapped to a tracked dish label and a food group) feeds tools/build_menu_audit.py, which build_venue_pages.py runs last. It writes menu-audit-public.js; the analysis page then shows "what guests ask for against what venues list" (Gap, Table stakes, Over-supplied, Niche) and median prices by course under "What do guests want?". Nothing shows until at least 10 venues are audited. The format is documented at the top of the script.

## 13 November 2026 (evening): first menu audit

* tools/data/menu-audit.json holds the published menus of 45 of the most-named UK venues, read on 13 November 2026 from each venue's own site or PDF (dish names and prices only). tools/data/menu-audit-notes.md lists the 104 venues tried and skipped, with reasons, and the mapping decisions. Most skips are menus published only as images, venues with no site of their own, or PDFs the fetch tool could not follow; the last few were not attempted because the search allowance ran out, and are the first to retry.
* tools/build_menu_audit.py changed after the first run: each share is now of the menus that print that course (15 of the 45 menus print no desserts); a Gap needs demand in the top quarter of its course, not just above the median (the first rule called 20 of 56 dishes gaps); a guest who says "steak" counts as served by any steak; "Other pasta" is marked Not comparable. The thresholds are named constants at the top of the script.
* The audit feeds the wording of section 2 on /analysis, one line for each reader under "What should I do?" (build_pages.py, the `AU_` strings) and the second home card, which replaced the staples card (build_home.py; it falls back to staples if there is no audit). On a phone the audit table drops the course and price columns (dmviz.css).

## 13 November 2026 (afternoon): leaner structure, analysis and reports separated

* **Header: five items.** Analysis and Reports are plain links; Where to eat (map, city guides, rankings), For venues (Check my menu, toolkit, Restaurant MOT) and Work with us (ways to work with us, press kit, partner area) have three entries each. Set in `HMENU` in tools/build_nav.py. Food trends (the home page) is reached from the logo; it and About sit in the footer. Dish trends now sits under Analysis.
* **Analysis = live data, Reports = dated publications.** `/reports` (tools/build_reports.py, run after build_case_studies.py and build_quarterly.py, before build_nav.py) lists the 2026 report and its chapters, State of the Menu editions and the Insight Series, each with its data date read from the pages.
* **/analysis is public-only for signed-out readers.** The partner briefing (scorecard, what to back, how sure, who buys, partner reference) sits in `.iv-pzone`, hidden until partner data loads; signed-out readers see one line with a sign-in link instead of five locked previews. The three public supporting charts moved into the Method section.
* **Home page: eight sections.** The market tabs left the home page (the city guides and the analysis carry that view). refresh_static.py treats those patterns as optional (`OPTIONAL`).
* Breadcrumbs come from the page list for pages not in the header (nav.js).

## 13 November 2026 (later): the partner area is the analysis

* There is no separate partner area. `/partner` redirects to `/analysis#partner` (partner.html is a stub written by build_partner.py). Sign-in sends partners to the analysis (middleware default and every "Partner sign-in" link).
* On `/analysis`, signed-out readers see the five questions, what to do and the method, then one line inviting partners to sign in. Signed-in partners see, on the same page: This quarter (clear movers, scores to back, operator mood), the category scorecard, what to back, how sure, who buys, data downloads, the partnership this term, terms, and the partner reference charts.
* `tools/build_partner.py` writes `partner/hub.js` (behind sign-in), which fills the `#p-hub-top` and `#p-hub-bottom` slots. Its source blocks (download table, terms, confidential line) are in `tools/data/partner-static.html`. "Pick the tool for the job" was dropped: the page itself is the toolbox.
* Header: Analysis, Reports, Where to eat, For venues, Work with us, plus a "Partner sign-in" link (hidden below 1100px wide; on phones it is in Work with us and the footer).

## 13 November 2026 (later still): no duplicates, and an interest filter

* **Retired, each now a redirect (vercel.json plus a stub page):** /explore (replaced by the interest filter on the home page), /awards (award winners are a layer on /map), /briefing (its two unique sections, "What changed since the last update" and "By Dunns range", now sit in the partner view of /analysis; the one-pager stays as the printable). Stubs are written by tools/build_partner.py; refresh_static.py and build_info.py no longer edit those pages.
* **Reports** no longer repeats the Insight Series list: it links to /case-studies (the library) and the free sample, and to the latest State of the Menu.
* **Interest filter** (`interest.js`, styles in brand.css): six interests (Food, Drinks, Growing sales, Cutting costs, Planning a menu or range, Places and locations), set in `INTERESTS` in tools/build_nav.py with their best pages in order and carried in nav-data.js. On the home page (section `pick`, after the numbers) it lists where to start; on /analysis (chips in the hero) it shows only the sections tagged for that interest (`SECI` in build_pages.py, written as `data-i`) and lists the related pages elsewhere. The choice is kept in the link (`?for=costs`) and in the browser.

## 13 November 2026 (evening): the filter reaches every page

* Every page and section in ITEMS carries at least one interest (`ITAGS` in tools/build_nav.py). A seventh interest, "Working with Dream Menu", covers partnerships, reports, press, how it works, take part and privacy.
* `build_nav.py` now refuses to run (`check_coverage`) if an item has no interest, or if a page on disk is not in ITEMS (sign-in, errors, internal tools and redirect stubs are listed in `NOT_PAGES`). Add new pages to ITEMS and ITAGS, or the build stops.
* The filter (interest.js) shows "Start here" (the hand-picked list in INTERESTS), then "Everything on <interest>" (all other tagged pages and sections, by site section, folded), and an "Every page" chip lists the whole site by section. The header drawer and the footer link to it ("Find what matters to you", "Find anything").
* Duplicate entries removed from the page list: a second "Partner briefing", a second "Every city's appetite", "Award winners on the map" and the "Work with us" sub-entry.

## 13 November 2026: "Can we trust it?" widened to 33 comparisons

* tools/build_benchmarks.py now holds 33 comparisons (21 public): new ones test Italian food (YouGov), sticky toffee pudding (YouGov), takeaway pizza (YouGov), zero-sugar cola (BSDA), margaritas and martinis (Bacardi Cocktail Trends), alcohol-free (Drinkaware), word of mouth (YouGov), small plates (OpenTable), Scottish scallops (Seafood Scotland), steak against chicken (AHDB/Worldpanel); for partners, fish mains (Seafish), beer and lager (HEINEKEN/CGA), lighter plates (Bidfood/CGA) and Scottish trading conditions (SLTA).
* Verdict labels: "Agrees", "Local insight" (stored as `differs`: the two disagree and the card explains the local reason) and "Context". Verdicts are set honestly per comparison; do not relabel a disagreement as agreement.

## 13 November 2026: benchmarks on every relevant page, one set of counts

* `tools/benchlib.py` reads bench-public.js and supplies the same wording and counts everywhere: a "How it compares" card on the dish pages it covers (`DISH` map), a line under This quarter on the home page, "Checked against outside research" on /press, and "Checked against the wider market" on /for-business (between `<!--fb-bench-->` markers, written by build_partner.py). Public comparisons only.
* On /analysis the counts in the "Can we trust it?" title and intro are `data-bn` spans that trend-charts.js rewrites from the comparisons the reader sees: 21 signed out, all of them for partners. Run order: build_benchmarks.py before build_partner, build_pages, build_home, build_press and build_venue_pages.
* Rank and share claims in benchmark text (number 2 dessert, number 3 cocktail, menus listing sticky toffee pudding, one guest in N picking alcohol-free) are computed from the data, not typed in.
* refresh_static.py no longer edits the retired awards entry in build_nav.py (that step would have stopped the Monday refresh).

## 13 November 2026: Gordon's Google Maps list on the map

* `tools/add_list_venues.py` reads the list as copied from Google Maps (`tools/data/gmaps/dream-menu-2025-26-list.txt`, 1,217 places) and `tools/data/gmaps/placements.py`, then calls add_venues.py. Result: 788 were already on the map, 30 are closed or gone (left off), 399 added: 300 placed from their name or list cluster, and 99 best guesses (Gordon: "place them anyway"; `GUESS` in placements.py, mostly Glasgow by default, labelled "Best guess ... to be confirmed" on the map). To place more, add a list number to PLACE (or SAME, for a venue already on the map under another name) and rerun.
* The list carries names only, so new pins are placed at neighbourhood or city level from the branch name or the list cluster, marked approximate, with a note. Five stated addresses are placed on their street.
* Totals now separate guests from the list: `meta.venues`, `pinned`, `countries` and `cities` count venues guests have named (1,695 venues, 30 countries, 122 cities); `meta.listed` (540) and `meta.on_map` / `on_map_pinned` (2,235 / 2,022) include list places. Before this, list-only places were counted as "venues named" (the old 1,935, 33 countries, 140 cities).
* On /map a list place says "On the Dream Menu list" instead of showing zero mentions.
* add_venues.py: new venues now create their city and country markets; runs with no interviews; more country codes.
* Site copy after the list import: city guides add "Also on Dream Menu's list" (list places in that city, not counted); /how-it-works explains list places (sentence kept current by refresh_static.py); the map intro and the Venue map entry mention the list; the partner venue extract counts every place on the map and says so. Venue pages use singular wording for one guest or one venue.

## Added 14 November 2026: seafood sub layers

Seafood sub layers come from one source, `tools/sublayers.py`, and appear the same way everywhere Seafood is shown as a food group:

- /analysis "What do guests want?": a ranking, not a breakdown. Seafood is listed dish by dish (scallops, prawns, oysters, white fish...) among the other food groups, top eight per course, with a note giving seafood's combined share. Built in `build_pages.py` (MIX courses) and drawn by `demandMix` in `trend-charts.js`.
- Partner category scorecard (/analysis chapter 6): each Seafood row (starter, main, side) has an "Inside" list.
- Partner "By Dunns range": the Fish and seafood cells name the leading sub layers.
- Partner course CSV download: one "sub layer" row per seafood dish and course.
- Seafood case study (`/case-studies/seafood`): full starter and main breakdowns.

Counts for dishes the site tracks come from `partner-data.js`, so they match the dish pages exactly; the rest come from `tools/data/seafood-sub-layers.json` (the Charting pivot of the Responses sheet). Any gap to the group total shows as "Other seafood". Sub layers link to a dish page where one exists. In the browser, `sublayers.js` reads `DM_MIX.sub` from `mix-public.js`. After a refresh, update the JSON from the pivot, then run `build_pages.py` and `build_case_studies.py`. To give another group sub layers, add its JSON to `FILES` in `tools/sublayers.py`.

## 16 November 2026: home page audit fixes

* **One base for course shares.** The hero card, the course cards (refresh_static.py) and the press kit now use shares of answers coded to a dish, the same base as /analysis and the home findings. Before, they divided by every answer, so tiramisu read 11.8% on one card and 12.2% on the next.
* **One scale and one decimal.** All five course cards share one bar scale (`hb_scale()`), so bar lengths compare across courses. Every share on the home page has one decimal place (`pc1`).
* **Plain names on the home page** (`HOME_NAME` in refresh_static.py): Steak (cut not named) shows as Steak, with a line in the chart notes; Irn-Bru and Coca-Cola are spelled the same in every debate label. A debate whose top two answers are under 3 points apart reads "Too close to call". Debates asked in fewer interviews say so.
* **build_home.py** now rewrites the source note on every run (before this it was added once and went stale), titles the band "Three findings and an outside check", words finding 1 in plain terms (`times()`), adds the "In their own words" section (anonymous guest answers chosen in `tools/data/home-quotes.json`, text read live from dm-data.js), puts the venue map with a picture (`map-card.webp`) in the Try it yourself band, adds a "The top five in every course" link to the hero card and the Report 2026 sponsor line under the hero buttons.
* **Data stamps**: the home page shows one date under the hero and the footer status panel, not a stamp under every section (`'/'` in dm-fresh.js).
* **Phones** (home.css, "audit fixes" block): shorter hero, the five numbers on one line, interest chips in one scrolling row, top three dishes per course, debates two to a row.
* **Footer** (build_nav.py): Partner sign-in left the About column (it is in the header and under Work with us); the bottom line keeps only the email address and Instagram, as the columns already link to privacy and how it works; the footer logo is decorative.

## 17 November 2026: site-wide audit fixes

* **Duplicate venues** (`tools/clean_venues.py`, rules in `tools/data/venue-cleanup.json`): 33 pairs that were the same place (same address, or a typo such as "Himalayan fine") are folded into one venue: mentions, guests, courses, dishes, quotes, best location and award links move to the kept venue; dm-cat.js is re-keyed (it is indexed by list position); the partner venue extract drops the duplicate rows; each old venue page redirects (vercel.json). Venues named went from 1,721 to 1,712; Ottoman Coffeehouse now has 7 mentions, Gleneagles 10, Ting Thai Caravan 7. Left apart on purpose, and listed in the JSON note: Cafe Andaluz (two branches, now named by street), Cardosi's, Murphy's Pakora / The Pakora Bar and Trust by Modou / 111 by Modou (different places, confirmed by Gordon).
* **Venue names**: 70 names that came in as full Google listings ("Masala Twist - Best Indian Restaurant In City Centre") have a plain display name, also in venue-cleanup.json. Branch names stay where a chain has more than one ("Nando's West End").
* **Analysis summary** (build_trends.py): the sides point is made once, in plain words; the top-five line no longer reads as if no dish moved. The chapter 3 intro (build_pages.py) uses the same wording.
* **Shorter analysis page** (`fold.js`, loaded by build_pages.py): secondary charts and long lists show at a set height with a "Show all" button (`FOLD` everywhere, `PHONE` under 720px). Links into a folded block open it. Phone height went from about 53,000px to 25,000px.
* **Map download halved** (`tools/build_map_awards.py`): map.html loads `awards-map.js` (no street addresses or source links, about 0.7 MB compressed instead of 1.4 MB); `awards-detail.js` loads the first time someone opens an award place. awards.js stays the source file for every build script.
* **Share images** (`tools/build_og.py`): og.png is redrawn with the current headline and totals, and every venue, city, neighbourhood and dish trend page gets its own card under og/ (no percentages, so a card is redrawn only when its text changes; tools/data/og-manifest.json). Fonts for the cards are in tools/fonts (TTF copies of the site fonts).
* Smaller: the home finding on menus links to /analysis#th-audit (the old #menu-gap anchor did not exist); rankings say "worldwide" instead of "in World"; the two operator-survey figures in the partner analysis say they are from the May 2026 survey.

## 18 November 2026: where to sell it, cost watch and market watch (partners)

* **Where to sell it** (`tools/build_accounts.py`, run automatically at the end of `build_venue_pages.py`, which now also runs `build_og.py` so a venue rebuild never drops the share images): every Scottish venue guests have named at least twice, scored for each supplier range by the dishes guests name there and their call (Back counts in full and Watch half, scaled by the trend score from `partner/dish-moves.js`; a dish in a food group with a Grow call counts a fifth). Each row gives the dish to open with, the next two, and anything clearly falling at the venue ("Watch out"). Writes `partner/sell-data.js` (behind sign-in). `partner/sell.js` draws it as chapter 7 on /analysis (top 12 per range and market) and as the full rep sheet at `/partner/accounts` (search, "Ours" ticks kept in the browser's localStorage only, print, CSV). The partner chapters after it are now 8 to 10.
* **Ranges** live in one place, `tools/ranges.py`, shared by "By Dunns range" and the rep sheet. Swap in Dunns' own category list there when Dunns shares it.
* **Cost watch**: `tools/data/market-watch.json` (`cost`) flags food groups with rising input costs (seafood, dairy and sugar desserts, cheese, potatoes, chicken; NIQ/Prestige Foodservice Price Index and the Brakes Summer 2026 report). `build_pages.py` adds the flag to the category scorecard rows and CSV; the rep sheet shows it above each range.
* **Market watch**: the same file (`watch`) holds six outside findings from 2026 trade research (venue churn, cities against towns, costs, price lines, smaller appetites, drinking less). `build_accounts.py` pairs each with a live Dream Menu figure and a "what to do" line; it shows in the partner briefing under This quarter (`#market-watch`, slot `#p-watch` written by build_partner.py). Outside figures are as reported in the 18 Nov research brief: check an original before Dunns quotes one externally, and update the file when a new edition is out.
* **Four new comparisons** in `build_benchmarks.py` (partner tier): Mediterranean food (OpenTable), Asian flavours and Latin American food (Bidfood 2026 trends, the Latin one a local insight: falling here), meat back with vegetables beside it (Datassential 2026). 37 comparisons in all, 21 public.

## 18 November 2026 (later): venue status and award coverage

* **Venue status** (`tools/build_status.py`, run inside `build_venue_pages.py` before `build_accounts.py`): downloads the Food Standards Agency hygiene register for all 32 Scottish councils (Open Government Licence, no key) and Glasgow City Council's licensed premises open data, then matches each Scottish venue guests name by postcode, distance and name. Matching is word by word and conservative (all distinctive words must match; a one-word name must be the first word of the other and not a common food word; partial matches must be a food business; a shared registration such as "Margo and Sebb's" counts for both). Writes `tools/data/venue-status.json` (not deployed): status listed / new (registered or licensed in the last 12 months) / check (full address known, not found), hygiene result and date, Glasgow licence number, capacity and grant date, and a hash of the licence holder so a change of holder is flagged on the next run (holder names are never stored). Also lists new leads: restaurants, cafés and bars in Glasgow and Edinburgh registered in the last 12 months and not yet inspected, plus Glasgow on-sales licences granted in that time, excluding venues guests already name. If the downloads fail it keeps the last file. Allowed domains needed: api.ratings.food.gov.uk, ratings.food.gov.uk, hub.arcgis.com.
* **Rep sheet** (`/partner/accounts`): a status line under each venue (hygiene result, new, licence changed hands, not found, licensed capacity), status and capacity in the CSV, and a "New openings to call" table with its own CSV. The market watch "churn" tile quotes the status counts.
* **Award coverage**: the rep sheet shows a guide award or, failing that, the venue's first trade award or listing. `tools/data/other-recognition.json` gains hand-checked recognition for Crabshakk Finnieston (Harden's, SquareMeal Silver Award), Celino's Partick (Scottish Italian Awards 2022) and Suissi Vegan Kitchen (HappyCow top 10, Good Food Guide); searches found none for Sugo Pasta, Malocchio or Royâ. The "guests and critics" finding now gives both measures: current guide awards, and guide awards plus trade awards and other lists (analysis.js `tb` line and the Marketing line in build_pages.py `_ROLES`).

## Open text, partner-only charts (24 Nov 2026)
- Report chapters (/report/*), the operator toolkit, tested ideas and the Insight Series are free to read. Their charts, exhibits and numeric data tables are for partners.
- `tools/build_gate.py` writes a public copy of each page to `/open/`, with every chart and numeric table swapped for a grey placeholder carrying a "Sign in to see it" link. Run it last, after `build_nav.py`.
- `middleware.js` (OPENTEXT) serves the `/open/` copy to signed-out visitors and the full page to partners, at the same address. `/open/` is noindex and disallowed in robots; the real addresses are in the sitemap.
- On /analysis, `nav.js` greys out the public charts for signed-out visitors (GATE list), except the samples in OPEN. The partner briefing stays fully locked.
- `/case-studies/guests-and-critics` stays fully open, charts included.

## Navigation (24 Nov 2026)
- Five sections, one list (SEC in tools/build_nav.py): Analysis, Reports, For foodies, For venues, About. The header dropdowns, the footer columns and the tab bar on short pages list the same pages, with the same names, in the same order. The Analysis dropdown lists the page's parts, then Dish trends.
- One bar under the header per page: long pages (3+ titled sections, or their own contents list) get only the "On this page" bar; short pages get only the section tab bar (is_long in build_nav.py, the same test nav.js uses). Breadcrumbs only on deep pages (venue, city, area, dish, report chapter, Insight Series report).
- Header right side: Search and Partner sign-in only (sign-in is also at the foot of the phone menu). Take part sits under For foodies.
- /reports is merged into /report: tools/build_reports.py writes the library (Report 2026 chapters, State of the Menu, Insight Series) into report.html under its hero, id="library"; /reports redirects there.
- The analysis hero no longer repeats its parts as a numbered list; the "On this page" bar does that.

## Audit rework (24 Nov 2026)
- Header grouped by reader: Findings (analysis, dish trends, Report 2026, State of the Menu, Insight Series, all reports), For partners (briefing, venues to call, data downloads, ways to work with us, press kit), For venues, For foodies, About. SEC in build_nav.py.
- Partner briefing on /analysis is visible to everyone: its sections and words show, and each chart slot is a greyed placeholder with "Sign in to see it" (nav.js SLOTS). Headlines that carry partner figures fall back to their data-short label when signed out.
- Partner sign-in returns to the page you were on (nav.js).
- Home: hero, numbers, findings, three doors (partners, venues, foodies), the dishes, guest voices, the debates. The interest filter, tools band, crave/over lists and risers left the home page (build_home.py).
- Headline interview count = latest interview number; % of interviews uses n_sheet (add_interviews.py).

## The analysis, split (24 Nov 2026)
- /analysis is an overview (the short version, a door to each part, what to do). Each part has its own page, written by tools/build_pages.py (PARTS): /analysis/demand, /analysis/change, /analysis/cities, /analysis/trust (with the method) and /analysis/partner (the briefing, greyed charts signed out).
- One tab bar (class anav) links the parts; no "On this page" bar on these pages. Old /analysis#<id> links are forwarded to the right page by a small script on the overview.
- No data downloads anywhere: no CSV buttons, no downloads section; /partner/data/ and *.csv are never served (middleware) or deployed (.vercelignore).

## The analysis, spread across the site (24 Nov 2026, replaces the split above)
- No analysis hub. Findings: /analysis/demand, /analysis/change, /analysis/cities. For partners: /analysis/partner. About: /analysis/trust (with the method). Written by build_pages.py (PARTS); each sits in its section's tab bar.
- "What should I do?" is split by reader: venues on /operators, opening or investing on /analysis/cities, suppliers on /analysis/partner, press on /press. The text is rewritten from the numbers each build (tools/data/evidence-roles.json); tools/build_evidence.py places the /operators and /press boxes. Run it after build_press.py and before build_nav.py.
- /analysis is a stub that forwards old /analysis#<id> links; with no hash it goes to /analysis/demand. The short version now lives on the home page findings.

## Four sections (24 Nov 2026)
- Header: Findings, For venues, For foodies, About, then Search and Partner sign-in. No partner menu.
- Findings: What guests want, What is changing, Where it differs, Partner briefing, Dish trends, Report 2026, State of the Menu, Insight Series. About: About Dream Menu, How it works, Can we trust it?, Ways to work with us, Press kit, Privacy.
- The rep sheet (/partner/accounts) is linked from the briefing's "Where to sell it" section, not the menu.

## Dish search (24 Nov 2026)
- build_nav.py adds every dish page (trends/*.html) to nav-data.js as `dishes` (name, course, one line). nav.js searches them with the pages; a dish whose name matches ranks first, with everyday aliases (ALIAS: dram, chips/fries, stp and so on).
- The home hero has a "Look up any dish" box (data-search-input); typing or tapping opens the site search with the text in it. Enter opens the top result.

## Grouped menus (25 Nov 2026)
- SUB in build_nav.py splits each section into two short titled groups. The dropdowns show them as titled columns (stacked on phones), the footer uses the same titles, and a short page's tab bar shows only its own group.
  Findings: The findings (What guests want, What is changing, Where it differs, Dish trends) | Reports and briefings (Partner briefing, Report 2026, State of the Menu, Insight Series).
  For venues: Tools for your venue | Get a review or a badge. For foodies: Where to eat | Join in. About: About Dream Menu | Work with us.
- The home page highlights no section. Old addresses (/insights, /intelligence, /explore) redirect straight to their pages.
- Link audit (25 Nov): 641 pages, no broken links. Unlinked by design: /review and /geocoder (admin), /login, /404, redirect stubs; the one-pager is linked from the signed-in briefing.

## 26 November 2026: category audit and a page for every dish

* Every food answer was checked against its category; 329 were recoded and overlapping categories merged or renamed (tools/data/category-audit-2026-11-26.json, and the CSV sent to Gordon to apply to the Responses sheet, which still holds the old codes).
* The four food courses in partner-data.js were rebuilt from the recoded answers by tools/rebuild_food_trends.py. Each course keeps its published top 14 dishes (`cats`) and top 10 groups, and adds `all`: every dish with 10 or more answers. tools/build_venue_pages.py gives each of those a dish page, lists them on /trends and in the menu check; charts and briefings still read the top 14. add_interviews.py keeps `all` in step; a dish that crosses 10 answers joins at the next rebuild from the sheet.
* Second audit (26 Nov 2026, later): variants of one dish are one dish, with the split kept as `parts` on the trend and shown as a "Which kind" card on the dish page: steak (every cut), chips and fries (every kind, from skinny fries to truffle and sweet potato), curry, pizza, burger, lamb, duck, cheesecake, ice cream, gelato and sorbet, pavlova and meringue, pâté and parfait; for drinks, margarita, Coke and Diet Coke, coffee, lager and beer (tools/merge_drink_families.py, run after rebuild_food_trends.py). Leftover catch-alls ("other pasta", "other fish"...) and non-dishes (drink instead of dessert, tasting menu, tapas) still count in course totals and groups but are not ranked and have no page. One name per dish across courses; plain labels; tapas and tasting menus are Other answers; pâté and charcuterie have their own group.
* Map and /rankings filters: dish-groups.js now also maps every audited category to its filter group (written by build_venue_pages.py from dm-labels.js), and /rankings and the city "Best for" panels read the audited categories. Before this the map's filter matched about 12% of dish mentions; it now matches 98%.
* Sub layers (26 Nov 2026, Gordon: group, don't split): tools/sublayers.py builds three levels for every food group, each answer counted once: the group, its dishes (10+ answers; the rest in one Other line) and, for family dishes, the kinds inside. The /analysis demand chart shows food groups that open into their dishes and kinds (sublayers.js); the /trends index opens family dishes into their kinds; the partner briefing tables do the same, with each kind's own trend. The old seafood split in the demand ranking is gone: seafood is one group that opens.
