# Schedule

Every evaluation is one of three kinds of move. The schedule decides how many of each.

| Move | What it does |
|---|---|
| a **new design** | starts a new family, from scratch or from an unusual starting point |
| a **crossover** | combines two designs from different families |
| a **local move** | changes one thing in an existing design |

New designs explore. Local moves exploit: they improve what has already been found. A budget spent only
on new designs finds many mediocre ideas and polishes none; one spent only on local moves polishes the
first idea it had.

## The default: explore first, then exploit

With 100 evaluations and the default plan, the first 60 are shared 65% new, 10% crossover, 25% local.
The last 40 are shared 15% new, 25% crossover, 60% local. So about 45 designs start new families and
about 39 refine existing ones.

The [run type](which-search.md#run-types) sets these shares, and you can set them
yourself:

```yaml
schedule:
  phases:
    - {until: 0.6, new: 0.65, cross: 0.10, local: 0.25}
    - {until: 1.0, new: 0.15, cross: 0.25, local: 0.60}
```

The shares are met by counting. Each slot goes to the kind of move that is furthest behind its share,
so even a short search gets the mix it was promised. When a kind of move is not yet possible (crossover
needs two scored families, a local move needs one scored design), its turn passes to another.

<div class="evo-widget" id="evo-plan-explorer" data-src="../assets/plans.json">Loading the plan explorer…</div>

Try `refine` against `survey` above: the same budget, spent on depth or on breadth. The figure is
drawn from the tool's own settings code, and `evoloop plan` prints the same for your search.

## Two kinds of new design

A third of the new designs are *novel* designs (`schedule.novel_share`). An ordinary new design is
asked to cover a family the search has not tried. A novel one is shown a few designs that have rarely
been built on, wherever they rank, and asked for something unlike the leader. It is the search's way of
going back to ideas it passed over.

## The novelty dial

`schedule.novelty`, from 0 to 1, says how much a design far from everything tried is favoured. It acts
in two places. When a writer returns several proposals for one slot, the one trained is the one with
the best forecast plus a bonus for being different, and the dial sets the size of that bonus. And in
the [archive strategy](parents.md#archive), it moves the choice of parent from the best-ranked toward
the least-visited.

How different is a proposal? Before training, only its code can be compared: the share of short token
sequences it has in common with earlier designs. After training, behavior can be compared too, if your
evaluator reports where a model's errors fall ([signature](project-contract.md#what-the-job-writes)).
Two designs whose errors fall in the same places count as the same behavior however differently they
are written.

## Letting the results move the shares

Two things can change the shares during a search.

With `schedule.adaptive` above 0, the shares drift toward whichever kind of move has produced gains.
Part of each gain is credited to the move that started the family, since otherwise local moves would
get all the credit for ideas that new designs supplied. This is off by default.

With the [strategist](strategist.md) on, an agent reviews the search every 15 designs, and when it
plateaus, and may shift the shares within bounds you set.

You can also change them yourself at any time: `evoloop set mysearch --name r1 schedule.novelty=0.6
--by "Your Name"` ([Monitor and steer a search](steering.md)).

## Settings on this page

[`schedule.phases`](fields.md#schedule-phases), [`schedule.novel_share`](fields.md#schedule-novel_share), [`schedule.novelty`](fields.md#schedule-novelty), [`schedule.novelty_measure`](fields.md#schedule-novelty_measure),
[`schedule.adaptive`](fields.md#schedule-adaptive), [`schedule.floor`](fields.md#schedule-floor), [`schedule.founder_credit`](fields.md#schedule-founder_credit), [`variation.proposals_per_slot`](fields.md#variation-proposals_per_slot).

