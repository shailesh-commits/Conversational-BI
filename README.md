# Conversational BI Assistant: Enterprise Demo Project

An end-to-end demonstration of LLM-powered Business Intelligence combining **OpenAI's GPT-4**, **SQLite**, and **Plotly** visualization. This project shows how natural-language business questions are converted to SQL, executed against a database, visualized, and summarized — all in seconds.

## Quick Start

### Prerequisites
- Python 3.8+
- An OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Installation & Setup

1. **Clone the repository:**
```bash
git clone https://github.com/technology-reboot/Conversational-BI.git
cd Conversational-BI
```

2. **Create a Python virtual environment:**
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure your OpenAI API key:**
```bash
# Create a .env file in the project root
echo "OPENAI_API_KEY=sk-..." > .env
```

5. **Generate sample data:**
```bash
python data/sample_data.py
```
This creates `data/sales_data.db`, a SQLite database with sample sales transactions, regional targets, and a product master table.

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

7. **Open the frontend:**
```
http://localhost:5000/frontend/index.html
```
Or serve it separately:
```bash
cd frontend
python -m http.server 8000
# then visit http://localhost:8000
```

### One-step start

The repo ships with startup scripts that handle the venv, dependency install, sample-data generation, and server launch in one go:

```bash
./run.sh        # macOS / Linux
run.bat         # Windows
```

## Architecture

```
┌─────────────────────────────────────────┐
│  Browser: HTML/CSS/JS frontend           │
│  ├─ Input: natural-language question     │
│  └─ Output: chart + SQL + narrative      │
└────────────┬──────────────────────────────┘
             │ HTTP REST API
┌────────────▼──────────────────────────────┐
│  Flask Backend (backend/app.py)            │
│  ├─ /query            – main endpoint      │
│  ├─ /schema           – database schema    │
│  ├─ /sql/validate     – validate raw SQL   │
│  ├─ /sql/execute      – run raw SQL        │
│  ├─ /sample-queries   – example questions  │
│  ├─ /cache/clear      – clear query cache  │
│  ├─ /cache/stats      – cache statistics   │
│  └─ /health           – health check       │
└────────────┬──────────────────────────────┘
             │ OpenAI API calls
┌────────────▼──────────────────────────────┐
│ OpenAI GPT-4                               │
│ ├─ nl_to_sql.py          – NL → SQL        │
│ └─ narrative_generator.py – NL summary     │
└────────────┬──────────────────────────────┘
             │ SQL execution
┌────────────▼──────────────────────────────┐
│  SQLite Database (data/sales_data.db)      │
│  ├─ sales                                  │
│  ├─ regional_targets                       │
│  └─ product_master                         │
└─────────────────────────────────────────────┘
```

## How It Works

**1. Natural language → SQL**
The question, together with a schema definition and few-shot examples, is sent to GPT-4 (temperature 0, for deterministic output) and a SQLite `SELECT` query is generated.

**2. Execute & fetch results**
`nl_to_sql.py` runs the generated SQL against `sales_data.db` and returns columns + rows.

**3. Visualize**
`chart_generator.py` inspects the result shape (scalar, single row, categorical, time series, or matrix) and produces an interactive Plotly chart accordingly — line chart for trends, bar chart for category comparisons, metric card for single values.

**4. Generate an executive narrative**
`narrative_generator.py` sends the results back to GPT-4 with a prompt asking for a 2–3 sentence, executive-audience summary.

## Project Structure

```
Conversational-BI/
├── README.md
├── requirements.txt
├── run.sh / run.bat                  # One-step setup + launch scripts
│
├── data/
│   └── sample_data.py                # Generates data/sales_data.db (created on first run)
│
├── backend/
│   ├── app.py                        # Flask server & API endpoints
│   ├── nl_to_sql.py                  # OpenAI integration: NL → SQL
│   ├── chart_generator.py            # Plotly chart generation
│   └── narrative_generator.py        # LLM-based result summarization
│
├── frontend/
│   ├── index.html                    # Main UI
│   ├── app.js                        # Frontend logic
│   └── styles.css                    # Styling
│
├── prompts/
│   ├── system_prompt_nl_to_sql.txt   # NL → SQL system prompt
│   └── examples_few_shot.json        # Few-shot examples for SQL generation
│
└── tests/
    └── test_queries.py               # Sample test queries
```

## Training Scenarios

These are useful demo walkthroughs for teaching the strengths and limits of LLM-powered BI.

### 1. Simple Aggregation (5 min)
**Question:** *"What was our total revenue by region last month?"*
Expected: correct `GROUP BY` SQL, a bar chart by region, and a narrative identifying the top performer. Teaching point: LLMs are reliable at straightforward aggregations and date handling.

### 2. Time Series Analysis (5 min)
**Question:** *"Show me revenue trends by region for the last 6 months."*
Expected: a multi-line chart with one line per region, time on the x-axis, and a narrative calling out growth/decline trends. Teaching point: time-series detection and multi-dimensional `GROUP BY`.

### 3. Complex Joins (7 min)
**Question:** *"Compare North America and Europe Premium product margins."*
Expected: a join between `sales` and `product_master`, filtered by region and tier, with a side-by-side margin comparison. Teaching point: multi-table joins and domain-specific filtering logic.

