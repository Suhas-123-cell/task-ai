# Evaluating Hypotheses and Model Selection

Estimating how well a learned hypothesis will perform on unseen data is as
important as the learning algorithm itself, because a hypothesis that
looks good on the training set may simply have overfit it. The
sample error of a hypothesis h on a sample S is the fraction of S that h
misclassifies; the true error is the probability that h misclassifies a
randomly drawn instance from the underlying (unknown) distribution. Sample
error is only an estimate of true error, and that estimate has variance
that shrinks as the sample size grows, formalized by confidence intervals
derived from the binomial (or its normal approximation).

Held-out validation splits the available data into a training set and a
separate test set that is never used to fit parameters, giving an
unbiased estimate of generalization error -- but at the cost of
"wasting" data that could otherwise have been used for training, which
matters when labeled data is scarce.

k-fold cross-validation addresses this by partitioning the data into k
equal folds, training k times (each time holding out a different fold as
the validation set and training on the remaining k-1 folds), and
averaging the resulting error estimates. This uses all the data for both
training and validation across the k runs while still keeping validation
data separate from training data within each run, at the cost of k times
the compute. Leave-one-out cross-validation is the special case k = n,
typically used only when data is very scarce.

When comparing two learning algorithms, a paired test (e.g. a paired
t-test over the per-fold error differences) is preferred over comparing
raw average errors, since it accounts for the fact that both algorithms
are evaluated on the same folds and so their errors are correlated --
increasing the statistical power to detect a genuine difference in
performance rather than noise.

Model selection more broadly must guard against two related failure
modes: using the test set repeatedly to make design decisions (which
leaks information from the test set into the model, inflating the
reported performance -- sometimes called "test set contamination"), and
comparing many candidate models/hyperparameters on the same validation
set without correction, which increases the chance that the
"best" validation score is partly a lucky fluctuation. A separate,
untouched test set reserved strictly for final reporting, and a
validation set used only for model/hyperparameter selection, is the
standard discipline for avoiding both pitfalls.
