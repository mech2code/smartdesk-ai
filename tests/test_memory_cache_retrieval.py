from cache.semantic_cache import cache_clear, cache_lookup, cache_store
from memory.longterm import load_employee, merge_employee_memory, save_employee
from memory.session import new_session
from rag.indexer import _chunk_text, _point_id
from rag.retriever import _rrf_merge


def test_longterm_memory_round_trip_and_merge(tmp_path, monkeypatch):
    import memory.longterm as longterm

    monkeypatch.setattr(longterm, "DB_PATH", tmp_path / "longterm.db")
    save_employee(
        "user@example.com",
        {"department": "Engineering", "ticket_history": ["HELP-1"]},
    )
    stored = load_employee("user@example.com")
    active = new_session(email="user@example.com")
    active["ticket_history"] = ["HELP-2"]
    merged = merge_employee_memory(active, stored)
    assert merged["department"] == "Engineering"
    assert merged["ticket_history"] == ["HELP-1", "HELP-2"]
    assert merged["current_state"] == "GREETING"


def test_semantic_cache_is_domain_scoped(monkeypatch):
    import cache.semantic_cache as semantic_cache

    cache_clear()
    monkeypatch.setattr(semantic_cache, "_embed", lambda _: [1.0, 0.0])
    cache_store("reset password", "IT answer", domain="it")
    assert cache_lookup("password reset", domain="it") == "IT answer"
    assert cache_lookup("password reset", domain="hr") is None


def test_rrf_combines_shared_document_ids():
    merged = _rrf_merge(["doc-a", "doc-b"], ["doc-b", "doc-c"])
    assert merged[0] == "doc-b"
    assert set(merged) == {"doc-a", "doc-b", "doc-c"}


def test_index_chunks_and_ids_are_deterministic():
    text = "First paragraph.\n\nSecond paragraph."
    assert _chunk_text(text, "guide.md") == _chunk_text(text, "guide.md")
    assert _point_id("it", "guide.md", 0) == _point_id("it", "guide.md", 0)
    assert _point_id("it", "guide.md", 0) != _point_id("hr", "guide.md", 0)

