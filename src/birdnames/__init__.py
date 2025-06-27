"""
BirdNames - A Python package for managing avian taxonomy.

Provides functionality for mapping between scientific and common names, 
and 4 and 6 letter species codes, with integration across several 
taxonomic authorities.
"""

from .converter import Converter

__version__ = "0.1.0"
__all__ = ["Converter"]