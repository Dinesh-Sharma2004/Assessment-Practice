import builder as B, oa4_mcq, oa4_sql, oa4_py
doc = B.assemble(4, "OA 4 — Time Series and Quantitative Analytics",
  "Mock data-science internship assessment: time-series validation and forecast errors, PCA and clustering, bootstrap, ANOVA, regression diagnostics, neural-network basics; price/benchmark SQL (Securities / DailyPrices / SectorMap / Benchmarks); resampling and rolling analytics in pandas; dynamic-programming and binary-search DSA.",
  B.build_mcqs("oa04", oa4_mcq.M), oa4_sql.build(), oa4_py.build_pandas(), oa4_py.build_dsa())
print(B.write(doc, 4))
