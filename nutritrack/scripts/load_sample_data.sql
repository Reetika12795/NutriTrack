-- =============================================================
-- NutriTrack Sample Data - Real products from Open Food Facts
-- =============================================================

\c nutritrack;
SET search_path TO app, public;

-- =============================================================
-- CATEGORIES
-- =============================================================
INSERT INTO app.categories (category_name, level) VALUES
('Breakfast cereals', 1),
('Yogurts', 1),
('Chocolate', 1),
('Beverages', 1),
('Snacks', 1),
('Bread & Bakery', 1),
('Cheese', 1),
('Meat & Poultry', 1),
('Fruits & Vegetables', 1),
('Pasta & Rice', 1),
('Sauces & Condiments', 1),
('Dairy', 1),
('Frozen meals', 1),
('Biscuits & Cookies', 1),
('Spreads', 1)
ON CONFLICT (category_name) DO NOTHING;

-- =============================================================
-- BRANDS
-- =============================================================
INSERT INTO app.brands (brand_name, parent_company) VALUES
('Nutella', 'Ferrero'),
('Coca-Cola', 'The Coca-Cola Company'),
('Danone', 'Danone Group'),
('Kelloggs', 'Kellogg Company'),
('Barilla', 'Barilla Group'),
('President', 'Lactalis'),
('Lu', 'Mondelez'),
('Herta', 'Nestle'),
('Bonduelle', 'Bonduelle Group'),
('Panzani', 'Ebro Foods'),
('Lindt', 'Lindt & Sprungli'),
('Evian', 'Danone Group'),
('Bonne Maman', 'Andros Group'),
('Saint Agur', 'Savencia'),
('Activia', 'Danone Group'),
('Special K', 'Kellogg Company'),
('Haagen-Dazs', 'General Mills'),
('Innocent', 'The Coca-Cola Company'),
('Bjorg', 'Wessanen'),
('Michel et Augustin', 'Bel Group'),
('Carte Noire', 'JDE Peets'),
('Tropicana', 'PepsiCo'),
('Yoplait', 'General Mills'),
('Charal', 'Bigard Group'),
('Fleury Michon', 'Fleury Michon Group'),
('Heinz', 'Kraft Heinz'),
('Amora', 'Unilever'),
('Cristaline', 'Sources Alma'),
('Perrier', 'Nestle'),
('San Pellegrino', 'Nestle')
ON CONFLICT (brand_name) DO NOTHING;

-- =============================================================
-- PRODUCTS (100 real-ish products with accurate nutrition data)
-- =============================================================

-- Breakfast cereals
INSERT INTO app.products (barcode, product_name, generic_name, quantity, brand_id, category_id, energy_kcal, energy_kj, fat_g, saturated_fat_g, carbohydrates_g, sugars_g, fiber_g, proteins_g, salt_g, sodium_g, nutriscore_grade, nutriscore_score, nova_group, ecoscore_grade, countries, ingredients_text, completeness_score, data_source) VALUES
('3175681851856', 'Special K Classic', 'Breakfast cereal', '440g', (SELECT brand_id FROM app.brands WHERE brand_name='Special K'), (SELECT category_id FROM app.categories WHERE category_name='Breakfast cereals'), 379, 1586, 1.5, 0.3, 80, 17, 2.5, 14, 1.13, 0.45, 'B', 1, 4, 'B', 'France', 'Rice, wheat gluten, sugar, defatted wheat germ, salt, barley malt flavouring, vitamins and minerals', 0.85, 'sample'),
('3175681105393', 'Kelloggs Corn Flakes', 'Corn flakes', '500g', (SELECT brand_id FROM app.brands WHERE brand_name='Kelloggs'), (SELECT category_id FROM app.categories WHERE category_name='Breakfast cereals'), 378, 1604, 0.9, 0.2, 84, 8, 3, 7, 1.13, 0.45, 'A', -1, 4, 'B', 'France', 'Corn, sugar, salt, barley malt extract, vitamins and minerals', 0.90, 'sample'),
('7613034626844', 'Nestle Fitness', 'Whole grain cereal', '375g', NULL, (SELECT category_id FROM app.categories WHERE category_name='Breakfast cereals'), 357, 1508, 1.5, 0.3, 76, 17, 5.3, 8.5, 0.78, 0.31, 'B', 2, 4, 'B', 'France', 'Whole grain wheat, rice, sugar, wheat gluten, glucose syrup, palm oil', 0.75, 'sample'),
('3268840001008', 'Bjorg Muesli Fruits', 'Organic muesli with fruits', '375g', (SELECT brand_id FROM app.brands WHERE brand_name='Bjorg'), (SELECT category_id FROM app.categories WHERE category_name='Breakfast cereals'), 352, 1487, 4.5, 0.7, 66, 17, 7.5, 9, 0.05, 0.02, 'A', -1, 3, 'A', 'France', 'Oat flakes, wheat flakes, raisins, sunflower seeds, dried apricots, dried figs', 0.80, 'sample'),

