# Groundwater Thesis — Netherlands Selective Transfer Learning

This repository contains the code, notebooks, and saved outputs for my master's
thesis on groundwater (water-table-depth anomaly) forecasting.

The **final, default analysis runs on the Netherlands target panel** (≈496 BRO
monitoring wells). The earlier Amsterdam case is retained only as
**legacy / preliminary reference material** (see
[Amsterdam (legacy)](#amsterdam-legacy)) and is *not* the default pipeline.

The research question is whether forecasting should use **no transfer**,
**fixed (always) transfer**, or **selective transfer** under one shared data and
split design. The thesis proposes a Context-Aware Selective Learning (CASL) gate
that decides, per well, how much transfer to apply.

---

## Quick start

```bash
# 1. Create the environment (reference list; not a locked spec)
pip install -r requirements.txt

# 2. Check which input data is present before running anything
python Code/repro_utils.py
```

`python Code/repro_utils.py` prints, for every required input, whether it is
present and — if missing — the exact project-relative path where it should go and
why it is not stored in GitHub. **Run it first.**

---

## Data availability and reproducibility

This repository contains the **code, notebooks, and the saved processed outputs**
(EDA / methodology / results tables and figures). Some **raw input datasets are
not stored in GitHub** because they are too large or are externally sourced under
their own licences.

All paths below are **relative to the repository root**. Nothing in the code uses
absolute machine-specific paths; the project root is auto-detected.

### Required external datasets (not in GitHub — provide separately)

| Dataset | Expected local path | Notes |
|---|---|---|
| BRO monitoring network GeoPackage | `Data/Datasets/brogmkenset.gpkg` | BRO bulk download, ~180 MB |
| BRO groundwater-use / pumping GeoPackage | `Data/Datasets/bro_groundwater_use.gpkg` | BRO bulk download, ~48 MB |
| **TSMP** groundwater-table-depth anomaly | `Data/Datasets/TSMP_G2A_monthly_groundwater_table_depth_anomaly_FZJ-IBG3_TSMP_0.1_degree_v1.1996_2016.nc` | FZJ-IBG3 TSMP-G2A NetCDF |
| **COSMO** precipitation anomaly | `Data/Datasets/COSMO_REA6_monthly_precipitation_anomaly_FZJ-IBG3_COSMO_0.1_degree_v1.1995_082019.nc` | FZJ-IBG3 COSMO-REA6 NetCDF |
| **GLEAM** soil-moisture anomaly | `Data/Datasets/GLEAM_monthly_soil_moisture_anomaly_FZJ-IBG3_GLEAM_0.1_degree_v1.1980_2020.nc` | FZJ-IBG3 GLEAM NetCDF |

These TSMP / COSMO / GLEAM rasters and the two BRO GeoPackages must be placed at
the paths above before the **full** EDA can be re-run from raw data. They are the
files most likely to be reported as missing on a fresh clone.

### Datasets that ship with the repository

- `Data/Netherlands_gw_data/` — per-well BRO groundwater record CSVs (the
  Netherlands target panel).
- `Data/Datasets/era5_land_monthly.nc` — small ERA5-Land reference grid.
- `Data/processed/model_inputs/*.parquet` — the **small processed model-input
  tables** built by the EDA notebook. These let you run the methodology and
  results stages **without** downloading the heavy raw rasters.
- `Data/processed/.../tables/` and `.../figures/` — the saved EDA, methodology,
  and results outputs reported in the thesis.

### What can be reproduced, and from what

| Stage | Notebook / script | Needs | Status without raw data |
|---|---|---|---|
| EDA (build model inputs) | `Code/EDA.ipynb` | BRO GeoPackages + TSMP/COSMO/GLEAM | Falls back to the committed processed parquet if rasters are missing; full raster-based rebuild needs the external files |
| Methodology (models, transfer, selector) | `Code/Methodology.ipynb` | `Data/processed/model_inputs/*.parquet` | **Runs** from the committed processed inputs |
| Results (final figures/tables) | `Code/Results.ipynb` | committed methodology tables | **Runs** from committed outputs |
| Selector ablation (robustness) | `Code/selector_robustness/run_selector_ablation_production.py` | `Code/Methodology.ipynb` definitions + model inputs | Runs if model inputs present |

Because the processed `model_inputs/*.parquet` are committed, an examiner can
clone the repo, run `Code/Methodology.ipynb` then `Code/Results.ipynb`, and
reproduce the **final thesis tables and figures without any external download**.
The external TSMP/COSMO/GLEAM/BRO files are only required to rebuild those
processed inputs from scratch in `Code/EDA.ipynb`.

> No private Google Drive / OneDrive links are included here. If raw data needs
> to be shared, that will be arranged separately.

---

## Repository structure

`Code/`

- `EDA.ipynb` — exploratory data analysis: defines the **Netherlands** target
  well universe, builds the processed model-input tables, and exports the EDA
  tables and figures.
- `Methodology.ipynb` — the fixed modelling pipeline, the no-/fixed-/selective-
  transfer comparisons, the CASL selector, and the robustness checks
  (Netherlands target panel).
- `Results.ipynb` — assembles the final thesis figures and short result text.
- `repro_utils.py` — data-availability check and shared missing-data helper.
- `selector_robustness/run_selector_ablation_production.py` — production-
  consistent selector-input ablation.

`Data/`

- `Datasets/` — external climate/geospatial inputs (mostly not in GitHub; see
  the table above).
- `Netherlands_gw_data/` — local groundwater well CSVs for the Netherlands target
  set.
- `processed/` — processed outputs organised by analysis stage.

### Processed data structure

- `Data/processed/eda/` — `tables/` (overview, correlations, similarity) and
  `figures/`, plus `target_universe/` documenting the Netherlands target-well
  selection.
- `Data/processed/model_inputs/` — shared modelling inputs (parquet) created in
  EDA and consumed by the methodology notebook.
- `Data/processed/methodology/` — `tables/` (protocol, core_results, selector,
  transfer, robustness, source_filter_selection, error_analysis) and `figures/`.
- `Data/processed/results/` — final `tables/` and `figures/` for the thesis.
- `Data/processed/amsterdam_reference/` — **legacy** Amsterdam comparison
  artefacts (kept for the scope-transition discussion only).

---

## Workflow (Netherlands, default)

1. `python Code/repro_utils.py` — confirm input availability.
2. `Code/EDA.ipynb` — builds the Netherlands target universe and the processed
   model inputs. (Needs the external rasters/GeoPackages for a full rebuild; if
   they are absent it falls back to the committed processed parquet.)
3. `Code/Methodology.ipynb` — runs the modelling, transfer comparisons, selector,
   and robustness analyses on the Netherlands panel.
4. `Code/Results.ipynb` — produces the final thesis figures and tables.

Optional: `python Code/selector_robustness/run_selector_ablation_production.py`
for the production-consistent selector-input ablation.

---

## Amsterdam (legacy)

The thesis began as an Amsterdam-only study. That earlier scope survives only as:

- `Data/processed/amsterdam_reference/` — saved Amsterdam comparison outputs.

The active code defaults to the Netherlands region
(`REGION_NAME = 'netherlands'` in `Code/EDA.ipynb`) and does **not** apply the
old Amsterdam-specific pumping-proximity filter. Treat any Amsterdam-specific
numbers as preliminary/reference, not as the final result.
