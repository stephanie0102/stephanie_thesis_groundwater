# Final Netherlands result — interpretation notes

These notes summarise the final Netherlands result after the source-filter
threshold was reselected on the Netherlands **validation** split, not inherited
from Amsterdam. The thesis target scope and baseline framing described below are
the canonical versions to quote.

**Naming note.** "SARP-style" was an earlier internal label for the Baseline LSTM
baselines reported in the thesis; the final thesis refers to these models as
Baseline LSTM (No TL) and Baseline LSTM (TL).

**Split roles (use this terminology consistently).** *Validation* = source-filter
threshold selection (the `maxsim0.40` decision); *calibration* = selector (gate)
training; *test* = final reporting. The source filter is **validation-selected**:
`maxsim0.40` is selected by validation RMSE; calibration is not used to choose the
final source-filter threshold and remains reserved for selector training. Prefer "validation-selected source filter" and avoid
"validation/calibration-selected", since calibration is reserved for selector
training.

## 1. Final framing

- **Target domain (final).** *All eligible Dutch BRO wells under the 1996–2016
  modelling constraints.* This is the 496-well Netherlands Mode-A subset:
  national BRO `gm_gld` series with CSV URLs, retained when `first_date ≤
  2005-01-01 AND last_date ≥ 2014-01-01 AND sum_observations_meta ≥ 500`,
  deduplicated to one tube per well, with ≥ 24 monthly anomaly rows in the
  1996-07 to 2016-06 modelling window and ≥ 8 train / ≥ 1 test window in the
  chronological 60 / 15 / 10 / 15 split. Funnel:
  `Data/processed/eda/tables/nl_candidate_funnel_final.csv`.

- **Source domain.** The TSMP / COSMO-REA6 / GLEAM-derived European-scale
  source / pretraining table at `Data/processed/model_inputs/pretrain_supervised_table.parquet`
  (122,880 rows × 21 cols, 512 source cells).

- **Baseline / anchor.** SARP-style local LSTM and SARP-style LSTM-TL,
  implemented in `Code/Methodology.ipynb` as `Baseline LSTM (No TL)` and
  `Baseline LSTM (TL)` (the stacked LSTM 128 → 64 → 32 backbone with no
  context branch and no site embedding). These are the *baselines* against
  which the thesis claims improvement.

- **Contribution.** Context-Aware Selective Learning: a deep-context
  per-well gate that blends a No-TL and an Always-TL parent at each window,
  trained on the calibration split using `GroupKFold` over `site_id`. The
  contribution is framed as treating transfer learning as a **well-level
  decision**, not as a single fixed rule.

- **Source-filter rule (final).** `maxsim0.40` — selected by minimum
  *validation* RMSE of Context-Aware Selective Learning across four candidate
  filters (no_filter / 0.40 / 0.50 / 0.60) on the Netherlands target.
  Calibration is not used to choose the final source-filter threshold and remains
  reserved for selector training. Test RMSE was NOT used to choose
  the filter. The Amsterdam-publication `maxsim0.60` rule is retained as a
  *legacy / sensitivity* point only. See
  `Data/processed/methodology/tables/source_filter_selection/selected_source_filter_protocol.csv`.

## 2. Final SARP comparison ([sarp_baseline_comparison.csv](../tables/../methodology/tables/core_results/sarp_baseline_comparison.csv))

Test split, 496 wells, 16,547 test windows, source filter = `maxsim0.40`:

| Rank | model_family | RMSE | MAE | R² | uses TL | SARP | selective |
|---:|---|---:|---:|---:|:---:|:---:|:---:|
| 1 | **Context-Aware Selective Learning** | **2.0925** | 0.909 | **0.189** | ✓ | – | ✓ |
| 2 | Site-Hard Expert Selector | 2.0964 | 0.917 | 0.186 | ✓ | – | ✓ |
| 3 | Deep Context LSTM (Always TL) | 2.0984 | 0.915 | 0.185 | ✓ | – | – |
| 4 | Deep Context LSTM (No TL) | 2.1062 | 0.933 | 0.178 | – | – | – |
| 5 | Random Forest | 2.1538 | 0.866 | 0.141 | – | – | – |
| 6 | Baseline LSTM (No TL) | 2.3229 | 1.058 | 0.001 | – | **SARP** | – |
| 7 | Baseline LSTM (TL) | 2.3435 | 1.069 | -0.017 | ✓ | **SARP** | – |

- The thesis-contribution model (Selective) beats **both SARP baselines** by
  ~0.23 RMSE (~10 %) — the largest gap in the table.
- Context-Aware (No TL) already beats SARP (No TL) by 0.22 RMSE. So the
  context branch + site embedding architecture is doing most of the heavy
  lifting *before* transfer learning enters the picture.
- The pooled gain of Selective over the next best ranked model is small
  (~0.004 RMSE vs Site-Hard, ~0.006 vs Always TL), but the well-level
  picture below shows where the substantive contribution sits.

## 3. Aggregate RMSE with confidence intervals (site-cluster bootstrap, 1000 resamples)

Anchor = Context-Aware Selective Learning. See
`tables/robustness/nl_site_bootstrap_significance.csv`.

