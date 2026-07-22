# Artificial Neural Networks

Artificial neural networks approximate real-valued, discrete-valued, and
vector-valued target functions using networks of interconnected units,
each computing a (typically nonlinear) function of a weighted sum of its
inputs. They are especially well suited to problems with noisy,
high-dimensional sensory input, such as raw pixels or audio, where the
target function may be poorly understood and where fast evaluation of the
learned function matters more than human readability of the result.

A single perceptron computes o = 1 if (w . x + b) > 0 else -1 (or 0),
where w is a weight vector learned from training data. A perceptron can
only represent linearly separable functions. Stacking layers of units with
differentiable nonlinear activations (sigmoid, tanh, ReLU) yields a
multilayer network capable of representing arbitrary boolean functions and,
with continuous activations, arbitrary continuous functions (given enough
hidden units) -- this is the universal approximation property.

Backpropagation trains multilayer networks by gradient descent on a
squared-error (or cross-entropy) loss surface. It works in two passes: a
forward pass computes the network's output for a given input, and a
backward pass computes the error at the output layer and propagates it
backward through the network using the chain rule, computing the gradient
of the error with respect to every weight. Weights are then updated in the
direction that reduces error: w_i <- w_i - eta * dE/dw_i, where eta is the
learning rate.

Because the error surface of a multilayer network can have many local
minima, backpropagation is not guaranteed to find a globally optimal set
of weights; in practice this is mitigated by techniques such as momentum,
adaptive learning rates (Adam, RMSProp), weight initialization schemes,
and simply the fact that in high-dimensional weight spaces, poor local
minima are comparatively rare.

Overfitting is again the central practical risk: a network with enough
hidden units and enough training epochs can memorize the training set.
Common mitigations are weight decay (L2 regularization), dropout
(randomly zeroing a fraction of unit activations during training so the
network cannot rely on any single unit), early stopping using a
validation set, and data augmentation. Convolutional layers add a further
inductive bias appropriate for grid-structured data like images: local
receptive fields and weight sharing across spatial locations dramatically
reduce the number of free parameters compared to a fully connected layer,
which is why CNNs generalize far better than dense networks on vision
tasks with limited data.