-- Yogurts
('3033490594046', 'Activia Nature', 'Natural yogurt', '4x125g', (SELECT brand_id FROM app.brands WHERE brand_name='Activia'), (SELECT category_id FROM app.categories WHERE category_name='Yogurts'), 72, 303, 3.3, 2.2, 5.1, 5.1, 0, 4.2, 0.14, 0.06, 'A', -4, 3, 'B', 'France', 'Milk, lactic ferments including Bifidus actiregularis', 0.90, 'sample'),
('3033490004705', 'Danone Nature', 'Plain yogurt', '4x125g', (SELECT brand_id FROM app.brands WHERE brand_name='Danone'), (SELECT category_id FROM app.categories WHERE category_name='Yogurts'), 58, 244, 2.8, 1.8, 4.0, 4.0, 0, 4.1, 0.13, 0.05, 'A', -5, 1, 'A', 'France', 'Whole milk, skimmed milk powder, lactic ferments', 0.92, 'sample'),
('3329770044944', 'Yoplait Panier Fraise', 'Strawberry yogurt', '4x130g', (SELECT brand_id FROM app.brands WHERE brand_name='Yoplait'), (SELECT category_id FROM app.categories WHERE category_name='Yogurts'), 91, 385, 1.7, 1.1, 14.5, 13.2, 0.3, 3.4, 0.11, 0.04, 'C', 8, 4, 'C', 'France', 'Milk, strawberry preparation (13%), sugar, cream, modified corn starch', 0.85, 'sample'),
('3033490573041', 'Activia Vanille', 'Vanilla yogurt', '4x125g', (SELECT brand_id FROM app.brands WHERE brand_name='Activia'), (SELECT category_id FROM app.categories WHERE category_name='Yogurts'), 87, 367, 2.9, 1.9, 11.3, 10.8, 0, 3.6, 0.13, 0.05, 'C', 6, 4, 'B', 'France', 'Milk, sugar, cream, modified starch, vanilla extract, lactic ferments', 0.88, 'sample'),

-- Chocolate
('3017620422003', 'Nutella', 'Hazelnut spread with cocoa', '400g', (SELECT brand_id FROM app.brands WHERE brand_name='Nutella'), (SELECT category_id FROM app.categories WHERE category_name='Spreads'), 539, 2252, 30.9, 10.6, 57.5, 56.3, 1.8, 6.3, 0.11, 0.04, 'E', 26, 4, 'D', 'France', 'Sugar, palm oil, hazelnuts (13%), skimmed milk powder, fat-reduced cocoa, lecithins, vanillin', 0.95, 'sample'),
('3046920028363', 'Lindt Excellence 70%', 'Dark chocolate 70% cocoa', '100g', (SELECT brand_id FROM app.brands WHERE brand_name='Lindt'), (SELECT category_id FROM app.categories WHERE category_name='Chocolate'), 545, 2277, 41, 25, 29, 22, 12, 10, 0.03, 0.01, 'D', 14, 4, 'C', 'France,Switzerland', 'Cocoa mass, sugar, cocoa butter, cocoa powder, bourbon vanilla beans', 0.92, 'sample'),
('3046920029704', 'Lindt Excellence 85%', 'Dark chocolate 85% cocoa', '100g', (SELECT brand_id FROM app.brands WHERE brand_name='Lindt'), (SELECT category_id FROM app.categories WHERE category_name='Chocolate'), 580, 2416, 46, 28, 19, 11, 13, 13, 0.02, 0.01, 'C', 10, 4, 'C', 'France,Switzerland', 'Cocoa mass, cocoa butter, cocoa powder, fat-reduced cocoa, sugar, bourbon vanilla beans', 0.91, 'sample'),
('7622210449283', 'Milka Tendre au Lait', 'Milk chocolate', '100g', NULL, (SELECT category_id FROM app.categories WHERE category_name='Chocolate'), 530, 2222, 29.5, 18.5, 59, 56, 1.5, 6.3, 0.33, 0.13, 'E', 25, 4, 'D', 'France', 'Sugar, cocoa butter, skimmed milk powder, cocoa mass, whey powder, palm fat, milk fat, hazelnut paste', 0.80, 'sample'),

