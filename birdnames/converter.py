"""
Main Converter class for birdnames package.
"""

import warnings
import pandas as pd
from pathlib import Path
from typing import Tuple, Union, List, Optional
import numpy as np
from .utils import fuzzy_match, TAXONOMIES, load_taxonomy, normalize_string


def _get_column_name(name_type: str, authority: str) -> str:
    """Get the actual column name for a given name type and authority.

    Args:
        name_type: Type of name ("common_name", "scientific_name", "alpha", etc.)
        authority: Taxonomic authority ("avilist", "ebird", "bbl", "ibp", etc.)

    Returns:
        Column name to use in the taxonomy dataframe
    """
    if name_type in ("scientific_name", "genus"):
        return name_type
    return f"{authority}_{name_type}"


class Converter:
    """
    Main converter class for translating between bird name types and taxonomic authorities.

    Example usage:
        converter = bn.Converter(
            from_type="common_name",
            to_type="scientific_name",
            from_authority="avilist",
            to_authority="avilist"
        )
        result = converter.convert("American Robin")
    """

    def __init__(
        self,
        from_type: str,
        to_type: str,
        from_authority: str = "avilist",
        to_authority: str = "avilist",
        from_year: Optional[int] = None,
        to_year: Optional[int] = None,
        soft_matching: bool = True,
        fuzzy_matching: bool = False,
    ):
        """
        Initialize converter with conversion parameters.

        Args:
            from_type: Source name type ("common_name", "scientific_name", "alpha", "alpha6", "ebird_code", "french_name")
            to_type: Target name type ("common_name", "scientific_name", "alpha", "alpha6", "ebird_code", "french_name")
            from_authority: Source taxonomic authority ("avilist", "ebird", "birdlife", "ibp", "bbl")
            to_authority: Target taxonomic authority ("avilist", "ebird", "birdlife", "ibp", "bbl")
            from_year: Year of source taxonomy (None = most recent)
            to_year: Year of target taxonomy (None = most recent)
            soft_matching: Handle case/spacing differences
            fuzzy_matching: Handle typos, finding the best match (slower)
        """
        self.from_type = from_type.lower().strip()
        self.to_type = to_type.lower().strip()
        self.from_authority = from_authority.lower().strip()
        self.to_authority = to_authority.lower().strip()
        self.from_year = from_year
        self.to_year = to_year
        self.soft_matching = soft_matching
        self.fuzzy_matching = fuzzy_matching

        # Determine years to use
        from_year = self.from_year or self._get_most_recent_year(self.from_authority)
        to_year = self.to_year or self._get_most_recent_year(self.to_authority)

        # Get column names
        from_col = _get_column_name(self.from_type, self.from_authority)
        to_col = _get_column_name(self.to_type, self.to_authority)

        # create pd.Series for mapping from one name type to another
        source_taxonomy = load_taxonomy(from_authority, from_year)
        same_taxonomy = to_authority == from_authority and to_year == from_year
        # if within a taxonomy: simply index=from and values=to
        # if converting to scientific name, we don't need to cross taxonomies
        if to_col == "scientific_name" or same_taxonomy:
            self.lookup = source_taxonomy[[from_col, to_col]]
        else:
            # dest_cols = [to_col] if to_col != "scientific_name" else []
            dest_taxonomy = load_taxonomy(to_authority, to_year).set_index(
                "scientific_name"
            )[[to_col]]
            # merge source and destination taxonomies on scientific name
            source_cols = [from_col] if from_col != "scientific_name" else []
            self.lookup = source_taxonomy.set_index("scientific_name")[
                source_cols
            ].join(dest_taxonomy)
            self.lookup = self.lookup.reset_index(drop=False)[[from_col, to_col]]

        # if soft matching, apply normalization to source column
        if soft_matching:
            self.lookup[from_col] = self.lookup[from_col].apply(normalize_string)

        # drop missing values
        self.lookup = self.lookup.dropna()

        # drop duplicated from_col
        self.lookup = self.lookup.drop_duplicates(subset=[from_col])

        # convert to a pd.Series for fast lookup
        self.lookup = self.lookup.set_index(from_col)[to_col]

    def _get_most_recent_year(self, authority: str) -> str:
        """Get the most recent year available for an authority.

        Args:
            authority: Taxonomic authority to find the most recent year for

        Returns:
            Most recent year available as string
        """
        data_dir = Path(__file__).parent.parent / "data" / "processed"

        # Find all files for this authority
        authority_files = list(data_dir.glob(f"{authority}_*_taxonomy.csv"))

        if not authority_files:
            raise FileNotFoundError(
                f"No taxonomy files found for authority: {authority}"
            )

        # Extract years and find the most recent
        years = []
        for file in authority_files:
            # File format: authority_year_taxonomy.csv
            parts = file.stem.split("_")
            if len(parts) >= 3:  # authority_year_taxonomy
                year = parts[-2]
                years.append(year)

        if not years:
            raise FileNotFoundError(
                f"No valid year files found for authority: {authority}"
            )

        # Return the most recent year (assumes numeric years)
        return max(years)

    def convert_single(self, name: str) -> Optional[str]:
        """Convert a single name.

        Args:
            name: Name to convert

        Returns:
            Converted name or None if no match found
        """
        if pd.isna(name) or name == "":
            return None

        if self.soft_matching:
            # Apply string normalization
            # (lowercase, remove spaces and characters)
            name = normalize_string(name)

        # try exact match first
        try:
            return self.lookup[name]
        except KeyError:
            # Fuzzy matching if enabled, and no exact matches
            if self.fuzzy_matching:
                # get the most similar result, with minimum similarity .8
                fuzzy_result = fuzzy_match(name, self.lookup.index.values)
                if fuzzy_result:  # found an inexact match
                    return self.lookup[fuzzy_result]

            return None  # no matches

    def __call__(
        self, names: Union[str, List[str], np.ndarray, pd.Series]
    ) -> Union[str, List[str]]:
        """
        Convert bird names from source to target type/authority.

        Args:
            names: Single name (str) or collection of names (list, np.array, pd.Series)

        Returns:
            Single converted name (str) or list of converted names
        """
        # Handle single string
        if isinstance(names, str):
            return self.convert_single(names)

        # Handle collections
        if isinstance(names, (list, np.ndarray, pd.Series)):
            # first create a list to hold results
            results = [self.convert_single(n) for n in names]

            # in returned value, retain original type for consistency
            if isinstance(names, pd.Series):
                return pd.Series(results, index=names.index)
            elif isinstance(names, np.ndarray):
                return np.array(results)
            else:
                return results

        raise TypeError(f"Unsupported input type: {type(names)}")

    def convert(self, names: Union[str, List[str], np.ndarray, pd.Series]):
        """alias for __call__"""
        return self(names)


