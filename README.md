# KOD3Y Taste Intelligence

An experimental cross-category cultural discovery app for the **2026 Qloo Agentic Hackathon**, developed under KOD3Y T3CH.

## Run locally

Requires Python 3.10+ (standard library only).

```powershell
py app.py
```

Open http://127.0.0.1:8787

Without a key, the app displays an explicit pending-key status. After receiving your individual hackathon key, **set it only locally** in the VS Code PowerShell terminal:

```powershell
$env:QLOO_API_KEY = Read-Host "Paste your Qloo API key"
py app.py
```

Do **not** screenshot the terminal while entering a key, put the key in a source file, or publish it to GitHub.

## How the Qloo integration works

- Server-only GET `https://hackathon.api.qloo.com/search?query=...&take=8` resolves a named interest into a real Qloo entity ID.
- Server-only GET `https://hackathon.api.qloo.com/v2/insights` uses `signal.interests.entities` and `filter.type` to recommend dining, music, or movie entities.
- Server uses `X-Api-Key` header; the browser receives only filtered names/descriptions/entity IDs, never credentials.
- Invalid, unauthorized or missing-key responses are shown clearly instead of fabricated output.

The implementation was written from Qloo's published API reference, **but has not yet been live-tested with an issued API key**. Search matching may need refinement after live testing; a named movie/artist/restaurant works better than a vague theme.

## Tests

```powershell
py -m unittest discover -v
```

## Remaining work

Test with real credentials, improve disambiguation and agent planning, deploy a live URL, record a demo and submit through Devpost. No public deployment or final submission has been performed.

## License

MIT. Copyright (c) 2026 codyhefrey. Any proprietary KOD3Y T3CH components should remain outside this public MIT repository.

See [PROJECT_STATUS.md](PROJECT_STATUS.md).
