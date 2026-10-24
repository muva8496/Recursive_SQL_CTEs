import sqlite3
import pandas as pd
import os

# Ensure output directory exists
os.makedirs("output", exist_ok=True)
os.makedirs("data", exist_ok=True)

db_path = "data/retail_hierarchy.db"

# 1. Connect to SQLite (creates the database file automatically)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 2. Create a hierarchical table for retail product categories
cursor.execute("""
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL,
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id)
);
""")

# Clear existing data to keep it clean on re-runs
cursor.execute("DELETE FROM categories;")

# 3. Insert multi-level hierarchical sample data
sample_data = [
    (1, "All Retail Stock", None),          # Level 1: Root
    (2, "Dry Foods & Groceries", 1),        # Level 2: Department
    (3, "Beverages", 1),                    # Level 2: Department
    (4, "Bakery", 2),                       # Level 3: Sub-category
    (5, "Cereals & Grains", 2),             # Level 3: Sub-category
    (6, "Soda & Juices", 3),                # Level 3: Sub-category
    (7, "Loaf Bread", 4),                   # Level 4: Item Type
    (8, "Buns & Rolls", 4),                 # Level 4: Item Type
    (9, "Maize Meal (2kg)", 5)              # Level 4: Item Type
]

cursor.executemany("INSERT INTO categories (category_id, category_name, parent_id) VALUES (?, ?, ?);", sample_data)
conn.commit()

print("Database and hierarchical table successfully built and populated!")

# 4. Write and Execute the Recursive SQL Query (WITH RECURSIVE CTE)
recursive_query = """
WITH RECURSIVE category_path AS (
    -- Anchor Member: Select the root node (Level 1)
    SELECT 
        category_id, 
        category_name, 
        parent_id, 
        1 AS level, 
        CAST(category_name AS TEXT) AS path
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    -- Recursive Member: Join child records back to the CTE path
    SELECT 
        c.category_id, 
        c.category_name, 
        c.parent_id, 
        cp.level + 1, 
        cp.path || ' -> ' || c.category_name
    FROM categories c
    JOIN category_path cp ON c.parent_id = cp.category_id
)
SELECT level, category_id, category_name, path 
FROM category_path
ORDER BY path;
"""

# Execute query and load into Pandas for clean display and CSV export
df_result = pd.read_sql_query(recursive_query, conn)

print("\n--- Recursive Query Execution Results ---")
print(df_result.to_string(index=False))

# Save output log as requested by your execution protocol
output_file = "output/recursive_query_tree.csv"
df_result.to_csv(output_file, index=False)
print(f"\nTree logs successfully committed to {output_file}")

# Close connection
conn.close()