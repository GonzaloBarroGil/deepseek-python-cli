# tests/test_sanity.py
"""Minimal test to verify mocking architecture works."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from deepseek_cli import DeepSeekCLI


def test_basic_mock():
    """Verify that requests.post is actually being mocked."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Hi back!"}}]
        }
        
        cli = DeepSeekCLI(argv=["Hello"])
        cli.run()
        
        assert mock_post.called, "requests.post was never called!"
        print(f"Mock called successfully")
