# Target Download Universe

I define the target download universe from monitoring tubes that:
- fall inside the Amsterdam study bbox `[4.55, 52.2, 5.15, 52.5]`;
- have at least one BRO GLD series in `brogmkenset.gpkg`;
- lie within 50 m of an exploded groundwater-use facility point, design well, or realised well from `bro_groundwater_use.gpkg`;
- and span the thesis overlap window (`first_date <= 2010-01-01`, `last_date >= 2020-01-01`).

Result: `113 tubes / 102 wells / 207 GLD files`.
