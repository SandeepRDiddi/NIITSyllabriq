from __future__ import annotations

import json
import math
import re
from collections import Counter
from typing import Iterable


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
}


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def split_sentences(text: str) -> list[str]:
    normalized = normalize_whitespace(text)
    if not normalized:
        return []
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", normalized) if item.strip()]


def tokenize(text: str) -> list[str]:
    return [tok for tok in re.findall(r"[a-zA-Z0-9_]+", (text or "").lower()) if tok not in STOPWORDS]


def cosine_similarity(text_a: str, text_b: str) -> float:
    counter_a = Counter(tokenize(text_a))
    counter_b = Counter(tokenize(text_b))
    if not counter_a or not counter_b:
        return 0.0

    dot = sum(counter_a[token] * counter_b[token] for token in counter_a.keys() & counter_b.keys())
    norm_a = math.sqrt(sum(value * value for value in counter_a.values()))
    norm_b = math.sqrt(sum(value * value for value in counter_b.values()))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def top_matching_sentences(source: str, candidate: str, limit: int = 5) -> list[str]:
    source_sentences = split_sentences(source)
    candidate_sentences = split_sentences(candidate)
    scored: list[tuple[float, str]] = []
    for sentence in candidate_sentences:
        best = max((cosine_similarity(sentence, src) for src in source_sentences), default=0.0)
        if best > 0:
            scored.append((best, sentence))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [sentence for _, sentence in scored[:limit]]


def as_pretty_json(data: object) -> str:
    return json.dumps(data, indent=2, ensure_ascii=True)


def dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = normalize_whitespace(item)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
