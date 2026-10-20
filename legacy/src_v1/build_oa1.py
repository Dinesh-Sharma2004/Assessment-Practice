import builder as B, oa1_mcq, oa1_sql, oa1_py
doc = B.assemble(1, "OA 1 — Market Data and ML Foundations",
  "Mock data-science internship assessment: ML foundations, probability and inference, AI search, market-data SQL (Securities / MarketQuotes / Trades), tick cleaning in pandas, and array/two-pointer and sliding-window DSA.",
  B.build_mcqs("oa01", oa1_mcq.M), oa1_sql.build(), oa1_py.build_pandas(), oa1_py.build_dsa())
print(B.write(doc, 1))
