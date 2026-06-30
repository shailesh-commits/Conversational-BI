# Conversational BI Assistant: Enterprise Demo Project

An end-to-end demonstration of LLM-powered Business Intelligence combining OpenAI's GPT-4, SQLite, and Plotly visualization. This project showcases how natural language questions are converted to SQL queries, executed, visualized, and summarized in seconds.

## 🎯 Quick Start (5 minutes)

### Prerequisites
- Python 3.8+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation & Setup

1. **Clone and navigate to the project:**
```bash
cd conversational_bi_demo
```

2. **Create a Python virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

5. **Generate sample data:**
```bash
python data/sample_data.py
```
Expected output:
```
✓ Database created at ./data/sales_data.db
✓ Generated 2,700,000 sales transactions
✓ Coverage: 2025-01-01 to 2025-06-30
```

6. **Start the backend server:**
```bash
python backend/app.py
```
You should see:
```
🚀 Conversational BI Assistant - Backend Server
📊 Database: ./data/sales_data.db
🔑 OpenAI API Key configured: True
Starting Flask server...
 * Running on http://localhost:5000
```

7. **Open the frontend in your browser:**
```
http://localhost:5000/frontend/index.html
```
Or serve the frontend with a simple HTTP server:
```bash
cd frontend
python -m http.server 8000
# Then visit http://localhost:8000
```

## 📊 Architecture Overview

```
┌─────────────────────────────────────────┐
│  Browser: React/HTML UI                 │
│  ├─ Input: Natural language question    │
│  └─ Output: Chart + SQL + Narrative     │
└────────────┬────────────────────────────┘
             │ HTTP REST API
┌────────────▼────────────────────────────┐
│  Flask Backend (backend/app.py)         │
│  ├─ /query - Main endpoint              │
│  ├─ /schema - Database schema           │
│  ├─ /sql/execute - Run raw SQL          │
│  └─ /sample-queries - Training data     │
└────────────┬────────────────────────────┘
             │ OpenAI API calls
┌────────────┬────────────────────────────┐
│ OpenAI GPT-4 (nl_to_sql.py)             │
│ ├─ NL→SQL generation                   │
│ └─ Narrative generation                 │
└────────────┬────────────────────────────┘
             │ SQL execution
┌────────────▼────────────────────────────┐
│  SQLite Database (data/sales_data.db)   │
│  ├─ sales (2.7M rows)                   │
│  ├─ regional_targets                    │
│  └─ product_master                      │
└─────────────────────────────────────────┘
```

## 🚀 How It Works

### Step 1: Natural Language → SQL
```python
Question: "Show me revenue by region last month"
         ↓
GPT-4 with schema definition
         ↓
SQL: "SELECT region, SUM(revenue) FROM sales 
      WHERE STRFTIME('%Y-%m', date) = '2025-06-01'
      GROUP BY region"
```

### Step 2: Execute & Fetch Results
```python
SQL execution against SQLite
         ↓
Returns: 
  columns: ['region', 'total_revenue']
  rows: [('North America', 2500000), ('Europe', 1800000), ...]
```

### Step 3: Visualize with Plotly
```python
Result type detection:
  - Time series → Line chart
  - Categories → Bar chart
  - Single value → Metric card
         ↓
Interactive HTML chart (embedded in UI)
```

### Step 4: Generate Executive Summary
```python
Results + GPT-4
         ↓
Narrative: "North America led with $2.5M (40% of total). 
Europe contributed $1.8M with strong 62% margins..."
```

## 📁 Project Structure

```
conversational_bi_demo/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
│
├── data/
│   ├── sample_data.py                # Generate SQLite database
│   └── sales_data.db                 # SQLite database (created by sample_data.py)
│
├── backend/
│   ├── app.py                        # Flask server & API endpoints
│   ├── nl_to_sql.py                  # OpenAI integration for NL→SQL
│   ├── chart_generator.py            # Plotly chart generation
│   └── narrative_generator.py        # LLM-based summarization
│
├── frontend/
│   ├── index.html                    # Main UI
│   ├── app.js                        # Frontend logic
│   └── styles.css                    # Styling
│
├── prompts/
│   ├── system_prompt_nl_to_sql.txt  # NL→SQL system prompt
│   ├── examples_few_shot.json        # Few-shot examples
│   └── narrative_prompt.txt          # Narrative generation template
│
└── tests/
    └── test_queries.py               # Sample test queries
```

