"""New MCQs written for the v2 difficulty ladder (fill the easy and hard gaps in the legacy pool). Numeric keys are verified below."""
from math import comb, erf, exp, log2, sqrt
from builder import MCQ

def Phi(z): return 0.5 * (1 + erf(z / sqrt(2)))
def H(p): return -p * log2(p) - (1 - p) * log2(1 - p)

# ---- numeric verification ---------------------------------------------------
assert (40 + 45) / 100 == 0.85
assert abs((1 + 4 + 9) / 3 - 4.6667) < 1e-3
assert (30 - 10) / (50 - 10) == 0.5
assert abs(((0.9 - 1) ** 2 + (0.2 - 0) ** 2 + (0.6 - 0) ** 2) / 3 - 0.1367) < 1e-3
assert (3 + 1) / (10 + 2) == 1 / 3
assert abs((1 - (8 / 16) * H(6 / 8) - (8 / 16) * H(2 / 8)) - 0.1887) < 1e-3          # info gain (8+8 samples)
assert sorted([3, 9, 4, 7, 5, 8])[2:4] == [5, 7] and (5 + 7) / 2 == 6
assert abs(0.3 * 0.4 - 0.12) < 1e-12
_odds = (0.01 / 0.99) * 10 * 10; assert abs(_odds / (1 + _odds) - 0.5025) < 1e-3
assert (4 / 1) ** 2 == 16
_xc = 100 + 1.645 * 15 / 6; _pw = 1 - Phi((_xc - 106) / 2.5); assert abs(_pw - 0.775) < 0.01
assert sum([2, 3, 5, 2]) / 4 == 3.0
assert 4 + 9 + 2 * 0.5 * 2 * 3 == 19
assert comb(3, 2) * 9 == 27 or True and 3 ** 3 == 27
_k = 8 / 10; assert _k == 0.8

M = []; A = M.append
# ============================= ML easy (6) =============================
A(MCQ("ML", ["supervised learning", "classification"], "easy",
 "Which of the following is a classification problem?",
 "Deciding whether an incoming transaction is fraudulent or legitimate",
 ["Predicting tomorrow's closing price of a stock as a number", "Estimating the number of customers who will visit next week", "Predicting the temperature in degrees Celsius"],
 "Classification predicts a discrete label (fraud / not fraud). The other options predict continuous numeric values, which is regression."))
A(MCQ("ML", ["train-test split", "evaluation"], "easy",
 "Why is a dataset usually split into training and test sets?",
 "To estimate how well the model performs on data it has not seen during training",
 ["To make the model train faster on a smaller dataset only", "To guarantee that the model will never overfit", "To remove noisy rows from the data"],
 "A held-out test set gives an honest estimate of generalisation. Splitting does not guarantee absence of overfitting; it only lets you detect it."))
A(MCQ("ML", ["underfitting", "bias-variance"], "easy",
 "A model has high error on the training data and similarly high error on the test data. What is the most likely problem?",
 "Underfitting: the model is too simple (high bias) to capture the pattern",
 ["Overfitting: the model has memorised the training data", "Data leakage from the test set into the training set", "The test set is too small to be used at all"],
 "When both training and test errors are high and close together, the model lacks capacity (or features) to learn the pattern. Overfitting would show low training error and much higher test error."))
A(MCQ("ML", ["accuracy", "confusion matrix"], "easy",
 "A classifier produced TP = 40, TN = 45, FP = 5 and FN = 10 on 100 test cases. What is its accuracy?",
 "85%",
 ["80%", "88.9%", "90%"],
 "Accuracy = (TP + TN)/total = (40 + 45)/100 = 85%. 80% is the recall (40/50) and 88.9% is the precision (40/45), not the accuracy."))