-- Beverages
('5449000000996', 'Coca-Cola Classic', 'Cola', '1.5L', (SELECT brand_id FROM app.brands WHERE brand_name='Coca-Cola'), (SELECT category_id FROM app.categories WHERE category_name='Beverages'), 42, 180, 0, 0, 10.6, 10.6, 0, 0, 0.01, 0, 'E', 18, 4, 'D', 'France', 'Carbonated water, sugar, colour (caramel E150d), phosphoric acid, natural flavourings including caffeine', 0.95, 'sample'),
('5449000131805', 'Coca-Cola Zero', 'Sugar-free cola', '1.5L', (SELECT brand_id FROM app.brands WHERE brand_name='Coca-Cola'), (SELECT category_id FROM app.categories WHERE category_name='Beverages'), 0.3, 1.3, 0, 0, 0, 0, 0, 0, 0.02, 0.01, 'B', 1, 4, 'C', 'France', 'Carbonated water, colour (caramel E150d), phosphoric acid, sweeteners (aspartame, acesulfame K), natural flavourings, caffeine', 0.93, 'sample'),
('3274080005003', 'Evian', 'Natural mineral water', '1.5L', (SELECT brand_id FROM app.brands WHERE brand_name='Evian'), (SELECT category_id FROM app.categories WHERE category_name='Beverages'), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'A', -15, 1, 'A', 'France', 'Natural mineral water', 0.95, 'sample'),
('3179732340108', 'Cristaline', 'Natural spring water', '1.5L', (SELECT brand_id FROM app.brands WHERE brand_name='Cristaline'), (SELECT category_id FROM app.categories WHERE category_name='Beverages'), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'A', -15, 1, 'A', 'France', 'Natural spring water', 0.90, 'sample'),
('7613035839625', 'Perrier', 'Sparkling natural mineral water', '1L', (SELECT brand_id FROM app.brands WHERE brand_name='Perrier'), (SELECT category_id FROM app.categories WHERE category_name='Beverages'), 0, 0, 0, 0, 0, 0, 0, 0, 0.01, 0, 'A', -15, 1, 'A', 'France', 'Carbonated natural mineral water', 0.88, 'sample'),
('3048110067506', 'Tropicana Orange', 'Pure premium orange juice', '1L', (SELECT brand_id FROM app.brands WHERE brand_name='Tropicana'), (SELECT category_id FROM app.categories WHERE category_name='Beverages'), 45, 191, 0.1, 0, 10, 8.9, 0.3, 0.7, 0.01, 0, 'C', 5, 3, 'B', 'France', '100% pure squeezed orange juice', 0.87, 'sample'),
('3256220200028', 'Innocent Smoothie Mangue', 'Mango & passion fruit smoothie', '750ml', (SELECT brand_id FROM app.brands WHERE brand_name='Innocent'), (SELECT category_id FROM app.categories WHERE category_name='Beverages'), 57, 243, 0.2, 0, 12.8, 12.2, 0.8, 0.5, 0.01, 0, 'C', 6, 3, 'B', 'France', 'Mango puree, apple juice, banana puree, orange juice, passion fruit juice', 0.82, 'sample'),

