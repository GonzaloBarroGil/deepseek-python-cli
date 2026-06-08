# tests/test_cli.py
"""
Test suite for deepseek-cli
Validates against spec/deepseek-cli/v1.0.0.yml

Version: 1.0.1 - Fixed mocking architecture
Run with: python -m pytest tests/ -v
"""

import json
import os
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the class directly for unit testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from deepseek_cli import DeepSeekCLI


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_api_key(monkeypatch):
    """Set a fake API key in the environment."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-mock-key-12345")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for file-based tests."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def mock_success_response():
    """Standard mock API success response."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "deepseek-chat",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "This is a test response."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": 12,
            "total_tokens": 21
        }
    }


@pytest.fixture
def cli_args():
    """Base CLI arguments that all tests can modify."""
    return [
        "deepseek-cli",  # argv[0]
        "test prompt",   # positional prompt
    ]


# ---------------------------------------------------------------------------
# Helper: Run the CLI with mocked API and capture output
# ---------------------------------------------------------------------------

def run_cli_with_mock(cli_class, mock_response, monkeypatch, capsys, extra_args=None):
    """
    Run the CLI with a mocked requests.post.
    Returns (payload_sent_dict, exit_code).
    """
    extra_args = extra_args or []
    payload_sent = {}
    
    def mock_post(url, **kwargs):
        """Capture the payload and return a mock response."""
        if "json" in kwargs:
            payload_sent.update(kwargs["json"])
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_resp.iter_lines.return_value = []
        return mock_resp
    
    with patch("requests.post", side_effect=mock_post):
        try:
            cli = cli_class(argv=extra_args)
            cli.run()
        except SystemExit as e:
            return payload_sent, e.code
    
    return payload_sent, 0


# ---------------------------------------------------------------------------
# Spec: inputs - Prompt sources
# ---------------------------------------------------------------------------

class TestPromptSources:
    """Validates that prompts are accepted from all specified sources."""

    def test_prompt_from_positional_arg(self, mock_api_key, mock_success_response, monkeypatch, capsys):
        """deepseek-cli 'prompt text'"""
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["Explain quantum computing"]
        )
        
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "This is a test response." in captured.out
        assert payload["messages"][-1]["content"] == "Explain quantum computing"

    def test_prompt_from_flag(self, mock_api_key, mock_success_response, monkeypatch, capsys):
        """deepseek-cli --prompt 'prompt text'"""
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["--prompt", "Test prompt"]
        )
        
        assert exit_code == 0
        assert payload["messages"][-1]["content"] == "Test prompt"

    def test_prompt_from_stdin(self, mock_api_key, mock_success_response, monkeypatch):
        """echo 'prompt' | deepseek-cli"""
        payload_sent = {}
        
        def mock_post(url, **kwargs):
            if "json" in kwargs:
                payload_sent.update(kwargs["json"])
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_success_response
            return mock_resp
        
        # Simulate stdin
        monkeypatch.setattr("sys.stdin", StringIO("Prompt from stdin"))
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        
        with patch("requests.post", side_effect=mock_post):
            cli = DeepSeekCLI(argv=[])  # No args, prompt comes from stdin
            cli.run()
        
        assert payload_sent["messages"][-1]["content"] == "Prompt from stdin"

    def test_prompt_from_file(self, mock_api_key, mock_success_response, temp_dir, monkeypatch, capsys):
        """deepseek-cli --file path/to/prompt.txt"""
        prompt_file = temp_dir / "prompt.txt"
        prompt_file.write_text("Prompt from file")
        
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["--file", str(prompt_file)]
        )
        
        assert exit_code == 0
        assert payload["messages"][-1]["content"] == "Prompt from file"

    def test_missing_prompt_errors(self, mock_api_key, monkeypatch):
        """deepseek-cli with no prompt source should exit with code 1."""
        # Simulate non-TTY with empty input so stdin returns nothing
        monkeypatch.setattr("sys.stdin", StringIO(""))
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        
        with pytest.raises(SystemExit) as exc_info:
            DeepSeekCLI(argv=[])
        
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Spec: inputs - System message
# ---------------------------------------------------------------------------

class TestSystemMessage:
    """Validates --system flag behavior."""

    def test_system_message_inline(self, mock_api_key, mock_success_response, monkeypatch, capsys):
        """deepseek-cli --system 'You are helpful' 'prompt'"""
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["--system", "You are a helpful assistant", "test"]
        )
        
        assert exit_code == 0
        system_msg = payload["messages"][0]
        assert system_msg["role"] == "system"
        assert system_msg["content"] == "You are a helpful assistant"

    def test_system_message_from_file(self, mock_api_key, mock_success_response, temp_dir, monkeypatch, capsys):
        """deepseek-cli --system path/to/system.txt"""
        system_file = temp_dir / "system.txt"
        system_file.write_text("System instructions from file")
        
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["--system", str(system_file), "test"]
        )
        
        assert exit_code == 0
        assert payload["messages"][0]["content"] == "System instructions from file"


