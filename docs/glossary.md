# Glossary

The words evoloop uses in a particular sense, in plain terms. Where the docs and the tool's files use
different words for one thing, both are given.

**Agent.** A language model called for one job: writing a design, analysing results, reviewing the
search. See [Agents](agents.md).

**Allowance.** The length of one training run, in whatever unit your evaluator uses (epochs, steps).
The setting is `evaluation.allowance`; the docs usually say *training length*.

**Baseline.** Your code as it stands, scored first, as the reference every gain is measured against.

**Block.** A stretch of your code between `EVOLVE-BLOCK-START` and `EVOLVE-BLOCK-END` markers. Only
blocks can change. A *structure* block holds code; a *params* block holds one dictionary of settings.

**Brief.** `brief.yaml`: the file that says what one search optimizes, what may change, and how much to
spend.

**Budget.** The number of evaluations a search may spend, and separately the dollars its agents may
cost.

**Conductor.** The strategist, when you have chosen to talk to it with `evoloop chat`.

**Controller.** The Python process that runs a search. Not an agent.

**Coordinator.** An optional agent that chooses the kind of move for each slot, in place of the
schedule.

**Crossover.** A design made from two parents of different lineages.

**Design.** One candidate solution: a version of the marked blocks. The tool's files also call it a
*candidate*, with ids like `C7`.

**Evaluation.** One design trained and scored once. The unit the budget is counted in. The tool's
files call each one a *run*, with ids like `R12`.

**Evaluator.** Your script, `adapter/run.py`, that trains one design and writes its score. The tool's
files call it the *adapter*.

**Family.** A label a writer gives a design, such as "dilated CNN". Used to tell kinds of design apart.

**Frozen code.** Everything outside the blocks. It is checked on every start and cannot change during
a search without your say-so.

**Harness.** The set of agent roles that run beside the writers (`harness.level`: `minimal`,
`standard`, `full`). Not to be confused with `harnessed`, the lowest level of autonomy.

**Ladder.** Stopping the weaker designs at several points of a training run.

**Ledger.** The record of every change made to a search while it ran: who, what, when.

**Limit.** A hard bound on something your evaluator reports, such as parameter count. A design outside
it is rejected.

**Lineage.** One design and everything derived from it. Ids like `L3`. A lineage usually stays within
one family, but the two are different things: the family is a label, the lineage is ancestry.

**Local move.** A change to one existing design: an edit, a settings move or an ablation.

**Mode.** The kind of move a slot makes: new, novel, crossover or local. (The word is also used for the
strategist's setting, `strategist.mode`: off, advise or act.)

**Noise floor.** How much the score differs between two runs of the same design. A difference smaller
than this counts as none. [Measure the noise floor](noise.md).

**Period.** A stretch of a search in which scores are comparable. Changing the training length starts a
new one. [When two scores can be compared](comparable.md).

**Plan.** What `evoloop plan` prints: what a search will do, the warnings, the cost estimate, and every
setting with where its value came from.

**Provisional.** The score of a design that was stopped part way.

**Run.** A search with a name (`--name r1`). Also, in the tool's files, one evaluation (`R12`).

**Run type.** A preset for how the budget is shared between new designs, crossover and local moves.

**Screen.** Stopping the weaker half of new designs half way through training. The default form of
early stopping.

**Signature.** A list of numbers your evaluator can report saying where a model's errors fall. Used to
tell models that fail differently apart.

**Site file.** A file describing one machine: its scheduler, queues and rules.
[Run on a cluster](servers.md).

**Skill.** An editable file of settings and advice for one kind of optimization goal.

**Slot.** One opening for a new design, which exists whenever a job can start.

**Strategist.** An agent that reviews the search at intervals and may change its course, within bounds.

**Strategy.** How parents are chosen: lineage, archive, tournament, pareto or greedy.

**Study file.** `study.json`: a finished search in the CAMEO format, for depositing.

**Writer.** The agent that writes designs.