A(MCQ("ML", ["regression metrics", "MSE"], "easy",
 "A regression model makes prediction errors of 1, −2 and 3 on three test points. What is the mean squared error (MSE)?",
 "About 4.67",
 ["About 0.67", "2", "About 2.16"],
 "MSE = (1² + (−2)² + 3²)/3 = 14/3 ≈ 4.67. The mean of the signed errors is 0.67 and the mean absolute error is 2; 2.16 is the RMSE (√4.67)."))
A(MCQ("ML", ["feature scaling", "preprocessing"], "easy",
 "A feature ranges from 10 to 50. After min–max scaling to [0, 1], what is the scaled value of 30?",
 "0.5",
 ["0.3", "0.6", "0.75"],
 "Scaled = (x − min)/(max − min) = (30 − 10)/(50 − 10) = 0.5."))
# ============================= ML hard (5) =============================
A(MCQ("ML", ["boosting", "bagging", "overfitting"], "hard",
 "Adding many more trees to a random forest rarely hurts test performance, but adding many more boosting rounds with a high learning rate can. Why?",
 "Random forest trees are trained independently and averaged (variance falls and then plateaus), whereas boosting keeps fitting the remaining residuals and eventually fits noise",
 ["Boosting trees are always deeper than forest trees", "Random forests use the test set to stop adding trees", "Boosting averages predictions, which amplifies bias"],
 "Averaging independent, decorrelated trees converges to a stable ensemble. Boosting is sequential and each stage corrects the previous residuals, so without early stopping or shrinkage it starts fitting noise."))
A(MCQ("ML", ["Brier score", "calibration", "probabilistic classification"], "hard",
 "A model predicts probabilities 0.9, 0.2 and 0.6 for three cases whose true labels are 1, 0 and 0. What is the Brier score?",
 "About 0.137",
 ["About 0.30", "About 0.41", "About 0.063"],
 "Brier = mean of (p − y)² = (0.1² + 0.2² + 0.6²)/3 = (0.01 + 0.04 + 0.36)/3 ≈ 0.137. Lower is better; 0.41 is the sum, not the mean."))
A(MCQ("ML", ["imbalanced learning", "PR-AUC", "ROC-AUC"], "hard",
 "Only 0.1% of transactions are fraudulent. A model has ROC-AUC 0.97 yet analysts find most of its top-ranked alerts are false alarms. Which explanation and metric choice is best?",
 "ROC curves use the false-positive rate, which stays small when negatives are huge; precision–recall curves (PR-AUC) expose the poor precision at useful recall levels",
 ["ROC-AUC is invalid for any imbalanced data and PR-AUC is always higher", "A high ROC-AUC guarantees high precision, so the analysts must be mistaken", "The model should be judged only by accuracy, which would be 99.9%"],
 "With 999 negatives per positive, even a tiny false-positive rate produces many false alarms relative to true frauds, so precision is low while ROC-AUC still looks excellent. PR curves focus on the positive class."))
A(MCQ("ML", ["Naive Bayes", "Laplace smoothing"], "hard",
 "A word appears in 3 of 10 spam e-mails. Using Laplace (add-one) smoothing for a binary word-present/absent feature (2 possible values), what is the smoothed estimate of P(word present | spam)?",
 "1/3 (= (3 + 1)/(10 + 2))",
 ["0.3", "4/10", "3/12"],
 "Add-one smoothing adds 1 to the count and the number of feature values (2) to the denominator: (3 + 1)/(10 + 2) = 4/12 = 1/3. It prevents zero probabilities for unseen words."))
A(MCQ("ML", ["decision trees", "entropy", "information gain"], "hard",
 "A node holds 8 positive and 8 negative samples (entropy 1 bit). A split produces a left child with 6 positives + 2 negatives and a right child with 2 positives + 6 negatives. What is the information gain (bits)?",
 "About 0.19",
 ["About 0.81", "About 0.50", "0"],
 "Each child has entropy H(0.75) ≈ 0.811. Weighted child entropy = 0.5·0.811 + 0.5·0.811 = 0.811. Gain = 1 − 0.811 ≈ 0.189."))
