# Run the CPU demo

The package carries a toy model search: find a small network that separates two interleaved spirals.
Every model is really trained (in NumPy, in a fraction of a second) and scored by its validation
accuracy. The proposals are scripted, so it needs no API key and no GPU, costs nothing, and finishes in
about half a minute. It exercises every part of the loop.

## Install and run

In a fresh Python environment (3.9 or later), with Git available:

```
git clone https://github.com/cameo-db/evoloop.git
cd evoloop
python -m pip install -e . numpy

evoloop example demo                        # copies the example to ./demo
evoloop plan demo                           # what the search will do, the warnings, every setting
evoloop brief demo --confirm "Your Name"    # your agreement to the plan
evoloop run demo --name first
evoloop report demo --name first
```

!!! warning "Install from the repository, not from PyPI"
    The package named `evoloop` on PyPI is a different project. Install from this repository, as above.
    NumPy is needed by the example's own training code; evoloop itself needs only PyYAML.

## What success looks like

`evoloop run` returns when the budget of 40 evaluations is spent:

```
run first: the budget of 40 evaluations is spent
report: demo/runs/first/report.md
```

Then `evoloop leaderboard demo --name first` shows the designs, best first (the last column, minutes, is left out here):

```
| kind     | model | lineage | family            | score   | state | length | fits | parameters |
| design   | C32   | L9      | periodic features | 0.97    | full  | 300    | 1    | 173        |
| design   | C17   | L9      | periodic features | 0.96833 | full  | 300    | 2    | 173        |
| design   | C14   | L9      | periodic features | 0.96667 | full  | 300    | 1    | 73         |
...
| baseline | C1    | L1      | baseline          | 0.5     | full  | 300    | 1    | 3          |
```