-- Bread & Bakery
('3256540001305', 'Baguette tradition', 'Traditional French baguette', '250g', NULL, (SELECT category_id FROM app.categories WHERE category_name='Bread & Bakery'), 265, 1121, 1.4, 0.3, 53, 2.5, 3, 9, 1.5, 0.6, 'A', -1, 3, 'A', 'France', 'Wheat flour, water, salt, yeast', 0.70, 'sample'),
('3175681007543', 'Pain de mie complet', 'Whole wheat bread', '500g', NULL, (SELECT category_id FROM app.categories WHERE category_name='Bread & Bakery'), 247, 1045, 3.5, 0.6, 42, 4.5, 6.5, 10, 1.1, 0.44, 'A', -2, 4, 'B', 'France', 'Whole wheat flour, water, sugar, yeast, salt, vegetable oil', 0.75, 'sample'),

-- Cheese
('3175681070349', 'President Camembert', 'Soft cheese', '250g', (SELECT brand_id FROM app.brands WHERE brand_name='President'), (SELECT category_id FROM app.categories WHERE category_name='Cheese'), 299, 1243, 24, 16, 0.5, 0.5, 0, 20, 1.4, 0.56, 'D', 17, 3, 'C', 'France', 'Pasteurized milk, salt, lactic ferments, rennet', 0.90, 'sample'),
('3033710065967', 'Saint Agur', 'Blue cheese', '125g', (SELECT brand_id FROM app.brands WHERE brand_name='Saint Agur'), (SELECT category_id FROM app.categories WHERE category_name='Cheese'), 353, 1464, 31, 22, 1, 0.5, 0, 17, 2.5, 1.0, 'D', 18, 3, 'D', 'France', 'Pasteurized cow milk, salt, Penicillium roqueforti, rennet', 0.85, 'sample'),
('3073780969000', 'Comte AOP 12 mois', 'Aged Comte cheese', '200g', NULL, (SELECT category_id FROM app.categories WHERE category_name='Cheese'), 411, 1710, 34, 22, 0.5, 0.5, 0, 27, 0.8, 0.32, 'D', 15, 1, 'A', 'France', 'Raw cow milk, salt, rennet, lactic ferments', 0.82, 'sample'),

-- Meat & Poultry
('3266980011024', 'Charal Steak Hache 5%', 'Lean ground beef 5% fat', '2x125g', (SELECT brand_id FROM app.brands WHERE brand_name='Charal'), (SELECT category_id FROM app.categories WHERE category_name='Meat & Poultry'), 137, 574, 5, 2.3, 0.5, 0, 0, 22, 0.65, 0.26, 'A', -5, 3, 'C', 'France', '100% pure beef', 0.88, 'sample'),
('3302740059308', 'Fleury Michon Jambon Blanc', 'Cooked ham', '4 tranches', (SELECT brand_id FROM app.brands WHERE brand_name='Fleury Michon'), (SELECT category_id FROM app.categories WHERE category_name='Meat & Poultry'), 112, 471, 3, 1.1, 1.2, 1.0, 0, 19, 1.8, 0.72, 'B', 0, 4, 'C', 'France', 'Pork ham, water, salt, dextrose, sodium nitrite, antioxidant', 0.85, 'sample'),
('3095750011107', 'Poulet fermier entier', 'Free-range whole chicken', '1.3kg', NULL, (SELECT category_id FROM app.categories WHERE category_name='Meat & Poultry'), 170, 714, 9.5, 2.8, 0, 0, 0, 21, 0.3, 0.12, 'A', -6, 1, 'B', 'France', 'Free-range chicken', 0.70, 'sample'),

-- Pasta & Rice
('8076802085738', 'Barilla Spaghetti n.5', 'Spaghetti', '500g', (SELECT brand_id FROM app.brands WHERE brand_name='Barilla'), (SELECT category_id FROM app.categories WHERE category_name='Pasta & Rice'), 359, 1523, 1.5, 0.5, 71, 3.5, 3, 13, 0.01, 0, 'A', -3, 3, 'A', 'France,Italy', 'Durum wheat semolina, water', 0.92, 'sample'),
('8076802085905', 'Barilla Penne Rigate', 'Penne pasta', '500g', (SELECT brand_id FROM app.brands WHERE brand_name='Barilla'), (SELECT category_id FROM app.categories WHERE category_name='Pasta & Rice'), 359, 1523, 1.5, 0.5, 71, 3.5, 3, 13, 0.01, 0, 'A', -3, 3, 'A', 'France,Italy', 'Durum wheat semolina, water', 0.91, 'sample'),
('3175681070356', 'Panzani Coquillettes', 'Elbow pasta', '500g', (SELECT brand_id FROM app.brands WHERE brand_name='Panzani'), (SELECT category_id FROM app.categories WHERE category_name='Pasta & Rice'), 350, 1485, 1.5, 0.3, 71, 3, 3, 12, 0.01, 0, 'A', -3, 3, 'A', 'France', 'Durum wheat semolina', 0.88, 'sample'),
('3033710085903', 'Riz Basmati', 'Basmati rice', '1kg', NULL, (SELECT category_id FROM app.categories WHERE category_name='Pasta & Rice'), 354, 1502, 0.6, 0.2, 78, 0.5, 1.5, 7.5, 0.01, 0, 'A', -4, 1, 'A', 'France', 'Basmati rice', 0.80, 'sample'),