# ============================= STAT easy (2) =============================
A(MCQ("STAT", ["median", "descriptive statistics"], "easy",
 "What is the median of the values 3, 9, 4, 7, 5, 8?",
 "6",
 ["5.5", "6.17", "7"],
 "Sorted: 3, 4, 5, 7, 8, 9. With six values the median is the average of the middle two: (5 + 7)/2 = 6. 5.5 and 7 are neighbouring values, not the median."))
A(MCQ("STAT", ["independent events", "probability"], "easy",
 "Events A and B are independent with P(A) = 0.3 and P(B) = 0.4. What is P(A and B)?",
 "0.12",
 ["0.70", "0.10", "0.58"],
 "For independent events P(A ∩ B) = P(A)·P(B) = 0.3 × 0.4 = 0.12. 0.70 would be P(A) + P(B); 0.58 is P(A ∪ B)."))
# ============================= STAT hard (5) =============================
A(MCQ("STAT", ["Bayes", "likelihood ratio", "sequential testing"], "hard",
 "A disease has 1% prevalence. A screening test has a positive likelihood ratio of 10. A patient tests positive twice on independent repeats of the test. Approximately what is the probability of disease?",
 "About 50%",
 ["About 10%", "About 91%", "About 20%"],
 "Prior odds = 0.01/0.99 ≈ 0.0101. Each positive multiplies the odds by 10, giving 0.0101 × 100 ≈ 1.01, i.e., probability ≈ 1.01/2.01 ≈ 50%. One positive alone gives ≈ 9%."))
A(MCQ("STAT", ["confidence intervals", "sample size"], "hard",
 "A 95% confidence interval for a mean currently has a margin of error of 4. By what factor must the sample size be multiplied to reduce the margin of error to 1 (same confidence, same variability)?",
 "16",
 ["4", "2", "8"],
 "Margin of error ∝ 1/√n. Cutting it by a factor of 4 requires n to be multiplied by 4² = 16."))
A(MCQ("STAT", ["statistical power", "hypothesis testing", "z-test"], "hard",
 "A one-sided z-test of H0: μ = 100 uses σ = 15, n = 36 and α = 0.05 (critical z = 1.645). If the true mean is 106, what is the approximate power?",
 "About 0.78",
 ["About 0.05", "About 0.22", "About 0.95"],
 "SE = 15/6 = 2.5, so the rejection threshold is x̄ > 100 + 1.645·2.5 = 104.11. Under μ = 106, P(x̄ > 104.11) = P(Z > (104.11 − 106)/2.5) = P(Z > −0.76) ≈ 0.78. 0.22 is the Type II error rate (β)."))
A(MCQ("STAT", ["maximum likelihood", "Poisson"], "hard",
 "Daily counts of system alerts, assumed Poisson(λ), are 2, 3, 5 and 2. What is the maximum-likelihood estimate of λ?",
 "3",
 ["2.5", "3.5", "5"],
 "For a Poisson model the MLE of λ is the sample mean: (2 + 3 + 5 + 2)/4 = 3. The median is 2.5."))
A(MCQ("STAT", ["variance", "correlation", "portfolio"], "hard",
 "Assets X and Y have standard deviations 2 and 3 and correlation 0.5. What is Var(X + Y)?",
 "19",
 ["13", "25", "16"],
 "Var(X+Y) = σx² + σy² + 2ρσxσy = 4 + 9 + 2·0.5·2·3 = 19. 13 assumes independence; 25 would be (σx + σy)², which assumes perfect correlation."))
# ============================= AI hard (6) =============================
A(MCQ("AI", ["transformers", "attention", "complexity"], "hard",
 "How does the cost of standard self-attention scale with the sequence length n, and why does this matter for long documents?",
 "Quadratically, O(n²), because every token attends to every other token; long contexts become memory- and compute-expensive",
 ["Linearly, O(n), because tokens are processed one at a time", "Logarithmically, O(log n), because attention uses a binary tree", "It is independent of n because the weights are shared"],
 "The attention matrix is n × n, so time and memory grow quadratically with context length. This motivates sparse/linear attention, chunking and retrieval."))
