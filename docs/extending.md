# Extending evoloop

evoloop is built to be extended. The library skills, run types and strategies are starting points, and
none of them is a boundary. Most of a search can be replaced without writing code, by giving a file or
a setting of your own. The rest is a small module with a short interface.

## Without code

| To change | Use | Example |
|---|---|---|
| The goal and the guidance the agents get | a custom skill | [Write a skill](custom-skills.md) |
| How the budget is spent | `run.type: custom` with your own `schedule.phases` | below |
| What is optimized | your evaluator: any script that writes a score | [Write the evaluator](evaluator.md) |
| What may change | your own marked blocks and roles, opened with `space.roles` | [Set up a search](setting-up.md#1-mark-the-editable-code) |
| The second objective | `strategy.second_metric`: any metric your evaluator reports | below |
| What counts as a kind of design | `strategy.descriptors`: any metric your evaluator reports | below |
| Hard limits | `limits` on any metric your evaluator reports | [Early stopping](early-stopping.md#limits) |
| Which model fills each role | `agents.models`, `agents.writer_mix` | [Models and prices](models.md) |
| The proposer | `agents.backend: stub` with a script of your own | below |
| The machine | a site file | [Run on a cluster](servers.md) |

A schedule of your own, with three phases:

```yaml
run:
  type: custom
  description: Explore briefly, cross the leaders, then refine.
schedule:
  phases:
    - {until: 0.2, new: 0.80, cross: 0.00, local: 0.20}
    - {until: 0.5, new: 0.20, cross: 0.50, local: 0.30}
    - {until: 1.0, new: 0.05, cross: 0.15, local: 0.80}
```

A trade-off between the score and a metric of your own. The evaluator reports `energy_joules` under
`diagnostics`, and selection keeps the designs that are not beaten on both:

```yaml
strategy:
  mechanism: pareto
  second_metric: energy_joules
  second_direction: minimize
```

An archive whose cells are your own metric, so that the best design is kept in each third of its range:

```yaml
strategy:
  mechanism: archive
  descriptors: [receptive_field]
```

A proposer of your own in place of the LLM. `agents.stub_module` names a Python file with one function,
`respond(role, context)`, which is given what an agent would be sent and returns what an agent would
return. The built-in example uses this for its scripted proposals, and it is a way to run a baseline
such as random search through the same loop:

```yaml
agents:
  backend: stub
  stub_module: my_proposer.py
```

## With code

| To add | Write | Model to follow |
|---|---|---|
| A parent-selection strategy | a class with `choose` and `population` in `evoloop/strategies/` | [`greedy.py`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/greedy.py) |
| A scheduler | a class with `submit`, `state`, `cancel` and `shutdown` in `evoloop/jobs.py` | the `Slurm` class in [`jobs.py`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py) |
| An LLM backend | a class with `call` in `evoloop/model/` | [`anthropic_api.py`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/anthropic_api.py) |
| A library skill | a folder under `evoloop/skills/` | [Write a skill](custom-skills.md#adding-a-skill-to-the-library) |

A strategy is the smallest of these. This one draws every parent at random from the scored designs:

```python
# evoloop/strategies/uniform.py
class Uniform:
    name = "uniform"

    def population(self, view, settings):
        return [{"candidate": c["id"], "score": view.display(c["value"]), "family": c["family"]}
                for c in view.scored()[:5]]

    def choose(self, view, mode, settings, rng):
        scored = [c["id"] for c in view.scored()]
        if mode == "local" and scored:
            parent = rng.choice(scored)
            return {"mode": "local", "lineage": view.cands[parent]["lineage"], "parents": [parent],
                    "step": "normal", "why": "a design drawn at random"}
        if mode == "cross" and len(scored) >= 2:
            first, second = rng.sample(scored, 2)
            return {"mode": "cross", "lineage": view.cands[first]["lineage"], "parents": [first, second],
                    "why": "two designs drawn at random"}
        return {"mode": "new", "lineage": None, "parents": [], "why": "a new design"}
```

`choose` is called once for each free slot with the kind of move the schedule picked, and returns the
parents. To make the strategy selectable, add its name to `MECHANISMS` in `evoloop/form.py` and its
class to `make` in `evoloop/strategies/__init__.py`. [Code map](code.md) lists every module.

An agent can write any of these for you. Open the repository in Claude Code, say what you want the
search to do differently, and ask it to add it.