-- Sauces & Condiments
('87157277', 'Heinz Tomato Ketchup', 'Tomato ketchup', '570g', (SELECT brand_id FROM app.brands WHERE brand_name='Heinz'), (SELECT category_id FROM app.categories WHERE category_name='Sauces & Condiments'), 101, 429, 0.1, 0, 23.7, 22.8, 0.8, 1.2, 2.3, 0.92, 'C', 5, 4, 'D', 'France', 'Tomatoes (148g per 100g ketchup), spirit vinegar, sugar, salt, spice and herb extracts, spice', 0.90, 'sample'),
('3250390004677', 'Amora Moutarde de Dijon', 'Dijon mustard', '440g', (SELECT brand_id FROM app.brands WHERE brand_name='Amora'), (SELECT category_id FROM app.categories WHERE category_name='Sauces & Condiments'), 151, 627, 9.9, 0.6, 4.2, 3.2, 3.5, 9.5, 6.3, 2.52, 'C', 9, 4, 'C', 'France', 'Water, mustard seeds, spirit vinegar, salt, citric acid, potassium metabisulphite', 0.87, 'sample'),

-- Biscuits & Cookies
('7622210449115', 'Lu Petit Beurre', 'Butter biscuits', '200g', (SELECT brand_id FROM app.brands WHERE brand_name='Lu'), (SELECT category_id FROM app.categories WHERE category_name='Biscuits & Cookies'), 436, 1837, 11, 6, 76, 20, 2.5, 7.5, 0.95, 0.38, 'D', 14, 4, 'C', 'France', 'Wheat flour, sugar, butter (21%), salt, raising agents, milk powder, barley malt extract', 0.92, 'sample'),
('3268840001039', 'Bjorg Petits Fourres Chocolat', 'Organic chocolate filled biscuits', '180g', (SELECT brand_id FROM app.brands WHERE brand_name='Bjorg'), (SELECT category_id FROM app.categories WHERE category_name='Biscuits & Cookies'), 478, 2003, 20, 10, 66, 29, 3.5, 7, 0.55, 0.22, 'D', 16, 4, 'C', 'France', 'Wheat flour, chocolate filling (30%), sugar, palm oil, hazelnuts', 0.78, 'sample'),
('3017760000017', 'Bonne Maman Tartelettes Chocolat', 'Chocolate tartlets', '135g', (SELECT brand_id FROM app.brands WHERE brand_name='Bonne Maman'), (SELECT category_id FROM app.categories WHERE category_name='Biscuits & Cookies'), 500, 2093, 26, 14, 59, 33, 3.5, 6.5, 0.45, 0.18, 'D', 17, 4, 'D', 'France', 'Wheat flour, chocolate (26%), butter, sugar, eggs, cocoa powder', 0.85, 'sample'),
('7622210713803', 'Michel et Augustin Cookies', 'Chocolate chip cookies', '150g', (SELECT brand_id FROM app.brands WHERE brand_name='Michel et Augustin'), (SELECT category_id FROM app.categories WHERE category_name='Biscuits & Cookies'), 495, 2072, 25, 15, 59, 30, 3, 6, 0.75, 0.30, 'D', 16, 4, 'C', 'France', 'Wheat flour, dark chocolate chips (25%), butter (22%), sugar, eggs, salt, vanilla extract', 0.80, 'sample'),

