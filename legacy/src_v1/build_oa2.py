import builder as B, oa2_mcq, oa2_sql, oa2_py
doc = B.assemble(2, "OA 2 — Risk, Classification, and Experimentation",
  "Mock data-science internship assessment: logistic regression, trees and confusion matrices, hypothesis testing and A/B experiments, responsible AI, risk-alert SQL (Accounts / Transactions / AccountProfiles / RiskAlerts), transaction feature engineering in pandas, and string/hash-map and greedy-interval DSA.",
  B.build_mcqs("oa02", oa2_mcq.M), oa2_sql.build(), oa2_py.build_pandas(), oa2_py.build_dsa())
print(B.write(doc, 2))
