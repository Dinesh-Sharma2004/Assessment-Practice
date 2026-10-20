from math import sqrt
from builder import MCQ

_mae = (2 + 2 + 2 + 10) / 4; _rmse = sqrt((4 + 4 + 4 + 100) / 4)
assert _mae == 4 and abs(_rmse - 5.2915) < 1e-3
assert (6 + 3) / (6 + 3 + 1) == 0.9
_sb, _sw = 30, 54; _f = (_sb / 2) / (_sw / 27); assert _f == 7.5
assert abs(0.8 ** 2 - 0.64) < 1e-12
assert .25 * 4 + .25 * 9 == 3.25
assert abs(2.0 - 0.1 * 0.5 - 1.95) < 1e-12
a = [1, 2, 2, 3]; b = [2, 2, 3, 4]
inner = sum(1 for x in a for y in b if x == y); left = inner + sum(1 for x in a if x not in b)
assert (inner, left) == (5, 6)
assert abs(1.2 * sqrt(252) - 19.05) < 0.01

M = []; A = M.append
# ---------------- ML (6)
A(MCQ("ML", ["time-series validation", "cross-validation"], "medium",
 "You are forecasting next-day volatility from three years of daily data. Which validation scheme is most appropriate for choosing hyper-parameters?",
 "Walk-forward (expanding or rolling window) validation: always train on the past and validate on a later block",
 ["Standard shuffled 5-fold cross-validation, because it uses all data efficiently", "Train on the most recent year and test on the oldest year", "Validate on the training data, since time series are autocorrelated"],
 "Shuffled folds put future observations in the training set and past ones in validation, leaking information and giving optimistic scores. Walk-forward validation mimics production: only past data can be used to predict the future."))
A(MCQ("ML", ["forecast errors", "MAE", "RMSE"], "medium",
 "A forecast has errors (actual − forecast) of 2, −2, 2 and −10 over four days. Which pair of statements is correct?",
 "MAE = 4 and RMSE ≈ 5.29; RMSE is larger because it penalises the large error more",
 ["MAE = 4 and RMSE = 4; the two metrics are always equal", "MAE ≈ 5.29 and RMSE = 4", "MAE = 0 because positive and negative errors cancel"],
 "MAE = (2+2+2+10)/4 = 4. RMSE = √((4+4+4+100)/4) = √28 ≈ 5.29. Squaring weights big errors more, so RMSE ≥ MAE with equality only if all absolute errors are equal. The mean of signed errors (the bias) is 0 here, which is not MAE."))
A(MCQ("ML", ["PCA", "dimensionality reduction"], "medium",
 "A PCA on standardised returns of 10 stocks gives eigenvalues 6, 3, 1 (and zeros for the remaining components). What fraction of total variance is explained by the first two principal components?",
 "90%",
 ["60%", "30%", "100%"],
 "Explained variance ratio = (6 + 3)/(6 + 3 + 1) = 0.9. The first component alone explains 60%."))
A(MCQ("ML", ["clustering", "silhouette score"], "medium",
 "After clustering stocks with k-means, a point has a silhouette value of −0.4. What does this indicate?",
 "The point is on average closer to the points of a neighbouring cluster than to its own cluster, so it is probably misassigned",
 ["The point is perfectly clustered", "The point is exactly on the cluster centroid", "The clustering algorithm failed to run"],
 "Silhouette s = (b − a)/max(a, b), where a is the mean distance to its own cluster and b the mean distance to the nearest other cluster. Values near +1 mean well clustered; negative values mean b < a."))
A(MCQ("ML", ["neural networks", "gradient descent", "learning rate"], "medium",
 "While training a neural network the loss oscillates wildly and sometimes becomes NaN after a few iterations. What is the most likely cause and fix?",
 "The learning rate is too large; reduce it (and/or clip gradients)",
 ["The learning rate is too small; increase it by 100×", "The model has too few parameters; add more epochs", "The labels are balanced; remove half of them"],
 "A too-large step overshoots minima and can blow up, giving oscillation or divergence (NaN). Reducing the learning rate or clipping gradients stabilises training."))
A(MCQ("ML", ["stationarity", "time series", "spurious regression"], "hard",
 "A student regresses one stock's raw price level on another's raw price level (both trending random walks) and gets R² = 0.95. What is the main concern?",
 "Spurious regression: non-stationary trending series can look strongly related by chance; model returns/differences or test for cointegration instead",
 ["R² can never be that high for financial data, so the regression must be a typo", "The regression proves that one stock causes the other", "High R² guarantees good out-of-sample forecasts"],
 "Independent random walks frequently yield high R² and significant t-statistics because of shared trends. Differencing to obtain stationary returns (or testing for cointegration) avoids this trap; correlation in levels is not causation."))
