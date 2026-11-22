# Worked example

A complete search you can run in half a minute on a laptop. It looks for a small neural network that
separates two interleaved spirals. Each design is trained for real, in NumPy. The proposals come from a
script, not an LLM, so it costs nothing and needs no API key.

## Run

Python 3.9 or later, with Git:

```
git clone https://github.com/cameo-db/evoloop.git
cd evoloop
python -m pip install -e . numpy

evoloop example demo
evoloop plan demo
evoloop brief demo --confirm "Your Name"
evoloop run demo --name first
evoloop leaderboard demo --name first
```

Install from the repository. The `evoloop` package on PyPI is an unrelated project.

| Command | What it does |
|---|---|
| `example` | copies the example into `./demo`: the code to optimize, an evaluator (the scoring script), and a brief (the settings) |
| `plan` | prints what the search will do |
| `brief --confirm` | records that you agree to the plan; nothing runs without it |
| `run` | runs the search until 40 evaluations are spent |
| `leaderboard` | lists the designs, best first |

## Result

```
| kind     | model | lineage | family            | score   | state | length | fits | parameters |
| design   | C32   | L9      | periodic features | 0.97    | full  | 300    | 1    | 173        |
| design   | C17   | L9      | periodic features | 0.96833 | full  | 300    | 2    | 173        |
| design   | C14   | L9      | periodic features | 0.96667 | full  | 300    | 1    | 73         |
...
| baseline | C1    | L1      | baseline          | 0.5     | full  | 300    | 1    | 3          |
```

`lineage` is the line of descent a design belongs to, and `family` is the label the writer gave that kind
of design. `state` says whether the run went its full `length` (300 training steps here) or was stopped
early. `fits` is how many times the design was trained.

