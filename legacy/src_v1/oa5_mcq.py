from math import log
from builder import MCQ

assert abs(20 / 520 - 0.0385) < 1e-4
_psi = (0.7 - 0.5) * log(0.7 / 0.5) + (0.3 - 0.5) * log(0.3 / 0.5); assert 0.1 < _psi < 0.25 and abs(_psi - 0.1695) < 1e-3
def prec(prev, tpr=0.8, fpr=0.05): return prev * tpr / (prev * tpr + (1 - prev) * fpr)
assert abs(prec(0.10) - 0.64) < 1e-9 and abs(prec(0.05) - 0.4571) < 1e-3
assert abs(1 - 0.95 ** 20 - 0.6415) < 1e-3 and abs(0.05 / 20 - 0.0025) < 1e-12
# Simpson numbers
T = {"small": (81, 87), "large": (192, 263)}; C = {"small": (234, 270), "large": (55, 80)}
assert 81 / 87 > 234 / 270 and 192 / 263 > 55 / 80
assert (81 + 192) / 350 < (234 + 55) / 350 and 87 + 263 == 350 and 270 + 80 == 350
_p = [0.001, 0.008, 0.039, 0.041, 0.30]; _m = 5
_k = max(i + 1 for i, p in enumerate(_p) if p <= (i + 1) / _m * 0.05); assert _k == 2
assert abs(1 - 0.9 ** 5 - 0.40951) < 1e-5
_prec = 2 / 4; assert _prec == 0.5
assert 250 * 0.01 == 2.5

M = []; A = M.append
# ---------------- ML (6)
A(MCQ("ML", ["model drift", "covariate shift", "concept drift"], "medium",
 "A credit-scoring model's applicant income distribution has shifted upward since training, but, for any given income, the default rate is unchanged. Which kind of drift is this?",
 "Covariate shift (data drift): P(x) changed while P(y | x) stayed the same",
 ["Concept drift: P(y | x) changed while P(x) stayed the same", "Label shift only: nothing about the inputs changed", "No drift, because the default rate by income is unchanged"],
 "Covariate shift means the input distribution moves while the conditional relationship is stable. The model may still be fine there, but accuracy can degrade in regions with little training data, so monitoring and possibly retraining are needed. Concept drift would change the relationship itself."))
A(MCQ("ML", ["calibration", "probabilities"], "medium",
 "Among all applications for which a classifier outputs a probability of about 0.80, only 60% are actually positive. What does this show and what is a standard remedy?",
 "The model is over-confident (poorly calibrated); recalibrate with Platt scaling or isotonic regression on held-out data",
 ["The model is perfectly calibrated because 0.80 is close to 0.60", "The model is under-confident; multiply all scores by 1.2", "The model has high AUC, so calibration is guaranteed"],
 "Calibration means predicted probabilities match empirical frequencies. A 0.8 prediction that is right 60% of the time is over-confident. Platt scaling or isotonic regression fitted on validation data can map scores to calibrated probabilities. AUC measures ranking, not calibration."))
A(MCQ("ML", ["threshold optimisation", "cost-sensitive decisions"], "hard",
 "A missed fraud (false negative) costs 500 and a false alarm (false positive) costs 20; correct decisions cost nothing. With perfectly calibrated probabilities, at which predicted fraud probability should you start flagging a transaction to minimise expected cost?",
 "About 0.0385 (= 20 / (20 + 500))",
 ["0.50, the default threshold", "0.96 (= 500 / 520)", "0.25"],
 "Flag when p·500 > (1 − p)·20, i.e., p > 20/520 ≈ 0.0385. Costs, not the 0.5 default, determine the optimal threshold; 0.96 inverts the cost ratio."))
A(MCQ("ML", ["population stability index", "monitoring"], "medium",
 "A feature falls in two bins. In training 50% / 50% of cases are in bins 1 / 2; in live data 70% / 30%. Using PSI = Σ (live − train)·ln(live / train), and the common rule of thumb (< 0.1 stable, 0.1–0.25 moderate shift, > 0.25 major shift), which statement is right?",
 "PSI ≈ 0.17, a moderate shift that warrants investigation",
 ["PSI ≈ 0.02, no shift", "PSI ≈ 0.45, a major shift requiring immediate retraining", "PSI cannot be computed with only two bins"],
 "PSI = 0.2·ln(1.4) + (−0.2)·ln(0.6) = 0.0673 + 0.1022 ≈ 0.17, which lies between 0.1 and 0.25. It is a heuristic trigger for investigation, not an automatic retraining rule."))
