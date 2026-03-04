import os
import random
from typing import Optional


def _prompts_dir() -> str:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(repo_root, "prompts")


def load_prompt(filename: str) -> str:
    path = os.path.join(_prompts_dir(), filename)
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def select_prompt_version(
    default_version: str,
    variants: Optional[list[str]] = None,
) -> str:
    if variants:
        return random.choice(variants)
    return default_version
