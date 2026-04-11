#!/usr/bin/env python3
"""rapt -- single-file entry point.

Usage:
    python rapt.py system_prompt.md -p openai
    python rapt.py prompt.md -p anthropic -m omission --verbose
    cat skills.md | python rapt.py - -p google --json
"""

from src.cli import main

if __name__ == "__main__":
    main()
