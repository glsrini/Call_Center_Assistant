# Call_Center_Assistant

A multi-agent customer support chat application for a digital music store. It uses the Chinook relational database as its only source of catalog and account facts, verifies customers before billing lookups, and keeps additive music preference memory per customer.

## Run locally

Use Python 3.12. Copy `.env.example` to `.env`, add an OpenAI-compatible API key, then install and launch:

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

On first start the app downloads the canonical Chinook SQLite SQL script and caches it in the user's cache directory. The database is loaded into memory at startup. Set `CHINOOK_SQL_URL` to use a mirror. Without an API key the app can still return deterministic summaries directly from tool results, but configure a key for natural language responses.

## Docker

```bash
docker build -t customer-support-assistant .
docker run --env-file .env -p 7860:7860 customer-support-assistant
```

## Tests

```bash
pytest tests/ -v
```

Tests create a small disposable Chinook-shaped SQLite fixture and do not need a network connection or API key.

## Runtime logs

The app writes INFO-level execution events to `logs/agent.log` and rotates the file at 2 MB, keeping up to three backups. Runtime logs are local and ignored by Git; the repository includes an empty `logs/` directory so the log destination exists after checkout. Log entries record session IDs, selected specialists, elapsed time, and failures without recording customer messages or assistant responses. For Docker deployments, mount `/app/logs` to persistent storage if logs should survive container replacement.

## Architecture

- `src/db.py` downloads/caches and loads the Chinook SQL source and exposes SQLAlchemy parameter-bound query execution and health checks.
- `src/tools.py` provides five catalog tools and four account tools. Every tool returns a JSON string, validates numeric identifiers, binds query parameters, and scopes invoice details to the verified customer.
- `src/agents.py` builds a LangGraph supervisor workflow with catalog and invoice specialist nodes, mixed-query sequencing, account verification, and a direct off-topic response. The specialist prompts require tool-grounded claims and honest empty/error handling.
- `src/memory.py` stores explicit music preferences per customer and merges additions without dropping prior preferences. Questions are ignored.
- `app.py` provides the Gradio chat UI, session UUIDs, verification follow-up, status feedback, and new-conversation reset.

The graph uses an in-memory checkpoint and the preference store is also in memory. Both reset when the process restarts. This is appropriate for the capstone; production deployments should replace them with persistent stores. User account data is never returned until the current chat session verifies the customer. Invoice ID queries are constrained to that customer.

## Example prompts

- “What rock albums do you have?”
- “Do you carry any songs by AC/DC?”
- “Show me my recent purchases.” (Then enter Customer ID, email, or phone.)
- “I love jazz and AC/DC.”
- “What’s the weather today?”

Do not commit `.env`, API keys, or the downloaded Chinook SQL script.
