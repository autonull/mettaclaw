import pytest
import os
import json
import lib_llm_ext

# Ensure chromadb functions return mock values to avoid loading chroma db in pure unit tests
@pytest.fixture(autouse=True)
def mock_chroma(monkeypatch):
    monkeypatch.setattr(lib_llm_ext._memory_manager, "chroma_available", False)

def test_generate_response_mocked(monkeypatch):
    def mock_completion(model, messages, max_tokens):
        class MockChoice:
            class MockMessage:
                content = f"Mocked response from {model}"
            message = MockMessage()
        class MockResp:
            choices = [MockChoice()]
        return MockResp()

    monkeypatch.setattr(lib_llm_ext.litellm, "completion", mock_completion, raising=False)
    monkeypatch.setattr(lib_llm_ext, "LITELLM_AVAILABLE", True)

    resp = lib_llm_ext.generate_response("gpt-4o", "Hello")
    assert resp == "Mocked response from gpt-4o"

    # Test ollama prefixing
    resp_ollama = lib_llm_ext.generate_response("llama3", "Hello")
    assert resp_ollama == "Mocked response from ollama/llama3"

def test_clean_response():
    assert lib_llm_ext._clean("test _quote_string_quote_") == 'test "string"'
    assert lib_llm_ext._clean(None) == ""

def test_zero_embedding():
    emb = lib_llm_ext._zero_embedding(5)
    assert len(emb) == 5
    assert emb == [0.0, 0.0, 0.0, 0.0, 0.0]

def test_query_no_chroma():
    # Because of mock_chroma fixture, this should fail gracefully
    resp = lib_llm_ext.query_memories("test")
    assert "ChromaDB not available" in resp

def test_remember_no_chroma():
    resp = lib_llm_ext.remember("test memory", "time")
    assert "ChromaDB not available" in resp

def test_memory_manager_mock_chroma(monkeypatch):
    mgr = lib_llm_ext.MemoryManager()
    # It should correctly identify chroma is missing
    assert mgr.chroma_available is False

    assert mgr.is_initialized() is False
    assert "ChromaDB not available" in mgr.remember("text", "time")
    assert "ChromaDB not available" in mgr.query("query")
