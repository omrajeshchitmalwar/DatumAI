"""
utils/llm_client.py
Communicates with the local Ollama server and parses structured responses.
"""
import json
import re
import requests
from typing import Any
from utils.data_loader import schema_to_prompt_text

OLLAMA_BASE_URL = "http://localhost:11434"

SYSTEM_PROMPT = """You are an expert data analyst assistant. The user has uploaded a dataset and will ask questions about it.

Your job is to ALWAYS respond with a JSON object containing ALL of the following keys:

{
"sql": "<valid DuckDB SQL query using the table name 'df', or null if not applicable>",
"python": "<pandas + matplotlib code that reproduces the result, or null>",
"chart_hint": "<one of: bar, line, scatter, pie, histogram, heatmap, box — or null>",
"chart_x": "<column name for x-axis, or null>",
"chart_y": "<column name for y-axis, or null>",
"chart_color": "<column name to use as color/hue, or null>",
"insight": "<brief plain English summary, 1-2 sentences>",
"follow_ups": ["<follow-up question 1>", "<follow-up question 2>"]
}

CORE BEHAVIOR:

* For ANY analytical question, you MUST generate:

  1. SQL query
  2. Python code
  3. A chart (if applicable)
* Only skip python or chart if the task is purely textual.

SQL RULES:

* Use DuckDB SQL. Table name is always `df`.
* Never invent column names.
* LIMIT to 100 rows when returning multiple rows.
* Do NOT use GROUP BY for single aggregates (SUM, COUNT, AVG, etc.).
* Only use ORDER BY when multiple rows are returned.

PYTHON RULES:

* Use pandas and matplotlib only.
* Assume dataframe is named `df`.
* Do not include explanations, only code.
* The code should match the SQL logic.

CHART RULES:

* Always provide chart_hint when data is visualizable.
* Choose appropriate chart:

  * bar → comparisons
  * line → trends over time
  * scatter → relationships
  * histogram → distributions
* Always provide chart_x and chart_y when chart_hint is not null.

INSIGHT RULES:

* Do NOT guess results.
* Describe what the query is analyzing, not the exact answer.

IMPORTANT:

* Output MUST be valid JSON.
* No markdown, no explanation outside JSON.
* Do not connect to external sources.
* Dataset is already loaded as `df`.

"""


def build_prompt(question: str, schema: dict, df_head: str) -> str:
    """Inject schema context and sample data into the user question."""
    schema_text = schema_to_prompt_text(schema)
    return f"""Dataset schema:
{schema_text}

Sample rows (first 5):
{df_head}

User question: {question}"""


def query_llm(prompt: str, model: str = "llama3.2:3b"):
    """
    Send prompt to Ollama and return a parsed response dict.
    On error, returns {"error": "..."}.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_predict": 400,
        },
    }
    print("MODEL USED:", model)
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=300,
        )

        if not resp.ok:
            try:
                body = resp.json()
                err_msg = body.get("error", str(body))
            except Exception:
                err_msg = resp.text

            if "requires more system memory" in err_msg.lower():
                return {
                    "error": (
                        f"The selected model '{model}' does not fit in available memory. "
                        f"Ollama says: {err_msg}"
                    )
                }

            return {"error": f"Ollama HTTP {resp.status_code}: {err_msg}"}

        data = resp.json()
        raw = data.get("message", {}).get("content", "")
        return _parse_llm_response(raw)

    except requests.exceptions.ConnectionError:
        return {
            "error": (
                "Cannot connect to Ollama. "
                "Make sure Ollama is running (`ollama serve`) and the model is pulled "
                f"(`ollama pull {model}`)."
            )
        }
    except requests.exceptions.Timeout:
        return {"error": "Ollama timed out. Try a smaller model or a simpler question."}
    except Exception as e:
        return {"error": f"Unexpected error: {type(e).__name__}: {e}"}


def _parse_llm_response(raw: str) -> dict[str, Any]:
    """
    Extract the JSON blob from the LLM response.
    Handles cases where the model wraps the JSON in markdown fences.
    """
    # Strip markdown code fences if present
    clean = re.sub(r"```(?:json)?", "", raw).strip()

    # Find the first { ... } block
    match = re.search(r"\{.*\}", clean, re.DOTALL)
    if not match:
        # Fallback: treat entire response as an insight
        return {
            "sql": None,
            "python": None,
            "chart_hint": None,
            "chart_x": None,
            "chart_y": None,
            "chart_color": None,
            "insight": raw.strip(),
            "follow_ups": [],
        }

    try:
        parsed = json.loads(match.group())
        # Ensure required keys exist
        defaults = {
            "sql": None,
            "python": None,
            "chart_hint": None,
            "chart_x": None,
            "chart_y": None,
            "chart_color": None,
            "insight": "",
            "follow_ups": [],
        }
        return {**defaults, **parsed}
    except json.JSONDecodeError:
        return {
            "sql": None,
            "python": None,
            "chart_hint": None,
            "chart_x": None,
            "chart_y": None,
            "chart_color": None,
            "insight": raw.strip(),
            "follow_ups": [],
        }
