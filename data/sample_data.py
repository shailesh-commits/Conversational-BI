"""
Sample data generator for Conversational BI Demo.
Creates SQLite database with realistic P&L data.
"""

import sqlite3
import random
from datetime import datetime, timedelta
import pandas as pd

def create_database(db_path="./data/sales_data.db"):
    """Create and seed SQLite database with sample data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS sales")
    cursor.execute("DROP TABLE IF EXISTS regional_targets")
    cursor.execute("DROP TABLE IF EXISTS product_master")
    
    # Create product_master table
    cursor.execute("""
    CREATE TABLE product_master (
        category_code TEXT PRIMARY KEY,
        category_name TEXT NOT NULL,
        category_tier TEXT NOT NULL,
        standard_margin_pct REAL NOT NULL
    )
    """)
    
    # Insert product data
    products = [
        ('Widgets-A', 'Premium Widget A', 'Premium', 72.0),
        ('Widgets-B', 'Premium Widget B', 'Premium', 70.0),
        ('Widgets-C', 'Premium Widget C', 'Premium', 68.0),
        ('Widgets-D', 'Standard Widget D', 'Standard', 55.0),
        ('Widgets-E', 'Standard Widget E', 'Standard', 52.0),
        ('Widgets-F', 'Standard Widget F', 'Standard', 50.0),
        ('Widgets-G', 'Standard Widget G', 'Standard', 48.0),
        ('Widgets-H', 'Standard Widget H', 'Standard', 46.0),
        ('Widgets-I', 'Standard Widget I', 'Standard', 44.0),
        ('Widgets-J', 'Budget Widget J', 'Budget', 35.0),
        ('Widgets-K', 'Budget Widget K', 'Budget', 32.0),
        ('Widgets-L', 'Budget Widget L', 'Budget', 28.0),
    ]
    cursor.executemany("INSERT INTO product_master VALUES (?, ?, ?, ?)", products)
    
    # Create regional_targets table
    cursor.execute("""
    CREATE TABLE regional_targets (
        region TEXT NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        revenue_target REAL NOT NULL,
        margin_target REAL NOT NULL,
        PRIMARY KEY (region, year, month)
    )
    """)
    
    # Insert targets for 2025
    regions = ['North America', 'Europe', 'APAC', 'Latin America', 'Africa']
    region_targets = {
        'North America': {'revenue': 2500000, 'margin': 48},
        'Europe': {'revenue': 1800000, 'margin': 62},
        'APAC': {'revenue': 1200000, 'margin': 38},
        'Latin America': {'revenue': 500000, 'margin': 50},
        'Africa': {'revenue': 250000, 'margin': 46}
    }
    
    for region in regions:
        for month in range(1, 13):
            revenue = region_targets[region]['revenue'] + random.randint(-200000, 200000)
            margin = region_targets[region]['margin'] + random.uniform(-3, 3)
            cursor.execute(
                "INSERT INTO regional_targets VALUES (?, ?, ?, ?, ?)",
                (region, 2025, month, revenue, margin)
            )
    
    # Create sales table
    cursor.execute("""
    CREATE TABLE sales (
        transaction_id INTEGER PRIMARY KEY,
        date DATE NOT NULL,
        region TEXT NOT NULL,
        product_category TEXT NOT NULL,
        units_sold INTEGER NOT NULL,
        revenue REAL NOT NULL,
        cost_of_goods_sold REAL NOT NULL,
        gross_margin_pct REAL NOT NULL,
        FOREIGN KEY (product_category) REFERENCES product_master(category_code),
        FOREIGN KEY (region) REFERENCES regional_targets(region)
    )
    """)
    
    # Generate sales data: 6 months (Jan - Jun 2025)
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 6, 30)
    
    region_weights = {
        'North America': 0.40,
        'Europe': 0.25,
        'APAC': 0.20,
        'Latin America': 0.10,
        'Africa': 0.05
    }
    
    product_weights = {
        'Widgets-A': 0.08, 'Widgets-B': 0.08, 'Widgets-C': 0.07,  # Premium
        'Widgets-D': 0.12, 'Widgets-E': 0.12, 'Widgets-F': 0.11, 'Widgets-G': 0.10, 'Widgets-H': 0.10, 'Widgets-I': 0.09,  # Standard
        'Widgets-J': 0.06, 'Widgets-K': 0.06, 'Widgets-L': 0.04,  # Budget
    }
    
    transaction_id = 1001
    current_date = start_date
    daily_transaction_count = 1500
    
    while current_date <= end_date:
        # Seasonal variation: Apr-Jun +10-15% boost
        seasonal_boost = 1.12 if current_date.month >= 4 else 1.0
        
        # Generate transactions for the day
        for _ in range(daily_transaction_count):
            region = random.choices(regions, weights=[region_weights[r] for r in regions])[0]
            product = random.choices(list(product_weights.keys()), weights=list(product_weights.values()))[0]
            
            # Base transaction size varies by product tier
            if 'A' in product or 'B' in product or 'C' in product:  # Premium
                units = random.randint(20, 150)
                base_price = 500
            elif product in ['J', 'K', 'L']:  # Budget
                units = random.randint(100, 500)
                base_price = 200
            else:  # Standard
                units = random.randint(50, 300)
                base_price = 400
            
            revenue = units * base_price * seasonal_boost * random.uniform(0.95, 1.05)
            
            # Get standard margin and apply variation
            cursor.execute("SELECT standard_margin_pct FROM product_master WHERE category_code = ?", (product,))
            standard_margin = cursor.fetchone()[0]
            gross_margin_pct = standard_margin + random.uniform(-5, 5)
            gross_margin_pct = max(15, min(80, gross_margin_pct))  # Clamp between 15-80
            
            cogs = revenue * (100 - gross_margin_pct) / 100
            
            cursor.execute(
                "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (transaction_id, current_date.strftime('%Y-%m-%d'), region, product, 
                 int(units), round(revenue, 2), round(cogs, 2), round(gross_margin_pct, 2))
            )
            transaction_id += 1
        
        current_date += timedelta(days=1)
    
    conn.commit()
    conn.close()
    print(f"✓ Database created at {db_path}")
    print(f"✓ Generated {transaction_id - 1001} sales transactions")
    print(f"✓ Coverage: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    create_database()
