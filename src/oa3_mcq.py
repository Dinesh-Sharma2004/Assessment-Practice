from math import exp, sqrt
from builder import MCQ

assert abs((1 - 1/1000) ** 1000 - 0.368) < 0.001
assert abs(0.1 * 0.3 / (0.1 * 0.3 + 0.9 * 0.05) - 0.4) < 1e-9
_e = -1 * .2 + 0 * .5 + 1 * .3; _v = (1 * .2 + 0 + 1 * .3) - _e ** 2
assert abs(_e - 0.1) < 1e-12 and abs(_v - 0.49) < 1e-12
_se = sqrt(.3 * .7 / 400); assert abs(.3 - 1.96 * _se - .255) < .001 and abs(.3 + 1.96 * _se - .345) < .001
assert 100 * 150 / 400 == 37.5
assert abs(exp(-3) - 0.0498) < 1e-4
assert (3 * 4 + 4 * 3) / (5 * 5) == 0.96
assert abs(3.0 - 1.2 * 2.2 - 0.36) < 1e-9

M = []; A = M.append
# ---------------- ML (6)
A(MCQ("ML", ["ensembles", "random forest", "variance"], "medium",
 "Why does a random forest usually generalise better than a single deep decision tree trained on the same data?",
 "Averaging many trees trained on bootstrap samples with random feature subsets reduces variance without greatly increasing bias",
 ["Each tree in the forest is shallower, which removes all bias", "The forest uses the test set to prune trees", "Random forests always have lower training error than a single tree"],
 "Deep trees have low bias but high variance. Bagging plus feature subsampling decorrelates the trees so their averaged prediction is more stable. The forest does not remove bias, never touches the test set, and its training error is not guaranteed to be lower."))
A(MCQ("ML", ["gradient boosting", "ensembles"], "medium",
 "Which description of gradient boosting is correct?",
 "Trees are added sequentially, each one fitted to the current errors (negative gradients) of the ensemble, and a learning rate shrinks each tree's contribution",
 ["All trees are trained independently in parallel and their votes are averaged", "Each tree is trained on a different, non-overlapping subset of features only", "It trains one very deep tree and then prunes it"],
 "Boosting builds an additive model stage by stage to correct previous errors; shrinkage (learning rate) and early stopping control overfitting. Independent training with averaging describes bagging/random forests."))
A(MCQ("ML", ["imbalanced learning", "data leakage", "oversampling"], "hard",
 "You will cross-validate a classifier on data with 1% positives and want to use SMOTE-style oversampling of the minority class. What is the correct procedure?",
 "Oversample only the training portion inside each fold and evaluate on untouched, original-distribution validation folds",
 ["Oversample the whole dataset first, then run cross-validation", "Oversample the validation fold so that it is balanced as well", "Oversampling is only valid after the final test, never in training"],
 "If synthetic or duplicated minority samples are created before splitting, copies/neighbours of validation points leak into training and scores are inflated. Validation data must keep the real class distribution."))
A(MCQ("ML", ["bootstrap", "out-of-bag"], "medium",
 "In a random forest each tree is trained on a bootstrap sample of n rows (sampling with replacement). For large n, roughly what fraction of rows is left out of a given tree's sample (and available for out-of-bag evaluation)?",
 "About 36.8% (≈ e^−1)",
 ["About 63.2%", "Exactly 50%", "Exactly 0%, since every row is sampled at least once"],
 "P(a given row is never drawn in n draws) = (1 − 1/n)^n → e^−1 ≈ 0.368. About 63.2% of rows are in the bootstrap sample; the rest provide a built-in validation estimate (OOB error)."))
A(MCQ("ML", ["feature importance", "model interpretation"], "hard",
 "A tree ensemble's impurity-based feature importance ranks a high-cardinality ID-like column (thousands of unique values) as the most important feature. What is the best response?",
 "Treat it with suspicion: impurity importance is biased towards high-cardinality features; check permutation importance on held-out data and consider dropping the identifier",
 ["Conclude the identifier is the strongest causal driver of the target", "Increase the number of trees until the importance disappears", "Standardise the column and re-run the same importance calculation"],
 "Splits on many-valued columns can reduce impurity by chance on training data, inflating impurity-based importance. Permutation importance on validation data measures the loss in performance when the feature is shuffled and is less biased. Importance is not causation."))
