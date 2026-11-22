# Limitations

## Disclaimer

Every AutoResearch method is a search, and how a search is run changes what it finds. The strategy,
the schedule, the budget, the skill and the LLM all shape the result. No setting of them is known to be
best for every problem, and that holds for a custom configuration as much as for a preset. evoloop is
infrastructure for running different kinds of search and for recording what each one did. It does not
guarantee what any of them finds.

The agents add variability of their own. An LLM does not return the same proposal twice, and its
behaviour differs between models and between versions of a model. Two runs of the same search with the
same settings try different designs and can end in different places.

Treat the result of a search as a candidate. Retrain it, score it on held-out data, and compare it
with a baseline before relying on it.

## Limitations of the method

- The search optimizes what the evaluator reports. If the validation metric can be raised without
improving the model, for example through leakage between training and validation data, an agent may
find that route. Check the designs at the top of the leaderboard, not only their scores.
- The best of many noisy scores is optimistic. The leader of several hundred training runs is partly
the luckiest. The noise floor and the re-checks of the leader reduce this and do not remove it.
[Comparing scores](comparable.md)
- The validation set is reused. After hundreds of evaluations against one validation set, its score
no longer estimates how a design generalizes. Test-set results are withheld from the agents and from
selection for this reason, and they are the figure to report.
- A budget covers a small part of the design space. Tens to hundreds of evaluations cannot be
exhaustive. A different strategy or schedule spends them in a different part of the space.
[Parent selection](parents.md) · [Schedule](schedule.md)
- Only the marked code can change. What a search can find is bounded by what you marked and by the
frozen code around it. An agent cannot restructure code outside the marked blocks.
- Guidance is advice. Notes, skills, `objective.constraints`, `space.forbidden` and `space.must_keep`
are text that an agent can set aside. Only `limits`, `space.forbidden_terms` and the set of open blocks
are enforced by code.
- Novelty is judged on code before training. How different a proposal is from earlier designs is
measured on its text. What a model does is known only after it is trained, and only if the evaluator
reports where its errors fall.
- Early stopping assumes early progress predicts the final score. Where it does not, designs that
start slowly are lost. [Early stopping](early-stopping.md)
- The noise floor is yours to supply. evoloop does not measure it. Too low and noise is taken for
progress; too high and real gains are ignored. [Measure the noise floor](noise.md)
- Agent cost grows with the size of the marked code. A writer is sent the parents' code and returns
what it changes. The cost estimate in the plan is approximate. [Budget and cost](cost.md)
