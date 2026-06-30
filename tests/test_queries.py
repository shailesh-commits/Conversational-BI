"""
Test queries for Conversational BI Assistant.
These are sample questions used during demos and training.
"""

import json

TEST_QUERIES = [
    {
        "question": "What was our total revenue by region last month?",
        "expected_pattern": ["SELECT", "region", "SUM(revenue)", "WHERE", "GROUP BY"],
        "description": "Simple aggregation and grouping"
    },
    {
        "question": "Show me the trend in Widgets-A sales over the last 6 months.",
        "expected_pattern": ["SELECT", "product_category", "date", "SUM(revenue)"],
        "description": "Time series analysis"
    },
    {
        "question": "Which regions have gross margins above 50%?",
        "expected_pattern": ["SELECT", "region", "HAVING", "gross_margin_pct", ">", "50"],
        "description": "Filtering with aggregation"
    },
    {
        "question": "Compare North America and Europe Premium product margins.",
        "expected_pattern": ["JOIN", "product_master", "category_tier", "Premium"],
        "description": "Multi-table join with filtering"
    },
    {
        "question": "Are we on track to hit annual targets by region?",
        "expected_pattern": ["regional_targets", "region", "revenue"],
        "description": "Target comparison"
    },
    {
        "question": "Which products are underperforming in APAC?",
        "expected_pattern": ["APAC", "product_category", "gross_margin_pct"],
        "description": "Ranking and filtering"
    },
    {
        "question": "Show me revenue trends by region for the last 6 months.",
        "expected_pattern": ["SELECT", "region", "date", "SUM(revenue)", "GROUP BY"],
        "description": "Multi-dimensional time series"
    },
    {
        "question": "What is the average margin by product category?",
        "expected_pattern": ["SELECT", "product_category", "AVG(gross_margin_pct)"],
        "description": "Basic aggregation"
    },
    {
        "question": "Which product category generated the most revenue in 2025?",
        "expected_pattern": ["product_category", "SUM(revenue)", "ORDER BY", "DESC", "LIMIT"],
        "description": "Top-N query"
    },
    {
        "question": "Show me APAC sales trends by month and product line.",
        "expected_pattern": ["APAC", "date", "product_category", "SUM(revenue)"],
        "description": "Multi-dimensional breakdown"
    }
]

def export_test_queries(filepath="test_queries.json"):
    """Export test queries to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(TEST_QUERIES, f, indent=2)
    print(f"✓ Test queries exported to {filepath}")

if __name__ == "__main__":
    export_test_queries()