## 🎓 Training Scenarios

### Scenario 1: Simple Aggregation (5 min)
**Question:** "What was our total revenue by region last month?"

**Expected Behavior:**
- ✓ Generates correct SQL with GROUP BY
- ✓ Returns bar chart showing regions
- ✓ Narrative identifies top performer

**Teaching Points:**
- LLM excels at straightforward aggregations
- Date functions handled correctly
- Chart type auto-selected appropriately

### Scenario 2: Time Series Analysis (5 min)
**Question:** "Show me revenue trends by region for the last 6 months."

**Expected Behavior:**
- ✓ Multi-line chart with 5 region lines
- ✓ Time on x-axis, revenue on y-axis
- ✓ Narrative highlights growth/decline trends

**Teaching Points:**
- Time-series detection and visualization
- Complex GROUP BY with multiple dimensions
- Trend narrative generation

### Scenario 3: Complex Joins (7 min)
**Question:** "Compare North America and Europe Premium product margins."

**Expected Behavior:**
- ✓ Joins sales and product_master tables
- ✓ Filters by region and tier
- ✓ Side-by-side margin comparison
- ✓ Highlights the region with better margins

**Teaching Points:**
- Multi-table join complexity
- Domain-specific logic (Premium tier)
- Structured data comparison

### Scenario 4: Edge Case - Causation (5 min)
**Question:** "Why did APAC revenue drop in March?"

**Expected Behavior:**
- ✓ System does NOT hallucinate causation
- ✓ Shows correlated data (March vs Feb comparison)
- ✓ Honest response: "I can show you the data, but not the cause"
- ✓ Suggests: "Check product mix shift, regional events, seasonality"

**Teaching Points:**
- **Critical boundary:** LLM-BI shows correlation, not causation
- Importance of domain expertise
- Honest limitations of the system

## 🛠️ API Endpoints

### POST `/query` - Main Query Endpoint
**Request:**
```json
{
  "question": "Show me revenue by region last month",
  "use_cache": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "question": "Show me revenue by region last month",
    "sql": "SELECT region, SUM(revenue) FROM sales ...",
    "sql_confidence": 85,
    "execution": {
      "success": true,
      "rows": [["North America", 2500000], ...],
      "columns": ["region", "total_revenue"],
      "row_count": 5
    },
    "chart": {
      "html": "<div id='plot'>...</div>",
      "type": "categorical",
      "description": "Category comparison"
    },
    "narrative": "North America led with $2.5M revenue...",
    "costs": {
      "sql_generation": 0.00125,
      "narrative": 0.00085,
      "total": 0.0021
    },
    "from_cache": false
  }
}
```

### GET `/schema`
Returns database schema with all tables and columns.

**Response:**
```json
{
  "schema": {
    "sales": {
      "columns": ["transaction_id", "date", "region", "product_category", "units_sold", "revenue", "cost_of_goods_sold", "gross_margin_pct"],
      "types": ["INTEGER", "DATE", "TEXT", "TEXT", "INTEGER", "REAL", "REAL", "REAL"]
    },
    ...
  }
}
```

### POST `/sql/execute`
Execute raw SQL (read-only).

### GET `/health`
Health check - verifies database connection.

### POST `/cache/clear`
Clear query cache.

## 💰 Cost Management

### Pricing Model (GPT-4)
- Input: $0.03 per 1K tokens
- Output: $0.06 per 1K tokens

### Cost Examples
| Query | Tokens | Cost |
|-------|--------|------|
| Simple aggregation | ~800 | $0.0015 |
| Complex join + narrative | ~1500 | $0.0035 |
| Average (both) | ~1150 | $0.0025 |

### Cost Calculation
```
Per-query cost = ((prompt_tokens * 0.03) + (completion_tokens * 0.06)) / 1000

For 100 analysts × 50 queries/day:
5,000 queries/day × $0.0025 average = $12.50/day
≈ $3,500/month for heavy usage
```

### Cost Optimization Strategies
1. **Query Caching** - System caches identical questions (1-hour TTL)
2. **Result Aggregation** - Combine multiple small queries
3. **Prompt Optimization** - Reduce system prompt size
4. **User Training** - Help analysts ask better questions