<div class="evo-chart">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 330" role="img" aria-label="The validation accuracy of each model in the built-in example, and the best so far, over 40 models">
<rect width="640" height="330" rx="8" fill="var(--evo-surface)"/>
<line x1="62" y1="284.0" x2="512" y2="284.0" stroke="var(--evo-grid)" stroke-width="1"/>
<text x="54" y="288.0" text-anchor="end" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">0.5</text>
<line x1="62" y1="231.2" x2="512" y2="231.2" stroke="var(--evo-grid)" stroke-width="1"/>
<text x="54" y="235.2" text-anchor="end" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">0.6</text>
<line x1="62" y1="178.4" x2="512" y2="178.4" stroke="var(--evo-grid)" stroke-width="1"/>
<text x="54" y="182.4" text-anchor="end" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">0.7</text>
<line x1="62" y1="125.6" x2="512" y2="125.6" stroke="var(--evo-grid)" stroke-width="1"/>
<text x="54" y="129.6" text-anchor="end" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">0.8</text>
<line x1="62" y1="72.8" x2="512" y2="72.8" stroke="var(--evo-grid)" stroke-width="1"/>
<text x="54" y="76.8" text-anchor="end" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">0.9</text>
<line x1="62" y1="20.0" x2="512" y2="20.0" stroke="var(--evo-grid)" stroke-width="1"/>
<text x="54" y="24.0" text-anchor="end" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">1</text>
<text x="62.0" y="302" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">1</text>
<text x="119.7" y="302" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">6</text>
<text x="177.4" y="302" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">11</text>
<text x="235.1" y="302" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">16</text>
<text x="292.8" y="302" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">21</text>
<text x="350.5" y="302" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">26</text>
<text x="408.2" y="302" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">31</text>
<text x="465.8" y="302" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">36</text>
<text x="287.0" y="322" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Model iteration</text>
<text transform="translate(16 152.0) rotate(-90)" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Validation accuracy (higher is better)</text>
<line x1="62" y1="284.0" x2="512" y2="284.0" stroke="var(--evo-soft)" stroke-width="1.5" stroke-dasharray="5 4"/>
<path d="M62.0 284.0 H73.5 V262.9 H96.6 V213.6 H108.2 V64.0 H142.8 V42.9 H177.4 V41.1 H212.0 V37.6 H246.6 V35.8 H512.0" fill="none" stroke="var(--evo-series)" stroke-width="2" stroke-linejoin="round"/>
<circle cx="62.0" cy="284.0" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 1 (C1): 0.5, the baseline</title></circle>
<circle cx="62.0" cy="284.0" r="10" fill="transparent"><title>Model 1 (C1): 0.5, the baseline</title></circle>
<circle cx="73.5" cy="262.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 2 (C2): 0.54, a new design</title></circle>
<circle cx="73.5" cy="262.9" r="10" fill="transparent"><title>Model 2 (C2): 0.54, a new design</title></circle>
<circle cx="85.1" cy="271.7" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 3 (C3): 0.5233, a new design</title></circle>
<circle cx="85.1" cy="271.7" r="10" fill="transparent"><title>Model 3 (C3): 0.5233, a new design</title></circle>
<circle cx="96.6" cy="213.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 4 (C4): 0.6333, an edit</title></circle>
<circle cx="96.6" cy="213.6" r="10" fill="transparent"><title>Model 4 (C4): 0.6333, an edit</title></circle>
<circle cx="108.2" cy="64.0" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 5 (C5): 0.9167, a new design</title></circle>
<circle cx="108.2" cy="64.0" r="10" fill="transparent"><title>Model 5 (C5): 0.9167, a new design</title></circle>
<circle cx="119.7" cy="262.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 6 (C6): 0.54, a settings move</title></circle>
<circle cx="119.7" cy="262.9" r="10" fill="transparent"><title>Model 6 (C6): 0.54, a settings move</title></circle>
<circle cx="131.2" cy="213.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 7 (C7): 0.6333, a new design</title></circle>
<circle cx="131.2" cy="213.6" r="10" fill="transparent"><title>Model 7 (C7): 0.6333, a new design</title></circle>
<circle cx="142.8" cy="42.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 8 (C8): 0.9567, an edit</title></circle>
<circle cx="142.8" cy="42.9" r="10" fill="transparent"><title>Model 8 (C8): 0.9567, an edit</title></circle>
<circle cx="154.3" cy="90.4" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 9 (C9): 0.8667, a new design</title></circle>
<circle cx="154.3" cy="90.4" r="10" fill="transparent"><title>Model 9 (C9): 0.8667, a new design</title></circle>
<circle cx="165.8" cy="208.3" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 10 (C10): 0.6433, an ablation</title></circle>
<circle cx="165.8" cy="208.3" r="10" fill="transparent"><title>Model 10 (C10): 0.6433, an ablation</title></circle>
<circle cx="177.4" cy="41.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 11 (C11): 0.96, a new design</title></circle>
<circle cx="177.4" cy="41.1" r="10" fill="transparent"><title>Model 11 (C11): 0.96, a new design</title></circle>
<circle cx="188.9" cy="46.4" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 12 (C12): 0.95, a new design</title></circle>
<circle cx="188.9" cy="46.4" r="10" fill="transparent"><title>Model 12 (C12): 0.95, a new design</title></circle>
<circle cx="200.5" cy="215.4" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 13 (C13): 0.63, a settings move</title></circle>
<circle cx="200.5" cy="215.4" r="10" fill="transparent"><title>Model 13 (C13): 0.63, a settings move</title></circle>
<circle cx="212.0" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 14 (C14): 0.9667, a new design</title></circle>
<circle cx="212.0" cy="37.6" r="10" fill="transparent"><title>Model 14 (C14): 0.9667, a new design</title></circle>
<circle cx="223.5" cy="48.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 15 (C15): 0.9467, an edit</title></circle>
<circle cx="223.5" cy="48.2" r="10" fill="transparent"><title>Model 15 (C15): 0.9467, an edit</title></circle>
<circle cx="235.1" cy="218.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 16 (C16): 0.6233, a new design</title></circle>
<circle cx="235.1" cy="218.9" r="10" fill="transparent"><title>Model 16 (C16): 0.6233, a new design</title></circle>
<circle cx="246.6" cy="35.8" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 17 (C17): 0.97, an edit</title></circle>
<circle cx="246.6" cy="35.8" r="10" fill="transparent"><title>Model 17 (C17): 0.97, an edit</title></circle>
<circle cx="258.2" cy="99.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 18 (C18): 0.85, a new design</title></circle>
<circle cx="258.2" cy="99.2" r="10" fill="transparent"><title>Model 18 (C18): 0.85, a new design</title></circle>
<circle cx="269.7" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 19 (C19): 0.9667, a settings move</title></circle>
<circle cx="269.7" cy="37.6" r="10" fill="transparent"><title>Model 19 (C19): 0.9667, a settings move</title></circle>
<circle cx="281.2" cy="41.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 20 (C20): 0.96, a new design</title></circle>
<circle cx="281.2" cy="41.1" r="10" fill="transparent"><title>Model 20 (C20): 0.96, a new design</title></circle>
<circle cx="292.8" cy="44.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 21 (C21): 0.9533, a new design</title></circle>
<circle cx="292.8" cy="44.6" r="10" fill="transparent"><title>Model 21 (C21): 0.9533, a new design</title></circle>
<circle cx="304.3" cy="48.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 22 (C22): 0.9467, an edit</title></circle>
<circle cx="304.3" cy="48.2" r="10" fill="transparent"><title>Model 22 (C22): 0.9467, an edit</title></circle>
<circle cx="315.8" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 23 (C17): 0.9667, a re-check on a new seed</title></circle>
<circle cx="315.8" cy="37.6" r="10" fill="transparent"><title>Model 23 (C17): 0.9667, a re-check on a new seed</title></circle>
<circle cx="327.4" cy="145.0" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 24 (C23): 0.7633, a new design</title></circle>
<circle cx="327.4" cy="145.0" r="10" fill="transparent"><title>Model 24 (C23): 0.7633, a new design</title></circle>
<circle cx="338.9" cy="49.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 25 (C24): 0.9433, a settings move</title></circle>
<circle cx="338.9" cy="49.9" r="10" fill="transparent"><title>Model 25 (C24): 0.9433, a settings move</title></circle>
<circle cx="350.5" cy="210.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 26 (C25): 0.64, a new design</title></circle>
<circle cx="350.5" cy="210.1" r="10" fill="transparent"><title>Model 26 (C25): 0.64, a new design</title></circle>
<circle cx="362.0" cy="85.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 27 (C26): 0.8767, an ablation</title></circle>
<circle cx="362.0" cy="85.1" r="10" fill="transparent"><title>Model 27 (C26): 0.8767, an ablation</title></circle>
<circle cx="373.5" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 28 (C27): 0.9667, an edit</title></circle>
<circle cx="373.5" cy="37.6" r="10" fill="transparent"><title>Model 28 (C27): 0.9667, an edit</title></circle>
<circle cx="385.1" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 29 (C28): 0.9667, an edit</title></circle>
<circle cx="385.1" cy="37.6" r="10" fill="transparent"><title>Model 29 (C28): 0.9667, an edit</title></circle>
<circle cx="396.6" cy="42.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 30 (C29): 0.9567, a settings move</title></circle>
<circle cx="396.6" cy="42.9" r="10" fill="transparent"><title>Model 30 (C29): 0.9567, a settings move</title></circle>
<circle cx="408.2" cy="48.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 31 (C30): 0.9467, an edit</title></circle>
<circle cx="408.2" cy="48.2" r="10" fill="transparent"><title>Model 31 (C30): 0.9467, an edit</title></circle>
<circle cx="419.7" cy="69.3" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 32 (C31): 0.9067, a new design</title></circle>
<circle cx="419.7" cy="69.3" r="10" fill="transparent"><title>Model 32 (C31): 0.9067, a new design</title></circle>
<circle cx="431.2" cy="35.8" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 33 (C32): 0.97, a settings move</title></circle>
<circle cx="431.2" cy="35.8" r="10" fill="transparent"><title>Model 33 (C32): 0.97, a settings move</title></circle>
<circle cx="442.8" cy="65.8" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 34 (C33): 0.9133, an ablation</title></circle>
<circle cx="442.8" cy="65.8" r="10" fill="transparent"><title>Model 34 (C33): 0.9133, an ablation</title></circle>
<circle cx="454.3" cy="55.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 35 (C35): 0.9333, an edit</title></circle>
<circle cx="454.3" cy="55.2" r="10" fill="transparent"><title>Model 35 (C35): 0.9333, an edit</title></circle>
<circle cx="465.8" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 36 (C36): 0.9667, an edit</title></circle>
<circle cx="465.8" cy="37.6" r="10" fill="transparent"><title>Model 36 (C36): 0.9667, an edit</title></circle>
<circle cx="477.4" cy="129.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 37 (C37): 0.7933, a settings move</title></circle>
<circle cx="477.4" cy="129.1" r="10" fill="transparent"><title>Model 37 (C37): 0.7933, a settings move</title></circle>
<circle cx="488.9" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 38 (C38): 0.9667, an edit</title></circle>
<circle cx="488.9" cy="37.6" r="10" fill="transparent"><title>Model 38 (C38): 0.9667, an edit</title></circle>
<circle cx="500.5" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 39 (C39): 0.9667, an edit</title></circle>
<circle cx="500.5" cy="37.6" r="10" fill="transparent"><title>Model 39 (C39): 0.9667, an edit</title></circle>
<circle cx="512.0" cy="41.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Model 40 (C40): 0.96, a settings move</title></circle>
<circle cx="512.0" cy="41.1" r="10" fill="transparent"><title>Model 40 (C40): 0.96, a settings move</title></circle>
<circle cx="512.0" cy="35.8" r="5" fill="var(--evo-series)" stroke="var(--evo-surface)" stroke-width="2"/>
<text x="524" y="276.0" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Baseline</text>
<text x="524" y="293.0" font-size="15" font-weight="600" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-ink)">0.5</text>
<text x="524" y="51.8" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Selected</text>
<text x="524" y="68.8" font-size="15" font-weight="600" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-ink)">0.97</text>
<circle cx="316" cy="250" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"/>
<text x="326" y="254" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">each model</text>
<line x1="402" y1="250" x2="422" y2="250" stroke="var(--evo-series)" stroke-width="2"/>
<text x="428" y="254" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">best so far</text>
</svg>
</div>

