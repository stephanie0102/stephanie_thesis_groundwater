# Netherlands result — interpretation notes

These notes accompany the saved Netherlands Mode-A result. They are
analytical scaffolding for the thesis and for a possible paper draft; they are
not thesis prose. All numbers come from the saved CSVs in
`Data/processed/methodology/tables/` and `Data/processed/methodology/tables/robustness/`.

## 1. Dataset description (use this wording)

> **All eligible Dutch BRO wells under the 1996–2016 modelling constraints.**

Specifically: the 496 monitoring wells that (a) have at least one BRO `gm_gld`
groundwater-level series with a CSV download URL, (b) pass the
metadata-level temporal filter `first_date ≤ 2005-01-01 AND
last_date ≥ 2014-01-01 AND sum_observations_meta ≥ 500`, (c) survive
one-tube-per-well deduplication, (d) yield ≥ 24 monthly anomaly rows inside the
1996-07 to 2016-06 modelling window, and (e) have ≥ 8 train windows and ≥ 1
test window after the chronological 60 / 15 / 10 / 15 split. Source: see
`Data/processed/eda/tables/nl_candidate_funnel_final.csv`.

Do **not** describe these as "all Netherlands wells" or "the Dutch
groundwater dataset" — the funnel collapses 112,627 national GLD series to
496 final modelling wells, so the result reflects the model-eligible subset,
not the full national network.

## 2. The aggregate accuracy gain is small

Pooled test RMSE on 16,547 test windows:

| Model | RMSE | MAE | R² |
|---|---:|---:|---:|
| Context-Aware Selective Learning | **2.0957** | 0.919 | 0.187 |
| Site-Hard Expert Selector | 2.0989 | 0.927 | 0.184 |
| Deep Context LSTM (No TL) | 2.1062 | 0.933 | 0.178 |
| Deep Context LSTM (Always TL) | 2.1095 | 0.926 | 0.176 |
| Random Forest | 2.1538 | 0.866 | 0.141 |

The headline gap between Context-Aware Selective Learning and the next-best
model (Site-Hard) is **−0.0033 RMSE**. The gap to the No-TL parent is
**−0.0105 RMSE**. These are small in absolute units and would not survive a
naive observation-level comparison.

The site-cluster bootstrap (1000 resamples; see
`tables/robustness/nl_site_bootstrap_significance.csv`) tells the same story
with confidence intervals:

| Comparison | mean Δ | 95 % CI | CI excludes 0 |
|---|---:|:---:|---|
| Selective − Site-Hard | −0.0033 | [−0.0064, −0.0007] | yes |
| Selective − No TL | −0.0115 | [−0.0200, −0.0066] | yes |
| Selective − Always TL | −0.0125 | [−0.0341, +0.0044] | no |
| Selective − Random Forest | −0.0518 | [−0.1604, +0.0367] | no |

So pooled RMSE gives Selective a genuine edge over Site-Hard and over No TL,
but not over Always TL or Random Forest at the bootstrap level (the latter
two have wide CIs driven by a handful of high-variance hard sites).

Paired site-level Wilcoxon signed-rank tests
(`tables/robustness/nl_paired_site_tests.csv`) over the 496 wells, with Holm
correction, are more decisive — Selective wins **per site** on all four
comparisons (Holm-adjusted p < 0.05 for every pair). For Random Forest the
direction flips: Selective is worse on most individual wells (median per-site
RMSE diff +0.07) but better pooled, because Random Forest blows up on a few
hard sites that dominate the squared-error aggregate.

## 3. The main contribution is risk control, not accuracy

The per-well outcome distribution (`tables/transfer/negative_transfer_ci.csv`):

| metric | rate | Wilson 95 % CI |
|---|---:|:---:|
| Always TL helps a well | 0.587 | [0.543, 0.629] |
| **Always TL harms a well** | **0.413** | **[0.371, 0.457]** |
| Selective partial rescue on harmed wells | **0.980** | [0.951, 0.992] |
| Selective full rescue on harmed wells | 0.259 | [0.203, 0.323] |

That is the result to lead with. Fixed transfer learning **harms** roughly
41 % of the wells in this dataset (95 % CI 37 – 46 %). Selective transfer
**recovers most of the loss** on 98 % of those harmed wells (95 % CI 95 – 99 %),
even though it only **fully** restores the No-TL level on ~26 % of them. So
Selective trades a tiny pooled gain for a large reduction in worst-case
per-well damage. This is the journal-style argument the thesis can defend
without overclaiming.

## 4. The `maxsim0.60` source filter is the most fragile choice

Source-filter sensitivity diagnostic
(`tables/robustness/nl_source_filter_sensitivity.csv`) — number of TSMP source
cells surviving each cosine-similarity threshold against the NL train period:

| τ | source cells kept | share |
|---:|---:|---:|
| no filter | 512 | 100 % |
| 0.30 | 288 | 56 % |
| 0.35 | 198 | 39 % |
| 0.40 | 133 | 26 % |
| 0.45 | 76 | 15 % |
| 0.50 | 34 | 7 % |
| 0.55 | 12 | 2 % |
| **0.60 (main run)** | **1** | **0.2 %** |

At the Amsterdam-publication threshold (0.60), only **one** TSMP source cell
survives for the entire 496-well NL target. This means the Always-TL parent
in this run effectively pretrains on a single source cell, which is a
material weakening of the source domain compared to the Amsterdam protocol.

The current notes do **not** propose changing the main result based on a
lower τ — that would require re-training all parents at each τ on validation
data, which is out of scope for the current write-up. The diagnostic is a
limitation to be acknowledged in the discussion: at NL scale, the Amsterdam
maxsim0.60 cut is borderline degenerate, and a future experiment should
reselect τ on validation RMSE only, possibly using ERA5 or another national
source domain (Mode B in the EDA notes).

## 5. What was *not* re-run for the Netherlands

To avoid implying analyses that were not actually performed:

- Seed-stability robustness (multiple seeds): **not re-run**.
- Rolling-temporal folds: **not re-run**.
- Selector ablation across feature subsets: **not re-run**.
- Label-budget curves: **not re-run**.
- Cluster bootstrap on the *original* Amsterdam protocol (the 2nd cluster
  bootstrap saved in the methodology folder): **not re-run**; only the
  site-cluster bootstrap reported above was computed.
- Source-filter retraining at lower τ: **not re-run** (only the cell-count
  diagnostic is computed).

These omissions should be stated as scope limits, not skipped silently.

## 6. Suggested one-paragraph summary for the abstract

> On 496 eligible Dutch BRO wells under the 1996–2016 modelling constraints,
> Context-Aware Selective Learning attains the best pooled test RMSE (2.0957)
> across five models; the gain over the No-TL parent is small (-0.011 RMSE,
> 95 % CI [-0.020, -0.007] by site-cluster bootstrap; Wilcoxon Holm-adjusted
> *p* < 1e-19 per-site). The substantive finding is at the well level: fixed
> transfer learning harms 41 % of wells (95 % CI 37–46 %), and selective
> transfer partially rescues 98 % of those harmed wells (95 % CI 95–99 %),
> trading a marginal pooled gain for a substantial reduction in worst-case
> per-well damage. The result generalises the Amsterdam thesis pipeline at
> national scale, but the Amsterdam maxsim0.60 source filter retains only 1
> of 512 TSMP source cells under NL scope and should be revisited in future
> work.
