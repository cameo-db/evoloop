# Working with the strategist

The strategist is an agent that looks at a search as a whole and can change how the remaining budget is
spent. It either advises you or acts on its own, and either way it works from a fixed list of actions
inside limits that code enforces. [Agents](agents.md#the-strategist) explains why it exists.

## Modes

`strategist.mode` has three values.

With `off` there is no strategist.

With `advise`, it reviews the search and proposes changes. Each proposal waits for your yes or no, and
nothing changes until you answer.

With `act`, proposals that stay inside the limits below are applied straight away. Larger ones still
wait for you. Three run types (`explore_then_exploit`, `refine`, `survey`) turn this on by default.

```
evoloop set mysearch --name r1 strategist.mode=advise --by "Your Name"
```

## Review timing

Every 15 scored designs, and whenever 12 designs have passed without the best score rising by more than
the noise. During a plateau it looks again every 6.

It is shown facts that code has worked out: how long since the best score rose, what each kind of move
has gained, how varied the recent designs are, the budget left, what the agents have cost, its own
earlier decisions and what followed them, and your notes.

## Actions

It may make up to two changes at a time, each of a different kind.

| Action | What it changes | Applied without asking? |
|---|---|---|
| `shares` | the split between new designs, crossover and local moves | yes, up to 15 points from where you left a share |
| `novelty` | how strongly different designs are favoured | yes |
| `local_mix` | the split between edits, settings moves and ablations | yes |
| `crossover_kinds` | which kinds of crossover are used | yes |
| `force` | makes the next few moves one particular kind | yes, up to 5 moves outstanding |
| `retire`, `revive` | retires a lineage, or brings one back | yes (lineage strategy only) |
| `direction` | a line of advice to the writers | yes; at most three stand at once |
| `strategy` | the parent rule itself | no: it waits for you |
| `question` | asks you something | the search does not wait for the answer |
| `stay` | nothing | |

## Bounds

Code checks each decision before applying it. A decision outside these limits either waits for you or
is refused, and either way it is recorded.

New designs cannot be pushed below 10% of the budget (`strategist.min_new_share`).

A share cannot drift. The 15-point allowance is measured from where you last left the shares, however
many decisions it takes to get there. To go further it has to ask.

No more than five ordered moves can be outstanding at once (`strategist.force_max`).

It cannot override you. A decision that would change a setting you changed during the search waits for
your approval.

The lineage holding the best design cannot be retired. A lineage that is revived gets one more chance,
and is retired again if it does not gain.

Anything listed in `strategist.ask_first` always waits for you. By default that is `strategy`.

## Approving and declining

```
evoloop report  mysearch --name r1                           # the strategist's section lists what is waiting
evoloop approve mysearch --name r1 --id S14 --by "Your Name"
evoloop decline mysearch --name r1 --id S14 --by "Your Name" --reason "keep exploring"
```

The report shows each waiting proposal with its reason, what it expects to gain, and why it is waiting.

When you approve one, it is checked against the search as it stands then. If things have moved on and
it no longer fits inside the limits, it is refused with the reason. A proposal left unanswered for 30
designs lapses.

## Notes to the strategist

Write a note addressed to it. It reads your notes every time it reviews the search.

```
evoloop note mysearch --name r1 "Exploration is underdelivering. Try crossover between the top two lineages." --roles strategist --by "Your Name"
```

Where its advice to the writers conflicts with a note of yours, the writers are told to follow yours.

## Chat

With `harness.conductor: agent`, the strategist also answers you.

```
evoloop set  mysearch --name r1 harness.conductor=agent --by "Your Name"
evoloop chat mysearch --name r1 --by "Your Name"
evoloop chat mysearch --name r1 "why so few new designs lately?" --by "Your Name"
```

It answers from the search's records. If you ask for a change, it makes the request through the same
list of actions and the same limits, and the command prints what it asked for. Saying "yes" to a
waiting proposal approves it in your name. What you say is kept and shown to it at later reviews, so a
conversation also shapes what it does when you are away.

It cannot edit files, or change a setting that is not on its list. For those it gives you the command.
Each message costs one agent call. Turning this on switches the strategist to `act` if it was off; set
`strategist.mode: advise` if you want every change to wait for you.

With `harness.conductor: code`, the default, no agent runs the search and there is nothing to talk to.

## Retiring a lineage yourself

```
evoloop lineage mysearch --name r1 --retire L4 --by "Your Name"
evoloop lineage mysearch --name r1 --revive L4 --by "Your Name"
```

Whoever spoke last about a lineage, you or the strategist, is the one obeyed.

## Evaluating the strategist

Each decision is recorded with the gain the strategist expected. Fifteen designs later, code records
how much the best score actually rose, and the report sets the two side by side.

That shows what followed a decision. It cannot show what the decision caused, because there is no copy
of the search without it. To find out whether the strategist earns its cost, run the same budget with
`strategist.mode: off` and compare. That comparison has not been made yet.

## Settings

| Setting | Default | |
|---|---|---|
| [`strategist.mode`](fields.md#strategist-mode) | `off`; `act` under three run types | off, advise or act |
| [`strategist.every`](fields.md#strategist-every) | 15 | scored designs between reviews |
| [`strategist.plateau`](fields.md#strategist-plateau) | 12 | designs without a gain that trigger a review |
| [`strategist.horizon`](fields.md#strategist-horizon) | 15 | designs after which a decision is scored; an unanswered proposal lapses after twice this |
| [`strategist.min_new_share`](fields.md#strategist-min_new_share) | 0.10 | the least share of new designs |
| [`strategist.max_share_shift`](fields.md#strategist-max_share_shift) | 0.15 | how far a share may move without asking |
| [`strategist.force_max`](fields.md#strategist-force_max) | 5 | ordered moves outstanding at once |
| [`strategist.ask_first`](fields.md#strategist-ask_first) | `["strategy"]` | actions that always wait for you |