### 4. Edge Case — Causation (5 min)
**Question:** *"Why did APAC revenue drop in March?"*
Expected: the system shows correlated data (e.g. March vs. February) rather than inventing a cause, and honestly states it can show the data but not the reason, suggesting checks like product mix shift or seasonality. Teaching point: this is the critical boundary of LLM-powered BI — correlation, not causation.

## API Endpoints

### `POST /query` — main query endpoint
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

### `GET /schema`
Returns the database schema (tables, columns, types).

### `POST /sql/validate`
Validates a raw SQL string (e.g. confirms it's a read-only `SELECT`) without executing it.

### `POST /sql/execute`
Executes raw, read-only SQL directly.

### `GET /sample-queries`
Returns a set of example natural-language questions for quick testing.

### `POST /cache/clear`
Clears the query cache.

### `GET /cache/stats`
Returns cache hit/miss statistics.

### `GET /health`
Health check — verifies the database connection and reports whether the OpenAI API key is configured.

## Cost Management

### Pricing model (GPT-4)
- Input: $0.03 per 1K tokens
- Output: $0.06 per 1K tokens

### Cost examples

| Query | Tokens | Cost |
|---|---|---|
| Simple aggregation | ~800 | $0.0015 |
| Complex join + narrative | ~1,500 | $0.0035 |
| Average (both calls) | ~1,150 | $0.0025 |

```
Per-query cost = ((prompt_tokens * 0.03) + (completion_tokens * 0.06)) / 1000

For 100 analysts × 50 queries/day:
5,000 queries/day × $0.0025 average ≈ $12.50/day ≈ $3,500/month for heavy usage
```

### Cost optimization strategies
1. **Query caching** — identical questions are cached (1-hour TTL by default)
2. **Result aggregation** — combine multiple small queries
3. **Prompt optimization** — keep the system prompt lean
4. **User training** — help analysts phrase clearer questions

## Security & Compliance

- **Read-only SQL** — `INSERT`, `UPDATE`, `DELETE`, `DROP`, and `ALTER` statements are blocked; only `SELECT` queries are permitted.
- **Audit trail** — each query can be logged with the question, generated SQL, results, timestamp, and cost; extendable to a compliance system.
- **Data governance** — no row-level data is sent to OpenAI as part of the prompt, only the schema; for PII, apply database-level masking before queries reach the system.

Example audit log entry:
```json
{
  "timestamp": "2026-06-30T10:30:45Z",
  "user": "analyst@company.com",
  "question": "Show me revenue by region",
  "sql": "SELECT region, SUM(revenue) FROM sales ...",
  "rows_returned": 5,
  "cost": 0.0021,
  "cache_hit": false,
  "execution_time_ms": 145
}
```

## Testing

```bash
python tests/test_queries.py
```

Manual testing checklist:
- Simple aggregation works
- Time-series chart renders correctly
- Narrative is factually accurate
- Error handling shows helpful messages
- Cache hits are detected
- Cost tracking is accurate
- SQL confidence scores reflect query complexity

## Advanced Customization

**Improve SQL quality** — edit `backend/nl_to_sql.py`: adjust the system prompt (`SCHEMA_DEFINITION`), the few-shot examples in `prompts/examples_few_shot.json`, the temperature (currently `0` for deterministic SQL), or the max token limit.

**Custom charts** — edit `backend/chart_generator.py` and add a new detection branch / chart function using Plotly's `go.Figure` API.

**Multi-language support** — extend the system prompt with translated variants keyed by language code.

## Troubleshooting

| Issue | Solution |
|---|---|
| `OPENAI_API_KEY not configured` | Create a `.env` file in the project root with `OPENAI_API_KEY=sk-...` |
| `Database not found` | Run `python data/sample_data.py` to generate `data/sales_data.db` |
| Backend returns 500 errors | Check the Flask server logs; confirm the OpenAI API is reachable |
| Incorrect SQL generated | Review the schema definition in `nl_to_sql.py` and the few-shot examples; try rephrasing the question |
| Charts not rendering | Check the browser console for JS errors and confirm the Plotly library loaded |

## Learning Objectives

After working through this demo, you should be able to:

1. Articulate when LLM-powered BI works well (aggregations, trends, comparisons)
2. Identify its failure modes (hallucination, complex business logic, causal claims)
3. Design effective system prompts with schema definitions and few-shot examples
4. Implement query caching and cost tracking
5. Reason about enterprise trade-offs between speed, cost, and reliability
6. Apply production patterns such as audit trails, SQL validation, and graceful error recovery

## Next Steps for Production

1. **Database** — migrate from SQLite to Snowflake, Redshift, or BigQuery
2. **Authentication** — add user/role-based access control
3. **Monitoring** — integrate with CloudWatch or Datadog for observability
4. **Governance** — add query-approval workflows for sensitive data
5. **Caching** — move to Redis for distributed caching across instances
6. **Load testing** — validate behavior at scale (100+ concurrent analysts)

## License

This project is intended for educational and training purposes.
