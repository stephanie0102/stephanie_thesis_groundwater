from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import time
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import geopandas as gpd
import pandas as pd
import pyogrio
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "Data" / "raw"
PROCESSED_DIR = ROOT / "Data" / "processed" / "target_download_universe"

MONITOR_GPKG = RAW_DIR / "brogmkenset.gpkg"
USE_GPKG = RAW_DIR / "bro_groundwater_use.gpkg"
CACHE_DIR = RAW_DIR / "bro_target_cache"

REGION_BBOX = (4.55, 52.20, 5.15, 52.50)
TARGET_DISTANCE_METERS = 50.0
MIN_FIRST_DATE = pd.Timestamp("2010-01-01")
MIN_LAST_DATE = pd.Timestamp("2020-01-01")

METRIC_CRS = "EPSG:28992"
SOURCE_CRS = "EPSG:4258"
BRO_GLD_CSV_URL = "https://publiek.broservices.nl/gm/gld/v1/objectsAsCsv/{gld_id}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an explicit Amsterdam target download universe from "
            "bro_groundwater_use.gpkg and brogmkenset.gpkg."
        )
    )
    parser.add_argument(
        "--distance-meters",
        type=float,
        default=TARGET_DISTANCE_METERS,
        help="Selection radius around groundwater-use objects for the download universe.",
    )
    parser.add_argument(
        "--region-bbox",
        nargs=4,
        type=float,
        default=REGION_BBOX,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Bounding box in lon/lat used to define the Amsterdam study area.",
    )
    parser.add_argument(
        "--download-cache",
        action="store_true",
        help="Download and normalize the selected GLD CSV files into Data/raw/bro_target_cache.",
    )
    parser.add_argument(
        "--replace-cache",
        action="store_true",
        help="Delete existing cache CSV files before downloading the new universe.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.20,
        help="Pause between BRO requests.",
    )
    return parser.parse_args()