# ---------------- STAT (5)
A(MCQ("STAT", ["bootstrap", "confidence intervals"], "medium",
 "You want a 95% confidence interval for the median daily return from 250 observations without assuming normality. Which bootstrap procedure is correct?",
 "Resample the 250 returns with replacement many times, compute the median of each resample, and take the 2.5th and 97.5th percentiles of those medians",
 ["Sample 250 returns without replacement many times and average the medians", "Take the 2.5th and 97.5th percentile of the original 250 returns", "Resample once and use ±1.96 standard deviations of that sample"],
 "The bootstrap approximates the sampling distribution of a statistic by resampling the data with replacement. The percentile interval of the bootstrap medians estimates uncertainty in the median; percentiles of the raw returns describe the spread of returns, not the uncertainty of the median."))
A(MCQ("STAT", ["ANOVA", "F-test"], "hard",
 "A one-way ANOVA compares mean returns of 3 sectors with 10 stocks each. The between-group sum of squares is 30 and the within-group sum of squares is 54. What is the F statistic?",
 "7.5",
 ["0.56", "15", "1.8"],
 "df between = 3 − 1 = 2, df within = 30 − 3 = 27. MSB = 30/2 = 15, MSW = 54/27 = 2, F = 15/2 = 7.5. 15 is MSB alone; 0.56 inverts the ratio of sums of squares."))
A(MCQ("STAT", ["regression assumptions", "heteroscedasticity"], "medium",
 "A plot of residuals versus fitted values from a linear regression of trading volume on market cap shows a funnel shape (spread grows with the fitted value). Which assumption is violated and what is a standard remedy?",
 "Homoscedasticity (constant error variance); use a transformation such as log(volume) or heteroscedasticity-robust standard errors",
 ["Linearity of means only; add an intercept", "Independence of features; delete the first row", "Normality of the features; standardise them"],
 "A funnel pattern means the error variance changes with the fitted value (heteroscedasticity). OLS coefficient estimates stay unbiased but standard errors are wrong; log transforms or robust (e.g., White) standard errors are common fixes."))
A(MCQ("STAT", ["correlation", "R-squared"], "easy",
 "In a simple linear regression of one stock's return on another's, the sample correlation is r = 0.8. What is R²?",
 "0.64",
 ["0.80", "0.89", "0.20"],
 "In simple linear regression R² = r² = 0.64: 64% of the variance of the response is explained by the predictor. √0.8 ≈ 0.89 is a common mistake."))
A(MCQ("STAT", ["variance", "portfolio", "independence"], "medium",
 "Two independent assets have return variances 4 and 9 (in %²). A portfolio invests 50% in each. What is the portfolio variance?",
 "3.25",
 ["6.5", "13", "2.5"],
 "For independent assets Var = w₁²σ₁² + w₂²σ₂² = 0.25·4 + 0.25·9 = 3.25. 6.5 is the weighted-average variance; 13 simply adds the variances."))
# ---------------- AI (4)
A(MCQ("AI", ["gradient descent", "optimisation"], "easy",
 "A weight has value 2.0, the gradient of the loss with respect to it is 0.5, and the learning rate is 0.1. After one gradient-descent step what is the weight?",
 "1.95",
 ["2.05", "1.5", "2.5"],
 "w ← w − η·∇L = 2.0 − 0.1·0.5 = 1.95. Gradient descent moves against the gradient."))
A(MCQ("AI", ["deep learning", "vanishing gradients", "activation functions"], "medium",
 "In a deep network with many sigmoid layers, gradients in the earliest layers become extremely small during training. Which change most directly helps?",
 "Use ReLU-type activations, careful initialisation/normalisation and residual (skip) connections",
 ["Use even more sigmoid layers", "Remove the loss function", "Set every weight to zero"],
 "Sigmoid derivatives are at most 0.25, so products over many layers shrink gradients (vanishing gradients). ReLU, good initialisation, normalisation and skip connections keep gradient signals usable. Zero initialisation also makes neurons identical."))
A(MCQ("AI", ["search", "hill climbing", "simulated annealing"], "medium",
 "A hill-climbing search for a portfolio configuration keeps getting stuck in a local optimum. Which modification can help it escape?",
 "Simulated annealing or random restarts: occasionally accept worse moves or start from different points",
 ["Only ever accept strictly better neighbours and remove randomness completely", "Use a smaller neighbourhood so fewer moves are considered", "Stop the search after the first step"],
 "Plain hill climbing cannot leave a local optimum. Randomisation (restarts) or accepting worse moves with a decreasing probability (simulated annealing) lets the search explore other regions."))
