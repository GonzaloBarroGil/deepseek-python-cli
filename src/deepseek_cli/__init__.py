"""deepseek-cli - Deterministic CLI wrapper for DeepSeek API.

Version: 1.3.0
Spec: spec/deepseek-cli/v1.3.0.yml
"""

from deepseek_cli.main import DeepSeekCLI, main as entry_point

__version__ = "1.3.0"
__all__ = ["DeepSeekCLI", "entry_point"]
