# AGENTS.md — SmartDesk AI

This file describes the architecture, decisions, and conventions for SmartDesk AI.
Read this before touching any code.

---

## What This Project Is

SmartDesk AI is an intelligent IT and HR helpdesk agent. It handles three flows:
1. **RAG** — answer employee questions from a company knowledge base
2. **Ticket Creation** — create Jira tickets when the KB cannot answer
3. **Ticket Status** — fetch status of previously created tickets

---

## Stack

| Component | Choice | Notes |
|---|---|---|
| Agent Framework | LangGraph | Subgraphs for IT/HR agents, MemorySaver for dev |
| LLM | GPT-4o | `gpt-4o` via OpenAI API |
| Embedding | OpenAI text-embedding-3-small | Same model for indexing AND querying |
| Vector DB | Qdrant | `docker run -p 6333:6333 qdrant/qdrant` |
| Retrieval | Hybrid (dense + BM25 + RRF) | cross-encoder/ms-marco-MiniLM-L-6-v2 re-ranker |
| Ticketing | Jira REST API | SQLite for email→ticket_id mapping |
| Evaluation | Ragas + LangSmith | Ragas for metrics, LangSmith for tracing |
| UI | Chainlit | `chainlit run app.py` |
| Cache | In-memory dict | Redis upgrade path for production |
| Long-term Memory | SQLite | Postgres upgrade path for production |

---

## Environment Variables (never hardcode)

```
OPENAI_API_KEY=
JIRA_BASE_URL=
JIRA_API_TOKEN=
JIRA_EMAIL=
JIRA_PROJECT_KEY=
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=true
QDRANT_HOST=localhost
QDRANT_PORT=6333
CONFIDENCE_THRESHOLD_IT=0.75
CONFIDENCE_THRESHOLD_HR=0.72
```

---

## Project Structure

```
smartdesk-ai/
├── app.py                    # Chainlit entry point
├── agent/
│   ├── orchestrator.py       # Top-level LangGraph graph
│   ├── intent_detector.py    # Classifies rag/ticket_create/ticket_status
│   ├── router.py             # Conditional edge function
│   ├── it_agent/
│   │   ├── graph.py          # IT subgraph
│   │   ├── tools.py          # search_kb (IT collection)
│   │   └── prompts.py        # IT system prompt
│   └── hr_agent/
│       ├── graph.py          # HR subgraph
│       ├── tools.py          # search_kb (HR collection)
│       └── prompts.py        # HR system prompt
├── tools/
│   ├── create_ticket.py      # Jira ticket creation with retry
│   └── get_ticket_status.py  # Jira status fetch
├── rag/
│   ├── indexer.py            # Chunk, embed, upsert to Qdrant
│   ├── retriever.py          # Hybrid search + RRF + re-ranker
│   └── confidence.py         # Hybrid gate logic
├── memory/
│   ├── session.py            # In-session dict management
│   └── longterm.py           # SQLite read/write
├── cache/
│   └── semantic_cache.py     # In-memory embedding cache
├── kb/
│   ├── it/                   # IT policy documents
│   └── hr/                   # HR policy documents
├── eval/
│   └── ragas_eval.py         # Evaluation pipeline
├── tests/
│   └── test_flows.py         # End-to-end flow tests
├── .env.example              # Template for environment variables
├── requirements.txt
└── README.md
```

---

## Core Conventions

### Tool naming
```python
@tool
def search_kb_it(query: str) -> str: ...
@tool
def search_kb_hr(query: str) -> str: ...
@tool
def create_ticket(email: str, summary: str, description: str, category: str, priority: str) -> str: ...
@tool
def get_ticket_status(email: str) -> str: ...
```

### Session memory shape
```python
session = {
    "email": str | None,           # validated email, session-level
    "current_state": str,          # FSM position
    "summary": str | None,         # flow-specific, cleared on new flow
    "description": str | None,     # flow-specific
    "category": str | None,        # inferred from conversation
    "priority": str | None,        # optional
    "last_activity": str,          # ISO timestamp for timeout
}
```

### State machine states
```
GREETING → COLLECTING_EMAIL → COLLECTING_SUMMARY → 
COLLECTING_DESCRIPTION → CONFIRMING → DONE
```

### Confidence gate (implement in confidence.py)
```python
def confidence_gate(query, domain):
    chunks, score = hybrid_search(query, domain)
    threshold = CONFIDENCE_THRESHOLD_IT if domain == "IT" else CONFIDENCE_THRESHOLD_HR
    if score < threshold:
        return None, "escalate"
    answer = llm_generate(chunks, query)
    if "don't have enough information" in answer.lower():
        return None, "escalate"
    return answer, "answer"
```

### Retry pattern for external APIs
```python
import time

def call_jira_with_retry(fn, *args, max_retries=3):
    for attempt in range(max_retries):
        try:
            return fn(*args)
        except JiraAPIError as e:
            if e.status_code == 503:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
                continue
            raise
    raise Exception("Jira unavailable after retries. Please try again later.")
```

---

## Retrieval Pipeline

```
User query
  → embed with text-embedding-3-small
  → dense search on Qdrant (IT or HR collection)
  → BM25 search on same collection
  → merge with RRF: score = 1/(rank_dense+60) + 1/(rank_bm25+60)
  → top 10 candidates to re-ranker
  → cross-encoder/ms-marco-MiniLM-L-6-v2 scores each pair
  → top 3 chunks passed to confidence gate
```

---

## HITL Requirements (mandatory per rubric)

Before calling `create_ticket`, the agent MUST:
1. Present full ticket draft: email, summary, description, category, priority
2. Wait for explicit "yes" confirmation
3. Allow field corrections at CONFIRMING state (backward transitions)
4. After creation: return ticket ID and confirmation message

---

## Evaluation (run before submission)

```bash
python eval/ragas_eval.py
```

Produces metrics: faithfulness, answer_relevance, context_precision
Target scores: faithfulness > 0.80, answer_relevance > 0.75
Include output in README under "Evaluation Results" section.

---

## Prerequisites

```bash
# 1. Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill environment variables
cp .env.example .env

# 4. Index the knowledge base
python rag/indexer.py

# 5. Run the agent
chainlit run app.py
```
