# Computational Learning Theory and PAC Learning

Computational learning theory asks precise, quantitative questions about
learning: how many training examples are needed to learn a hypothesis
with a guaranteed bound on its error, and how does this number grow with
the complexity of the hypothesis space?

The Probably Approximately Correct (PAC) learning framework formalizes
this. A concept class C is PAC-learnable by a learner L using hypothesis
space H if, for any target concept in C, any distribution over the
instance space, any error bound epsilon (0 < epsilon < 1/2), and any
confidence bound delta (0 < delta < 1/2), the learner will, with
probability at least (1 - delta), output a hypothesis h with true error at
most epsilon, given a number of training examples polynomial in 1/epsilon,
1/delta, and the size of the concept representation, and with
computation time also polynomial in these quantities.

For the consistent-learner case (a learner that always outputs a
hypothesis perfectly consistent with the training data), a general sample
complexity bound can be derived purely from the size of the hypothesis
space: to guarantee that any consistent hypothesis has true error at most
epsilon with probability at least (1 - delta), it suffices to see
m >= (1/epsilon) * (ln|H| + ln(1/delta)) training examples. This bound
formalizes something intuitive: larger, more expressive hypothesis spaces
(bigger |H|) require proportionally more data to rule out
"accidentally consistent but wrong" hypotheses -- the same
bias-variance tradeoff that appears throughout machine learning, here
made precise.

For infinite hypothesis spaces (e.g. linear separators over the reals),
|H| is infinite and the above bound is vacuous, so sample complexity is
instead bounded using the Vapnik-Chervonenkis (VC) dimension of H -- the
size of the largest set of instances that H can shatter (label in every
possible way). A hypothesis space with VC dimension d requires roughly
O((1/epsilon) * (d * log(1/epsilon) + log(1/delta))) examples for PAC
learnability, connecting a purely combinatorial property of the
hypothesis space to its sample efficiency, and explaining, for instance,
why a linear classifier over a huge feature space still generalizes
reasonably well given enough (but not exorbitant) data.
