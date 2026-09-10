# Alphaminr Backend

**Generate a daily markets newsletter that traces today's news to the companies it touches.**

Alphaminr Backend is a small Flask service. On request, or on a schedule, it pulls the last day of government policy, economic data, central bank and geopolitical news through Brave Search, hands that context to Claude with web search enabled, and gets back a complete HTML newsletter. Each newsletter is stored in PostgreSQL and served by id. The editor UI that reads from this service lives in [alphaminr_frontend](https://github.com/krishivseth/alphaminr_frontend).

## What it does

- **Collects the day's news.** Four search passes run before generation: government policies, economic data releases, central bank statements, and geopolitical developments. Each runs several queries against Brave Search restricted to the past day. A separate pass tries to pull current index, commodity and crypto prices.
- **Writes the newsletter with Claude.** The collected results and market data are folded into a long prompt. Claude is called with the Anthropic web search tool (limited to a handful of finance and news domains) and asked to produce five headlines, each with impact analysis and the tickers of affected public companies, as a finished HTML email.
- **Stores and serves newsletters.** Every generated newsletter gets a UUID and an upsert into a `newsletters` table. There are routes to list newsletters, fetch one as raw HTML, and check health.
- **Runs on a schedule.** The same generation function runs from a Railway cron service, from `cron.py`, or from a secret-protected `/api/cron/generate` endpoint that an external cron can hit.
- **Talks to Brave over MCP with a fallback.** Searches go through the official `@brave/brave-search-mcp-server` over stdio. If the server cannot be started or a call fails, the client falls back to the Brave Search REST API directly.

## How it works

```mermaid
flowchart LR
    FE["alphaminr_frontend<br/>editor portal"]
    CRON["Railway cron / external cron"]
    BE["Flask app<br/>app.py"]
    MCP["Brave Search MCP server<br/>(npx, stdio) or Brave REST API"]
    CL["Claude<br/>with web_search tool"]
    DB[("PostgreSQL")]

    FE -- "POST /api/generate<br/>GET /api/newsletters" --> BE
    CRON -- "cron.py or<br/>POST /api/cron/generate" --> BE
    BE -- "policy, economic, central bank,<br/>geopolitical, market queries" --> MCP
    BE -- "prompt + search context" --> CL
    CL -- "HTML newsletter" --> BE
    BE -- "upsert by UUID" --> DB
```

Generation is synchronous. A request to `/api/generate` runs all the searches, one Claude call, and the database write before it returns, so expect it to take well over a minute. The response includes the HTML, the new newsletter id, and timings.

When the process starts, `app.py` checks for `RAILWAY_CRON_SCHEDULE`. If it is set, it generates one newsletter and exits instead of starting the web server. `railway.toml` applies the same check in its start command and otherwise launches gunicorn.

## Quick start

You need Python 3.11, Node 20+ (for the Brave MCP server), a PostgreSQL database, a Brave Search API key, and an Anthropic API key.

```bash
pip install -r requirements.txt
npm install -g @brave/brave-search-mcp-server

export BRAVE_SEARCH_API_KEY=...
export ANTHROPIC_API_KEY=...
export DATABASE_URL=postgres://user:pass@host:5432/dbname

python app.py            # http://localhost:5000
```

The app exits at import time if either API key is missing. `DATABASE_URL` is read lazily, so the server starts without it, but every newsletter route will fail.

To run it the way the Dockerfile does:

```bash
gunicorn -w 2 -k gthread --threads 4 -t 180 app:app --bind 0.0.0.0:8080
```

Generate a newsletter and view it:

```bash
curl -X POST http://localhost:5000/api/generate -H "Content-Type: application/json" -d '{}'
curl http://localhost:5000/api/newsletters
open http://localhost:5000/newsletter/<id>
```

Smoke-test a deployment:

```bash
RAILWAY_URL=https://your-app.railway.app python test_railway.py
```

## Configuration

| Variable | Required | Purpose |
|----------|----------|---------|
| `BRAVE_SEARCH_API_KEY` | Yes | Brave Search key. Passed to the MCP server as `BRAVE_API_KEY` and used directly for the REST fallback. |
| `ANTHROPIC_API_KEY` | Yes | Anthropic key for the Claude call. |
| `DATABASE_URL` | Yes for storage | PostgreSQL connection string. Connections use `sslmode=require`. Railway provides this when a Postgres service is attached. |
| `ANTHROPIC_MODEL` | No | Model for generation. Default `claude-sonnet-4-20250514`. |
| `ANTHROPIC_MAX_TOKENS` | No | Output token limit. Default `2200`. |
| `CRON_SECRET` | No | If set, `/api/cron/generate` requires a matching `X-Cron-Secret` header. If unset, the endpoint is open and logs a warning. |
| `RAILWAY_CRON_SCHEDULE` | No | Set by Railway cron services. When present, the process generates once and exits. |
| `PORT` | No | Listen port. Default `5000` for `python app.py`, `8080` for the Docker/gunicorn command. |
| `RAILWAY_URL` | No | Used only by `test_railway.py`. Default `http://localhost:5000`. |

A `.env` file in the project root is loaded with `python-dotenv`.

## API

| Route | Purpose |
|-------|---------|
| `GET /` | Minimal HTML page with a generate button |
| `GET, POST /api/generate` | Generate a newsletter, save it, return the HTML and id |
| `GET, POST /api/cron/generate` | Same as above, guarded by `CRON_SECRET`, returns the id without the HTML |
| `GET /api/newsletters` | List newsletter ids and creation dates, newest first |
| `GET /newsletter/<id>` | Raw HTML for one newsletter |
| `GET /health` | Status plus whether each API key is set |
| `POST /api/test-mcp` | Run one `web_search` or `news_search` query, report result count |
| `POST /api/test-search` | Run one of the four news passes, return the first three results |

## Deployment

The repo is set up for Railway. `railway.toml` selects the Dockerfile builder, which installs Python 3.11, Node 20, the Python requirements, and the Brave MCP server globally. Attach a PostgreSQL service and set the two API keys.

Scheduled generation has three options. `railway.toml` declares a cron schedule of `0 */5 * * *` running `cron.py`. A separate Railway cron service can run the same image, in which case the start command detects `RAILWAY_CRON_SCHEDULE` and generates instead of serving. Or an external scheduler can `POST /api/cron/generate` with the `X-Cron-Secret` header; see [CRON_SETUP.md](./CRON_SETUP.md) for a GitHub Actions example.

`Procfile` and `nixpacks.toml` are older alternatives to the Dockerfile and start the app with `python3 app.py`.

## Project layout

```
app.py                             Flask app: search passes, prompt, Claude call, Postgres storage, routes, cron entry
mcp_client.py                      Brave Search MCP client over stdio, with direct REST API fallback
cron.py                            Standalone cron entry that calls run_cron_generation() and exits
cron_endpoint.py                   Copy of the /api/cron/generate handler; not imported by app.py
generate_newsletter_original.py    Earlier standalone version of the generator, kept for reference
test_railway.py                    Smoke test against a running deployment
Dockerfile, railway.toml           Railway build and start configuration
Procfile, nixpacks.toml            Alternative Railway start configurations
CRON_SETUP.md                      Notes on scheduling generation
```

## Limitations

- Generation is one blocking request with no queue or job status. Gunicorn runs with a 180 second timeout for this reason.
- Market data is scraped from Brave search snippets with simple parsing, so values often come back as `N/A`. The prompt tells Claude to search for prices itself when that happens.
- The `/api/test-mcp` and `/api/test-search` routes and `/api/generate` have no authentication. Only the cron endpoint checks a secret, and only when `CRON_SECRET` is set.
- The `newsletters` table has `status`, `editor_notes` and `sent_at` columns, but this service only ever writes `draft`. Editing and sending happen in the frontend.
- The MCP server is spawned with `npx` on first use. If Node or the package is missing, every search silently falls back to the REST API.
- There is no test suite beyond the deployment smoke test.

## License

MIT.
