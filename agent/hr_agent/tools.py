from langchain_core.tools import tool
from rag.retriever import hybrid_search


@tool
def search_kb_hr(query: str) -> str:
    """Search the HR knowledge base for answers about benefits, leave, payroll, remote work, and company policies."""
    chunks, score = hybrid_search(query, domain="hr")
    if not chunks:
        return "No relevant information found in the HR knowledge base."
    return f"[Confidence score: {score:.3f}]\n\n" + "\n\n---\n\n".join(chunks)
