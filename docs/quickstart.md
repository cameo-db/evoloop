# Run the CPU demo

The package carries a small search: find a formula that fits a dataset. Scripted proposals stand in for
a model, so it needs no API key and no GPU, costs nothing, and finishes in under a minute. It exercises
every part of the loop.

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

`evoloop run` returns when the budget of 24 evaluations is spent:

```
run first: the budget of 24 evaluations is spent
report: demo/runs/first/report.md
```

Then `evoloop leaderboard demo --name first` shows the designs, best first:

```
| kind   | model | lineage | family                  | score    | state | length | fits |
| design | C7    | L5      | modulated trigonometric | 0.012471 | full  | 600    | 1    |
| design | C19   | L5      | modulated trigonometric | 0.012472 | full  | 600    | 1    |
...
| baseline | C1 | L1    | baseline                | 16.188   | full  | 600    | 1    |
```

<div class="evo-chart">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 320" role="img" aria-label="Validation score of each design in the CPU demo, and the best so far, over 25 scored runs">
<rect width="640" height="320" rx="8" fill="var(--evo-surface)"/>
<line x1="64" y1="274.0" x2="508" y2="274.0" stroke="var(--evo-grid)" stroke-width="1"/>
<text x="56" y="278.0" text-anchor="end" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">0.01</text>
<line x1="64" y1="210.0" x2="508" y2="210.0" stroke="var(--evo-grid)" stroke-width="1"/>
<text x="56" y="214.0" text-anchor="end" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">0.1</text>
<line x1="64" y1="146.0" x2="508" y2="146.0" stroke="var(--evo-grid)" stroke-width="1"/>
<text x="56" y="150.0" text-anchor="end" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">1</text>
<line x1="64" y1="82.0" x2="508" y2="82.0" stroke="var(--evo-grid)" stroke-width="1"/>
<text x="56" y="86.0" text-anchor="end" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">10</text>
<line x1="64" y1="18.0" x2="508" y2="18.0" stroke="var(--evo-grid)" stroke-width="1"/>
<text x="56" y="22.0" text-anchor="end" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">100</text>
<text x="64.0" y="292" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">1</text>
<text x="138.0" y="292" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">5</text>
<text x="212.0" y="292" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">9</text>
<text x="286.0" y="292" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">13</text>
<text x="360.0" y="292" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">17</text>
<text x="434.0" y="292" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">21</text>
<text x="508.0" y="292" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">25</text>
<text x="286.0" y="312" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Scored run</text>
<text transform="translate(16 146.0) rotate(-90)" text-anchor="middle" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Validation score (log scale; lower is better)</text>
<line x1="64" y1="68.6" x2="508" y2="68.6" stroke="var(--evo-soft)" stroke-width="1.5" stroke-dasharray="5 4"/>
<text x="518" y="66.6" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Baseline</text>
<text x="518" y="83.6" font-size="15" font-weight="600" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-ink)">16.19</text>
<path d="M64.0 68.6 H82.5 V76.2 H101.0 V77.3 H156.5 V77.3 H175.0 V267.9 H230.5 V267.9 H508.0" fill="none" stroke="var(--evo-series)" stroke-width="2" stroke-linejoin="round"/>
<circle cx="64.0" cy="68.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C1 (R1): 16.19, the baseline</title></circle>
<circle cx="64.0" cy="68.6" r="10" fill="transparent"><title>C1 (R1): 16.19, the baseline</title></circle>
<circle cx="82.5" cy="76.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C2 (R2): 12.31, new_approach</title></circle>
<circle cx="82.5" cy="76.2" r="10" fill="transparent"><title>C2 (R2): 12.31, new_approach</title></circle>
<circle cx="101.0" cy="77.3" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C3 (R3): 11.83, new_approach</title></circle>
<circle cx="101.0" cy="77.3" r="10" fill="transparent"><title>C3 (R3): 11.83, new_approach</title></circle>
<circle cx="119.5" cy="68.6" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C4 (R4): 16.2, structural_change</title></circle>
<circle cx="119.5" cy="68.6" r="10" fill="transparent"><title>C4 (R4): 16.2, structural_change</title></circle>
<circle cx="138.0" cy="76.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C5 (R5): 12.33, new_approach</title></circle>
<circle cx="138.0" cy="76.2" r="10" fill="transparent"><title>C5 (R5): 12.33, new_approach</title></circle>
<circle cx="156.5" cy="77.3" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C6 (R6): 11.83, settings_move</title></circle>
<circle cx="156.5" cy="77.3" r="10" fill="transparent"><title>C6 (R6): 11.83, settings_move</title></circle>
<circle cx="175.0" cy="267.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C7 (R7): 0.01247, new_approach</title></circle>
<circle cx="175.0" cy="267.9" r="10" fill="transparent"><title>C7 (R7): 0.01247, new_approach</title></circle>
<circle cx="193.5" cy="76.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C8 (R8): 12.31, structural_change</title></circle>
<circle cx="193.5" cy="76.2" r="10" fill="transparent"><title>C8 (R8): 12.31, structural_change</title></circle>
<circle cx="212.0" cy="77.4" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C9 (R9): 11.81, new_approach</title></circle>
<circle cx="212.0" cy="77.4" r="10" fill="transparent"><title>C9 (R9): 11.81, new_approach</title></circle>
<circle cx="230.5" cy="267.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C10 (R10): 0.01247, ablation</title></circle>
<circle cx="230.5" cy="267.9" r="10" fill="transparent"><title>C10 (R10): 0.01247, ablation</title></circle>
<circle cx="249.0" cy="76.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C11 (R11): 12.02, new_approach</title></circle>
<circle cx="249.0" cy="76.9" r="10" fill="transparent"><title>C11 (R11): 12.02, new_approach</title></circle>
<circle cx="267.5" cy="79.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C12 (R12): 11.07, new_approach</title></circle>
<circle cx="267.5" cy="79.2" r="10" fill="transparent"><title>C12 (R12): 11.07, new_approach</title></circle>
<circle cx="286.0" cy="264.4" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C13 (R13): 0.01414, settings_move</title></circle>
<circle cx="286.0" cy="264.4" r="10" fill="transparent"><title>C13 (R13): 0.01414, settings_move</title></circle>
<circle cx="304.5" cy="76.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C14 (R14): 12.31, new_approach</title></circle>
<circle cx="304.5" cy="76.2" r="10" fill="transparent"><title>C14 (R14): 12.31, new_approach</title></circle>
<circle cx="323.0" cy="76.0" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C15 (R15): 12.41, structural_change</title></circle>
<circle cx="323.0" cy="76.0" r="10" fill="transparent"><title>C15 (R15): 12.41, structural_change</title></circle>
<circle cx="341.5" cy="77.4" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C16 (R16): 11.82, new_approach</title></circle>
<circle cx="341.5" cy="77.4" r="10" fill="transparent"><title>C16 (R16): 11.82, new_approach</title></circle>
<circle cx="360.0" cy="75.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C17 (R17): 12.47, structural_change</title></circle>
<circle cx="360.0" cy="75.9" r="10" fill="transparent"><title>C17 (R17): 12.47, structural_change</title></circle>
<circle cx="378.5" cy="79.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C18 (R18): 11.07, settings_move</title></circle>
<circle cx="378.5" cy="79.2" r="10" fill="transparent"><title>C18 (R18): 11.07, settings_move</title></circle>
<circle cx="397.0" cy="267.9" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C19 (R19): 0.01247, settings_move</title></circle>
<circle cx="397.0" cy="267.9" r="10" fill="transparent"><title>C19 (R19): 0.01247, settings_move</title></circle>
<circle cx="415.5" cy="79.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C20 (R20): 11.07, structural_change</title></circle>
<circle cx="415.5" cy="79.2" r="10" fill="transparent"><title>C20 (R20): 11.07, structural_change</title></circle>
<circle cx="434.0" cy="75.8" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C21 (R21): 12.5, structural_change</title></circle>
<circle cx="434.0" cy="75.8" r="10" fill="transparent"><title>C21 (R21): 12.5, structural_change</title></circle>
<circle cx="452.5" cy="77.3" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C22 (R22): 11.85, new_approach</title></circle>
<circle cx="452.5" cy="77.3" r="10" fill="transparent"><title>C22 (R22): 11.85, new_approach</title></circle>
<circle cx="471.0" cy="75.8" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C10 (R23): 12.5, a re-check of the leader on a new seed</title></circle>
<circle cx="471.0" cy="75.8" r="10" fill="transparent"><title>C10 (R23): 12.5, a re-check of the leader on a new seed</title></circle>
<circle cx="489.5" cy="77.3" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C23 (R24): 11.82, graft</title></circle>
<circle cx="489.5" cy="77.3" r="10" fill="transparent"><title>C23 (R24): 11.82, graft</title></circle>
<circle cx="508.0" cy="79.2" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"><title>C24 (R25): 11.08, new_approach</title></circle>
<circle cx="508.0" cy="79.2" r="10" fill="transparent"><title>C24 (R25): 11.08, new_approach</title></circle>
<circle cx="508.0" cy="267.9" r="5" fill="var(--evo-series)" stroke="var(--evo-surface)" stroke-width="2"/>
<text x="518" y="259.9" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">Selected</text>
<text x="518" y="276.9" font-size="15" font-weight="600" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-ink)">0.01247</text>
<circle cx="74" cy="28" r="4" fill="var(--evo-dot)" stroke="var(--evo-surface)" stroke-width="2"/>
<text x="84" y="32" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">each design</text>
<line x1="166" y1="28" x2="186" y2="28" stroke="var(--evo-series)" stroke-width="2"/>
<text x="192" y="32" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif" fill="var(--evo-soft)">best so far</text>
</svg>
</div>