A(MCQ("ML", ["monitoring", "label delay", "proxy metrics"], "medium",
 "Ground-truth labels for a lending model arrive 12 months after scoring. What is the best monitoring strategy in the meantime?",
 "Track input-feature drift, score/prediction distributions and data-quality metrics as early-warning proxies, and evaluate performance once labels mature",
 ["Do nothing until labels arrive", "Evaluate accuracy using the training labels", "Monitor only the model's inference latency"],
 "With delayed labels, performance cannot be measured directly. Proxy signals (feature and score drift, missing-value rates, approval rates) provide early warnings; delayed-label metrics then confirm."))
A(MCQ("ML", ["evaluation metrics", "base rate", "precision"], "hard",
 "A model has true-positive rate 0.80 and false-positive rate 0.05 and is deployed unchanged. When the fraud prevalence falls from 10% to 5%, what happens to precision?",
 "It falls from about 64% to about 46%, because false positives make up a larger share of the flags",
 ["It stays at 64%, because TPR and FPR are unchanged", "It rises, because there are fewer positives to find", "It falls to exactly 32%"],
 "Precision = prev·TPR / (prev·TPR + (1 − prev)·FPR). At 10%: 0.08/(0.08 + 0.045) = 0.64. At 5%: 0.04/(0.04 + 0.0475) ≈ 0.457. TPR and FPR are prevalence-independent but precision is not."))
# ---------------- STAT (5)
A(MCQ("STAT", ["multiple testing", "family-wise error"], "medium",
 "A team runs 20 independent A/B metric comparisons at α = 0.05, and in truth none of the metrics is affected. What is the approximate probability of at least one 'significant' result, and what is the Bonferroni per-test threshold?",
 "About 64%; Bonferroni threshold 0.05/20 = 0.0025",
 ["5%; Bonferroni threshold 0.05", "About 64%; Bonferroni threshold 0.05 × 20 = 1.0", "About 95%; Bonferroni threshold 0.0025"],
 "P(at least one false positive) = 1 − 0.95²⁰ ≈ 0.64. Bonferroni controls the family-wise error rate by testing each hypothesis at α/m = 0.0025."))
A(MCQ("STAT", ["Benjamini-Hochberg", "false discovery rate"], "hard",
 "Five sorted p-values are 0.001, 0.008, 0.039, 0.041, 0.30. With the Benjamini–Hochberg procedure at q = 0.05 (m = 5), how many hypotheses are rejected?",
 "2",
 ["4", "3", "1"],
 "BH compares the k-th smallest p-value with (k/m)·q = 0.01, 0.02, 0.03, 0.04, 0.05. The largest k with p(k) ≤ threshold is k = 2 (0.008 ≤ 0.02), while 0.039 > 0.03 and 0.041 > 0.04, so 2 hypotheses are rejected. Comparing raw p-values to 0.05 would wrongly reject 4."))
A(MCQ("STAT", ["causal reasoning", "Simpson's paradox", "confounding"], "hard",
 "A new model (treatment) and the old model (control) each handled 350 cases. Success rates: small accounts — treatment 81/87 (93%), control 234/270 (87%); large accounts — treatment 192/263 (73%), control 55/80 (69%). Overall, treatment is 273/350 (78%) and control 289/350 (83%). What explains this?",
 "Simpson's paradox: the treatment was assigned more large (harder) accounts; compare within segments (or adjust for account size) rather than using the pooled rates",
 ["The overall rates must be wrong, because a method cannot be better in every segment and worse overall", "The control is truly better because the overall rate is higher", "Small accounts should be dropped from the analysis"],
 "The treatment arm contains 263 large accounts versus 80 in control. Segment mix differs, so pooled rates mislead. Within each segment the treatment is better; randomisation or stratified/adjusted analysis addresses the confounding by account size."))
