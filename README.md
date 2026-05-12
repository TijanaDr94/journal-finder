# MDPI Journal finder service

A REST API that ranks MDPI journals for a given title and abstract of a manuscript.

## Supported Journals

| Journal | Scope page   | Domain                         |
|---|---|--------------------------------|
| [Molecules](https://www.mdpi.com/journal/molecules) | https://www.mdpi.com/journal/molecules/about#Scope | Chemistry   |
| [AI](https://www.mdpi.com/journal/ai) | https://www.mdpi.com/journal/ai/about#Scope | Machine learning, NLP, computer vision |
| [Physics](https://www.mdpi.com/journal/physics) | https://www.mdpi.com/journal/physics/about#Scope | Theoretical and experimental physics |
| [Energies](https://www.mdpi.com/journal/energies) | https://www.mdpi.com/journal/energies/about#Scope | Renewable energy  |


## How to run code

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

### Local (requires Python 3.11+ and uv)

```bash
uv sync
uv run uvicorn app.main:app --reload
```

The service starts at **http://localhost:8000**.
Docs with endpoints: **http://localhost:8000/docs**
