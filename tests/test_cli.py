# tests/test_cli.py
"""
Test suite for deepseek-cli
Validates against spec/deepseek-cli/v1.0.0.yml

Run with: python -m pytest tests/ -v
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Path to the CLI script
CLI_PATH = Path(__file__).parent.parent / "src" / "deepseek_cli.py"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_api_key():
    """Set a fake API key in the environment for tests that need one."""
    old_key = os.environ.get("DEEPSEEK_API_KEY")
    os.environ["DEEPSEEK_API_KEY"] = "sk-test-mock-key-12345"
    yield
    if old_key:
        os.environ["DEEPSEEK_API_KEY"] = old_key
    else:
        del os.environ["DEEPSEEK_API_KEY"]


@pytest.fixture
def temp_dir():
    """Create a temporary directory for file-based tests."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def mock_response():
    """Standard mock API response."""
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


# ---------------------------------------------------------------------------
# Spec: inputs - Prompt sources
# ---------------------------------------------------------------------------

class TestPromptSources:
    """Validates that prompts are accepted from all specified sources."""

    def test_prompt_from_positional_arg(self, mock_api_key, mock_response):
        """deepseek-cli 'prompt text'"""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = subprocess.run(
                [sys.executable, str(CLI_PATH), "Explain quantum computing"],
                capture_output=True, text=True, timeout=30
            )
            
            assert result.returncode == 0
            assert "This is a test response." in result.stdout

    def test_prompt_from_flag(self, mock_api_key, mock_response):
        """deepseek-cli --prompt 'prompt text'"""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = subprocess.run(
                [sys.executable, str(CLI_PATH), "--prompt", "Test prompt"],
                capture_output=True, text=True, timeout=30
            )
            
            assert result.returncode == 0
            args, kwargs = mock_post.call_args
            payload = json.loads(kwargs["json"]) if "json" in kwargs else json.loads(args[1])
            assert payload["messages"][-1]["content"] == "Test prompt"

    def test_prompt_from_stdin(self, mock_api_key, mock_response):
        """echo 'prompt' | deepseek-cli"""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = subprocess.run(
                [sys.executable, str(CLI_PATH)],
                input="Prompt from stdin",
                capture_output=True, text=True, timeout=30
            )
            
            assert result.returncode == 0
            assert "This is a test response." in result.stdout

    def test_prompt_from_file(self, mock_api_key, mock_response, temp_dir):
        """deepseek-cli --file path/to/prompt.txt"""
        prompt_file = temp_dir / "prompt.txt"
        prompt_file.write_text("Prompt from file")
        
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = subprocess.run(
                [sys.executable, str(CLI_PATH), "--file", str(prompt_file)],
                capture_output=True, text=True, timeout=30
            )
            
            assert result.returncode == 0

    def test_missing_prompt_errors(self, mock_api_key):
        """deepseek-cli with no prompt source should exit with code 1."""
        # Need to pass something to avoid stdin blocking
        result = subprocess.run(
            [sys.executable, str(CLI_PATH)],
            input="",  # Empty stdin, not a TTY
            capture_output=True, text=True, timeout=30
        )
        
        assert result.returncode == 1
        assert "ERROR" in result.stderr


# ---------------------------------------------------------------------------
# Spec: inputs - System message
# ---------------------------------------------------------------------------

