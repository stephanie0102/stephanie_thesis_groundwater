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

**What CASL does and does not claim.** CASL gives a small but supported RMSE
improvement over the baselines. Its main contribution is well-level
transfer-risk control: it reduces the risk of negative transfer by deciding, per
well, how much transfer to use. It is not a large accuracy breakthrough, and it
is not a full drought early-warning system.

## Dataset

The final thesis dataset contains **496 monitoring wells**. I use the processed
model-input files saved in `Data/processed/model_inputs/` for the final analysis.
These files contain the downloaded and prepared groundwater observations, TSMP-G2A
groundwater anomalies, COSMO-REA6 precipitation anomalies, GLEAM soil-moisture
anomalies, and BRO groundwater-use features.

The final analysis starts from these processed parquet files. The raw datasets
below are only the sources I used to build the processed dataset.

The five data sources are:

1. **BRO groundwater monitoring** (`brogmkenset.gpkg`) — local groundwater
   observations, the target wells, `water_level_nap_m`, and `wtda`.
2. **BRO groundwater-use** (`bro_groundwater_use.gpkg`) — pumping-proxy features
   `pumping_available`, `pumping_m3_month`, `pumping_m3_month_log1p`.
3. **TSMP-G2A groundwater anomaly** (`TSMP_G2A_..._TSMP_0.1_degree_v1.1996_2016.nc`)
   — variable `wtd_a`, renamed to `tsmp_wtda`.
4. **COSMO-REA6 precipitation anomaly** (`COSMO_REA6_..._COSMO_0.1_degree_v1.1995_082019.nc`)
   — variable `pr_a`.
5. **GLEAM soil-moisture anomaly** (`GLEAM_..._GLEAM_0.1_degree_v1.1980_2020.nc`)
   — variable `sm_a`.

`era5_land_monthly.nc` and the CLC (Corine Land Cover) GeoPackage are present
locally but are **auxiliary** — the final modelling pipeline does not use them.

---

## Setup

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

### Terminology (used consistently across this repo)

- **Raw external datasets** — the TSMP / COSMO / GLEAM NetCDF (`.nc`) files and
  the BRO GeoPackage (`.gpkg`) files. Large, externally sourced, **not in GitHub**.
- **Processed model-input files** — `Data/processed/model_inputs/*.parquet`. The
  small tables derived from the raw external datasets; they already contain all
  model features and **ship with the repo**.
- **Thesis code pipeline** — `Code/EDA.ipynb` → `Code/Methodology.ipynb` →
  `Code/Results.ipynb`, running on the committed processed model-input files. This
  is the full pipeline for the thesis results.
- **Canonical thesis dataset** — the committed 496-well processed model-input
  files in `Data/processed/model_inputs/`. This frozen dataset is the canonical
  input for all final thesis results.
- **Optional raw preprocessing rebuild** — the guarded rebuild path inside
  `Code/EDA.ipynb`. It shows how the raw datasets were prepared and needs the raw
  external datasets listed below. It is off by default (`RUN_RAW_REBUILD = False`).

### The thesis code pipeline

The thesis code runs as one pipeline:

`Code/EDA.ipynb` → `Code/Methodology.ipynb` → `Code/Results.ipynb`

1. **`Code/EDA.ipynb` — prepares and checks the final thesis dataset.** By default
   it loads the saved 496-well processed dataset from
   `Data/processed/model_inputs/`, so it needs no external data. The optional raw
   preprocessing rebuild (off by default, `RUN_RAW_REBUILD = False`) shows how the
   dataset was built and requires the raw external datasets listed below.
2. **`Code/Methodology.ipynb` — builds the models.** This is the model-building
   notebook and is part of the full thesis pipeline. It runs on the committed
   processed model-input files (no external data needed). **It retrains models and
   can overwrite the committed result files, so run it intentionally and keep
   backups if you want to preserve the committed result files.**
3. **`Code/Results.ipynb` — generates the final reported tables and figures.**

First run `python Code/repro_utils.py` to confirm the committed processed
model-input files are present and the 496-well dataset is valid. Because the
processed model-input files and the result tables are committed, every step
except the optional raw rebuild runs without any external download.

### Required external datasets (not in GitHub — provide separately)

| Dataset | Expected local path | Notes |
|---|---|---|
| BRO monitoring network GeoPackage | `Data/Datasets/brogmkenset.gpkg` | BRO bulk download, ~180 MB |
| BRO groundwater-use / pumping GeoPackage | `Data/Datasets/bro_groundwater_use.gpkg` | BRO bulk download, ~48 MB |
| **TSMP** groundwater-table-depth anomaly | `Data/Datasets/TSMP_G2A_monthly_groundwater_table_depth_anomaly_FZJ-IBG3_TSMP_0.1_degree_v1.1996_2016.nc` | FZJ-IBG3 TSMP-G2A NetCDF |
| **COSMO** precipitation anomaly | `Data/Datasets/COSMO_REA6_monthly_precipitation_anomaly_FZJ-IBG3_COSMO_0.1_degree_v1.1995_082019.nc` | FZJ-IBG3 COSMO-REA6 NetCDF |
| **GLEAM** soil-moisture anomaly | `Data/Datasets/GLEAM_monthly_soil_moisture_anomaly_FZJ-IBG3_GLEAM_0.1_degree_v1.1980_2020.nc` | FZJ-IBG3 GLEAM NetCDF |

