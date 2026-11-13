# Menu audit notes, 13 November 2026

Venues audited: 45. Venues tried and skipped: 104. Worked down the United Kingdom list by mentions (not closed, not areas) to about rank 150.

Menus were read only from each venue's own website or its own PDF. Dish names and prices only.

## Why so many were skipped

- No website of its own (Instagram, delivery apps or listings only).
- Menu published only as an image, a flipbook or a script-loaded widget that cannot be read as text.
- Menu PDF hosted on a file host that the fetch tool would not follow, or the site refuses automated reading (robots).
- The web search allowance for the run (200 searches) ran out before the last venues were looked up. These are marked "not attempted" and are the first to retry next time.

## To check in the venue data

- The Gannet: reported closed at the end of 2025 by an outside guide; dm-data.js still has it open. Not changed here.
- Celentano's: appears to have moved to the Arthouse hotel on Bath Street in 2026. Not changed here.
- Casa Italian Kitchen is in Strathaven, listed under Glasgow.

## Method decisions

- Each dish share is worked out over the menus where that course was read (several menus print no desserts or keep them on a separate card), not over all audited venues.
- Every pasta main maps to "Other pasta" and every sushi roll or sashimi plate to "Sushi and sashimi"; these are whole categories, so their menu share is naturally high.
- Plain or lightly seasoned fries map to "Skinny fries"; chips of any thicker cut to "Triple-cooked chips". Guests who say "triple-cooked" may mean something narrower than "chips".
- Monkfish, sea bass, bream, skate and coley mains count with "Cod, hake and white fish", including in curries.
- Mochi ice cream and salt and chilli chips were left unmapped. Chutneys, pickles and raita were not recorded.
- Tasting-menu venues are under-represented: most print no course names.

## Skipped venues

