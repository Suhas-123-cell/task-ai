# Concept Learning and the General-to-Specific Ordering

Concept learning is the task of inferring a boolean-valued function from
training examples of its input and output. Formally, given a set of training
examples of some target concept c, the learner is asked to output a
hypothesis h from a hypothesis space H that best approximates c over the
instance space X.

Each hypothesis in H can be represented as a conjunction of constraints on
the instance attributes. Each constraint may be a specific value, "?"
(any value is acceptable), or "0" (no value is acceptable). The most
general hypothesis is the one where every constraint is "?"; the most
specific hypothesis (the one satisfied by no instance) has every
constraint set to "0".

The general-to-specific ordering is a partial order over H: hypothesis h1
is more general than or equal to h2 if every instance satisfying h2 also
satisfies h1. This ordering underlies both the FIND-S algorithm and the
CANDIDATE-ELIMINATION algorithm.

FIND-S starts with the most specific hypothesis and generalizes it just
enough to cover each new positive training example, ignoring negative
examples entirely. It is efficient but cannot detect whether it has
learned a consistent concept, cannot detect noisy or inconsistent data,
and typically finds only one of many hypotheses consistent with the
training data.

CANDIDATE-ELIMINATION overcomes some of these limitations by maintaining a
version space -- the set of all hypotheses in H consistent with the
observed training examples -- represented compactly by its most general
boundary (G) and most specific boundary (S). Every hypothesis in the
version space lies between some member of S and some member of G in the
general-to-specific ordering. A new positive example specializes members
of G that are inconsistent with it and generalizes members of S; a new
negative example generalizes members of G and specializes members of S.

The inductive bias of a learner is the set of assumptions that, together
with the training data, deductively justify its classifications of unseen
instances. Without an inductive bias -- for example, if H is the power set
of the instance space -- a learner can do no better than rote memorization,
because a fully expressive hypothesis space is equivalent to no bias at
all and yields no generalization beyond the observed examples. This is a
central and often-overlooked idea: bias is not a flaw to be removed, it is
the necessary ingredient that makes generalization possible.
