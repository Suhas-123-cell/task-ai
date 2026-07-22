# Reinforcement Learning

Reinforcement learning addresses the problem of an agent that must learn
a control policy through trial-and-error interaction with an environment,
receiving delayed reward signals rather than labeled examples of correct
behavior. The environment is typically modeled as a Markov Decision
Process (MDP): a set of states S, a set of actions A, a transition
function that gives the probability of moving to state s' after taking
action a in state s, and a reward function r(s, a) giving the immediate
reward for that transition. The Markov property assumes the next state
and reward depend only on the current state and action, not on the full
history.

The agent's objective is to learn a policy pi(s) -> a that maximizes the
expected cumulative discounted reward, V^pi(s) = E[sum over t of
gamma^t * r_t], where gamma in [0, 1) is a discount factor that weighs
near-term reward more heavily than distant reward and ensures the sum
converges over an infinite horizon.

Q-learning is a foundational model-free algorithm: rather than learning
V(s) directly (which would still require knowing the transition function
to select actions), it learns Q(s, a), the expected discounted reward of
taking action a in state s and then behaving optimally thereafter. The
update rule, applied after observing a transition (s, a, r, s'), is:
Q(s, a) <- Q(s, a) + alpha * (r + gamma * max_a' Q(s', a') - Q(s, a))
Under standard conditions (every state-action pair visited infinitely
often, appropriately decaying learning rate alpha), Q-learning converges
to the optimal Q-function regardless of the policy used to generate
training data -- it is "off-policy" in that sense, which is a major
practical advantage.

The exploration-exploitation tradeoff is central: the agent must balance
exploiting actions currently believed best against exploring less-tried
actions that might turn out better. A common simple strategy is
epsilon-greedy action selection: with probability (1 - epsilon) choose
the currently best-known action, and with probability epsilon choose a
random action, often annealing epsilon down over training.

For large or continuous state spaces where a tabular Q(s, a) is
infeasible, the Q-function is approximated with a parametric function
(historically linear functions of hand-crafted features; in modern deep
reinforcement learning, a neural network -- the Deep Q-Network, or DQN,
approach), trading the convergence guarantees of the tabular case for the
ability to generalize across a huge or continuous state space, at the
cost of training stability, which is why DQN required additional
techniques like experience replay and target networks to work reliably.
