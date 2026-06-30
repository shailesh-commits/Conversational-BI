"""
Flask backend for Conversational BI Assistant.
Handles NL-to-SQL, execution, visualization, and narrative generation.
"""

import os
import json
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import sqlite3
from datetime import datetime

from nl_to_sql import generate_sql_from_nl, execute_sql, validate_sql
from chart_generator import generate_chart
from narrative_generator import generate_narrative

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / 'frontend'

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path='')
CORS(app)

DATABASE_PATH = os.getenv('DATABASE_PATH', './data/sales_data.db')

# Query cache to avoid duplicate API calls
query_cache = {}

def format_response(success, data=None, error=None):
    """Standard response format."""
    return {
        'success': success,
        'data': data,
        'error': error,
        'timestamp': datetime.now().isoformat()
    }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sales")
        count = cursor.fetchone()[0]
        conn.close()
        
        return format_response(True, {'database': 'connected', 'sales_records': count})
    except Exception as e:
        return format_response(False, error=f'Database connection failed: {str(e)}'), 500

@app.route('/schema', methods=['GET'])
def get_schema():
    """Retrieve database schema."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        schema = {}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            schema[table_name] = {
                'columns': [col[1] for col in columns],
                'types': [col[2] for col in columns]
            }
        
        conn.close()
        return format_response(True, {'schema': schema})
    
    except Exception as e:
        return format_response(False, error=str(e)), 500

@app.route('/query', methods=['POST'])
def process_query():
    """
    Main endpoint: Process natural language query.
    
    Request body:
    {
        'question': 'User natural language question',
        'use_cache': true/false (optional)
    }
    
    Response:
    {
        'question': original question,
        'sql': generated SQL,
        'sql_confidence': 0-100,
        'execution': {
            'success': bool,
            'rows': result rows,
            'columns': column names,
            'row_count': number of rows,
            'error': error message if failed
        },
        'chart': {
            'html': Plotly HTML,
            'type': chart type,
            'description': chart description
        },
        'narrative': generated summary,
        'costs': {
            'sql_generation_cost': amount,
            'narrative_cost': amount,
            'total_cost': amount
        },
        'tokens': {
            'sql_generation': count,
            'narrative': count
        }
    }
    """
    
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        use_cache = data.get('use_cache', True)
        
        if not user_question:
            return format_response(False, error='Question is required'), 400
        
        # Check cache
        if use_cache and user_question in query_cache:
            cached = query_cache[user_question]
            cached['from_cache'] = True
            return format_response(True, cached)
        
        # Step 1: Generate SQL
        sql_result = generate_sql_from_nl(user_question, DATABASE_PATH)
        
        if not sql_result['success']:
            return format_response(False, error=f"SQL generation failed: {sql_result['error']}"), 400
        
        sql = sql_result['sql']
        sql_confidence = sql_result['confidence']
        sql_cost = sql_result['cost']
        sql_tokens = sql_result['tokens']
        
        # Step 2: Execute SQL
        exec_result = execute_sql(sql, DATABASE_PATH)
        
        if not exec_result['success']:
            return format_response(False, error=f"SQL execution failed: {exec_result['error']}"), 400
        
        rows = exec_result['rows']
        columns = exec_result['columns']
        row_count = exec_result['row_count']
        
        # Step 3: Generate chart
        chart_result = generate_chart(columns, rows, user_question)
        
        # Step 4: Generate narrative
        narrative_result = generate_narrative(columns, rows, user_question, sql)
        
        # Compile response
        response_data = {
            'question': user_question,
            'sql': sql,
            'sql_confidence': sql_confidence,
            'execution': {
                'success': True,
                'rows': rows,
                'columns': columns,
                'row_count': row_count
            },
            'chart': {
                'html': chart_result['html'],
                'type': chart_result['type'],
                'description': chart_result['description']
            },
            'narrative': narrative_result['narrative'],
            'costs': {
                'sql_generation': sql_cost,
                'narrative': narrative_result['cost'],
                'total': sql_cost + narrative_result['cost']
            },
            'tokens': {
                'sql_generation': sql_tokens['total'],
                'narrative': narrative_result['tokens_used']
            },
            'from_cache': False
        }
        
        # Cache the result
        query_cache[user_question] = response_data
        
        return format_response(True, response_data)
    
    except Exception as e:
        return format_response(False, error=f"Unexpected error: {str(e)}"), 500

@app.route('/sql/validate', methods=['POST'])
def validate_sql_endpoint():
    """Validate SQL syntax without executing."""
    try:
        data = request.get_json()
        sql = data.get('sql', '').strip()
        
        if not sql:
            return format_response(False, error='SQL is required'), 400
        
        is_valid = validate_sql(sql, DATABASE_PATH)
        
        return format_response(True, {'valid': is_valid})
    
    except Exception as e:
        return format_response(False, error=str(e)), 500

@app.route('/sql/execute', methods=['POST'])
def execute_sql_endpoint():
    """Execute raw SQL query."""
    try:
        data = request.get_json()
        sql = data.get('sql', '').strip()
        
        if not sql:
            return format_response(False, error='SQL is required'), 400
        
        # Security: Prevent modifications
        if any(keyword in sql.upper() for keyword in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER']):
            return format_response(False, error='Only SELECT queries allowed'), 400
        
        result = execute_sql(sql, DATABASE_PATH)
        
        return format_response(result['success'], result if result['success'] else None, 
                             error=result['error'] if not result['success'] else None)
    
    except Exception as e:
        return format_response(False, error=str(e)), 500

@app.route('/sample-queries', methods=['GET'])
def get_sample_queries():
    """Return sample queries for training."""
    sample_queries = [
        "What was our total revenue by region last month?",
        "Show me the trend in Widgets-A sales over the last 6 months.",
        "Which regions have gross margins above 50%?",
        "Compare North America and Europe Premium product margins.",
        "Are we on track to hit annual targets by region?",
        "Which products are underperforming in APAC?",
        "Show me revenue trends by region for the last 6 months.",
        "What is the average margin by product category?",
        "Which product category generated the most revenue in 2025?",
        "Show me APAC sales trends by month and product line."
    ]
    
    return format_response(True, {'queries': sample_queries})

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear query cache."""
    global query_cache
    count = len(query_cache)
    query_cache = {}
    return format_response(True, {'cleared_queries': count})

@app.route('/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics."""
    return format_response(True, {
        'cached_queries': len(query_cache),
        'queries': list(query_cache.keys())
    })

if __name__ == '__main__':
    print("🚀 Conversational BI Assistant - Backend Server")
    print(f"📊 Database: {DATABASE_PATH}")
    print(f"🔑 OpenAI API Key configured: {bool(os.getenv('OPENAI_API_KEY'))}")
    print("\nStarting Flask server...")
    
    print("\nFlask static frontend path:", STATIC_DIR)
    app.run(debug=True, host='0.0.0.0', port=5000)