The starting design is a linear classifier, which cannot separate spirals: it scores 0.50, chance. Forty
models later the selected design scores 0.97 on validation data and 0.96 on the held-out test set,
which the search never sees. About four labels in a hundred are wrong on purpose, so nothing can score
much higher. Hover over a point for the model and the move that made it.

What to notice in the figure:

- **The best score rises in steps.** A hidden layer (model 4), distance from the centre as an input
  (model 5), more layers (models 8 and 11), then inputs that vary along the radius (model 14).
- **Most models do not beat the best.** That is what a search looks like: many are tried, few are kept.
- **The leader was checked.** Design C17 reached 0.97, was trained again on a new seed, and scored
  0.967. The leaderboard ranks a design by the mean of its fits, so a single lucky fit does not win.
- **The proposals are scripted.** They are real edits (wider, deeper, other inputs, another learning
  rate) and real training runs, drawn from a fixed list. This shows how a search proceeds and what it
  records, not what a language model would find.

To see the selected design, with its code, where it came from and what its writer predicted:

```
evoloop show demo C32 --name first
```

Use the design named at the top of your own leaderboard. The figure is drawn from the run's records by
`python tools/demo_figure.py demo/runs/first docs/assets`.

??? note "The numbers behind the figure"
    | Model | Design | Made by | Validation accuracy |
    |---|---|---|---|
    | 1 | C1 | the baseline | 0.5 |
    | 2 | C2 | a new design | 0.54 |
    | 3 | C3 | a new design | 0.5233 |
    | 4 | C4 | an edit | 0.6333 |
    | 5 | C5 | a new design | 0.9167 |
    | 6 | C6 | a settings move | 0.54 |
    | 7 | C7 | a new design | 0.6333 |
    | 8 | C8 | an edit | 0.9567 |
    | 9 | C9 | a new design | 0.8667 |
    | 10 | C10 | an ablation | 0.6433 |
    | 11 | C11 | a new design | 0.96 |
    | 12 | C12 | a new design | 0.95 |
    | 13 | C13 | a settings move | 0.63 |
    | 14 | C14 | a new design | 0.9667 |
    | 15 | C15 | an edit | 0.9467 |
    | 16 | C16 | a new design | 0.6233 |
    | 17 | C17 | an edit | 0.97 |
    | 18 | C18 | a new design | 0.85 |
    | 19 | C19 | a settings move | 0.9667 |
    | 20 | C20 | a new design | 0.96 |
    | 21 | C21 | a new design | 0.9533 |
    | 22 | C22 | an edit | 0.9467 |
    | 23 | C17 | a re-check on a new seed | 0.9667 |
    | 24 | C23 | a new design | 0.7633 |
    | 25 | C24 | a settings move | 0.9433 |
    | 26 | C25 | a new design | 0.64 |
    | 27 | C26 | an ablation | 0.8767 |
    | 28 | C27 | an edit | 0.9667 |
    | 29 | C28 | an edit | 0.9667 |
    | 30 | C29 | a settings move | 0.9567 |
    | 31 | C30 | an edit | 0.9467 |
    | 32 | C31 | a new design | 0.9067 |
    | 33 | C32 | a settings move | 0.97 |
    | 34 | C33 | an ablation | 0.9133 |
    | 35 | C35 | an edit | 0.9333 |
    | 36 | C36 | an edit | 0.9667 |
    | 37 | C37 | a settings move | 0.7933 |
    | 38 | C38 | an edit | 0.9667 |
    | 39 | C39 | an edit | 0.9667 |
    | 40 | C40 | a settings move | 0.96 |

