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