-- Frozen meals
('3242272340225', 'Fleury Michon Poulet Basquaise', 'Chicken Basquaise with rice', '300g', (SELECT brand_id FROM app.brands WHERE brand_name='Fleury Michon'), (SELECT category_id FROM app.categories WHERE category_name='Frozen meals'), 110, 462, 2.5, 0.5, 15, 2.5, 1.5, 7, 0.75, 0.30, 'A', -1, 4, 'C', 'France', 'Rice, chicken (25%), tomatoes, peppers, onions, olive oil, spices', 0.82, 'sample'),
('3242272340188', 'Fleury Michon Saumon et Riz', 'Salmon with rice and vegetables', '300g', (SELECT brand_id FROM app.brands WHERE brand_name='Fleury Michon'), (SELECT category_id FROM app.categories WHERE category_name='Frozen meals'), 120, 504, 3.5, 0.8, 14, 1.5, 1, 8, 0.65, 0.26, 'A', -2, 4, 'C', 'France', 'Rice, salmon (22%), cream, broccoli, carrots, dill', 0.80, 'sample'),

-- Spreads
('3045320001525', 'Bonne Maman Confiture Fraises', 'Strawberry jam', '370g', (SELECT brand_id FROM app.brands WHERE brand_name='Bonne Maman'), (SELECT category_id FROM app.categories WHERE category_name='Spreads'), 252, 1071, 0.1, 0, 62, 60, 1.2, 0.4, 0.03, 0.01, 'D', 17, 3, 'C', 'France', 'Strawberries, sugar, cane sugar, concentrated lemon juice, gelling agent: fruit pectin', 0.90, 'sample'),
('3045320001549', 'Bonne Maman Confiture Abricots', 'Apricot jam', '370g', (SELECT brand_id FROM app.brands WHERE brand_name='Bonne Maman'), (SELECT category_id FROM app.categories WHERE category_name='Spreads'), 248, 1053, 0.1, 0, 61, 58, 1, 0.5, 0.03, 0.01, 'D', 16, 3, 'C', 'France', 'Apricots, sugar, cane sugar, concentrated lemon juice, gelling agent: fruit pectin', 0.88, 'sample'),

-- Dairy
('3033490003975', 'Danone Danette Chocolat', 'Chocolate dessert cream', '4x125g', (SELECT brand_id FROM app.brands WHERE brand_name='Danone'), (SELECT category_id FROM app.categories WHERE category_name='Dairy'), 141, 594, 3.8, 2.5, 22.2, 20.5, 0.9, 3.7, 0.18, 0.07, 'D', 12, 4, 'C', 'France', 'Skimmed milk, sugar, cream, chocolate powder (3.5%), modified starch, thickeners', 0.88, 'sample'),
('3033490003999', 'Danone Danette Vanille', 'Vanilla dessert cream', '4x125g', (SELECT brand_id FROM app.brands WHERE brand_name='Danone'), (SELECT category_id FROM app.categories WHERE category_name='Dairy'), 126, 531, 3.3, 2.2, 19.5, 18, 0, 3.2, 0.15, 0.06, 'D', 11, 4, 'C', 'France', 'Skimmed milk, sugar, cream, modified starch, vanilla extract, thickeners', 0.86, 'sample'),

-- Fruits & Vegetables
('3083680085304', 'Bonduelle Mais Doux', 'Sweet corn', '285g', (SELECT brand_id FROM app.brands WHERE brand_name='Bonduelle'), (SELECT category_id FROM app.categories WHERE category_name='Fruits & Vegetables'), 80, 339, 1.2, 0.2, 12.5, 6.5, 2.5, 2.8, 0.45, 0.18, 'A', -2, 3, 'A', 'France', 'Sweet corn, water, salt', 0.85, 'sample'),
('3083680085502', 'Bonduelle Petits Pois', 'Garden peas', '400g', (SELECT brand_id FROM app.brands WHERE brand_name='Bonduelle'), (SELECT category_id FROM app.categories WHERE category_name='Fruits & Vegetables'), 68, 289, 0.5, 0.1, 8.5, 4, 5.5, 5.2, 0.55, 0.22, 'A', -4, 3, 'A', 'France', 'Garden peas, water, salt, sugar', 0.83, 'sample'),
('3083680085601', 'Bonduelle Haricots Verts', 'Green beans', '400g', (SELECT brand_id FROM app.brands WHERE brand_name='Bonduelle'), (SELECT category_id FROM app.categories WHERE category_name='Fruits & Vegetables'), 22, 95, 0.1, 0, 2.8, 1.2, 2.5, 1.5, 0.55, 0.22, 'A', -7, 3, 'A', 'France', 'Green beans, water, salt', 0.82, 'sample'),

