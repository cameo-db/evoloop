# Model and effort

Which model the agents run on, and how hard it reasons, are settings with defaults. You can change
them when you set a search up and while it runs, for every role at once or role by role.

## The defaults

| Setting | Default | Meaning |
|---|---|---|
| `agents.default_model` | `claude-opus-5-5` | the model every role uses |
| `agents.models` | none | a model for one role, over the default: `{writer: claude-fable-5-2}` |
| `agents.effort` | `medium` | how hard the model reasons, for every role |
| `agents.efforts` | `{writer: high}` | an effort for one role, over the default |
| `agents.fallbacks` | `default` | a request the model declines is answered by another model, where the API offers that |

So out of the box every role runs on Claude Opus 5.5; the writer, whose designs are where judgment
matters most, at high effort, and the analyst, strategist, coordinator and assessor at medium.

`evoloop plan` shows the model and effort of each role beside what it is likely to cost, and what the
same search would cost on each current model.

## Changing them

At setup, in `brief.yaml` or by answer:

```
evoloop brief mysearch --answer agents.default_model=claude-sonnet-5-5 --answer agents.effort=high
evoloop brief mysearch --answer 'agents.models={"writer": "claude-fable-5-2"}' --answer 'agents.efforts={"writer": "xhigh", "analyst": "low"}'
```

During a run; the change applies from the next call, and is in the ledger:

```
evoloop set mysearch --name r1 agents.default_model=claude-sonnet-5-5 --by "Your Name"
evoloop set mysearch --name r1 'agents.efforts={"writer": "max"}' --by "Your Name"
```

A common arrangement is a stronger model for the writer and a cheaper one for the roles that read and
summarise:

```yaml
agents:
  default_model: claude-sonnet-5-5
  models: {writer: claude-opus-5-5}
  effort: low
  efforts: {writer: high, strategist: medium}
```

## The models

`evoloop menu models` prints this list. Prices are Anthropic's first-party API rates in dollars per
million tokens as of 2026-11-03; they may have changed, and other platforms price separately.

| Model | Input | Output | Effort levels | Its own default |
|---|---|---|---|---|
| `claude-opus-5-5` | $4 | $20 | low, medium, high, xhigh, max | medium |
| `claude-sonnet-5-5` | $2 | $10 | low, medium, high, xhigh, max | high |
| `claude-haiku-5-5` | $0.10 | $0.50 | low, medium, high, xhigh, max | medium |
| `claude-fable-5-2` | $8 | $40 | low, medium, high, xhigh, max | high |

[The menu](menu.md#models) lists the earlier models too.

- **Another model.** Any model id can be given. One that is not on the list is priced only if you give
  `agents.prices`, and its effort is sent as you set it.
- **Your own prices.** `agents.prices: {model: {input: x, output: y}}` always wins over the list. Use
  it when prices have changed or you are on another platform's rates.
- **Without a price** the spend cap cannot count a model's calls: the plan warns, and a capped run
  pauses after three calls with no cost.

## Effort

| Level | Use |
|---|---|
| `low` | the least reasoning and the fewest tokens; simple, high-volume calls |
| `medium` | the default for every role but the writer |
| `high` | the default for the writer |
| `xhigh` | between high and max; not accepted by the 4.6 models |
| `max` | the most reasoning, when correctness matters more than cost |
| `model_default` | send no effort; the model uses its own default |

Effort decides how much the model reasons before it answers. That reasoning is billed as output
tokens, so higher effort costs more and takes longer; on the most capable models a single call at high
effort can take minutes (`agents.call_timeout_seconds`, 900 by default).

The plan warns when an effort does not suit a model on the list (`xhigh` on a 4.6 model, any effort on
`claude-haiku-4-5`), and such an effort is left out of the request rather than sent to fail.

Whether more effort finds better designs on your problem is not known in advance. The scorecard shows
the writer's forecasts against outcomes and what each move returned, before and after a change of
effort or model, since the ledger records when it changed.

## What it does to the cost

The built-in example at 100 designs, with the defaults, as `evoloop plan` prints it:

```
What the agents will cost (an estimate, for 100 designs):
  writer       about 110 (100 to 130) calls, about 674,160 (534,610 to 898,476) tokens, about $5.45 ($3.39 to $8.48)   [claude-opus-5-5, effort high]
  analyst      about 12 (12 to 15) calls, about 50,975 (49,725 to 63,420) tokens, about $0.30 ($0.28 to $0.41)   [claude-opus-5-5, effort medium]
  strategist   about 10 (7 to 13) calls, about 33,128 (21,585 to 45,670) tokens, about $0.19 ($0.12 to $0.29)   [claude-opus-5-5, effort medium]
  assessor     about 6 (6 to 6) calls, about 45,644 (44,894 to 46,768) tokens, about $0.24 ($0.23 to $0.27)   [claude-opus-5-5, effort medium]
  in all       about 138 (125 to 164) calls, about 803,906 (650,814 to 1,054,334) tokens, about $6.18 ($4.02 to $9.45)

The same search with another model for every role (agents.default_model; yours is claude-opus-5-5):
  claude-opus-5-5      about $6.18 ($4.02 to $9.45)   ($4 in, $20 out per million tokens; the current Opus)
  claude-sonnet-5-5    about $3.10 ($2.01 to $4.71)   ($2 in, $10 out per million tokens; the current Sonnet: faster and cheaper)
  claude-haiku-5-5     about $0.16 ($0.10 to $0.24)   ($0.1 in, $0.5 out per million tokens; the cheapest; the price is for prompts up to 100K tokens)
  claude-fable-5-2     about $12.39 ($8.04 to $18.87)   ($8 in, $40 out per million tokens; the most capable; single calls can take minutes)
```

Two cautions on reading it:

- **The estimate does not count the model's reasoning.** The figures above are the same at every
  effort; the real cost rises with effort. Once a run has made a few calls, `evoloop estimate --name`
  uses its measured cost per call, which includes the reasoning.
- **The example's code is a few lines long.** A real model's blocks are far larger, and so is each call.

See [Agentic or harnessed, and what it costs](autonomy.md) for how the estimate is made and how far
to trust it.

## The backends

| `agents.backend` | Model and effort are sent as | Cost comes from |
|---|---|---|
| `anthropic_api` | the Messages API's `model`, and `output_config.effort` | tokens in the reply, times your price or the list's |
| `claude_code` | `claude --print --model ... --effort ...` | the cost the command reports |
| `stub` | not used | nothing: no model call is made |

With `agents.fallbacks: default`, on the models where the API offers it, a request the model declines
is answered by another model in the same call instead of being lost; the reply says which model
answered, and the call is priced at that model's rates. `agents.fallbacks: off` switches it off. This
applies to `anthropic_api` only.

Neither backend has been called from this version against the real service; see
[Status and limits](status.md).
