"""
Basic tests for the Converter class.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from birdnames import Converter


class TestConverter:
    """Test cases for Converter class."""
    
    def test_converter_initialization(self):
        """Test that Converter can be initialized with basic parameters."""
        converter = Converter(
            from_type="common_name",
            to_type="scientific_name",
            from_authority="avilist",
            to_authority="avilist"
        )
        
        assert converter.from_type == "common_name"
        assert converter.to_type == "scientific_name"
        assert converter.from_authority == "avilist"
        assert converter.to_authority == "avilist"
        assert converter.soft_matching is True
        assert converter.fuzzy_matching is False
    
    def test_column_name_mapping(self):
        """Test that column name mapping works correctly."""
        converter = Converter(
            from_type="common_name",
            to_type="scientific_name"
        )
        
        # Test scientific name (universal)
        assert converter._get_column_name("scientific_name", "avilist") == "scientific_name"
        
        # Test authority-specific columns
        assert converter._get_column_name("common_name", "avilist") == "avilist_common_name"
        assert converter._get_column_name("common_name", "ebird") == "ebird_common_name"
        
        # Test IBP alpha codes
        assert converter._get_column_name("alpha_code_4", "ibp") == "ibp_alpha_code_4"
        assert converter._get_column_name("alpha_code_6", "ibp") == "ibp_alpha_code_6"
        
        # Test eBird species codes
        assert converter._get_column_name("species_code", "ebird") == "ebird_species_code"
    
    def test_invalid_combinations(self):
        """Test that invalid type/authority combinations raise errors."""
        converter = Converter(
            from_type="common_name",
            to_type="scientific_name"
        )
        
        # Alpha codes only available for IBP
        with pytest.raises(ValueError):
            converter._get_column_name("alpha_code_4", "avilist")
        
        # Species codes only available for eBird
        with pytest.raises(ValueError):
            converter._get_column_name("species_code", "avilist")
        
        # Unknown name type
        with pytest.raises(ValueError):
            converter._get_column_name("unknown_type", "avilist")
    
    def test_string_normalization(self):
        """Test string normalization for soft matching."""
        converter = Converter(
            from_type="common_name",
            to_type="scientific_name",
            soft_matching=True
        )
        
        assert converter._normalize_string("  American Robin  ") == "american robin"
        assert converter._normalize_string("BLUE JAY") == "blue jay"
        
        # Test with soft matching disabled
        converter.soft_matching = False
        assert converter._normalize_string("  American Robin  ") == "  American Robin  "
    
    def test_input_type_handling(self):
        """Test that different input types are handled correctly."""
        # This test would require actual data files, so we'll mock the behavior
        # In a real implementation, you'd want to create test data files
        
        # Test that the convert method accepts different input types
        converter = Converter(
            from_type="common_name",
            to_type="scientific_name"
        )
        
        # These would fail without data, but test the type checking logic
        test_inputs = [
            "American Robin",  # string
            ["American Robin", "Blue Jay"],  # list
            pd.Series(["American Robin", "Blue Jay"]),  # pandas Series
        ]
        
        for test_input in test_inputs:
            try:
                # This will likely fail due to missing data files, but shouldn't fail on type checking
                result = converter.convert(test_input)
            except FileNotFoundError:
                # Expected when data files don't exist
                pass
            except TypeError as e:
                # Should not get type errors
                pytest.fail(f"Unexpected TypeError for input {type(test_input)}: {e}")


if __name__ == "__main__":
    pytest.main([__file__])