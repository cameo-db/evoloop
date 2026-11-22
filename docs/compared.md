# Comparison with other AutoResearch methods

evoloop belongs to a group of systems in which an LLM proposes changes to code and an automatic
evaluation decides what is kept. This page places it among them, lists the mechanisms it takes from
earlier work with their sources, and says where it differs and where it falls short.

## Related systems

| System | Searches over | How the next candidate is chosen |
|---|---|---|
| FunSearch ([Romera-Paredes et al., 2024](#ref-funsearch)) | one function inside a fixed program skeleton | islands of programs, sampled by score, with the weaker islands reset at intervals |
| AlphaEvolve ([Novikov et al., 2025](#ref-alphaevolve)) | marked regions of a codebase | a program database that combines a MAP-Elites archive with islands; an ensemble of LLMs writes diffs |
| OpenEvolve ([Sharma, 2025](#ref-openevolve)) | as AlphaEvolve | an open-source implementation of AlphaEvolve |
| ShinkaEvolve ([Lange et al., 2025](#ref-shinka)) | programs | parent sampling that balances exploration and exploitation, rejection of proposals too similar to earlier ones, and a bandit over the LLMs |
| AIDE ([Jiang et al., 2025](#ref-aide)) | machine-learning scripts | a tree of solutions, in which a policy picks the node to improve next |
| The AI Scientist ([Lu et al., 2024](#ref-aiscientist)) | whole research projects: idea, code, experiments, paper, review | an archive of earlier ideas and their reviews |
| autoresearch ([Karpathy, 2026](#ref-autoresearch)) | one training script for a small language model | an agent edits the script, trains for a fixed five minutes, and keeps the change if the validation metric improved |
| evoloop | marked blocks of machine-learning code: architecture, training recipe, hyperparameters | lineages by default; an archive, a tournament, a Pareto front or greedy selection as alternatives |

LLM-written edits were used for architecture search before these systems, for example in EvoPrompting
([Chen et al., 2023](#ref-evoprompting)).

## Evaluation cost

FunSearch and AlphaEvolve search over programs that are scored in seconds. They can afford thousands
to millions of evaluations, and a score is the same every time it is measured. A search over model
architectures is in a different regime.

| | Program search (FunSearch, AlphaEvolve) | Architecture search |
|---|---|---|
| One evaluation | seconds, on a CPU | minutes to hours, on a GPU |
| Evaluations in a search | thousands to millions | tens to hundreds |
| The score | exact | noisy: two fits of one model differ |
| A wrong turn | costs little | costs a real share of the budget |

evoloop takes the mechanisms of the program-search systems and weights them for the second regime.
With a few hundred evaluations, what matters most is which design is tried next, that a noisy score is
not mistaken for a gain, and that the researcher can change course when the results call for it.

## Borrowed mechanisms

Every mechanism below is an option in evoloop. [Options and presets](menu.md) lists the settings.

### From FunSearch

| Mechanism | In evoloop | How it differs here |
|---|---|---|
| Evolve one function inside a fixed skeleton | `EVOLVE-BLOCK` markers in `base/`; the rest is frozen and hashed | several blocks, each with a kind and a role, so the space can be opened role by role |
| Islands, with the weaker half reset at intervals | `strategy.islands`, `strategy.reset_every` | off by default: islands split a small budget thinly |
| Programs kept apart by what they do | `strategy.descriptors: [behaviour]` | grouped by where a trained model's errors fall, by correlation and not by an exact match |

### From AlphaEvolve

| Mechanism | In evoloop | How it differs here |
|---|---|---|
| A program database: an archive on islands | `strategy.mechanism: archive` with `strategy.islands` | cells are family, size, behaviour or any reported metric |
| A fast and a strong model writing together | `agents.writer_mix` | any models and shares; the report compares their designs |
| Edits as diffs | `variation.edit_format: diff` | an edit applies only if its text occurs exactly once in the block |
| An evaluation cascade | the quick check, then `evaluation.ladder` | successive halving inside one job, not a set of cheaper tests |
| Several objectives | `strategy.mechanism: pareto` | two metrics, not many |
| Instructions that evolve | `variation.approaches` | one line per slot varies, with a record of what it led to |

### From other methods

| Method | Mechanism | In evoloop | How it differs here |
|---|---|---|---|
| NEAT ([Stanley and Miikkulainen, 2002](#ref-neat)) | new species protected while young | `strategy.mechanism: lineage` | lineages of designs, not genomes; the default |
| MAP-Elites ([Mouret and Clune, 2015](#ref-mapelites)) | the best of each kind, on a grid | `strategy.mechanism: archive` | the grid's axes are yours to choose |
| Regularized evolution ([Real et al., 2019](#ref-regevo)) | tournament selection with aging | `strategy.mechanism: tournament` | as published, at smaller scale |
| NSGA-II ([Deb et al., 2002](#ref-nsga2)) | selection from the non-dominated front | `strategy.mechanism: pareto` | two metrics; no crowding distance |
| Successive halving ([Jamieson and Talwalkar, 2016](#ref-sha)), Hyperband ([Li et al., 2018](#ref-hyperband)), ASHA ([Li et al., 2020](#ref-asha)) | weak runs stopped by rank | `evaluation.ladder` | within one job, charged by the share of the run used |
| TPE ([Bergstra et al., 2011](#ref-tpe)) | Bayesian choice of hyperparameters | `variation.settings_by: tpe` | a small implementation; each setting modelled alone |
| Network morphism and weight sharing | a child starts from its parent's weights | `evaluation.inherit_weights` | the evaluator decides what to load |

## Additions

Four things are not in the methods above.

- A search can be changed while it runs. Most settings change without a restart, each change is
  recorded with who made it, and because a strategy keeps no state, even the strategy can change.
  [Monitor and steer a search](steering.md)
- Scores are compared only when they mean the same thing. You state how noisy your score is, and a
  difference below that counts as none. Lengthening training starts a new comparison period, so old
  and new scores are never ranked together. [Comparing scores](comparable.md)
- The goal of a search is set apart from how to search. A skill carries the settings and the guidance
  for one kind of goal, and can be edited. [Choose a skill and a run type](which-search.md)
- The agents are audited. Every call is recorded with what the agent forecast and what happened, and
  a scorecard says whether each role earns its cost. [Audit the agents](auditing.md)

## Limitations

- Throughput. There is no tier of cheap stand-in evaluations (a smaller dataset or model) with
  promotion to the real task. The ladder stops weak designs early within the real task, which
  stretches a budget a few-fold, not a thousandfold.
- No guarantee. Like every method on this page, evoloop is a search, and how a search is run changes
  what it finds. [Limitations](limitations.md)
- Novelty before training. How different a proposal is from what has been tried is measured on its
  code. What a model does is known only after it is trained.
- Prompt evolution. Only one line of the writer's instructions varies.
- Scope of an edit. A writer changes marked blocks. It cannot restructure the frozen code around them.

## Approximating other methods

| To search like | Set |
|---|---|
| FunSearch | `strategy.mechanism: archive`, `strategy.descriptors: [behaviour]`, `strategy.islands: 4`, `strategy.reset_every: 40`, `harness.level: minimal` |
| AlphaEvolve | `strategy.mechanism: archive` on `strategy.islands: 3`, `agents.writer_mix`, `variation.edit_format: diff`, `variation.approaches: evolve`, `evaluation.ladder` |
| Regularized evolution | `strategy.mechanism: tournament`, a schedule of local moves only |
| BOHB ([Falkner et al., 2018](#ref-bohb)) | `run.skill: settings-tuning-bayesian` with `evaluation.ladder` |
| Hill climbing | `strategy.mechanism: greedy` |

These resemble the methods. They are not reimplementations, and they need budgets in the hundreds to
behave as described.

## References

1. <span id="ref-funsearch"></span>Romera-Paredes, B., Barekatain, M., Novikov, A., et al. Mathematical discoveries from program search with large language models. *Nature* 625, 468–475 (2024). [doi:10.1038/s41586-023-06924-6](https://doi.org/10.1038/s41586-023-06924-6)
2. <span id="ref-alphaevolve"></span>Novikov, A., et al. AlphaEvolve: A coding agent for scientific and algorithmic discovery. [arXiv:2506.13131](https://arxiv.org/abs/2506.13131) (2025).
3. <span id="ref-openevolve"></span>Sharma, A. OpenEvolve: an open-source implementation of AlphaEvolve. [github.com/codelion/openevolve](https://github.com/codelion/openevolve) (2025).
4. <span id="ref-shinka"></span>Lange, R. T., Imajuku, Y., Cetin, E. ShinkaEvolve: Towards open-ended and sample-efficient program evolution. [arXiv:2509.19349](https://arxiv.org/abs/2509.19349) (2025).
5. <span id="ref-aide"></span>Jiang, Z., et al. AIDE: AI-driven exploration in the space of code. [arXiv:2502.13138](https://arxiv.org/abs/2502.13138) (2025).
6. <span id="ref-aiscientist"></span>Lu, C., Lu, C., Lange, R. T., Foerster, J., Clune, J., Ha, D. The AI Scientist: Towards fully automated open-ended scientific discovery. [arXiv:2408.06292](https://arxiv.org/abs/2408.06292) (2024).
7. <span id="ref-autoresearch"></span>Karpathy, A. autoresearch. [github.com/karpathy/autoresearch](https://github.com/karpathy/autoresearch) (2026).
8. <span id="ref-evoprompting"></span>Chen, A., Dohan, D. M., So, D. R. EvoPrompting: Language models for code-level neural architecture search. *NeurIPS* (2023). [arXiv:2302.14838](https://arxiv.org/abs/2302.14838)
9. <span id="ref-neat"></span>Stanley, K. O., Miikkulainen, R. Evolving neural networks through augmenting topologies. *Evolutionary Computation* 10(2), 99–127 (2002). [doi:10.1162/106365602320169811](https://doi.org/10.1162/106365602320169811)
10. <span id="ref-mapelites"></span>Mouret, J.-B., Clune, J. Illuminating search spaces by mapping elites. [arXiv:1504.04909](https://arxiv.org/abs/1504.04909) (2015).
11. <span id="ref-regevo"></span>Real, E., Aggarwal, A., Huang, Y., Le, Q. V. Regularized evolution for image classifier architecture search. *AAAI* (2019). [arXiv:1802.01548](https://arxiv.org/abs/1802.01548)
12. <span id="ref-nsga2"></span>Deb, K., Pratap, A., Agarwal, S., Meyarivan, T. A fast and elitist multiobjective genetic algorithm: NSGA-II. *IEEE Transactions on Evolutionary Computation* 6(2), 182–197 (2002). [doi:10.1109/4235.996017](https://doi.org/10.1109/4235.996017)
13. <span id="ref-sha"></span>Jamieson, K., Talwalkar, A. Non-stochastic best arm identification and hyperparameter optimization. *AISTATS* (2016). [arXiv:1502.07943](https://arxiv.org/abs/1502.07943)
14. <span id="ref-hyperband"></span>Li, L., Jamieson, K., DeSalvo, G., Rostamizadeh, A., Talwalkar, A. Hyperband: A novel bandit-based approach to hyperparameter optimization. *Journal of Machine Learning Research* 18(185), 1–52 (2018). [arXiv:1603.06560](https://arxiv.org/abs/1603.06560)
15. <span id="ref-asha"></span>Li, L., Jamieson, K., Rostamizadeh, A., et al. A system for massively parallel hyperparameter tuning. *MLSys* (2020). [arXiv:1810.05934](https://arxiv.org/abs/1810.05934)
16. <span id="ref-tpe"></span>Bergstra, J., Bardenet, R., Bengio, Y., Kégl, B. Algorithms for hyper-parameter optimization. *NeurIPS* (2011).
17. <span id="ref-bohb"></span>Falkner, S., Klein, A., Hutter, F. BOHB: Robust and efficient hyperparameter optimization at scale. *ICML* (2018). [arXiv:1807.01774](https://arxiv.org/abs/1807.01774)