class TestSystemMessage:
    """Validates --system flag behavior."""

    def test_system_message_inline(self, mock_api_key, mock_response):
        """deepseek-cli --system 'You are helpful' 'prompt'"""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = subprocess.run(
                [sys.executable, str(CLI_PATH), "--system", "You are a helpful assistant", "test"],
                capture_output=True, text=True, timeout=30
            )
            
            assert result.returncode == 0
            args, kwargs = mock_post.call_args
            payload = json.loads(kwargs["json"]) if "json" in kwargs else json.loads(args[1])
            system_msg = payload["messages"][0]
            assert system_msg["role"] == "system"
            assert system_msg["content"] == "You are a helpful assistant"

    def test_system_message_from_file(self, mock_api_key, mock_response, temp_dir):
        """deepseek-cli --system path/to/system.txt"""
        system_file = temp_dir / "system.txt"
        system_file.write_text("System instructions from file")
        
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = subprocess.run(
                [sys.executable, str(CLI_PATH), "--system", str(system_file), "test"],
                capture_output=True, text=True, timeout=30
            )
            
            assert result.returncode == 0
            args, kwargs = mock_post.call_args
            payload = json.loads(kwargs["json"]) if "json" in kwargs else json.loads(args[1])
            assert payload["messages"][0]["content"] == "System instructions from file"


# ---------------------------------------------------------------------------
# Spec: determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    """Validates deterministic defaults per spec."""

    def test_temperature_defaults_to_zero(self, mock_api_key, mock_response):
        """Temperature should be 0.0 by default."""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            subprocess.run(
                [sys.executable, str(CLI_PATH), "test"],
                capture_output=True, text=True, timeout=30
            )
            
            args, kwargs = mock_post.call_args
            payload = json.loads(kwargs["json"]) if "json" in kwargs else json.loads(args[1])
            assert payload["temperature"] == 0.0

    def test_seed_is_set(self, mock_api_key, mock_response):
        """A fixed seed should be present in the payload."""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            subprocess.run(
                [sys.executable, str(CLI_PATH), "test"],
                capture_output=True, text=True, timeout=30
            )
            
            args, kwargs = mock_post.call_args
            payload = json.loads(kwargs["json"]) if "json" in kwargs else json.loads(args[1])
            assert "seed" in payload
            assert payload["seed"] == 42

    def test_temperature_can_be_overridden(self, mock_api_key, mock_response):
        """User can override temperature."""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            subprocess.run(
                [sys.executable, str(CLI_PATH), "--temperature", "0.7", "test"],
                capture_output=True, text=True, timeout=30
            )
            
            args, kwargs = mock_post.call_args
            payload = json.loads(kwargs["json"]) if "json" in kwargs else json.loads(args[1])
            assert payload["temperature"] == 0.7


# ---------------------------------------------------------------------------
# Spec: structured output
# ---------------------------------------------------------------------------

class TestStructuredOutput:
    """Validates --json and --schema flags."""

    def test_json_mode_sets_response_format(self, mock_api_key, mock_response):
        """--json should set response_format to json_object."""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "choices": [{"message": {"content": '{"key": "value"}'}}]
            }
            
            subprocess.run(
                [sys.executable, str(CLI_PATH), "--json", "test"],
                capture_output=True, text=True, timeout=30
            )
            
            args, kwargs = mock_post.call_args
            payload = json.loads(kwargs["json"]) if "json" in kwargs else json.loads(args[1])
            assert payload["response_format"]["type"] == "json_object"

    def test_schema_file_is_loaded(self, mock_api_key, mock_response, temp_dir):
        """--schema should include JSON schema in the request."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }
        schema_file = temp_dir / "schema.json"
        schema_file.write_text(json.dumps(schema))
        
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "choices": [{"message": {"content": '{"name": "test"}'}}]
            }
            
            subprocess.run(
                [sys.executable, str(CLI_PATH), "--json", "--schema", str(schema_file), "test"],
                capture_output=True, text=True, timeout=30
            )
            
            args, kwargs = mock_post.call_args
            payload = json.loads(kwargs["json"]) if "json" in kwargs else json.loads(args[1])
            assert "json_schema" in payload["response_format"]


# ---------------------------------------------------------------------------
# Spec: tool calling
# ---------------------------------------------------------------------------

class TestToolCalling:
    """Validates --tools flag."""

    def test_tools_file_is_loaded(self, mock_api_key, mock_response, temp_dir):
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
        
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            subprocess.run(
                [sys.executable, str(CLI_PATH), "--tools", str(tools_file), "test"],
                capture_output=True, text=True, timeout=30
            )
            
            args, kwargs = mock_post.call_args
            payload = json.loads(kwargs["json"]) if "json" in kwargs else json.loads(args[1])
            assert "tools" in payload
            assert payload["tools"][0]["function"]["name"] == "get_weather"

    def test_tool_calls_printed_as_json(self, mock_api_key):
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
        
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = tool_response
            
            result = subprocess.run(
                [sys.executable, str(CLI_PATH), "test"],
                capture_output=True, text=True, timeout=30
            )
            
            assert result.returncode == 0
            # Should contain the tool calls JSON
            output = json.loads(result.stdout)
            assert output[0]["function"]["name"] == "get_weather"


# ---------------------------------------------------------------------------
# Spec: error handling - exit codes
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Validates error exit codes per spec."""

    def test_missing_api_key_exits_1(self):
        """Missing API key should exit with code 1."""
        # Explicitly unset any existing key
        env = {k: v for k, v in os.environ.items() if k != "DEEPSEEK_API_KEY"}
        
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), "--api-key", "", "test"],
            capture_output=True, text=True, timeout=30,
            env=env
        )
        
        assert result.returncode == 1
        assert "ERROR" in result.stderr

    def test_api_error_exits_2(self, mock_api_key):
        """API returning non-200 should exit with code 2."""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 401
            mock_post.return_value.text = "Unauthorized"
            
            result = subprocess.run(
                [sys.executable, str(CLI_PATH), "test"],
                capture_output=True, text=True, timeout=30
            )
            
            assert result.returncode == 2
            assert "401" in result.stderr