- Crabshakk Finnieston (Glasgow, 45 mentions): Food menu is a PDF on crabshakk.co.uk that redirects to an off-site CDN; fetch refused
- Big Counter (Glasgow, 37 mentions): No own website or menu page found in three searches; only third-party listings.
- Corner Shop (Glasgow, 27 mentions): Own site (cornershopglasgow.co.uk) has no menu or PDF, only Instagram specials; /menu 404
- Porter & Rye (Glasgow, 23 mentions): Menus on porterandrye.com/menus are images only; image fetch failed, no readable text menu
- The Loveable Rogue (Glasgow, 20 mentions): Own Southside page links menus only as PDFs (/s/SOUTH-ALC-JULY-2026.pdf etc.) which redirect off-domain and WebFetch blocks them; no text menu on page.
- The Spanish Butcher Glasgow (Glasgow, 20 mentions): Menus only as PDFs on spanishbutcher.com; WebFetch blocked the PDF links (redirect to file host), no HTML menu on site
- Gloriosa (Glasgow, 15 mentions): Own site (gloriosaglasgow.com) only has a sample menu as an unreadable image
- The Palmerston (Edinburgh, 15 mentions): No own website found (only Instagram listed); menu not available from venue's own pages.
- Eleven Fifty Five (Glasgow, 14 mentions): Own website not found in search or listings within 3 attempts
- Suissi Vegan Kitchen (Glasgow, 14 mentions): Own site (suissivegankitchen.co.uk) has no readable menu text; /menu page empty
- Barry Fish (Edinburgh, 13 mentions): Own menu page (barryfish.co.uk/menus) shows dinner menu only as an image; image fetch failed
- Celino's Partick (Glasgow, 13 mentions): Own-site a la carte and dessert PDFs (celinos.com/menu/west/) are image-only, no readable text
- Gōst Bar & Restaurant (Glasgow, 13 mentions): Own site not found in search; guessed domains gostglasgow.com / gostglasgow.co.uk refused (robots_disallowed).
- Santa Lucia Merchant City Glasgow (Glasgow, 13 mentions): Could not find the venue's own website or menu in three searches (only listings, blogs, aggregators)
- Barras Market (Glasgow, 12 mentions): a market, not one venue with a menu
- Bread & Butter (UK chain, 12 mentions): not a venue: mostly bread and butter pudding answers
- Celentano's (Glasgow, 12 mentions): Relocated to Arthouse Hotel 2026; no current own-site menu found (old Cathedral House page has no menu, celentano.com failed)
- Fallachan Kitchen (Glasgow, 12 mentions): Tasting-menu PDFs on own site redirect to blocked Squarespace CDN; no dish names readable
- Paesano Pizza West End (Glasgow, 12 mentions): paesanopizza.co.uk menu is an image; only specials readable on West End page, main menu not readable
- Sabzi (Edinburgh, 12 mentions): Own site (sabzistreetfood.com) menu loads only via Flipdish ordering widget/app; no readable menu text
- Brett (Glasgow, 11 mentions): Own site not found by search; guessed domains refused (robots_disallowed); only Michelin/review listings
- The Gannet (Glasgow, 11 mentions): Reported closed at end of 2025 (Hardens); own site shows no menu
- Hey Palu (Edinburgh, 11 mentions): Cocktail bar; nibbles menu is an image only, could not be read
- Ramen Dayo (Glasgow, 11 mentions): No official website found in three searches; only delivery apps and review sites
- El Jefe’s (Glasgow, 10 mentions): Own site not found in search; guessed site eljefesglasgow.com refused (robots disallowed); only delivery/review listings surfaced
- The Clarence Glasgow (Glasgow, 10 mentions): Menu PDFs linked from theclarenceglasgow.co.uk redirect off-domain and WebFetch was blocked (3 attempts).
- West Side Tavern (Glasgow, 10 mentions): No own website or menu found in searches; only listings and reviews.
- The Caravan Shop (Glasgow, 10 mentions): All-day menu is a Squarespace PDF that redirects to a blocked domain; /menus also blocked
- Battlefield Rest (Glasgow, 9 mentions): Own site (battlefieldrest.co.uk/full-menu) shows menus only as images; dishes not readable.
- Kelvingrove Café (Glasgow, 9 mentions): Own site (kelvingrovecafe.com) shows food menus only as images; no readable menu text
- Lobo (Glasgow, 9 mentions): Own site not found by search (only OpenTable/review listings); lobo.scot fetch refused
- The Real Wan (Glasgow, 9 mentions): No own website found (only Instagram/Facebook and booking widget)
- GaGa kitchen + bar (Glasgow, 9 mentions): gagaglasgow.com homepage has no menu or menu link; /menu returns error
- Amore Ristorante e Pizzeria (Glasgow, 8 mentions): A la carte and dolci menus on amoreglasgow.co.uk are images only; dish names not readable.
- LYLA (Edinburgh, 8 mentions): Tasting-menu only (10 courses, £185); own site prints no course or dish names.
- La Bodega (Glasgow, 8 mentions): Own site labodegaglasgow.com returns 'site not found'; no other own menu page found
- Loop & Scoop (Glasgow, 8 mentions): Own site fetch refused (robots_disallowed); only Just Eat/review listings found
- Non Viet Restaurant (Glasgow, 8 mentions): Search returned only delivery apps/aggregators; guessed own domain nonviet.co.uk refused (robots_disallowed).
- ORO (Glasgow, 8 mentions): Could not find the venue's own website in three searches (only OpenTable, Deliveroo, reviews)
- Sebb (Glasgow, 8 mentions): duplicate, unclear entry for Sebb's
- Smokey Trotters Kitchen (Glasgow, 8 mentions): No own website found; only delivery-app and listing pages
- Table Twenty Eight (Glasgow, 8 mentions): table28.co.uk is JavaScript-only (no readable menu); /menus returns error
- The McMillan Bar + Chop House (Glasgow, 8 mentions): Own site lists A La Carte PDF but menu PDFs and menus page blocked by fetch tool (redirect off-site); no menu read
- Dumpling Monkey (Glasgow, 8 mentions): Own site not reachable (dumplingmonkey.co.uk blocked by robots, .com error page); web search budget exhausted
- Ardnamurchan Scottish Restaurant & Bar (Glasgow, 7 mentions): No own website/menu found in three searches; only OpenTable and review listings.
- Bar Vini (Glasgow, 7 mentions): Own site barvini.com has no menu or menu links (booking widget and socials only)
- Errol's Hot Pizza (Glasgow, 7 mentions): No own website or menu page found in three searches; only third-party listings.
- Ho Lee Fook (Glasgow, 7 mentions): No own website found (Instagram only); no own menu page
- Kelp (Glasgow, 7 mentions): kelpglasgow.com fetch refused (permission not granted; www variant robots-disallowed); kelp-restaurant.co.uk robots-disallowed
- La Gelatessa - Gelato & Coffee (Glasgow, 7 mentions): Own site not found (search returned only reviews/listings); guessed domain refused; search budget then exhausted
- Little Hoi An (Glasgow, 7 mentions): No own website found in search; guessed domain littlehoian.co.uk refused (robots_disallowed).
- Loon Fung Cantonese Restaurant (Glasgow, 7 mentions): Could not find the venue's own website or menu in three searches (only Deliveroo, listings)
- OUTLIER (Glasgow, 7 mentions): No own website found; listings link only to Instagram
- Pad T’aye Hamilton (Glasgow, 7 mentions): Own site not found in search; guessed site padtaye.co.uk refused (robots disallowed)
- The Delphine Glasgow (Glasgow, 7 mentions): Menus page (thedelphine.com/menus/) uses a script-loaded flipbook; no readable dish list or prices
- The Kirkmichael Arms (Ayr, 7 mentions): Own site fetch refused (robots disallowed); web search budget exhausted so no alternative own page found.
- UNALOME by Graeme Cheevers (Glasgow, 7 mentions): Own site/menu not found in three searches; only Michelin and review pages.
- Alma Mexicana (Glasgow, 6 mentions): No own website found in searches; no address in batch
- Bramble (Edinburgh, 6 mentions): WebFetch permission for bramblebar.co.uk not granted (timed out); cocktail bar, no food menu read
- Cail Bruich (Glasgow, 6 mentions): Tasting-menu only; sample dinner menu PDF redirects off-domain and was blocked, course names not readable
- Chateau-X Steakhouse Glasgow West End (Glasgow, 6 mentions): chateau-x.co.uk fetch refused (permission not granted; www variant robots-disallowed)
- Crabshakk Botanics (Glasgow, 6 mentions): Botanics menu PDF (Oct26) is linked from own site but the PDF fetch was blocked (redirects off-domain); no menu text on the page
- Daddy Marmalades (Glasgow, 6 mentions): Cocktail bar; no own menu found in search and candidate own domains returned empty JS-only pages.
- Eight Coffee Co (Glasgow, 6 mentions): Coffee shop/brunch venue; no own-site food menu found in two searches
- Fazenda (Edinburgh, 6 mentions): WebFetch blocked fazenda.co.uk/edinburgh/menus (site blocked/redirect off-domain); refused previously too
- Finsbay Flatiron (Glasgow, 6 mentions): finsbayflatiron.com/menu-1 shows the menu only as images, not readable
- HEYTEA (Byres Road) (Glasgow, 6 mentions): drinks only
- La Masa (Glasgow, 6 mentions): Own Glasgow site not found (lamasaglasgow.com blocked; lamasa.co.uk is an unrelated London branch linking only to delivery apps); web search budget exhausted
- Little Capo (Edinburgh, 6 mentions): Own site not found: web search budget exhausted, guessed domain failed.
- Maggie's Grill (Aberdeen, 6 mentions): Own site found (maggiesgrill.co.uk) but its menu page failed to fetch (client error) twice.
- Maison by Glaschu (Glasgow, 6 mentions): Own /menus page names only a few dishes, no full a la carte or prices
- Makars Mash Bar (Edinburgh, 6 mentions): WebFetch permission for makarsmash.com not granted (timed out); no other own-site URL known without search
- Malaga Tapas Bearsden (Glasgow, 6 mentions): Own site malagatapas.co.uk refused fetch (robots disallowed); only delivery-app menus found
- Mono (Glasgow, 6 mentions): Own site confirmed (monocafebar.com/food) but food menu is a PNG image whose fetch was blocked; no text menu
- Nippon Kitchen (Glasgow, 6 mentions): Only Toast online-ordering/Deliveroo/review pages found; guessed own domain failed; search budget then exhausted
- Noodles and Dumplings (Glasgow, 6 mentions): No own website found in search (only delivery/hygiene listings); guessed domain refused (robots_disallowed).
- Sotto (Edinburgh, 6 mentions): Menus only as PDFs on sottoedinburgh.com; WebFetch blocked the dinner PDF (redirect to file host)
- The Seafood Shack (Ullapool, 6 mentions): Daily-changing menu shown only as photos on own site; no readable dish list
- Ting Thai Caravan (Glasgow, 6 mentions): No official website found in three attempts; only delivery apps and listings
- Vinette (Edinburgh, 6 mentions): Own site (vinette.co.uk, 36 Broughton St) links a Sample Dinner Menu PDF but fetch was blocked (redirect off-site); no dishes on the page itself
- The Big Taquero (Glasgow, 6 mentions): thebigtaquero.com is a JS-only page returning no menu text (2 attempts); search budget exhausted.
- The Malletsheugh (Glasgow, 6 mentions): No own website/menu found; only aggregator and review sites.
- Aroma Coffee & Kitchen (Glasgow, 5 mentions): aromacoffeekitchen.co.uk blocked by robots.txt; own site unconfirmed, no search available
- Cafe Andaluz (Glasgow, 5 mentions): Own site confirmed (incl. Glasgow West Cresswell Lane page) but a la carte and dessert PDFs could not be fetched (client error / blocked redirect)
- Devil of Brooklyn (Glasgow, 5 mentions): No own menu found in search; candidate domain devilofbrooklyn.com returned an empty JS-only page.
- FIN & GRAPE (Edinburgh, 5 mentions): Menus only as PDFs on finandgrape.com; WebFetch blocked the dinner PDF (redirect to file host)
- L'Escargot Bleu (Edinburgh, 5 mentions): Sample menu is a PDF that redirects off-site (fetch refused); sample-menu page errored
- Mirin (Edinburgh, 5 mentions): mirinedinburgh.co.uk refused before and no other own domain obvious; not attempted per batch note
- Nauticus (Edinburgh, 5 mentions): Own site not reachable (one domain for sale, another robots disallowed); search budget exhausted.
- Pakistani Street Food Pollokshields (Glasgow, 5 mentions): No own website found; menu only on delivery apps.
- Quality Chop House (London, 5 mentions): Own site menus page lists no dishes (menu not in page text, no menu PDF linked)
- Ssamm Korean BBQ (Glasgow, 5 mentions): ssamm.co.uk permission not granted (timed out); ssammkoreanbbq.co.uk blocked by robots.txt
- The Anchor Line (Glasgow, 5 mentions): Own /menus page links a la carte only as PDF (/s/AL-A3-ALC-MENU-AW2026-Web-Copy.pdf) which redirects off-domain and WebFetch blocks it; no text menu on page.
- The Dipping Lugger (Ullapool, 5 mentions): Own site thedippinglugger.co.uk refused fetch (robots disallowed); no other own-site menu found
- The Kitchin (Edinburgh, 5 mentions): Food menu on thekitchin.com/menus is an image hosted on Google Drive; fetch robots-disallowed
- Turkiye EFES Restaurant (Glasgow, 5 mentions): Own site turkiyeglasgow.co.uk shows a la carte and dessert menus only as images; not readable
- Wagamama (UK chain, 5 mentions): wagamama.com/menu loads dishes dynamically; only 5 lunch items and no prices readable
- Wetherspoons (UK chain, 5 mentions): jdwetherspoon.com food-drink and pubs pages have no national menu with dishes/prices; menus are per pub behind pub search, not reachable in 3 attempts
- tipo (Edinburgh, 5 mentions): WebFetch permission for tipoedinburgh.co.uk not granted (timed out)
- Noto (Edinburgh, 5 mentions): WebFetch permission for notoedinburgh.co.uk not granted (timed out)
- Anxious Pete's (Glasgow, 4 mentions): anxiouspetes.co.uk robots-disallowed; anxiouspetes.com is a Square Online page with no address, menu or prices
- Beirut Star (Glasgow, 4 mentions): beirutstar.co.uk robots-disallowed; no other own domain known
- Brel (Glasgow, 4 mentions): WebFetch permission for brelbar.com not granted (timed out)
- Chaakoo Bombay Cafe (Glasgow, 4 mentions): Menus page only links a PDF (chaakoo.co.uk/s/PR-CHK-GLAEDI-ALC-Menu-SS26.pdf) whose fetch was blocked (redirect off-domain)

