from langchain_core.tools import tool
from rag.retriever import hybrid_search


@tool
def search_kb_it(query: str) -> str:
    """Search the IT knowledge base for answers about VPN, passwords, MFA, software, email, and Wi-Fi."""
    chunks, score = hybrid_search(query, domain="it")
    if not chunks:
        return "No relevant information found in the IT knowledge base."
    return f"[Confidence score: {score:.3f}]\n\n" + "\n\n---\n\n".join(chunks)
