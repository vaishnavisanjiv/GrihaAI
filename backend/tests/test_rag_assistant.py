from app.services.rag_service import retrieve_knowledge
from app.services.assistant_service import build_assistant_response


def test_retrieve_knowledge_returns_matching_clauses():
    results = retrieve_knowledge("door exit width fire safety")
    assert results
    assert any("exit" in item["title"].lower() or "exit" in item["text"].lower() for item in results)


def test_assistant_response_includes_rag_evidence():
    response = build_assistant_response(
        db=None,
        question="What is the main fire exit risk?",
        analysis_id=None,
    )
    assert "answer" in response
    assert "evidence" in response
