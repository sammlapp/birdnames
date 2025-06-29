#!/usr/bin/env python3
"""
Taxonomy ingestion script for birdnames package.
Processes taxonomy files and creates standardized CSV files.
Creates individual authority files plus a merged table keyed by scientific name.
"""

import pandas as pd
from pathlib import Path


def ingest_ebird_clements(file_path):
    """Process eBird/Clements taxonomy CSV file."""
    print("Processing eBird/Clements taxonomy...")

    df = pd.read_csv(file_path, encoding="utf-8-sig")

    # options for common name column:
    df = df.rename(
        columns={
            "PRIMARY_COM_NAME": "English name",
            "SCI_NAME": "scientific name",
            "ORDER1": "order",
            "FAMILY": "family",
        }
    )

    # convert column names to lowercase
    df.columns = df.columns.str.lower()

    # Filter to species only (category == 'species')
    species_df = df[df["category"] == "species"].copy()

    # Create standardized output
    output_df = species_df[
        ["scientific name", "english name", "species_code", "order", "family"]
    ].copy()
    output_df.columns = [
        "scientific_name",
        "ebird_common_name",
        "ebird_ebird_code",
        "ebird_order",
        "ebird_family",
    ]

    # Clean family names
    output_df["ebird_family"] = output_df["ebird_family"].str.replace(
        r" \(.*\)", "", regex=True
    )

    # Extract genus from scientific name (first part before space)
    output_df["genus"] = output_df["scientific_name"].str.split().str[0]

    print(f"Processed {len(output_df)} eBird species")
    return output_df


def ingest_ibp(file_path):
    """Process IBP alpha codes CSV file."""
    print("Processing IBP taxonomy...")

    df = pd.read_csv(file_path)

    # Filter rows with valid data
    valid_df = df[df["SPEC"].notna() & df["SCINAME"].notna()].copy()

    output_df = valid_df[["SCINAME", "COMMONNAME", "SPEC", "SPEC6"]].copy()
    output_df.columns = [
        "scientific_name",
        "ibp_common_name",
        "ibp_alpha",
        "ibp_alpha6",
    ]

    # Extract genus from scientific name (first part before space)
    output_df["genus"] = output_df["scientific_name"].str.split().str[0]

    print(f"Processed {len(output_df)} IBP species")
    return output_df


def ingest_birdlife(file_path):
    """Process BirdLife Excel file."""
    print("Processing BirdLife taxonomy...")

    df = pd.read_excel(file_path)

    # Expected columns: Seq, Order, Family, Family name, Common name, Scientific name, 2024 IUCN Red List category
    output_df = df[
        [
            "Scientific name",
            "Common name",
            "Order",
            "Family name",
            "2024 IUCN Red List category",
        ]
    ].copy()
    output_df.columns = [
        "scientific_name",
        "birdlife_common_name",
        "birdlife_order",
        "birdlife_family",
        "birdlife_iucn_status",
    ]

    # Remove rows with empty scientific names
    output_df = output_df[output_df["scientific_name"].notna()]
    output_df = output_df[output_df["scientific_name"].astype(str).str.strip() != ""]

    # Extract genus from scientific name (first part before space)
    output_df["genus"] = output_df["scientific_name"].str.split().str[0]

    print(f"Processed {len(output_df)} BirdLife entries")
    return output_df


def ingest_avilist(file_path):
    """Process AviList Excel file."""
    print("Processing AviList taxonomy...")

    df = pd.read_excel(file_path)

    # Use known column names from AviList - include taxonomic hierarchy and rank
    output_df = df[
        [
            "Scientific_name",
            "English_name_AviList",
            "Taxon_rank",
            "Order",
            "Family",
            "IUCN_Red_List_Category",
            "AvibaseID",
        ]
    ].copy()

    output_df.columns = [
        "scientific_name",
        "avilist_common_name",
        "avilist_taxon_rank",
        "avilist_order",
        "avilist_family",
        "avilist_iucn_status",
        "avilist_avibase_id",
    ]

    # Remove rows with empty scientific names
    output_df = output_df[output_df["scientific_name"].notna()]
    output_df = output_df[output_df["scientific_name"].astype(str).str.strip() != ""]

    # Extract genus from scientific name (first part before space)
    output_df["genus"] = output_df["scientific_name"].str.split().str[0]

    print(f"Processed {len(output_df)} AviList entries")
    return output_df


