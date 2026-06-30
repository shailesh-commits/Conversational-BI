"""
Chart generator: Creates Plotly charts from SQL results.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import json

def detect_result_type(columns, rows):
    """
    Detect the type of result set to determine best chart.
    
    Returns: 'scalar', 'single_row', 'categorical', 'time_series', 'matrix'
    """
    if len(rows) == 0:
        return 'empty'
    
    if len(rows) == 1:
        if len(columns) == 1:
            return 'scalar'
        else:
            return 'single_row'
    
    # Check for time series (contains date or month columns)
    time_keywords = ['date', 'month', 'year', 'time', 'period']
    has_time_column = any(col.lower() in time_keywords or any(kw in col.lower() for kw in time_keywords) for col in columns)
    
    if has_time_column:
        return 'time_series'
    
    # Check for multiple numeric columns
    return 'categorical'

def create_dataframe(columns, rows):
    """Convert database result to pandas DataFrame."""
    return pd.DataFrame(rows, columns=columns)

def generate_chart(columns, rows, user_question="", chart_type=None):
    """
    Generate appropriate chart based on result type.
    
    Args:
        columns (list): Column names
        rows (list): Data rows
        user_question (str): Original user question
        chart_type (str): Force specific chart type if provided
    
    Returns:
        dict: {
            'html': Plotly HTML,
            'type': chart type used,
            'description': chart description
        }
    """
    
    if len(rows) == 0:
        return {
            'html': '<p>No results found for this query.</p>',
            'type': 'empty',
            'description': 'Empty result set'
        }
    
    df = create_dataframe(columns, rows)
    result_type = detect_result_type(columns, rows)
    
    # If user specifies chart type, use it
    if chart_type:
        result_type = chart_type
    
    try:
        if result_type == 'scalar':
            fig = create_scalar_chart(df)
            chart_desc = "Single value metric"
        
        elif result_type == 'single_row':
            fig = create_single_row_chart(df)
            chart_desc = "Single row of data"
        
        elif result_type == 'time_series':
            fig = create_time_series_chart(df)
            chart_desc = "Time series trend"
        
        elif result_type == 'categorical':
            fig = create_categorical_chart(df)
            chart_desc = "Category comparison"
        
        else:
            fig = create_categorical_chart(df)
            chart_desc = "Data visualization"
        
        return {
            'html': fig.to_html(full_html=False, include_plotlyjs=False),
            'type': result_type,
            'description': chart_desc
        }
    
    except Exception as e:
        return {
            'html': f'<p>Error generating chart: {str(e)}</p>',
            'type': 'error',
            'description': f'Chart generation failed: {str(e)}'
        }

def create_scalar_chart(df):
    """Create a big number/metric display."""
    value = df.iloc[0, 0]
    col_name = df.columns[0]
    
    fig = go.Figure(data=[
        go.Indicator(
            mode="number",
            value=value,
            title={"text": col_name},
            domain={'x': [0, 1], 'y': [0, 1]}
        )
    ])
    
    fig.update_layout(
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_single_row_chart(df):
    """Create a bar chart for single row with multiple columns."""
    columns = df.columns.tolist()
    values = df.iloc[0].tolist()
    
    fig = go.Figure(data=[
        go.Bar(x=columns, y=values, text=values, textposition='auto')
    ])
    
    fig.update_layout(
        title="Data Summary",
        xaxis_title="Metrics",
        yaxis_title="Values",
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_time_series_chart(df):
    """Create a line chart for time series data."""
    # Identify date column and numeric columns
    date_col = None
    for col in df.columns:
        if 'date' in col.lower() or 'month' in col.lower() or 'year' in col.lower() or 'time' in col.lower() or 'period' in col.lower():
            date_col = col
            break
    
    if date_col is None:
        date_col = df.columns[0]
    
    # Get numeric columns (excluding date)
    numeric_cols = [col for col in df.columns if col != date_col and df[col].dtype in ['float64', 'int64']]
    
    if not numeric_cols:
        numeric_cols = df.columns[1:].tolist()
    
    fig = go.Figure()
    
    # If there's a grouping column (like region or category)
    other_cols = [col for col in df.columns if col != date_col and col not in numeric_cols]
    
    if other_cols:
        # Multi-line chart with grouping
        groupby_col = other_cols[0]
        for group in df[groupby_col].unique():
            group_data = df[df[groupby_col] == group]
            fig.add_trace(go.Scatter(
                x=group_data[date_col],
                y=group_data[numeric_cols[0]] if numeric_cols else group_data.iloc[:, 1],
                name=str(group),
                mode='lines+markers'
            ))
    else:
        # Single line chart
        for col in numeric_cols:
            fig.add_trace(go.Scatter(
                x=df[date_col],
                y=df[col],
                name=col,
                mode='lines+markers'
            ))
    
    fig.update_layout(
        title="Trend Over Time",
        xaxis_title=date_col,
        yaxis_title="Value",
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_categorical_chart(df):
    """Create a bar chart for categorical data."""
    if len(df.columns) < 2:
        return create_single_row_chart(df)
    
    # First column is category, rest are values
    category_col = df.columns[0]
    value_col = df.columns[1]
    
    # If there's a third column, it might be a grouping
    if len(df.columns) > 2:
        group_col = df.columns[2]
        fig = px.bar(
            df,
            x=category_col,
            y=value_col,
            color=group_col,
            barmode='group',
            title=f"{value_col} by {category_col}",
            height=500
        )
    else:
        fig = px.bar(
            df,
            x=category_col,
            y=value_col,
            title=f"{value_col} by {category_col}",
            height=500,
            text=value_col
        )
        fig.update_traces(textposition='auto')
    
    fig.update_xaxes(tickangle=-45)
    
    return fig

def generate_chart_html(columns, rows):
    """Wrapper function that returns HTML string."""
    result = generate_chart(columns, rows)
    return result['html']
