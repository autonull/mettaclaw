import pytest
import os
import tempfile
from datetime import datetime
import src.helper as helper

def test_get_provider_env_vars(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-123")
    assert helper.get_provider() == "OpenAI"

    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-123")
    assert helper.get_provider() == "Anthropic"

    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert helper.get_provider() == "Ollama"

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