def load_monitoring_tubes_with_series(bbox_tuple: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    tubes = pyogrio.read_dataframe(
        MONITOR_GPKG,
        layer="gm_gmw_monitoringtube",
        bbox=bbox_tuple,
        fid_as_index=True,
    )
    tubes = (
        tubes.reset_index()
        .rename(columns={"fid": "site_id", "gm_gmw_fk": "well_id"})
        [["site_id", "well_id", "gmw_bro_id", "tube_number", "geometry"]]
    )
    tubes = gpd.GeoDataFrame(tubes, geometry="geometry", crs=SOURCE_CRS).to_crs(METRIC_CRS)

    series = pyogrio.read_dataframe(MONITOR_GPKG, layer="gm_gld", fid_as_index=True)
    series["number_of_observations"] = pd.to_numeric(series["number_of_observations"], errors="coerce")
    series["research_first_date"] = pd.to_datetime(series["research_first_date"], errors="coerce")
    series["research_last_date"] = pd.to_datetime(series["research_last_date"], errors="coerce")

    series_agg = series.groupby("gm_gmw_monitoringtube_fk", as_index=False).agg(
        n_gld_series=("gm_gmw_monitoringtube_fk", "size"),
        max_observations_meta=("number_of_observations", "max"),
        sum_observations_meta=("number_of_observations", "sum"),
        first_date_meta=("research_first_date", "min"),
        last_date_meta=("research_last_date", "max"),
    )

    tubes = (
        tubes.merge(
            series_agg,
            left_on="site_id",
            right_on="gm_gmw_monitoringtube_fk",
            how="inner",
        )
        .drop(columns=["gm_gmw_monitoringtube_fk"])
        .reset_index(drop=True)
    )
    tubes["lon"] = tubes.to_crs("EPSG:4326").geometry.x
    tubes["lat"] = tubes.to_crs("EPSG:4326").geometry.y
    return tubes


def load_groundwater_use_sources(
    bbox_tuple: tuple[float, float, float, float],
) -> tuple[gpd.GeoDataFrame, dict[str, int]]:
    bbox_geom = box(*bbox_tuple)

    facility = pyogrio.read_dataframe(USE_GPKG, layer="groundwater_usage_facility", bbox=bbox_tuple)
    facility = gpd.GeoDataFrame(facility[["bro_id", "geometry"]], geometry="geometry", crs=SOURCE_CRS)
    facility = facility.explode(index_parts=False).reset_index(drop=True).to_crs(METRIC_CRS)
    facility["use_obj_type"] = "facility_point"
    facility["use_obj_id"] = facility["bro_id"].astype(str)
    facility["facility_bro_id"] = facility["bro_id"].astype(str)

    conn = sqlite3.connect(USE_GPKG)
    try:
        loc = pd.read_sql_query(
            "SELECT bro_location_pk, design_well_fk, realised_well_fk FROM bro_location",
            conn,
        )
        pt = pd.read_sql_query(
            "SELECT bro_location_fk, x_or_lon, y_or_lat FROM bro_point",
            conn,
        )
        pt["x"] = pd.to_numeric(pt["x_or_lon"], errors="coerce")
        pt["y"] = pd.to_numeric(pt["y_or_lat"], errors="coerce")
        points = gpd.GeoDataFrame(
            pt[["bro_location_fk", "x", "y"]],
            geometry=gpd.points_from_xy(pt["x"], pt["y"]),
            crs=METRIC_CRS,
        )

        realised_well = pd.read_sql_query(
            "SELECT realised_well_pk, realised_well_id FROM realised_well",
            conn,
        )
        design_well = pd.read_sql_query(
            "SELECT design_well_pk, design_well_id FROM design_well",
            conn,
        )

        realised = (
            loc.dropna(subset=["realised_well_fk"])
            .merge(points, left_on="bro_location_pk", right_on="bro_location_fk", how="inner")
            .merge(realised_well, left_on="realised_well_fk", right_on="realised_well_pk", how="left")
        )
        realised = gpd.GeoDataFrame(
            realised[["realised_well_id", "geometry"]],
            geometry="geometry",
            crs=METRIC_CRS,
        ).to_crs("EPSG:4326")
        realised = realised[realised.within(bbox_geom)].to_crs(METRIC_CRS).reset_index(drop=True)
        realised["use_obj_type"] = "realised_well"
        realised["use_obj_id"] = realised["realised_well_id"].astype(str)
        realised["facility_bro_id"] = pd.NA

        design = (
            loc.dropna(subset=["design_well_fk"])
            .merge(points, left_on="bro_location_pk", right_on="bro_location_fk", how="inner")
            .merge(design_well, left_on="design_well_fk", right_on="design_well_pk", how="left")
        )
        design = gpd.GeoDataFrame(
            design[["design_well_id", "geometry"]],
            geometry="geometry",
            crs=METRIC_CRS,
        ).to_crs("EPSG:4326")
        design = design[design.within(bbox_geom)].to_crs(METRIC_CRS).reset_index(drop=True)
        design["use_obj_type"] = "design_well"
        design["use_obj_id"] = design["design_well_id"].astype(str)
        design["facility_bro_id"] = pd.NA
    finally:
        conn.close()

    sources = pd.concat(
        [
            facility[["use_obj_type", "use_obj_id", "facility_bro_id", "geometry"]],
            realised[["use_obj_type", "use_obj_id", "facility_bro_id", "geometry"]],
            design[["use_obj_type", "use_obj_id", "facility_bro_id", "geometry"]],
        ],
        ignore_index=True,
    )
    sources = gpd.GeoDataFrame(sources, geometry="geometry", crs=METRIC_CRS)

    counts = {
        "facility_points_bbox": int(len(facility)),
        "facility_objects_bbox": int(facility["bro_id"].nunique()),
        "realised_well_points_bbox": int(len(realised)),
        "realised_wells_bbox": int(realised["realised_well_id"].nunique()),
        "design_well_points_bbox": int(len(design)),
        "design_wells_bbox": int(design["design_well_id"].nunique()),
    }
    return sources, counts


def build_universe(
    tubes: gpd.GeoDataFrame,
    sources: gpd.GeoDataFrame,
    distance_meters: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    nearest = gpd.sjoin_nearest(
        tubes,
        sources,
        how="left",
        distance_col="distance_to_use_m",
    )
    nearest = (
        nearest.sort_values(["site_id", "distance_to_use_m", "use_obj_type", "use_obj_id"])
        .drop_duplicates("site_id")
        .reset_index(drop=True)
    )

    selected = nearest[
        (nearest["distance_to_use_m"] <= distance_meters)
        & (nearest["first_date_meta"] <= MIN_FIRST_DATE)
        & (nearest["last_date_meta"] >= MIN_LAST_DATE)
    ].copy()

    selected["tube_rank_within_well_meta"] = (
        selected.sort_values(
            ["well_id", "distance_to_use_m", "sum_observations_meta", "tube_number", "site_id"],
            ascending=[True, True, False, True, True],
        )
        .groupby("well_id")
        .cumcount()
        + 1
    )
    return nearest, selected


def build_gld_download_table(selected_tubes: pd.DataFrame) -> pd.DataFrame:
    gld = pyogrio.read_dataframe(MONITOR_GPKG, layer="gm_gld", fid_as_index=True)
    gld = gld.rename(columns={"bro_id": "gld_bro_id"})
    gld["research_first_date"] = pd.to_datetime(gld["research_first_date"], errors="coerce")
    gld["research_last_date"] = pd.to_datetime(gld["research_last_date"], errors="coerce")
    gld["number_of_observations"] = pd.to_numeric(gld["number_of_observations"], errors="coerce")

    out = selected_tubes[
        [
            "site_id",
            "well_id",
            "gmw_bro_id",
            "tube_number",
            "distance_to_use_m",
            "use_obj_type",
            "use_obj_id",
            "tube_rank_within_well_meta",
        ]
    ].merge(
        gld[
            [
                "gm_gmw_monitoringtube_fk",
                "gld_bro_id",
                "number_of_observations",
                "research_first_date",
                "research_last_date",
                "series_unknown_csv_url",
                "series_preliminary_csv_url",
                "series_fully_assessed_csv_url",
            ]
        ],
        left_on="site_id",
        right_on="gm_gmw_monitoringtube_fk",
        how="left",
    )
    out = out.drop(columns=["gm_gmw_monitoringtube_fk"]).rename(
        columns={
            "number_of_observations": "gld_observations_meta",
            "research_first_date": "gld_first_date_meta",
            "research_last_date": "gld_last_date_meta",
        }
    )
    out["bro_csv_url"] = out["gld_bro_id"].map(lambda x: BRO_GLD_CSV_URL.format(gld_id=x))
    out = out.sort_values(["site_id", "gld_bro_id"]).reset_index(drop=True)
    return out


def iter_measurements_from_bro_csv(raw_text: str) -> Iterable[tuple[str, float]]:
    reader = csv.reader(raw_text.splitlines())
    for row in reader:
        if len(row) < 2:
            continue
        ts = row[0].strip().strip('"')
        val = row[1].strip().strip('"')
        if not ts or not val:
            continue
        if ts.startswith("tijdstip meting") or ts.startswith("observatie ID") or ts.startswith("BRO-ID"):
            continue
        try:
            water_level = float(val)
        except ValueError:
            continue
        if ts[:4].isdigit():
            yield ts, water_level


def fetch_bro_csv(gld_id: str, retries: int = 6, sleep_seconds: float = 0.20) -> str:
    url = BRO_GLD_CSV_URL.format(gld_id=gld_id)
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urlopen(req, timeout=90) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            wait = sleep_seconds * (2 ** attempt)
            time.sleep(wait)
    raise RuntimeError(f"Failed to download {gld_id}: {last_error}")


def refresh_cache(download_glds: pd.DataFrame, replace_cache: bool, sleep_seconds: float) -> pd.DataFrame:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if replace_cache:
        for fp in CACHE_DIR.glob("*.csv"):
            fp.unlink()

    rows = []
    total = len(download_glds)
    for idx, rec in enumerate(download_glds.itertuples(index=False), start=1):
        site_id = int(rec.site_id)
        gld_id = str(rec.gld_bro_id)
        cache_path = CACHE_DIR / f"{site_id}_{gld_id}.csv"
        status = "downloaded"
        actual_rows = 0
        actual_first_date = pd.NaT
        actual_last_date = pd.NaT
        cache_rel = pd.NA
        try:
            raw_text = fetch_bro_csv(gld_id=gld_id, sleep_seconds=sleep_seconds)
            measurements = list(iter_measurements_from_bro_csv(raw_text))
            if measurements:
                with cache_path.open("w", newline="", encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    writer.writerow(["date", "water_level_nap_m"])
                    writer.writerows(measurements)
                dates = pd.to_datetime([m[0] for m in measurements], errors="coerce", utc=True).tz_convert(None)
                actual_rows = int(len(measurements))
                actual_first_date = dates.min()
                actual_last_date = dates.max()
                cache_rel = str(cache_path.relative_to(ROOT))
            else:
                status = "empty"
        except Exception as exc:
            status = f"error: {exc}"

        rows.append(
            {
                "site_id": site_id,
                "gld_bro_id": gld_id,
                "cache_path": cache_rel,
                "download_status": status,
                "actual_observation_rows": actual_rows,
                "actual_first_date": actual_first_date,
                "actual_last_date": actual_last_date,
            }
        )
        if idx % 25 == 0 or idx == total:
            print(f"Downloaded {idx}/{total} GLD files")
        time.sleep(sleep_seconds)

    return pd.DataFrame(rows)


def summarize_actual_downloads(
    download_glds: pd.DataFrame,
    actual_glds: pd.DataFrame,
    selected_tubes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if actual_glds.empty:
        tube_actual = selected_tubes.copy()
        tube_actual["actual_observation_rows"] = pd.NA
        tube_actual["actual_first_date"] = pd.NaT
        tube_actual["actual_last_date"] = pd.NaT
        tube_actual["downloaded_gld_count"] = 0
    else:
        gld_actual = download_glds.merge(actual_glds, on=["site_id", "gld_bro_id"], how="left")
        tube_actual = gld_actual.groupby("site_id", as_index=False).agg(
            downloaded_gld_count=("download_status", lambda s: int((pd.Series(s).fillna("") == "downloaded").sum())),
            actual_observation_rows=("actual_observation_rows", "sum"),
            actual_first_date=("actual_first_date", "min"),
            actual_last_date=("actual_last_date", "max"),
        )
        tube_actual = selected_tubes.merge(tube_actual, on="site_id", how="left")

    target_wells = (
        tube_actual.sort_values(
            [
                "well_id",
                "distance_to_use_m",
                "actual_observation_rows",
                "sum_observations_meta",
                "tube_number",
                "site_id",
            ],
            ascending=[True, True, False, False, True, True],
            na_position="last",
        )
        .drop_duplicates("well_id", keep="first")
        .reset_index(drop=True)
    )
    target_wells["tube_rank_within_well_actual"] = 1
    return tube_actual, target_wells


def write_outputs(
    all_tubes: pd.DataFrame,
    selected_tubes: pd.DataFrame,
    download_glds: pd.DataFrame,
    tube_actual: pd.DataFrame,
    target_wells: pd.DataFrame,
    summary: dict,
) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    all_tubes.drop(columns=["geometry"], errors="ignore").to_csv(
        PROCESSED_DIR / "amsterdam_monitoring_tubes_with_use_context.csv",
        index=False,
    )
    selected_tubes.drop(columns=["geometry"], errors="ignore").to_csv(
        PROCESSED_DIR / "download_universe_tubes.csv",
        index=False,
    )
    download_glds.to_csv(PROCESSED_DIR / "download_universe_glds.csv", index=False)
    tube_actual.drop(columns=["geometry"], errors="ignore").to_csv(
        PROCESSED_DIR / "download_universe_tubes_with_actual_counts.csv",
        index=False,
    )
    target_wells.drop(columns=["geometry"], errors="ignore").to_csv(
        PROCESSED_DIR / "selected_target_wells.csv",
        index=False,
    )
    with (PROCESSED_DIR / "selection_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)

    summary_md = [
        "# Target Download Universe",
        "",
        "I define the target download universe from monitoring tubes that:",
        f"- fall inside the Amsterdam study bbox `{summary['region_bbox']}`;",
        "- have at least one BRO GLD series in `brogmkenset.gpkg`;",
        (
            "- lie within "
            f"{summary['target_distance_meters']:.0f} m of an exploded groundwater-use facility point, "
            "design well, or realised well from `bro_groundwater_use.gpkg`;"
        ),
        "- and span the thesis overlap window (`first_date <= 2010-01-01`, `last_date >= 2020-01-01`).",
        "",
        f"Result: `{summary['selected_tubes']} tubes / {summary['selected_wells']} wells / {summary['selected_glds']} GLD files`.",
    ]
    (PROCESSED_DIR / "selection_summary.md").write_text("\n".join(summary_md) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    bbox_tuple = tuple(args.region_bbox)

    tubes = load_monitoring_tubes_with_series(bbox_tuple)
    sources, source_counts = load_groundwater_use_sources(bbox_tuple)
    all_tubes, selected_tubes = build_universe(
        tubes=tubes,
        sources=sources,
        distance_meters=args.distance_meters,
    )
    download_glds = build_gld_download_table(selected_tubes)

    actual_glds = pd.DataFrame(columns=["site_id", "gld_bro_id", "actual_observation_rows", "actual_first_date", "actual_last_date"])
    if args.download_cache:
        actual_glds = refresh_cache(
            download_glds=download_glds,
            replace_cache=args.replace_cache,
            sleep_seconds=args.sleep_seconds,
        )

    tube_actual, target_wells = summarize_actual_downloads(
        download_glds=download_glds,
        actual_glds=actual_glds,
        selected_tubes=selected_tubes,
    )

    summary = {
        "region_bbox": list(bbox_tuple),
        "target_distance_meters": float(args.distance_meters),
        "min_first_date": str(MIN_FIRST_DATE.date()),
        "min_last_date": str(MIN_LAST_DATE.date()),
        "bbox_tubes_with_series": int(len(tubes)),
        "bbox_wells_with_series": int(tubes["well_id"].nunique()),
        "all_tubes_with_use_context": int(len(all_tubes)),
        "selected_tubes": int(len(selected_tubes)),
        "selected_wells": int(selected_tubes["well_id"].nunique()),
        "selected_glds": int(len(download_glds)),
        "downloaded_cache_files": int((actual_glds.get("download_status", pd.Series(dtype=str)) == "downloaded").sum()),
        "empty_cache_files": int((actual_glds.get("download_status", pd.Series(dtype=str)) == "empty").sum()),
        "error_cache_files": int(
            actual_glds.get("download_status", pd.Series(dtype=str)).fillna("").astype(str).str.startswith("error").sum()
        ),
    }
    summary.update(source_counts)

    write_outputs(
        all_tubes=all_tubes,
        selected_tubes=selected_tubes,
        download_glds=download_glds,
        tube_actual=tube_actual,
        target_wells=target_wells,
        summary=summary,
    )

    print("Target download universe built:")
    print(f"- Bbox tubes with series: {summary['bbox_tubes_with_series']} / {summary['bbox_wells_with_series']} wells")
    print(f"- Selected tubes: {summary['selected_tubes']} / {summary['selected_wells']} wells")
    print(f"- Selected GLD files: {summary['selected_glds']}")
    if args.download_cache:
        print(f"- Downloaded cache files: {summary['downloaded_cache_files']}")


if __name__ == "__main__":
    main()
