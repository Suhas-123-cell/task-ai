# Decision Tree Learning

Decision tree learning approximates discrete-valued target functions by a
tree in which each internal node tests an attribute, each branch
corresponds to a possible value of that attribute, and each leaf assigns a
classification. Decision trees are attractive because the learned
hypothesis can be re-expressed as a set of if-then rules, which improves
human readability.

The core algorithm (ID3 and its successor C4.5) builds the tree top-down,
at each step selecting the attribute that best splits the remaining
training examples using a greedy, no-backtracking search. "Best" is
measured by information gain, which is defined in terms of entropy.

Entropy of a collection S with respect to a boolean classification is:
Entropy(S) = -p_plus * log2(p_plus) - p_minus * log2(p_minus)
where p_plus and p_minus are the proportions of positive and negative
examples in S. Entropy is 0 when all members belong to the same class and
1 when the collection is evenly split, so entropy measures the impurity
of a collection.

Information Gain of an attribute A relative to a collection S is the
expected reduction in entropy caused by partitioning S according to A:
Gain(S, A) = Entropy(S) - sum over each value v of A of
(|S_v| / |S|) * Entropy(S_v)
ID3 selects, at each node, the attribute with the highest information
gain among the attributes not yet used on the path from the root.

A key failure mode is overfitting: as the tree grows deeper it can start
fitting noise or idiosyncrasies of the training set, hurting accuracy on
unseen data even as training accuracy keeps improving. Two standard
countermeasures are pre-pruning (stop growing the tree early, e.g. via a
minimum information-gain threshold or a maximum depth) and post-pruning
(grow the full tree, then remove subtrees whose removal does not hurt
accuracy on a held-out validation set -- typically the more effective
approach in practice, e.g. reduced-error pruning or rule post-pruning).

Random forests and gradient-boosted trees (e.g. XGBoost) build on this
foundation by combining many trees: random forests average many
decorrelated trees (each trained on a bootstrap sample with a random
subset of features considered at each split) to reduce variance, while
boosting trains trees sequentially, each one correcting the residual
errors of the ensemble so far, which reduces bias.
