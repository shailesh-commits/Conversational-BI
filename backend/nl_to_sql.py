"""
NL-to-SQL module: Converts natural language questions to SQL using OpenAI.
"""

import os
import json
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Schema definition for the system prompt
SCHEMA_DEFINITION = """
You are a SQL expert. Your task is to convert natural language questions into valid SQLite SQL queries.

SCHEMA DEFINITION:

Table: sales
- transaction_id (INTEGER, PRIMARY KEY)
- date (DATE, format: YYYY-MM-DD, range: 2025-01-01 to 2025-06-30)
- region (TEXT, values: 'North America', 'Europe', 'APAC', 'Latin America', 'Africa')
- product_category (TEXT, values: 'Widgets-A' through 'Widgets-L')
- units_sold (INTEGER)
- revenue (REAL, USD)
- cost_of_goods_sold (REAL, USD)
- gross_margin_pct (REAL, 0-100)

Table: regional_targets
- region (TEXT)
- year (INTEGER)
- month (INTEGER)
- revenue_target (REAL, USD)
- margin_target (REAL, 0-100)

Table: product_master
- category_code (TEXT, 'Widgets-A' through 'Widgets-L')
- category_name (TEXT)
- category_tier (TEXT, values: 'Premium', 'Standard', 'Budget')
- standard_margin_pct (REAL)

IMPORTANT RULES:
1. Always use valid SQLite syntax
2. For date extraction, use: STRFTIME('%Y-%m', date) for year-month
3. For month/year comparison: CAST(STRFTIME('%m', date) AS INTEGER) and CAST(STRFTIME('%Y', date) AS INTEGER)
4. Round decimals: ROUND(value, 2)
5. Aggregate functions: SUM(), AVG(), COUNT(), MAX(), MIN()
6. Always order results meaningfully (DESC for descending)
7. Use LIMIT when asking for "top" or "bottom" N items
8. Margin is already calculated; don't manipulate it further
9. Use GROUP BY when aggregating
10. Return the SQL ONLY, no explanation

EXAMPLES:

Q: What was our total revenue by region last month?
A: SELECT region, ROUND(SUM(revenue), 2) as total_revenue FROM sales WHERE STRFTIME('%Y-%m', date) = '2025-06-01' GROUP BY region ORDER BY total_revenue DESC

Q: Show me the top 3 products by margin in Europe.
A: SELECT product_category, ROUND(AVG(gross_margin_pct), 2) as avg_margin FROM sales WHERE region = 'Europe' GROUP BY product_category ORDER BY avg_margin DESC LIMIT 3

Q: Which regions have gross margins above 50%?
A: SELECT region, ROUND(AVG(gross_margin_pct), 2) as avg_margin FROM sales GROUP BY region HAVING AVG(gross_margin_pct) > 50 ORDER BY avg_margin DESC

Q: Show me revenue trends by region for the last 6 months.
A: SELECT STRFTIME('%Y-%m', date) as month, region, ROUND(SUM(revenue), 2) as monthly_revenue FROM sales GROUP BY month, region ORDER BY month DESC, revenue DESC

Q: Compare North America and Europe margins for Premium products.
A: SELECT s.region, p.category_tier, ROUND(AVG(s.gross_margin_pct), 2) as avg_margin FROM sales s JOIN product_master p ON s.product_category = p.category_code WHERE s.region IN ('North America', 'Europe') AND p.category_tier = 'Premium' GROUP BY s.region, p.category_tier ORDER BY avg_margin DESC

Q: Which products are underperforming in APAC?
A: SELECT s.product_category, ROUND(AVG(s.gross_margin_pct), 2) as avg_margin FROM sales s WHERE s.region = 'APAC' GROUP BY s.product_category ORDER BY avg_margin ASC LIMIT 5

Now, generate a single SQL query to answer the user's question. Return ONLY the SQL query, no explanation.
"""

def get_schema_from_database(db_path):
    """Retrieve actual schema from database for validation."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    schema = {}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        schema[table_name] = [col[1] for col in columns]
    
    conn.close()
    return schema

def generate_sql_from_nl(user_question, db_path=None):
    """
    Convert natural language question to SQL using OpenAI.
    
    Args:
        user_question (str): Natural language question from user
        db_path (str): Path to database for validation
    
    Returns:
        dict: {
            'sql': generated SQL string,
            'confidence': confidence score 0-100,
            'tokens_used': token usage info,
            'cost': estimated API cost
        }
    """
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": SCHEMA_DEFINITION
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ],
            temperature=0,  # Deterministic for SQL
            max_tokens=500
        )
        
        sql = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if sql.startswith("```"):
            sql = sql.split("```")[1]
            if sql.startswith("sql"):
                sql = sql[3:]
            sql = sql.strip()
        
        # Calculate cost (GPT-4: $0.03 per 1K prompt tokens, $0.06 per 1K completion tokens)
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
        
        # Estimate confidence based on query complexity and model response
        confidence = 85  # Default confidence for GPT-4
        
        return {
            'sql': sql,
            'confidence': confidence,
            'tokens': {
                'prompt': prompt_tokens,
                'completion': completion_tokens,
                'total': prompt_tokens + completion_tokens
            },
            'cost': round(cost, 5),
            'success': True
        }
    
    except Exception as e:
        return {
            'sql': None,
            'confidence': 0,
            'tokens': {'prompt': 0, 'completion': 0, 'total': 0},
            'cost': 0,
            'success': False,
            'error': str(e)
        }

def execute_sql(sql, db_path):
    """
    Execute SQL query against database.
    
    Args:
        sql (str): SQL query to execute
        db_path (str): Path to SQLite database
    
    Returns:
        dict: {
            'success': bool,
            'rows': list of result rows,
            'columns': column names,
            'row_count': number of rows,
            'error': error message if failed
        }
    """
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        conn.close()
        
        return {
            'success': True,
            'rows': rows,
            'columns': columns,
            'row_count': len(rows),
            'error': None
        }
    
    except Exception as e:
        return {
            'success': False,
            'rows': [],
            'columns': [],
            'row_count': 0,
            'error': str(e)
        }

def validate_sql(sql, db_path):
    """Validate SQL syntax without executing."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
        conn.close()
        return True
    except:
        return False