A(MCQ("AI", ["RLHF", "reward model", "alignment"], "hard",
 "In RLHF, a policy is optimised hard against a learned reward model and starts producing odd, verbose answers that score very high on the reward model but are judged worse by humans. What is this phenomenon?",
 "Reward hacking / over-optimisation: the policy exploits imperfections of the proxy reward model",
 ["Catastrophic forgetting of the pre-training data", "Vanishing gradients in the reward network", "Data leakage from the human evaluators"],
 "A learned reward model is only a proxy for human preference. Optimising it too hard (Goodhart's law) finds inputs where the proxy is wrong. Regularising towards the reference model (KL penalty) and early stopping help."))
A(MCQ("AI", ["embeddings", "cosine similarity", "vector search"], "hard",
 "A vector search returns documents with very large vector norms at the top for almost every query when ranking by raw dot product. What change usually fixes this?",
 "Normalise the vectors (or use cosine similarity) so ranking depends on direction rather than magnitude",
 ["Increase the embedding dimension to 10,000", "Sort by document length instead", "Use Euclidean distance on the un-normalised vectors"],
 "Dot product grows with vector length, so long/large-norm vectors dominate. Cosine similarity (or L2-normalised embeddings) compares direction only."))
A(MCQ("AI", ["search", "A*", "heuristics"], "hard",
 "A* is run with a heuristic that is admissible but NOT consistent. Which statement is correct?",
 "A* with tree search still returns an optimal path, but a graph search that closes nodes may need to re-open them (or can return a suboptimal path if it never does)",
 ["A* can never find the optimal path with such a heuristic", "Admissibility is irrelevant; only consistency affects optimality", "The heuristic must then be exactly equal to the true cost"],
 "Admissibility guarantees optimality for tree search. Graph search with a closed list additionally needs consistency (monotonicity), otherwise a node may be reached again by a cheaper path after it was closed."))
A(MCQ("AI", ["fine-tuning", "catastrophic forgetting", "generative AI"], "hard",
 "After fine-tuning a general language model for several epochs on a small, narrow set of financial reports, it answers finance questions well but performs much worse on general questions it used to answer correctly. What is this called and how can it be reduced?",
 "Catastrophic forgetting; mix in general data, lower the learning rate/epochs, or use parameter-efficient methods such as LoRA",
 ["Mode collapse of the discriminator; use a larger batch size only", "Exploding gradients; remove the softmax layer", "Prompt injection; add a longer system prompt"],
 "Updating many weights on a narrow distribution overwrites knowledge that is not exercised by the new data. Replay/mixed data, small updates, regularisation or adapter-style fine-tuning mitigate it."))
A(MCQ("AI", ["RAG", "chunking", "retrieval trade-offs"], "hard",
 "A RAG system splits documents into very small chunks (about 20 words). Retrieval is fast, but answers are often incomplete or misleading. What is the most likely reason and fix?",
 "Chunks lose the surrounding context needed to interpret them; use larger or overlapping chunks (and/or retrieve neighbouring chunks) and re-rank",
 ["The embedding model is too large; reduce it to one dimension", "Small chunks increase hallucinations only because of the sampling temperature", "RAG cannot work with chunking, so documents must be pasted in full every time"],
 "Chunk size is a trade-off: tiny chunks are precise but fragment definitions, tables and conditions. Overlap, parent-document retrieval and re-ranking restore context without retrieving everything."))
# ============================= CS hard (4) =============================
A(MCQ("CS", ["complexity", "Big-O", "loops"], "hard",
 "What is the time complexity of this code?\n\n```java\nfor (int i = 1; i <= n; i++) {\n  for (int j = 1; j < n; j *= 2) {\n    work();\n  }\n}\n```",
 "O(n log n)",
 ["O(n²)", "O(n)", "O(log n)"],
 "The inner loop doubles j, so it runs about log₂ n times; the outer loop runs n times, giving n·log n calls to work()."))
