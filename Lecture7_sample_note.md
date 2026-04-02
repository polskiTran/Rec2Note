# Lecture7 022622 - Value and Q-Functions in MDPs and Introduction to Dynamic Programming

## Summary

### Overview
This lecture provides a crucial correction regarding the optimal policy in deterministic environments, emphasizing that it's inherently deterministic while policy evaluation still involves averaging for stochastic policies. It then introduces the Q-function, defining its relationship with the value function and extending these concepts to optimal policies in both deterministic and non-deterministic settings. The lecture highlights the practical challenges of solving Markov Decision Processes (MDPs), such as large state spaces, cycles, and the 'credit assignment problem.' Finally, it transitions to dynamic programming as a foundational framework for reinforcement learning, outlining the iterative process of policy evaluation and improvement, and defining on-policy learning.

### Key Points
- In a deterministic environment, the optimal policy itself is deterministic, always choosing the single best action that maximizes future value, though evaluating a *stochastic* policy still involves averaging over its actions.
- The Q-function assigns a 'Q-value' to each state-action pair (s, a), representing the expected total discounted reward from taking that specific action in that state and subsequently following a given policy.
- The value of a state (V(s)) is directly related to the Q-function; it's the expected Q-value of that state, averaged over all possible actions taken from that state according to the current policy.
- For non-deterministic environments, the calculation of Q and V functions must account for the joint probability distribution of next states and rewards, as both transitions and rewards are now random.
- A key challenge in reinforcement learning is the 'credit assignment problem,' which involves attributing credit or blame to earlier decisions when rewards are often delayed or sparse.
- Reinforcement Learning is considered 'approximate dynamic programming,' aiming to find practical, computationally feasible methods to solve MDPs.
- Dynamic programming involves an iterative cycle of policy evaluation (updating value estimates for a given policy) and policy improvement (updating the policy based on improved value estimates).
- The policy evaluation algorithm iteratively updates state values using the Bellman equation until the estimated values converge to the true value function for the given policy.
- On-policy learning refers to situations where the agent learns about a policy by using experience generated from interactions with the environment by that same policy.
### Topics
- [Correction on Optimal Policy for Deterministic Environments] Clarified that in a deterministic environment, the optimal policy is to always take the single best action to maximize future value. The expectation for a policy's value function (V_pi) is still over the actions dictated by the policy, but the subsequent state (S') is deterministically determined by (S,A).
- [Introduction to Q-Function] Defined the Q-function (Q(s,a)) as a function that assigns a Q-value to each state-action pair, representing the expected cumulative discounted reward from taking action 'a' in state 's' and then following a given policy.
- [Value Function vs. Q-Function (Deterministic Environment)] Contrasted the state value function V(s) with the state-action value function Q(s,a). V(s) is the average of Q(s,a) over all actions 'a' from state 's' according to the policy. Q(s,a) for a deterministic environment is the immediate reward R(s,a) plus the discounted value of the resulting state S'.
- [Optimal Value and Q-Functions (Deterministic Environment)] Introduced the Bellman optimality equations, where the optimal value V*(s) is the maximum Q*(s,a) over all actions 'a', and Q*(s,a) is the immediate reward plus the discounted optimal value of the next state (maximized over future actions).
- [Non-Deterministic Environments (Q-Function)] Extended the definitions to non-deterministic environments where state transitions and rewards are governed by a joint probability distribution P(s', R | s, a). Q_pi(s,a) is then the expected value of (immediate reward + discounted future value) averaged over all possible next states and rewards.
- [Illustrative Example: Calculating State Values] Presented a simple deterministic, acyclic environment with six states and a terminal state to demonstrate the recursive calculation of state values (V_pi) for a given stochastic policy, starting from the terminal state and working backward.
- [Representing Policies] Discussed various ways to represent a policy: tabular representations, greedy policies (taking the action with the highest Q-value), stochastic greedy policies (e.g., using a softmax function and roulette wheel selection to introduce exploration), and parameterized functions like neural networks.
- [Challenges in Markov Decision Processes (MDPs)] Outlined key problems that make solving MDPs difficult: the presence of cycles (leading to potentially infinite trajectories), computational intractability for large state spaces, the credit assignment problem (delayed or sparse rewards), and often unknown transition and reward functions.
- [Dynamic Programming] Introduced dynamic programming as the theoretical foundation for solving MDPs, stating that reinforcement learning is essentially 'approximate dynamic programming' designed for practical implementation.
- [Policy Evaluation Algorithm] Described an iterative policy evaluation algorithm, similar to the Gauss-Seidel method, which initializes state values (e.g., to zero) and then repeatedly updates them using the Bellman equation for a given policy until the changes (delta) in value estimates fall below a specified epsilon (convergence criterion).
- [On-Policy Learning] Defined on-policy learning as a method where the policy being evaluated and improved is also the policy that is used to generate the experience or trajectories from the environment.
### Key Terms
- [Optimal Policy (Deterministic Environment)] A policy that, in a deterministic environment, always selects the single best action at each state, leading to the state with the highest future value, thus maximizing total discounted reward.
- [Q-function (Q(s,a))] A function that assigns a Q-value to each state-action pair (s,a), representing the expected total discounted reward obtained by taking action 'a' in state 's' and then subsequently following a specific policy.
- [Q-value] The numerical output of the Q-function for a given state-action pair, indicating the estimated long-term desirability or total expected discounted reward of taking that specific action in that state.
- [Value Function (V(s))] A function that assigns a value to each state 's', representing the total expected discounted reward obtained from starting in state 's' and following a specific policy.
- [Optimal Value Function (V*(s))] The maximum possible expected total discounted reward obtainable from state 's' by following an optimal policy.
- [Optimal Q-Function (Q*(s,a))] The maximum possible expected total discounted reward obtained by taking action 'a' in state 's' and then following an optimal policy for all subsequent steps.
- [Trajectory] A sequence of observed (state, action, reward) tuples over time, representing an agent's experience in the environment (e.g., S_t, A_t, R_{t+1}, S_{t+1}, A_{t+1}, R_{t+2}, ...).
- [Softmax Function] A mathematical function that converts a vector of real numbers (e.g., Q-values) into a probability distribution, where values with higher magnitudes are assigned higher probabilities, used in stochastic greedy policies for exploration.
- [Roulette Wheel Selection] A method for probabilistically selecting actions, where each action is assigned a 'slice' on a conceptual roulette wheel proportional to its probability (e.g., derived from softmax Q-values), and an action is chosen by spinning the wheel.
- [Credit Assignment Problem] The fundamental challenge in reinforcement learning of determining which past actions or states were responsible for a future, often delayed or sparse, reward or penalty.
- [Dynamic Programming] A class of algorithms used to solve complex problems by breaking them down into simpler subproblems. In the context of MDPs, it refers to methods for computing optimal policies given a perfect model of the environment; reinforcement learning is considered approximate dynamic programming.
- [Policy Evaluation] The process within dynamic programming (and reinforcement learning) of estimating the value function (V_pi or Q_pi) for a given fixed policy pi.
- [Policy Improvement] The process within dynamic programming (and reinforcement learning) of deriving a new, often better, policy from the current value function estimates.
- [On-Policy Learning] A type of reinforcement learning where the agent learns about the value function of a policy (or improves it) using data generated by following that exact same policy during exploration.
## Student Questions
- Q: (00:44:53) Is the method of evaluating policy described (running a long trajectory or multiple trials) similar to a Monte Carlo simulation?
    - A: Yes, absolutely. The Monte Carlo version would involve starting from a random state, estimating its value, then resetting the system and repeating this process many times from different initial states. For example, if there are 10 states, one might decide to run 20 simulations from each initial state, leading to a total of 200 simulations. Each simulation would need to run for a substantial number of steps (e.g., 100 steps) to sufficiently capture the discounted future rewards, even with a strong discounting factor. This makes the Monte Carlo approach, while conceptually valid, very tedious and computationally intensive. The alternative, running one extremely long trajectory, would also be a way to estimate values, but it differs from the typical Monte Carlo method which relies on multiple independent trials.

## Study Questions

- Q: (00:00:11) [factual] What was the correction made by the lecturer regarding the optimal policy in a deterministic environment?
    - A: In a deterministic environment, the optimal policy itself is deterministic, meaning there will always be a single best action to take in every state. The expectation over the policy is still present in the value function (V_pi) during the search process if the policy itself is stochastic, but the *optimal* policy for a deterministic environment does not require averaging over environmental transitions or rewards.

- Q: (00:31:00) [conceptual] Explain the relationship between the Value Function V(s) and the Q-function Q(s, a) as described by the lecturer.
    - A: The Q-function Q(s, a) quantifies the discounted expected gain you can achieve by taking a specific action 'A' in the current state 'S'. The Value Function V(s) represents the total discounted expected gain you can expect from being in a particular state 'S', which is derived by averaging the Q-values of all possible actions from that state, weighted by their probabilities under the current policy.

- Q: (00:15:11) [conceptual] How is the joint probability distribution P(S', R | S, A) used to describe a non-deterministic environment, and why is it generally not factorized into separate probabilities for state and reward?
    - A: P(S', R | S, A) describes the probability of transitioning to a next state S' and receiving a reward R, given the current state S and chosen action A. It is generally not factorized into P(S' | S, A) * P(R | S, A) because the reward received for an action is often dependent on the specific state the agent ends up in, meaning the reward and next state are not independent events.

- Q: (00:40:15) [factual] What is a 'trajectory' in the context of reinforcement learning, and how might one estimate state values from it?
    - A: A trajectory is a sequence of states, actions, and rewards over time (e.g., State -> Action -> Reward -> Next State -> Action -> Reward...). One way to estimate values from a trajectory is to track the accumulated discounted reward from the first time a particular state is encountered within that trajectory.

- Q: (01:05:12) [critical] Describe the 'credit assignment problem' and its significance in reinforcement learning.
    - A: The credit assignment problem is the challenge of determining which past actions or decisions are responsible for a delayed or sparse reward. For example, in a chess game, the reward (winning/losing) only appears at the end, making it difficult to assign credit or blame to individual moves made much earlier. This problem is significant because it complicates the learning process, as the agent needs to understand the long-term consequences of its actions, not just immediate rewards.

- Q: (01:06:08) [conceptual] The lecturer states that reinforcement learning is 'approximate dynamic programming'. Explain what makes full-fledged dynamic programming intractable and how RL addresses this.
    - A: Full-fledged dynamic programming becomes intractable due to several factors: the presence of cycles with non-zero rewards leading to infinite trajectories, the computational prohibitive nature of calculating values for a large number of states, the sparse or delayed nature of rewards (credit assignment problem), and the common lack of knowledge about the environment's transition and reward functions. Reinforcement learning addresses this by employing approximate methods that learn through interaction and experience, rather than requiring a complete model or exhaustive calculation.

- Q: (01:12:34) [factual] Outline the general iterative policy evaluation (IPE) algorithm.
    - A: The IPE algorithm aims to evaluate a given policy 'pi' by iteratively updating state values. It initializes all state values to zero. In a loop, it sets a 'delta' to zero. For each state S, it stores the current value (vprev), updates the state's value V(S) using the Bellman equation (averaging over actions and their subsequent rewards and discounted next state values), and updates 'delta' with the maximum absolute change between the new and old V(S) across all states. This loop repeats until 'delta' is less than a small threshold epsilon, indicating convergence.

- Q: (01:18:23) [factual] What is 'on-policy learning'?
    - A: On-policy learning refers to a method where the policy being evaluated or improved is also the policy used to generate the data (i.e., interactions, experiences, or trajectories) from the environment. The agent learns from its own actions taken under the current policy.