A(MCQ("STAT", ["A/B testing", "peeking", "Type I error"], "medium",
 "An analyst checks an A/B test's p-value every day and stops the experiment the first time p < 0.05. What is the problem?",
 "Repeated looks with early stopping inflate the overall Type I error rate above 5%; use a fixed horizon or a sequential-testing/alpha-spending method",
 ["There is no problem because each individual p-value is valid at 5%", "The procedure lowers the Type I error rate below 5%", "It affects only Type II error"],
 "Each additional look gives another chance for a false positive, so the chance that some look crosses 0.05 under H0 is much larger than 5%. Sequential designs adjust thresholds for repeated looks."))
A(MCQ("STAT", ["binomial distribution", "probability"], "easy",
 "A monitoring rule fires a false alarm with probability 0.10 each day, independently. What is the probability of at least one false alarm in 5 days?",
 "About 41% (1 − 0.9⁵)",
 ["50% (5 × 0.10)", "About 59% (0.9⁵)", "About 10%"],
 "P(no alarm in 5 days) = 0.9⁵ ≈ 0.59, so P(at least one) ≈ 0.41. Adding probabilities (5 × 0.1) ignores overlap and overstates the result."))
# ---------------- AI (4)
A(MCQ("AI", ["evaluation", "data contamination", "benchmarks"], "medium",
 "A language model scores extremely well on a public benchmark, but the benchmark's questions appear verbatim in its web-scraped training data. What is the main concern?",
 "Data contamination: the score may reflect memorisation, so it overstates generalisation; use held-out or freshly written evaluation items",
 ["The benchmark is too easy for all models, so nothing can be learned", "Contamination makes scores underestimate the model", "Nothing: more training data always makes benchmark results more trustworthy"],
 "If test items leaked into training data, high scores can come from memorisation. Evaluation should use unseen data or contamination checks."))
A(MCQ("AI", ["fairness", "impossibility", "calibration"], "hard",
 "When two groups have different base rates of the outcome, which statement about fairness criteria is generally true?",
 "A non-perfect classifier cannot simultaneously satisfy calibration within groups and equal false-positive and false-negative rates across groups, so trade-offs must be chosen explicitly",
 ["All fairness criteria can always be satisfied simultaneously by tuning thresholds", "Equal accuracy across groups implies all other fairness criteria", "Fairness criteria only apply when the base rates are identical"],
 "Known impossibility results (e.g., Kleinberg et al.; Chouldechova) show that with unequal base rates, calibration and equalised error rates conflict unless the classifier is perfect. Practitioners must pick criteria suited to the context and document the trade-off."))
A(MCQ("AI", ["multi-armed bandits", "exploration"], "easy",
 "In an ε-greedy bandit used to choose which alert-ranking model to show analysts, what does ε = 0.1 mean?",
 "With probability 0.1 a random model is tried (exploration); otherwise the model with the best estimated reward is used (exploitation)",
 ["The best model is chosen 10% of the time and a random one 90%", "The reward is multiplied by 0.1", "The algorithm stops after 10 trials"],
 "ε-greedy balances exploration and exploitation: exploit the best-known arm most of the time and explore a random arm with probability ε."))
A(MCQ("AI", ["responsible AI", "documentation", "governance"], "easy",
 "What is the main purpose of a model card for a production ML model?",
 "To document intended use, training/evaluation data, performance across groups, limitations and known risks so users can judge appropriate use",
 ["To store the model's weights and source code", "To guarantee the model is unbiased", "To replace validation and monitoring"],
 "Model cards support transparency and accountability by summarising context, metrics and limitations. They do not guarantee fairness and do not replace testing or monitoring."))
# ---------------- SQL (2)
A(MCQ("SQL", ["NULL behaviour", "NOT IN"], "hard",
 "Table Predictions has run_id values 1, 2, 3. A subquery SELECT run_id FROM ArchivedRuns returns the values 1 and NULL. What does SELECT run_id FROM Predictions WHERE run_id NOT IN (SELECT run_id FROM ArchivedRuns) return?",
 "No rows, because NOT IN with a NULL in the list never evaluates to true",
 ["Rows 2 and 3", "Rows 1, 2 and 3", "An error, because NULL is not allowed in a subquery"],
 "x NOT IN (1, NULL) expands to x <> 1 AND x <> NULL; the second term is UNKNOWN, so the whole condition is never TRUE. Use NOT EXISTS, or filter NULLs out of the subquery."))
