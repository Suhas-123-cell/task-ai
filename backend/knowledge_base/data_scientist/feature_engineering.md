# Feature Engineering

Feature engineering is the process of transforming raw data into inputs
that make the underlying pattern easier for a model to learn -- often
having a bigger practical impact on model quality than the choice of
algorithm itself, since even a powerful model cannot learn a signal that
is not present or is badly obscured in its input representation.

Numeric features commonly need scaling, since many algorithms (k-NN,
SVMs, neural networks, anything based on gradient descent or distance
computation) are sensitive to feature magnitude: standardization
(subtract the mean, divide by standard deviation, producing zero mean and
unit variance) and min-max normalization (rescaling to a fixed range like
[0, 1]) are the two most common approaches, while tree-based models
(decision trees, random forests, gradient boosting) are invariant to
monotonic rescaling of individual features and generally do not need this
step.

Categorical features must be converted to a numeric representation.
One-hot encoding creates a separate binary column per category and is
appropriate when categories have no inherent order and their number is
modest; it becomes impractical (dimensionality explosion, sparse,
mostly-empty feature matrix) for high-cardinality categories like a user
ID or a free-text tag, where target encoding (replacing a category with a
statistic of the target variable computed on training data, e.g. mean
target value per category) or embedding-based representations are more
common -- though target encoding must be computed carefully (using only
training-fold data) to avoid leaking target information into the encoding
itself.

Handling missing values is itself a feature-engineering decision, not
just a cleaning step: mean/median imputation is simple but can distort
variance and correlations; a missing-value indicator column added
alongside an imputed value preserves the information that a value was
missing (which is sometimes itself predictive) rather than discarding it.

Feature leakage is the single most dangerous and most common bug in
applied feature engineering: using information that would not actually be
available at prediction time (e.g. a feature computed using data from
after the event being predicted, or a feature derived using the full
dataset including the test set, such as normalizing using statistics
computed over train+test combined). A model trained with leaked features
can show excellent validation and even test performance while being
functionally useless in production, because the leaked information will
not exist at real inference time -- which is why feature pipelines should
always be fit strictly on training data and then applied unchanged to
validation/test/production data, never re-fit on each split.
