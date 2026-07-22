# Model Evaluation Metrics

Choosing the right evaluation metric is itself a modeling decision, and
the wrong choice can make a genuinely bad model look good, or a genuinely
good model look bad, on paper. For classification, accuracy (fraction of
correct predictions) is intuitive but misleading on imbalanced data: a
classifier that always predicts the majority class on a 95%/5% imbalanced
dataset achieves 95% accuracy while being completely useless for the
minority class, which is often the class that actually matters (fraud,
disease, a rare defect).

Precision (of everything predicted positive, what fraction actually is
positive) and recall (of everything actually positive, what fraction was
correctly identified) capture the two different ways a classifier can be
wrong, and there is generally a tradeoff between them controlled by the
classifier's decision threshold: raising the threshold for predicting
"positive" tends to increase precision and decrease recall, and vice
versa. The F1 score (the harmonic mean of precision and recall)
summarizes both into one number when neither is unambiguously more
important, though in practice the right balance between precision and
recall is a business/domain decision (e.g. in a medical screening
context, missing a true positive is usually far more costly than a false
alarm, which argues for optimizing recall even at the cost of precision).

ROC-AUC (area under the receiver operating characteristic curve, which
plots true positive rate against false positive rate across all
thresholds) summarizes a classifier's ranking quality independent of any
single threshold choice, but can be overly optimistic on heavily
imbalanced data; PR-AUC (area under the precision-recall curve) is
generally more informative in that regime, since it does not have a
large "true negatives" term dominating the picture.

For regression, Mean Squared Error (MSE) penalizes large errors more
than proportionally (since errors are squared), which is appropriate when
large errors are disproportionately costly, while Mean Absolute Error
(MAE) penalizes all errors proportionally to their size and is more
robust to a few large outlier errors dominating the metric. R-squared
describes the proportion of variance in the target explained by the
model relative to a naive baseline that always predicts the mean, but can
be misleadingly inflated by simply adding more features regardless of
whether they are genuinely predictive, which is why adjusted R-squared or
out-of-sample (not training-set) R-squared is preferred for model
comparison.

In every case, the metric must be computed on data the model did not see
during training (a held-out validation or test set, or cross-validation
folds) -- a metric computed on training data measures memorization
capacity, not generalization, and will systematically overstate real-
world performance.