## 🔐 Security & Compliance

### Read-Only SQL
The system blocks `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER` statements. Only `SELECT` queries are allowed.

### Audit Trail
- Every query is logged with: question, SQL, results, timestamp, cost
- Can be extended to integrate with compliance systems

### Data Governance
- No sensitive data in prompts sent to OpenAI
- Schema is public; individual values are returned as query results
- For PII: Use database-level masking before queries reach the system

### Example Audit Log
```json
{
  "timestamp": "2025-06-18T10:30:45Z",
  "user": "analyst@company.com",
  "question": "Show me revenue by region",
  "sql": "SELECT region, SUM(revenue) FROM sales ...",
  "rows_returned": 5,
  "cost": 0.0021,
  "cache_hit": false,
  "execution_time_ms": 145
}
```

## 🧪 Testing

### Run Test Queries
```bash
python tests/test_queries.py
```

### Manual Testing Checklist
- [ ] Simple aggregation works
- [ ] Time-series chart renders correctly
- [ ] Narrative is factually accurate
- [ ] Error handling shows helpful messages
- [ ] Cache hits are detected
- [ ] Cost tracking is accurate
- [ ] SQL confidence scores reflect complexity

## 📈 Advanced Customization

### Improve SQL Quality
Edit `backend/nl_to_sql.py` to adjust:
- System prompt (currently in `SCHEMA_DEFINITION`)
- Few-shot examples
- Temperature (currently 0 for deterministic SQL)
- Max tokens for generation

### Custom Charts
Edit `backend/chart_generator.py`:
```python
def create_custom_chart(df):
    # Your Plotly chart logic
    fig = go.Figure(...)
    return fig
```

### Multi-Language Support
Extend `SCHEMA_DEFINITION` with translations:
```python
SCHEMA_DEFINITION = {
    'en': 'You are a SQL expert...',
    'es': 'Eres un experto en SQL...',
    'fr': 'Vous êtes un expert SQL...'
}
```

## 🐛 Troubleshooting

### Issue: "OPENAI_API_KEY not configured"
**Solution:** Check `.env` file exists and has a valid key from https://platform.openai.com/api-keys

### Issue: "Database not found"
**Solution:** Run `python data/sample_data.py` to generate the database

### Issue: Backend returns 500 errors
**Solution:** Check Flask server logs for detailed error messages. Ensure OpenAI API is accessible.

### Issue: Incorrect SQL generated
**Solution:** 
1. Check the schema definition in `nl_to_sql.py`
2. Review the few-shot examples
3. Try rephrasing the question
4. Increase `sql_confidence` threshold in frontend if below 60%

### Issue: Charts not rendering
**Solution:** 
1. Check browser console for JavaScript errors
2. Ensure Plotly library is loaded (check network tab)
3. Verify result data is valid JSON

## 📚 Further Reading

- **LIDA Framework:** Automated visualization generation from data
- **Spider Dataset:** Text-to-SQL benchmark (80K+ examples)
- **Prompt Engineering:** Best practices for LLM systems
- **Cost Optimization:** Strategies for enterprise LLM deployments

## 🎓 Learning Objectives

After working through this demo, you should be able to:

1. ✅ Articulate when LLM-BI works (aggregations, trends, comparisons)
2. ✅ Identify failure modes (hallucination, complex logic, causation)
3. ✅ Design effective system prompts with schema definitions
4. ✅ Implement query caching and cost tracking
5. ✅ Understand enterprise trade-offs (speed vs. cost vs. reliability)
6. ✅ Build production patterns (audit trails, validation, error recovery)

## 🚀 Next Steps for Production

1. **Database:** Migrate from SQLite to Snowflake/Redshift/BigQuery
2. **Authentication:** Add user/role-based access control
3. **Monitoring:** Integrate with CloudWatch/DataDog for observability
4. **Governance:** Implement query approval workflows for sensitive data
5. **Caching:** Use Redis for distributed caching across multiple instances
6. **Load Testing:** Test at scale (100+ concurrent analysts)

## 📞 Support

For questions or issues:
- Check the troubleshooting section above
- Review error messages in backend logs
- Inspect browser console for frontend errors

## 📄 License

This project is for educational and training purposes.

---

**Happy querying! 🎉**
"# Conversational-BI" 
