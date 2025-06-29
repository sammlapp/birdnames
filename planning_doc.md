# BirdNames
birdnames is a python package for managing avian taxonomy. 

It provides functionality for mapping between scientific and common names, and 4 and 6 letter species codes, with integration across several taxonomic authorities:
Avilist, the newly created global unified bird taxonomy (scientific names, English common names, and higher taxonomic orders)
Ebird: common names and 6-letter codes
IBP (Institute for Bird Populations): common names, scientific names, and 4-letter alpha codes for North American species
BBL (Breeding Bird Laboratory): common names, scientific names, and 4-letter alpha codes for North American species


# Package design principles:

## Core Design Principles
- **Single Responsibility**: Each module handles one aspect of taxonomy management
- **Dependency Inversion**: Abstract interfaces for data sources to support multiple taxonomic authorities
- **Immutable Data**: Taxonomy data structures should be immutable to prevent accidental corruption
- **Fail-Fast**: Explicit error handling with informative messages rather than silent failures
- **Extensibility**: Plugin architecture for adding new taxonomic authorities
- **Performance**: Lazy loading and caching for large taxonomy datasets

## Development Standards
The package must be easy to maintain. In particular, it must have a workflow for ingesting updated taxonomies, which are typically released yearly. We should be able to trigger a simple workflow that updates the taxonomies. 

The package will have a comprehensive test suite using pytest with >95% coverage. We will use black automatic code formatting and ruff for linting. Type hints are required throughout. The github repository will have a main branch and feature branches for development. Pull requests to main will be reviewed by a package maintainer and PRs will trigger a github runner that runs the test suite, checks formatting, type checking, and security scans.

The package should have detailed, user-friendly documentation using Sphinx with API reference, tutorials, and examples. Documentation will be hosted on ReadTheDocs with automatic builds from the repository.

We will use poetry for package development, and therefore dependencies will be described in a pyproject.toml file. 

The package will be published to PyPi. Releases will correspond to tags on GitHub and will use semantic versioning (starting with v0.1.0). 

# Key challenges:
conflicts and mismatches between taxonomies: we should handle these elegantly, without silent errors

# Features

## Core Features
- **Universal Name Conversion**: Convert between any name type (common name, scientific name, 4-letter code, 6-letter code) across taxonomic authorities
- **Multi-year Taxonomy Support**: Access historical taxonomies by year with most recent as default
- **Fuzzy Matching**: Handle typos and variations in bird names with confidence scoring
- **Bulk Operations**: Process lists/DataFrames efficiently with batch conversion
- **Conflict Resolution**: Configurable strategies for handling taxonomic disagreements
- **Data Validation**: Verify taxonomy integrity and detect inconsistencies

## Advanced Features
- **Synonymy Tracking**: Map deprecated names to current accepted names
- **Geographic Filtering**: Filter results by region/country where applicable
- **Export Utilities**: Generate lookup tables and mapping files
- **Integration Hooks**: Pandas DataFrame support, CLI tools
- **Caching Layer**: Persistent caching for improved performance
- **Update Notifications**: Alert users when new taxonomy versions are available

# Package Structure

```
birdnames/
├── pyproject.toml
├── README.md
├── src/
│   └── birdnames/
│       ├── __init__.py
│       ├── converter.py          # Main Converter class
│       ├── sources/
│       │   ├── __init__.py
│       │   ├── avilist.py        # Avilist data handler
│       │   ├── ebird.py          # eBird data handler
│       │   ├── ibp.py            # IBP data handler
│       │   └── bbl.py            # BBL data handler
│       └── utils.py              # Fuzzy matching & utilities
├── tests/
│   ├── test_converter.py
│   └── test_sources.py
├── data/
│   └── taxonomies/              # Taxonomy data files
└── scripts/
    └── update_taxonomies.py     # Taxonomy update automation
```

# API Design