In this run the baseline formula scored 16.19 and the selected one 0.01247. The score is the validation
error plus 0.002 for each fitted constant, so lower is better and a simpler formula wins a tie. Each
point is one design; hover over it for its name and the move that made it.

Three things worth noticing in the figure:

- **Most designs did not help.** That is normal: the search found one family that fits (run 7) and
  spent later moves refining it.
- **The leader was checked.** Design C10 matched the best score, was fitted again on a new seed (run
  23), and scored 12.5 that time. The leaderboard ranks it by the mean of its fits, so C7 is selected.
- **These are scripted proposals.** They show that the machinery works, not what an agent can find.

To see the selected design, with its code, where it came from and what its writer predicted:

```
evoloop show demo C7 --name first
```

Use the design named at the top of your own leaderboard. The figure is drawn from the run's records by
`python tools/demo_figure.py demo/runs/first docs/assets`.

??? note "The numbers behind the figure"
    | Scored run | Design | Move | Validation score |
    |---|---|---|---|
    | 1 | C1 | baseline | 16.19 |
    | 2 | C2 | new_approach | 12.31 |
    | 3 | C3 | new_approach | 11.83 |
    | 4 | C4 | structural_change | 16.2 |
    | 5 | C5 | new_approach | 12.33 |
    | 6 | C6 | settings_move | 11.83 |
    | 7 | C7 | new_approach | 0.01247 |
    | 8 | C8 | structural_change | 12.31 |
    | 9 | C9 | new_approach | 11.81 |
    | 10 | C10 | ablation | 0.01247 |
    | 11 | C11 | new_approach | 12.02 |
    | 12 | C12 | new_approach | 11.07 |
    | 13 | C13 | settings_move | 0.01414 |
    | 14 | C14 | new_approach | 12.31 |
    | 15 | C15 | structural_change | 12.41 |
    | 16 | C16 | new_approach | 11.82 |
    | 17 | C17 | structural_change | 12.47 |
    | 18 | C18 | settings_move | 11.07 |
    | 19 | C19 | settings_move | 0.01247 |
    | 20 | C20 | structural_change | 11.07 |
    | 21 | C21 | structural_change | 12.5 |
    | 22 | C22 | new_approach | 11.85 |
    | 23 | C10 | re-check on a new seed | 12.5 |
    | 24 | C23 | graft | 11.82 |
    | 25 | C24 | new_approach | 11.08 |

