# Instance-Based Learning

Instance-based methods, unlike decision trees or neural networks, do not
construct an explicit general hypothesis at training time. Instead they
store the training examples (or a compact representation of them) and
defer generalization until a new query instance must be classified --
sometimes called "lazy learning" as opposed to the "eager learning" of
methods that build a model upfront.

The k-Nearest Neighbor (k-NN) algorithm classifies a new instance by
retrieving the k training examples closest to it under some distance
metric (commonly Euclidean distance over a real-valued feature space) and
assigning the majority class among those neighbors (or, for regression,
averaging their target values, sometimes weighted by inverse distance).
Because k-NN considers the entire instance space at query time rather than
committing to a single global hypothesis, it can represent highly complex,
non-linear target functions -- effectively its hypothesis space is the
space of all possible partitions of the instance space induced by the
stored examples and the choice of k.

A well-known weakness is sensitivity to irrelevant attributes: because
distance is computed over all features equally, features that are
irrelevant to the target concept can dominate the distance calculation and
badly distort which neighbors are actually "close" in a meaningful sense.
This motivates feature scaling, feature selection, or learned distance
metrics before applying k-NN. Another weakness is the cost of prediction,
since a naive implementation must compute distance to every stored
training example for every query; this is addressed in practice with
spatial index structures (kd-trees, ball trees) or approximate nearest
neighbor libraries for high-dimensional embeddings.

Locally weighted regression generalizes k-NN by fitting a simple
parametric function (e.g. a local linear model) using only the training
examples near the query point, weighted by their distance to the query --
producing a global function that is piecewise approximated locally,
which can capture more nuance than a single global linear or polynomial
fit while remaining far cheaper to fit than a fully non-parametric global
model. This same "compare against stored examples in embedding space" idea
underlies modern dense retrieval: encoding text into vector embeddings and
retrieving nearest neighbors by cosine or Euclidean distance is the
direct descendant of instance-based learning applied to unstructured
data, and is the retrieval mechanism used by this project's own RAG
pipeline.