def determine_name_type(
    names: Union[str, List[str], np.ndarray, pd.Series],
) -> Tuple[str, str, int, list]:
    """Determine the type of bird names in the input list.

    The type and authority with the most matches to `names` is returned.
    The function also returns a list of all names without a match in the
    selected taxonomy.

    Args:
        names: List of bird names (common names, scientific names, alpha codes, etc.)

    Returns:
        Tuple of:
        - Type of the names (one of "common_name", "scientific_name", "alpha", "alpha6", "ebird_code", "french_name")
        - Authority of the names (one of "avilist", "ebird", "birdlife", "ibp", "bbl")
        - year: Year of the taxonomy used (int)
        - List of names without a match in the selected type & authority
    """
    if isinstance(names, str):
        names = [names]

    names_set = set(names)

    # first, remove NAs, Nones, and empty strings
    cleaned_names = [name for name in names if pd.notna(name) and name != ""]

    if len(cleaned_names) == 0:
        raise ValueError("Input list contains no valid names.")

    # Define all possible combinations to test: authority, year, and name type
    # list all available options, from smallest to largest
    options = TAXONOMIES.sort_values(by="entries").drop(columns="entries")
    options = options.melt(
        id_vars=["authority", "year"], var_name="name_type", value_name="value"
    )
    # list of (authority, year, name_type)
    options = options[options.value].drop(columns="value")

    best_matches = 0
    best_type = None
    best_authority = None
    best_year = None
    unmatched = []

    # Test each combination
    # keep track of loaded taxonomies to avoid reloading
    taxonomy = None
    loaded_authority = None
    loaded_year = None
    for authority, year, name_type in options.itertuples(index=False):
        # load the table for this authority and year, unless already loaded
        if taxonomy is None or (loaded_year != year or loaded_authority != authority):
            taxonomy = load_taxonomy(authority, year)
            loaded_authority = authority
            loaded_year = year
        taxonomy_names = set(taxonomy[_get_column_name(name_type, authority)])

        # find the size of the intersection between cleaned_names and the names in this type/authority
        matches = len(names_set.intersection(taxonomy_names))

        # Update best match if this taxonomy contains more matching codes
        if matches > best_matches:
            best_matches = matches
            best_type = name_type
            best_authority = authority
            best_year = year
            unmatched = names_set.difference(taxonomy_names)

        # if all names match, we can stop early
        if matches == len(names_set):
            break

    if best_type is None:
        raise ValueError("Could not determine type and authority for the input names.")

    return best_type, best_authority, best_year, unmatched


