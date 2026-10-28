# KOD3Y Taste Intelligence

A transparent early-stage cultural discovery web prototype for the Qloo Agentic Hackathon, developed under KOD3Y T3CH.

## Run locally

Requires Python 3.10+ (standard library only).

```powershell
py app.py
```

Open http://127.0.0.1:8787

## Tests

```powershell
py -m unittest discover -v
```

## Integration status

The user interface and local API work. **Real Qloo insights are NOT integrated yet.** The app intentionally returns an explicit integration status instead of fabricated recommendations. `QLOO_API_KEY` is read from the environment, but a key alone does not enable live calls: the Qloo entity resolution and insights flow still needs implementation and testing.

Never commit API keys, payment details, or secrets. This is not yet a valid final hackathon submission. See [PROJECT_STATUS.md](PROJECT_STATUS.md).

## License

MIT. Copyright (c) 2026 codyhefrey.
