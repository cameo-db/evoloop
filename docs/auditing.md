# Auditing the agents

The agents can be reviewed like a consulting group: what each one said, whether it was right, what it
cost. There are three levels.

| Level | What you get | Cost |
|---|---|---|
| Records | every call: what it was shown, what it answered, what it cost | none; always on |
| Scorecard | figures per role, computed by code from the records | none; in every report |
| Review | an assessor's written review of each role, for you | one agent call per role per review |

## Records

`calls.jsonl` has one line per agent call: the role, the sections of context it was shown with their
sizes, the ids of your notes it was shown, its reasoning and its one-line note, its cost and time. The
whole reply, with the code of every proposal whether chosen or not, is in `replies/`.

## The scorecard

In `evoloop report`, under *Agents*, *By kind of move* and *What each mode returned*:

- **Spend by role**: calls, dollars, seconds, failed calls.
- **The writer's forecasts against outcomes**: how often it had the sign right, its mean stated gain
  beside the mean gain that came about, and the rank correlation between forecast and outcome.
- **By kind of move**: runs, failures, and how often the move raised the best score.
- **By mode**: runs, and the gain in the best score each mode is credited with.
- **The coordinator**, when an agent coordinates: how many choices, and how many departed from what
  the schedule alone would have chosen.
- **Your notes**: how many calls were shown each one, and how many said they followed it.

The scorecard judges what a role stated against what happened. It does not show what the search would
have been without the role. Finding that out takes a stretch of a run with the role switched off
(`harness.level`, `harness.coordinator`), and at a small budget the comparison is noisy.

## Reviews

`audit.reviews` sets when the assessor reviews the agents:

| Value | Reviews at |
|---|---|
| `none` | never |
| `end` | the end of the run |
| `halfway` | 50% of the budget, and the end |
| `thirds` | 33%, 67%, and the end |
| `quarterly` | 25%, 50%, 75%, and the end |
| a list, e.g. `[0.1, 0.4]` | those shares of the budget |
| `on_demand` | only when you ask |

`audit.review_roles` limits the reviews to the roles you name. To ask for one now:

```
evoloop review mysearch --name r1 --by "Your Name"
evoloop review mysearch --name r1 --roles writer --by "Your Name"
```

Each review has an assessment, strengths, weaknesses, and suggestions; a suggestion is a specific
change to a role's instructions or to what it is shown, with the scorecard figure it should move.
Reviews are in the report and in `reviews.jsonl`.

**A review changes nothing by itself.** It is written for you. To adopt a suggestion, give it to the
agents as a note and say which review it came from:

```
evoloop note mysearch --name r1 "State the parameter count of every proposal." --roles writer --from-review V3 --by "Your Name"
```

or change the setting it concerns. The next review of that role is shown the notes adopted from
earlier reviews, so it can say whether they did what they were for.

## Changing who does a role

The model behind a role is a setting that can change during a run:

```
evoloop set mysearch --name r1 'agents.models={"writer": "another-model"}' --by "Your Name"
```

The ledger records when, so the scorecard before and after can be compared.

## Spend

`budget.model_dollars` caps the agents' cost: no call is made once it is reached, and the run ends as
paused, to be continued when you raise the cap. A reply that was paid for and could not be used is
still charged. If a backend reports no cost for its calls while a dollar cap is set, the run pauses
after three such calls rather than spend unseen; give `agents.prices` for the model, or cap the number
of calls with `budget.model_calls`.