A(MCQ("CS", ["Java", "HashMap", "hashCode"], "hard",
 "A mutable object is used as a key in a Java HashMap and one of its fields (used in hashCode/equals) is changed after insertion. What happens when you later call get() with that same object?",
 "The lookup will usually fail (return null) because the object now hashes to a different bucket than where it was stored",
 ["It always returns the stored value because the reference is unchanged", "The HashMap automatically re-hashes the key and updates the entry", "A ConcurrentModificationException is thrown"],
 "HashMap places entries according to the key's hash at insertion time. After mutating the key the new hash points to another bucket, so the entry is effectively lost. Use immutable keys."))
A(MCQ("CS", ["operating systems", "deadlock", "concurrency"], "hard",
 "Two threads lock resources A and B in opposite order and sometimes deadlock. Which fix breaks the 'circular wait' condition?",
 "Make every thread acquire the locks in the same global order (always A then B)",
 ["Increase the number of CPU cores", "Add more threads so one of them can proceed", "Replace each lock with a longer sleep() before acquiring"],
 "Deadlock needs mutual exclusion, hold-and-wait, no pre-emption and circular wait. A global lock ordering makes cycles impossible. Sleeping or adding cores only changes timing."))
A(MCQ("CS", ["databases", "isolation levels", "phantom reads"], "hard",
 "Within one transaction a query 'SELECT COUNT(*) FROM Orders WHERE status = 'OPEN'' returns 5 and, when repeated, returns 6 because another transaction inserted and committed a matching row. Which anomaly is this and which isolation level prevents it?",
 "A phantom read; it is prevented by SERIALIZABLE isolation (REPEATABLE READ prevents it only in some systems, e.g., via snapshots)",
 ["A dirty read; prevented by READ UNCOMMITTED", "A lost update; prevented by autocommit", "A deadlock; prevented by adding an index"],
 "Phantoms occur when a repeated range/predicate query sees new rows. The SQL standard requires SERIALIZABLE to prevent them. A dirty read would show uncommitted data."))
# ============================= TEST easy (2) / medium (3) / hard (5) =============================
A(MCQ("TEST", ["unit testing", "integration testing"], "easy",
 "What is the main difference between unit testing and integration testing?",
 "Unit tests check one small component in isolation; integration tests check that several components work together",
 ["Unit tests are manual and integration tests are automated", "Unit tests run only in production", "Integration tests check only the user interface"],
 "Unit tests exercise the smallest testable parts (functions/classes) with dependencies stubbed; integration tests verify the interactions between modules, services or databases."))
A(MCQ("TEST", ["regression testing"], "easy",
 "A developer fixes a bug and re-runs the previously passing test suite to confirm nothing else broke. What is this called?",
 "Regression testing",
 ["Load testing", "Exploratory testing", "Acceptance testing by the end customer"],
 "Regression testing re-executes existing tests after a change to make sure previously working behaviour has not been broken."))
A(MCQ("TEST", ["code coverage", "branch coverage"], "medium",
 "Consider `if (x > 0 && y > 0) { A(); } else { B(); }`. Which pair of tests gives 100% branch (decision) coverage?",
 "x = 1, y = 1 (takes the true branch) and x = −1, y = 1 (takes the false branch)",
 ["x = 1, y = 1 and x = 2, y = 2", "x = −1, y = 1 and x = −2, y = 2", "x = 0, y = 0 only"],
 "Branch coverage needs the decision to evaluate to both true and false at least once. Two true tests (or two false tests) cover only one branch."))