def discover_taxonomy_files():
    """Discover all taxonomy files in the taxonomies directory structure."""
    taxonomies_dir = Path("taxonomies")
    taxonomy_files = {}

    if not taxonomies_dir.exists():
        print(f"Warning: {taxonomies_dir} directory not found")
        return taxonomy_files

    # Walk through authority/year structure
    for authority_dir in taxonomies_dir.iterdir():
        if not authority_dir.is_dir():
            continue

        authority = authority_dir.name
        taxonomy_files[authority] = {}

        for year_dir in authority_dir.iterdir():
            if not year_dir.is_dir():
                continue

            year = year_dir.name

            # Find the first file in the year directory
            files_in_year = list(year_dir.iterdir())
            data_files = [
                f for f in files_in_year if f.is_file() and not f.name.startswith(".")
            ]

            if data_files:
                taxonomy_files[authority][year] = data_files[0]
                print(f"Found {authority} {year}: {data_files[0].name}")
            else:
                print(f"Warning: No data files found in {year_dir}")

    return taxonomy_files


def main():
    """Main ingestion function."""
    output_dir = Path(__file__).parent.parent / "data/processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Discover all taxonomy files
    taxonomy_files = discover_taxonomy_files()

    # keep a list of all available taxonomies
    all_taxonomies = []

    if not taxonomy_files:
        print("No taxonomy files found!")
        return

    # Process each authority and year
    for authority, years in taxonomy_files.items():
        print(f"\nProcessing {authority}...")

        for year, file_path in years.items():
            print(f"  Processing {authority} {year}: {file_path.name}")

            try:
                if authority == "ebird":
                    df = ingest_ebird_clements(file_path)
                elif authority == "ibp":
                    df = ingest_ibp(file_path)
                elif authority == "birdlife":
                    df = ingest_birdlife(file_path)
                elif authority == "avilist":
                    df = ingest_avilist(file_path)
                elif authority == "bbl":
                    # BBL files are already processed to expected format in fetch_bbl_data.py
                    df = pd.read_csv(file_path)
                else:
                    print(f"    Unknown authority: {authority}, skipping")
                    continue

                # Save authority-year specific CSV file
                output_file = output_dir / f"{authority}_{year}_taxonomy.csv"
                df.to_csv(output_file, index=False)

                # Add to all taxonomies, with boolean flags for whether columns exist
                all_taxonomies.append(
                    {
                        "authority": authority,
                        "year": year,
                        "scientific_name": "scientific_name" in df.columns,
                        "common_name": f"{authority}_common_name" in df.columns,
                        "alpha": f"{authority}_alpha" in df.columns,
                        "alpha6": f"{authority}_alpha6" in df.columns,
                        "ebird_code": f"{authority}_ebird_code" in df.columns,
                        "order": f"{authority}_order" in df.columns,
                        "family": f"{authority}_family" in df.columns,
                        "genus": "genus" in df.columns,
                        "french_name": f"{authority}_french_name" in df.columns,
                        "entries": len(df),
                    }
                )

                print(f"    Saved to {output_file}")
                print(f"    Processed {len(df)} entries")

            except Exception as e:
                print(f"    Error processing {authority} {year}: {e}")
                continue

    # create dataframe listing available taxonomies
    all_taxonomies_df = pd.DataFrame(all_taxonomies)
    all_taxonomies_file = output_dir.parent / "available_taxonomies.csv"
    all_taxonomies_df.to_csv(all_taxonomies_file, index=False)

    print("\nIngestion complete!")


if __name__ == "__main__":
    main()