def alpha(
    names: Union[str, List[str], np.ndarray, pd.Series],
    alpha_code_authority: Optional[str] = "bbl",
    year: Optional[int] = None,
    soft_matching: bool = True,
    fuzzy_matching: bool = False,
    unmatched_names_behavior: str = "ignore",
):
    """Convert bird names from any type to 4-letter alpha codes

    This function determines the authority and type in `names` automatically,
    and converts to 4-letter alpha codes. It only selects one source name format,
    eg all scientific names, it does not allow the source names to be variable.

    After selecting the best possible taxonomy and name type (EG scientific names from AviList 2024),
    any values in `names` that are not in the selected taxonomy will be converted to None.

    Args:
        names: List of bird names (common names, scientific names, alpha codes, etc.)
        alpha_code_authority: Authority for the returned 4-letter alpha codes ("bbl", "ibp")
        year: Year of the taxonomy to use (None = most recent)
        soft_matching: Handle case/spacing differences
        fuzzy_matching: Handle typos, finding the best match (slower)
        unmatched_names_behavior: How to handle unmatched names ("ignore", "warn", "error")

    Returns:
        4-letter alpha codes for each value in `names` (same type as input)
    """
    authorities_with_alpha = set(
        TAXONOMIES[TAXONOMIES["alpha"] == True]["authority"].values
    )
    if alpha_code_authority not in authorities_with_alpha:
        raise ValueError(
            f"`alpha_code_authority` must be one of {authorities_with_alpha}, got {alpha_code_authority}"
        )
    if unmatched_names_behavior not in ["ignore", "warn", "error"]:
        raise ValueError(
            "unmatched_names_behavior must be one of 'ignore', 'warn', 'error'"
        )
    src_type, src_authority, src_year, unmatched_names = determine_name_type(names)

    if len(unmatched_names) > 0:
        msg = f"{len(unmatched_names)} names could not be matched to any known bird name in {src_type} ({src_authority}, {src_year})."
        if unmatched_names_behavior == "warn":
            warnings.warn(msg)
        elif unmatched_names_behavior == "error":
            raise ValueError(msg)
        # if "ignore", do nothing

    # create a converter from the selected name type to the desired alpha code
    converter = Converter(
        from_type=src_type,
        to_type="alpha",
        from_authority=src_authority,
        to_authority=alpha_code_authority,
        from_year=src_year,
        to_year=year,
        soft_matching=soft_matching,
        fuzzy_matching=fuzzy_matching,
    )
    return converter(names)


def scientific(
    names: Union[str, List[str], np.ndarray, pd.Series],
    scientific_name_authority: Optional[str] = "avilist",
    year: Optional[int] = None,
    soft_matching: bool = True,
    fuzzy_matching: bool = False,
    unmatched_names_behavior: str = "ignore",
):
    """Convert bird names from any type to scientific names

    This function determines the authority and type in `names` automatically,
    and converts to scientific names. It only selects one source name format,
    eg all common names, it does not allow the source names to be variable.

    After selecting the best possible taxonomy and name type (EG common names from AviList 2024),
    any values in `names` that are not in the selected taxonomy will be converted to None.

    Args:
        names: List of bird names (common names, scientific names, alpha codes, etc.)
        scientific_name_authority: Authority for the returned scientific names ("avilist", "ebird")
        year: Year of the taxonomy to use (None = most recent)
        soft_matching: Handle case/spacing differences
        fuzzy_matching: Handle typos, finding the best match (slower)
        unmatched_names_behavior: How to handle unmatched names ("ignore", "warn", "error")

    Returns:
        Scientific names for each value in `names` (same type as input)
    """
    scientific_name_authority = scientific_name_authority.lower()
    authorities = set(TAXONOMIES["authority"].values)
    if scientific_name_authority not in authorities:
        raise ValueError(
            f"`scientific_name_authority` must be one of {authorities}. Got {scientific_name_authority}."
        )
    if unmatched_names_behavior not in ["ignore", "warn", "error"]:
        raise ValueError(
            "unmatched_names_behavior must be one of 'ignore', 'warn', 'error'"
        )
    src_type, src_authority, src_year, unmatched_names = determine_name_type(names)

    if len(unmatched_names) > 0:
        msg = f"{len(unmatched_names)} names could not be matched to any known bird name in {src_type} ({src_authority}, {src_year})."
        if unmatched_names_behavior == "warn":
            warnings.warn(msg)
        elif unmatched_names_behavior == "error":
            raise ValueError(msg)
        # if "ignore", do nothing

    # create a converter from the selected name type to the desired scientific name
    converter = Converter(
        from_type=src_type,
        to_type="scientific_name",
        from_authority=src_authority,
        to_authority=scientific_name_authority,
        from_year=src_year,
        to_year=year,
        soft_matching=soft_matching,
        fuzzy_matching=fuzzy_matching,
    )
    return converter(names)