A(MCQ("ML", ["anomaly detection", "isolation forest"], "medium",
 "How does an Isolation Forest decide that a point is anomalous?",
 "Anomalies are isolated by random splits in fewer steps, so they have shorter average path lengths in the trees",
 ["Anomalies are the points with the longest path length in the trees", "Anomalies are the points farthest from the global mean in every feature", "Anomalies are points that the forest classifies with the lowest accuracy"],
 "Isolation Forest repeatedly splits randomly on features; rare, different points are separated quickly (short paths), while dense normal points need many splits."))
# ---------------- STAT (5)
A(MCQ("STAT", ["bayes", "conditional probability", "text features"], "medium",
 "10% of news articles are negative-sentiment. 30% of negative articles contain the word 'lawsuit' versus 5% of non-negative articles. If an article contains 'lawsuit', what is the probability it is negative?",
 "40%",
 ["30%", "10%", "75%"],
 "P(neg|lawsuit) = 0.10·0.30 / (0.10·0.30 + 0.90·0.05) = 0.03/0.075 = 0.40. 30% is the likelihood P(lawsuit|neg), not the posterior."))
A(MCQ("STAT", ["expectation", "variance", "discrete distributions"], "medium",
 "A sentiment label X takes values −1, 0, +1 with probabilities 0.2, 0.5, 0.3. What is Var(X)?",
 "0.49",
 ["0.50", "0.10", "0.70"],
 "E[X] = −0.2 + 0 + 0.3 = 0.1; E[X²] = 0.2 + 0 + 0.3 = 0.5; Var = 0.5 − 0.1² = 0.49. 0.50 forgets to subtract the squared mean."))
A(MCQ("STAT", ["confidence intervals", "proportions"], "medium",
 "In a sample of 400 articles, 120 are classified as positive. What is the approximate 95% confidence interval for the true proportion positive (normal approximation)?",
 "(0.255, 0.345)",
 ["(0.280, 0.320)", "(0.200, 0.400)", "(0.255, 0.405)"],
 "p̂ = 0.30, SE = √(0.3·0.7/400) ≈ 0.0229, margin = 1.96·0.0229 ≈ 0.045, giving (0.255, 0.345)."))
A(MCQ("STAT", ["chi-square test", "contingency tables"], "medium",
 "In a 2×2 table of article sentiment (positive/negative) by source type (wire/blog), row totals are 100 (positive) and 300 (negative), column totals are 150 (wire) and 250 (blog), total N = 400. What is the expected count for positive–wire under independence?",
 "37.5",
 ["25", "50", "75"],
 "Expected = (row total × column total) / N = 100·150/400 = 37.5. The chi-square statistic sums (O − E)²/E over cells."))
A(MCQ("STAT", ["Poisson distribution", "anomaly rates"], "medium",
 "A newswire publishes on average 3 articles per hour about a company, modelled as Poisson. What is the probability of seeing no articles in the next hour?",
 "About 5% (e^−3 ≈ 0.0498)",
 ["About 33%", "About 95%", "Exactly 0, because the mean is 3"],
 "P(N = 0) = e^−λ = e^−3 ≈ 0.0498. About 95% is the probability of at least one article."))
# ---------------- AI (4)
A(MCQ("AI", ["embeddings", "cosine similarity"], "easy",
 "Two embedding vectors are u = (3, 4) and v = (4, 3). What is their cosine similarity?",
 "0.96",
 ["0.50", "1.00", "0.00"],
 "u·v = 12 + 12 = 24 and |u||v| = 5·5 = 25, so cos = 24/25 = 0.96. It would be 1 only for vectors pointing in the same direction."))
A(MCQ("AI", ["transformers", "self-attention", "positional encoding"], "medium",
 "Why do transformer models need positional encodings (or equivalent position information)?",
 "Self-attention by itself treats the input as an unordered set, so word order information must be injected explicitly",
 ["To reduce the dimensionality of the embeddings", "To make attention weights sum to one", "To allow the model to process only short sentences"],
 "Attention computes pairwise interactions without any inherent order, so 'A beat B' and 'B beat A' would look identical without position information. Softmax already normalises attention weights."))
A(MCQ("AI", ["RAG", "retrieval", "evaluation"], "medium",
 "A RAG assistant for financial filings sometimes answers with outdated figures even though the correct filing is in the index. Which diagnostic step is most useful first?",
 "Measure retrieval quality separately (e.g., recall@k of the right passage); if the right chunk is missing from the top-k, fix chunking/metadata filters/reranking before changing the generator",
 ["Increase the generator's temperature to get more varied answers", "Delete the index and rely only on the model's parametric memory", "Fine-tune the model on the questions asked so far, without checking retrieval"],
 "RAG quality depends on both retrieval and generation. If the correct passage is not retrieved, no generator can ground its answer in it; evaluating each stage separately localises the failure. Higher temperature increases randomness, not grounding."))
