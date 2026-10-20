from math import erf, sqrt
from builder import MCQ

def Phi(z): return 0.5 * (1 + erf(z / sqrt(2)))

# --- verification of numeric keys -------------------------------------------------
_p, _r = 30/50, 30/40
assert abs(2*_p*_r/(_p+_r) - 0.6667) < 1e-3
assert abs(0.02*0.9/(0.02*0.9+0.98*0.05) - 0.2687) < 1e-3
assert abs(Phi((-1.9-0.1)/1.5) - 0.0912) < 1e-3
assert (12 - 1.96*8/8, 12 + 1.96*8/8) == (10.04, 13.96)
assert (2*4+3, 4*9) == (11, 36)
assert 30/sqrt(100) == 3 and 30/sqrt(400) == 1.5
assert sum([100, 25]) == 125   # AAPL BUY rows

M = []
A = M.append
# ============================== ML (6) ==============================
A(MCQ("ML", ["overfitting", "bias-variance"], "easy",
 "A depth-unrestricted decision tree predicting next-day volume has a training RMSE of 0.4 and a validation RMSE of 3.9. Which action is the most appropriate first step?",
 "Constrain the model (e.g., limit tree depth or require a minimum leaf size) and re-check validation error",
 ["Add more tree depth so training error becomes exactly zero", "Report the training RMSE because it is the lower and therefore better estimate", "Remove the validation set so the model can use more data for training"],
 "A large train/validation gap signals high variance (overfitting). Restricting model capacity or adding regularization usually narrows the gap. Making the tree deeper would worsen it; training error is an optimistic estimate and must not be reported as performance."))
A(MCQ("ML", ["evaluation metrics", "classification"], "medium",
 "A fraud classifier scored 1,000 transactions and produced: TP = 30, FP = 20, FN = 10, TN = 940. What is its F1 score (to three decimals)?",
 "0.667",
 ["0.600", "0.750", "0.970"],
 "Precision = 30/(30+20) = 0.60 and recall = 30/(30+10) = 0.75, so F1 = 2·0.6·0.75/(0.6+0.75) = 0.667. 0.97 is accuracy ((30+940)/1000), which is dominated by the many true negatives; 0.60 and 0.75 are only the components."))
A(MCQ("ML", ["bias-variance", "model selection"], "medium",
 "For a k-nearest-neighbours classifier the team recorded: k=1 → train error 0%, 5-fold CV error 22%; k=15 → train 12%, CV 14%; k=200 → train 25%, CV 26%. Which interpretation is correct?",
 "k=1 overfits (high variance); k=200 underfits (high bias); k=15 gives the best bias-variance trade-off of the three",
 ["k=1 is best because its training error is lowest", "k=200 is best because its training and CV errors are nearly equal", "All three are equivalent because CV error is always higher than training error"],
 "Choose by validation/CV error, not training error. k=1 memorises noise (0% train, 22% CV). k=200 is too smooth so even training error is high (high bias). Similar train and CV error alone does not mean the model is good if both are high."))
A(MCQ("ML", ["data leakage", "feature engineering"], "medium",
 "You are building a model at market close to predict whether tomorrow's closing price will be higher than today's. One candidate feature is 'tomorrow's total traded volume'. What is the correct decision?",
 "Exclude it: it is not available at prediction time, so it leaks future information and will inflate offline metrics",
 ["Include it: more predictive features always improve the model", "Include it only in the training set and leave it out of the test set", "Include it but standardise it so the leakage has less effect"],
 "A feature must be computable at the moment of prediction. Tomorrow's volume is only known after the target period, so offline scores would be unrealistically good and the model would fail in production. Scaling or train-only inclusion does not fix leakage."))
A(MCQ("ML", ["regularization", "linear models"], "medium",
 "A linear regression has 200 correlated input features and the analyst wants an automatic feature subset where many coefficients are exactly zero. Which method is best suited?",
 "L1-regularised regression (Lasso)",
 ["L2-regularised regression (Ridge), which sets many coefficients exactly to zero", "Ordinary least squares with no penalty", "Increasing the learning rate of the optimiser"],
 "The L1 penalty has a corner at zero and tends to drive some coefficients exactly to zero, giving sparsity. Ridge shrinks coefficients toward zero but rarely makes them exactly zero. OLS has no shrinkage; the learning rate affects optimisation, not the penalty."))
A(MCQ("ML", ["decision trees", "preprocessing"], "easy",
 "Which model's predictions are least affected if every numeric feature is multiplied by a different positive constant (feature rescaling)?",
 "A decision tree, because splits depend only on the ordering of feature values",
 ["k-nearest neighbours, because distances are scale invariant", "Ridge regression, because the penalty is applied per example", "A support vector machine with an RBF kernel"],
 "Trees choose thresholds on single features, so positive rescaling only moves the thresholds. Distance-based models (kNN, RBF-SVM) change which points are near; penalised linear models change how much each coefficient is penalised."))