```python
import birdnames as bn

# Simple converter setup
converter = bn.Converter(
    from_type="common_name",
    to_type="scientific_name", 
    from_authority="avilist",
    to_authority="avilist",
    from_year=None,           # None = most recent
    to_year=None,
    soft_matching=True,       # Handle case/spacing differences
    fuzzy_matching=False      # Handle typos (slower)
)

# Single conversion - returns string
result = converter.convert("American Robin")
# Returns: "Turdus migratorius"

# Batch conversion - returns list of strings
results = converter.convert(["American Robin", "Blue Jay", "Cardinal"])
# Returns: ["Turdus migratorius", "Cyanocitta cristata", "Cardinalis cardinalis"]

# Works with numpy arrays and pandas Series
import pandas as pd
df = pd.DataFrame({"birds": ["American Robin", "Blue Jay"]})
df["scientific"] = converter.convert(df["birds"])

# Cross-authority conversion
cross_converter = bn.Converter(
    from_type="common_name",
    to_type="alpha_code",
    from_authority="ebird", 
    to_authority="ibp"
)
result = cross_converter.convert("American Robin")
# Returns: "AMRO"
```

# Taxonomic conversion philosophy
Use the scientific name to index between taxonomies. 


# Taxonomy sources:
Clements (eBird) taxonomy: web page: https://www.birds.cornell.edu/clementschecklist/introduction/updateindex/october-2024/2024-citation-checklist-downloads/ Download link: https://www.birds.cornell.edu/clementschecklist/wp-content/uploads/2024/10/eBird-Clements-v2024-integrated-checklist-October-2024-rev.csv ; File: eBird-Clements-v2024-integrated-checklist-October-2024-rev.csv

IBP alpha codes: https://www.birdpop.org/pages/birdSpeciesCodes.php (File: IBP-AOS-LIST24.csv; no download link, its a php page where you have to click a button to dowload)

BirdLife taxonomy: https://datazone.birdlife.org/about-our-science/taxonomy (File: HBW_BirdLife_List of Birds_v.9.xlsx) columns: Seq.	Order	Family	Family name	Common name	Scientific name	
2024 IUCN Red List category
Note: for the 2021 taxonomy I used Microsoft Excel to convert to UTF-8 encoding

Avilist: https://www.avilist.org/checklist/v2025/, download link: https://www.avilist.org/wp-content/uploads/2025/06/AviList-v2025-11Jun-extended.xlsx; File: AviList-v2025-11Jun-extended.xlsx ; 
Avilist columns: 
Sequence	Taxon_rank	Order	Family	Family_English_name	Scientific_name	Authority	Bibliographic_details	English_name_AviList	English_name_Clements_v2024	English_name_BirdLife_v9	Proposal_number	Decision_summary	Range	Extinct_or_possibly_extinct	IUCN_Red_List_Category	BirdLife_DataZone_URL	ebird_code_Cornell_Lab	Birds_of_the_World_URL	AvibaseID	Gender_of_genus	Type_species_of_genus


BBL (Bird Banding Lab) 4 letter alpha codes:
Tessa Rhinehart's Goldeneye extension provides [code](https://github.com/rhine3/goldeneye/blob/master/src/alpha-code-prep.ipynb) for parsing the php website: 

The code below grabs the table from this website - https://www.pwrc.usgs.gov/BBL/Bander_Portal/login/speclist.php
This requires installation of pandas and lxml
```python
[bbl_table] = pd.read_html("https://www.pwrc.usgs.gov/BBL/Bander_Portal/login/speclist.php")
bbl_table = bbl_table[["Scientific Name","Common Name","Alpha Code","French Name", "T & E"]]
bbl_table.columns = ['scientific_name','bbl_common_name','bbl_alpha', 'bbl_french_name']
# bbl_table.to_csv("bbl-alpha-codes_2024.csv", index=False)
```

We'll need to manually create different year versions - I'm not sure if historical versions are available. 

During ingestion: 
1. retain the order and family information about each taxon
"Order" and "Family" columns from Avilist; "Order" and "Family name" columns from BirdLife; "order" and "family" columns
2. retain the taxonomic rank of the entry (not all entries are species):
"Taxon_rank" column in avilist
