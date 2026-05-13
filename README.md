# MDPI Journal finder service

A REST API that ranks MDPI journals for a given title and abstract of a manuscript.

## What it does

Researchers submitting a paper often need to identify which journal best fits their work. This service automates that 
decision: send a manuscript title and abstract, get back a ranked list of four MDPI journals with relevance scores.

## Supported Journals

| Journal | Scope page   | Domain                         |
|---|---|--------------------------------|
| [Molecules](https://www.mdpi.com/journal/molecules) | https://www.mdpi.com/journal/molecules/about#Scope | Chemistry   |
| [AI](https://www.mdpi.com/journal/ai) | https://www.mdpi.com/journal/ai/about#Scope | Machine learning, NLP, computer vision |
| [Physics](https://www.mdpi.com/journal/physics) | https://www.mdpi.com/journal/physics/about#Scope | Theoretical and experimental physics |
| [Energies](https://www.mdpi.com/journal/energies) | https://www.mdpi.com/journal/energies/about#Scope | Renewable energy  |


## Approach

The service supports three scoring modes, selected via `SCORING_MODE`:

BM25 - a fast keyword-based search model that compares the input text with each journal’s scope description.
It is fast and free and doesn't require API key.
The title and abstract are tokenized and compared against each journal’s scope and keyword list using BM25. 
A simple keyword overlap score is also added to improve results when important terms appear directly in the text.
BM25 handles general text matching, while the keyword overlap helps with important domain specific terms.

```
bm25_final = 0.6 × bm25_norm + 0.4 × keyword_overlap_norm
```

LLM (with BM25 fallback) - if an OpenAI API key is provided, the service uses gpt-4o-mini to improve the ranking by
understanding meaning and context, not just exact keywords. It is better at handling synonyms, paraphrasing, and 
domain-specific language. It returns scores and a short explanation for each journal but adds some latency and API cost.
To reduce repeated API calls and costs, responses are cached in memory (LRU cache), so identical requests can reuse 
previous results. If the LLM call fails (network error, quota exceeded, no key configured), the service falls back to
BM25 and logs a warning.


Hybrid (BM25 + LLM blend) 
If an `OPENAI_API_KEY` is configured, the LLM also runs and two scores (BM25 and LLM) are then linearly blended:

```
final_score = HYBRID_ALPHA × bm25_score + (1 − HYBRID_ALPHA) × llm_score
```

Conclusion:
BM25 is fast and reliable, but it can miss matches when different wording is used.
LLM reranking is usually more accurate because it understands context, but it is slower, costs money, and can produce 
slightly different outputs between runs (reduced by using temperature=0).
The hybrid design avoids the main weaknesses of each approach alone.

Alternative approaches that were not considered in this project:
- Embedding models (like sentence-transformers) are better at understanding meaning and synonyms, but requires downloading
a large model and adds unnecessary complexity for only 4 journals.
- Fine-tuned classifier could give the best results, but needs a large labelled dataset of papers and journals

Future improvements:
The BM25 stage was intentionally kept simple because the LLM reranker already handles most semantic understanding. If 
the system needed to scale further or work without an LLM, the next improvements would include better text normalization
(stemming or lemmatization), weighted keywords, improved score normalization, and embedding-based retrieval for better
semantic matching.

## How to run code

### Local (requires Python 3.11+ and uv)

```bash
uv sync
uv run uvicorn app.main:app --reload
```

### Docker Compose

```bash
# Without LLM reranking (BM25 only, no API key needed)
docker compose up --build

# With LLM reranking (better results)
OPENAI_API_KEY=sk-... 
docker compose up --build
```

### Docker run

```bash
docker build -t journal-finder:latest .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... journal-finder:latest
```

The service starts at **http://localhost:8000**.
Docs with endpoints: **http://localhost:8000/docs**


## Running Tests

```bash
uv run pytest tests/ -v
```

## Environment Variables

| Variable | Default | Description                                            |
|---|---|--------------------------------------------------------|
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key (Optional) - omit to use BM25-only mode. |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model used for reranking.                       |
| `SCORING_MODE` | `hybrid` | `hybrid` \| `bm25` \| `llm`      |
| `CORS_ORIGINS` | `*` | Comma-separated list of allowed CORS origins.          |


## API

### `POST /find-journal`

Rank journals

**Request**

```json
{
  "title": "Manuscript title.",
  "abstract": "Plain text abstract of the manuscript."
}
```

**Response**

```json
{
  "ranked_journals": [
    {
      "journal_id": "ai",
      "journal_name": "AI",
      "issn": "2673-2688",
      "url": "https://www.mdpi.com/journal/ai",
      "score": 1,
      "rank": 1,
      "reasoning": "The manuscript focuses on machine learning models, which aligns perfectly with the scope of the AI journal that emphasizes artificial intelligence applications and techniques."
    },
    {
      "journal_id": "molecules",
      "journal_name": "Molecules",
      "issn": "1420-3049",
      "url": "https://www.mdpi.com/journal/molecules",
      "score": 0.2857,
      "rank": 2,
      "reasoning": "While the manuscript discusses predictive modeling, it does not primarily focus on chemistry or related disciplines, making it a poor fit for Molecules."
    },
    {
      "journal_id": "energies",
      "journal_name": "Energies",
      "issn": "1996-1073",
      "url": "https://www.mdpi.com/journal/energies",
      "score": 0.2143,
      "rank": 3,
      "reasoning": "The manuscript's focus on liver failure prediction does not align with the energy-related topics covered by Energies, resulting in a low relevance score."
    },
    {
      "journal_id": "physics",
      "journal_name": "Physics",
      "issn": "2624-8174",
      "url": "https://www.mdpi.com/journal/physics",
      "score": 0,
      "rank": 4,
      "reasoning": "The content of the manuscript is unrelated to the field of physics, which focuses on fundamental studies and technologies, leading to a very low fit."
    }
  ],
  "scoring_method": "hybrid",
  "model_used": "gpt-4o-mini"
}
```

- `score` - normalised relevance in [0, 1] (higher = better fit)
- `rank` - 1-based position (1 = best match)
- `reasoning` - present only when LLM scoring was used
- `scoring_method` - `"bm25"`, `"llm"`, or `"hybrid"`

Every response (in response header) also includes:
- `Request-ID` - server-generated UUID (or from request) for log correlation
- `Process-Time` - server-side processing time in seconds (float)


Example:
```bash
access-control-allow-origin: * 
content-length: 1312 
content-type: application/json 
date: Wed,11 May 2026 09:40:50 GMT 
process-time: 3.6358 
request-id: 96ca3493-6d03-452f-8875-b157620fb544 
server: uvicorn 
```

### `GET /health`

Liveness probe, returns `{"status": "ok", "version": "..."}`.

### `GET /config`

Returns scoring configuration

### `GET /docs`

Swagger UI with interactive endpoints


## Test json files from `examples/` folder

The `examples/` directory contains real example requests. All manuscripts are real published papers sourced 
from [mdpi.com](https://www.mdpi.com/).

| File             | Manuscript | Expected top journal |
|------------------|---|---|
| `ai.json`        | ML models for predicting post-hepatectomy liver failure | AI |
| `molecules.json` | Molecular dynamics modeling of iron oxides | Molecules |
| `physics.json`   | Transverse dynamics of strange hadrons in heavy-ion collisions | Physics |
| `energies.json`  | Determinants of energy consumption in South Africa (ARDL model) | Energies |


Results:

All three scoring modes correctly rank the expected journal first across all 4 examples.

**BM25** (`SCORING_MODE=bm25`) produces sensible rankings with no API key required. 
Notes:
- The Physics paper scores Energies very close behind (0.901 vs 1.0), because of the lexical overlap between the two 
scope descriptions. BM25 cannot distinguish physical from energetic context.
- The Molecules paper scores Physics second at 0.659, which is understandable given the use of physics terminology in
the abstract.

**LLM** (`SCORING_MODE=llm`) produces more differentiated scores using semantic understanding. The LLM correctly 
separates relevant from irrelevant journals, for example, the Physics paper drops Energies to 0.20 (from 0.901 in BM25).
Reasoning explanations are included per journal, making the ranking interpretable.

**Hybrid** (`SCORING_MODE=hybrid`, 30% BM25 + 70% LLM) combines keyword-based scoring with LLM reasoning for more 
balanced results. BM25 gives a fast and stable baseline, while the LLM improves semantic understanding and handles 
synonyms better. Scores can differ from pure LLM mode because the BM25 signal still influences the final ranking. 
For example, in the Physics paper example, Energies receives a higher score due to keyword overlap with the 
journal scope.
