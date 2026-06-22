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

### Terminology (used consistently across this repo)

- **Raw external datasets** — the TSMP / COSMO / GLEAM NetCDF (`.nc`) files and
  the BRO GeoPackage (`.gpkg`) files. Large, externally sourced, **not in GitHub**.
- **Processed model-input files** — `Data/processed/model_inputs/*.parquet`. The
  small tables derived from the raw external datasets; they already contain all
  model features and **ship with the repo**.
- **Final Netherlands modelling pipeline** — `Code/Methodology.ipynb` and
  `Code/Results.ipynb` running on the committed processed model-input files. This
  is the canonical pipeline for the thesis results.
- **Canonical thesis dataset** — the committed 496-well processed model-input
  files in `Data/processed/model_inputs/`. This frozen dataset is the canonical
  input for all final thesis results.
- **Raw preprocessing (exploratory)** — `Code/EDA.ipynb`. It shows how the raw
  datasets were prepared. It is **not** required to reproduce the final results.

### Two levels of reproducibility

- **Level 1 — Final thesis results (main path, no external data needed).** The
  final thesis dataset is the committed 496-well processed model-input files in
  `Data/processed/model_inputs/`. Reproduce the final reported tables and figures
  by: (1) `python Code/repro_utils.py` to confirm the committed inputs; (2)
  optionally `Code/EDA.ipynb` with `RUN_RAW_REBUILD = False` to load and check the
  committed 496-well dataset; (3) `Code/Results.ipynb` to rebuild the final tables
  and figures from the committed result artifacts. No raw external datasets and no
  model training are required. **`Code/Methodology.ipynb` is the training notebook
  and is not part of this quick reproduction path** — it retrains models and can
  overwrite the committed result tables (see below).
- **Level 2 — Raw preprocessing (exploratory, external data needed).**
  `Code/EDA.ipynb` shows how the processed dataset was constructed from the raw
  datasets (BRO `.gpkg` + TSMP/COSMO/GLEAM `.nc`). It is exploratory and is not
  part of the final reproducibility path.

### Required external datasets (not in GitHub — provide separately)

| Dataset | Expected local path | Notes |
|---|---|---|
| BRO monitoring network GeoPackage | `Data/Datasets/brogmkenset.gpkg` | BRO bulk download, ~180 MB |
| BRO groundwater-use / pumping GeoPackage | `Data/Datasets/bro_groundwater_use.gpkg` | BRO bulk download, ~48 MB |
| **TSMP** groundwater-table-depth anomaly | `Data/Datasets/TSMP_G2A_monthly_groundwater_table_depth_anomaly_FZJ-IBG3_TSMP_0.1_degree_v1.1996_2016.nc` | FZJ-IBG3 TSMP-G2A NetCDF |
| **COSMO** precipitation anomaly | `Data/Datasets/COSMO_REA6_monthly_precipitation_anomaly_FZJ-IBG3_COSMO_0.1_degree_v1.1995_082019.nc` | FZJ-IBG3 COSMO-REA6 NetCDF |
| **GLEAM** soil-moisture anomaly | `Data/Datasets/GLEAM_monthly_soil_moisture_anomaly_FZJ-IBG3_GLEAM_0.1_degree_v1.1980_2020.nc` | FZJ-IBG3 GLEAM NetCDF |

These raw external datasets (TSMP / COSMO / GLEAM `.nc` and the two BRO `.gpkg`)
are required **only for the Level-2 raw preprocessing rebuild** in `Code/EDA.ipynb`.
They are **not** needed for the final Netherlands modelling pipeline. They are the
files most likely to be reported as missing on a fresh clone — that is expected.

### Datasets that ship with the repository

- `Data/Netherlands_gw_data/` — per-well BRO groundwater record CSVs (the
  Netherlands target panel).
- `Data/Datasets/era5_land_monthly.nc` — small ERA5-Land reference grid
  (**auxiliary**, not used by the final modelling pipeline).
- `Data/processed/model_inputs/*.parquet` — the **small processed model-input
  files** built by the EDA notebook (the frozen **496-well canonical thesis
  dataset**). These let you run the final Netherlands modelling pipeline
  **without** the raw external datasets.
- `Data/processed/.../tables/` and `.../figures/` — the saved EDA, methodology,
  and results outputs reported in the thesis.

### What can be reproduced, and from what

| Stage | Notebook / script | Needs | Level | Notes |
|---|---|---|---|---|
| Input check | `python Code/repro_utils.py` | committed processed model-input files | 1 | Confirms the committed 496-well inputs are present and valid |
| Reproduce final tables/figures | `Code/Results.ipynb` | committed methodology result tables | 1 | **Main reproduction step.** Rebuilds the final tables/figures from committed artifacts; no training |
| Training / model building | `Code/Methodology.ipynb` | `Data/processed/model_inputs/*.parquet` | — | **Retrains models and can overwrite the committed result tables.** Not part of the quick reproduction path; run only to rebuild the models |
| Selector ablation (robustness) | `Code/selector_robustness/run_selector_ablation_production.py` | `Code/Methodology.ipynb` definitions + processed model-input files | 1 | Runs from committed processed inputs |
| Raw preprocessing (exploratory) | `Code/EDA.ipynb` | raw external datasets (BRO `.gpkg` + TSMP/COSMO/GLEAM `.nc`) | 2 | Exploratory only; shows how the processed dataset was built. Not required for the final results. By default it loads and checks the committed 496-well dataset. |

Because the processed model-input files and the result tables are committed, an
examiner can clone the repo and run `Code/Results.ipynb` to reproduce the **final
Netherlands thesis tables and figures without any external download and without
training (Level 1)**. `Code/Methodology.ipynb` is the training notebook; it
retrains models and can overwrite the committed result tables, so it is not part
of the quick reproduction path. The raw external datasets are required only for
the Level-2 raw preprocessing rebuild in `Code/EDA.ipynb`.

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

**Main path — reproduce the final thesis results (Level 1).** This starts from
the committed 496-well canonical dataset and needs no external data and no
training:

1. `python Code/repro_utils.py` — confirm the committed processed model-input
   files are present and the 496-well dataset is valid.
2. *(optional)* `Code/EDA.ipynb` with `RUN_RAW_REBUILD = False` — load and check
   the committed 496-well dataset.
3. `Code/Results.ipynb` — rebuild the final thesis tables and figures from the
   committed result artifacts.

**Training / model building (not the default reproduction step).**
`Code/Methodology.ipynb` is the notebook that builds and trains the models. **It
retrains models and can overwrite the committed result tables**, so run it only
when you want to rebuild the models — not as part of the quick reproduction above.
The selector ablation `python Code/selector_robustness/run_selector_ablation_production.py`
is part of this training/robustness work.

**Optional — raw preprocessing (Level 2, exploratory).** `Code/EDA.ipynb` shows
how the processed model-input files were built from the raw external datasets. By
default it loads and checks the committed 496-well dataset. It is exploratory and
is **not** needed for the final results.

---

## Amsterdam (legacy)

The thesis began as an Amsterdam-only study. That earlier scope survives only as:

- `Data/processed/amsterdam_reference/` — saved Amsterdam comparison outputs.

The active code defaults to the Netherlands region
(`REGION_NAME = 'netherlands'` in `Code/EDA.ipynb`) and does **not** apply the
old Amsterdam-specific pumping-proximity filter. Treat any Amsterdam-specific
numbers as preliminary/reference, not as the final result.
