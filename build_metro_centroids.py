"""
Build metro centroids reference file from Census CBSA gazetteer.
Input: Census 2023 CBSA gazetteer (downloaded automatically)
Output: labor-gap-app/data/metro_centroids.csv
"""

from pathlib import Path
import pandas as pd
import urllib.request
import io
import zipfile
import tempfile

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# CBSA gazetteer URL (2023 vintage - zipped)
GAZETTEER_URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_cbsa_national.zip"


def build_centroids():
    """Download Census CBSA gazetteer and extract metro centroids."""

    # Download gazetteer zip
    print("Downloading Census CBSA gazetteer (2023)...")
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        urllib.request.urlretrieve(GAZETTEER_URL, tmp.name)
        tmp_path = tmp.name

    # Extract and read
    with zipfile.ZipFile(tmp_path, "r") as zf:
        names = zf.namelist()
        txt_name = [n for n in names if n.endswith(".txt")][0]
        with zf.open(txt_name) as f:
            gaz = pd.read_csv(f, sep="\t")

    Path(tmp_path).unlink(missing_ok=True)

    # Clean column names (Census adds trailing spaces)
    gaz.columns = gaz.columns.str.strip()

    # Rename to our conventions
    gaz = gaz.rename(columns={
        "GEOID": "met2013",
        "NAME": "metro_name",
        "INTPTLAT": "lat",
        "INTPTLONG": "lon",
    })

    # Keep only columns we need
    gaz = gaz[["met2013", "metro_name", "lat", "lon"]].copy()
    print(f"Gazetteer has {len(gaz)} CBSAs")

    # Load our tightness data to get the 260 metros we need
    tightness_path = Path(__file__).parent.parent / "tightness_wage_metro.csv"
    if not tightness_path.exists():
        tightness_path = DATA_DIR / "tightness_wage_metro.csv"
    tw = pd.read_csv(tightness_path, usecols=["met2013", "state_abbr"])
    our_metros = tw.drop_duplicates("met2013")[["met2013", "state_abbr"]]
    print(f"Our data has {len(our_metros)} metros")

    # Merge
    merged = our_metros.merge(gaz, on="met2013", how="left")

    # Check for missing
    missing = merged[merged["lat"].isna()]
    if len(missing) > 0:
        print(f"\nMissing {len(missing)} metros from gazetteer:")
        print(missing[["met2013", "state_abbr"]])

        # Manual fallback for 2013-vintage CBSAs renamed/recoded by 2023
        manual = {
            # Canton-Massillon, OH (was 17460, now 15940)
            17460: ("Canton-Massillon, OH Metro Area", 40.711051, -81.261468),
            # Dayton, OH (was 19380, now 19430 Dayton-Kettering-Beavercreek)
            19380: ("Dayton-Kettering-Beavercreek, OH Metro Area", 39.829746, -84.140992),
            # Prescott, AZ (was 39140, now 39150 Prescott Valley-Prescott)
            39140: ("Prescott Valley-Prescott, AZ Metro Area", 34.631071, -112.577225),
            # Madera, CA (small metro, not in 2023 gazetteer)
            31460: ("Madera, CA Metro Area", 36.961, -120.060),
            # Ocean City, NJ (small metro, not in 2023 gazetteer)
            36140: ("Ocean City, NJ Metro Area", 39.278, -74.575),
        }
        for idx, row in missing.iterrows():
            code = row["met2013"]
            if code in manual:
                name, lat, lon = manual[code]
                merged.loc[idx, "metro_name"] = name
                merged.loc[idx, "lat"] = lat
                merged.loc[idx, "lon"] = lon

    # Drop any still missing
    still_missing = merged[merged["lat"].isna()]
    if len(still_missing) > 0:
        print(f"\nStill missing {len(still_missing)} after manual fill — dropping")
        merged = merged.dropna(subset=["lat"])

    # Shorten metro names: drop " Metro Area" / " Micro Area" and state suffix
    merged["metro_name_short"] = (
        merged["metro_name"]
        .str.replace(r"\s+(Metro|Micro)\s+Area$", "", regex=True)
        .str.replace(r",\s*[A-Z]{2}(-[A-Z]{2})*$", "", regex=True)
    )

    # Sort by met2013
    merged = merged.sort_values("met2013").reset_index(drop=True)
    print(f"\nFinal centroids file: {len(merged)} metros")

    # Save
    out_path = DATA_DIR / "metro_centroids.csv"
    merged.to_csv(out_path, index=False)
    print(f"Saved to {out_path}")

    return merged


if __name__ == "__main__":
    build_centroids()
