"""Reproducibility helpers for the Netherlands groundwater thesis pipeline.

This module is the single place that knows which input files the pipeline needs,
where they must live (as project-relative paths), and whether they ship with the
GitHub repository or have to be provided separately because of size limits.

Two uses:

1. As a command-line data-availability check (run this FIRST after cloning)::

       python Code/repro_utils.py

   It prints, for every required input, whether it is present locally and -- if
   it is missing -- the exact relative path where it should be placed and why it
   is not in GitHub.

2. As a helper imported by the notebooks/scripts to fail with a clear, actionable
   message instead of a bare ``FileNotFoundError``::

       from repro_utils import require_inputs
       require_inputs(["monitor_gpkg", "tsmp_nc", "cosmo_nc", "gleam_nc"])

The default analysis target is the **Netherlands** panel. The old Amsterdam case
is retained only as legacy/reference outputs and is not part of this check.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


def find_project_root(start: Path | None = None) -> Path:
    """Return the repository root regardless of whether code runs from the repo
    root, ``Code/`` or ``Data/``."""
    here = (start or Path(__file__).resolve()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "Data" / "processed").exists() or (candidate / "Code").exists():
            # The repo root is the directory that contains both Code/ and Data/.
            if (candidate / "Code").exists() and (candidate / "Data").exists():
                return candidate
    # Default: two levels up from this file (Code/repro_utils.py -> repo root).
    return Path(__file__).resolve().parents[1]


ROOT = find_project_root()


@dataclass(frozen=True)
class InputSpec:
    key: str
    relpath: str            # path relative to the repository root
    label: str              # human-readable name
    on_github: bool         # True if the file ships with the repo
    note: str               # where it comes from / why it may be missing

    @property
    def path(self) -> Path:
        return ROOT / self.relpath


# ---------------------------------------------------------------------------
# Registry of required inputs for the Netherlands pipeline.
# ---------------------------------------------------------------------------
# The raw external datasets (TSMP/COSMO/GLEAM NetCDF rasters and the BRO
# GeoPackages) are NOT stored in GitHub (size / external licensing). The per-well
# groundwater CSVs and the small processed model-input parquet files are intended
# to ship with the repo so that the final Netherlands modelling results can be
# reproduced without the raw external datasets.
REQUIRED_INPUTS: list[InputSpec] = [
    # --- BRO geospatial (large, NOT in GitHub) ---
    InputSpec(
        "monitor_gpkg",
        "Data/Datasets/brogmkenset.gpkg",
        "BRO monitoring network GeoPackage (monitoring tubes + GLD series)",
        on_github=False,
        note="BRO bulk download (~180 MB). Too large for GitHub.",
    ),
    InputSpec(
        "use_gpkg",
        "Data/Datasets/bro_groundwater_use.gpkg",
        "BRO groundwater-use / pumping GeoPackage",
        on_github=False,
        note="BRO bulk download (~48 MB). Too large for GitHub.",
    ),
    # --- FZJ-IBG3 monthly anomaly rasters (large, NOT in GitHub) ---
    InputSpec(
        "tsmp_nc",
        "Data/Datasets/TSMP_G2A_monthly_groundwater_table_depth_anomaly_FZJ-IBG3_TSMP_0.1_degree_v1.1996_2016.nc",
        "TSMP groundwater-table-depth anomaly (source/pretraining signal)",
        on_github=False,
        note="FZJ-IBG3 TSMP-G2A product. External NetCDF, provided separately.",
    ),
    InputSpec(
        "cosmo_nc",
        "Data/Datasets/COSMO_REA6_monthly_precipitation_anomaly_FZJ-IBG3_COSMO_0.1_degree_v1.1995_082019.nc",
        "COSMO-REA6 precipitation anomaly",
        on_github=False,
        note="FZJ-IBG3 COSMO-REA6 product. External NetCDF, provided separately.",
    ),
    InputSpec(
        "gleam_nc",
        "Data/Datasets/GLEAM_monthly_soil_moisture_anomaly_FZJ-IBG3_GLEAM_0.1_degree_v1.1980_2020.nc",
        "GLEAM soil-moisture anomaly",
        on_github=False,
        note="FZJ-IBG3 GLEAM product. External NetCDF, provided separately.",
    ),
    # --- Small inputs that DO ship with the repo ---
    InputSpec(
        "era5_nc",
        "Data/Datasets/era5_land_monthly.nc",
        "ERA5-Land monthly reference grid",
        on_github=True,
        note="Small (~1 MB). Committed to the repo.",
    ),
    InputSpec(
        "nl_gw_dir",
        "Data/Netherlands_gw_data",
        "Netherlands per-well BRO groundwater records (target panel CSVs)",
        on_github=True,
        note="~1100 CSV files. Committed to the repo.",
    ),
    # --- Processed model inputs (small parquet; recommended to commit) ---
    InputSpec(
        "pretrain_supervised",
        "Data/processed/model_inputs/pretrain_supervised_table.parquet",
        "Processed source/pretraining table (built by EDA from the raw external datasets)",
        on_github=True,
        note="~9 MB. Lets Methodology/Results run WITHOUT the raw external datasets.",
    ),
    InputSpec(
        "finetune_supervised",
        "Data/processed/model_inputs/finetune_supervised_table.parquet",
        "Processed Netherlands target table (built by EDA)",
        on_github=True,
        note="~3 MB. Lets Methodology/Results run WITHOUT the raw external datasets.",
    ),
    InputSpec(
        "monthly_local",
        "Data/processed/model_inputs/monthly_local_wtda.parquet",
        "Processed monthly local water-table-depth-anomaly table",
        on_github=True,
        note="~2 MB. Built by EDA.",
    ),
    InputSpec(
        "baseline_monthly",
        "Data/processed/model_inputs/baseline_monthly_table.parquet",
        "Processed baseline monthly table",
        on_github=True,
        note="Small. Built by EDA.",
    ),
]

REQUIRED_BY_KEY = {spec.key: spec for spec in REQUIRED_INPUTS}

# Convenience groups for callers.
RAW_EDA_INPUTS = ["monitor_gpkg", "use_gpkg", "tsmp_nc", "cosmo_nc", "gleam_nc"]
PROCESSED_MODEL_INPUTS = [
    "pretrain_supervised",
    "finetune_supervised",
    "monthly_local",
    "baseline_monthly",
]


class MissingInputError(FileNotFoundError):
    """Raised when one or more required inputs are absent. The message lists
    each missing file, its expected project-relative path, and why it may not be
    present so an examiner knows exactly what to provide."""


def _format_missing(specs: Iterable[InputSpec]) -> str:
    lines = [
        "",
        "Missing required input file(s) for the Netherlands pipeline:",
        "",
    ]
    for spec in specs:
        lines.append(f"  - {spec.label}")
        lines.append(f"      expected at: {spec.relpath}")
        lines.append(f"      reason     : {spec.note}")
    lines += [
        "",
        "These files are not included in GitHub because they are too large or",
        "externally sourced. Place them at the paths above (relative to the repo",
        "root), then re-run. To see the full availability report, run:",
        "",
        "    python Code/repro_utils.py",
        "",
    ]
    return "\n".join(lines)


def require_inputs(keys: Iterable[str]) -> dict[str, Path]:
    """Verify that the given registry keys are present. Returns a {key: Path} map
    on success; raises :class:`MissingInputError` with an actionable message
    otherwise."""
    missing: list[InputSpec] = []
    resolved: dict[str, Path] = {}
    for key in keys:
        spec = REQUIRED_BY_KEY.get(key)
        if spec is None:
            raise KeyError(f"Unknown input key: {key!r}. Known keys: {sorted(REQUIRED_BY_KEY)}")
        if spec.path.exists():
            resolved[key] = spec.path
        else:
            missing.append(spec)
    if missing:
        raise MissingInputError(_format_missing(missing))
    return resolved


def availability_report(keys: Iterable[str] | None = None) -> list[tuple[InputSpec, bool]]:
    specs = (
        [REQUIRED_BY_KEY[k] for k in keys] if keys is not None else list(REQUIRED_INPUTS)
    )
    return [(spec, spec.path.exists()) for spec in specs]


def main() -> int:
    print(f"Repository root: {ROOT}")
    print(f"Default analysis target: Netherlands panel\n")
    report = availability_report()
    width = max(len(spec.relpath) for spec, _ in report)
    present = 0
    for spec, ok in report:
        status = "OK     " if ok else "MISSING"
        if ok:
            present += 1
        tag = "github" if spec.on_github else "external"
        print(f"[{status}] ({tag:8s}) {spec.relpath:<{width}}  - {spec.label}")
    print(f"\n{present}/{len(report)} required inputs present.")

    missing_external = [s for s, ok in report if not ok and not s.on_github]
    missing_github = [s for s, ok in report if not ok and s.on_github]
    if missing_external:
        print("\nExternal files to provide separately (not in GitHub):")
        for spec in missing_external:
            print(f"  - {spec.relpath}\n      {spec.note}")
    if missing_github:
        print("\nFiles that should ship with the repo but are missing locally:")
        for spec in missing_github:
            print(f"  - {spec.relpath}")
    if not missing_external and not missing_github:
        print("\nAll required inputs are available. The full pipeline can run.")
    elif not missing_github and all(
        REQUIRED_BY_KEY[k].path.exists() for k in PROCESSED_MODEL_INPUTS
    ):
        print(
            "\nThe raw external datasets are not present, but the processed "
            "model-input files are:\n  -> the final Netherlands modelling pipeline "
            "(Methodology.ipynb, Results.ipynb) can run and reproduce the final "
            "results. This is sufficient for the final results, but not for "
            "rebuilding the preprocessing/EDA from scratch (that needs the raw "
            "external datasets)."
        )
    return 0 if all(ok for _, ok in report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
