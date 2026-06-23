"""Final Netherlands 5-seed stability check.

This is a supporting robustness check for the final Netherlands result. It reuses
the committed Methodology training pipeline (the same 496-well processed dataset
and the same model configuration as the final fixed-seed run) and retrains the
core model comparison under five seeds.

It does NOT touch or overwrite the main fixed-seed result files: every training
run is called with ``persist_artifacts=False`` (nothing is written to
``Data/processed/methodology/``). Only the two summary CSVs below are written, to
``Data/processed/results/final_checks/``:

    nl_seed_stability_per_seed.csv
    nl_seed_stability_summary.csv

Run:  python Code/final_checks/run_nl_seed_stability.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

# Seeds: the five used in the earlier stability design; includes the main seed 42.
SEEDS = [11, 23, 42, 67, 89]
METRIC_COLS = ["model_family", "rmse_test", "mae_test", "r2_test"]


def load_methodology_namespace() -> dict:
    """Execute the definition cells of Code/Methodology.ipynb to obtain the
    training classes, WITHOUT running the final orchestration cell."""
    nb = json.loads((ROOT / "Code" / "Methodology.ipynb").read_text())
    code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    g: dict = {"__name__": "__seed_stability__"}
    # The last code cell is the main()/results orchestration; skip it.
    for i, cell in enumerate(code_cells[:-1]):
        exec(compile("".join(cell["source"]), f"<methodology cell {i}>", "exec"), g)
    assert "LSTMTransferLearningImplementation" in g, "training class not found"
    return g


def main() -> int:
    t0 = time.time()
    print(f"ROOT: {ROOT}", flush=True)
    g = load_methodology_namespace()
    Impl = g["LSTMTransferLearningImplementation"]

    per_seed_frames = []
    for s in SEEDS:
        ts = time.time()
        print(f"[seed {s}] training core comparison ...", flush=True)
        impl = Impl(root=ROOT, sequence_length=9, seed=s)
        results = impl.run(
            run_rf=True,
            run_selective_tl=True,
            run_baseline=True,
            run_significance=False,
            run_seed_stability=False,
            run_rolling_temporal=False,
            run_selector_ablation=False,
            run_label_budget=False,
            persist_artifacts=False,   # never write to the main result files
            display_outputs=False,
        )
        core = results["publication_core_comparison"][METRIC_COLS].copy()
        core.insert(0, "seed", s)
        per_seed_frames.append(core)
        print(f"[seed {s}] done in {time.time() - ts:.1f}s", flush=True)

    per_seed = pd.concat(per_seed_frames, ignore_index=True)

    summary = (
        per_seed.groupby("model_family")
        .agg(
            n_seeds=("seed", "nunique"),
            mean_rmse=("rmse_test", "mean"),
            std_rmse=("rmse_test", "std"),
            mean_mae=("mae_test", "mean"),
            std_mae=("mae_test", "std"),
            mean_r2=("r2_test", "mean"),
            std_r2=("r2_test", "std"),
        )
        .reset_index()
        .sort_values("mean_rmse")
        .reset_index(drop=True)
    )

    out_dir = ROOT / "Data" / "processed" / "results" / "final_checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    per_seed.to_csv(out_dir / "nl_seed_stability_per_seed.csv", index=False)
    summary.to_csv(out_dir / "nl_seed_stability_summary.csv", index=False)

    print("\n=== per-seed ===", flush=True)
    print(per_seed.round(4).to_string(index=False), flush=True)
    print("\n=== summary (mean +/- std over seeds) ===", flush=True)
    print(summary.round(4).to_string(index=False), flush=True)
    print(f"\nTOTAL {time.time() - t0:.1f}s | seeds={SEEDS}", flush=True)
    print("WROTE:", out_dir / "nl_seed_stability_per_seed.csv", flush=True)
    print("WROTE:", out_dir / "nl_seed_stability_summary.csv", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
