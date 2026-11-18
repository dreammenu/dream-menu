"""Dream Menu's indicative supplier ranges: parent food groups rolled up the way a wholesaler's catalogue is split.
Used by build_briefing_extras.py (By Dunns range) and build_accounts.py (Where to sell it).
Swap in Dunns' own category list when Dunns shares it; every page that uses ranges follows this one list."""
RANGES = [
    ('Fish and seafood', ['Seafood']),
    ('Meat and poultry', ['Steak and beef', 'Chicken', 'Pork', 'Game and duck', 'Lamb']),
    ('Potatoes, vegetables and salad', ['Potatoes and fries', 'Vegetables and salad']),
    ('World foods, pasta and rice', ['Pasta and Italian', 'Asian', 'Indian', 'Mexican and Latin', 'Mediterranean and Middle Eastern']),
    ('Bakery, desserts and puddings', ['Bread', 'Tiramisu and creamy desserts', 'Cakes and bakes', 'Puddings', 'Chocolate desserts',
                                       'Cheesecake', 'Tarts and pies', 'Fruit and meringue']),
    ('Dairy, cheese and frozen', ['Ice cream and frozen', 'Cheese']),
    ('Soft drinks and low/no', ['Soft drinks', 'No and low alcohol']),
    ('Coffee and tea', ['Coffee and tea']),
    ('Beer, wine and spirits', ['Cocktails', 'Wine and fizz', 'Beer and cider', 'Spirits']),
    ('Pub classics, burgers and sharing', ['Burgers and fried food', 'Scottish and British classics', 'Sharing and tasting']),
]
RANGE_OF = {g: r for r, gs in RANGES for g in gs}