| Comparison | mean Δ RMSE | 95 % CI | CI excludes 0 |
|---|---:|:---:|---|
| Selective − Site-Hard | -0.0043 | [-0.0084, -0.0019] | **yes** |
| Selective − No TL | -0.0145 | [-0.0218, -0.0089] | **yes** |
| Selective − Always TL | -0.0060 | [-0.0103, -0.0012] | **yes** |
| Selective − Random Forest | -0.0549 | [-0.1642, +0.0321] | no (RF tail) |
| Selective − Baseline LSTM (No TL) | **-0.2314** | [-0.3308, -0.1367] | **yes** |
| Selective − Baseline LSTM (TL) | **-0.2526** | [-0.3610, -0.1447] | **yes** |

At the validation-selected source filter, Selective beats the No-TL parent,
the Always-TL parent, the Site-Hard variant, and both SARP baselines with
confidence intervals that exclude zero. Random Forest remains the one
comparison where the bootstrap CI is wide because RF loses badly on a few
extreme wells that dominate the squared-error aggregate.

## 4. Paired site-level Wilcoxon (Holm-corrected) — `tables/robustness/nl_paired_site_tests.csv`

| Comparison | median Δ per-site RMSE | p (Holm) | significant @ 0.05 |
|---|---:|---:|:---:|
| Selective vs Site-Hard | -0.0095 | 6e-13 | ✓ |
| Selective vs No TL | -0.0243 | 1e-28 | ✓ |
| Selective vs Always TL | -0.0095 | 1e-12 | ✓ |
| Selective vs Random Forest | +0.0699 | 2e-18 | ✓ (RF wins per-site) |
| Selective vs Baseline LSTM (No TL) | -0.0177 | 2e-6 | ✓ |
| Selective vs Baseline LSTM (TL) | -0.0178 | 1e-6 | ✓ |

All paired tests are highly significant after Holm correction. The Random
Forest case is the one direction-flip — RF beats Selective per-site but
loses pooled — a known artefact of squared-error aggregation across
heterogeneous wells.

## 5. Negative-transfer rate and selective rescue (Wilson 95 % CIs)

`tables/transfer/nl_negative_transfer_ci.csv` (denominator = 496 wells; 207 harmed):

| metric | rate | Wilson 95 % CI |
|---|---:|:---:|
| Always TL helps a well | 0.583 | [0.539, 0.625] |
| **Always TL harms a well** | **0.417** | **[0.375, 0.461]** |
| Selective partial rescue on harmed wells | **0.990** | [0.966, 0.997] |
| Selective full rescue on harmed wells | **0.386** | [0.323, 0.454] |

Compared with the legacy `maxsim0.60` run, the selected filter:

- Slightly raises the **harm rate** of fixed transfer (41.7 % vs 41.3 % at
  τ = 0.60). This is real: a larger source pool gives Always-TL more
  opportunities to misfit harder NL wells.
- **Lifts the full-rescue rate by ~13 percentage points** (38.6 % vs 25.9 %)
  and the partial-rescue rate by ~1 point (99.0 % vs 98.0 %). The selector
  has more useful disagreement to exploit at τ = 0.40.

This is the journal-style argument: with a Netherlands-validated source filter,
the **selective rescue** of harmed wells is substantially stronger than under
the inherited Amsterdam rule, and the small pooled RMSE gain is robust at the
well level.

## 6. Source-filter sensitivity table

`tables/robustness/nl_source_filter_sensitivity.csv`. Full Methodology pipeline
re-run at four candidate τ values:

| τ | source cells | val RMSE | cal RMSE | test RMSE |
|:---:|---:|---:|---:|---:|
| no_filter (512) | 512 | 1.5909 | **2.0561** | 2.0722 |
| **0.40 (selected)** | 133 | **1.5896** | 2.0583 | 2.0925 |
| 0.50 | 34 | 1.5903 | 2.0506 | **2.0644** |
| 0.60 (legacy) | 1 | 1.5902 | 2.0581 | 2.0957 |

The validation differences are small (the lowest val RMSE differs from the
highest by only 0.0013). The selected τ = 0.40 is therefore not a dominant
winner — it is the validation-best on a tight cluster. A defensible
alternative would be `maxsim0.50` (lowest *test* RMSE) but choosing on test
RMSE would be circular, so the validation rule stands.

## 7. What the main claim should rest on

1. **Aggregate RMSE with confidence intervals.** Selective beats the No-TL
   parent and both SARP baselines with bootstrap CIs that exclude zero.
2. **Negative-transfer rate.** Always TL harms 41.7 % of Netherlands wells
   (95 % CI 37.5–46.1 %). Naively applying transfer learning is *not* safe.
3. **Selective rescue rate.** Selective partial-rescues 99 % and
   full-rescues 39 % of harmed wells under the validation-selected source
   filter — a substantive risk-control effect.
4. **Comparison against SARP baselines.** Selective beats SARP (No TL) by
   ~0.23 RMSE and SARP (TL) by ~0.25 RMSE. The improvement is one order of
   magnitude larger than the gap between Selective and the next deep model,
   which makes the contribution defensible even when readers question the
   small head-to-head Selective-vs-Always-TL margin.

## 8. Wording / scoping rules

- **Use:** “all eligible Dutch BRO wells under the 1996–2016 modelling
  constraints”.
- **Do not use:** “all Dutch wells”, “the Dutch groundwater dataset”,
  “the whole Netherlands network”, “national groundwater forecast”, or any
  variant that implies the result generalises beyond the 496-well
  model-eligible subset.
- The baseline framing is **SARP-style**, not “the Amsterdam baseline” or
  “the previous thesis baseline”. The Amsterdam protocol is, at most, a
  historical motivation for the methodology — the comparison is against
  SARP-style LSTM / LSTM-TL.
- The source filter is **Netherlands-selected on validation**, not inherited
  from Amsterdam.
