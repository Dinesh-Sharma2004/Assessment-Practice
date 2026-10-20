import builder as B, oa3_mcq, oa3_sql, oa3_py
doc = B.assemble(3, "OA 3 — NLP, Generative AI, and Anomaly Detection",
  "Mock data-science internship assessment: ensembles, imbalanced learning, embeddings, transformers, RAG and hallucinations; news-sentiment SQL (NewsArticles / Entities / SentimentScores / MarketEvents); text normalisation and entity linking in pandas; heap/top-K and BFS graph DSA.",
  B.build_mcqs("oa03", oa3_mcq.M), oa3_sql.build(), oa3_py.build_pandas(), oa3_py.build_dsa())
print(B.write(doc, 3))