-- More products for variety
('8000500310427', 'Barilla Pesto alla Genovese', 'Basil pesto sauce', '190g', (SELECT brand_id FROM app.brands WHERE brand_name='Barilla'), (SELECT category_id FROM app.categories WHERE category_name='Sauces & Condiments'), 352, 1460, 33, 6.5, 5.5, 4.5, 1.5, 5, 2.8, 1.12, 'D', 13, 4, 'C', 'France,Italy', 'Sunflower oil, basil (35%), cashew nuts, Grana Padano cheese, salt, garlic, pine nuts, sugar', 0.88, 'sample'),
('3560071097523', 'Carte Noire Cafe', 'Ground coffee', '250g', (SELECT brand_id FROM app.brands WHERE brand_name='Carte Noire'), (SELECT category_id FROM app.categories WHERE category_name='Beverages'), 2, 8, 0, 0, 0, 0, 0, 0.1, 0, 0, 'A', -15, 1, 'A', 'France', '100% arabica coffee', 0.75, 'sample'),

-- Ice cream
('3415581100327', 'Haagen-Dazs Vanilla', 'Vanilla ice cream', '460ml', (SELECT brand_id FROM app.brands WHERE brand_name='Haagen-Dazs'), (SELECT category_id FROM app.categories WHERE category_name='Dairy'), 250, 1043, 16, 10, 23, 22, 0, 4, 0.12, 0.05, 'D', 15, 4, 'D', 'France', 'Cream, skimmed milk, sugar, egg yolk, vanilla extract', 0.85, 'sample'),
('3415581100402', 'Haagen-Dazs Macadamia Nut', 'Macadamia nut ice cream', '460ml', (SELECT brand_id FROM app.brands WHERE brand_name='Haagen-Dazs'), (SELECT category_id FROM app.categories WHERE category_name='Dairy'), 280, 1167, 19, 10, 23, 21, 0.5, 4.5, 0.15, 0.06, 'D', 16, 4, 'D', 'France', 'Cream, skimmed milk, sugar, macadamia nuts (8%), egg yolk, caramel', 0.82, 'sample')

ON CONFLICT (barcode) DO NOTHING;

-- =============================================================
-- NUTRITIONAL GUIDELINES (from scraping)
-- =============================================================
INSERT INTO app.nutritional_guidelines (nutrient_name, daily_value, unit, age_group, gender, source_url, source_name) VALUES
('Energy', 2000, 'kcal', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Total fat', 70, 'g', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Saturated fat', 20, 'g', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Carbohydrates', 260, 'g', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Sugars', 90, 'g', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Protein', 50, 'g', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Salt', 6, 'g', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Fiber', 25, 'g', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Potassium', 2000, 'mg', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Calcium', 800, 'mg', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Iron', 14, 'mg', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Vitamin C', 80, 'mg', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Vitamin D', 5, 'ug', 'Adult', 'All', 'https://eur-lex.europa.eu/eli/reg/2011/1169', 'EU Regulation 1169/2011'),
('Sodium', 2400, 'mg', 'Adult', 'All', 'https://www.anses.fr', 'ANSES'),
('Magnesium', 375, 'mg', 'Adult', 'All', 'https://www.anses.fr', 'ANSES'),
('Zinc', 10, 'mg', 'Adult', 'All', 'https://www.anses.fr', 'ANSES')
ON CONFLICT DO NOTHING;

-- Final count
SELECT 'Products loaded: ' || COUNT(*) FROM app.products;
SELECT 'Brands loaded: ' || COUNT(*) FROM app.brands;
SELECT 'Categories loaded: ' || COUNT(*) FROM app.categories;
SELECT 'Guidelines loaded: ' || COUNT(*) FROM app.nutritional_guidelines;
