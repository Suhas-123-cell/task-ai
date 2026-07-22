# Experimentation and A/B Testing

A/B testing is a controlled experiment used to estimate the causal effect
of a change (a new feature, a different ranking algorithm, a UI variant)
by randomly assigning users or requests to a control group (existing
behavior) and one or more treatment groups (the change), then comparing an
agreed-upon metric between groups. Randomization is what allows a causal
claim ("the change caused the difference") rather than a merely
correlational one, because it ensures -- in expectation, at sufficient
sample size -- that the groups are balanced on every other factor, known
or unknown, that might otherwise confound the comparison.

Before running a test, a power analysis should determine the required
sample size given the minimum effect size worth detecting, the metric's
natural variance, and the desired statistical power (commonly 80%) and
significance level (commonly 5%) -- running a test with too few samples
for the effect size actually expected produces an underpowered test that
will very likely fail to detect a real effect even when one exists, which
is easy to misread as "the change had no effect" rather than "the test
could not have detected this effect reliably."

The choice of a single, pre-registered primary metric (decided before
looking at results) guards against a specific bias: when many metrics are
examined after the fact and the "best-looking" one is reported, at least
one metric will often appear to move favorably by chance alone, even with
no real effect -- the same multiple-comparisons problem that appears in
general hypothesis testing. Guardrail metrics (secondary metrics that
must not regress, e.g. overall latency or an unrelated engagement metric)
are tracked alongside the primary metric specifically to catch harmful
side effects that the primary metric alone would miss.

Common pitfalls include peeking (repeatedly checking results and stopping
the test as soon as significance is reached, which inflates the false
positive rate well above the nominal significance level, since it is
effectively many sequential tests rather than one), novelty effects
(a change performs well briefly simply because it is new and users are
curious, an effect that fades and should be checked for with a
sufficiently long test duration), and network/interference effects
(where a treatment given to one user affects outcomes for other users --
common in social or marketplace products -- which violates the
independence assumption underlying standard A/B test analysis and
typically requires a different randomization unit, e.g. randomizing by
whole geographic market or cluster rather than by individual user).