# ============================== STAT (5) ==============================
A(MCQ("STAT", ["bayes", "conditional probability"], "medium",
 "2% of trades are fraudulent. A detector flags 90% of fraudulent trades and also flags 5% of legitimate trades. A randomly chosen trade is flagged. What is the probability that it is fraudulent?",
 "About 26.9%",
 ["About 90%", "About 2%", "About 47%"],
 "P(F|flag) = 0.02·0.90 / (0.02·0.90 + 0.98·0.05) = 0.018/0.067 ≈ 0.269. The base rate is low, so most flags are false alarms even with a good detector; 90% is the recall P(flag|F), not the posterior."))
A(MCQ("STAT", ["normal distribution", "probability"], "medium",
 "Daily returns of a stock are modelled as Normal with mean 0.10% and standard deviation 1.50%. Approximately what is the probability that tomorrow's return is below −1.90%?",
 "About 9.1%",
 ["About 4.8%", "About 18.2%", "About 0.9%"],
 "z = (−1.90 − 0.10)/1.50 = −1.333, and Φ(−1.333) ≈ 0.091. Forgetting to subtract the mean (z = −1.27) or using the wrong tail gives other options; 18.2% would be a two-sided probability."))
A(MCQ("STAT", ["confidence intervals", "sampling"], "easy",
 "A random sample of n = 64 order latencies has mean 12.0 ms and sample standard deviation 8.0 ms. Using the normal approximation, what is an approximate 95% confidence interval for the true mean latency?",
 "(10.04, 13.96) ms",
 ["(4.16, 19.84) ms", "(11.00, 13.00) ms", "(8.08, 15.92) ms"],
 "SE = 8/√64 = 1, so the interval is 12 ± 1.96·1 = (10.04, 13.96). (4.16, 19.84) wrongly uses the standard deviation instead of the standard error; (8.08, 15.92) uses SE = 2 (n=16)."))
A(MCQ("STAT", ["expectation", "variance"], "easy",
 "A random variable X (daily P&L in thousands) has E[X] = 4 and Var(X) = 9. What are the mean and variance of Y = 2X + 3?",
 "E[Y] = 11 and Var(Y) = 36",
 ["E[Y] = 11 and Var(Y) = 39", "E[Y] = 8 and Var(Y) = 36", "E[Y] = 11 and Var(Y) = 18"],
 "E[2X+3] = 2·4 + 3 = 11. Adding a constant does not change variance and scaling by 2 multiplies variance by 2² = 4, so Var(Y) = 4·9 = 36."))
A(MCQ("STAT", ["central limit theorem", "sampling"], "medium",
 "Trade sizes are right-skewed with standard deviation 30 shares. The standard error of the sample mean is computed from samples of n = 100. If the desk instead samples n = 400 independent trades, what happens to the standard error?",
 "It falls from 3 to 1.5, i.e., it is halved",
 ["It falls from 3 to 0.75, i.e., it is quartered", "It stays at 3 because the population is skewed", "It falls from 30 to 7.5"],
 "SE = σ/√n: 30/10 = 3 for n = 100 and 30/20 = 1.5 for n = 400. Quadrupling n only halves SE. Skewness affects how fast the sampling distribution becomes normal, not the SE formula."))
# ============================== AI (4) ==============================
A(MCQ("AI", ["search", "A*"], "medium",
 "Which statement about A* search is correct?",
 "With an admissible heuristic (one that never overestimates the true remaining cost) A* returns a lowest-cost path",
 ["A* is optimal for any heuristic as long as it is non-negative", "A* always expands fewer nodes than breadth-first search regardless of the heuristic", "A* ignores the cost already paid and ranks nodes only by the heuristic"],
 "A* orders nodes by f = g + h. If h is admissible (and the graph search is handled consistently), the first goal popped is optimal. A non-negative but overestimating heuristic can mislead the search; ranking only by h is greedy best-first search, which is not optimal."))
A(MCQ("AI", ["supervised vs unsupervised", "clustering"], "easy",
 "A team has two years of unlabelled order-flow records and wants to discover groups of traders with similar behaviour. Which approach fits?",
 "Unsupervised learning, e.g., k-means or hierarchical clustering on behavioural features",
 ["Supervised classification with logistic regression, since logistic regression works on any dataset", "Supervised regression to predict trader IDs", "Reinforcement learning, since there is a reward in every trade"],
 "With no labels and an exploratory goal of finding structure, clustering is the natural tool. Logistic regression needs labelled targets; there is no sequential decision problem or reward signal specified for reinforcement learning."))
A(MCQ("AI", ["neural networks", "activation functions"], "medium",
 "A feed-forward network has three dense layers but every layer uses the identity (linear) activation. What is the effect on the function the network can represent?",
 "It is equivalent to a single linear transformation, so depth adds no representational power",
 ["It can approximate any continuous function because it has three layers", "It becomes equivalent to a decision tree of depth three", "It can represent XOR because depth increases capacity"],
 "Composition of linear maps is linear: W3(W2(W1x)) = (W3W2W1)x. Non-linear activations (ReLU, tanh, ...) are what let depth model non-linear patterns like XOR."))
