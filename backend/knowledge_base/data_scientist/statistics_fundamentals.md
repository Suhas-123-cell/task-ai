# Statistical Fundamentals for Data Science

Descriptive statistics summarize a dataset without making claims about a
broader population: mean and median describe central tendency (mean is
sensitive to outliers, median is robust to them, so a large gap between
the two is itself a signal of skew or outliers), variance and standard
deviation describe spread, and skewness/kurtosis describe the shape of
the distribution's tails and asymmetry.

Inferential statistics, by contrast, use a sample to make a claim about a
population the analyst cannot fully observe. A hypothesis test starts
from a null hypothesis (typically "no effect" or "no difference") and
asks how likely the observed data (or something more extreme) would be if
the null hypothesis were true -- that probability is the p-value. A
common but important misconception: the p-value is not the probability
that the null hypothesis is true, and a small p-value does not by itself
establish that an effect is large or practically important, only that it
is unlikely to be pure chance given the model's assumptions -- statistical
significance and practical significance are different questions, and a
large enough sample size can make a practically meaningless effect
statistically significant.

The choice of test depends on the data and question: a t-test compares
means between two groups (assuming approximately normal data, or relying
on the Central Limit Theorem for large samples); a chi-squared test
checks whether categorical variables are associated; ANOVA generalizes
the t-test to compare means across more than two groups. Regardless of
test, multiple comparisons inflate the false-positive rate -- running 20
independent tests at a 5% significance threshold will, by chance alone,
produce roughly one "significant" result even if nothing is actually
different -- which is why corrections like Bonferroni or controlling the
false discovery rate matter whenever many hypotheses are tested at once
(e.g. many candidate features, many A/B test metrics).

Confidence intervals communicate the uncertainty of an estimate directly:
a 95% confidence interval for a mean means that if the same sampling and
estimation procedure were repeated many times, about 95% of the resulting
intervals would contain the true population value -- it is a statement
about the reliability of the estimation procedure across repetitions, not
a 95% probability that the true value lies in this one particular
computed interval. Reporting an interval alongside a point estimate is
almost always more honest and more useful than the point estimate alone.