Validation accuracy went from 0.50 for the baseline, a linear classifier, to 0.97. The held-out test
accuracy of the selected design is 0.96. Four labels in a hundred are wrong on purpose, so 0.96 is about
the ceiling. Your run may order tied designs differently.

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
<text x="287.0" y="322" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Evaluation</text>
<text transform="translate(16 152.0) rotate(-90)" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Validation accuracy (higher is better)</text>
<line x1="62" y1="284.0" x2="512" y2="284.0" stroke="var(--evo-soft)" stroke-width="1.5" stroke-dasharray="5 4"/>
<path d="M62.0 284.0 H73.5 V262.9 H96.6 V213.6 H108.2 V64.0 H142.8 V42.9 H177.4 V41.1 H212.0 V37.6 H246.6 V35.8 H512.0" fill="none" stroke="var(--evo-series)" stroke-width="2" stroke-linejoin="round"/>
<circle cx="62.0" cy="284.0" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 1 (design C1): 0.5, the baseline</title></circle>
<circle cx="62.0" cy="284.0" r="10" fill="transparent"><title>Evaluation 1 (design C1): 0.5, the baseline</title></circle>
<circle cx="73.5" cy="262.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 2 (design C2): 0.54, a new design</title></circle>
<circle cx="73.5" cy="262.9" r="10" fill="transparent"><title>Evaluation 2 (design C2): 0.54, a new design</title></circle>
<circle cx="85.1" cy="271.7" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 3 (design C3): 0.5233, a new design</title></circle>
<circle cx="85.1" cy="271.7" r="10" fill="transparent"><title>Evaluation 3 (design C3): 0.5233, a new design</title></circle>
<circle cx="96.6" cy="213.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 4 (design C4): 0.6333, an edit</title></circle>
<circle cx="96.6" cy="213.6" r="10" fill="transparent"><title>Evaluation 4 (design C4): 0.6333, an edit</title></circle>
<circle cx="108.2" cy="64.0" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 5 (design C5): 0.9167, a new design</title></circle>
<circle cx="108.2" cy="64.0" r="10" fill="transparent"><title>Evaluation 5 (design C5): 0.9167, a new design</title></circle>
<circle cx="119.7" cy="262.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 6 (design C6): 0.54, a settings move</title></circle>
<circle cx="119.7" cy="262.9" r="10" fill="transparent"><title>Evaluation 6 (design C6): 0.54, a settings move</title></circle>
<circle cx="131.2" cy="213.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 7 (design C7): 0.6333, a new design</title></circle>
<circle cx="131.2" cy="213.6" r="10" fill="transparent"><title>Evaluation 7 (design C7): 0.6333, a new design</title></circle>
<circle cx="142.8" cy="42.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 8 (design C8): 0.9567, an edit</title></circle>
<circle cx="142.8" cy="42.9" r="10" fill="transparent"><title>Evaluation 8 (design C8): 0.9567, an edit</title></circle>
<circle cx="154.3" cy="90.4" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 9 (design C9): 0.8667, a new design</title></circle>
<circle cx="154.3" cy="90.4" r="10" fill="transparent"><title>Evaluation 9 (design C9): 0.8667, a new design</title></circle>
<circle cx="165.8" cy="208.3" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 10 (design C10): 0.6433, an ablation</title></circle>
<circle cx="165.8" cy="208.3" r="10" fill="transparent"><title>Evaluation 10 (design C10): 0.6433, an ablation</title></circle>
<circle cx="177.4" cy="41.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 11 (design C11): 0.96, a new design</title></circle>
<circle cx="177.4" cy="41.1" r="10" fill="transparent"><title>Evaluation 11 (design C11): 0.96, a new design</title></circle>
<circle cx="188.9" cy="46.4" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 12 (design C12): 0.95, a new design</title></circle>
<circle cx="188.9" cy="46.4" r="10" fill="transparent"><title>Evaluation 12 (design C12): 0.95, a new design</title></circle>
<circle cx="200.5" cy="215.4" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 13 (design C13): 0.63, a settings move</title></circle>
<circle cx="200.5" cy="215.4" r="10" fill="transparent"><title>Evaluation 13 (design C13): 0.63, a settings move</title></circle>
<circle cx="212.0" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 14 (design C14): 0.9667, a new design</title></circle>
<circle cx="212.0" cy="37.6" r="10" fill="transparent"><title>Evaluation 14 (design C14): 0.9667, a new design</title></circle>
<circle cx="223.5" cy="48.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 15 (design C15): 0.9467, an edit</title></circle>
<circle cx="223.5" cy="48.2" r="10" fill="transparent"><title>Evaluation 15 (design C15): 0.9467, an edit</title></circle>
<circle cx="235.1" cy="218.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 16 (design C16): 0.6233, a new design</title></circle>
<circle cx="235.1" cy="218.9" r="10" fill="transparent"><title>Evaluation 16 (design C16): 0.6233, a new design</title></circle>
<circle cx="246.6" cy="35.8" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 17 (design C17): 0.97, an edit</title></circle>
<circle cx="246.6" cy="35.8" r="10" fill="transparent"><title>Evaluation 17 (design C17): 0.97, an edit</title></circle>
<circle cx="258.2" cy="99.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 18 (design C18): 0.85, a new design</title></circle>
<circle cx="258.2" cy="99.2" r="10" fill="transparent"><title>Evaluation 18 (design C18): 0.85, a new design</title></circle>
<circle cx="269.7" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 19 (design C19): 0.9667, a settings move</title></circle>
<circle cx="269.7" cy="37.6" r="10" fill="transparent"><title>Evaluation 19 (design C19): 0.9667, a settings move</title></circle>
<circle cx="281.2" cy="41.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 20 (design C20): 0.96, a new design</title></circle>
<circle cx="281.2" cy="41.1" r="10" fill="transparent"><title>Evaluation 20 (design C20): 0.96, a new design</title></circle>
<circle cx="292.8" cy="44.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 21 (design C21): 0.9533, a new design</title></circle>
<circle cx="292.8" cy="44.6" r="10" fill="transparent"><title>Evaluation 21 (design C21): 0.9533, a new design</title></circle>
<circle cx="304.3" cy="48.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 22 (design C22): 0.9467, an edit</title></circle>
<circle cx="304.3" cy="48.2" r="10" fill="transparent"><title>Evaluation 22 (design C22): 0.9467, an edit</title></circle>
<circle cx="315.8" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 23 (design C17): 0.9667, a re-check on a new seed</title></circle>
<circle cx="315.8" cy="37.6" r="10" fill="transparent"><title>Evaluation 23 (design C17): 0.9667, a re-check on a new seed</title></circle>
<circle cx="327.4" cy="145.0" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 24 (design C23): 0.7633, a new design</title></circle>
<circle cx="327.4" cy="145.0" r="10" fill="transparent"><title>Evaluation 24 (design C23): 0.7633, a new design</title></circle>
<circle cx="338.9" cy="49.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 25 (design C24): 0.9433, a settings move</title></circle>
<circle cx="338.9" cy="49.9" r="10" fill="transparent"><title>Evaluation 25 (design C24): 0.9433, a settings move</title></circle>
<circle cx="350.5" cy="210.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 26 (design C25): 0.64, a new design</title></circle>
<circle cx="350.5" cy="210.1" r="10" fill="transparent"><title>Evaluation 26 (design C25): 0.64, a new design</title></circle>
<circle cx="362.0" cy="85.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 27 (design C26): 0.8767, an ablation</title></circle>
<circle cx="362.0" cy="85.1" r="10" fill="transparent"><title>Evaluation 27 (design C26): 0.8767, an ablation</title></circle>
<circle cx="373.5" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 28 (design C27): 0.9667, an edit</title></circle>
<circle cx="373.5" cy="37.6" r="10" fill="transparent"><title>Evaluation 28 (design C27): 0.9667, an edit</title></circle>
<circle cx="385.1" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 29 (design C28): 0.9667, an edit</title></circle>
<circle cx="385.1" cy="37.6" r="10" fill="transparent"><title>Evaluation 29 (design C28): 0.9667, an edit</title></circle>
<circle cx="396.6" cy="42.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 30 (design C29): 0.9567, a settings move</title></circle>
<circle cx="396.6" cy="42.9" r="10" fill="transparent"><title>Evaluation 30 (design C29): 0.9567, a settings move</title></circle>
<circle cx="408.2" cy="48.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 31 (design C30): 0.9467, an edit</title></circle>
<circle cx="408.2" cy="48.2" r="10" fill="transparent"><title>Evaluation 31 (design C30): 0.9467, an edit</title></circle>
<circle cx="419.7" cy="69.3" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 32 (design C31): 0.9067, a new design</title></circle>
<circle cx="419.7" cy="69.3" r="10" fill="transparent"><title>Evaluation 32 (design C31): 0.9067, a new design</title></circle>
<circle cx="431.2" cy="35.8" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 33 (design C32): 0.97, a settings move</title></circle>
<circle cx="431.2" cy="35.8" r="10" fill="transparent"><title>Evaluation 33 (design C32): 0.97, a settings move</title></circle>
<circle cx="442.8" cy="65.8" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 34 (design C33): 0.9133, an ablation</title></circle>
<circle cx="442.8" cy="65.8" r="10" fill="transparent"><title>Evaluation 34 (design C33): 0.9133, an ablation</title></circle>
<circle cx="454.3" cy="55.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 35 (design C35): 0.9333, an edit</title></circle>
<circle cx="454.3" cy="55.2" r="10" fill="transparent"><title>Evaluation 35 (design C35): 0.9333, an edit</title></circle>
<circle cx="465.8" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 36 (design C36): 0.9667, an edit</title></circle>
<circle cx="465.8" cy="37.6" r="10" fill="transparent"><title>Evaluation 36 (design C36): 0.9667, an edit</title></circle>
<circle cx="477.4" cy="129.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 37 (design C37): 0.7933, a settings move</title></circle>
<circle cx="477.4" cy="129.1" r="10" fill="transparent"><title>Evaluation 37 (design C37): 0.7933, a settings move</title></circle>
<circle cx="488.9" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 38 (design C38): 0.9667, an edit</title></circle>
<circle cx="488.9" cy="37.6" r="10" fill="transparent"><title>Evaluation 38 (design C38): 0.9667, an edit</title></circle>
<circle cx="500.5" cy="37.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 39 (design C39): 0.9667, an edit</title></circle>
<circle cx="500.5" cy="37.6" r="10" fill="transparent"><title>Evaluation 39 (design C39): 0.9667, an edit</title></circle>
<circle cx="512.0" cy="41.1" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>Evaluation 40 (design C40): 0.96, a settings move</title></circle>
<circle cx="512.0" cy="41.1" r="10" fill="transparent"><title>Evaluation 40 (design C40): 0.96, a settings move</title></circle>
<circle cx="431.2" cy="35.8" r="5.5" fill="var(--evo-series)" stroke="var(--evo-surface)" stroke-width="2"/>
<text x="524" y="276.0" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Baseline</text>
<text x="524" y="293.0" font-size="15" font-weight="600" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-ink)">0.5</text>
<text x="524" y="51.8" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Selected</text>
<text x="524" y="68.8" font-size="15" font-weight="600" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-ink)">0.97</text>
<circle cx="182" cy="250" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"/>
<text x="192" y="254" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">each evaluation</text>
<line x1="300" y1="250" x2="320" y2="250" stroke="var(--evo-series)" stroke-width="2"/>
<text x="326" y="254" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">best validation accuracy so far</text>
</svg>
</div>

