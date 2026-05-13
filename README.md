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

The service uses a two-step hybrid scoring approach:

BM25 – a fast keyword-based search model that compares the input text with each journal’s scope description.
It is fast and free and doesn't require API key.

LLM reranking (optional) - if an OpenAI API key is provided, the service uses gpt-4o-mini to improve the ranking by
understanding meaning and context, not just exact keywords. It is better at handling synonyms, paraphrasing, and 
domain-specific language. It returns scores and a short explanation for each journal but adds some latency and API cost.

To reduce repeated API calls and costs, responses are cached in memory (LRU cache), so identical requests can reuse 
previous results.

Conclusion:
BM25 is fast and reliable, but it can miss matches when different wording is used.
LLM reranking is usually more accurate because it understands context, but it is slower, costs money, and can produce 
slightly different outputs between runs (reduced by using temperature=0).

This hybrid design ensures the service always works, even without an API key, while providing better results when
LLM support is enabled.


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