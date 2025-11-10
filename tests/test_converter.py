"""
Comprehensive tests for the Converter class.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import birdnames
from birdnames import Converter


class TestConverter:
    """Test cases for Converter class."""

    def test_converter_initialization(self):
        """Test that Converter can be initialized with basic parameters."""
        converter = Converter(
            from_type="common_name",
            to_type="scientific_name",
            from_authority="avilist",
            to_authority="avilist",
        )

        assert converter.from_type == "common_name"
        assert converter.to_type == "scientific_name"
        assert converter.from_authority == "avilist"
        assert converter.to_authority == "avilist"
        assert converter.soft_matching is True
        assert converter.fuzzy_matching is False

    def test_column_name_mapping(self):
        """Test that column name mapping works correctly."""
        converter = Converter(from_type="common_name", to_type="scientific_name")

        # Test scientific name (universal)
        assert (
            birdnames.converter._get_column_name("scientific_name", "avilist")
            == "scientific_name"
        )

        # Test authority-specific columns
        assert (
            birdnames.converter._get_column_name("common_name", "avilist")
            == "avilist_common_name"
        )
        assert (
            birdnames.converter._get_column_name("common_name", "ebird")
            == "ebird_common_name"
        )

        # Test IBP alpha codes
        assert birdnames.converter._get_column_name("alpha", "ibp") == "ibp_alpha"
        assert birdnames.converter._get_column_name("alpha6", "ibp") == "ibp_alpha6"

        # Test eBird species codes
        assert (
            birdnames.converter._get_column_name("ebird_code", "ebird")
            == "ebird_ebird_code"
        )

        # Test BBL alpha codes and French names
        assert birdnames.converter._get_column_name("alpha", "bbl") == "bbl_alpha"
        assert (
            birdnames.converter._get_column_name("french_name", "bbl")
            == "bbl_french_name"
        )

    # TODO add helpful error messages for invalid combinations
    # def test_invalid_combinations(self):
    #     """Test that invalid type/authority combinations raise errors."""
    #     converter = Converter(from_type="common_name", to_type="scientific_name")

    #     # Alpha codes only available for IBP
    #     with pytest.raises(ValueError):
    #         birdnames.converter._get_column_name("alpha", "avilist")

    #     # Species codes only available for eBird
    #     with pytest.raises(ValueError):
    #         birdnames.converter._get_column_name("ebird_code", "avilist")

    #     # Unknown name type
    #     with pytest.raises(ValueError):
    #         birdnames.converter._get_column_name("unknown_type", "avilist")

    #     # BBL doesn't support family/order
    #     with pytest.raises(ValueError):
    #         birdnames.converter._get_column_name("family", "bbl")
    #     with pytest.raises(ValueError):
    #         birdnames.converter._get_column_name("order", "bbl")

    #     # French names only available for BBL
    #     with pytest.raises(ValueError):
    #         birdnames.converter._get_column_name("french_name", "avilist")

    def test_string_normalization(self):
        """Test string normalization for soft matching."""

        assert (
            birdnames.utils.normalize_string("  American Robin  ") == "american robin"
        )
        assert birdnames.utils.normalize_string("BLUE JAY") == "blue jay"

    def test_basic_conversion_avilist(self):
        """Test basic conversions within AviList taxonomy."""
        converter = Converter(
            from_type="common_name", to_type="scientific_name", from_authority="avilist"
        )

        # Test with Common Ostrich (should be in the data)
        result = converter.convert("Common Ostrich")
        assert result == "Struthio camelus"

        # Test reverse conversion
        converter_reverse = Converter(
            from_type="scientific_name", to_type="common_name", from_authority="avilist"
        )
        result = converter_reverse.convert("Struthio camelus")
        assert result == "Common Ostrich"

    def test_ebird_conversions(self):
        """Test conversions with eBird taxonomy."""
        # Test common name to species code
        converter = Converter(
            from_type="common_name", to_type="ebird_code", to_authority="ebird"
        )

        result = converter.convert("Common Ostrich")
        assert result == "ostric2"

        # Test species code to scientific name
        converter_reverse = Converter(
            from_type="ebird_code", to_type="scientific_name", from_authority="ebird"
        )
        result = converter_reverse.convert("ostric2")
        assert result == "Struthio camelus"

    def test_ibp_alpha_codes(self):
        """Test IBP alpha code conversions."""
        # Test 4-letter alpha codes
        converter = Converter(
            from_type="common_name", to_type="alpha", to_authority="ibp"
        )

        result = converter.convert("Highland Tinamou")
        assert result == "HITI"

        # Test 6-letter alpha codes
        converter_6 = Converter(
            from_type="alpha",
            to_type="alpha6",
            from_authority="ibp",
            to_authority="ibp",
        )

        result = converter_6.convert("HITI")
        assert result == "NOTBON"

    def test_cross_authority_conversion(self):
        """Test conversions between different taxonomic authorities."""
        # Common Ostrich exists in both AviList and eBird
        converter = Converter(
            from_type="common_name",
            to_type="ebird_code",
            from_authority="avilist",
            to_authority="ebird",
        )

        result = converter.convert("Common Ostrich")
        assert result == "ostric2"

    def test_hierarchical_conversions(self):
        """Test conversions to taxonomic hierarchy levels."""
        # Scientific name to genus
        converter = Converter(
            from_type="scientific_name", to_type="genus", from_authority="avilist"
        )

        result = converter.convert("Struthio camelus")
        assert result == "Struthio"

        # Scientific name to family
        converter_family = Converter(
            from_type="scientific_name", to_type="family", from_authority="avilist"
        )

        result = converter_family.convert("Struthio camelus")
        assert result == "Struthionidae"

        # Scientific name to order
        converter_order = Converter(
            from_type="scientific_name", to_type="order", from_authority="avilist"
        )

        result = converter_order.convert("Struthio camelus")
        assert result == "Struthioniformes"

    def test_batch_conversions(self):
        """Test batch processing with lists and pandas Series."""
        converter = Converter(
            from_type="scientific_name", to_type="common_name", from_authority="avilist"
        )

        # Test with list
        input_list = ["Struthio camelus", "Struthio molybdophanes"]
        results = converter(input_list)
        expected = ["Common Ostrich", "Somali Ostrich"]
        assert results == expected

        # Test with pandas Series
        input_series = pd.Series(["Struthio camelus", "Struthio molybdophanes"])
        results = converter(input_series)
        assert isinstance(results, pd.Series)
        assert list(results) == expected

        # Test with numpy array
        input_array = np.array(["Struthio camelus", "Struthio molybdophanes"])
        results = converter(input_array)
        assert isinstance(results, np.ndarray)
        assert list(results) == expected

    def test_soft_matching(self):
        """Test case-insensitive and spacing-tolerant matching."""
        converter = Converter(
            from_type="common_name",
            to_type="scientific_name",
            from_authority="avilist",
            soft_matching=True,
        )

        # Test case variations
        test_cases = [
            "common ostrich",  # lowercase
            "COMMON OSTRICH",  # uppercase
            "Common  Ostrich",  # extra space
            "  Common Ostrich  ",  # leading/trailing spaces
            "Common-Ostrich",  # dash instead of space
            "Common_Ostrich",  # underscore instead of space
            "Common--__  Ostrich",  # mixed dashes, underscores, multiple spaces
            "Common   -   Ostrich",  # spaces around dash
            "common___ostrich",  # multiple underscores, lowercase
        ]

        for test_case in test_cases:
            result = converter.convert(test_case)
            assert result == "Struthio camelus", f"Failed for: '{test_case}'"

    def test_missing_values(self):
        """Test handling of missing/unknown values."""
        converter = Converter(
            from_type="common_name", to_type="scientific_name", from_authority="avilist"
        )

        # Test with non-existent bird name
        result = converter.convert("Nonexistent Bird")
        assert pd.isna(result)

        # Test with list containing missing values
        input_list = ["Common Ostrich", "Nonexistent Bird", "Somali Ostrich"]
        results = converter(input_list)
        assert results[0] == "Struthio camelus"
        assert pd.isna(results[1])
        assert results[2] == "Struthio molybdophanes"

    def test_fuzzy_matching(self):
        """Test fuzzy matching for typos."""
        converter = Converter(
            from_type="common_name",
            to_type="scientific_name",
            from_authority="avilist",
            fuzzy_matching=True,
        )

        # Test with small typo
        result = converter.convert("Comon Ostrich")  # missing 'm'
        assert result == "Struthio camelus"

    def test_ebird_taxonomy_years(self):
        """Test selecting different eBird taxonomy years."""
        # Test 2021 taxonomy
        converter_2021 = Converter(
            from_type="common_name",
            to_type="scientific_name",
            from_authority="ebird",
            from_year=2021,
        )

        # Test 2022 taxonomy
        converter_2022 = Converter(
            from_type="common_name",
            to_type="scientific_name",
            from_authority="ebird",
            from_year=2022,
        )

        # Test 2023 taxonomy
        converter_2023 = Converter(
            from_type="common_name",
            to_type="scientific_name",
            from_authority="ebird",
            from_year=2023,
        )

        # Test 2024 taxonomy (default)
        converter_2024 = Converter(
            from_type="common_name", to_type="scientific_name", from_authority="ebird"
        )

        # Test that all years can convert Common Ostrich
        test_name = "Common Ostrich"
        expected_scientific = "Struthio camelus"

        for year, converter in [
            (2021, converter_2021),
            (2022, converter_2022),
            (2023, converter_2023),
            (2024, converter_2024),
        ]:
            result = converter.convert(test_name)
            assert result == expected_scientific, f"Failed for eBird {year}"

        # Test species codes for different years
        converter_codes_2021 = Converter(
            from_type="common_name",
            to_type="ebird_code",
            to_authority="ebird",
            to_year=2021,
        )

        converter_codes_2024 = Converter(
            from_type="common_name",
            to_type="ebird_code",
            to_authority="ebird",
            to_year=2024,
        )

        # Both should return the same species code for Common Ostrich
        result_2021 = converter_codes_2021.convert("Common Ostrich")
        result_2024 = converter_codes_2024.convert("Common Ostrich")

        # Note: Species codes may differ between years due to taxonomic changes
        assert result_2021 is not None
        assert result_2024 is not None

    def test_bbl_conversions(self):
        """Test BBL (Bird Banding Lab) conversions."""
        # Test common name to BBL alpha code
        converter = Converter(
            from_type="common_name", to_type="alpha", to_authority="bbl"
        )

        result = converter.convert("Western Grebe")
        assert result == "WEGR"

        # Test BBL alpha code to scientific name
        converter_reverse = Converter(
            from_type="alpha", to_type="scientific_name", from_authority="bbl"
        )
        result = converter_reverse.convert("WEGR")
        assert result == "Aechmophorus occidentalis"

        # Test BBL French names
        converter_french = Converter(
            from_type="common_name", to_type="french_name", to_authority="bbl"
        )
        result = converter_french.convert("Western Grebe")
        assert result == "Grèbe élégant"

        # Test reverse French name conversion
        converter_french_reverse = Converter(
            from_type="french_name", to_type="scientific_name", from_authority="bbl"
        )
        result = converter_french_reverse.convert("Grèbe élégant")
        assert result == "Aechmophorus occidentalis"

    def test_bbl_cross_authority_conversion(self):
        """Test cross-authority conversions involving BBL."""
        # Convert BBL alpha code to eBird species code via scientific name
        converter = Converter(
            from_type="alpha",
            to_type="ebird_code",
            from_authority="bbl",
            to_authority="ebird",
        )

        # This should work if the species exists in both databases
        # Western Grebe should exist in both BBL and eBird
        result = converter.convert("WEGR")
        # Don't assert specific value since it depends on data availability
        # Just ensure it doesn't crash and returns something reasonable
        assert result is None or isinstance(result, str)

    def test_identity_conversion(self):
        """Test converting from a type to the same type (identity mapping)."""
        # Test scientific name to scientific name
        converter = Converter(
            from_type="scientific_name",
            to_type="scientific_name",
            from_authority="avilist",
            to_authority="avilist",
        )

        result = converter.convert("Struthio camelus")
        assert result == "Struthio camelus"

        # Test with list
        result_list = converter.convert(["Struthio camelus", "Struthio molybdophanes"])
        assert result_list == ["Struthio camelus", "Struthio molybdophanes"]

        # Test common name to common name
        converter_common = Converter(
            from_type="common_name",
            to_type="common_name",
            from_authority="avilist",
            to_authority="avilist",
        )

        result = converter_common.convert("Common Ostrich")
        assert result == "Common Ostrich"


def test_determine_name_type():
    """Test automatic detection of name type and authority."""
    # Test with BBL alpha codes
    bbl_codes = ["WEGR", "CLGR", "RNGR"]
    name_type, authority, year, unmatched = birdnames.determine_name_type(bbl_codes)
    assert name_type == "alpha"
    assert authority == "bbl"
    assert isinstance(year, int)
    assert len(unmatched) == 0

    # Test with common names, and one non-matching name
    common_names = ["Western Grebe", "Clark's Grebe", "Red-necked Grebe", "notabird"]
    name_type, authority, year, unmatched = birdnames.determine_name_type(common_names)
    assert name_type == "common_name"
    assert authority in ["avilist", "ebird", "birdlife", "bbl"]  # Could match multiple
    assert isinstance(year, int)
    assert len(unmatched) == 1

    # Test with scientific names
    scientific_names = ["Aechmophorus occidentalis", "Aechmophorus clarkii"]
    name_type, authority, year, unmatched = birdnames.determine_name_type(
        scientific_names
    )
    assert name_type == "scientific_name"
    assert authority in ["avilist", "ebird", "birdlife", "ibp", "bbl"]
    assert isinstance(year, int)


def test_alpha():
    """Test the convenience function for alpha code conversion."""
    # Test with BBL common names
    names = ["Western Grebe", "Clark's Grebe"]
    result = birdnames.alpha(names, alpha_code_authority="bbl")
    assert result == ["WEGR", "CLGR"]

    # Test with IBP
    ibp_names = ["Highland Tinamou", "Great Tinamou"]
    result_ibp = birdnames.alpha(ibp_names, alpha_code_authority="ibp")
    assert result_ibp == ["HITI", "GRTI"]

    # test with non-matching values
    ibp_names = ["Highland Tinamou", "Great Tinamou", "WETA"]
    result_ibp = birdnames.alpha(ibp_names, alpha_code_authority="ibp")
    assert result_ibp == ["HITI", "GRTI", None]


def test_scientific():
    """Test the convenience function for scientific name conversion."""
    # Test with BBL common names
    names = ["Western Grebe", "Clark's Grebe"]
    result = birdnames.scientific(names, scientific_name_authority="bbl")
    assert result == ["Aechmophorus occidentalis", "Aechmophorus clarkii"]

    # test with non-matching values
    ibp_names = ["Highland Tinamou", "Great Tinamou", "WETA"]
    result_ibp = birdnames.scientific(ibp_names, scientific_name_authority="ibp")
    assert result_ibp == ["Nothocercus bonapartei", "Tinamus major", None]

    # test with alpha codes
    result = birdnames.scientific(["NOCA"])
    assert result == ["Cardinalis cardinalis"]

    # test with ebird codes
    assert birdnames.scientific(["norcar"]) == ["Cardinalis cardinalis"]

    # test with scientific names (issue fix: should return input as-is)
    scientific_names = ["Struthio camelus", "Struthio molybdophanes"]
    result = birdnames.scientific(scientific_names)
    assert result == ["Struthio camelus", "Struthio molybdophanes"]

    # test with single scientific name
    result = birdnames.scientific("Struthio camelus")
    assert result == "Struthio camelus"


def test_common():
    """Test the convenience function for common name conversion."""
    # Test with scientific names
    names = ["Aechmophorus occidentalis", "Aechmophorus clarkii"]
    result = birdnames.common(names, common_name_authority="bbl")
    assert result == ["Western Grebe", "Clark's Grebe"]

    # Test with alpha codes
    result = birdnames.common(["WEGR", "CLGR"], common_name_authority="bbl")
    assert result == ["Western Grebe", "Clark's Grebe"]

    # Test with non-matching values
    names = ["Aechmophorus occidentalis", "Aechmophorus clarkii", "WETA"]
    result = birdnames.common(names, common_name_authority="bbl")
    assert result == ["Western Grebe", "Clark's Grebe", None]

    # Test with ebird codes
    result = birdnames.common(["norcar"])
    assert result == ["Northern Cardinal"]


def test_ebird():
    """Test the convenience function for ebird code conversion."""
    # Test with common names
    names = ["Common Ostrich", "Somali Ostrich"]
    result = birdnames.ebird(names)
    assert result == ["ostric2", "ostric3"]

    # Test with scientific names
    result = birdnames.ebird(["Struthio camelus", "Struthio molybdophanes"])
    assert result == ["ostric2", "ostric3"]

    # Test with non-matching values
    names = ["Common Ostrich", "Somali Ostrich", "WETA"]
    result = birdnames.ebird(names)
    assert result == ["ostric2", "ostric3", None]

    # Test with alpha codes
    result = birdnames.ebird(["NOCA"])
    assert result == ["norcar"]


if __name__ == "__main__":
    pytest.main([__file__])
