from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PLACES_PATH = PROCESSED_DIR / "places.csv"


def load_places(path: Path = PLACES_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";").copy()

    expected_columns = ["place_id", "place_name", "lat", "lon"]
    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        raise ValueError(f"places.csv fehlt erforderliche Spalten: {missing}")

    for col in ["place_id", "place_name"]:
        df[col] = df[col].astype(str).str.strip()

    for col in ["lat", "lon"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "is_featured" in df.columns:
        df["is_featured"] = (
            df["is_featured"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({"true": True, "false": False})
        )

    return df


def get_place_options(places_df: pd.DataFrame) -> list[dict]:
    places = (
        places_df[["place_id", "place_name"]]
        .drop_duplicates()
        .sort_values("place_name")
    )

    return [
        {"label": row["place_name"], "value": row["place_id"]}
        for _, row in places.iterrows()
    ]


def merge_places_into_profiles(
    profiles_df: pd.DataFrame,
    places_df: pd.DataFrame,
) -> pd.DataFrame:
    place_cols = [col for col in ["place_id", "place_name", "lat", "lon"] if col in places_df.columns]

    merged = profiles_df.merge(
        places_df[place_cols].drop_duplicates(subset=["place_id"]),
        on="place_id",
        how="left",
        suffixes=("", "_places"),
    )

    if "place_name_places" in merged.columns:
        merged["place_name"] = merged["place_name"].fillna(merged["place_name_places"])
        merged = merged.drop(columns=["place_name_places"])

    return merged


def validate_places_against_profiles(
    profiles_df: pd.DataFrame,
    places_df: pd.DataFrame,
) -> dict:
    profile_ids = set(profiles_df["place_id"].dropna().astype(str).unique())
    places_ids = set(places_df["place_id"].dropna().astype(str).unique())

    missing_in_places = sorted(profile_ids - places_ids)
    unused_in_places = sorted(places_ids - profile_ids)

    return {
        "missing_in_places": missing_in_places,
        "unused_in_places": unused_in_places,
    }


def get_map_df(places_df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        col for col in [
            "place_id",
            "place_name",
            "lat",
            "lon",
            "zone_label",
            "canton",
            "language_region",
            "place_type",
            "is_featured",
            "short_description",
            "elevation_m"
        ]
        if col in places_df.columns
    ]

    map_df = (
        places_df[cols]
        .drop_duplicates(subset=["place_id"])
        .dropna(subset=["lat", "lon"])
        .sort_values("place_name")
        .reset_index(drop=True)
    )

    return map_df
