"""
Main Converter class for birdnames package.
"""

import warnings
import pandas as pd
from pathlib import Path
from typing import Union, List, Optional
import numpy as np
from .utils import fuzzy_match


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
            from_type: Source name type ("common_name", "scientific_name", "alpha_code_4", "alpha_code_6", "species_code")
            to_type: Target name type ("common_name", "scientific_name", "alpha_code_4", "alpha_code_6", "species_code")
            from_authority: Source taxonomic authority ("avilist", "ebird", "birdlife", "ibp")
            to_authority: Target taxonomic authority ("avilist", "ebird", "birdlife", "ibp")
            from_year: Year of source taxonomy (None = most recent)
            to_year: Year of target taxonomy (None = most recent)
            soft_matching: Handle case/spacing differences
            fuzzy_matching: Handle typos (slower)
        """
        self.from_type = from_type
        self.to_type = to_type
        self.from_authority = from_authority
        self.to_authority = to_authority
        self.from_year = from_year
        self.to_year = to_year
        self.soft_matching = soft_matching
        self.fuzzy_matching = fuzzy_matching

        # Load data
        self._load_data()

    def _load_data(self):
        """Load taxonomy data files."""
        data_dir = Path(__file__).parent.parent.parent / "data" / "processed"

        # Load source authority data
        from_file = data_dir / f"{self.from_authority}_taxonomy.csv"
        if not from_file.exists():
            raise FileNotFoundError(f"Taxonomy file not found: {from_file}")
        self.from_data = pd.read_csv(from_file)

        # Load target authority data (may be same as source)
        if self.to_authority == self.from_authority:
            self.to_data = self.from_data
        else:
            to_file = data_dir / f"{self.to_authority}_taxonomy.csv"
            if not to_file.exists():
                raise FileNotFoundError(f"Taxonomy file not found: {to_file}")
            self.to_data = pd.read_csv(to_file)

    def _get_column_name(self, name_type: str, authority: str) -> str:
        """Get the actual column name for a given name type and authority."""
        if name_type == "scientific_name":
            return "scientific_name"
        elif name_type == "genus":
            return "genus"
        elif name_type == "family":
            return f"{authority}_family"
        elif name_type == "order":
            return f"{authority}_order"
        elif name_type == "common_name":
            return f"{authority}_common_name"
        elif name_type == "alpha_code_4":
            if authority == "ibp":
                return "ibp_alpha_code_4"
            else:
                raise ValueError(f"4-letter alpha codes not available for {authority}")
        elif name_type == "alpha_code_6":
            if authority == "ibp":
                return "ibp_alpha_code_6"
            else:
                raise ValueError(f"6-letter alpha codes not available for {authority}")
        elif name_type == "species_code":
            if authority == "ebird":
                return "ebird_species_code"
            else:
                raise ValueError(f"Species codes not available for {authority}")
        else:
            raise ValueError(f"Unknown name type: {name_type}")

    def _normalize_string(self, s: str) -> str:
        """Normalize string for soft matching."""
        if not isinstance(s, str):
            return s
        if self.soft_matching:
            return s.strip().lower()
        return s

    def _convert_single(self, name: str) -> Optional[str]:
        """Convert a single name."""
        if pd.isna(name) or name == "":
            return None

        # Get column names
        from_col = self._get_column_name(self.from_type, self.from_authority)
        to_col = self._get_column_name(self.to_type, self.to_authority)

        # Cross-authority conversion requires scientific name as intermediate
        if self.from_authority != self.to_authority:
            return self._convert_cross_authority(name, from_col, to_col)
        else:
            return self._convert_same_authority(name, from_col, to_col)

    def _convert_same_authority(
        self, name: str, from_col: str, to_col: str, data: Optional[pd.DataFrame] = None
    ) -> Optional[str]:
        """Convert within the same authority."""
        if data is None:
            data = self.from_data

        # Exact match first
        if self.soft_matching:
            mask = data[from_col].astype(
                str
            ).str.lower().str.strip() == self._normalize_string(name)
        else:
            mask = data[from_col] == name

        matches = data[mask]

        if len(matches) > 0:
            if len(matches) > 1:
                # If there are multiple matches, don't return any
                warnings.warn(
                    f"Multiple matches found for '{name}' in {from_col}. Returning None."
                )
                return None
            result = matches.iloc[0][to_col]
            return result if pd.notna(result) else None

        # Fuzzy matching if enabled
        if self.fuzzy_matching:
            fuzzy_result = fuzzy_match(name, data[from_col].dropna().tolist())
            if fuzzy_result:
                fuzzy_matches = data[data[from_col] == fuzzy_result]
                if len(fuzzy_matches) > 0:
                    result = fuzzy_matches.iloc[0][to_col]
                    return result if pd.notna(result) else None

        return None

    def _convert_cross_authority(
        self, name: str, from_col: str, to_col: str
    ) -> Optional[str]:
        """Convert between different authorities using scientific name as bridge."""
        # Step 1: Convert to scientific name in source authority
        if self.from_type == "scientific_name":
            sci_name = name
        else:
            sci_name = self._convert_same_authority(
                name, from_col, "scientific_name", self.from_data
            )
            if not sci_name:  # no matches
                return None

        # Step 2: Convert from scientific name in target authority
        if self.to_type == "scientific_name":
            return sci_name
        else:
            return self._convert_same_authority(
                sci_name, "scientific_name", to_col, self.to_data
            )

    def convert(
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
            return self._convert_single(names)

        # Handle collections
        if isinstance(names, (list, np.ndarray, pd.Series)):
            results = []
            for name in names:
                result = self._convert_single(name)
                results.append(result)
            return results

        raise TypeError(f"Unsupported input type: {type(names)}")