# ---------------------------------------------------------------------------
# Spec: determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    """Validates deterministic defaults per spec."""

    def test_temperature_defaults_to_zero(self, mock_api_key, mock_success_response, monkeypatch, capsys):
        """Temperature should be 0.0 by default."""
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["test"]
        )
        
        assert exit_code == 0
        assert payload["temperature"] == 0.0

    def test_seed_is_set(self, mock_api_key, mock_success_response, monkeypatch, capsys):
        """A fixed seed should be present in the payload."""
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["test"]
        )
        
        assert exit_code == 0
        assert "seed" in payload
        assert payload["seed"] == 42

    def test_temperature_can_be_overridden(self, mock_api_key, mock_success_response, monkeypatch, capsys):
        """User can override temperature."""
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["--temperature", "0.7", "test"]
        )
        
        assert exit_code == 0
        assert payload["temperature"] == 0.7


# ---------------------------------------------------------------------------
# Spec: structured output
# ---------------------------------------------------------------------------

class TestStructuredOutput:
    """Validates --json and --schema flags."""

    def test_json_mode_sets_response_format(self, mock_api_key, mock_success_response, monkeypatch, capsys):
        """--json should set response_format to json_object."""
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["--json", "test"]
        )
        
        assert exit_code == 0
        assert payload["response_format"]["type"] == "json_object"

    def test_schema_file_is_loaded(self, mock_api_key, mock_success_response, temp_dir, monkeypatch, capsys):
        """--schema should include JSON schema in the request."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }
        schema_file = temp_dir / "schema.json"
        schema_file.write_text(json.dumps(schema))
        
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["--json", "--schema", str(schema_file), "test"]
        )
        
        assert exit_code == 0
        assert "json_schema" in payload["response_format"]


# ---------------------------------------------------------------------------
# Spec: tool calling
# ---------------------------------------------------------------------------

class TestToolCalling:
    """Validates --tools flag."""

    def test_tools_file_is_loaded(self, mock_api_key, mock_success_response, temp_dir, monkeypatch, capsys):
        """--tools should include tool definitions in the request."""
        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }
            }
        }]
        tools_file = temp_dir / "tools.json"
        tools_file.write_text(json.dumps(tools))
        
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["--tools", str(tools_file), "test"]
        )
        
        assert exit_code == 0
        assert "tools" in payload
        assert payload["tools"][0]["function"]["name"] == "get_weather"

    def test_tool_calls_printed_as_json(self, mock_api_key, monkeypatch, capsys):
        """When response includes tool_calls, they should be printed as JSON."""
        tool_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "London"}'
                        }
                    }]
                }
            }]
        }
        
        def mock_post(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = tool_response
            return mock_resp
        
        with patch("requests.post", side_effect=mock_post):
            cli = DeepSeekCLI(argv=["test"])
            cli.run()
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output[0]["function"]["name"] == "get_weather"


# ---------------------------------------------------------------------------
# Spec: error handling - exit codes
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Validates error exit codes per spec."""

    def test_missing_api_key_exits_1(self, monkeypatch):
        """Missing API key should exit with code 1."""
        # Ensure no API key in environment
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        
        with pytest.raises(SystemExit) as exc_info:
            DeepSeekCLI(argv=["test"])
        
        assert exc_info.value.code == 1

    def test_api_error_exits_2(self, mock_api_key, monkeypatch):
        """API returning non-200 should exit with code 2."""
        def mock_post(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_resp.text = "Unauthorized"
            return mock_resp
        
        with patch("requests.post", side_effect=mock_post):
            with pytest.raises(SystemExit) as exc_info:
                cli = DeepSeekCLI(argv=["test"])
                cli.run()
        
        assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# Spec: version
# ---------------------------------------------------------------------------

class TestVersion:
    """Validates --version flag."""

    def test_version_output(self, capsys):
        """--version should print version and exit 0."""
        with patch("sys.argv", ["deepseek-cli", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                DeepSeekCLI()
        
        assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# Spec: verbose mode
# ---------------------------------------------------------------------------

class TestVerboseMode:
    """Validates --verbose flag outputs request/response to stderr."""

    def test_verbose_outputs_request(self, mock_api_key, mock_success_response, monkeypatch, capsys):
        """--verbose should print request details to stderr."""
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["--verbose", "test"]
        )
        
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "--- REQUEST ---" in captured.err
        assert "--- RESPONSE ---" in captured.err

    def test_normal_mode_no_debug_output(self, mock_api_key, mock_success_response, monkeypatch, capsys):
        """Without --verbose, stderr should be empty on success."""
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["test"]
        )
        
        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.err == ""


# ---------------------------------------------------------------------------
# Spec: model flag
# ---------------------------------------------------------------------------

class TestModelFlag:
    """Validates --model flag."""

    def test_default_model(self, mock_api_key, mock_success_response, monkeypatch, capsys):
        """Default model should be deepseek-chat."""
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["test"]
        )
        
        assert exit_code == 0
        assert payload["model"] == "deepseek-chat"

    def test_custom_model(self, mock_api_key, mock_success_response, monkeypatch, capsys):
        """--model should override the default."""
        payload, exit_code = run_cli_with_mock(
            DeepSeekCLI, mock_success_response, monkeypatch, capsys,
            extra_args=["--model", "deepseek-coder", "test"]
        )
        
        assert exit_code == 0
        assert payload["model"] == "deepseek-coder"