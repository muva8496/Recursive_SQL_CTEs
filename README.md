# Retail Hierarchy & Recursive SQL Pipeline

A robust data engineering project implementing hierarchical data modeling, recursive Common Table Expressions (CTEs), and automated inventory stock health analytics using Python and SQLite.

---

## 📋 Table of Contents
1. [Overview & Problem Statement](#overview--problem-statement)
2. [Architectural Concept: Why Recursive SQL?](#architectural-concept-why-recursive-sql)
3. [Database Schema Design](#database-schema-design)
4. [Core Implementation: The Recursive CTE](#core-implementation-the-recursive-cte)
5. [Project Directory Structure](#project-directory-structure)
6. [Prerequisites & Environment Setup](#prerequisites--environment-setup)
7. [Execution Guide](#execution-guide)
8. [Analytical Output & Stock Health Metrics](#analytical-output--stock-health-metrics)
9. [Future Roadmap](#future-roadmap)

---

## 1. Overview & Problem Statement

In standard relational database design, flat tables are sufficient for independent entities. However, retail inventory management naturally forms **hierarchical trees** (e.g., Root Department $\rightarrow$ Sub-category $\rightarrow$ Product Line $\rightarrow$ Specific SKU). 

Standard SQL queries cannot easily traverse multi-level parent-child relationships dynamically without hardcoding complex joins. This project solves that limitation by leveraging **Recursive SQL CTEs (`WITH RECURSIVE`)** to automatically calculate lineage strings, map multi-tier roll-ups, and evaluate real-time inventory health (identifying understocked bottlenecks and overstocked capital traps).

---

## 2. Architectural Concept: Why Recursive SQL?

Traditional queries stop at a single table level. A recursive CTE operates in two distinct phases:
* **The Anchor Member:** Isolates the root node (e.g., `All Retail Stock` where `parent_id IS NULL`) as the absolute starting point of the loop.
* **The Recursive Member:** Joins child records back to the working CTE table iteratively, appending breadcrumb paths (using string concatenation `||`) and descending deeper into the tree until zero child records remain.

---

## 3. Database Schema Design

The project uses an embedded SQLite database (`retail_hierarchy.db`) featuring two core relational tables:

### `categories` (Hierarchical Adjacency List)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `category_id` | INTEGER | PRIMARY KEY | Unique identifier for the category/node |
| `category_name` | TEXT | NOT NULL | Name of the department, sub-category, or item group |
| `category_id` | INTEGER | FOREIGN KEY | Self-referencing pointer linking a child to its parent node |

### `store_inventory` (Transactional / Operational Stock Data)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `item_id` | INTEGER | PRIMARY KEY | Unique identifier for the specific stock SKU |
| `category_id` | INTEGER | FOREIGN KEY | Maps the item to its leaf category |
| `item_name` | TEXT | NOT NULL | Description of the retail item |
| `units_sold` | INTEGER | DEFAULT 0 | Total sales velocity metric |
| `current_stock` | INTEGER | DEFAULT 0 | Real-time physical count on shelves |
| `max_capacity` | INTEGER | DEFAULT 0 | Maximum storage threshold for the item |

---

## 4. Core Implementation: The Recursive CTE

The core engine of the script executes the following SQL logic to traverse the taxonomy:

```sql
WITH RECURSIVE category_path AS (
    -- 1. Anchor Member: Root Node
    SELECT 
        category_id, 
        category_name, 
        parent_id, 
        1 AS level, 
        CAST(category_name AS TEXT) AS path
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    -- 2. Recursive Member: Iterative Child Traversal
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
ORDER BY path;"# Recursive_SQL_CTEs" 
