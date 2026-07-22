# Exploratory Data Analysis

Exploratory Data Analysis (EDA) is the disciplined first pass over a
dataset before any modeling: understanding its shape, quality, and
structure so that modeling decisions are grounded in what the data
actually looks like rather than in assumptions. Skipping EDA is a common
source of downstream failures -- a model trained on data with an
unnoticed data-quality issue will often still "work" in the sense of
producing output, while being quietly wrong.

Data quality checks come first: missing values (and whether they are
missing completely at random, missing at random given other observed
variables, or missing not at random -- which determines whether
imputation is even valid), duplicate records, inconsistent categorical
encodings (e.g. "NY", "New York", "ny" all meaning the same thing), and
type mismatches (a numeric column stored as text due to a stray
non-numeric value) all need to be found and resolved before they silently
corrupt an analysis or model.

Univariate analysis examines one variable at a time: histograms and box
plots reveal distribution shape, skew, and outliers for numeric
variables; bar charts reveal the frequency and balance of categories for
categorical variables. A heavily imbalanced categorical target (e.g. 95%
of a binary label in one class) is a critical finding at this stage,
since it changes which evaluation metrics are meaningful later (accuracy
becomes close to useless; precision, recall, and F1, or a metric like
PR-AUC, become necessary).

Bivariate and multivariate analysis examines relationships between
variables: a correlation matrix or pairwise scatter plots for numeric
variables, and grouped summary statistics or contingency tables for
categorical-versus-numeric or categorical-versus-categorical
relationships. High correlation between two candidate input features
(multicollinearity) is worth flagging before modeling, since it can make
some models' coefficients unstable and hard to interpret, even if it
does not necessarily hurt raw predictive accuracy.

Outlier handling requires judgment, not a mechanical rule: an outlier
might be a data-entry error (safe to correct or remove), a genuinely rare
but valid observation (removing it would bias the model against a real
phenomenon), or the exact signal the analysis is meant to find (e.g.
fraud detection, where "outliers" are the target class) -- so the right
handling of an outlier depends entirely on domain context, not a
one-size-fits-all statistical threshold like "more than 3 standard
deviations from the mean."
