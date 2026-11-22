# Audit the agents

Agents cost money, and it is fair to ask whether each one earns it. evoloop keeps what each agent said
and what happened afterwards, so you can check.

For example, a writer proposing an edit also states what it expects: a gain of 0.8 noise floors, with a
40% chance of beating the parent. The design is trained and scores 0.003 below its parent. Both the
forecast and the outcome are recorded. Over a hundred designs, the report can say how often the writer
called the direction right and whether its confident forecasts gained more than its doubtful ones.

There are three levels of checking. The first two cost nothing.

## The records

`calls.jsonl` has one line for every agent call: which role, what it was shown, which of your notes it
saw, its reasoning in a few sentences, its cost and how long it took. The full reply, including the code
of proposals that were not chosen, is in `replies/`.

## The scorecard

Every report includes figures worked out from those records:

| For | The report shows |
|---|---|
| each role | calls, dollars, seconds, failed calls |
| the writer's forecasts | how often the direction was right; the mean gain forecast against the mean gain observed; the rank correlation between the two |
| each kind of move | how many were made, how many failed, how often one raised the best score |
| new designs, crossover, local moves | how much of the rise in the best score each is credited with |
| the coordinator, if an agent chooses each move | how often it departed from what the schedule alone would have chosen |
| your notes | how many calls were shown each one, and how many said they followed it |

The scorecard compares what a role said with what happened. It cannot tell you what the search would
have done without that role. For that, run part of a search with the role switched off
(`harness.level`, `harness.coordinator`) and compare; at a small budget the comparison will be noisy.

## Reviews

A review is a written assessment of each role by another agent, the assessor. It costs one agent call
per role.

`audit.reviews` sets when reviews happen: `none`, `end`, `halfway` (at 50% of the budget and the end),
`thirds`, `quarterly`, `on_demand`, or a list of points such as `[0.1, 0.4]`. To ask for one now:

```
evoloop review mysearch --name r1 --by "Your Name"
evoloop review mysearch --name r1 --roles writer --by "Your Name"
```

Each review gives an assessment, strengths, weaknesses and suggestions. A suggestion is a specific
change to a role's instructions or to what it is shown, with the scorecard figure it is meant to move.
Reviews appear in the report and in `reviews.jsonl`.

A review does not change the search. To act on a suggestion, pass it to the agents as a note and say
which review it came from:

```
evoloop note mysearch --name r1 "State the parameter count of every proposal." --roles writer --from-review V3 --by "Your Name"
```

The next review of that role is shown the notes adopted from earlier reviews, so it can say whether
they worked.

## Changing the model behind a role

```
evoloop set mysearch --name r1 'agents.models={"writer": "claude-sonnet-5-5"}' --by "Your Name"
```

The change is recorded with the evaluation it took effect at, so the scorecard before and after can be
compared. [Models and prices](models.md) lists the models; [Budget and cost](cost.md) covers the spend
cap.