These raw external datasets (TSMP / COSMO / GLEAM `.nc` and the two BRO `.gpkg`)
are required **only for the optional raw preprocessing rebuild** in `Code/EDA.ipynb`.
The rest of the pipeline runs on the committed processed model-input files, so
these raw files are the ones most likely to be reported as missing on a fresh
clone — that is expected.

### Datasets that ship with the repository

- `Data/Netherlands_gw_data/` — per-well BRO groundwater record CSVs (the
  Netherlands target panel).
- `Data/Datasets/era5_land_monthly.nc` — small ERA5-Land reference grid
  (**auxiliary**, not used by the final modelling pipeline).
- `Data/processed/model_inputs/*.parquet` — the **small processed model-input
  files** built by the EDA notebook (the frozen **496-well canonical thesis
  dataset**). These let you run the thesis code pipeline
  **without** the raw external datasets.
- `Data/processed/.../tables/` and `.../figures/` — the saved EDA, methodology,
  and results outputs reported in the thesis.

### What each step does, and what it needs

| Step | Notebook / script | Needs | Notes |
|---|---|---|---|
| Input check (run first) | `python Code/repro_utils.py` | committed processed model-input files | Confirms the committed 496-well inputs are present and valid |
| 1. Prepare/check dataset | `Code/EDA.ipynb` | committed processed model-input files | By default loads and checks the committed 496-well dataset; needs no external data. Optional raw rebuild (`RUN_RAW_REBUILD = True`) needs the raw external datasets |
| 2. Build the models | `Code/Methodology.ipynb` | `Data/processed/model_inputs/*.parquet` | Model-building notebook; part of the full pipeline. **Retrains models and can overwrite the committed result files** — run it intentionally and keep backups to preserve them |
| 3. Final tables/figures | `Code/Results.ipynb` | committed methodology result tables | Generates the final reported tables and figures from the committed artifacts; no training |
| Selector ablation (robustness) | `Code/selector_robustness/run_selector_ablation_production.py` | `Code/Methodology.ipynb` definitions + processed model-input files | Robustness check that runs from the committed processed inputs |

Because the processed model-input files and the result tables are committed, every
step except the optional raw rebuild in `Code/EDA.ipynb` runs without any external
download. An examiner can clone the repo and run the pipeline
(`EDA.ipynb` → `Methodology.ipynb` → `Results.ipynb`) on the committed dataset.
Note that `Code/Methodology.ipynb` retrains models and can overwrite the committed
result files, so keep backups if you want to preserve them. The raw external
datasets are only needed for the optional raw preprocessing rebuild in
`Code/EDA.ipynb`.

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

The thesis code pipeline is `Code/EDA.ipynb` → `Code/Methodology.ipynb` →
`Code/Results.ipynb`. It starts from the committed 496-well canonical dataset and
needs no external data:

1. `python Code/repro_utils.py` — confirm the committed processed model-input
   files are present and the 496-well dataset is valid.
2. `Code/EDA.ipynb` — prepares and checks the final thesis dataset. By default
   (`RUN_RAW_REBUILD = False`) it loads and checks the committed 496-well dataset.
3. `Code/Methodology.ipynb` — builds the models. This is part of the full
   pipeline. **It retrains models and can overwrite the committed result files**,
   so run it intentionally and keep backups if you want to preserve the committed
   result files. The selector ablation
   `python Code/selector_robustness/run_selector_ablation_production.py` is part of
   this model-building/robustness work.
4. `Code/Results.ipynb` — generates the final reported tables and figures.

**Optional — raw preprocessing rebuild.** `Code/EDA.ipynb` also contains a guarded
rebuild path (`RUN_RAW_REBUILD = True`) that shows how the processed model-input
files were built from the raw external datasets. It is off by default and needs
the raw external datasets listed above.

---

## Amsterdam (legacy)

The thesis began as an Amsterdam-only study. That earlier scope survives only as:

- `Data/processed/amsterdam_reference/` — saved Amsterdam comparison outputs.

The active code defaults to the Netherlands region
(`REGION_NAME = 'netherlands'` in `Code/EDA.ipynb`) and does **not** apply the
old Amsterdam-specific pumping-proximity filter. Treat any Amsterdam-specific
numbers as preliminary/reference, not as the final result.
