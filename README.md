# KOD3Y Taste Intelligence

**A grounded cross-category discovery agent** for the 2026 Qloo Agentic Hackathon, developed under KOD3Y T3CH.

The user enters one to three **named** favorites (movies, musicians, restaurants); the agent orchestrates real entity resolution through Qloo Search, then Qloo Insights recommendations across music, film and/or dining. The UI shows the resolved seeds, the Qloo response records and the exact tool steps used. Results are **never fabricated**.

## What is built

- Responsive interactive discovery website and Python standard-library API
- Three-step Qloo agent tool workflow: interpret input, resolve named entities, query relevant Insights categories and attach trace
- Optional dining region field, passed to Qloo as `filter.location.query`
- Explainability requested via `feature.explainability=true`; displayed numeric affinities only when Qloo returns them
- Explicit status if Qloo credentials are missing, rejected or rate limited
- Unit tests that mock Qloo calls without credentials
- GitHub Actions CI checks and Render deployment blueprint

**Crucial:** The developer submitted the Qloo key-request form on October 29, 2026 and a key had not yet been observed in Gmail. The implementation was built against official docs, but **not live-tested with a real issued Qloo key**. Thus there is no proof this is a functional final hackathon entry yet.

## Start locally (Windows PowerShell)

```powershell
git clone https://github.com/codyhefrey/kod3y-taste-intelligence.git
cd kod3y-taste-intelligence
py -m unittest discover -v
py app.py
```

Open http://127.0.0.1:8787. The page loads without a key and displays a transparent pending-access message instead of simulated cultural picks.

When Qloo emails a hackathon key, store it in the **server environment only**:

```powershell
$env:QLOO_API_KEY = Read-Host "Paste your issued Qloo API key"
py app.py
```

Never paste an API key into this repository, public chat, screenshots, Devpost or browser JavaScript. Do not expose it through URL query strings. In a hosting dashboard, use a secret environment variable.

## Qloo API design

Base: `https://hackathon.api.qloo.com`

1. GET `/search` with `query=<name>&take=10`. The server selects an actual Qloo entity UUID from the returned results (rather than inventing an ID).
2. GET `/v2/insights` with `filter.type`, `signal.interests.entities=<comma separated UUIDs>`, `filter.exclude.entities`, `feature.explainability=true`, and `take`.
3. For dining, optional `filter.location.query` scopes the results. The server returns a filtered list of category-specific entities and a tool trace.

`X-Api-Key` is sent **only** from the server to Qloo. Exact compatibility needs confirmation with the assigned key. Qloo scores indicate affinity, not percentages or probabilities. The labels "agent" and "AI" describe the tool-orchestration workflow; this version does not run an autonomous third-party LLM.

## Tests

```powershell
py -m unittest discover -s . -p 'test_*.py' -v
```

See the [GitHub Actions tab](https://github.com/codyhefrey/kod3y-taste-intelligence/actions) for the latest CI status.

## Public hosting

`render.yaml` configures a free-tier Python service, the `/api/health` endpoint and a **private** `QLOO_API_KEY` environment variable. No live demo has been deployed or verified through this repository change. A localhost address is **not** acceptable as the competition's public demo URL.

## Hackathon requirements and ownership

Submission deadline: **October 30, 2026, 11:45 PM Toronto time (EDT)**. Required: real Qloo-integrated agentic app, public functional demo, public open-source repository, descriptive project text. **Qloo does not require a demo video.** Keep the working demo accessible during the judging window.

See [SUBMISSION.md](SUBMISSION.md) for the final Devpost draft and checklists. The public files are MIT-licensed; private KOD3Y T3CH source is not included.

## License

MIT. Copyright (c) 2026 codyhefrey. Third-party API access and data remain subject to Qloo's applicable terms.
