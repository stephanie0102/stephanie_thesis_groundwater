# Technical follow-up — supplementary evidence summary

This note documents a set of supplementary analyses built **on top of the final
Netherlands pipeline**. No parent or core models were retrained, the Netherlands
core results are unchanged, and the Amsterdam reference artefacts are unchanged.
All quantities below are derived from already-saved final artefacts.

## 1. H1 — source-target similarity vs transfer gain
Files: `methodology/tables/transfer/h1_similarity_transfer_evidence.csv`,
`methodology/tables/transfer/h1_similarity_tertiles.csv`,
`results/figures/results_h1_similarity_transfer_gain.png`.

With `transfer_gain = RMSE_NoTL − RMSE_AlwaysTL` over the 496 final wells, the
pooled rank association between best source-target similarity and transfer gain is
weak and not significant (Spearman ρ = 0.067, p = 0.14) but is in the expected
direction. In a controlled regression (`transfer_gain ~ best_similarity +
target_variability + n_test_windows`) similarity is not individually significant
(p = 0.12); the number of test windows is the dominant term. Similarity
diagnostics nonetheless account for roughly 15 % of the selector's permutation
importance.

**Result: H1 is partially supported** — source-target similarity is informative but
not sufficient as a standalone explanation of transfer success.

## 2. Negative-transfer rescue — effect size
Files: `methodology/tables/transfer/rescue_effect_size_summary.csv`,
`methodology/tables/transfer/rescue_effect_size_by_site.csv`,
`results/figures/results_rescue_effect_size_distribution.png`.

On the 207 wells where fixed transfer harms accuracy (`RMSE_AlwaysTL >
RMSE_NoTL`), the context-aware selector partially rescues 99.0 % of wells
(`RMSE_AlwaysTL − RMSE_CASL > 0`), consistent with the existing confidence-interval
table. The magnitude is modest: median improvement 0.031 RMSE (IQR 0.025); 91 % of
harmed wells improve by more than 0.01 RMSE and 22 % by more than 0.05 RMSE. The
selector fully recovers to below the No-TL parent (`RMSE_NoTL − RMSE_CASL > 0`) on
38.6 % of harmed wells.

**Result:** the high partial-rescue rate is robust and consistently right-signed,
but reflects mostly small-to-moderate damage limitation rather than large rescues;
it should be reported together with the effect-size magnitudes and the full-rescue
rate.

## 3. Random Forest fairness
File: `methodology/tables/core_results/random_forest_fairness_summary.csv`.

Context-Aware Selective Learning has the lowest test RMSE (2.0925 vs Random Forest
2.1538) and the highest test R² (0.189). Random Forest has the lowest test MAE
(0.866 vs 0.909) and is the single-best model on the most individual wells
(166 of 496). The selector is preferred on RMSE because this work prioritises
large-error / extreme-anomaly risk; Random Forest is the stronger central-tendency
model. The two are reported as a trade-off rather than treating Random Forest's MAE
or per-well lead as a refutation of the selector.

## 4. Operational event-metric feasibility
File: `results/tables/operational_event_metrics_feasibility.csv` (illustrative).

Event-based detection metrics (recall, precision, F1, false-alarm rate at a
predeclared standardized-anomaly threshold of 1.5) **can** be computed from the
already-saved test-split prediction detail without rerunning any model. An
illustrative table is provided for both anomaly tails. Severe-event recall is low
(single-digit to ~30 %) with high precision, i.e. the models under-shoot extremes.
Accordingly the appropriate framing is:

> "This thesis provides a forecasting and transfer-risk control framework, not a
> complete operational drought early-warning system."

## 5. Selector ablation — PRODUCTION-CONSISTENT
Files: `methodology/tables/robustness/selector_ablation_production_summary.csv`,
`methodology/tables/robustness/selector_ablation_production_by_seed.csv`,
`methodology/tables/robustness/selector_ablation_parent_predictions_{val,cal,test}.csv`,
`results/figures/results_selector_ablation_production.png`.
Reproduced by `Code/selector_robustness/run_selector_ablation_production.py`.

This ablation reuses the production implementation end to end: the
validation-selected source filter (`maxsim0.40`), the same
train/validation/calibration/test split, the same parent models, and the same
calibration-trained gate. The parent models were retrained **once** (seed 42) to
recover and persist the validation/calibration/test parent predictions; the gate
was then retrained on the **calibration** split for each feature-group variant and
evaluated on **test** only. The main production result tables were not modified.

The full selector reproduces the production CASL result exactly (test RMSE
2.0925, MAE 0.909, R² 0.189, 99.0 % partial / 38.6 % full rescue), confirming the
retrained parents match production. Test RMSE by removed group (Δ vs full
selector; mean over three gate seeds, which were identical — the gate is
deterministic given fixed parents, so this is selector-training stability, not
parent-seed robustness):

| Variant | n_feat | test RMSE | Δ RMSE vs full | full-rescue |
|---|---:|---:|---:|---:|
| no_recent_target_state | 29 | 2.0948 | **+0.0023** | 0.348 |
| no_seasonality | 43 | 2.0933 | +0.0008 | 0.406 |
| full_selector | 47 | 2.0925 | 0.000 | 0.386 |
| no_site_history | 34 | 2.0924 | −0.0001 | 0.415 |
| no_pumping_anthropogenic | 44 | 2.0922 | −0.0002 | 0.411 |
| no_similarity | 33 | 2.0919 | −0.0006 | 0.396 |

**Reading (no overclaiming).** Removing **recent target-state inputs is the only
ablation that measurably degrades the selector** (largest RMSE rise, lowest R²,
full-rescue drops 0.386 → 0.348) — recent target state is the strongest group.
Seasonality is a small positive contributor. Similarity, site-history and pumping
are near-redundant for pooled test RMSE: dropping them moves RMSE by ≤ 0.0006
(within noise), and dropping similarity even nudges pooled RMSE marginally lower.
This is consistent with H1 (Section 1): similarity is used as one selector input
and carries ~15 % of gate permutation importance, but it is not decisive on its
own. Overall the selector draws on multiple feature groups with recent target
state dominant; all single-group effects are small, so the selector is robust to
dropping any one auxiliary group.

## Citation status
- **Safe to cite as final evidence:** H1 similarity result (Section 1), rescue
  effect-size result (Section 2), Random Forest fairness (Section 3),
  production-consistent selector ablation (Section 5).
- **Cite as a feasibility statement only:** operational event metrics (Section 4).
- The earlier selector-only diagnostic (test-split cross-fit) is superseded by
  Section 5 and is retained locally outside the version-controlled tree.
