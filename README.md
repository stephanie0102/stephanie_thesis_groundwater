# Groundwater Thesis — Selective Transfer Learning for the Netherlands

This repository contains the code, notebooks, and saved outputs for my MSc thesis
on forecasting groundwater anomalies (water-table-depth anomaly, `wtda`) for wells
in the Netherlands.

The question I study is *when* transfer learning helps. I compare three options
under the same data and the same train/test splits: no transfer, fixed (always)
transfer, and selective transfer. The selective method is a Context-Aware
Selective Learning (CASL) gate that decides, per well, how much transfer to use.

**What CASL does, and does not, claim.** CASL gives a small but consistent RMSE
improvement over the baselines. Its main point is transfer-risk control: it lowers
the risk of negative transfer by choosing per well how much to transfer. It is not
a large jump in accuracy, and it is not a full operational drought early-warning
system.

## The code pipeline

Run the three notebooks in this order:

`Code/EDA.ipynb` → `Code/Methodology.ipynb` → `Code/Results.ipynb`

- **`Code/EDA.ipynb`** prepares and checks the dataset. By default it loads the
  saved 496-well dataset and needs no raw data. It also has an optional rebuild
  path (off by default, `RUN_RAW_REBUILD = False`) that shows how the dataset was
  built from the raw files.
- **`Code/Methodology.ipynb`** builds and trains the models (no transfer, fixed
  transfer, selective transfer, the CASL selector, and the robustness checks).
  Note: it retrains the models and can overwrite the saved result files, so run it
  on purpose and keep a backup if you want to keep the current results.
- **`Code/Results.ipynb`** makes the final tables and figures from the saved
  results.

## Setup and how to run

```bash
pip install -r requirements.txt   # reference list, not a locked environment
python Code/repro_utils.py        # check the processed files and the 496-well dataset
```

Run `python Code/repro_utils.py` first. For each required file it tells you whether
it is present and, if not, where it should go. The processed files and the result
tables are committed, so you can clone the repo and run the whole pipeline without
downloading any raw data. The only step that needs raw data is the optional rebuild
inside EDA.

## The dataset

The final thesis dataset is the saved 496-well processed files in
`Data/processed/model_inputs/` (parquet). These already hold everything the models
need: the groundwater observations, TSMP-G2A groundwater anomalies, COSMO-REA6
precipitation anomalies, GLEAM soil-moisture anomalies, and BRO groundwater-use
features. The analysis starts from these files.

The raw files below are the original sources I used to build the processed files.
They are **not committed** because they are large, and they are only needed for the
optional rebuild in EDA. On a fresh clone they show up as missing — that is normal.

| Raw source | Expected path | Notes |
|---|---|---|
| BRO monitoring network | `Data/Datasets/brogmkenset.gpkg` | BRO download, ~180 MB; gives `water_level_nap_m`, `wtda`, and the target wells |
| BRO groundwater-use | `Data/Datasets/bro_groundwater_use.gpkg` | BRO download, ~48 MB; pumping-proxy features |
| TSMP-G2A groundwater anomaly | `Data/Datasets/TSMP_G2A_monthly_groundwater_table_depth_anomaly_FZJ-IBG3_TSMP_0.1_degree_v1.1996_2016.nc` | variable `wtd_a`, renamed to `tsmp_wtda` |
| COSMO-REA6 precipitation anomaly | `Data/Datasets/COSMO_REA6_monthly_precipitation_anomaly_FZJ-IBG3_COSMO_0.1_degree_v1.1995_082019.nc` | variable `pr_a` |
| GLEAM soil-moisture anomaly | `Data/Datasets/GLEAM_monthly_soil_moisture_anomaly_FZJ-IBG3_GLEAM_0.1_degree_v1.1980_2020.nc` | variable `sm_a` |

The three large gridded NetCDF files are shared in a Google Drive folder:

https://drive.google.com/drive/folders/15gmZoAzqh4nt2hRrfALUoGn-KzzaU85B?usp=sharing

The Google Drive folder contains the three large gridded NetCDF files used in the
optional preprocessing rebuild. The final 496-well processed thesis dataset is
already included in this repository, so these files are not needed to reproduce the
final reported tables and figures. If you do want to run the rebuild, download these
files into `Data/Datasets/`:

- `TSMP_G2A_monthly_groundwater_table_depth_anomaly_FZJ-IBG3_TSMP_0.1_degree_v1.1996_2016.nc`
- `COSMO_REA6_monthly_precipitation_anomaly_FZJ-IBG3_COSMO_0.1_degree_v1.1995_082019.nc`
- `GLEAM_monthly_soil_moisture_anomaly_FZJ-IBG3_GLEAM_0.1_degree_v1.1980_2020.nc`

The raw BRO files (`brogmkenset.gpkg` and `bro_groundwater_use.gpkg`) are not shared
in the Google Drive folder. The BRO groundwater observations and groundwater-use
features needed for the final experiments are already inside the processed parquet
files in `Data/processed/model_inputs/`.

`Data/Datasets/era5_land_monthly.nc` and the CLC land-cover file are kept locally
but are not used by the final models.

All paths in the code are relative to the repository root, so nothing depends on my
machine.

### Data references

- BRO groundwater monitoring and groundwater-use data: Dutch Basisregistratie
  Ondergrond (BRO) / DINOloket.
- TSMP-G2A, COSMO-REA6, and GLEAM gridded inputs: Jülich DATA record "Advancing
  AI-based pan-European groundwater monitoring", DOI `10.26165/JUELICH-DATA/ZBLDIR`.

## What is in the repository

`Code/`
- `EDA.ipynb` — defines the Netherlands target wells, builds the processed files,
  and exports the EDA tables and figures.
- `Methodology.ipynb` — the modelling pipeline: the transfer comparisons, the CASL
  selector, and the robustness checks.
- `Results.ipynb` — the final figures and short result text.
- `repro_utils.py` — checks which input files are present.
- `selector_robustness/run_selector_ablation_production.py` — the selector-input
  ablation; runs from the processed files.

`Data/`
- `Datasets/` — raw climate and geospatial inputs (mostly not committed; see the
  table above).
- `Netherlands_gw_data/` — the per-well groundwater CSVs for the Netherlands.
- `processed/` — the saved outputs, grouped by stage:
  - `model_inputs/` — the 496-well processed files (committed).
  - `eda/`, `methodology/`, `results/` — the tables and figures for each stage.
  - `amsterdam_reference/` — old Amsterdam outputs, kept only for the
    scope-change discussion.

## Amsterdam (earlier scope)

The project started as an Amsterdam-only study. Only the saved Amsterdam outputs in
`Data/processed/amsterdam_reference/` remain. The code now defaults to the
Netherlands (`REGION_NAME = 'netherlands'` in `Code/EDA.ipynb`) and does not use
the old Amsterdam pumping-proximity filter. Treat any Amsterdam numbers as
early/reference results, not the final ones.