40 training runs, 39 designs. Hover over a point to see the design and the move that produced it.

## Search history

These are the evaluations that raised the best score.

| Evaluation | Move | Change | Validation accuracy |
|---|---|---|---|
| 1 | baseline | linear classifier on the raw coordinates | 0.500 |
| 2 | new design | squares and products of the coordinates as inputs | 0.540 |
| 4 | edit | a hidden layer | 0.633 |
| 5 | new design | distance from the centre as an input, with a hidden layer | 0.917 |
| 8 | edit | a second, narrower layer | 0.957 |
| 11 | new design | two wider hidden layers | 0.960 |
| 14 | new design | sine and cosine of the radius as inputs | 0.967 |
| 17 | edit of 14 | a second layer | 0.970 |

The other 32 evaluations did not improve on the best at the time. That ratio is normal.

Evaluation 23 retrained design C17 on a new seed and got 0.967. A design with two runs is ranked by
their mean, which is why C17 is second on the leaderboard and C32, a later variant, is first.

## Code changes

The search can only change code between the markers. The model block at the start:

```python
# EVOLVE-BLOCK-START name=model kind=structure role=network
HIDDEN = []            # no hidden layer: a linear classifier
ACTIVATION = "tanh"

def features(x):
    return x
# EVOLVE-BLOCK-END
```