A(MCQ("SQL", ["transactions", "isolation", "lost update"], "medium",
 "Two analysts load the same alert row, each changes a different column in their application, and each saves the whole row back. The second save overwrites the first change. Which classic problem is this and what is a typical remedy?",
 "A lost update; use transactions with row locking (SELECT ... FOR UPDATE) or optimistic concurrency with a version column, and update only the changed columns",
 ["A phantom read; add an index", "A dirty read; avoid COMMIT", "A deadlock; restart the database"],
 "When concurrent writers overwrite each other's changes based on stale reads, an update is lost. Locking, higher isolation levels, optimistic version checks and column-specific UPDATE statements prevent it."))
# ---------------- JAVA, OOP, TEST, EXCEL, FIN
A(MCQ("JAVA", ["references", "arrays"], "easy",
 "What does this code print?\n\n```java\nint[] a = {1, 2, 3};\nint[] b = a;\nb[0] = 9;\nSystem.out.println(a[0]);\n```",
 "9",
 ["1", "0", "It does not compile"],
 "Arrays are objects; `b = a` copies the reference, so both variables point to the same array and the change through `b` is visible via `a`."))
A(MCQ("OOP", ["interfaces", "abstraction"], "medium",
 "Why is it generally good practice to declare a variable as `List<Prediction> results = new ArrayList<>();` rather than `ArrayList<Prediction> results = new ArrayList<>();`?",
 "Programming to the interface lets you swap the implementation (e.g., LinkedList or an immutable list) without changing the code that uses `results`",
 ["List is always faster than ArrayList", "ArrayList cannot be used with generics", "It prevents the list from ever being modified"],
 "Depending on an abstraction (interface) reduces coupling: callers use only the List contract, so implementations can change freely. It has no direct effect on speed or mutability."))
A(MCQ("TEST", ["ML testing", "invariance tests", "behavioural testing"], "medium",
 "A sentiment model should not change its prediction when a company name in the text is replaced by another company name. Which kind of test checks this?",
 "An invariance (perturbation) test: apply a label-preserving change and assert the prediction does not change",
 ["A boundary test of the learning rate", "A load test of the server", "A test that predictions are exactly equal to the training labels"],
 "Behavioural ML testing includes invariance tests (label-preserving perturbations), directional-expectation tests and minimum-functionality tests, which reveal brittle or biased behaviour that aggregate accuracy hides."))
A(MCQ("EXCEL", ["COUNTIFS", "precision"], "medium",
 "Column B holds actual labels 1,0,1,1,0,0 and column C holds predicted labels 1,1,0,1,0,1 in rows 2–7. What does =COUNTIFS(B2:B7,1,C2:C7,1)/COUNTIF(C2:C7,1) return?",
 "0.5 (precision)",
 ["0.667 (recall)", "0.333", "2"],
 "COUNTIFS counts rows where actual = 1 and predicted = 1 (true positives = 2). COUNTIF(C,1) counts predicted positives (4). 2/4 = 0.5 is precision; recall would divide by the 3 actual positives."))
A(MCQ("FIN", ["VaR", "backtesting", "model risk"], "hard",
 "A bank's 99% one-day Value-at-Risk model is backtested over 250 trading days and the loss exceeds VaR on 10 days. What is the most reasonable interpretation?",
 "About 2.5 breaches would be expected; 10 is far more, which suggests the model underestimates risk and needs review or recalibration",
 ["10 breaches is fewer than expected, so the model is conservative", "Breach counts are irrelevant to VaR models", "The result proves the market was unusually calm"],
 "A 99% VaR should be exceeded about 1% of days: 250 × 0.01 = 2.5. Observing 10 breaches suggests understated risk (e.g., fat tails, volatility clustering, stale data), triggering model validation."))
