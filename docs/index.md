---
hide:
  - navigation
  - toc
---

<div class="evo-lead" markdown>

![evoloop](assets/evoloop-logo.png#only-light){ .evo-wordmark-img }
![evoloop](assets/evoloop-logo-dark.png#only-dark){ .evo-wordmark-img }
{ .evo-wordmark }

# An optimization loop for models, algorithms, and data pipelines

Give evoloop working code and a way to score it. You choose which parts may change. AI agents propose
changes, evoloop evaluates each version, and the results guide what it tries next. For numerical
settings, a built-in optimizer can propose the changes with no agent at all.

Use it to improve a model's accuracy, find a smaller model at a similar score, tune a training recipe,
or make a pipeline faster while checking that its outputs stay correct.

[Explore search options](which-search.md){ .md-button .md-button--primary }
[Set up a project](setting-up.md){ .md-button }

</div>

<div class="evo-loop evo-widget" id="evo-loop">
  <div class="evo-loop-goals"></div>
  <div class="evo-loop-stages">
    <div class="evo-stage">
      <span class="evo-step">1</span>
      <h3>Propose a change</h3>
      <p data-stage="propose">An agent writes a new architecture, edits one part of an earlier design, or combines two designs.</p>
    </div>
    <div class="evo-arrow" aria-hidden="true">→</div>
    <div class="evo-stage">
      <span class="evo-step">2</span>
      <h3>Evaluate it</h3>
      <p data-stage="evaluate">Your script trains the model and reports its validation score.</p>
    </div>
    <div class="evo-arrow" aria-hidden="true">→</div>
    <div class="evo-stage">
      <span class="evo-step">3</span>
      <h3>Choose what to try next</h3>
      <p data-stage="choose">Several families of designs are kept going. The strongest get more edits, and new families keep being tried.</p>
    </div>
  </div>
  <div class="evo-loop-back" aria-hidden="true"></div>
  <p class="evo-loop-note">Each result feeds the next proposal, until the budget you set is spent. <a class="evo-loop-link" data-base="which-search/" href="which-search/">Preview this search</a></p>
</div>

## A goal, and a way to spend the budget

Two choices shape a search, and they are separate.

The **goal** is what you want: a more accurate model, a smaller one, a faster pipeline. It decides what
may change, what your scoring script has to measure, and what the agents are told.

The **run type** is how the evaluations are spent. A search can explore broadly, refine a model that
already works, or start broad and narrow later. The same goal can be pursued any of these ways.

[Which search should I run?](which-search.md) puts the two together and shows the search that results.

## What it is used for

<div class="grid cards" markdown>

-   **Better models**

    ---

    [Improve a model's score](guides/model-performance.md) with the architecture open,
    [train a fixed architecture better](guides/model-training-recipe.md),
    [tune hyperparameters](guides/settings-tuning.md), or
    [adapt a pretrained model](guides/model-finetuning.md).

-   **Smaller and faster models**

    ---

    [One cheaper model](guides/model-efficiency.md) at about the same score,
    [the best model at several sizes](guides/model-size-frontier.md), or
    [a student distilled from a teacher](guides/model-distillation.md).

-   **Algorithms and pipelines**

    ---

    [A faster algorithm](guides/algorithm-runtime.md) or
    [a cheaper data pipeline](guides/data-pipeline.md) with outputs checked against a reference, or
    [a more accurate bioinformatics method](guides/bioinformatics-algorithm.md).

-   **Something else**

    ---

    [Ensemble members](guides/model-ensemble-members.md),
    [interpretable models](guides/model-mechanistic.md), or a goal of your own:
    each goal is an [editable file](skills.md) of settings and advice for the agents.

</div>

## See a worked example

The package carries a small search you can run on a laptop in half a minute, with no API key and no
GPU. It trains 39 small classifiers and takes the validation accuracy from 0.50 to 0.97.
[Run the demo](quickstart.md) walks through it: the commands, the leaderboard, the winning design's
code, and how to change the search while it runs.

## Where this stands

evoloop passes its tests on two built-in examples with scripted proposals standing in for a language
model. It has not yet been run with a real model on a real training task, and its settings have not
been compared against each other. [Status and limits](status.md) lists what has been run.

To go deeper: [how one step of a search works](how-it-works.md),
[how evoloop relates to FunSearch and AlphaEvolve](compared.md), and the
[reference](reference.md).
