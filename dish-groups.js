/* dish-groups.js: guest-facing dish and drink categories for the /rankings and /map filters (21 Nov 2026).
   Each venue's "k" list holds raw dish categories with mention counts. This file folds them into
   about 20 groups a guest would search by (seafood, cocktails, pizza...). Raw labels that are not
   dishes (venue names, notes) match nothing and are left out. Labels cut short in the data are
   matched to the full label they start. */
(function(){
var G=[
 ['food','seafood','Seafood and fish',['Seafood','Fish / seafood','Seafood sides (mussels, oysters, prawns, crab)','Seafood platter']],
 ['food','japanese','Sushi and Japanese',['Sushi / Japanese','Tempura']],
 ['food','steak','Steak and beef',['Steak / beef','Steakhouse / Grill','Slow-cooked / braised beef','Tartare / carpaccio']],
 ['food','burgers','Burgers and fried chicken',['Burger','Chicken','Fried chicken / wings / tenders','Fried chicken sides (tenders, wings)']],
 ['food','grill','Lamb, pork, game and grills',['Lamb','Pork','Game / venison / duck','Game / snails','BBQ / grilled meats (skewers, churrasco, souvlaki)','Ribs (any)','Skewers / satay']],
 ['food','italian','Italian, pasta and pizza',['Italian','Pasta','Pizza','Fried Italian bites','Arancini / croquette','Burrata / cheese bites']],
 ['food','asian','Asian',['Asian','Asian small plates (rolls, dumplings, dim sum)','Asian noodles / hotpot','Asian sides (spring rolls, tempura, dosa, wonton)']],
 ['food','indian','Indian',['Curry / Indian','Indian','Pakora / Indian starters']],
 ['food','mexican','Mexican and Latin American',['Mexican / Latin American','Tacos / Mexican','Latin American bites','Nachos','Corn ribs / elote']],
 ['food','mideast','Middle Eastern',['Middle Eastern','Turkish / Middle Eastern grill','Dips (hummus, taramasalata, tahini)','Hummus / dips']],
 ['food','british','British, Scottish and pub classics',['British / Scottish / Pub','Sunday roast','Haggis bon bons','Haggis, neeps & tatties','Pie']],
 ['food','small','Small plates and sharing',['Small plates / sharing','Sharing boards (small plates, antipasti, charcuterie)','Chorizo (tapas-style)','Pâté / parfait','Olives','Peppers (padron, piquillo, jalapeño)','Street Food / Market']],
 ['food','veg','Vegan and vegetarian',['Vegan / Vegetarian','Vegetarian / vegan mains','Vegetable-forward starters']],
 ['food','sides','Chips, bread and sides',['Chips / fries','Potatoes (non-fries)','Side salad','Vegetable sides (greens, broccoli, cabbage)','Bread-based sides (naan, focaccia, bao, sourdough)','Bread / focaccia / sourdough / toast','Mac & cheese','Onion rings','Truffle fries','Cheese-based sides (mozzarella, halloumi, burrata)','Fried veg bites (cauliflower, croquettes)','Rice (any style)','Salad','Soup']],
 ['food','desserts','Desserts',['Tiramisu','Cake (general)','Cake / baked treats','Sticky toffee pudding','Cheesecake','Tart (any)','Chocolate (general)','Chocolate fondant / fudge cake / gateau','Pancakes / waffles / churros / French toast','Cheese (as dessert)','Pavlova / meringue / soufflé','Cookie dough','Affogato','Brownie','Crème brûlée / crema catalana','Crumble','Banoffee pie','Doughnuts','Fruit pie (apple, cherry, pecan)','Panna cotta','Key lime pie / posset','Eton mess','Rice pudding','Middle Eastern desserts (knafeh, gulab jamun)']],
 ['food','icecream','Ice cream and gelato',['Ice cream / gelato']],
 ['food','cafe','Cafés, bakeries and brunch',['Café / Bakery / Dessert','Toast / sandwich / toastie','Neighbourhood brunch cafes']],
 ['drink','cocktails','Cocktails',['Cocktail (general)','Margarita','Martini (non-espresso)','Espresso martini','Pornstar martini','Negroni','Spritz / Aperol spritz','Old Fashioned','Mojito','Piña Colada','Gin & tonic','Spirit-based mixed drinks (rum, tequila, amaretto)']],
 ['drink','wine','Wine, beer and whisky',['White/Red/Rose wine','Champagne / sparkling wine','Beer / lager / ale','Guinness','Whisky / dram']],
 ['drink','coffee','Coffee and soft drinks',['Coffee (non-cocktail)','Hot drinks (tea, hot chocolate)','Soft drink / diet soda','Milkshake / milk tea / boba','Lassi / smoothie','Milk','Mocktail (non-alcoholic specialty)']]
];
var EX={}, KEYS=[], LAB={};
G.forEach(function(g){LAB[g[1]]=g[2];g[3].forEach(function(r){var k=r.toLowerCase();EX[k]=g[1];KEYS.push(k)})});
var memo={};
function groupOf(raw){
  var k=String(raw||'').toLowerCase().trim();
  if(k in memo)return memo[k];
  var g=EX[k]||null;
  if(!g&&k.length>=6){for(var i=0;i<KEYS.length;i++){if(KEYS[i].indexOf(k)===0){g=EX[KEYS[i]];break}}}
  return memo[k]=g;
}
/* Mentions per group for one venue, cached on the venue. */
function venueGroups(v){
  if(v._dg)return v._dg;
  var o={};(v.k||[]).forEach(function(p){var g=groupOf(p[0]);if(g)o[g]=(o[g]||0)+(p[1]||0)});
  try{Object.defineProperty(v,'_dg',{value:o,enumerable:false})}catch(e){v._dg=o}
  return o;
}
/* <option> markup, food then drinks. */
function options(){
  var by={food:[],drink:[]};G.forEach(function(g){by[g[0]].push('<option value="'+g[1]+'">'+g[2]+'</option>')});
  return '<optgroup label="Food">'+by.food.join('')+'</optgroup><optgroup label="Drinks">'+by.drink.join('')+'</optgroup>';
}
window.DMG={groups:G,label:function(id){return LAB[id]||''},groupOf:groupOf,venue:venueGroups,count:function(v,id){return venueGroups(v)[id]||0},options:options};
})();
