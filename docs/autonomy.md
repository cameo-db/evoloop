# Agentic or harnessed, and what it costs

How much of a search do the agents decide? That is one setting, `harness.autonomy`, with three levels.
The more the agents decide, the more calls they make, so the choice is also a choice about cost.
`evoloop plan` shows the likely cost at each level before anything is spent.

## The three levels

| | `harnessed` | `guided` | `agentic` |
|---|---|---|---|
| In a sentence | code decides where the search goes; agents write | code runs the schedule; a strategist may change its course within bounds | agents choose each slot and steer the search |
| Who picks each slot | the schedule | the schedule | a coordinator agent, from options code prepares |
| Strategist | off | acts within the default bounds; asks first before changing the strategy | meets more often, wider bounds, asks first for nothing |
| Settings moves | drawn by code | written by an agent | written by an agent |
| Proposals per slot | 1 | from the budget guidance | 3 |
| Analyst | on | on | on, more often |
| Reviews of the agents | at the end | from the budget guidance | thirds |
| Agent calls | fewest | middle | most |

What every level keeps, because code enforces it: the budget and the spend cap, the floor on new
designs (`strategist.min_new_share`), the frozen problem (objective, data, scoring), the checks on
every design, and the record of every decision. "Agentic" widens what agents may decide; it does not
remove the floors.

Left empty, the run type decides (`explore_then_exploit`, `refine` and `survey` are close to `guided`;
`discovery` and `settings_only` use a lighter harness). What you set yourself in the brief is kept at
every level, so you can take `agentic` and still write `strategist.mode: advise`.

```
evoloop brief mysearch --answer harness.autonomy=agentic
evoloop set   mysearch --name r1 harness.autonomy=harnessed --by "Your Name"     # during a run
```

A change during a run applies to the next design, and the ledger entry lists every setting that moved
with it. [The menu](menu.md) shows exactly what each level sets.

## What the agents will cost

```
evoloop plan mysearch          # the settings, then the estimate
evoloop estimate mysearch      # the estimate alone
```

This is the estimate for the built-in example at 100 designs, with a model priced by hand at $3 per
million input tokens and $15 per million output tokens. The price is an illustration; put in your
own (`agents.prices`).

```
What the agents will cost (an estimate, for 100 designs):
  writer       about 110 (100 to 130) calls, about 674,160 (534,610 to 898,476) tokens, about $4.09 ($2.54 to $6.36)
  analyst      about 12 (12 to 15) calls, about 50,975 (49,725 to 63,420) tokens, about $0.23 ($0.21 to $0.31)
  strategist   about 10 (7 to 13) calls, about 33,128 (21,585 to 45,670) tokens, about $0.14 ($0.09 to $0.22)
  assessor     about 6 (6 to 6) calls, about 45,644 (44,894 to 46,768) tokens, about $0.18 ($0.17 to $0.20)
  in all       about 138 (125 to 164) calls, about 803,906 (650,814 to 1,054,334) tokens, about $4.64 ($3.01 to $7.09)

The same search at each level of autonomy (harness.autonomy; yours is not set, so the run type decides):
  harnessed  about 109 (101 to 129) calls, about $2.62 ($1.92 to $3.74)
  guided     about 138 (125 to 164) calls, about $4.64 ($3.01 to $7.09)
  agentic    about 267 (242 to 316) calls, about $5.72 ($3.92 to $8.47)
```

The example's code is a few lines long. A real model's blocks are far larger, and the writer's cost
grows with them: it is shown the parents' open blocks and returns the blocks it changes.

### How the estimate is made

- **Calls** follow from the settings. One writer call for each design an agent writes (block swaps and
  settings drawn by code need none); one coordinator call a design when an agent coordinates; an
  analyst call every `harness.analyst_every` runs; a strategist meeting every `strategist.every`
  designs; an assessor call per role per review.
- **The size of a call** is measured from your search folder: the task text and the open blocks, at
  about four characters to a token, with the designs each kind of slot is shown and the blocks it
  returns.
- **Dollars** come from `agents.prices`, which you give: `{model: {input: x, output: y}}` in dollars
  per million tokens. No price is built in. Without one the estimate is in calls and tokens.

### How far to trust it

It is a rough guide: expect the true figure within about a factor of two. Every line is a range.

- The number of calls is fairly sure; the plan counts them from the settings.
- The size of a call is a guess. Models differ in how much they write, and their own reasoning is not
  counted at all.
- One design in ten is assumed to fail or be refused and be written again (the range runs from none to
  three in ten), and the strategist is assumed to meet half again as often as scheduled because of
  plateaus.
- It has not been checked against a real run of this version.

### During a run

```
evoloop estimate mysearch --name r1
```

Once a role has made a few calls, its own mean cost per call replaces the guess, and the remaining
designs are projected from that. The report and `status.json` carry the same projection, and the
[spend governor](strategist.md#the-spend-governor) acts on it.

## Choosing

| If | Consider |
|---|---|
| the agent budget is tight, or you want a clean test of a fixed schedule | `harnessed` |
| you want the search to react to what it finds, with you approving the large changes | `guided` |
| evaluations are expensive next to agent calls, and you want the most judgment per design | `agentic` |
| evaluations are cheap and there are thousands of them | `harnessed`, or the `discovery` run type with its minimal harness: a call per design is then most of the cost |

Whether more autonomy finds better models is not known; nothing here has been measured on a real
search. The estimate tells you what a level costs, not what it returns.
