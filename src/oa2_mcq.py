from math import exp, sqrt, erf
from builder import MCQ

def Phi(z): return 0.5 * (1 + erf(z / sqrt(2)))
assert abs(exp(0.69) - 2.0) < 0.01
g = lambda p, n: 1 - (p / n) ** 2 - ((n - p) / n) ** 2
assert abs(g(40, 50) - 0.32) < 1e-9 and abs(g(30, 50) - 0.48) < 1e-9
assert round(((1.96 + 0.84) * 10 / 2) ** 2) == 196
p1, p2, n = 200 / 2000, 240 / 2000, 2000
pp = (200 + 240) / 4000
z = (p2 - p1) / sqrt(pp * (1 - pp) * (2 / n)); assert abs(z - 2.02) < 0.01 and 2 * (1 - Phi(z)) < 0.05
assert abs(0.15 - 0.3 * 0.5) < 1e-12
assert 7 / 2 == 3.5 and int(7 / 2) == 3

M = []; A = M.append
# ---------------- ML (6)
A(MCQ("ML", ["logistic regression", "interpretation"], "medium",
 "A logistic regression for card fraud has a coefficient of +0.69 on the feature 'number of foreign transactions in the last 24 h' (all other features held fixed). How is this coefficient best interpreted?",
 "Each additional foreign transaction multiplies the odds of fraud by about 2 (e^0.69 ≈ 2)",
 ["Each additional foreign transaction raises the probability of fraud by 0.69", "Each additional foreign transaction multiplies the probability of fraud by about 2", "The feature explains 69% of the variance in fraud"],
 "Logistic regression is linear in the log-odds, so a coefficient β multiplies the odds by e^β per unit increase. The effect on probability is not constant (it depends on the baseline), and the coefficient is not a variance-explained measure."))
A(MCQ("ML", ["decision trees", "Gini impurity"], "medium",
 "A node has 50 fraud and 50 legitimate samples (Gini = 0.5). Split A sends 40 fraud + 10 legit left and 10 fraud + 40 legit right. Split B sends 30 fraud + 20 legit left and 20 fraud + 30 legit right. Which split does a Gini-based tree prefer?",
 "Split A, with weighted child Gini 0.32 versus 0.48 for split B",
 ["Split B, because its children are larger and therefore more stable", "Split B, with weighted child Gini 0.32", "Neither: both give the same impurity as the parent"],
 "Gini of a child = 1 − Σp². Split A children: 1 − (0.8² + 0.2²) = 0.32 each → weighted 0.32. Split B: 1 − (0.6² + 0.4²) = 0.48. The lower weighted impurity (larger impurity decrease) wins."))
A(MCQ("ML", ["confusion matrix", "threshold"], "easy",
 "A fraud model outputs probabilities. The risk team says missing a real fraud case is far more costly than reviewing a legitimate one. What should happen to the classification threshold, and what is the typical consequence?",
 "Lower the threshold: recall rises and precision usually falls",
 ["Raise the threshold: recall rises and precision usually falls", "Lower the threshold: precision rises and recall usually falls", "Keep 0.5, since the threshold has no effect on recall"],
 "Flagging more cases (lower cut-off) catches more true frauds (higher recall) at the cost of more false positives (lower precision). Raising the threshold does the opposite."))
A(MCQ("ML", ["ROC AUC", "evaluation metrics"], "medium",
 "A classifier has ROC AUC = 0.82 on a held-out set. Which statement is correct?",
 "If you pick one random positive and one random negative case, the model scores the positive higher about 82% of the time",
 ["82% of all predictions are correct at every threshold", "The model has a precision of 0.82 at the 0.5 threshold", "The model is guaranteed to be calibrated"],
 "AUC is the probability that a random positive is ranked above a random negative. It is threshold-independent, says nothing about precision at a specific cut-off, and does not imply calibrated probabilities."))
A(MCQ("ML", ["model selection", "cross-validation", "data leakage"], "medium",
 "A team tries 200 hyper-parameter settings, picks the one with the best score on the test set, and reports that score as the expected production performance. What is wrong?",
 "The test set was used for model selection, so the reported score is optimistically biased; tune on a validation set or with CV and keep the test set untouched",
 ["Nothing; more tuning always yields an unbiased estimate", "The model must be retrained on the test set to be fair", "Hyper-parameters should never be tuned"],
 "Selecting the best of many candidates on the same data exploits chance fluctuations. A final untouched test set (or nested CV) is needed for an unbiased estimate."))
A(MCQ("ML", ["logistic regression", "regularization"], "hard",
 "A logistic regression without regularization is fitted to training data in which one feature perfectly separates the two classes. What typically happens?",
 "The maximum-likelihood coefficient grows without bound (the optimiser does not converge to a finite solution); a regularization penalty keeps it finite",
 ["The coefficient converges to exactly 1", "The model automatically drops that feature", "The loss becomes negative"],
 "With perfect separation the likelihood keeps improving as the weight grows, so no finite maximiser exists. L2 (or L1) regularization adds a penalty that yields finite coefficients."))
