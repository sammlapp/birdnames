# BirdNames

A Python package for managing avian taxonomy and converting between different bird name formats across multiple taxonomic authorities.

## Features

- Convert between scientific names, common names, 4-letter alpha codes, 6-letter alpha codes, and species codes
- Support for multiple taxonomic authorities: AviList, eBird/Clements, BirdLife, and IBP
- Cross-authority conversions using scientific names as bridge
- Hierarchical conversions (species → genus → family → order)
- Fuzzy matching for handling typos and variations
- Batch processing support for lists, numpy arrays, and pandas Series

## Installation

```bash
pip install birdnames
```

## Quick Start

```python
import birdnames as bn

# Basic conversion within same authority
converter = bn.Converter(
    from_type="common_name",
    to_type="scientific_name",
    from_authority="avilist"
)

result = converter.convert("American Robin")
print(result)  # "Turdus migratorius"
```

## Usage Examples

### Common Name to Scientific Name

```python
import birdnames as bn

converter = bn.Converter(
    from_type="common_name",
    to_type="scientific_name",
    from_authority="avilist"
)

# Single conversion
scientific_name = converter.convert("American Robin")
print(scientific_name)  # "Turdus migratorius"

# Batch conversion
common_names = ["American Robin", "Blue Jay", "Northern Cardinal"]
scientific_names = converter.convert(common_names)
print(scientific_names)
# ["Turdus migratorius", "Cyanocitta cristata", "Cardinalis cardinalis"]
```

### Common Name to 4-Letter Alpha Codes (IBP)

```python
# Convert common names to 4-letter alpha codes
converter = bn.Converter(
    from_type="common_name",
    to_type="alpha_code_4",
    from_authority="avilist",
    to_authority="ibp"
)

alpha_code = converter.convert("American Robin")
print(alpha_code)  # "AMRO"

# Batch conversion
common_names = ["American Robin", "Blue Jay", "Northern Cardinal"]
alpha_codes = converter.convert(common_names)
print(alpha_codes)  # ["AMRO", "BLJA", "NOCA"]
```

### Common Name to eBird Species Codes

```python
# Convert common names to eBird species codes
converter = bn.Converter(
    from_type="common_name",
    to_type="species_code",
    from_authority="avilist",
    to_authority="ebird"
)

species_code = converter.convert("American Robin")
print(species_code)  # "amero"

# Batch conversion
common_names = ["American Robin", "Blue Jay", "Northern Cardinal"]
species_codes = converter.convert(common_names)
print(species_codes)  # ["amero", "blujay", "norcar"]
```

### Cross-Authority Conversions

```python
# Convert eBird species codes to IBP alpha codes
converter = bn.Converter(
    from_type="species_code",
    to_type="alpha_code_4",
    from_authority="ebird",
    to_authority="ibp"
)

alpha_code = converter.convert("amero")
print(alpha_code)  # "AMRO"
```

### Hierarchical Conversions

```python
# Convert species to genus
converter = bn.Converter(
    from_type="scientific_name",
    to_type="genus"
)

genus = converter.convert("Turdus migratorius")
print(genus)  # "Turdus"

# Convert species to family
converter = bn.Converter(
    from_type="common_name",
    to_type="family",
    from_authority="avilist"
)

family = converter.convert("American Robin")
print(family)  # "Turdidae"

# Convert species to order
converter = bn.Converter(
    from_type="scientific_name",
    to_type="order",
    from_authority="avilist"
)

order = converter.convert("Turdus migratorius")
print(order)  # "Passeriformes"
```

### Working with Pandas DataFrames

```python
import pandas as pd
import birdnames as bn

# Create sample data
df = pd.DataFrame({
    'common_name': ['American Robin', 'Blue Jay', 'Northern Cardinal']
})

# Convert to scientific names
converter = bn.Converter(
    from_type="common_name",
    to_type="scientific_name",
    from_authority="avilist"
)

df['scientific_name'] = converter.convert(df['common_name'])
print(df)
```

### Advanced Options

```python
# Enable fuzzy matching for typos
converter = bn.Converter(
    from_type="common_name",
    to_type="scientific_name",
    from_authority="avilist",
    fuzzy_matching=True
)

result = converter.convert("Amercan Robin")  # Note the typo
print(result)  # "Turdus migratorius"

# Disable soft matching (case/spacing insensitive)
converter = bn.Converter(
    from_type="common_name",
    to_type="scientific_name",
    from_authority="avilist",
    soft_matching=False
)
```

## Supported Name Types

- `"scientific_name"`: Scientific/binomial names (e.g., "Turdus migratorius")
- `"common_name"`: English common names (e.g., "American Robin")
- `"genus"`: Genus names (e.g., "Turdus")
- `"family"`: Family names (e.g., "Turdidae")
- `"order"`: Order names (e.g., "Passeriformes")
- `"alpha_code_4"`: 4-letter alpha codes (IBP only, e.g., "AMRO")
- `"alpha_code_6"`: 6-letter alpha codes (IBP only, e.g., "AMROBI")
- `"species_code"`: eBird species codes (eBird only, e.g., "amero")

## Supported Taxonomic Authorities

- `"avilist"`: AviList global unified bird taxonomy
- `"ebird"`: eBird/Clements Checklist
- `"birdlife"`: BirdLife International taxonomy
- `"ibp"`: Institute for Bird Populations (North American species)

## Data Sources

The package integrates data from:

- **AviList**: Global unified bird taxonomy with scientific names, English common names, and taxonomic hierarchy
- **eBird/Clements**: Cornell Lab's taxonomy with common names and 6-letter species codes
- **BirdLife International**: Global taxonomy with IUCN Red List status
- **IBP**: Institute for Bird Populations with 4-letter and 6-letter alpha codes for North American species

## Development

### Data Ingestion

To update taxonomy data, run the ingestion script:

```bash
python ingest_taxonomies.py
```

This will process the raw taxonomy files and create standardized CSV files for the package.

### Testing

```bash
pytest tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Citation

If you use this package in your research, please cite:

```
BirdNames: A Python package for avian taxonomy management
```