## Mapping and menu-choice decisions the collectors were unsure about

- Royâ: a la carte page has no desserts; Mazzeh veg plates (Broccoli, Baby Heritage Carrot) recorded as starters per section; Ribeye Tataki left null (seared, not tartare/carpaccio); Iskander Steak null (cut not clear, Iskender-style dish)
- Six by Nico: 6-course tasting menu 'American Murder Mystery' (cooking 05 Oct-15 Nov, current on 13 Nov); courses 1-4 recorded as starters, 5 as main, 6 as dessert; snacks as starters; only the two add-ons carry prices; vegetarian variants omitted as duplicates; Burnt End Hash Browns grouped Steak and beef on the assumption of beef burnt ends
- Nonna Said…: 'street food' and 'loaded' sections recorded as starters (loaded items look like loaded fries but sit with street food); 'Nonna's rings' left null (not stated as onion rings); 'Garlic, chilli and lime fries' null rather than Loaded fries (seasoned, not topped); crust add-ons and dips omitted; no desserts on menu
- Sebb's: menu has no section headings; small plates coded as starters, only rump and half chicken (£35, likely to share) as mains; sea bream (£12.50) coded starter; spiced fries left null rather than Skinny fries
- Dogstar: 'Sample Autumn 26' PDF prints prices in a separate column that cannot be matched to dishes in extracted text, so prices omitted; no course headings, so starter/main/side split is my judgement (scallop starter; grouse, turbot, pumpkin rice mains; mustard leaf salad side); desserts from separate dessert PDF (dogstar-dessert-menu-2026.pdf)
- Maki & Ramen: used chain-wide menu page (no prices printed); individual hosomaki/nigiri/sashimi pieces and rice/egg extras left out; mochi mapped Ice cream with group Asian; maki rolls coded as mains (Sushi and sashimi)
- Madurai: PDF text extraction jumbled section headings; five priced £17-25 items under 'Starters' (Chutta Monkfish, Pollicha Salmon, Elakkai Lamb Chops, Chicken Rhost, Vaattuna Paneer Broccoli) coded as mains; no desserts printed on a la carte PDF; monkfish curries mapped Cod, hake and white fish with group Indian; curry leaf potatoes left null (cooking style unclear)
- Malocchio: crispy potatoes and focaccia are listed under cicchetti so recorded as starters; 'our proteins' section (incl. scallops, fried provolone) treated as mains; pizzette treated as Pizza mains; 'sourdough focaccia' mapped to null/Bread per focaccia rule.
- Chaophraya: national a la carte (JULY26 estate PDF) and Sep26 dessert menu as listed on the Glasgow menus page, read via fetch summary; multi-protein dishes recorded once at lowest price; Thai soups recorded as starters, salads as mains; Five Spice Fries left null (seasoned, not clearly topped); Pak choi mapped to Greens (judgement call); sides prices on the page differ slightly from the PDF (used a la carte prices).
- The Alchemist Glasgow: used the chain's national food menu PDF (alchemist-food-menus-3.pdf, undated; chosen over -1.pdf as it carries higher, likely newer prices) - no Glasgow-specific menu found; read via fetch summary, which omitted the fries section (fries not recorded); plant-based duplicates and burger add-ons skipped; Caesar and bang bang salads grouped Chicken by assumption; BBQ pork mapped to Pulled pork and BBQ ribs; Salt & shake potatoes left as a starter (null).
- El Santo: desserts are not in the a la carte PDF; dessert names (no prices) taken from the venue's own page https://elsanto.co.uk/a-la-carte/. Tacos listed under Small Plates so recorded as starters. Guacamole mapped to 'Hummus, dips and falafel' (dip) with no group as starter groups have no Latin option.
- Sannio: a la carte PDF blocked (redirect), used text of the venue's own /menu page. Flat iron steak recorded once at 7oz price (£22). 'Gelarto Ice Cream' mapped to Gelato as printed spelling suggests gelato. 'Skinny Dirty Spicy Fries' mapped to Loaded fries. Sanguinaccio è Gamberoni (black pudding & king prawns) mapped to Prawns. 24ct gold tiramisu omitted as a duplicate variant.
- The Ivy Buchanan Street: page is titled The Ivy Glasgow Brasserie (the Buchanan St site) and currently includes festive items (Festive Shepherd's Pie, Pigs in Blankets, Mince Pies); haggis bon-bons had no printed price; desserts taken from the venue's separate desserts-menu page (https://ivycollection.com/restaurants-near-me/the-ivy-scotland/the-ivy-glasgow/desserts-menu)
- Sugo Pasta: Mitchell Street specials included, Cresswell Lane-only specials excluded; sourdough with evoo mapped to Sourdough and butter (listed as a side); 'Chocolate or Raspberry Sauce' add-on excluded
- Five March: single small-plates list; split into s/m by size and price (cavatelli, coley, pork collar, beef shin, chicken sandwich as mains); labneh mapped to Hummus, dips and falafel; sourdough with brie and honey left null (not plain bread and butter); burger night, lunch deal and set menus excluded
- Casa Italian Kitchen: venue is in Strathaven (batch city Glasgow); evening menu is a 'sample' set menu (2 courses £29.50 / 3 £34.50) so starters, mains, pizzas and desserts carry no prices; section headings were jumbled in the PDF text so course assignment is best reading; snacks recorded as starters
- Gleneagles: used The Birnam (all-day brasserie) dinner PDF as the main a la carte; large cuts priced per 100g so price omitted; prime rib on the bone mapped to Ribeye steak; smoked cod's roe mapped to Hummus, dips and falafel (taramasalata-style); kids section, 'Thoughtfully Crafted' kids dinner, small bites, first dessert list (£8, appears to be children's) and snacks platter excluded; sauces excluded; baby potatoes left null (not stated as roast/crispy)
- Kyloe: desserts read from the separate dessert PDF (https://kyloerestaurant.com/download/13937/?tmstv=1784896178); 'Roasted King Prawns' £8 (apparent steak add-on), 'Steak Me Out' and 'Midweek steak frites' deals excluded; Sharing Sunday Roast included as main; 'of the day' steaks mapped to Steak (cut not named) with no price (market price); ice cream price is per scoop; Creamed Spinach Yorkie mapped to Greens and creamed spinach
- Ka Pao: PDF has no starter/main headings; split small plates (<=12.50) as starters and curries/large plates as mains. Charred cabbage (10.00) and choi sum treated as sides mapped to Greens. Skate wing mapped to Cod, hake and white fish. Soft-serve ice cream price not clearly printed, omitted.
- Elements: used 'Seasonal Menu' PDF (Menus-Oct-2026) with priced a la carte rather than the £85 fixed-price A-la-carte PDF; PDF text layout scrambled, so prices taken from fetch tool's best pairing. Wee Bites and Small Plates both recorded as starters; no sides printed. Separate 'STARTERS' list (pressed duck etc, likely set lunch) excluded. Deer tartare left null (beef-only rule).
- Cafe Gandolfi: 'Crispy Open Lasagna' listed under Smaller so recorded as starter (no starter pasta label). Banoffee Pavlova left null (not berry-led).
- Mother India: menu read from the Mother India page (Westminster Terrace); no desserts printed. 'Food for Grown Ups' veg dishes (small price 9.00 used) recorded as sides; chutneys and raita omitted as condiments. All mains grouped Indian (cuisine) rather than Chicken/Seafood; Cod Malabar mapped to Cod, hake and white fish.
- Old Pal: all-day PDF layout scrambled; 'Salt & vinegar onion rings 25' under mains appears to be part of the seabass line (likely seabass price 25), so onion rings omitted and seabass recorded without price.
- Margo: food page has no starter/main headings; split by order and price (nibbles+small plates to gnocchi = s; hake to fish of the day = m; chips to broccoli = d). Focaccia offered with whipped butter mapped Sourdough and butter; skate wing mapped Cod, hake and white fish; cured trout with tiger milk mapped Ceviche and crudo.
- Eleanore: only a 'sample menu' on own site, priced as set dinner (2 courses £39 / 3 £45); only snacks and sides carry prices. Oysters price is £8 for two. Tirami-choux left null rather than Tiramisu.
- Miller & Carter Glasgow: Glasgow branch menu pages did not render dishes; used chain's national main-menu PDF on millerandcarter.co.uk (2025 'ln25' file, region/pricing tier unstated, may not be the current Scottish price list).
- Chez Jules: 'Le Pave de boeuf' mapped Steak (cut not named); 'Le Petit' (unclear steak) left null; 'La cote de boeuf moyenne' mapped Sharing steaks though may be for one; Formules pour deux recorded as mains at lowest (single/half) price.
- Dishoom: menu page sections were unlabeled blocks; salads/rolls and grills treated as mains, small plates as starters. Several described dishes (chicken ruby/makhani, chicken biryani, keema pau, poppadoms, chole puri) had no readable name/price and were omitted; puddings are on a separate menu not read.
- Dishoom: Goan Monkfish Curry mapped to 'Cod, hake and white fish' (monkfish main) with group Indian.
- Civerinos Finnieston: PDF text extraction was jumbled; pizza prices recorded at the 14in whole-pie price (Detroit Double Pepperoni at pie price); side/starter prices could not be matched to items so omitted. Lunch-only panuozzo and dips left out. Starter vs side split for bites/gnocchi/salads is a judgement call.
- Gaucho Edinburgh: the Edinburgh page and /menu render only Snacks (rest is JS), so used the chain's most recent full a la carte PDF on its own site (Jan 2026, coded CNW, location not stated); no desserts printed in that ALC; Edinburgh page snack prices differ slightly (Pan de Bono 5.95, Rosemary Focaccia listed). Gaucho Platter mapped to Sharing steaks; 'Green Vegetables' side mapped to Greens.
- Gaucho Edinburgh: dish list extracted via fetch summariser from the PDF, not verbatim text.
- Hawksmoor Edinburgh: puddings are on a separate menu not readable from the ALC page/PDF, so no desserts recorded. Large cuts (T-bone, porterhouse, prime rib, chateaubriand, monkfish, lobster) are priced per 100g, so price omitted; bone-in prime rib mapped to Sharing steaks. Longhorn Feast cuts recorded as separate items. Beef dripping fries mapped to Skinny fries. Sunday Roast and chicken prices taken from the PDF (food page shows chicken at 24).
- Ardfern: evening menu is a small-plates 'sample menu'; the three larger plates (venison sausage, mussel flatbread, burger) recorded as mains, the rest as starters. Venison sausage left as dish null (not a venison main as such).
- Mowgli Street Food Glasgow: street snacks and small street plates recorded as starters; grill items and curries as mains; 'Companions' as sides. Lamb Kofta Kebabs mapped to Kebab and souvlaki. Fenugreek fries mapped to Skinny fries (seasoned) and Treacle Tamarind Fries to Loaded fries. Four ice cream cone flavours recorded as one entry; kids menu excluded.
- Grosso: Chicken Parmigiana listed under Pasta, recorded as main null/Chicken rather than Other pasta; Chicken Caesar Salad and focaccias listed under 'Bits on the side' so recorded as sides; menu PDF has no desserts section
- CIBO: Salads section (Caesar, Panzanella etc., £8-10) recorded as starters; Straccetti alla Romana (beef strips salad) given Vegetables and salad; Frutti di Mare listed under Risotto so named 'Risotto Frutti di Mare'; Antipasto Cibo lowest price (for 1) used; Patatini Pazzo printed without price; Cacio e Pepe side left null
- Ox and Finch: page has two unlabelled food menus; savoury dishes from the first, desserts from the second (first had none)
- Ox and Finch: whipped cod roe mapped to Hummus, dips and falafel (taramasalata-style); skate wing left null (not in white-fish list); 450g sirloin left null (not stated as sharing)
- Ox and Finch: crème brûlée tart mapped null / Tarts and pies rather than Crème brûlée
- La Lanterna: City Centre a la carte PDF has no food desserts listed; none recorded
- La Lanterna: Fiorentina (T-bone) mapped to Sharing steaks though not explicitly 'to share'; Costata mapped to Ribeye steak; Tournedos Rossini mapped to Fillet steak; Tagliata mapped to Steak (cut not named)
- La Lanterna: four risottos recorded under their printed names (MARE MONTI etc., printed under a Risotto heading)
- Yorokobi by CJ: used full menu PDF; excluded Lunch & Early Bird bentos and per-head Set Menus. Special rolls, sashimi platters and sushi sets mapped as mains 'Sushi and sashimi'; plain maki/hand rolls and 2-piece nigiri recorded as starters (Asian, dish null). For multi-option items the first-listed price is used (e.g. sashimi 12 pieces, gyoza vegetable, KFC 3 pieces, tempura prawn). Takoyaki mapped to 'Squid and octopus'. No dessert section on the menu.
- Swadish: desserts taken from the separate dessert menu PDF (https://www.swadish.co.uk/_files/ugd/47693f_35ce8040efa744c6a04e9d8559e36eb5.pdf). Lamb Raan and Atta Chicken (serve 2-4) recorded as mains. Bun Muska (amuse, no price) and tasting menu omitted. Sea bass/bream/halibut/monkfish mains mapped to 'Cod, hake and white fish' with group Indian. Indian desserts put in group Asian; 'Chocolate and Raspberry' form unknown so dish null.
- Sticks'n'Sushi: used UK main menu PDF (Oct 2026) plus UK dessert PDF (https://a.storyblok.com/f/286316/x/341c8b9adf/sns-dessert-uk-2026-07-150x150-web.pdf) for desserts; menu URL field holds the main PDF only
- Sticks'n'Sushi: sashimi, nigiri, aburi, rolls, maki and uramaki treated as mains (Sushi and sashimi, group Asian); nigiri/sticks priced at the lowest (2 pcs) price
- Sticks'n'Sushi: yakitori sticks treated as mains, grouped by main ingredient, dish null
- Sticks'n'Sushi: set menus (As Good As It Gets, Set For Success, Perfect Day, Shake Overdrive, Mixed Emotions, Four Meal Drive, Beautiful Mess, Greenkeeper, Robust) omitted as set menus
- Sticks'n'Sushi: Kani Korokke (crab croquette) mapped to Crab; Ebi Sando mapped to Prawns and langoustines; Maguro Carpaccio (tuna) mapped to Ceviche and crudo; Gindara no Miso (black cod/sablefish) left null
- Sticks'n'Sushi: Come for a Swim (45, sharing selection) recorded as starter, Sharing and tasting; Gohan side printed with two unlabelled prices 2.6 and 4, lowest used
- Sticks'n'Sushi: dessert names are printed as Mango/Matcha/Goma/Sakura; mapped from descriptions (coconut rice pudding, dark chocolate fondant, vanilla crème brûlée, vanilla ice cream)
- 1610 at The Globe Inn: dinner a la carte PDF has no dessert section; Smoked Butter Jersey Royals mapped null (not crispy/roast)
- Amalfi: no desserts on the a la carte page; Homemade Breadbasket left null (not clearly bread and butter); duplicate Focaccia side omitted; Seasonal Vegetables null; veal dishes group null
- Babs: dessert PDF returned a bot-verification page twice so desserts missing; two unheaded blocks in the food PDF assigned by guess (couscous/calamari/saganaki/souvlaki/soutzoukakia/house bread/fritters/Greek salad as small plates; Mixed Bab, wraps, Bifteki burger as mains); shawarma/gyros wraps, shish platters and Iskender mapped Kebab and souvlaki; garlic parm and topped fries as Loaded fries
- Bantawala: PDF layout scrambled prices for pakoras, dosas, tandoor and the choice-of-protein curry list, so those are recorded without prices; curry-base list recorded as mains; Venison Curry mapped Venison; condiments (chutney, pickle, raita) recorded as sides
- Bucks Bar: national menu on bucksbar.co.uk (branch not separately priced); wings recorded once at 4-wing price; Koffmann's Fries mapped Skinny fries; Salt and Chilli Chips mapped Loaded fries; chicken burgers group null per burger rule
