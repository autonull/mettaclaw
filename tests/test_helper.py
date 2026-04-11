import pytest
import os
import tempfile
from datetime import datetime
import src.helper as helper

def test_extract_timestamp():
    # Valid timestamp
    ts = helper.extract_timestamp('("2023-10-27 14:32:10" (remember "foo"))')
    assert ts == datetime(2023, 10, 27, 14, 32, 10)

    # Invalid formats
    assert helper.extract_timestamp("no timestamp here") is None
    assert helper.extract_timestamp('("2023-10-27" (remember "foo"))') is None

def test_extract_commands():
    # Single command
    res = helper._extract_commands('(send "hello")')
    assert res == ['(send "hello")']

    # Multiple commands side-by-side
    res = helper._extract_commands('(send "hello") (query "test")')
    assert res == ['(send "hello")', '(query "test")']

    # Nested with extra whitespace
    res = helper._extract_commands('  (  send  (query "test") )  ')
    assert res == ['(  send  (query "test") )']

    # Double parens unwrapping
    res = helper._extract_commands('((send "hello"))')
    assert res == ['(send "hello")']

    # Triple parens unwrapping
    res = helper._extract_commands('(((send "hello")))')
    assert res == ['(send "hello")']

def test_balance_parentheses():
    # Regular LLM list output
    assert helper.balance_parentheses('((send "hi") (query "topic"))') == '((send "hi") (query "topic"))'

    # Two disjoint commands
    assert helper.balance_parentheses('(send "hi") (query "topic")') == '((send "hi") (query "topic"))'

    # Unwrapped single command
    assert helper.balance_parentheses('(send "hi")') == '((send "hi"))'

    # Markdown explanation garbage
    assert helper.balance_parentheses('Sure, here is the command: (send "hi")') == '((pin "Sure, here is the command:") (send "hi"))'

    # Empty string
    assert helper.balance_parentheses('') == '((send "Error: empty response"))'

    # Garbage string without parens
    assert helper.balance_parentheses('no commands here') == '((send "no commands here"))'

def test_clean_response():
    assert helper.clean_response("hello _quote_world_quote_ and _apostrophe_friend_apostrophe_") == 'hello "world" and \'friend\''
    assert helper.clean_response(None) == ""

def test_summarize_errors():
    assert helper.summarize_errors(None) == ""
    assert helper.summarize_errors([]) == ""

    # Simulation of MeTTa error list
    err_list = "((MULTI_COMMAND_FAILURE ...) (SINGLE_COMMAND_FORMAT_ERROR (query ...)) (SINGLE_COMMAND_FORMAT_ERROR (send ...)))"
    summary = helper.summarize_errors(err_list)
    assert "MULTI_COMMAND_FAILURE x1" in summary
    assert "SINGLE_COMMAND_FORMAT_ERROR x2" in summary
    assert "(query ...)" in summary

def test_file_operations():
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test.txt")
        assert helper.file_exists(filepath) == False

        # Write
        assert helper.write_file(filepath, "hello world") == True
        assert helper.file_exists(filepath) == True

        with open(filepath, "r") as f:
            assert f.read() == "hello world"

def test_clean_irc_message():
    assert helper.clean_irc_message("jules: hello there") == "hello there"
    assert helper.clean_irc_message("jules:hello there") == "jules:hello there" # Missing space after colon
    assert helper.clean_irc_message("hello there") == "hello there"
    assert helper.clean_irc_message(None) is None

def test_get_llm_model(monkeypatch):
    # Test fallback
    monkeypatch.delenv("OLLAMA_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert helper.get_llm_model() == "llama3"

    # Test OpenAI
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert helper.get_llm_model() == "gpt-4o"
    monkeypatch.setenv("OPENAI_MODEL", "gpt-3.5-turbo")
    assert helper.get_llm_model() == "gpt-3.5-turbo"
    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.delenv("OPENAI_MODEL")

    # Test Ollama
    monkeypatch.setenv("OLLAMA_API_BASE", "http://localhost:11434")
    assert helper.get_llm_model() == "ollama/llama3"
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1")
    assert helper.get_llm_model() == "ollama/llama3.1"
    monkeypatch.setenv("OLLAMA_MODEL", "ollama/llama3.2")
    assert helper.get_llm_model() == "ollama/llama3.2"
    monkeypatch.delenv("OLLAMA_API_BASE")
    monkeypatch.delenv("OLLAMA_MODEL")

    # Test Anthropic
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert helper.get_llm_model() == "claude-3-5-sonnet-20241022"
    monkeypatch.delenv("ANTHROPIC_API_KEY")

    # Test Groq
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    assert helper.get_llm_model() == "groq/llama-3.3-70b-versatile"
