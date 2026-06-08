#!/usr/bin/env python3
"""
deepseek-cli - Deterministic CLI wrapper for DeepSeek API
Version: 1.0.0
Spec: spec/deepseek-cli/v1.0.0.yml
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

import requests


class DeepSeekCLI:
    """Main CLI handler following the spec contract."""
    
    BASE_URL = "https://api.deepseek.com/v1/chat/completions"
    
    def __init__(self, argv=None):
        self.args = self._parse_args(argv)
        self.api_key = self._get_api_key()
        self.prompt = self._get_prompt()
        self.messages = self._build_messages()
    
    def _parse_args(self, argv=None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Deterministic CLI for DeepSeek API"
        )
        parser.add_argument(
            "prompt", nargs="?", default=None,
            help="Prompt text (positional, overridden by --prompt or stdin)"
        )
        parser.add_argument("--prompt", default=None, dest="prompt_flag", help="Prompt as flag")
        parser.add_argument("--system", default=None, help="System message text or file")
        parser.add_argument("--model", default="deepseek-chat", help="Model name")
        parser.add_argument(
            "--temperature", type=float, default=0.0,
            help="Sampling temperature (default: 0.0 for determinism)"
        )
        parser.add_argument("--max-tokens", type=int, default=4096)
        parser.add_argument("--json", action="store_true", dest="json_mode")
        parser.add_argument("--schema", type=Path, help="JSON Schema file")
        parser.add_argument("--tools", type=Path, help="Tool definitions JSON file")
        parser.add_argument("--api-key", help="API key (env: DEEPSEEK_API_KEY)")
        parser.add_argument("--stream", action="store_true")
        parser.add_argument("--file", type=Path, help="Read prompt from file")
        parser.add_argument("--verbose", action="store_true")
        parser.add_argument("--version", action="version", version="1.0.0")
        
        return parser.parse_args(argv)
        
    def _get_api_key(self) -> str:
        key = self.args.api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            self._error("DEEPSEEK_API_KEY not set and --api-key not provided", 1)
        return key
    
    def _get_prompt(self) -> str:
        """Resolve prompt from multiple sources, following spec priority.
        
        Priority:
        1. --prompt flag (stored in args.prompt_flag)
        2. Positional argument (stored in args.prompt)
        3. --file flag
        4. stdin (if not a TTY)
        """
        # Check --prompt flag first (highest priority)
        if self.args.prompt_flag:
            return self.args.prompt_flag
        
        # Check positional argument
        if self.args.prompt:
            return self.args.prompt
        
        # Check --file flag
        if self.args.file:
            return self.args.file.read_text()
        
        # Check stdin (only if it's being piped, not an interactive terminal)
        try:
            is_tty = sys.stdin.isatty()
        except Exception:
            is_tty = True
        
        if not is_tty:
            try:
                stdin_content = sys.stdin.read().strip()
                if stdin_content:
                    return stdin_content
            except OSError:
                pass
        
        # Nothing found
        self._error(
            "No prompt provided. Use --prompt, positional argument, --file, or pipe to stdin.",
            1
        )

    def _build_messages(self) -> list:
        messages = []
        if self.args.system:
            system_text = self._resolve_file_or_text(self.args.system)
            messages.append({"role": "system", "content": system_text})
        messages.append({"role": "user", "content": self.prompt})
        return messages
    
    def _resolve_file_or_text(self, value: str) -> str:
        """If value is a file path that exists, return its contents."""
        path = Path(value)
        if path.is_file():
            return path.read_text()
        return value
    
    def _load_json_file(self, path: Optional[Path]) -> Optional[dict]:
        if path and path.is_file():
            with open(path) as f:
                return json.load(f)
        return None
    
    def run(self):
        payload = {
            "model": self.args.model,
            "messages": self.messages,
            "temperature": self.args.temperature,
            "max_tokens": self.args.max_tokens,
            "stream": self.args.stream,
        }
        
        # Determinism: attempt to set seed if API supports it
        payload["seed"] = 42  # Fixed seed for reproducibility
        
        # Structured output via JSON mode
        if self.args.json_mode:
            payload["response_format"] = {"type": "json_object"}
            if self.args.schema:
                schema = self._load_json_file(self.args.schema)
                if schema:
                    payload["response_format"]["json_schema"] = schema
        
        # Tool definitions
        tools = self._load_json_file(self.args.tools)
        if tools:
            payload["tools"] = tools
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        if self.args.verbose:
            print("--- REQUEST ---", file=sys.stderr)
            print(json.dumps(payload, indent=2), file=sys.stderr)
        
        try:
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                stream=self.args.stream,
                timeout=120,
            )
            
            if response.status_code != 200:
                self._error(
                    f"API error [{response.status_code}]: {response.text}",
                    2
                )
            
            if self.args.stream:
                self._handle_stream(response)
            else:
                data = response.json()
                self._handle_response(data)
                
        except requests.RequestException as e:
            self._error(f"Request failed: {e}", 2)
    
    def _handle_stream(self, response):
        """Stream chunks to stdout."""
        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        sys.stdout.write(content)
                        sys.stdout.flush()
        print()  # Final newline
    
    def _handle_response(self, data: dict):
        """Extract and output the response content."""
        if self.args.verbose:
            print("--- RESPONSE ---", file=sys.stderr)
            print(json.dumps(data, indent=2), file=sys.stderr)
        
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        
        # Handle tool calls if present
        tool_calls = message.get("tool_calls", [])
        if tool_calls:
            print(json.dumps(tool_calls, indent=2))
        else:
            print(content)
    
    def _error(self, message: str, code: int):
        print(f"ERROR: {message}", file=sys.stderr)
        sys.exit(code)


def main():
    cli = DeepSeekCLI()
    cli.run()


if __name__ == "__main__":
    main()

