# See what a choice changes

Two figures you can change. The first shows what evoloop will actually do for a combination of choices.
The second is a toy search you can run, to see why those choices matter.

## What a search comes to

Pick a goal, a way of searching, how much the agents decide, and a budget. The panel shows the plan
that results: how the budget is shared between new designs, crossover and local moves, how parents are
chosen, who writes the designs, and how many agent calls to expect. Lines marked on the left differ from
the plain default.

<div class="evo-widget" id="evo-plan-explorer" data-src="../assets/plans.json">Loading the plan explorer…</div>

This is not a mock-up. Every combination was worked out by the code that resolves a real brief, and
`evoloop plan` prints the same for yours.

Things to try:

- **`refine` against `survey`.** The bar turns from mostly local moves to mostly new designs: the same
  budget, spent on depth or on breadth.
- **`settings-tuning`, then every level of autonomy.** The agent calls stay at none. This skill searches
  without agents, and a level of autonomy does not change that.
- **`model-efficiency`.** Parents are now chosen on a trade-off front of score and size, and the plan warns
  about what your evaluator must report.
- **A budget of 30.** Several combinations draw warnings: a population, islands or a wide search space
  have too little to work with.

## Why the way parents are chosen matters

A toy. Imagine every possible design laid out on a line, with similar designs close together, and a
curve giving the true quality of each. There are three peaks, and the baseline starts on the lowest and
broadest. The search cannot see the curve. It can only try a design and get a score, which is the true
quality plus some noise.

<div class="evo-widget" id="evo-playground">The playground needs JavaScript.</div>

Each dot is a design that was tried. A **new design** lands anywhere. A **local move** lands near its
parent. A **crossover** lands between two parents. The dashed line joins the newest design to its
parents.

Things to try:

- **Greedy, with 10% new designs.** It climbs the hill it started on and mostly stays there. Press
  *Another landscape* a few times: sometimes a lucky new design finds a better hill, often not.
- **Raise new designs to 40%.** More of the line is sampled and the high peak is usually found, but fewer
  evaluations are left to climb it.
- **Lineage or archive at 20%.** A design on a different hill is kept and built on even while it is behind,
  so a better peak is climbed once it is found. The archive spreads its effort widest.
- **Turn the noise up.** Greedy starts chasing lucky scores: the leader's score flatters it. Tournament
  forgets old designs, so one lucky score does not lead for long.

What this figure leaves out: a real design space is not a line, a real design is not one number, and a
real evaluation takes minutes or hours. It shows how the choice of parents shapes where a fixed budget
goes. It says nothing about how well any strategy does on your problem.
[How a search works](how-it-works.md) describes each strategy exactly.
