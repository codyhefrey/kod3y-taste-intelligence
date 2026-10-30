# Qloo Agentic Hackathon — Devpost preparation

**Contest:** https://qloo.devpost.com/  
**Deadline:** Friday, October 30, 2026, **11:45 PM Toronto (EDT)**  
**Project:** KOD3Y Taste Intelligence  
**Code:** https://github.com/codyhefrey/kod3y-taste-intelligence  
**Demo:** https://kod3y-taste-intelligence-demo.onrender.com — hosted interface confirmed by Render; real Qloo results need issued API key  
**License:** MIT (public standalone competition edition)

> Only submit a claim of functional Qloo integration after you successfully test your issued hackathon key. A no-key fallback screen does not satisfy the working Qloo application requirement.

## Project tagline

An explainable cultural discovery agent grounded in Qloo's taste graph.

## Draft description — edit to match verified live behavior

Recommendation systems often suggest familiar choices without showing how one cultural interest connects to another. KOD3Y Taste Intelligence lets a person enter up to three favorite cultural entities, such as a movie or artist, and ask a tool-using discovery workflow to explore movies, music and dining beyond their usual preferences.

The workflow validates the request, searches Qloo for actual entity IDs, feeds the verified IDs as taste signals into Qloo Insights, and returns category-specific recommendations. The interface displays the resolved interests, the origin of each recommendation, optional Qloo affinity scores where available, and a concise trace of the underlying API calls. A location filter can refine dining discovery without silently using the visitor's precise position.

Unlike a generic chatbot that invents suggestions, this application deliberately shows no recommendations when the API is unavailable or cannot resolve the user's input. Affinity scores are presented as matching signals, not probabilities.

The prototype is built using Python's standard library, accessible HTML/CSS/JavaScript, Qloo's Search and Insights APIs, GitHub Actions tests and a cloud-ready deployment blueprint.

### Technical workflow

1. Validate and parse up to three favorites.
2. Resolve real Qloo IDs via `GET /search`.
3. Plan and execute requests for one or more requested categories via `GET /v2/insights`.
4. Preserve provenance, available affinity evidence and auditable per-tool status.
5. Show errors, missing-key state or no-results without inventing recommendations.

### What makes Qloo essential

Qloo provides the entity graph and taste-based affinity data that connect one interest to otherwise unrelated cultural recommendations. Without the Qloo API, this application deliberately refuses to produce pretend recommendations. This is a deterministic agentic workflow, **not** a claim of an LLM autonomous agent.

### Intended users / impact

Travelers discovering new cultural experiences, curious viewers and listeners, and businesses looking to understand cross-category connections between customers' interests.

### Development during contest period

Created the KOD3Y Taste Intelligence standalone public demo, a server-side Qloo Search/Insights orchestration workflow, a results/evidence interface, mocked tests and deployment configuration in the eligible development period.

## Submission checklist

- [x] Public repository and MIT license
- [x] Multi-step agentic discovery code with documentation
- [x] Automated code tests
- [x] API key request form submitted October 29
- [ ] **Issued Qloo hackathon key received**
- [ ] **Live Qloo results verified against real API**
- [ ] Public website actually deployed and reachable
- [ ] Devpost description and real demo URL entered and submitted before deadline
- [ ] Check final rules, API authorization, and open-source licensing

**Qloo video note:** The official competition page expressly states demo videos are **not required**. Prioritize a truly working public website instead.

## Intellectual-property boundary

The contest's public repository is MIT open source. It does **not** include private KOD3Y T3CH code, secrets or proprietary datasets. Qloo event rules grant judging and promotional use rights for submitted materials; publishing under MIT grants public reuse rights for this specific code. Review before final submission.
