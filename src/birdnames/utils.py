"""
Utility functions for birdnames package.
"""

from typing import Optional, List
import difflib


def fuzzy_match(
    query: str, candidates: List[str], threshold: float = 0.8
) -> Optional[str]:
    """
    Find the best fuzzy match for a query string from a list of candidates.

    Args:
        query: String to search for
        candidates: List of candidate strings to match against
        threshold: Minimum similarity score (0-1) to consider a match

    Returns:
        Best matching candidate string, or None if no match above threshold
    """
    if not query or not candidates:
        return None

    # Use difflib to find closest matches
    matches = difflib.get_close_matches(query, candidates, n=1, cutoff=threshold)

    return matches[0] if matches else None


def normalize_name(name: str) -> str:
    """
    Normalize a bird name for consistent matching.

    Args:
        name: Bird name to normalize

    Returns:
        Normalized name
    """
    if not isinstance(name, str):
        return name

    return name.strip().title()
