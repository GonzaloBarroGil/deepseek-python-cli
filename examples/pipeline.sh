#!/usr/bin/env bash
# examples/pipeline.sh
# Example shell pipeline demonstrating deepseek-cli composability.
#
# Usage:
#   export DEEPSEEK_API_KEY="sk-..."
#   chmod +x examples/pipeline.sh
#   ./examples/pipeline.sh
#
# This pipeline:
#   1. Reads a question from stdin
#   2. Sends it to deepseek-cli with a system message
#   3. Parses the JSON response
#   4. Extracts a specific field with jq

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SYSTEM_PROMPT="You are a helpful assistant. Always respond with valid JSON matching the requested schema."
SCHEMA_FILE="$(dirname "$0")/schema.json"

# ---------------------------------------------------------------------------
# Check prerequisites
# ---------------------------------------------------------------------------
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required (https://stedolan.github.io/jq/)" >&2; exit 1; }

if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    echo "ERROR: DEEPSEEK_API_KEY environment variable is not set" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Pipeline: Generate a random person
# ---------------------------------------------------------------------------
echo "=== Pipeline: Generate a random person ==="
echo ""

python3 "$(dirname "$0")/../src/deepseek_cli.py" \
    --system "$SYSTEM_PROMPT" \
    --json \
    --schema "$SCHEMA_FILE" \
    "Generate a random person profile. Include name, age, city, and occupation." \
    2> pipeline-errors.log | tee pipeline-output.json

echo ""
echo "---"
echo "Response saved to pipeline-output.json"
echo "Errors (if any) saved to pipeline-errors.log"

# ---------------------------------------------------------------------------
# Extract a specific field using jq
# ---------------------------------------------------------------------------
echo ""
echo "=== Extracting 'name' field with jq ==="
jq -r '.name // "No name found"' pipeline-output.json

echo ""
echo "=== Extracting 'city' field with jq ==="
jq -r '.city // "No city found"' pipeline-output.json

echo ""
echo "Pipeline complete."