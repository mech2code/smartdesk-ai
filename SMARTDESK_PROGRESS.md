# SmartDesk AI — Capstone Mentoring Progress Log

## Status: ALL BLOCKS COMPLETE ✅
## Next Step: Implementation (see IMPLEMENTATION_PLAN.md)

---

## How to Resume
If starting a new conversation, upload this file and say:
> "I am continuing my SmartDesk AI capstone. All learning blocks are complete. Here is my progress log and architecture decisions. Help me with implementation."

---

## FINAL ARCHITECTURE DECISIONS

| Component | Decision | Reason |
|---|---|---|
| Agent Framework | LangGraph | Explicit state machine, subgraph multi-agent, first-class HITL, 90M monthly downloads |
| LLM Provider | GPT-4o | Strong instruction following, reliable tool-call JSON, 128k context window |
| Embedding Model | OpenAI text-embedding-3-small | Best retrieval quality for mixed IT+HR domain, 1,536 dimensions |
| Vector Database | Qdrant | Production-grade persistence, native metadata filtering, one-line Docker setup |
| Retrieval Strategy | Hybrid Search (dense+BM25+RRF) | BM25 wins exact terms, dense wins semantics, RRF merges — bonus marks in rubric |
| Re-ranker | cross-encoder/ms-marco-MiniLM-L-6-v2 | Free, local, 100-300ms CPU, purpose-built for passage ranking |
| Ticketing Platform | Jira + SQLite email mapping | Industry standard for IT helpdesk, SQLite maps email→[ticket_ids] |
| Evaluation | Ragas + LangSmith | Ragas = quantitative bonus marks, LangSmith = development tracing |
| UI | Chainlit | Purpose-built LLM chat UI, streaming, production-quality, deadline-friendly |
| Semantic Cache | In-memory dict → Redis | Cache RAG query-answer pairs, 2-4s latency savings per hit |
| Long-term Memory | SQLite → Postgres | Zero setup for capstone, Postgres upgrade path in README |
| Confidence Gate | Hybrid (score threshold + LLM self-assessment) | Score catches obvious misses cheaply, LLM catches subtle misses |

---

## Complete Knowledge Base (all concepts)

### Block 0 — How Agentic Systems Work
- **0a** Agent = decision loop driven by LLM reasoning (not memory, not multi-turn)
- **0b** Tool = RPC — LLM emits JSON, your code executes. 3 tools: search_kb, create_ticket, get_ticket_status
- **0c** Intent = classify WHY before doing anything. Ambiguity = ask, don't guess
- **0d** Orchestrator = stateful process managing full loop. Owns low-confidence decision
- **0e** Router = dumb switch (pure function, no memory). Fires ONCE at flow entry
- **0f** State machine = GREETING → COLLECTING_EMAIL → COLLECTING_SUMMARY → CONFIRMING → DONE
- **0g** Session memory = validated dict, injected every API call. Only validated data stored
- **0h** Context window = fixed token buffer, rebuilt every call. ~7,400 tokens per SmartDesk query
- **0i** Multi-agent = orchestrator + IT-agent + HR-agent. Only orchestrator knows both exist
- **0j** Chain (fixed) vs tool call (one RPC) vs agent loop (iterates on LLM decisions)

### Block 1 — The RAG Pipeline
- **1a** KB always wins over LLM training data. Zero chunks = escalate immediately
- **1b** Embedding = text → float vector. Same model for indexing AND querying — always
- **1c** Vector DB record = (vector + chunk text + metadata). Separate IT + HR collections
- **1d** Cosine similarity = angle between vectors. K = ceiling, threshold = quality floor. Both apply
- **1e** ~500 token chunks, 50-100 token overlap at boundaries. FAQ = one chunk. Guide = one chunk per section
- **1f** Pipeline: embed → hybrid search → threshold filter → re-rank → pass to LLM
- **1g** Grounding = system prompt instruction. Not automatic. Requires explicit "answer only from context"
- **1h** Threshold 0.70-0.75 default. Too high = loud failures (unnecessary escalation). Too low = silent hallucinations
- **1i** Escalation triggers: score < threshold OR zero chunks. Carry forward original query to pre-populate ticket
- **1j** Intent detector = single point of failure for all three flows simultaneously

### Block 2 — Architecture Choices
- **2a** LangGraph: nodes=functions, edges=transitions, subgraphs=sub-agents. MemorySaver (dev) → PostgresSaver (prod)
- **2b** GPT-4o: 128k window. 7,400 tokens per query = 5.8% of window
- **2c** text-embedding-3-small: 1,536 dims, 8,191 token limit. Switching = full re-index
- **2d** Qdrant: `docker run -p 6333:6333 qdrant/qdrant`. Native metadata filtering
- **2e** BM25 wins: exact rare terms. Dense wins: semantic/emotional. Cannot split by domain
- **2f** RRF: score = 1/(rank_dense+60) + 1/(rank_bm25+60). Drop-in for single search step
- **2g** Re-ranker: two-pass (hybrid: 500→10 candidates, re-ranker: 10→top 3). 100-300ms CPU
- **2h** Jira + SQLite {email:[ticket_ids]}. Exponential backoff on 503. Multi-server → Postgres
- **2i** Ragas: faithfulness (grounding), answer relevance, context precision. LangSmith: tracing
- **2j** Chainlit: streaming with cl.Message. Under 50 lines integration. Deadline-friendly
- **2k** Semantic cache: before RAG pipeline, threshold ~0.85, saves 2-4s per hit
- **2l** SQLite long-term memory: read on session start, write on session end. Postgres for multi-server

### Block 3 — Confidence & Escalation Design
- **3a** Threshold: empirical, per-domain, plot score distributions, find the gap. Monitor escalation rate weekly
- **3b** LLM self-assessment: "Answer ONLY from context. If insufficient, say I don't have enough information"
- **3c** Hybrid gate: score threshold (cheap, first) → LLM self-assessment (expensive, second). Both must pass
- **3d** HITL: fires at CONFIRMING state. Present full ticket draft. Wait for clean yes. Provide ticket ID after creation

---

## Hybrid Gate Pseudocode (implement exactly)
```python
chunks, score = hybrid_search(query)
if score < threshold:
    return escalate()
answer = llm_generate(chunks, query)  # system prompt enforces grounding
if "don't have enough information" in answer:
    return escalate()
return answer
```

## Session Memory Injection (inject on every API call)
```python
system_prompt = f"""
You are SmartDesk AI. Answer ONLY from the provided context.
If context is insufficient, say: "I don't have enough information 
about that in our knowledge base."
Do NOT use outside knowledge.

Current session context:
- Employee email: {session.get('email', 'not yet provided')}
- Current state: {session.get('current_state', 'GREETING')}
- Issue summary: {session.get('summary', 'not yet provided')}
"""
```

## State Machine (implement exactly)
```
GREETING → intent detected as ticket_create
COLLECTING_EMAIL → validate email format → store in session
COLLECTING_SUMMARY → store summary in session
COLLECTING_DESCRIPTION → store description in session  
CONFIRMING → present full ticket draft → wait for yes/no
  → yes: call create_ticket tool → transition to DONE
  → no/change: transition back to relevant collection state
DONE → return ticket ID → clear flow-specific session fields
```