## What the run leaves behind

The run's folder is `demo/runs/first/`.

| File | Holds |
|---|---|
| `report.md` | the leaderboard, the population, what each mode and move returned, the ledger, the agents' spend |
| `status.json` | the same in brief, rewritten every turn while the run goes |
| `runs.jsonl`, `models.jsonl`, `recipes.jsonl` | every training run, architecture and recipe |
| `ledger.jsonl` | every change to the run and every note, with who made it |
| `calls.jsonl`, `replies/` | every agent call: what it was shown, what it answered, what it cost |
| `study.json` | the run in the CAMEO entry format |

## Try steering it

Start a second, longer run and change it while it goes:

```
evoloop brief demo --answer budget.evaluations=80 --confirm "Your Name"
evoloop run demo --name second &
evoloop set demo --name second schedule.novelty=0.8 --by "Your Name" --reason "try wider"
evoloop set demo --name second evaluation.allowance=450 --by "Your Name" --reason "shorter fits"
evoloop note demo --name second "Prefer forms with few constants." --roles writer --by "Your Name"
evoloop status demo --name second
```

The report's *Steering ledger* section shows each entry with the number of evaluations at which it was
applied. Shortening the fits changes what a score means, so the second change starts a new comparison
period: the leaders are fitted again at the new length, and earlier scores stop deciding selection.

The example's designs train in a fraction of a second, so a run may end before a request arrives. A
request made to a run that has ended waits, and is applied when the run is continued with the same
`evoloop run` command.

## Next

- [Use your own project](setting-up.md): mark the code, write the evaluator, answer the questions.
- [What do you want to optimize?](guides/index.md): a starting configuration for each goal.
- Before spending on real agents, dry-run your project with `agents.backend: stub`.
