"""Production-consistent selector ablation for the final Netherlands pipeline.

This reuses the EXACT production implementation from Code/Methodology.ipynb
(LSTMTransferLearningImplementation): the same data preparation, the same
validation-selected source filter (maxsim0.40), the same chronological
train/validation/calibration/test split, the same parent models, and the same
calibration-trained gate routine (`_fit_selector_payload`). Only the selector's
input feature groups are ablated.

Protocol roles (unchanged from production):
  train       -> parent (No-TL / Always-TL) training
  validation  -> source-filter threshold selection (maxsim0.40, already selected)
  calibration -> selector (gate) training            [self.selector_split == 'cal']
  test        -> final reporting only

Parent models are retrained ONCE (seed 42) to recover val/cal/test parent
predictions, which are then persisted so this ablation is reproducible. The main
production result tables (summary_wide.csv, publication_core_comparison.csv,
site_transfer_effects.csv, selector_by_site.csv, test_error_detail.csv, ...) are
NOT written by this script.

The gate (selector) is then retrained for each feature-group variant on the
calibration split and evaluated on the test split. Multiple GATE seeds are run
on the single set of parents; this measures selector-training stability given
fixed production parents, NOT parent-training stability.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_MAX_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
import ast
import json
import time
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# Resolve the repository root relative to this file so the script is portable:
# Code/selector_robustness/run_selector_ablation_production.py -> repo root is two levels up.
REPO = Path(__file__).resolve().parents[2]
NB = REPO / "Code" / "Methodology.ipynb"
ROBUST = REPO / "Data/processed/methodology/tables/robustness"
FIGDIR = REPO / "Data/processed/results/figures"

PARENT_SEED = 42
GATE_SEEDS = [11, 23, 42]

# ---------------------------------------------------------------------------
# Load the production implementation classes from the notebook WITHOUT running
# any demo / driver code. Keep definitions, imports and environment setup;
# drop bare display()/print()/demo expression statements.
# ---------------------------------------------------------------------------
DEF_CELLS = [2, 5, 7, 9, 12, 14, 16, 18, 20, 22, 25, 27, 29, 31]
SETUP_PREFIXES = ("os.environ", "warnings.filterwarnings", "set_global_seed",
                  "torch.set_num", "torch.manual_seed", "np.random.seed",
                  "random.seed", "sns.set_theme", "matplotlib.use", "pd.set_option")


def _sanitize(cell_src: str) -> str:
    tree = ast.parse(cell_src)
    keep = []
    for node in tree.body:
        if isinstance(node, ast.Expr):
            try:
                txt = ast.unparse(node.value)
            except Exception:
                txt = ""
            if txt.startswith(SETUP_PREFIXES):
                keep.append(node)
            # else: drop demo/display/print expression
        else:
            keep.append(node)
    tree.body = keep
    return ast.unparse(tree)


def load_pipeline():
    nb = json.load(open(NB))
    ns: dict = {"__name__": "_production_pipeline"}
    os.chdir(REPO)  # so the notebook's find_project_root() resolves correctly
    for idx in DEF_CELLS:
        src = "".join(nb["cells"][idx]["source"])
        exec(compile(_sanitize(src), f"<cell {idx}>", "exec"), ns)
    return ns


def main():
    t0 = time.time()
    ns = load_pipeline()
    Impl = ns["LSTMTransferLearningImplementation"]
    ROOT = ns["ROOT"]
    print(f"[{time.time()-t0:6.1f}s] pipeline classes loaded; ROOT={ROOT}")

    impl = Impl(root=ROOT, seed=PARENT_SEED)
    assert impl.transfer_config["source_mode"] == "maxsim0.40", impl.transfer_config["source_mode"]
    assert impl.selector_split == "cal"

    impl.load_data()
    impl.prepare_datasets()
    print(f"[{time.time()-t0:6.1f}s] data prepared; source filter = "
          f"{impl.transfer_config['source_mode']}, selector_split = {impl.selector_split}")

    # ---- Train parents ONCE (seed 42) --------------------------------------
    parents = impl.run_parent_models()
    impl.results["parent_payloads"] = parents
    NO, AL = impl.NO_TL_NAME, impl.ALWAYS_TL_NAME
    print(f"[{time.time()-t0:6.1f}s] parents trained (seed {PARENT_SEED}): {NO} | {AL}")

    # ---- Persist parent predictions for val / cal / test -------------------
    for split in ["val", "cal", "test"]:
        meta = parents[NO][f"{split}_meta"][["site_id", "target_month"]].reset_index(drop=True).copy()
        meta["split"] = split
        meta["y_true"] = np.asarray(parents[NO][f"{split}_true"]).flatten()
        meta["pred_no_tl"] = np.asarray(parents[NO][f"{split}_pred"]).flatten()
        meta["pred_always_tl"] = np.asarray(parents[AL][f"{split}_pred"]).flatten()
        out = ROBUST / f"selector_ablation_parent_predictions_{split}.csv"
        meta.to_csv(out, index=False)
        print(f"[{time.time()-t0:6.1f}s] wrote {out.name}  ({len(meta)} rows)")

    # ---- Fixed parent per-site test RMSE -> fixed-transfer harmed wells -----
    no_site = impl._site_level_rmse(parents[NO]["test_true"], parents[NO]["test_pred"],
                                    parents[NO]["test_meta"], "rmse_no_tl")
    al_site = impl._site_level_rmse(parents[AL]["test_true"], parents[AL]["test_pred"],
                                    parents[AL]["test_meta"], "rmse_always_tl")
    parent_site = no_site.merge(al_site, on="site_id")
    harmed_ids = parent_site.loc[parent_site["rmse_always_tl"] > parent_site["rmse_no_tl"], "site_id"]
    harmed = parent_site[parent_site["site_id"].isin(harmed_ids)].copy()
    print(f"[{time.time()-t0:6.1f}s] fixed-transfer harmed wells: {len(harmed)} / {len(parent_site)}")

    # ---- Feature-group variants (built from production feature groups) -----
    groups = impl._selector_feature_groups()
    main_cols = list(impl._selector_feature_specs()[impl.SELECTOR_MAIN_KEY]["feature_cols"])
    sim_g = set(groups["similarity"])
    site_g = set(groups["site"])
    win_g = set(groups["window_state"])
    cal_g = set(groups["calendar"])
    season_g = cal_g | {"shared_last_month_sin", "shared_last_month_cos"}
    pump_g = {"pumping_log_mean", "pumping_log_std", "context_last_pumping_m3_month_log1p"}

    def drop(cols, rm):
        return [c for c in cols if c not in rm]

    variants = {
        "full_selector": main_cols,
        "no_similarity": drop(main_cols, sim_g),
        "no_recent_target_state": drop(main_cols, win_g),
        "no_seasonality": drop(main_cols, season_g),
        "no_site_history": drop(main_cols, site_g),
        "no_pumping_anthropogenic": drop(main_cols, pump_g & set(main_cols)),
    }
    for k, v in variants.items():
        print(f"    variant {k:26s} n_features={len(v)}")

    # ---- Shared gate frames (independent of gate seed) ---------------------
    selector_static = (
        impl.results["best_match_lookup"][["site_id", "cell_id", "cosine_similarity", "months_used"]]
        .drop_duplicates("site_id")
        .merge(impl.build_selector_features(), on="site_id", how="left")
    )
    cal_frame = impl._build_gate_split_frame("cal", selector_static)
    val_frame = impl._build_gate_split_frame("val", selector_static)
    test_frame = impl._build_gate_split_frame("test", selector_static)

    def rescue_rates(payload):
        var_site = impl._site_level_rmse(payload["test_true"], payload["test_pred"],
                                         payload["test_meta"], "rmse_var")
        h = harmed.merge(var_site, on="site_id", how="left")
        partial = float((h["rmse_var"] < h["rmse_always_tl"]).mean())
        full = float((h["rmse_var"] < h["rmse_no_tl"]).mean())
        return partial, full

    # ---- Run variants x gate seeds (production gate, cal-trained) -----------
    rows = []
    for seed in GATE_SEEDS:
        impl.seed = int(seed)
        for name, cols in variants.items():
            payload = impl._fit_selector_payload(
                selector_static=selector_static,
                val_frame=val_frame, cal_frame=cal_frame, test_frame=test_frame,
                feature_cols=cols, model_label=f"{name} (seed {seed})",
                compute_feature_importance=False,
            )
            tm = next(r for r in payload["metrics"] if str(r["model"]).endswith("(test)"))
            partial, full = rescue_rates(payload)
            rows.append(dict(variant=name, seed=int(seed), n_features=len(cols),
                             selector_model=str(payload.get("best_candidate", "?")),
                             rmse=tm["rmse"], mae=tm["mae"], r2=tm["r2"],
                             partial_rescue_rate_harmed=partial, full_rescue_rate_harmed=full))
            print(f"[{time.time()-t0:6.1f}s] seed={seed} {name:26s} "
                  f"rmse={tm['rmse']:.4f} mae={tm['mae']:.4f} r2={tm['r2']:.4f} "
                  f"partial={partial:.3f} full={full:.3f} ({payload.get('best_candidate')})")

    by_seed = pd.DataFrame(rows)
    by_seed.to_csv(ROBUST / "selector_ablation_production_by_seed.csv", index=False)

    # ---- Aggregate summary (mean +/- std over gate seeds) ------------------
    agg = by_seed.groupby("variant").agg(
        n_features=("n_features", "first"),
        rmse_mean=("rmse", "mean"), rmse_std=("rmse", "std"),
        mae_mean=("mae", "mean"), mae_std=("mae", "std"),
        r2_mean=("r2", "mean"), r2_std=("r2", "std"),
        partial_rescue_rate_harmed_mean=("partial_rescue_rate_harmed", "mean"),
        full_rescue_rate_harmed_mean=("full_rescue_rate_harmed", "mean"),
    ).reset_index()
    full_rmse = float(agg.loc[agg["variant"] == "full_selector", "rmse_mean"].iloc[0])
    full_mae = float(agg.loc[agg["variant"] == "full_selector", "mae_mean"].iloc[0])
    agg["delta_rmse_vs_full"] = agg["rmse_mean"] - full_rmse
    agg["delta_mae_vs_full"] = agg["mae_mean"] - full_mae
    agg["n_gate_seeds"] = len(GATE_SEEDS)
    agg["parent_seed"] = PARENT_SEED
    agg["n_harmed_wells"] = len(harmed)
    agg["evidence_type"] = "production_consistent_parents_retrained_gate_cal_trained"
    agg = agg.sort_values("rmse_mean").reset_index(drop=True)
    agg.to_csv(ROBUST / "selector_ablation_production_summary.csv", index=False)

    # ---- Figure ------------------------------------------------------------
    order = agg.sort_values("rmse_mean")["variant"].tolist()
    plot = agg.set_index("variant").loc[order]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    ax = axes[0]
    colors = ["#2a9d8f" if v == "full_selector" else "#8ab0ab" for v in order]
    ax.barh(order, plot["rmse_mean"], xerr=plot["rmse_std"], color=colors)
    ax.axvline(full_rmse, ls="--", color="#e76f51", lw=1.5, label="full selector")
    ax.set_xlabel("Test RMSE (cal-trained gate, production parents)")
    ax.set_title("Production selector ablation - test RMSE")
    ax.legend(frameon=False, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(plot["rmse_mean"].min() - 0.003, plot["rmse_mean"].max() + 0.006)
    ax = axes[1]
    x = np.arange(len(order)); w = 0.38
    ax.bar(x - w/2, plot["partial_rescue_rate_harmed_mean"], w, label="partial rescue", color="#2a9d8f")
    ax.bar(x + w/2, plot["full_rescue_rate_harmed_mean"], w, label="full rescue", color="#e76f51")
    ax.set_xticks(x); ax.set_xticklabels(order, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel(f"Rate on {len(harmed)} fixed-transfer harmed wells")
    ax.set_title("Rescue rates by selector variant")
    ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Production-consistent selector input ablation (final Netherlands, maxsim0.40)",
                 y=1.02, fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGDIR / "results_selector_ablation_production.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    print("\n=== PRODUCTION SELECTOR ABLATION SUMMARY (mean over gate seeds) ===")
    print(agg[["variant", "n_features", "rmse_mean", "mae_mean", "r2_mean",
               "partial_rescue_rate_harmed_mean", "full_rescue_rate_harmed_mean",
               "delta_rmse_vs_full"]].to_string(index=False))
    print(f"\nfull_selector test RMSE = {full_rmse:.4f}  (production CASL reference = 2.0925)")
    print(f"total runtime: {time.time()-t0:.1f}s")
    print("Saved:")
    for f in ["selector_ablation_production_summary.csv", "selector_ablation_production_by_seed.csv",
              "selector_ablation_parent_predictions_val.csv",
              "selector_ablation_parent_predictions_cal.csv",
              "selector_ablation_parent_predictions_test.csv"]:
        print("  ", ROBUST / f)
    print("  ", FIGDIR / "results_selector_ablation_production.png")


if __name__ == "__main__":
    main()
