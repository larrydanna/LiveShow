"""Script near-match detection utilities.

Keeps matching logic isolated so thresholds and algorithms can be tuned
without touching the import endpoint.
"""

import re
from difflib import SequenceMatcher
from typing import Any

# --- Thresholds (tune here) ---
TITLE_MATCH_THRESHOLD = 0.85
BODY_MATCH_THRESHOLD = 0.80
# A script is a near-match when:
#   title_score >= TITLE_MATCH_THRESHOLD
#   OR (title_score >= TITLE_PARTIAL_THRESHOLD AND body_score >= BODY_MATCH_THRESHOLD)
TITLE_PARTIAL_THRESHOLD = 0.60


def normalize(text: str) -> str:
    """Lower-case, trim, and collapse internal whitespace."""
    return re.sub(r"\s+", " ", (text or "").lower().strip())


def similarity_ratio(a: str, b: str) -> float:
    """Return a 0–1 similarity score between two strings (normalized)."""
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def find_near_match(
    title: str,
    body: str,
    existing_scripts: list[Any],
) -> list[dict]:
    """Return a list of near-match candidates from *existing_scripts*.

    Each candidate is a dict:
        {
            "id": <int>,
            "title": <str>,
            "title_score": <float>,
            "body_score": <float>,
        }

    Candidates are sorted by title_score descending.
    *existing_scripts* must have `.id`, `.title`, and `.body` attributes.
    """
    candidates = []
    for script in existing_scripts:
        t_score = similarity_ratio(title, script.title)
        b_score = similarity_ratio(body, script.body)
        is_near = t_score >= TITLE_MATCH_THRESHOLD or (
            t_score >= TITLE_PARTIAL_THRESHOLD and b_score >= BODY_MATCH_THRESHOLD
        )
        if is_near:
            candidates.append(
                {
                    "id": script.id,
                    "title": script.title,
                    "title_score": round(t_score, 4),
                    "body_score": round(b_score, 4),
                }
            )
    candidates.sort(key=lambda c: c["title_score"], reverse=True)
    return candidates
