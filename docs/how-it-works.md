# How a search works

## One design at a time

A design is written only when it can run. Each time a job slot is free:

1. **The schedule picks the mode** of the slot.
2. **The strategy picks the parents**, from the results alone.
3. **A writer makes the design**: an agent writes the open blocks, or code does (a block swap, sampled
   settings).
4. **Code checks it**: only open blocks changed, the code parses, no forbidden term, not an exact copy
   of a design already tried.
5. **It is trained once and scored.** The score joins the results the next slot is chosen from.

Every design is fitted once. A second fit happens only as a re-check of the leader, or when the length
of a run is changed.

## The schedule: modes and phases

Four modes share the evaluations:

| Mode | What the slot does |
|---|---|
| `new` | a new family from the known design space |
| `novel` | a design built from or against designs that were rarely built on |
| `cross` | a crossover of two lineages |
| `local` | one change, a settings move or an ablation on an existing lineage |

`schedule.phases` gives the shares by phase. The default is exploration first, then exploitation:

| Phase | New designs | Crossover | Local |
|---|---|---|---|
| the first 60% of the budget | 65% | 10% | 25% |
| the rest | 15% | 25% | 60% |

`schedule.novel_share` splits the new designs into `new` and `novel` (a third novel by default).

The mix is met by counting, not by drawing: each slot goes to the mode furthest behind its share, so a
short run gets the mix it was promised. A mode with nothing to do passes its share on: crossover needs
two scored lineages, a local move needs one scored design.

**Adaptive schedule.** With `schedule.adaptive` above 0 the shares are blended with what each mode has
returned so far, each mode keeping at least `schedule.floor`. A gain is credited partly to the move
that made it and partly (`schedule.founder_credit`, half by default) to the slot that founded the
lineage. Without that, a new design is never credited for what was later built on it, and the figures
always favour local moves. It is off by default.

## The strategies

A strategy answers one question: for a slot of this mode, which candidates are the parents? It keeps no
state of its own, so the strategy can be changed during a run.

**`lineage`** keeps species alive side by side.

- A lineage is founded by a new design, a block swap or a hybrid.
- Until it has had `population.trial_runs` runs it is in a protected trial: it is owed local moves
  before anything else and is not compared with other lineages.
- The `population.lineages` best lineages that finished their trial are active. The rest sit on the
  bench, where they can still be a crossover partner.
- No lineage takes more than `population.quota` of the local slots.
- The lineage is drawn by rank, favouring those built on least; within it the parent is drawn among
  the candidates tied with its best within the noise.
- After `population.retire_after` local moves in a row with no gain above the noise, it retires.

**`archive`** keeps the best of each kind of design. Every scored design falls in a cell given by
`strategy.descriptors` (its family label and a size bin by default). Parents are drawn across the
cells; `schedule.novelty` moves the draw from "by rank" (0) to "by how rarely a cell has been built
on" (1). A design that is different but behind stays in play.

**`tournament`** draws `strategy.tournament_size` of the `strategy.window` most recent designs and
builds on the best of them. Old designs leave the population however good they were.

**`greedy`** builds on the current best.

**Islands.** `strategy.islands: N` runs N populations of the chosen strategy apart. A slot goes to the
island with the fewest runs, and that island sees only its own results. Every
`strategy.migrate_every` scored runs, the best design of another island is brought in as a parent.
Islands split the budget: on a small one each island gets few runs, and the plan warns.

## Crossover

| Kind | What happens | Written by |
|---|---|---|
| `block_swap` | whole marked blocks taken from each parent | code |
| `graft` | the one change that gained most in the donor's history, applied to the recipient | an agent |
| `hybrid` | one design written from the two parents | an agent |

Only the kinds listed in `crossover.kinds` are used. When none of them is possible for a pair (a block
swap needs two open blocks that differ, a graft needs a recorded gain in the donor's lineage), the slot
becomes a local move and the run's record says so.

**The partner.** The first parent is drawn by score. The second is the candidate whose errors fall
least like the first one's, when the adapter reports where a model's errors fall (`signature` in
`result.json`); otherwise one of another family. Two designs that fail in different places are the
pair worth combining.

## Local moves

`schedule.local_mix` shares the local slots between `edit` (one structural change), `settings` (only
values in the params blocks) and `ablation` (one component removed). With
`variation.step_adaptation`, a lineage whose recent edits gained often is asked for bolder ones, and
one whose edits rarely gained for smaller ones.

## Novelty

- **Novel slots** show the writer designs that were rarely built on, from anywhere in the ranking, and
  ask for something unlike the leader.
- **Several proposals per slot.** With `variation.proposals_per_slot` above 1 the writer returns
  several proposals with a forecast for each. One is trained: the one with the best forecast plus a
  bonus for distance from every design tried, scaled by `schedule.novelty`. A bold idea gets its chance
  at the cheap stage, before a training run is spent.
- **The archive** keeps what is different.
- **Specialists.** With `evaluation.speciality_metrics`, a parent is sometimes the design best on one
  metric rather than best overall.

Distance between designs is measured on the code: the share of three-token runs two designs have in
common. A proposal is not refused for being similar; only an exact copy is.

## Screening new designs

A new design's first run is compared, at `evaluation.screen_fraction` of its length, with the new
designs before it at the same point. One clearly in the lower part is stopped there and charged for
what it ran. This needs the adapter to report progress, and at least
`evaluation.screen_min_pool` earlier designs. `evaluation.screen_keep: 1` switches it off.

## Noise

`evaluation.noise` is how much the score differs between two fits of the same model. Every comparison
is made in that unit: a gain smaller than it is no gain, candidates within it are tied. With the `full`
harness the leader is fitted again on a new seed every 20 designs, and its score becomes the mean of
its fits: the leader of many single fits is partly the luckiest one.

## The harness

| Level | Roles that run |
|---|---|
| `minimal` | the writer |
| `standard` | the writer, and the analyst, which writes lessons from the results |
| `full` | the same, with the re-check of the leader |

A lesson counts as supported only when its evidence comes from two lineages; otherwise it is shown to
writers as an idea worth testing, never as a constraint.

**Coordinator.** By default code chooses each slot. With `harness.coordinator: agent` an agent chooses
among the options code prepares, one per possible mode, and what the schedule alone would have chosen
is recorded beside every choice.

## What a failed design costs

A design that fails, or fails the quick check, is not charged, up to
`budget.max_uncounted_failures`; beyond that each one is charged. When eight designs in a row end
without a score, the run stops as stalled rather than paying for more.