The same block in the selected design:

```python
HIDDEN = [12, 8]
ACTIVATION = "tanh"

def features(x):
    r = np.sqrt((x ** 2).sum(1))
    return np.stack([x[:, 0], x[:, 1], np.sin(6.0 * r), np.cos(6.0 * r)], axis=1)
```

`evoloop show demo C32 --name first` prints a design's code, its parent, and how it scored.

## The skill

The example's brief names a skill:

```yaml
run:
  type: explore_then_exploit
  skill: model-performance
```

evoloop copied that skill to `demo/skills/model-performance/skill.yaml` when you confirmed the brief.
Each time a design was written, the writer was sent the skill's instructions along with the parent's
code and the results so far. In this example the writer is a script and ignores them. With an LLM
backend the same file is what tells the agent how to approach the task, and you can edit it.

## Steering

```
evoloop brief demo --answer budget.evaluations=120 --confirm "Your Name"
evoloop run demo --name second &
evoloop set demo --name second schedule.novelty=0.8 --by "Your Name"
evoloop set demo --name second evaluation.allowance=200 --by "Your Name"
evoloop status demo --name second
```

The first `set` takes effect from the next design. The second shortens training, which changes what a
score means, so evoloop starts a new comparison period: it retrains the leading designs at the new
length and stops ranking new scores against old ones. Both changes are listed in the report under
"Steering ledger".

Designs here train in a fraction of a second, so the search may finish before a command arrives. If so,
run `evoloop run demo --name second` again and the change is applied then.

## Limits of the example

The proposals are scripted: a fixed list of new designs and simple edits. The example shows the
mechanics (the loop, the records, steering) on real training runs. It says nothing about what an LLM
would propose or how good the result would be on a real task.

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


A second example searches for a formula that fits a dataset, where a lower score is better:
`evoloop example demo2 --kind formula`.

Next: [Set up a project](setting-up.md).
