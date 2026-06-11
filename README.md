# deepseek-cli

> Deterministic CLI wrapper for the DeepSeek API
>
> **Version:** 1.2.0  
> **Spec:** `spec/deepseek-cli/v1.2.0.yml`  
> **License:** Apache-2.0

---

## Table of Contents

- [Overview](#overview)
- [Design Philosophy](#design-philosophy)
- [Tech Specs](#tech-specs)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Prompt Sources](#prompt-sources)
  - [System Messages](#system-messages)
  - [Structured Output](#structured-output)
  - [Tool Calling](#tool-calling)
  - [Determinism Controls](#determinism-controls)
  - [Verbose Debugging](#verbose-debugging)
- [Exit Codes](#exit-codes)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Development](#development)
  - [Running Tests](#running-tests)
  - [Test Coverage by Spec](#test-coverage-by-spec)
  - [Making Changes (SDD Workflow)](#making-changes-sdd-workflow)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

---

## Overview

`deepseek-cli` is a zero-dependency-wrapper-that-isn't-zero-dependencies-but-almost command-line tool for interacting with DeepSeek's chat completion API. It prioritizes **determinism**, **composability**, and **spec-compliance** — every feature is documented in a machine-readable specification before implementation.

It is the first building block of a broader **Spec-Driven Development (SDD)** environment, designed to serve as both a standalone utility and a primitive that orchestrators can shell out to reliably.

---

## Design Philosophy

| Principle | Implementation |
|---|---|
| **Determinism by default** | Temperature `0.0`, fixed seed, structured output modes |
| **Spec-first** | Every behavior defined in `spec/` before code is written |
| **Composability** | Unix pipes, exit codes, stdin/stdout/stderr contracts |
| **Auditability** | Verbose mode logs full request/response pairs |
| **Versioned contracts** | Specs live under `spec/deepseek-cli/v{major}.{minor}.{patch}.yml` |
| **Minimal dependencies** | Only `requests` (and `pytest` for development) |

---

## Tech Specs

| Property | Value |
|---|---|
| **Language** | Python 3.9+ (tested on 3.14.5) |
| **API Endpoint** | `https://api.deepseek.com/v1/chat/completions` |
| **Default Model** | `deepseek-chat` |
| **Default Temperature** | `0.0` |
| **Default Max Tokens** | `4096` |
| **Seed** | Fixed at `42` (for reproducibility) |
| **Auth** | Bearer token via `DEEPSEEK_API_KEY` env var or `--api-key` flag |
| **Output** | Plain text to stdout, diagnostics to stderr |
| **Streaming** | Supported via `--stream` flag |
| **Structured Output** | JSON mode via `--json`, with optional `--schema` file |
| **Tool Calling** | Tool definitions via `--tools` JSON file |

### API Compatibility

| DeepSeek Model | Compatible | Notes |
|---|---|---|
| `deepseek-chat` | ✅ | Default |
| `deepseek-coder` | ✅ | Use `--model deepseek-coder` |
| `deepseek-reasoner` | ✅ | Use `--model deepseek-reasoner` |

---

## Dependencies

### Runtime

| Package | Version | Purpose |
|---|---|---|
| `requests` | `>=2.31.0` | HTTP client for API calls |

### Development

| Package | Version | Purpose |
|---|---|---|
| `pytest` | `>=8.0.0` | Test framework |
| `pytest-cov` | `>=5.0.0` | Coverage reporting (optional) |

### System

- Python 3.9 or later
- A DeepSeek API key ([get one here](https://platform.deepseek.com/api_keys))

---

## Installation

### Option 1: pip Install (Recommended)

```bash
# Clone the repository
git clone git@github.com:GonzaloBarroGil/deepseek-python-cli.git
cd deepseek-python-cli

# Install in editable mode (development)
pip install -e .

# Or install directly
pip install .
```

### Option 2: PyPI

```bash
pip install deepseek-cli
```

The package is published on PyPI at [https://pypi.org/project/deepseek-cli/](https://pypi.org/project/deepseek-cli/).

### Set Your API Key

```bash
export DEEPSEEK_API_KEY="sk-your-key-here"

# Or add to your shell profile (~/.bashrc, ~/.zshrc):
echo 'export DEEPSEEK_API_KEY="sk-your-key-here"' >> ~/.bashrc
```

### Quick Start

```bash
# Simple query
deepseek-cli "Explain quantum entanglement in one sentence"

# Pipe from a file
cat question.txt | deepseek-cli

# With a system message
deepseek-cli --system "Answer in Spanish" "¿Qué es la inteligencia artificial?"

# Structured output (JSON)
deepseek-cli --json "List 3 colors" 

# With a JSON schema
deepseek-cli --json --schema schemas/colors.json "List 3 colors"

# Verbose mode for debugging
deepseek-cli --verbose "Hello, world!"
```

## Usage

### Prompt Sources

The CLI accepts prompts from four sources, in this priority order:

| Priority | Source | Example
|---|---|---|
| 1 (highest) | `--prompt flag` | `deepseek-cli --prompt "text"` |
| 2 | Positional argument | `deepseek-cli "text"` |
| 3 | `--file flag` | `deepseek-cli --file prompt.txt` |
| 4 (lowest) | stdin pipe | `echo "text" | deepseek-cli` |

If no prompt is provided, the CLI exits with code 1 and an error message on stderr.

### System Messages

```bash
# Inline system message
deepseek-cli --system "You are a Python expert" "Explain decorators"

# From file
deepseek-cli --system prompts/expert.txt "Explain decorators"
```

If the argument to --system matches an existing file path, its contents are used. Otherwise, the string itself is used as the system message.

### Structured Output

```bash
# Basic JSON mode
deepseek-cli --json "Return a JSON object with name, age, and city"

# With a JSON Schema (ensures valid output structure)
cat > schema.json << 'EOF'
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "age": {"type": "integer"},
    "city": {"type": "string"}
  },
  "required": ["name", "age", "city"]
}
EOF

deepseek-cli --json --schema schema.json "Generate a random person"
```

**Important**: When using --json, the model is constrained to return only valid JSON. This is essential for deterministic pipelines.

### Tool Calling

Define tools in a JSON file following the OpenAI/DeepSeek function calling format:

```bash
cat > tools.json << 'EOF'
[
  {
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "Get current weather for a city",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {
            "type": "string",
            "description": "City name"
          }
        },
        "required": ["city"]
      }
    }
  }
]
EOF

deepseek-cli --tools tools.json "What's the weather in London?"
```

If the model responds with a tool call, it prints the tool call array as JSON to stdout instead of text.

### Determinism Controls

```bash
# Default: temperature=0.0, seed=42 (maximum determinism)
deepseek-cli "Write a haiku"

# Override temperature for more variety
deepseek-cli --temperature 0.7 "Write a haiku"

# Different model
deepseek-cli --model deepseek-coder "Write a Python function to sort a list"
```

**Known limitation**: Not all DeepSeek models fully respect seed. For the highest determinism:

- Use `deepseek-chat`
- Set `--temperature 0.0`
- Use `--json` with a schema when possible

### Verbose Debugging

```bash
# Full request/response logging to stderr
deepseek-cli --verbose "test"

# Save trace to file
deepseek-cli --verbose "test" 2> trace.log

# Combine with script(1) for complete terminal capture
script session.log deepseek-cli --verbose "test"
```

Example verbose output on stderr:

```text
--- REQUEST ---
{
  "model": "deepseek-chat",
  "messages": [{"role": "user", "content": "test"}],
  "temperature": 0.0,
  "max_tokens": 4096,
  "seed": 42
}
--- RESPONSE ---
{
  "id": "chatcmpl-...",
  "choices": [{"message": {"content": "..."}}],
  "usage": {...}
}
```

## Exit Codes

Per the specification, exit codes have fixed meanings for reliable scripting:

| Code | Meaning | Example |
|---|---|---|
| 0 | Success | Response printed to stdout |
| 1 | Configuration error | Missing API key, no prompt provided |
| 2 | API error | HTTP 4xx/5xx, network failure |
| 3 | Schema validation error | Reserved for future use |

#### Scripting example:

```bash
#!/bin/bash
if deepseek-cli "Is this safe?" > response.txt 2> error.log; then
    echo "Success: $(cat response.txt)"
else
    exit_code=$?
    echo "Failed with code $exit_code" >&2
    exit $exit_code
fi
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | Yes* | — | Your DeepSeek API key |

## Project Structure

```text
deepseek-python-cli/
│
├── spec/                          # Specification files (the source of truth)
│   └── deepseek-cli/
│       ├── v1.0.0.yml             # Previous version spec
│       ├── v1.1.0.yml             # Previous version spec
│       └── v1.2.0.yml             # Current version spec
│
├── src/                           # Implementation
│   └── deepseek_cli/              # Python package
│       ├── __init__.py             # Package exports
│       ├── main.py                 # CLI logic
│       └── py.typed                # PEP 561 marker
│
├── tests/                         # Test suite
│   ├── test_cli.py                # Validates CLI against spec
│   ├── test_packaging.py          # Validates packaging structure
│   └── test_sanity.py             # Minimal integration test
│
├── examples/                      # Example scripts and configs
│   ├── tools.json                 # Sample tool definitions
│   ├── schema.json                # Sample JSON schema
│   └── pipeline.sh                # Example shell pipeline
│
├── pyproject.toml                 # Package build configuration
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Development dependencies
├── Makefile                       # Automation (install, test, validate-spec, freeze, build, publish)
├── README.md                      # This file
└── LICENSE                        # Apache-2.0
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
make test
# or:
python -m pytest tests/ -v

# Run a specific test class
python -m pytest tests/test_cli.py::TestDeterminism -v

# Run with coverage report
python -m pytest tests/test_cli.py --cov=src --cov-report=term-missing

# Run with verbose output (see print statements)
python -m pytest tests/test_cli.py -v -s
```

### Test Coverage by Spec

Every test class maps to a section of the specification:

| Test Class | Spec Section | Number of Tests |
|---|---|---|
| `TestPromptSources` | Inputs - prompt sources | 5 |
| `TestSystemMessage` | Inputs - system message | 2 |
| `TestDeterminism` | Determinism configuration | 3 |
| `TestStructuredOutput` | Structured output (JSON) | 2 |
| `TestToolCalling` | Tool calling | 2 |
| `TestErrorHandling` | Error handling / exit codes | 2 |
| `TestVersion` | Version flag | 1 |
| `TestVerboseMode` | Verbose debugging | 2 |
| `TestModelFlag` | Model selection | 2 |
| `TestPackageStructure` | Packaging - structure | 4 |
| `TestEntryPointExports` | Packaging - exports | 2 |
| `TestPyprojectToml` | Packaging - pyproject.toml | 5 |
| `TestOldFileRemoved` | Packaging - migration | 1 |
| `TestPyPIReadiness` | PyPI publication metadata | 8 |
| **Total** |  | **42 tests** |

## Making Changes (SDD Workflow)

This project follows Spec-Driven Development. To add or change a feature:

1. Create a new spec version
```bash
cp spec/deepseek-cli/v1.0.0.yml spec/deepseek-cli/v1.1.0.yml
# Edit v1.1.0.yml with your changes
```

2. Write tests first (TDD)
```bash
# Add test cases to tests/test_cli.py that validate the new spec
```

3. Run tests (they should fail)
```bash
python -m pytest tests/ -v
```

4. Update documentation
```bash
# Update README.md, version numbers, etc.
```

5. Commit atomically
```bash
git add spec/deepseek-cli/v1.1.0.yml tests/test_cli.py src/deepseek_cli/ README.md
git commit -m "feat: add streaming support (v1.1.0)"
git tag v1.1.0
```

## Roadmap

| Version | Feature | Status |
|---|---|---|
| `1.0.0` | Basic CLI, prompt sources, system messages, JSON mode, tools | ✅ Released |
| `1.1.0` | Pip packaging (`pip install .`), streaming (`--stream`) | ✅ Released |
| `1.2.0` | PyPI publication (`pip install deepseek-cli`) | ✅ Current |
| `1.3.0` | Conversation history (`--continue`, `--history-file`) | 📋 Planned |
| `1.4.0` | Multi-turn chat mode (`--interactive`) | 📋 Planned |
| `2.0.0` | Orchestrator integration (agent/sub-agent support) | 📋 Planned |

## Contributing

This project is part of a broader Spec-Driven Development initiative. Contributions are welcome if they follow the SDD workflow:

1. Fork the repository
2. Create a spec change proposal (new version in spec/)
3. Write tests
4. Implement
5. Submit a PR with spec, tests, and code

For bugs that don't change the spec, a test reproducing the bug is still required.

## License

Apache-2.0 License — see LICENSE for details.

## Related Projects

- DeepSeek API Documentation
- OpenAI Function Calling Guide (compatible format)

*Built with determinism in mind. Spec version: v1.2.0.*

