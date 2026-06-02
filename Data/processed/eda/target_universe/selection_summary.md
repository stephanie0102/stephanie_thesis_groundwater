# Target Download Universe

I define the target download universe from monitoring tubes that:
- fall inside the study bounding box `[3.2, 50.7, 7.3, 53.6]`;
- have at least one BRO GLD series in `brogmkenset.gpkg`;
- lie within 50 m of an exploded groundwater-use facility point, design well, or realised well from `bro_groundwater_use.gpkg`;
- and span the thesis overlap window (`first_date <= 2010-01-01`, `last_date >= 2020-01-01`).

Result: `17867 tubes / 11686 wells / 27269 GLD files`.
