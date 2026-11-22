---
hide:
  - navigation
---

# evoloop

## Summary

**evoloop is an open-source tool for LLM-driven evolutionary search over machine-learning code:
architectures, training recipes and hyperparameters.**

You give it a codebase with the editable regions marked and a script that trains and scores one
candidate. It then runs a population-based search. LLM agents write every candidate, as a mutation of
an earlier one, a crossover of two, or a new design. Deterministic code does the rest: it selects the
parents, validates each candidate, schedules the training jobs, and enforces the budget.

It belongs to the same family as FunSearch and AlphaEvolve. It differs in what it is built for: ML
research on a lab's own GPUs, where one evaluation is a full training run and a researcher wants to
watch and redirect the search.

| | |
|---|---|
| **Searches over** | Model architecture, training recipe, hyperparameters, or all three. Distillation of a teacher into smaller students. Any other code a script can score, such as an algorithm or a data pipeline. |
| **Search method** | Evolutionary. By default the population is a set of lineages with an explore-then-exploit schedule. MAP-Elites archive, tournament, Pareto and greedy selection are alternatives. |
| **Agents** | A writer proposes candidates. An analyst distils results into lessons for the writer. A strategist reallocates the search. How much the agents decide is configurable. |
| **Enforced by code** | Only the marked regions can change. The budget and any hard limits (model size, speed) hold. The test set is never shown to an agent. Every candidate, score and decision is logged. |
| **Researcher control** | You approve a plan with a cost estimate before anything is spent. During the run you can change settings, send the agents notes, or stop. Runs from Claude Code or the command line. |
| **Skills** | Thirteen editable presets, one per goal: raising a score, distillation, an accuracy-size frontier, fine-tuning, and others. Each sets the search and briefs the agents. Optional. |
| **CAMEO** | Reads and writes [CAMEO](https://cameo-db.github.io) study files. A search can start from designs in the database, and its full record can be deposited there. |
| **Runs on** | A workstation or a Slurm cluster. One GPU job per candidate, many in parallel. |
| **Status** | Version 0.2. The test suite passes with scripted agents. It has not yet been validated with an LLM on a real training task. |

[Set up a search](setting-up.md){ .md-button .md-button--primary }
[Source on GitHub](https://github.com/cameo-db/evoloop){ .md-button }

## How it works

<style>
.evo-loop-list { display: none; }
@media screen and (max-width: 620px) { .evo-loop-svg { display: none !important; } .evo-loop-list { display: block; } }
</style>
<svg class="evo-loop-svg" viewBox="0 0 1200 724" role="img" aria-label="The evoloop loop. The writer agent proposes candidate code by mutation, crossover or a new design. Your script trains candidates as parallel jobs, with weak runs stopped early. Code scores each on the validation metric, with the test set held out. The analyst agent turns scores into lessons for the writer, and the strategist agent adjusts the schedule. In the centre, code keeps the lineages: it selects the parents and retires stalled lineages. Inputs are a brief and a baseline, optionally a skill and designs from CAMEO. Outputs are a leaderboard and study.json." style="width:100%;max-width:940px;height:auto;display:block;margin:28px auto 12px;font-family:inherit">
  <defs>
    <marker id="evo-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#7d8790"/></marker>
    <marker id="evo-k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="currentColor"/></marker>
  </defs>
  <g fill="none" stroke="#7d8790" stroke-width="3.5">
    <path d="M760 100 Q990 104 1022 258" marker-end="url(#evo-a)"/>
    <path d="M1010 420 Q985 595 762 606" marker-end="url(#evo-a)"/>
    <path d="M440 606 Q215 595 190 422" marker-end="url(#evo-a)"/>
    <path d="M190 276 Q215 108 438 104" marker-end="url(#evo-a)"/>
  </g>
  <g fill="none" stroke="currentColor" stroke-width="3.5">
    <path d="M258 68 H438" marker-end="url(#evo-k)"/>
    <path d="M760 644 H940" marker-end="url(#evo-k)"/>
  </g>
  <g stroke-width="3">
    <rect x="40" y="24" width="210" height="104" rx="16" fill="#f1f3f4" stroke="#9aa3ad"/>
    <rect x="950" y="578" width="210" height="104" rx="16" fill="#f1f3f4" stroke="#9aa3ad"/>
    <rect x="450" y="36" width="300" height="124" rx="16" fill="#01796e" stroke="#01796e"/>
    <rect x="40" y="286" width="300" height="124" rx="16" fill="#01796e" stroke="#01796e"/>
    <rect x="876" y="270" width="300" height="124" rx="16" fill="#e9eef0" stroke="#aab2b8"/>
    <rect x="868" y="278" width="300" height="124" rx="16" fill="#e9eef0" stroke="#8a949b"/>
    <rect x="860" y="286" width="300" height="124" rx="16" fill="#e9eef0" stroke="#5f6b73"/>
    <rect x="450" y="546" width="300" height="124" rx="16" fill="#e9eef0" stroke="#5f6b73"/>
  </g>
  <g text-anchor="middle" font-weight="700" font-size="26">
    <text x="600" y="78" fill="#ffffff">Propose</text>
    <text x="1010" y="328" fill="#1c2326">Train</text>
    <text x="600" y="588" fill="#1c2326">Score</text>
    <text x="190" y="328" fill="#ffffff">Analyze</text>
    <text x="600" y="326" fill="currentColor" font-size="23">Lineages</text>
    <text x="145" y="60" fill="#1c2326" font-size="19">Brief + baseline</text>
    <text x="1055" y="614" fill="#1c2326" font-size="19">Leaderboard</text>
  </g>
  <g text-anchor="middle" font-size="17">
    <text x="600" y="110" fill="#ffffff">writer agent</text>
    <text x="600" y="136" fill="#ffffff">mutation · crossover · new design</text>
    <text x="1010" y="360" fill="#1c2326">your script, parallel jobs</text>
    <text x="1010" y="386" fill="#1c2326">weak runs stopped early</text>
    <text x="600" y="620" fill="#1c2326">validation metric</text>
    <text x="600" y="646" fill="#1c2326">test set held out</text>
    <text x="190" y="360" fill="#ffffff">analyst: lessons</text>
    <text x="190" y="386" fill="#ffffff">strategist: schedule</text>
    <text x="600" y="356" fill="currentColor">code selects the parents,</text>
    <text x="600" y="380" fill="currentColor">retires stalled lineages</text>
    <text x="145" y="88" fill="#1c2326" font-size="16">optional: a skill,</text>
    <text x="145" y="110" fill="#1c2326" font-size="16">CAMEO designs</text>
    <text x="1055" y="642" fill="#1c2326" font-size="16">+ study.json</text>
    <text x="1055" y="664" fill="#1c2326" font-size="16">for CAMEO</text>
  </g>
  <g font-size="16.5" font-style="italic" fill="currentColor" opacity="0.8" text-anchor="middle">
    <text x="868" y="206">candidate code</text>
    <text x="872" y="500">trained models</text>
    <text x="328" y="500">scores</text>
    <text x="336" y="206">lessons</text>
  </g>
  <g font-size="16" fill="currentColor">
    <rect x="40" y="694" width="30" height="20" rx="5" fill="#01796e"/>
    <text x="80" y="710">LLM agents</text>
    <rect x="200" y="694" width="30" height="20" rx="5" fill="#e9eef0" stroke="#5f6b73" stroke-width="2.5"/>
    <text x="240" y="710">deterministic code</text>
  </g>
</svg>

<p class="evo-loop-list"><b>Propose</b> &rarr; <b>Train</b> &rarr; <b>Score</b> &rarr; <b>Analyze</b> &rarr; back to Propose.</p>

The loop runs until the evaluation budget is spent, with as many candidates in training as you have
GPUs.

| Step | Done by | Detail |
|---|---|---|
| **Propose** | writer agent | Code selects one or two parents and the kind of move. The writer returns new code for the marked regions, with a hypothesis and a predicted effect. Code rejects a candidate that edits anything else, fails to parse, or duplicates an earlier one. |
| **Train** | your script | Each candidate trains as its own job. By default a new design in the bottom half of its peers at 50% of the run is stopped there. |
| **Score** | code | Reads the validation metric your script reports. Candidates outside a hard limit are rejected. Test-set metrics are recorded but withheld from every agent. |
| **Analyze** | analyst and strategist agents | Every 8 candidates the analyst writes lessons, which the writer sees on its next call. Every 15, or on a plateau, the strategist may shift the schedule or retire a lineage, within bounds you set. Both are optional. |
| **Lineages** | code | The population. Code selects parents from it and retires lineages that stop improving. |

[How it works, in detail](how-it-works.md) · [Agents](agents.md)

## Lineages

Greedy search, which always edits the current best, converges on the first workable design. evoloop's
default keeps several lineages in play. A lineage is one founding design and its descendants.

<svg class="evo-loop-svg" viewBox="0 0 1200 500" role="img" aria-label="An illustration of lineages in one search, as validation score against evaluations spent. The baseline CNN stops improving and is retired. A dilated CNN climbs steadily. A transformer starts below the others, is protected for its first two runs, and then climbs. A crossover of the dilated CNN and the transformer founds a new lineage that ends as the best version." style="width:100%;max-width:940px;height:auto;display:block;margin:24px auto 8px;font-family:inherit">
  <rect x="80" y="64" width="620" height="356" fill="#01796e" opacity="0.06"/>
  <path d="M700 64 V420" stroke="#7d8790" stroke-width="2" stroke-dasharray="5 6"/>
  <path d="M80 64 V420 H1120" stroke="#7d8790" stroke-width="2" fill="none"/>
  <g font-size="18" font-weight="700" fill="currentColor"><text x="92" y="48">Explore: mostly new designs</text><text x="712" y="48">Exploit: local moves and crossover</text></g>
  <g font-size="15" fill="currentColor" opacity="0.8" text-anchor="end"><text x="70" y="425">0.60</text><text x="70" y="255">0.70</text><text x="70" y="85">0.80</text></g>
  <path d="M100 386 L150 369 L210 360 L280 352 L350 352 L420 352 L480 352" stroke="#9aa3ab" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
  <circle cx="100" cy="386" r="7" fill="#ffffff" stroke="#9aa3ab" stroke-width="3"/>
  <circle cx="150" cy="369" r="7" fill="#ffffff" stroke="#9aa3ab" stroke-width="3"/>
  <circle cx="210" cy="360" r="7" fill="#9aa3ab"/>
  <circle cx="280" cy="352" r="7" fill="#9aa3ab"/>
  <circle cx="350" cy="352" r="7" fill="#9aa3ab"/>
  <circle cx="420" cy="352" r="7" fill="#9aa3ab"/>
  <circle cx="480" cy="352" r="7" fill="#9aa3ab"/>
  <path d="M511 343 L529 361 M511 361 L529 343" stroke="#9aa3ab" stroke-width="3.5" fill="none"/>
  <path d="M170 352 L230 318 L300 284 L380 250 L470 225 L560 208 L640 199 L720 191 L790 182 L860 182 L940 179 L1010 179" stroke="#5f6b73" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
  <circle cx="170" cy="352" r="7" fill="#ffffff" stroke="#5f6b73" stroke-width="3"/>
  <circle cx="230" cy="318" r="7" fill="#ffffff" stroke="#5f6b73" stroke-width="3"/>
  <circle cx="300" cy="284" r="7" fill="#5f6b73"/>
  <circle cx="380" cy="250" r="7" fill="#5f6b73"/>
  <circle cx="470" cy="225" r="7" fill="#5f6b73"/>
  <circle cx="560" cy="208" r="7" fill="#5f6b73"/>
  <circle cx="640" cy="199" r="7" fill="#5f6b73"/>
  <circle cx="720" cy="191" r="7" fill="#5f6b73"/>
  <circle cx="790" cy="182" r="7" fill="#5f6b73"/>
  <circle cx="860" cy="182" r="7" fill="#5f6b73"/>
  <circle cx="940" cy="179" r="7" fill="#5f6b73"/>
  <circle cx="1010" cy="179" r="7" fill="#5f6b73"/>
  <path d="M440 411 L500 386 L570 335 L640 301 L710 276 L780 262 L850 257" stroke="#5f6b73" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
  <circle cx="440" cy="411" r="7" fill="#ffffff" stroke="#5f6b73" stroke-width="3"/>
  <circle cx="500" cy="386" r="7" fill="#ffffff" stroke="#5f6b73" stroke-width="3"/>
  <circle cx="570" cy="335" r="7" fill="#5f6b73"/>
  <circle cx="640" cy="301" r="7" fill="#5f6b73"/>
  <circle cx="710" cy="276" r="7" fill="#5f6b73"/>
  <circle cx="780" cy="262" r="7" fill="#5f6b73"/>
  <circle cx="850" cy="257" r="7" fill="#5f6b73"/>
  <path d="M720 191 Q750 188 770 176 M710 276 Q760 250 768 180" stroke="#01796e" stroke-width="3" fill="none" stroke-dasharray="6 5"/>
  <path d="M770 174 L820 157 L880 140 L940 123 L1000 111 L1060 100" stroke="#01796e" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
  <circle cx="770" cy="174" r="7" fill="#ffffff" stroke="#01796e" stroke-width="3"/>
  <circle cx="820" cy="157" r="7" fill="#ffffff" stroke="#01796e" stroke-width="3"/>
  <circle cx="880" cy="140" r="7" fill="#01796e"/>
  <circle cx="940" cy="123" r="7" fill="#01796e"/>
  <circle cx="1000" cy="111" r="7" fill="#01796e"/>
  <circle cx="1060" cy="100" r="7" fill="#01796e"/>
  <circle cx="1060" cy="100" r="15" fill="none" stroke="#01796e" stroke-width="3"/>
  <g font-size="16" fill="currentColor">
    <text x="200" y="384" font-weight="700">Baseline CNN</text>
    <text x="200" y="406">retired: 6 moves without a gain</text>
    <text x="1024" y="184" font-weight="700">Dilated CNN</text>
    <text x="778" y="236" font-weight="700" fill="#01796e">crossover</text>
    <text x="866" y="263" font-weight="700">Transformer</text>
    <text x="866" y="285">first 2 runs protected</text>
    <text x="714" y="88" font-weight="700">Dilated CNN &#215; Transformer</text>
    <text x="714" y="110">hybrid lineage, founded by crossover</text>
  </g>
  <g font-size="15.5" fill="currentColor" opacity="0.85">
    <text x="80" y="448">evaluations &#8594;</text>
    <text x="1120" y="448" text-anchor="end">one marker = one trained candidate</text>
    <text x="80" y="476">Schematic, not data. Hollow markers: protected trial runs.</text>
    <text transform="translate(24 300) rotate(-90)">validation score</text>
  </g>
</svg>

| Rule | Default | In the figure |
|---|---|---|
| **Founding** | A new design, or a crossover, starts a lineage. | Dilated CNN, Transformer, and the hybrid. |
| **Protected trial** | A lineage's first 2 runs are not compared with other lineages. | The Transformer starts lowest and survives to be tuned. |
| **Retirement** | 6 local moves in a row without a gain above the noise floor. | The baseline CNN. |
| **Crossover** | The writer combines parents from two lineages. A retired lineage can still be a parent. | Dilated CNN × Transformer, which ends as the best. |
| **Population** | Up to 8 active lineages. None takes more than 40% of the local moves. | |
| **Schedule** | First 60% of the budget: 65% new designs. After: 60% local moves, 25% crossover. | The shaded and unshaded halves. |

Every number is a setting. [Parent selection](parents.md) covers the other four strategies.
[Comparison with FunSearch and AlphaEvolve](compared.md)

## Getting started

!!! tip "Recommended: run it from Claude Code"
    Open the evoloop repository in [Claude Code](https://claude.com/claude-code) and say what you want to optimize.
    It marks the code with you, writes the scoring adapter, asks the setup questions one at a time, and
    shows you the plan. After you approve, it launches the search, monitors it, and applies your feedback
    as steering.

The same steps by hand: [Set up a search](setting-up.md). Each run needs:

1. **Editable regions**, marked in your code with a pair of comment lines.
2. **An adapter**: a script that trains one candidate and writes its validation score.
3. **A brief**: the objective, the budget, and the search settings. `evoloop setup` asks for them.
   A [skill](which-search.md) fills in most of them for a given goal.

To start from existing designs, import them from an earlier run or a CAMEO study:
[Start from earlier designs](warm-start.md). To deposit your results: [Save and deposit the study](study.md).

## Documentation

| | |
|---|---|
| **Get started** | [Set up a search](setting-up.md) · [Write the evaluator](evaluator.md) · [Run on a cluster](servers.md) · [Worked example](quickstart.md) |
| **How it works** | [Overview](how-it-works.md) · [Schedule](schedule.md) · [Parent selection](parents.md) · [Moves](moves.md) · [Early stopping](early-stopping.md) · [Agents](agents.md) |
| **Run** | [Monitor and steer](steering.md) · [Budget and cost](cost.md) · [Start from earlier designs](warm-start.md) · [Deposit the study](study.md) |
| **Skills** | [Choose a skill](which-search.md) · [Edit, merge or write a skill](skills.md) |
| **Reference** | [Commands](commands.md) · [Brief fields](fields.md) · [All options](options.md) · [Code map](code.md) · [Status and limits](status.md) |
