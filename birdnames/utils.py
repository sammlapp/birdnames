"""
Utility functions for birdnames package.
"""

from typing import Optional, List
import difflib
from pathlib import Path
import pandas as pd

# load the available taxonomies from the CSV file into a dataframe
package_dir = Path(__file__).parent
available_taxonomies_file = package_dir / "data" / "available_taxonomies.csv"
TAXONOMIES = pd.read_csv(available_taxonomies_file)


# utility for displaying available taxonomies
def color_boolean(val):
    if val == True:
        color = "#C4E5C4"  # Green for True
    elif val == False:
        color = "#EEEEEE"
    else:
        color = ""  # Handle cases where the value isn't boolean
    return f"background-color: {color}"


def list_taxonomies():
    return TAXONOMIES.set_index(["authority", "year"]).style.map(color_boolean)


def normalize_string(s: str) -> str:
    """Normalize string for soft matching.

    Args:
        s: String to normalize

    Returns:
        Normalized string (lowercase, single spaces) if soft_matching enabled, else unchanged
    """
    if not isinstance(s, str):
        return s
    # Replace multiple spaces, dashes, underscores with single space
    import re

    normalized = re.sub(r"[-_\s]+", " ", s)
    return normalized.strip().lower()


def load_taxonomy(authority: str, year: int) -> pd.DataFrame:
    """
    Load a specific taxonomy table based on authority and year.

    To see available authorities and years, use `birdnames.list_taxonomies()`.

    Args:
        authority: Taxonomic authority (one of 'avilist', 'ebird', 'birdlife', 'ibp', 'bbl')
        year: Year of the taxonomy

    Returns:
        DataFrame containing the taxonomy data
    """
    # Construct the file path based on authority and year
    file_path = package_dir / "data" / "processed" / f"{authority}_{year}_taxonomy.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"Taxonomy file not found: {file_path}")

    # Load the CSV into a DataFrame
    return pd.read_csv(file_path, dtype=str)


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
    if len(candidates) == 0 or not query:
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