def common(
    names: Union[str, List[str], np.ndarray, pd.Series],
    common_name_authority: Optional[str] = "avilist",
    year: Optional[int] = None,
    soft_matching: bool = True,
    fuzzy_matching: bool = False,
    unmatched_names_behavior: str = "ignore",
):
    """Convert bird names from any type to English common names

    This function determines the authority and type in `names` automatically,
    and converts to common names. It only selects one source name format,
    eg all common names, it does not allow the source names to be variable.

    After selecting the best possible taxonomy and name type (EG common names from AviList 2024),
    any values in `names` that are not in the selected taxonomy will be converted to None.

    Args:
        names: List of bird names (scientific names, alpha codes, etc.)
        common_name_authority: Authority for the returned common names ("avilist", "ebird")
        year: Year of the taxonomy to use (None = most recent)
        soft_matching: Handle case/spacing differences
        fuzzy_matching: Handle typos, finding the best match (slower)
        unmatched_names_behavior: How to handle unmatched names ("ignore", "warn", "error")

    Returns:
        Common names for each value in `names` (same type as input)
    """
    common_name_authority = common_name_authority.lower()
    authorities_with_common_name = set(
        TAXONOMIES[TAXONOMIES["common_name"] == True]["authority"].values
    )
    if not common_name_authority in authorities_with_common_name:
        raise ValueError(
            f"`common_name_authority` must be one of {authorities_with_common_name}. Got {common_name_authority}."
        )
    if unmatched_names_behavior not in ["ignore", "warn", "error"]:
        raise ValueError(
            "unmatched_names_behavior must be one of 'ignore', 'warn', 'error'"
        )
    src_type, src_authority, src_year, unmatched_names = determine_name_type(names)

    if len(unmatched_names) > 0:
        msg = f"{len(unmatched_names)} names could not be matched to any known bird name in {src_type} ({src_authority}, {src_year})."
        if unmatched_names_behavior == "warn":
            warnings.warn(msg)
        elif unmatched_names_behavior == "error":
            raise ValueError(msg)
        # if "ignore", do nothing

    # create a converter from the selected name type to the desired common name
    converter = Converter(
        from_type=src_type,
        to_type="common_name",
        from_authority=src_authority,
        to_authority=common_name_authority,
        from_year=src_year,
        to_year=year,
        soft_matching=soft_matching,
        fuzzy_matching=fuzzy_matching,
    )
    return converter(names)


def ebird(
    names: Union[str, List[str], np.ndarray, pd.Series],
    year: Optional[int] = None,
    soft_matching: bool = True,
    fuzzy_matching: bool = False,
    unmatched_names_behavior: str = "ignore",
):
    """Convert bird names from any type to ebird codes

    This function determines the authority and type in `names` automatically,
    and converts to ebird codes. It only selects one source name format,
    eg all common names, it does not allow the source names to be variable.

    After selecting the best possible taxonomy and name type (EG common names from AviList 2024),
    any values in `names` that are not in the selected taxonomy will be converted to None.

    Args:
        names: List of bird names (scientific names, alpha codes, etc.)
        year: Year of the ebird taxonomy to use (None = most recent)
        soft_matching: Handle case/spacing differences
        fuzzy_matching: Handle typos, finding the best match (slower)
        unmatched_names_behavior: How to handle unmatched names ("ignore", "warn", "error")

    Returns:
        ebird codes for each value in `names` (same type as input)
    """
    if unmatched_names_behavior not in ["ignore", "warn", "error"]:
        raise ValueError(
            "unmatched_names_behavior must be one of 'ignore', 'warn', 'error'"
        )
    src_type, src_authority, src_year, unmatched_names = determine_name_type(names)

    if len(unmatched_names) > 0:
        msg = f"{len(unmatched_names)} names could not be matched to any known bird name in {src_type} ({src_authority}, {src_year})."
        if unmatched_names_behavior == "warn":
            warnings.warn(msg)
        elif unmatched_names_behavior == "error":
            raise ValueError(msg)
        # if "ignore", do nothing

    # create a converter from the selected name type to the desired ebird code
    converter = Converter(
        from_type=src_type,
        to_type="ebird_code",
        from_authority=src_authority,
        to_authority="ebird",
        from_year=src_year,
        to_year=year,
        soft_matching=soft_matching,
        fuzzy_matching=fuzzy_matching,
    )
    return converter(names)