# ---------------------------------------------------------------------------
# Spec: version
# ---------------------------------------------------------------------------

class TestVersion:
    """Validates --version flag."""

    def test_version_output(self, mock_api_key):
        """--version should print version and exit 0."""
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), "--version"],
            capture_output=True, text=True, timeout=30
        )
        
        assert result.returncode == 0
        assert "1.0.0" in result.stdout


# ---------------------------------------------------------------------------
# Spec: verbose mode
# ---------------------------------------------------------------------------

class TestVerboseMode:
    """Validates --verbose flag outputs request/response to stderr."""

    def test_verbose_outputs_request(self, mock_api_key, mock_response):
        """--verbose should print request details to stderr."""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = subprocess.run(
                [sys.executable, str(CLI_PATH), "--verbose", "test"],
                capture_output=True, text=True, timeout=30
            )
            
            assert result.returncode == 0
            assert "--- REQUEST ---" in result.stderr
            assert "--- RESPONSE ---" in result.stderr

    def test_normal_mode_no_debug_output(self, mock_api_key, mock_response):
        """Without --verbose, stderr should be empty on success."""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            result = subprocess.run(
                [sys.executable, str(CLI_PATH), "test"],
                capture_output=True, text=True, timeout=30
            )
            
            assert result.returncode == 0
            assert result.stderr == ""


# ---------------------------------------------------------------------------
# Spec: model flag
# ---------------------------------------------------------------------------

class TestModelFlag:
    """Validates --model flag."""

    def test_default_model(self, mock_api_key, mock_response):
        """Default model should be deepseek-chat."""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            subprocess.run(
                [sys.executable, str(CLI_PATH), "test"],
                capture_output=True, text=True, timeout=30
            )
            
            args, kwargs = mock_post.call_args
            payload = json.loads(kwargs["json"]) if "json" in kwargs else json.loads(args[1])
            assert payload["model"] == "deepseek-chat"

    def test_custom_model(self, mock_api_key, mock_response):
        """--model should override the default."""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            subprocess.run(
                [sys.executable, str(CLI_PATH), "--model", "deepseek-coder", "test"],
                capture_output=True, text=True, timeout=30
            )
            
            args, kwargs = mock_post.call_args
            payload = json.loads(kwargs["json"]) if "json" in kwargs else json.loads(args[1])
            assert payload["model"] == "deepseek-coder"

