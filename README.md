# Groundwater Thesis

This repository contains the notebooks and processed outputs for my master's thesis on Amsterdam groundwater forecasting.

My main question is whether Amsterdam forecasting should use no transfer, fixed transfer, or selective transfer under the same data and split design.

## Repository Structure

`Code/`

- `Exploratory Data Analysis.ipynb`: defines the Amsterdam target well set and exports the EDA tables and figures.
- `Methodology.ipynb`: runs the fixed modelling pipeline, the transfer-learning comparisons, and the robustness checks.
- `Results.ipynb`: prepares the final thesis figures and short result text for the written Results chapter.

`Data/`

- `Datasets/`: external climate and geospatial input data.
- `Amsterdam_gw_data/`: local groundwater well CSV files for the Amsterdam target set.
- `processed/`: processed outputs organised by analysis stage.

## Processed Data Structure

`Data/processed/eda/`

- `tables/overview/`: corpus overview and missingness summaries.
- `tables/correlations/`: lag and correlation diagnostics.
- `tables/similarity/`: source-target similarity tables and best-match tables.
- `figures/overview/`: coverage plots, distribution plots, and representative signal plots.
- `figures/correlations/`: EDA correlation heatmaps.
- `figures/similarity/`: source-target similarity figures.
- `target_universe/`: files used to document the Amsterdam target well selection.

`Data/processed/model_inputs/`

- Shared modelling inputs created in EDA and used later in the methodology notebook.

`Data/processed/methodology/`

- `tables/protocol/`: protocol summary, feature inventory, similarity summary, and transfer configuration.
- `tables/core_results/`: main model comparison tables and site-level core outputs.
- `tables/selector/`: selector search results, selector decisions, and selector feature importance.
- `tables/transfer/`: transfer-effect diagnostics, cohorts, and negative-transfer summaries.
- `tables/robustness/`: significance tests, seed stability, rolling folds, label-budget checks, and ablations.
- `figures/`: methodology and robustness figures.

`Data/processed/results/`

- `figures/`: final clean figures for the thesis.

## Workflow

1. Run `Code/Exploratory Data Analysis.ipynb`.
2. Run `Code/Methodology.ipynb`.
3. Run `Code/Results.ipynb`.