# ---------------- STAT (5)
A(MCQ("STAT", ["p-value", "hypothesis testing"], "medium",
 "In a test of whether a new fraud rule changes the alert rate, you obtain p = 0.03. Which interpretation is correct?",
 "If the rule truly had no effect, results at least as extreme as those observed would occur about 3% of the time",
 ["There is a 3% probability that the null hypothesis is true", "There is a 97% probability that the rule works", "The effect size is 3%"],
 "A p-value is computed assuming H0 is true: P(data this extreme | H0). It is not the probability that H0 is true or that the alternative holds, and it says nothing about effect magnitude."))
A(MCQ("STAT", ["Type I error", "Type II error", "power"], "medium",
 "With the sample size fixed, an analyst reduces the significance level from α = 0.05 to α = 0.01. What is the usual effect?",
 "Type I error rate decreases and Type II error rate increases (power decreases)",
 ["Both Type I and Type II error rates decrease", "Type I error increases and power increases", "Neither changes unless the sample size changes"],
 "A stricter α demands stronger evidence to reject H0: fewer false positives but more missed true effects (lower power) for a given n and effect size."))
A(MCQ("STAT", ["power", "sample size"], "hard",
 "To detect a true mean shift of 2 units with a one-sample two-sided z-test (σ = 10, α = 0.05, desired power 80%, z-values 1.96 and 0.84), what sample size is needed?",
 "196",
 ["49", "98", "784"],
 "n = ((z_{α/2} + z_β)·σ/δ)² = ((1.96 + 0.84)·10/2)² = 14² = 196. 784 would result from using δ = 1; 49 from forgetting to square the (σ/δ) ratio correctly."))
A(MCQ("STAT", ["A/B testing", "two-proportion z-test"], "medium",
 "In an A/B test, control converted 200 of 2,000 users (10%) and treatment 240 of 2,000 (12%). Using a pooled two-proportion z-test, what is the z statistic (approximately) and the conclusion at α = 0.05 (two-sided)?",
 "z ≈ 2.02, so the difference is statistically significant",
 ["z ≈ 2.02, so the difference is not significant because the critical value is 2.58", "z ≈ 0.02, so the difference is not significant", "z ≈ 4.0, so the difference is significant"],
 "Pooled p = 440/4000 = 0.11; SE = √(0.11·0.89·(1/2000 + 1/2000)) ≈ 0.00989; z = 0.02/0.00989 ≈ 2.02 > 1.96, p ≈ 0.043. The 2.58 critical value corresponds to α = 0.01."))
A(MCQ("STAT", ["independence", "conditional probability"], "easy",
 "For two events: P(Flagged) = 0.30, P(High-value) = 0.50 and P(Flagged and High-value) = 0.15. Which statement is correct?",
 "They are independent, because P(A∩B) = P(A)·P(B) = 0.15",
 ["They are mutually exclusive, because 0.15 is small", "They are dependent, because P(A∩B) is not zero", "They are independent because P(A) + P(B) < 1"],
 "Independence means P(A∩B) = P(A)P(B); here 0.3 × 0.5 = 0.15. Mutually exclusive events would have P(A∩B) = 0 (and are then dependent, unless one has probability 0)."))
# ---------------- AI (4)
A(MCQ("AI", ["fairness", "responsible AI"], "medium",
 "A loan model approves 60% of applicants from group X and 40% from group Y, but among truly creditworthy applicants both groups are approved at the same rate (equal true positive rate). Which statement is accurate?",
 "Equal opportunity (equal TPR) holds, but demographic parity (equal approval rates) does not",
 ["Both demographic parity and equal opportunity hold", "Neither fairness criterion holds", "Demographic parity holds because the TPRs match"],
 "Demographic parity compares overall positive-decision rates (60% vs 40% → violated). Equal opportunity compares TPR among truly positive individuals (equal → satisfied). Different fairness criteria can disagree, so the choice must be justified for the use case."))
A(MCQ("AI", ["fairness", "proxy variables"], "medium",
 "A team removes the protected attribute 'gender' from a credit model's inputs and claims the model is now unbiased. Why is that claim weak?",
 "Other features (e.g., occupation or purchase categories) can act as proxies for gender, so disparities can persist; fairness must be measured on outcomes",
 ["Removing a feature can never change a model's predictions", "Protected attributes are always the most predictive features, so removal is impossible", "Fairness only matters for neural networks"],
 "'Fairness through unawareness' fails when other variables are correlated with the protected attribute. Auditing outcomes (e.g., approval and error rates by group) is required."))
A(MCQ("AI", ["explainability", "interpretability"], "medium",
 "A customer disputes why their individual transaction was blocked. Which kind of explanation best serves this request?",
 "A local, per-prediction explanation (e.g., SHAP values or a counterfactual: \"approved if amount were below X\")",
 ["A global feature-importance bar chart averaged over all customers", "The model's overall accuracy on the test set", "The list of all hyper-parameters"],
 "The question concerns one decision, so a local explanation that attributes that single prediction (or offers a counterfactual) is appropriate. Global importance describes the model on average and does not justify one decision."))
