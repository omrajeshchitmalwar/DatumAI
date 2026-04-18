# 📊 DatumAI

> Upload any dataset. Ask questions in plain English. Get SQL queries, Python analysis, visualizations, and insights — powered by a local LLM. **100% free, 100% local, zero cloud dependencies.**

![Python](https://img.shields.io/badge/python-3.11-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.35-red)
![DuckDB](https://img.shields.io/badge/duckdb-0.10-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

---

<img width="1854" height="941" alt="Screenshot from 2026-04-19 01-12-50" src="https://github.com/user-attachments/assets/a5d312b1-13c7-45b1-bbc9-eba17c04d272" />


## ✨ What it does

Upload a CSV, Excel, or JSON file and ask natural language questions like:

| Question | What you get |
|---|---|
| *Why did sales drop in March?* | Trend query + line chart + written explanation |
| *Show me the top 10 customers by revenue* | SQL + ranked table + bar chart |
| *What's the correlation between price and quantity?* | Heatmap + statistical insight |
| *Find outliers in the order_value column* | Box plot + IQR analysis |
| *Which product category has the highest margin?* | Aggregation query + pie chart |

Each response gives you:
- 🔍 **Auto-generated SQL** (editable, runnable DuckDB query)
- 📊 **Interactive chart** (Plotly — zoom, hover, export)
- 🐍 **Python code** (pandas snippet you can copy)
- 💡 **Plain English insight** (2-4 sentence explanation)
- 💬 **Suggested follow-ups** (one-click next questions)

---

## 🏗️ Architecture

```
User
 │
 ▼
Streamlit UI  ──→  Ollama (local LLM)
     │                   │
     │          ┌─────────────────┐
     │          │  Prompt builder │  ← schema + sample rows injected
     │          │  Response parser│  ← JSON extraction + validation
     │          └─────────────────┘
     │
     ▼
DuckDB ──→ Result DataFrame ──→ Plotly chart
Pandas ──→ Python analysis
     │
     ▼
Result display (table + chart + insight + CSV download)
```

---

## 🚀 Quick start

### 1. Install Ollama

Download from [ollama.com](https://ollama.com) and install for your OS.

```bash
# Pull your preferred model (choose one)
ollama pull llama3        # 4.7 GB — best quality
ollama pull mistral       # 4.1 GB — fast
ollama pull codellama     # 3.8 GB — good at SQL

# Start the server (runs in background)
ollama serve
```

### 2. Clone and set up the project

```bash
git clone https://github.com/your-username/data-analyst-copilot.git
cd data-analyst-copilot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env .env.local
# Edit .env.local if you want to change the Ollama URL or default model
```

### 4. Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 📁 Project structure

```
data-analyst-copilot/
├── app.py                    # Streamlit entry point & chat loop
├── requirements.txt
├── .env                      # Config (Ollama URL, model, limits)
├── .python-version           # 3.11.9 (for pyenv)
├── .gitignore
│
├── utils/
│   ├── data_loader.py        # CSV/Excel/JSON parsing + schema extraction
│   ├── llm_client.py         # Ollama REST client + prompt builder
│   └── query_engine.py       # DuckDB SQL executor + Python sandbox
│
└── components/
    ├── chart_renderer.py     # Plotly figure factory (bar/line/scatter/…)
    └── result_display.py     # Streamlit result rendering + download
```

---

## 🎛️ Supported chart types

The LLM automatically picks the right chart type, but you can also ask for one explicitly:

| Chart | When it's used |
|---|---|
| `bar` | Category comparisons, rankings |
| `line` | Time-series, trends |
| `scatter` | Correlations between two numeric columns |
| `pie` | Part-to-whole breakdowns |
| `histogram` | Distribution of a single column |
| `box` | Outlier detection, spread by category |
| `heatmap` | Full correlation matrix |

---

## 💾 Supported file formats

| Format | Extension | Notes |
|---|---|---|
| CSV | `.csv` | Any delimiter auto-detected |
| Excel | `.xlsx`, `.xls` | First sheet used |
| JSON | `.json` | Records-oriented arrays |

Column names are automatically cleaned (lowercased, spaces → underscores).

---

## ⚙️ Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `DEFAULT_MODEL` | `llama3` | LLM to use |
| `MAX_QUERY_ROWS` | `1000` | Row cap for query results |
| `MAX_UPLOAD_MB` | `100` | Max file size |

---

## 🔒 Privacy

All processing is **local**. Your data never leaves your machine:
- Files are parsed in-memory (never written to disk)
- LLM inference runs via Ollama on your CPU/GPU
- No telemetry, no API keys, no cloud calls

---

## 🛠️ Troubleshooting

**"Cannot connect to Ollama"**
→ Run `ollama serve` in a separate terminal.

**"Model not found"**
→ Run `ollama pull llama3` (or whichever model you selected).

**SQL errors / wrong column names**
→ The LLM occasionally hallucinates column names. The app auto-retries with heuristic fixes. You can also edit the SQL directly in the expander and re-run.

**Slow responses**
→ Try `mistral` instead of `llama3` for faster inference, especially on CPU.

---

## 🗺️ Roadmap

- [ ] Multi-table joins (upload multiple CSVs)
- [ ] Chat memory (reference previous queries)
- [ ] Export full analysis report to PDF
- [ ] Support for Parquet files
- [ ] Editable SQL with re-run button
- [ ] Vector search over column descriptions

---

## 📄 License

MIT — free for personal and commercial use.
