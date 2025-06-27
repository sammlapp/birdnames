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

    # Filter to species only (category == 'species')
    species_df = df[df["category"] == "species"].copy()

    # Create standardized output
    output_df = species_df[
        ["scientific name", "English name", "species_code", "order", "family"]
    ].copy()
    output_df.columns = [
        "scientific_name",
        "ebird_common_name",
        "ebird_species_code",
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
        "ibp_alpha_code_4",
        "ibp_alpha_code_6",
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


def main():
    """Main ingestion function."""
    taxonomies_dir = Path("taxonomies")
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    # File mappings - updated for new BirdLife file
    files = {
        "ebird": taxonomies_dir
        / "eBird-Clements-v2024-integrated-checklist-October-2024-rev.csv",
        "ibp": taxonomies_dir / "IBP-AOS-LIST24.csv",
        "birdlife": taxonomies_dir / "HBW_BirdLife_List of Birds_v.9.xlsx",
        "avilist": taxonomies_dir / "AviList-v2025-11Jun-extended.xlsx",
    }

    # Process each taxonomy
    dataframes = {}
    for authority, file_path in files.items():
        if not file_path.exists():
            print(f"Warning: {file_path} not found, skipping {authority}")
            continue

        try:
            if authority == "ebird":
                df = ingest_ebird_clements(file_path)
            elif authority == "ibp":
                df = ingest_ibp(file_path)
            elif authority == "birdlife":
                df = ingest_birdlife(file_path)
            elif authority == "avilist":
                df = ingest_avilist(file_path)

            # Save individual authority CSV file
            output_file = output_dir / f"{authority}_taxonomy.csv"
            df.to_csv(output_file, index=False)
            print(f"Saved {authority} data to {output_file}")

            dataframes[authority] = df

        except Exception as e:
            print(f"Error processing {authority}: {e}")
            continue

    print("\nIngestion complete!")

    # Print summary by authority
    for authority, df in dataframes.items():
        print(f"  {authority}: {len(df)} species")


if __name__ == "__main__":
    main()