There is a second example, a search for a formula that fits a dataset, where the score is an error and
lower is better: `evoloop example demo2 --kind formula`.

## What the run leaves behind

The run's folder is `demo/runs/first/`.

| File | Holds |
|---|---|
| `report.md` | the leaderboard, the population, what each mode and move returned, the ledger, the agents' spend |
| `status.json` | the same in brief, rewritten every turn while the run goes |
| `runs.jsonl`, `models.jsonl`, `recipes.jsonl` | every training run, architecture and recipe |
| `ledger.jsonl` | every change to the run and every note, with who made it |
| `calls.jsonl`, `replies/` | every agent call: what it was shown, what it answered, what it cost |
| `study.json` | the run as one JSON file in the CAMEO entry format ([saving and depositing it](records.md#saving-the-study-as-json-and-depositing-it-in-cameo)) |

## Try steering it

Start a second, longer run and change it while it goes:

```
evoloop brief demo --answer budget.evaluations=120 --confirm "Your Name"
evoloop run demo --name second &
evoloop set demo --name second schedule.novelty=0.8 --by "Your Name" --reason "try wider"
evoloop set demo --name second evaluation.allowance=200 --by "Your Name" --reason "shorter fits"
evoloop note demo --name second "Prefer small networks." --roles writer --by "Your Name"
evoloop status demo --name second
```

The report's *Steering ledger* section shows each entry with the number of evaluations at which it was
applied. Shortening the fits changes what a score means, so the second change starts a new comparison
period: the leaders are fitted again at the new length, and earlier scores stop deciding selection.

The example's models train in a fraction of a second, so a run may end before a request arrives. A
request made to a run that has ended waits, and is applied when the run is continued with the same
`evoloop run` command.

## Next

- [Use your own project](setting-up.md): mark the code, write the evaluator, answer the questions.
- [What do you want to optimize?](guides/index.md): a starting configuration for each goal.
- Before spending on real agents, dry-run your project with `agents.backend: stub`.
