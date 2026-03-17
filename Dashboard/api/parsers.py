"""Shared utilities for parsing vault markdown and JSONL files."""

import json
import collections
from pathlib import Path

import yaml


def parse_frontmatter(path):
    """Split ---YAML--- frontmatter from markdown body.

    Returns (meta_dict, body_str). Returns ({}, "") on any error.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}, ""

    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}

    return meta, parts[2].strip()


def read_jsonl_tail(path, n=10):
    """Return the last *n* JSON objects from a JSONL file.

    Returns [] on any error.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            tail = collections.deque(fh, maxlen=n)
    except (OSError, UnicodeDecodeError):
        return []

    entries = []
    for line in tail:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def list_md_files(directory):
    """Glob *.md in *directory*, parse frontmatter for each.

    Returns list of (meta_dict, body_str, Path) tuples.
    """
    d = Path(directory)
    if not d.is_dir():
        return []

    results = []
    for p in sorted(d.glob("*.md")):
        meta, body = parse_frontmatter(p)
        results.append((meta, body, p))
    return results
