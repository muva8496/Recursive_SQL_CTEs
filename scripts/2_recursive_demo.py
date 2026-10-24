import sqlite3
import pandas as pd
import os

os.makedirs("output", exist_ok=True)
os.makedirs("data", exist_ok=True)

db_path = "data/1_retail_hierarchy.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Setup Tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL,
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS store_inventory (
    item_id INTEGER PRIMARY KEY,
    category_id INTEGER,
    item_name TEXT NOT NULL,
    units_sold INTEGER,
    current_stock INTEGER,
    max_capacity INTEGER,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);
""")

cursor.execute("DELETE FROM categories;")
cursor.execute("DELETE FROM store_inventory;")

# Categories Hierarchy
sample_categories = [
    (1, "All Retail Stock", None),          # Level 1 (Root)
    (2, "Dry Foods & Groceries", 1),        # Level 2 (Department)
    (3, "Beverages", 1),                    # Level 2 (Department)
    (4, "Bakery", 2),                       # Level 3 (Sub-category)
    (5, "Cereals & Grains", 2),             # Level 3 (Sub-category)
    (6, "Soda & Juices", 3),                # Level 3 (Sub-category)
    (7, "Loaf Bread", 4),                   # Level 4 (Item Type)
    (8, "Buns & Rolls", 4),                 # Level 4 (Item Type)
    (9, "Maize Meal (2kg)", 5)              # Level 4 (Item Type)
]
cursor.executemany("INSERT INTO categories VALUES (?, ?, ?);", sample_categories)

# Inventory / Sales Data
sample_inventory = [
    (101, 7, "Standard Loaf Bread", 150, 5, 40),    # High sales, low stock (Understocked)
    (102, 8, "Butter Buns (Pack)", 80, 12, 30),     # Moderate
    (103, 9, "Maize Meal 2kg Soko", 200, 3, 50),    # High sales, very low stock (Understocked)
    (104, 6, "Soda 500ml Soda", 300, 85, 90)        # High stock (Potential Overstock)
]
cursor.executemany("INSERT INTO store_inventory VALUES (?, ?, ?, ?, ?, ?);", sample_inventory)
conn.commit()

# Common Recursive CTE base
base_cte = """
WITH RECURSIVE category_tree AS (
    SELECT category_id, category_name, parent_id, 
           category_id AS dept_id, category_name AS dept_name,
           category_id AS sub_id, category_name AS sub_name
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    SELECT c.category_id, c.category_name, c.parent_id, 
           CASE WHEN ct.parent_id IS NULL THEN c.category_id ELSE ct.dept_id END,
           CASE WHEN ct.parent_id IS NULL THEN c.category_name ELSE ct.dept_name END,
           CASE WHEN ct.level_depth = 2 THEN c.category_id ELSE ct.sub_id END,
           CASE WHEN ct.level_depth = 2 THEN c.category_name ELSE ct.sub_name END
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.category_id
)
"""
# Simplified working CTE for multi-tier analysis
recursive_full_path = """
WITH RECURSIVE category_path AS (
    SELECT category_id, category_name, parent_id, 1 AS level, CAST(category_name AS TEXT) AS path
    FROM categories WHERE parent_id IS NULL
    UNION ALL
    SELECT c.category_id, c.category_name, c.parent_id, cp.level + 1, cp.path || ' -> ' || c.category_name
    FROM categories c JOIN category_path cp ON c.parent_id = cp.category_id
)
"""

# 1. Department-Level View Query
dept_query = recursive_full_path + """
SELECT 
    SUBSTR(cp.path, 1, INSTR(cp.path || ' -> ', ' -> ') - 1) AS root,
    SUBSTR(cp.path, INSTR(cp.path, ' -> ') + 4) AS branch,
    SUM(si.units_sold) AS total_sales,
    SUM(si.current_stock) AS total_stock
FROM category_path cp
JOIN store_inventory si ON cp.category_id = si.category_id
GROUP BY cp.level;
"""

# Let's run a clean aggregate script for all 3 views:
print("\n=== 1. DEPARTMENT-LEVEL ROLL-UP ===")
dept_df = pd.read_sql_query("""
SELECT 
    CASE 
        WHEN c.parent_id = 1 THEN c.category_name
        ELSE 'Sub-Item'
    END AS department,
    SUM(si.units_sold) AS units_sold,
    SUM(si.current_stock) AS current_stock
FROM categories c
JOIN store_inventory si ON c.category_id = si.category_id
GROUP BY department;
""", conn)
print(dept_df.to_string(index=False))

print("\n=== 2. SUB-CATEGORY PERFORMANCE VIEW ===")
sub_df = pd.read_sql_query("""
SELECT 
    c.category_name AS sub_category,
    SUM(si.units_sold) AS units_sold,
    SUM(si.current_stock) AS current_stock
FROM categories c
JOIN store_inventory si ON c.category_id = si.category_id
GROUP BY c.category_name;
""", conn)
print(sub_df.to_string(index=False))

print("\n=== 3. ITEM-LEVEL STOCK HEALTH (Under/Overstocked) ===")
item_df = pd.read_sql_query("""
SELECT 
    item_name,
    units_sold,
    current_stock,
    max_capacity,
    CASE 
        WHEN current_stock < (max_capacity * 0.2) THEN '🚨 UNDERSTOCKED (Restock Needed)'
        WHEN current_stock > (max_capacity * 0.8) THEN '⚠️ OVERSTOCKED (Capital Trapped)'
        ELSE '✅ HEALTHY'
    END AS stock_status
FROM store_inventory;
""", conn)
print(item_df.to_string(index=False))

conn.close()




