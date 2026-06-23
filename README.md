# Groundwater Thesis — Selective Transfer Learning (Netherlands)

This repository has the code, notebooks, and saved outputs for my MSc thesis. The
goal is to forecast groundwater anomalies (water-table-depth anomaly, `wtda`) for
wells in the Netherlands.

I study one question: when does transfer learning help? Using the same data and the
same train/test splits, I compare three options: no transfer, fixed (always)
transfer, and selective transfer. The selective method is a Context-Aware Selective
Learning (CASL) gate that decides, per well, how much transfer to use.

**What CASL claims.** CASL gives a small but steady RMSE improvement over the
baselines. Its main point is transfer-risk control: it lowers the risk of negative
transfer by choosing per well how much to transfer. It is not a big jump in
accuracy, and it is not a full drought early-warning system.

## How to run

Run the three notebooks in this order:

`Code/EDA.ipynb` → `Code/Methodology.ipynb` → `Code/Results.ipynb`

- **`Code/EDA.ipynb`** prepares and checks the dataset. By default it loads the
  saved 496-well dataset and needs no raw data.
- **`Code/Methodology.ipynb`** builds and trains the models (no transfer, fixed
  transfer, selective transfer, the CASL selector, and the robustness checks). It
  retrains the models and can overwrite the saved results, so run it on purpose and
  keep a backup if you want to keep the current results.
- **`Code/Results.ipynb`** makes the final tables and figures from the saved
  results.

Before running, set up and check the inputs:

```bash
pip install -r requirements.txt   # reference list, not a locked environment
python Code/repro_utils.py        # checks the processed files and the 496-well dataset
```

`repro_utils.py` tells you, for each needed file, whether it is there and where it
should go. The processed files and the result tables are already in the repo, so you
can clone it and run the whole pipeline without downloading any raw data. Only the
optional rebuild in EDA needs the raw files.

## The dataset

The final dataset is the saved 496-well files in `Data/processed/model_inputs/`
(parquet). They already hold everything the models need: the groundwater
observations, TSMP-G2A groundwater anomalies, COSMO-REA6 precipitation anomalies,
GLEAM soil-moisture anomalies, and BRO groundwater-use features. All the analysis
starts from these files.

The raw files below are the original sources I used to build the processed files.
They are **not in the repo** because they are large. You only need them for the
optional rebuild in EDA, so on a fresh clone they show up as missing — that is
normal.

| Raw source | Where it goes | Notes |
|---|---|---|
| BRO monitoring network | `Data/Datasets/brogmkenset.gpkg` | BRO download, ~180 MB; gives `water_level_nap_m`, `wtda`, and the target wells |
| BRO groundwater-use | `Data/Datasets/bro_groundwater_use.gpkg` | BRO download, ~48 MB; pumping-proxy features |
| TSMP-G2A groundwater anomaly | `Data/Datasets/TSMP_G2A_monthly_groundwater_table_depth_anomaly_FZJ-IBG3_TSMP_0.1_degree_v1.1996_2016.nc` | variable `wtd_a`, renamed to `tsmp_wtda` |
| COSMO-REA6 precipitation anomaly | `Data/Datasets/COSMO_REA6_monthly_precipitation_anomaly_FZJ-IBG3_COSMO_0.1_degree_v1.1995_082019.nc` | variable `pr_a` |
| GLEAM soil-moisture anomaly | `Data/Datasets/GLEAM_monthly_soil_moisture_anomaly_FZJ-IBG3_GLEAM_0.1_degree_v1.1980_2020.nc` | variable `sm_a` |

The three large NetCDF files (TSMP-G2A, COSMO-REA6, GLEAM) are in a Google Drive
folder:

https://drive.google.com/drive/folders/15gmZoAzqh4nt2hRrfALUoGn-KzzaU85B?usp=sharing

These three files are only used by the optional rebuild in EDA. The final 496-well
dataset is already in the repo, so you do not need them to reproduce the final
tables and figures. If you want to run the rebuild, put the three files in
`Data/Datasets/`.

The two BRO files (`brogmkenset.gpkg` and `bro_groundwater_use.gpkg`) are **not** in
the Google Drive folder. The BRO observations and groundwater-use features that the
final experiments need are already inside the processed parquet files.

All paths in the code are relative to the repo root, so nothing depends on my
computer.

### Data sources

- BRO groundwater monitoring and groundwater-use data: Dutch Basisregistratie
  Ondergrond (BRO) / DINOloket.
- TSMP-G2A, COSMO-REA6, and GLEAM gridded inputs: Jülich DATA record "Advancing
  AI-based pan-European groundwater monitoring", DOI `10.26165/JUELICH-DATA/ZBLDIR`.

## What is in the repo

`Code/`
- `EDA.ipynb` — picks the Netherlands target wells, builds the processed files, and
  exports the EDA tables and figures.
- `Methodology.ipynb` — the modelling pipeline: the transfer comparisons, the CASL
  selector, and the robustness checks.
- `Results.ipynb` — the final figures and short result text.
- `repro_utils.py` — checks which input files are present.
- `selector_robustness/run_selector_ablation_production.py` — the selector-input
  ablation; runs from the processed files.

`Data/`
- `Datasets/` — raw inputs (not in the repo; see the table above).
- `Netherlands_gw_data/` — the per-well groundwater CSVs for the Netherlands.
- `processed/` — the saved outputs, grouped by stage:
  - `model_inputs/` — the 496-well processed files (in the repo).
  - `eda/`, `methodology/`, `results/` — the tables and figures for each stage.
  - `amsterdam_reference/` — old Amsterdam outputs, kept only for the scope-change
    discussion.

## Amsterdam (earlier scope)

The project started as an Amsterdam-only study. Only the saved Amsterdam outputs in
`Data/processed/amsterdam_reference/` remain. The code now defaults to the
Netherlands (`REGION_NAME = 'netherlands'` in `Code/EDA.ipynb`) and does not use the
old Amsterdam pumping filter. Treat any Amsterdam numbers as early/reference
results, not the final ones.
