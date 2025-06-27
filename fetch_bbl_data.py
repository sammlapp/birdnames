#!/usr/bin/env python3
"""
Script to fetch BBL (Bird Banding Lab) 4-letter alpha codes from USGS website.
Based on Tessa Rhinehart's Goldeneye extension code.
"""

import pandas as pd
from pathlib import Path


def fetch_bbl_data():
    """Fetch BBL data from USGS website and save to CSV."""
    print("Fetching BBL data from USGS website...")

    try:
        # Fetch the table from the BBL website
        [bbl_table] = pd.read_html(
            "https://www.pwrc.usgs.gov/BBL/Bander_Portal/login/speclist.php"
        )

        # Select and rename columns
        bbl_table = bbl_table[
            ["Scientific Name", "Common Name", "Alpha Code", "French Name", "T & E*"]
        ]
        bbl_table.columns = [
            "scientific_name",
            "bbl_common_name",
            "bbl_alpha_code_4",
            "bbl_french_name",
            "bbl_threatened_endangered",
        ]

        # Clean up the data
        bbl_table["scientific_name"] = bbl_table["scientific_name"].str.strip()
        bbl_table["bbl_common_name"] = bbl_table["bbl_common_name"].str.strip()
        bbl_table["bbl_alpha_code_4"] = bbl_table["bbl_alpha_code_4"].str.strip()

        # Remove rows where scientific name is empty or NA
        bbl_table = bbl_table.dropna(subset=["scientific_name"])
        bbl_table = bbl_table[bbl_table["scientific_name"] != ""]

        # Add genus column
        bbl_table["genus"] = bbl_table["scientific_name"].str.split().str[0]

        # Save to processed data directory
        data_dir = Path(__file__).parent / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)

        output_file = data_dir / "bbl_2024_taxonomy.csv"
        bbl_table.to_csv(output_file, index=False)

        print(f"Successfully saved {len(bbl_table)} BBL records to {output_file}")
        print(f"Sample records:")
        print(bbl_table.head())

        return bbl_table

    except Exception as e:
        print(f"Error fetching BBL data: {e}")
        return None


if __name__ == "__main__":
    fetch_bbl_data()