A(MCQ("AI", ["game search", "minimax"], "medium",
 "In a two-player game search, alpha-beta pruning is applied to minimax. Which statement is true?",
 "It returns the same root value as plain minimax while potentially exploring fewer nodes",
 ["It returns an approximate value that can differ from minimax, trading accuracy for speed", "It increases the number of nodes explored but makes each cheaper", "It only works if every node has exactly two children"],
 "Alpha-beta only prunes branches that cannot influence the final decision, so the minimax value is unchanged; the savings depend on move ordering. It works for any branching factor."))
# ============================== SQL (2) ==============================
A(MCQ("SQL", ["NULL behaviour", "aggregation"], "easy",
 "Table P(price) contains the values 10, NULL, 20, NULL, 30. What does SELECT COUNT(*), COUNT(price), AVG(price) FROM P return?",
 "5, 3, 20",
 ["5, 5, 12", "3, 3, 20", "5, 3, 12"],
 "COUNT(*) counts rows (5); COUNT(price) ignores NULLs (3); AVG ignores NULLs, so (10+20+30)/3 = 20, not 60/5 = 12."))
A(MCQ("SQL", ["joins", "NULL behaviour"], "medium",
 "A query lists every security with its filled trades: SELECT s.ticker, t.trade_id FROM Securities s LEFT JOIN Trades t ON t.security_id = s.security_id WHERE t.status = 'FILLED'. Securities that have no trades at all are missing from the output. Why?",
 "The WHERE condition on the right-hand table is false (NULL) for the null-extended rows, so they are filtered out; the status test belongs in the ON clause",
 ["LEFT JOIN only returns rows that have a match in both tables", "Securities without trades violate a foreign-key constraint", "SQL removes NULL rows automatically after any join"],
 "The WHERE clause is evaluated after the join; for unmatched securities t.status is NULL, and NULL = 'FILLED' is not true, so those rows disappear and the LEFT JOIN behaves like an INNER JOIN. Moving the predicate into ON preserves them."))
# ============================== JAVA, OOP, TEST, EXCEL, FIN ==============================
A(MCQ("JAVA", ["strings", "equality"], "easy",
 "What does the following Java code print?\n\n```java\nString a = new String(\"AAPL\");\nString b = new String(\"AAPL\");\nSystem.out.println((a == b) + \" \" + a.equals(b));\n```",
 "false true",
 ["true true", "true false", "false false"],
 "`new String(...)` creates two distinct objects, so `==` (reference comparison) is false, while `equals` compares character content and is true."))
A(MCQ("OOP", ["polymorphism", "dynamic dispatch"], "medium",
 "Given the classes below, what does `new LimitOrder().label()` return?\n\n```java\nclass Order {\n  String tag() { return \"ORDER\"; }\n  String label() { return \"[\" + tag() + \"]\"; }\n}\nclass LimitOrder extends Order {\n  String tag() { return \"LIMIT\"; }\n}\n```",
 "[LIMIT]",
 ["[ORDER]", "LIMIT", "It does not compile because label() is not overridden"],
 "`label()` is inherited, but the call `tag()` inside it is dispatched at run time on the actual object (a LimitOrder), so the overridden version runs. This is run-time polymorphism."))
A(MCQ("TEST", ["boundary value analysis"], "easy",
 "An order-entry rule accepts quantities from 1 to 1,000 inclusive. Which set of test inputs best applies boundary value analysis?",
 "0, 1, 1000, 1001",
 ["1, 500, 1000", "−5000, 5000, 10000", "250, 500, 750"],
 "Defects cluster at the edges, so test just outside and exactly on each boundary: 0 and 1 for the lower edge, 1000 and 1001 for the upper edge. Mid-range values add little boundary coverage."))
A(MCQ("EXCEL", ["SUMIFS", "formulas"], "easy",
 "Rows 2–6 of a sheet hold Ticker (col A), Side (col B), Qty (col C): AAPL/BUY/100, AAPL/SELL/40, MSFT/BUY/70, AAPL/BUY/25, MSFT/SELL/10. What does =SUMIFS(C2:C6, A2:A6, \"AAPL\", B2:B6, \"BUY\") return?",
 "125",
 ["165", "100", "195"],
 "SUMIFS adds Qty only where all criteria hold: AAPL and BUY → rows 2 and 5, 100 + 25 = 125. 165 would include the AAPL SELL row; 195 also adds the MSFT BUY row (100+70+25)."))
A(MCQ("FIN", ["data quality", "outliers", "market data"], "medium",
 "A minute-by-minute price feed for a stock reads 100.2, 100.3, 1003.1, 100.4, 100.5. What is the best first action?",
 "Treat 1003.1 as a probable decimal-shift error: flag it, compare with bid/ask or another source, and correct or exclude it with a documented rule",
 ["Keep it, because extreme values are always real market information", "Replace every value in the series with the series mean", "Delete the whole day's data without investigation"],
 "A tenfold jump that reverts immediately is a classic bad-tick pattern. Flag and validate against independent data, then apply a documented fix. Blindly keeping, mean-imputing everything, or deleting the whole day are all unjustified."))
