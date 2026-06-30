"""
Narrative generator: Creates human-readable summaries of query results using OpenAI.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

NARRATIVE_PROMPT_TEMPLATE = """
You are a financial analyst. Summarize the following query results in 2-3 sentences for an executive audience.

Data Columns: {columns}
Data Sample (first few rows): {sample_rows}

Requirements:
- Highlight the most important finding
- Use specific numbers from the data
- Be concise and actionable
- For trends, mention direction and magnitude
- For comparisons, mention which is best/worst

Narrative (2-3 sentences):
"""

def generate_narrative(columns, rows, user_question="", sql=""):
    """
    Generate a narrative summary of query results.
    
    Args:
        columns (list): Column names from query result
        rows (list): Data rows
        user_question (str): Original user question
        sql (str): SQL query executed
    
    Returns:
        dict: {
            'narrative': generated text,
            'tokens_used': token count,
            'cost': API cost,
            'success': bool
        }
    """
    
    if len(rows) == 0:
        return {
            'narrative': "No data found for this query.",
            'tokens_used': 0,
            'cost': 0,
            'success': True
        }
    
    try:
        # Prepare sample data (first 10 rows)
        sample_size = min(10, len(rows))
        sample_rows = []
        for i in range(sample_size):
            row_dict = {columns[j]: str(rows[i][j]) for j in range(len(columns))}
            sample_rows.append(row_dict)
        
        prompt = NARRATIVE_PROMPT_TEMPLATE.format(
            columns=", ".join(columns),
            sample_rows=json.dumps(sample_rows, indent=2)
        )
        
        if user_question:
            prompt = f"Original question: {user_question}\n\n{prompt}"
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial analyst providing executive summaries of business data."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        narrative = response.choices[0].message.content.strip()
        
        # Calculate cost
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
        
        return {
            'narrative': narrative,
            'tokens_used': prompt_tokens + completion_tokens,
            'cost': round(cost, 5),
            'success': True
        }
    
    except Exception as e:
        return {
            'narrative': f"Error generating narrative: {str(e)}",
            'tokens_used': 0,
            'cost': 0,
            'success': False,
            'error': str(e)
        }

def generate_executive_summary(results_data):
    """
    Generate a comprehensive executive summary.
    
    Args:
        results_data (dict): {
            'question': user question,
            'sql': SQL query,
            'columns': result columns,
            'rows': result rows,
            'row_count': number of rows
        }
    
    Returns:
        str: Executive summary
    """
    
    question = results_data.get('question', '')
    row_count = results_data.get('row_count', 0)
    
    narrative = generate_narrative(
        results_data.get('columns', []),
        results_data.get('rows', []),
        user_question=question,
        sql=results_data.get('sql', '')
    )
    
    summary = f"{narrative['narrative']}\n\n"
    summary += f"*Data: {row_count} rows returned*"
    
    return summary