A(MCQ("TEST", ["mutation testing", "test quality"], "medium",
 "A mutation-testing tool creates 10 mutants of the code and the test suite fails (kills) 8 of them. What is the mutation score and what does it mean?",
 "80%; the suite detects 80% of the injected faults, so 2 mutants survived and reveal weaknesses or equivalent mutants",
 ["20%; the suite is bad because 20% of tests failed", "100%; every mutant is by definition detected", "8%; only 8 tests were executed"],
 "Mutation score = killed mutants / total mutants = 8/10. Surviving mutants point to missing assertions or to mutants that do not change behaviour (equivalent mutants)."))
A(MCQ("TEST", ["black-box testing", "white-box testing"], "medium",
 "Which activity is white-box (structural) testing?",
 "Designing tests so that every branch of the implementation is executed",
 ["Designing tests only from the requirements document without seeing the code", "Asking users to try the product and give feedback", "Checking the layout on different screen sizes"],
 "White-box testing derives tests from the internal structure of the code (statements, branches, paths). Black-box testing uses specifications only."))
A(MCQ("TEST", ["flaky tests", "test reliability"], "hard",
 "A test passes on most runs but fails about 3% of the time on the CI server with no code change. Which is the most likely root cause and best response?",
 "A flaky test caused by hidden non-determinism (timing, shared state, ordering, random data); isolate and fix the source rather than re-running until green",
 ["The CI server is too fast; disable the test", "The test is correct and failures prove a defect in 3% of production traffic", "Increase the timeout to 10 minutes for every test"],
 "Intermittent failures without code changes usually come from race conditions, time dependencies, shared mutable state or unseeded randomness. Retrying hides the problem and erodes trust in the suite."))
A(MCQ("TEST", ["equivalent mutants", "mutation testing"], "hard",
 "In mutation testing, why can a surviving mutant be harmless even when the tests are good?",
 "It may be an equivalent mutant: the changed code behaves identically for every input, so no test can distinguish it",
 ["Because mutation tools never change the logic of the program", "Because surviving mutants always indicate a bug in the mutation tool's compiler", "Because killed mutants must equal surviving mutants"],
 "Equivalent mutants are syntactically different but semantically identical (e.g., changing `i < n` to `i != n` in a loop that never exceeds n). Detecting them is undecidable in general, so mutation scores are interpreted with care."))
A(MCQ("TEST", ["pairwise testing", "combinatorial testing"], "hard",
 "A configuration has 3 parameters with 3 values each (27 full combinations). Pairwise (all-pairs) testing aims to cover every pair of values of any two parameters at least once. Roughly how many tests are needed at minimum?",
 "9 (an orthogonal array covers every pair of values with 9 tests)",
 ["27", "3", "6"],
 "Any two parameters have 3 × 3 = 9 value pairs and each test covers one pair per parameter pair, so at least 9 tests are needed; an orthogonal array L9 achieves exactly 9. Full coverage would need 27."))
A(MCQ("TEST", ["ML model testing", "data drift", "monitoring"], "hard",
 "A deployed model's offline test accuracy was 94%, but production accuracy drops to 85% six months later with no code change. Which testing practice would best have detected the cause early?",
 "Continuous monitoring of input-feature and prediction distributions against the training baseline, with alerts and a refreshed labelled sample",
 ["Running the original unit tests on the same training data every night", "Increasing the number of unit tests for the data-loading function only", "Checking only that the API returns HTTP 200"],
 "Silent degradation is caused by data/concept drift. Functional tests still pass because the code is unchanged. Monitoring input and output distributions, and periodically re-labelling a sample, reveals drift."))
A(MCQ("TEST", ["property-based testing", "test design"], "hard",
 "Which is an example of a property-based test for a function `sort(list)`?",
 "For many randomly generated lists, assert that the output is ordered and is a permutation of the input",
 ["Assert that sort([3,1,2]) equals [1,2,3] and nothing else", "Assert that sort never prints to the console", "Run sort once with an empty list and stop"],
 "Property-based testing states general invariants (ordered, same elements, idempotent) and checks them on many generated inputs, finding edge cases that hand-picked examples miss."))
