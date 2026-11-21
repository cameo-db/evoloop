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
[Set it up with an agent](#you-make-five-decisions-an-agent-can-do-the-rest){ .md-button }

The demo runs locally with scripted proposals: no API key, no GPU, under a minute.
{ .evo-fine }

</div>
<div class="evo-hero-figure" markdown>

**A toy model search** · a small classifier on two spirals, 40 models, each trained once on a CPU
{ .evo-caption }

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

Each point is a model that was really trained; the line is the best so far. The proposals are scripted here, so
this shows how a search proceeds, not what an agent would find.
[Reproduce it](quickstart.md)
{ .evo-fine }

</div>
</div>

## You make five decisions; an agent can do the rest

evoloop has many settings, and you are not meant to work through them. It is built to be set up **with
a coding agent**: open the repository in Claude Code (or another agent that can read files and run
commands) and say *"set up an evoloop search for my project"*. The agent follows
[AGENTS.md](https://github.com/cameo-db/evoloop/blob/main/AGENTS.md): it reads your code, marks the
blocks, writes the evaluator, proposes an answer to each question with its reason, and asks you only
what it cannot work out. Everything it proposes is shown to you before anything runs.

What is yours to decide:

| Decision | Why it cannot be defaulted |
|---|---|
| **What to optimize** | A better score, a smaller model, tuned settings and a faster algorithm are different searches. [Pick a goal](guides/index.md) |
| **What may change** | The search only touches the blocks you allow. Everything else is frozen |
| **How a design is scored** | The search optimizes exactly this number. You also say how much it varies between two runs of the same design |
| **How much to spend** | Evaluations (your compute) and agent dollars. Both are caps the search cannot exceed |
| **Hard limits**, if any | A largest size or slowest speed you would accept. Enforced by code |

Everything else has a default chosen from those answers and the size of your budget, is shown in the
plan with where it came from, and can be changed while the search runs. Skip it until a result gives
you a reason to change it. Running on a cluster? [Describe the machine once](servers.md).

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

evoloop passes its tests on its two built-in examples with scripted proposals, and has run one of them on a Slurm
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