A(MCQ("AI", ["reinforcement learning", "discount factor"], "medium",
 "In reinforcement learning for trade execution, what does choosing a discount factor γ close to 0 imply?",
 "The agent is short-sighted: it mostly maximises immediate rewards and gives little weight to future rewards",
 ["The agent ignores immediate rewards and cares only about the far future", "The agent cannot learn anything", "Rewards are automatically normalised to a mean of zero"],
 "The return is Σ γᵗ rₜ. With γ ≈ 0 only the first terms matter. γ close to 1 values long-term outcomes (but makes learning harder)."))
# ---------------- SQL (2)
A(MCQ("SQL", ["window functions", "GROUP BY"], "easy",
 "You want every price row to appear together with the average close of its sector on the same row. Which construct achieves this without collapsing rows?",
 "AVG(close) OVER (PARTITION BY sector)",
 ["SELECT sector, AVG(close) ... GROUP BY sector", "SELECT DISTINCT AVG(close)", "HAVING AVG(close) > 0"],
 "Window aggregates compute a value over a partition but keep each input row. GROUP BY collapses rows to one per group."))
A(MCQ("SQL", ["joins", "duplicates"], "hard",
 "Table A has key values 1, 2, 2, 3 and table B has key values 2, 2, 3, 4. How many rows does A LEFT JOIN B ON A.key = B.key return?",
 "6",
 ["4", "5", "8"],
 "Key 2 matches 2×2 = 4 row pairs, key 3 matches 1, so the inner join has 5 rows; key 1 has no match but is kept by LEFT JOIN with NULLs, giving 6. Many-to-many matches multiply rows."))
# ---------------- JAVA, OOP, TEST, EXCEL, FIN
A(MCQ("JAVA", ["strings", "immutability"], "easy",
 "What does this code print?\n\n```java\nString s = \"ab\";\ns.concat(\"cd\");\nSystem.out.println(s);\n```",
 "ab",
 ["abcd", "cd", "It does not compile"],
 "Strings are immutable: `concat` returns a new String that is discarded here, so `s` still refers to \"ab\"."))
A(MCQ("OOP", ["static members", "class vs instance"], "easy",
 "What does the final line print?\n\n```java\nclass Counter {\n  static int c = 0;\n  Counter() { c++; }\n}\n// elsewhere:\nnew Counter(); new Counter();\nSystem.out.println(Counter.c);\n```",
 "2",
 ["0", "1", "It does not compile because c is static"],
 "A static field belongs to the class and is shared by all instances; each constructor call increments the same variable."))
A(MCQ("TEST", ["test design", "off-by-one"], "medium",
 "A function returns the rolling mean of a series for a given window size. Which test is most likely to expose an off-by-one error in how the first rolling value is produced?",
 "A series whose length equals the window size, expecting exactly one output equal to the mean of the whole series",
 ["A very long random series, checking only that the function does not crash", "A series of identical values and a window of 1", "A test that checks only the data type of the return value"],
 "Edge cases at the boundary between 'not enough data' and 'one full window' reveal off-by-one mistakes. Long random inputs and type checks do not pin down the first index."))
A(MCQ("EXCEL", ["VLOOKUP", "approximate match"], "medium",
 "A2:B5 contains market-cap bands sorted ascending: 0 → \"Micro\", 1E9 → \"Small\", 5E9 → \"Mid\", 2E10 → \"Large\". What does =VLOOKUP(7.5E9, A2:B5, 2, TRUE) return?",
 "Mid",
 ["Small", "Large", "#N/A"],
 "With approximate match (TRUE) on sorted data, VLOOKUP returns the row of the largest value less than or equal to the lookup value: 5E9 → \"Mid\". With FALSE it would return #N/A because 7.5E9 is not an exact key."))
A(MCQ("FIN", ["volatility", "annualisation"], "easy",
 "A stock's daily return standard deviation is 1.2%. Assuming independent daily returns and 252 trading days per year, what is the approximate annualised volatility?",
 "About 19.0%",
 ["About 302%", "About 1.2%", "About 4.8%"],
 "Volatility scales with the square root of time: 1.2% × √252 ≈ 1.2% × 15.87 ≈ 19.05%. Multiplying by 252 would wrongly scale variance-like quantities."))