A(MCQ("AI", ["hallucinations", "generative AI", "responsible AI"], "medium",
 "A summarisation model writes a fluent quote attributed to a CEO that does not appear in the source article. Which mitigation is most appropriate for a production newsroom tool?",
 "Ground generation in the source, require citations/quote verification against the text, and keep a human review step for high-stakes outputs",
 ["Set temperature to 0, which guarantees that hallucinations cannot occur", "Make the prompt longer and more polite", "Remove all source documents so the model relies on its own knowledge"],
 "Hallucinated content is plausible but unsupported. Lower temperature can reduce variability but offers no guarantee; grounding, automated checks against sources and human oversight address the risk."))
# ---------------- SQL (2)
A(MCQ("SQL", ["window functions", "ranking"], "medium",
 "Scores in descending order are 90, 90, 80. Which window function assigns the ranks 1, 1, 2 respectively?",
 "DENSE_RANK()",
 ["RANK()", "ROW_NUMBER()", "NTILE(3)"],
 "DENSE_RANK gives tied rows the same rank without gaps (1,1,2). RANK leaves a gap after ties (1,1,3); ROW_NUMBER numbers rows uniquely (1,2,3)."))
A(MCQ("SQL", ["schema design", "keys", "many-to-many"], "medium",
 "An article can mention many entities and an entity can appear in many articles, with a sentiment score per mention. What is the standard relational design?",
 "A junction table (article_id, entity_id, score) with a composite primary key (article_id, entity_id) and foreign keys to both parents",
 ["Store a comma-separated list of entity ids in an Articles column", "Add one entity_id column to Articles", "Duplicate the article text for each entity in the Entities table"],
 "Many-to-many relationships are modelled with an associative table keyed by both foreign keys; lists in a column violate first normal form and make joins and constraints hard."))
# ---------------- JAVA, OOP, TEST, EXCEL, FIN
A(MCQ("JAVA", ["collections", "overloading"], "medium",
 "What does this code print?\n\n```java\nList<Integer> list = new ArrayList<>(List.of(10, 20, 30));\nlist.remove(1);\nSystem.out.println(list);\n```",
 "[10, 30]",
 ["[20, 30]", "[10, 20, 30]", "[10, 20]"],
 "`remove(1)` with an int literal resolves to `remove(int index)`, deleting the element at index 1 (20). To remove the value 1 you would call `list.remove(Integer.valueOf(1))`."))
A(MCQ("OOP", ["constructors", "inheritance"], "easy",
 "What is printed by `new B();`?\n\n```java\nclass A { A() { System.out.print(\"A\"); } }\nclass B extends A { B() { System.out.print(\"B\"); } }\n```",
 "AB",
 ["BA", "B", "A"],
 "A subclass constructor implicitly calls `super()` first, so the superclass constructor body runs before the subclass constructor body."))
A(MCQ("TEST", ["mocking", "unit testing"], "medium",
 "A unit test for a function that computes a daily sentiment average calls a live sentiment API over the network. What is the best improvement?",
 "Replace the API with a stub/mock returning fixed values so the test is fast, deterministic and independent of the network",
 ["Keep the live call and re-run the test until it passes", "Delete the test because networks are unreliable", "Test only that the function does not throw an exception"],
 "Unit tests should isolate the unit under test. Stubbing the external dependency makes results repeatable, so assertions about the calculation are meaningful."))
A(MCQ("EXCEL", ["text functions", "TRIM", "SUBSTITUTE"], "medium",
 "Cell A2 contains \"  Fed holds rates steady \" (extra spaces at both ends). What does =LEN(TRIM(A2))-LEN(SUBSTITUTE(TRIM(A2),\" \",\"\"))+1 return?",
 "4",
 ["3", "6", "5"],
 "TRIM leaves \"Fed holds rates steady\" (22 characters, 3 spaces); removing spaces leaves 19 characters; 22 − 19 + 1 = 4 words."))
A(MCQ("FIN", ["abnormal returns", "event study", "CAPM"], "medium",
 "On an earnings-news day a stock returned +3.0% while the market index returned +2.2%. The stock's beta is 1.2. Using a simple market model (expected return = beta × market return, risk-free rate ignored), what is the abnormal return?",
 "+0.36%",
 ["+0.80%", "+1.80%", "+3.00%"],
 "Expected return = 1.2 × 2.2% = 2.64%. Abnormal return = actual − expected = 3.00% − 2.64% = 0.36%. +0.80% ignores beta (3.0 − 2.2); +3.0% ignores market movement."))
