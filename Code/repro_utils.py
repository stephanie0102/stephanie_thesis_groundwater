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
    optional: bool = False  # True if only needed for the optional raw rebuild

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
#
# Auxiliary files NOT listed here because the final modelling pipeline does not
# use them: Data/Datasets/era5_land_monthly.nc (ERA5-Land) and any CLC / Corine
# Land Cover GeoPackage.
REQUIRED_INPUTS: list[InputSpec] = [
    # --- BRO geospatial (large, NOT in GitHub) ---
    InputSpec(
        "monitor_gpkg",
        "Data/Datasets/brogmkenset.gpkg",
        "BRO monitoring network GeoPackage (monitoring tubes + GLD series)",
        on_github=False,
        note="BRO bulk download (~180 MB). Too large for GitHub.",
        optional=True,
    ),
    InputSpec(
        "use_gpkg",
        "Data/Datasets/bro_groundwater_use.gpkg",
        "BRO groundwater-use / pumping GeoPackage",
        on_github=False,
        note="BRO bulk download (~48 MB). Too large for GitHub.",
        optional=True,
    ),
    # --- FZJ-IBG3 monthly anomaly rasters (large, NOT in GitHub) ---
    InputSpec(
        "tsmp_nc",
        "Data/Datasets/TSMP_G2A_monthly_groundwater_table_depth_anomaly_FZJ-IBG3_TSMP_0.1_degree_v1.1996_2016.nc",
        "TSMP groundwater-table-depth anomaly (source/pretraining signal)",
        on_github=False,
        note="FZJ-IBG3 TSMP-G2A product. External NetCDF, provided separately.",
        optional=True,
    ),
    InputSpec(
        "cosmo_nc",
        "Data/Datasets/COSMO_REA6_monthly_precipitation_anomaly_FZJ-IBG3_COSMO_0.1_degree_v1.1995_082019.nc",
        "COSMO-REA6 precipitation anomaly",
        on_github=False,
        note="FZJ-IBG3 COSMO-REA6 product. External NetCDF, provided separately.",
        optional=True,
    ),
    InputSpec(
        "gleam_nc",
        "Data/Datasets/GLEAM_monthly_soil_moisture_anomaly_FZJ-IBG3_GLEAM_0.1_degree_v1.1980_2020.nc",
        "GLEAM soil-moisture anomaly",
        on_github=False,
        note="FZJ-IBG3 GLEAM product. External NetCDF, provided separately.",
        optional=True,
    ),
    # --- Small inputs that DO ship with the repo ---
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


def check_final_dataset() -> bool:
    """Load the committed 496-well finetune table and verify its shape and key
    columns. Returns True if the canonical dataset looks correct."""
    spec = REQUIRED_BY_KEY["finetune_supervised"]
    if not spec.path.exists():
        print("\nFinal dataset check: SKIPPED (finetune_supervised_table.parquet missing).")
        return False
    try:
        import pandas as pd
        df = pd.read_parquet(spec.path)
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"\nFinal dataset check: could not load parquet ({exc}).")
        return False
    n_wells = df["site_id"].nunique()
    key_cols = ["wtda", "tsmp_wtda", "pr_a", "sm_a", "pumping_available",
                "pumping_m3_month_log1p"]
    checks = {
        "wells == 496": n_wells == 496,
        "shape == (100472, 30)": df.shape == (100472, 30),
        "key columns present": all(c in df.columns for c in key_cols),
    }
    print("\nFinal 496-well dataset check (Data/processed/model_inputs/finetune_supervised_table.parquet):")
    print(f"  wells: {n_wells} | shape: {df.shape}")
    for name, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    return all(checks.values())


def main() -> int:
    print(f"Repository root: {ROOT}")
    print(f"Default analysis target: Netherlands panel (committed 496-well dataset)\n")
    report = availability_report()
    width = max(len(spec.relpath) for spec, _ in report)
    required = [(s, ok) for s, ok in report if not s.optional]
    optional = [(s, ok) for s, ok in report if s.optional]

    print("REQUIRED for the final results (Level 1 - committed, no external data needed):")
    req_present = 0
    for spec, ok in required:
        if ok:
            req_present += 1
        print(f"  [{'OK     ' if ok else 'MISSING'}] {spec.relpath:<{width}}  - {spec.label}")
    print(f"  -> {req_present}/{len(required)} required inputs present.")

    print("\nOPTIONAL raw external datasets (Level 2 - only for the raw preprocessing rebuild in EDA):")
    for spec, ok in optional:
        print(f"  [{'present' if ok else 'absent '}] {spec.relpath:<{width}}  - {spec.label}")
    print("  -> These are NOT needed to reproduce the final results.")

    # Verify the canonical 496-well dataset actually loads with the right columns.
    final_ok = check_final_dataset()

    missing_required = [s for s, ok in required if not ok]
    if not missing_required and final_ok:
        print("\nAll required inputs are present and the 496-well dataset is valid.")
        print("-> Run Code/Methodology.ipynb then Code/Results.ipynb to reproduce the final results.")
        return 0
    if missing_required:
        print("\nMissing REQUIRED inputs for the final results:")
        for spec in missing_required:
            print(f"  - {spec.relpath}\n      {spec.note}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