A(MCQ("AI", ["neural networks", "early stopping"], "easy",
 "While training a neural network, training loss keeps decreasing but validation loss starts increasing after epoch 12. What is the standard remedy?",
 "Stop at (or restore weights from) about epoch 12 – early stopping – and/or add regularization such as dropout",
 ["Train for many more epochs until the validation loss comes down by itself", "Evaluate only on the training data from now on", "Increase the learning rate to reduce the training loss faster"],
 "Diverging validation loss indicates overfitting. Early stopping and regularization limit memorisation; training longer or ignoring validation performance makes it worse."))
# ---------------- SQL/DBMS (2)
A(MCQ("SQL", ["indexes", "query optimisation"], "medium",
 "A composite index exists on Transactions(account_id, txn_time). Which query can use the index efficiently for an index range scan?",
 "WHERE account_id = 42 AND txn_time >= '2025-01-01'",
 ["WHERE txn_time >= '2025-01-01' (no condition on account_id)", "WHERE amount > 1000", "WHERE txn_time = '2025-01-01' OR amount > 5"],
 "A B-tree composite index is ordered by its leading column first. Seeking on account_id and then ranging on txn_time uses it fully; predicates that skip the leading column or involve other columns cannot use it for a seek (leftmost-prefix rule)."))
A(MCQ("SQL", ["transactions", "ACID"], "easy",
 "A funds transfer runs two UPDATEs (debit account A, credit account B). The system crashes after the first UPDATE but before the second. Which ACID property ensures the debit is rolled back?",
 "Atomicity",
 ["Isolation", "Consistency of the index", "Durability"],
 "Atomicity means a transaction is all-or-nothing: if it cannot complete, its partial changes are undone. Isolation concerns concurrent transactions; durability guarantees that committed data survives crashes."))
# ---------------- JAVA, OOP, TEST, EXCEL, FIN
A(MCQ("JAVA", ["arithmetic", "type conversion"], "easy",
 "What is the output?\n\n```java\nint a = 7;\ndouble r = a / 2;\nSystem.out.println(r);\n```",
 "3.0",
 ["3.5", "3", "4.0"],
 "`a / 2` is integer division (both operands are int) giving 3 before it is widened to double 3.0. Writing `a / 2.0` would give 3.5."))
A(MCQ("OOP", ["composition", "inheritance"], "medium",
 "A `RiskReport` class needs the ability to format numbers using the existing `Formatter` class. Which design is generally preferable?",
 "Give RiskReport a Formatter field (composition), because a report is not a kind of formatter",
 ["Make RiskReport extend Formatter, since this reuses the code", "Copy the Formatter code into every report class", "Make all Formatter methods static and extend them in each report"],
 "Inheritance should model an 'is-a' relationship; reuse alone is better achieved by composition ('has-a'), which keeps coupling lower and avoids exposing unrelated inherited methods."))
A(MCQ("TEST", ["equivalence partitioning"], "easy",
 "A KYC form accepts ages 18–65 inclusive. Using equivalence partitioning, what is the minimum number of test cases to cover every equivalence class (one representative each)?",
 "3 (below 18, 18–65, above 65)",
 ["1", "2", "48"],
 "There are three classes: invalid-low, valid, invalid-high; each class needs one representative. Boundary-value analysis would add edge cases (17, 18, 65, 66) on top of this."))
A(MCQ("EXCEL", ["INDEX", "MATCH", "lookup"], "medium",
 "Cells A2:A5 contain B1, B2, B3, B4 and C2:C5 contain 10, 20, 30, 40. What does =INDEX(C2:C5, MATCH(\"B3\", A2:A5, 0)) return?",
 "30",
 ["3", "B3", "#N/A"],
 "MATCH with match type 0 finds the exact position of \"B3\" in A2:A5 (3rd item); INDEX then returns the 3rd value in C2:C5, i.e., 30. The position (3) is only the intermediate result."))
A(MCQ("FIN", ["data quality", "currency", "units"], "medium",
 "A fraud rule flags any transaction with amount > 10,000. The Transactions table stores 'amount' in the transaction's local currency (USD, EUR, JPY) without conversion. What is the most likely data-quality problem?",
 "Mixed currencies make the threshold inconsistent: many ordinary JPY transactions are flagged while large USD/EUR ones may not be; amounts should be normalised to a common currency first",
 ["Nothing; amounts in different currencies are directly comparable", "The threshold should be compared with the account number instead", "Currencies only matter for date columns"],
 "10,000 JPY is under $100 whereas 10,000 USD is a large payment. Comparing raw amounts across currencies produces false positives and false negatives, so convert using dated FX rates (or store a normalised amount) before applying thresholds."))
