import builder as B, oa5_mcq, oa5_sql, oa5_py
doc = B.assemble(5, "OA 5 — Production ML and AI Decision Systems",
  "Mock data-science internship assessment: model drift, calibration, threshold optimisation, fairness, causal reasoning, multiple testing and AI evaluation; model-monitoring SQL (ModelRuns / Predictions / GroundTruthLabels / AlertActions); drift and metric pipelines in pandas; backtracking and shortest-path DSA.",
  B.build_mcqs("oa05", oa5_mcq.M), oa5_sql.build(), oa5_py.build_pandas(), oa5_py.build_dsa())
print(B.write(doc, 5))
