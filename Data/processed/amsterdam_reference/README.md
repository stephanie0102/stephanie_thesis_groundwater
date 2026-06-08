# Amsterdam Reference Artefacts

These files recover the earlier Amsterdam local/dense urban case from git commit `891d494` (`add error analysis`), the last pre-Netherlands commit in the current history.

They are reference artefacts only. They must not replace the active Netherlands pipeline under `Code/` or `Data/processed/methodology/`.

Recovered scope:

- target panel: Amsterdam local case, 102 wells in the protocol summary
- test windows: 2,034
- selected source filter: `maxsim0.60`
- retained source cells: 160 of 512
- best model in the recovered model comparison: Site-Hard Expert Selector, RMSE 2.045239
- fixed-transfer harmed subset in the recovered negative-transfer summary: 42 of 99 analysed wells

Some Amsterdam transfer-summary tables use smaller denominators than the protocol (`96` or `99`) because they require complete per-site transfer-effect joins. The protocol well count remains 102.
