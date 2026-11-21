---
hide:
  - navigation
  - toc
---

<div class="evo-hero" markdown>
<div class="evo-hero-text" markdown>

# Optimize the parts of your code you choose.

Mark the code that may change and supply a scoring function. Agents propose code edits, or a built-in
optimizer tunes fixed settings. evoloop evaluates the variants within your budget, and records every
decision so you can steer the search while it runs.

[Run the CPU demo](quickstart.md){ .md-button .md-button--primary }
[Use my own project](setting-up.md){ .md-button }

The demo runs locally with scripted proposals: no API key, no GPU, under a minute.
{ .evo-fine }

</div>
<div class="evo-hero-figure" markdown>

**Fitting a formula to data** · the CPU demo, a budget of 24 evaluations
{ .evo-caption }

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

Scripted proposals stand in for a model here: this shows the machinery, not what an agent can find.
[Reproduce it](quickstart.md)
{ .evo-fine }

</div>
</div>

## How a search runs

<div class="grid cards" markdown>

-   **1. Define the experiment**

    ---

    Mark the blocks that may change, tell evoloop how to score one design, and read the plan before
    anything runs.

    [Use my own project](setting-up.md)

-   **2. Run and steer**

    ---

    The search proposes and evaluates changes, one job per design. Adjust its direction as results
    arrive; every change is recorded.

    [Steering a run](steering.md)

-   **3. Compare the designs**

    ---

    Open the leaderboard, inspect the selected design's code and history, and save the study as JSON for
    the CAMEO database.

    [What a run leaves behind](records.md)

</div>

## What do you want to optimize?

Each goal is a different search. Its guide gives a starting configuration, why it fits, what your
evaluator must report, and how to read the result.

<div class="grid cards" markdown>

-   [**Tune hyperparameters**](guides/settings-tuning.md)

    Numbers only, by a Bayesian estimator. No agent calls.

-   [**Improve a model's score**](guides/model-performance.md)

    The architecture is open; one number to raise.

-   [**Train a fixed architecture better**](guides/model-training-recipe.md)

    The loss, optimizer, schedule and augmentation.

-   [**Find a smaller or faster model**](guides/model-efficiency.md)

    One cheaper model at about the same score.

-   [**Find the best model at several sizes**](guides/model-size-frontier.md)

    A whole trade-off curve to choose from.

-   [**Distil a student from a teacher**](guides/model-distillation.md)

    A small model that keeps a large one's accuracy.

-   [**Make an algorithm or pipeline faster**](guides/algorithm-runtime.md)

    The same output, in less time or memory.

-   [**All optimization guides**](guides/index.md)

    Ensembles, fine-tuning, interpretable models, bioinformatics methods.

</div>

## The skill library

Each goal above is a **skill**: one file that holds the settings that suit the task, guidance for the
agents, "if the results show this, do that" diagnoses, and what your evaluator must report. evoloop
comes with a library of twelve, and the library is meant to grow.

| Domain | Skill | For |
|---|---|---|
| Models | [`model-performance`](guides/model-performance.md) | the best score, nothing else weighed |
| | [`model-distillation`](guides/model-distillation.md) | a smaller or faster student that matches a teacher |
| | [`model-efficiency`](guides/model-efficiency.md) | the same score at a lower cost in parameters or time |
| | [`model-size-frontier`](guides/model-size-frontier.md) | the best model at every size or speed across a broad range |
| | [`model-training-recipe`](guides/model-training-recipe.md) | a better score from the same architecture, by training it better |
| | [`model-ensemble-members`](guides/model-ensemble-members.md) | strong models whose errors do not coincide |
| | [`model-finetuning`](guides/model-finetuning.md) | the best score starting from a pretrained model |
| | [`model-mechanistic`](guides/model-mechanistic.md) | an interpretable or biophysical model, improved without losing its meaning |
| Settings | [`settings-tuning`](guides/settings-tuning.md) | the best settings of fixed code, with no agent calls |
| Algorithms | [`algorithm-runtime`](guides/algorithm-runtime.md) | the same results in less time or memory |
| Bioinformatics | [`bioinformatics-algorithm`](guides/bioinformatics-algorithm.md) | better accuracy against a truth set |
| Pipelines | [`data-pipeline`](guides/data-pipeline.md) | the same output in less time, memory or cost |

**It is extensible.**

- **Edit one.** Your search gets its own copy of every skill it uses, in `mysearch/skills/`. Change the
  guidance, add a diagnosis from your own experience; the library's original is untouched.
- **Combine them.** `run.skill: [model-distillation, model-size-frontier]` gives a family of students.
- **Write your own.** Copy the nearest one with `evoloop skills NAME --copy DIR`, rename it, and point
  `run.skill` at it.
- **Add it to the library.** A skill is a folder with one file; a pull request adds it for everyone.

`evoloop skills` lists the library and `evoloop skills --search WORDS` searches it.
[How skills work](skills.md) · [Every skill in full](skill-library.md)

## Keep and share the result

Every search ends with a `study.json`: every model, training recipe and run in one file, in the format of
[CAMEO](https://cameo-db.github.io), a public database of models, how they were trained, and how they
performed. [How to save the study as JSON and deposit it](records.md#saving-the-study-as-json-and-depositing-it-in-cameo).

## What it has been shown to do

evoloop passes its tests on the built-in demo with scripted proposals, and has run that demo on a Slurm
cluster. It has **not** yet been run with a real model on a real training task, and no comparison of
its search settings has been made. The guides give reasoned starting points, not measured ones.
[Status and limits](status.md) says exactly what has been run.

<div class="grid cards" markdown>

-   **Understand it**

    [How a search works](how-it-works.md) · [How each choice changes the search](choices.md) ·
    [How it compares with established methods](compared.md)

-   **Look something up**

    [Commands](commands.md) · [Fields of the brief](fields.md) · [The evaluator contract](project-contract.md) ·
    [Skill library](skill-library.md)

</div>
