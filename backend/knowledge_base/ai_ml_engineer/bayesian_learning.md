# Bayesian Learning

Bayesian learning provides a probabilistic framework for reasoning about
which hypothesis is most likely given observed data, and for combining
prior knowledge with observed data in a principled way. The central tool
is Bayes' theorem:
P(h|D) = P(D|h) * P(h) / P(D)
where P(h) is the prior probability of hypothesis h, P(D|h) is the
likelihood of observing data D given h holds, and P(h|D) is the posterior
probability of h after observing D.

The Maximum A Posteriori (MAP) hypothesis is the h in H that maximizes
P(h|D), i.e. h_MAP = argmax_h P(D|h) P(h). If we further assume a uniform
prior over H, MAP reduces to the Maximum Likelihood (ML) hypothesis,
h_ML = argmax_h P(D|h). Many familiar learning algorithms can be
re-derived as MAP or ML estimation under specific assumptions -- for
example, minimizing sum-of-squared-error is equivalent to finding the ML
hypothesis under the assumption that training data is corrupted by
independent, zero-mean Gaussian noise.

The Naive Bayes classifier applies Bayes' theorem with a strong
simplifying (and usually false, but empirically often "good enough")
assumption: the attributes of an instance are conditionally independent
given the target class. This reduces the classifier to:
v_NB = argmax_vj P(vj) * product over i of P(ai | vj)
which requires estimating only P(vj) and P(ai|vj) for each attribute
value and class, rather than the full joint distribution -- a massive
reduction in the number of parameters that must be estimated from limited
data, which is exactly why the "naive" independence assumption is
tolerated: it trades statistical bias for a large reduction in variance.

Bayesian belief networks (Bayes nets) relax the full independence
assumption of naive Bayes, instead encoding conditional independence
assumptions among subsets of variables via a directed acyclic graph, with
each node storing a conditional probability table given its parents. This
allows more expressive joint distributions to be represented and reasoned
over tractably. The Minimum Description Length (MDL) principle offers a
Bayesian-flavored justification for preferring shorter hypotheses: it
recasts h_MAP as the hypothesis that minimizes the description length of
the hypothesis plus the description length of the data given the
hypothesis, formalizing Occam's razor in information-theoretic terms.
