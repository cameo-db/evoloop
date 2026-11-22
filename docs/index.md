---
hide:
  - navigation
  - toc
---

<div class="evo-lead" markdown>

# An optimization loop for models, algorithms, and data pipelines

evoloop improves code you already have. Mark the parts that may change and supply a script that scores a
version. An LLM agent proposes changes, evoloop runs your script on each one, and the scores decide what
is tried next. You set the budget.

People use it to raise a model's accuracy, tune hyperparameters, distil a model into a smaller one, or
make an algorithm or pipeline faster with its output checked.

[Browse the skills](which-search.md){ .md-button .md-button--primary }
[Set up a project](setting-up.md){ .md-button }

</div>

<div class="evo-loop evo-widget" id="evo-loop">
  <div class="evo-loop-goals"></div>
  <p class="evo-loop-skillline">The skill <a class="evo-loop-skill" data-base="guides/" href="guides/model-performance/">model-performance</a> is read at every stage. It tells the agent what to try, says what your script must report, and sets which designs are kept.</p>
  <div class="evo-loop-stages">
    <div class="evo-stage">
      <span class="evo-step">1</span>
      <h3>Propose a change</h3>
      <p data-stage="propose">The agent is told to work out what limits the current best model (capacity, optimization or generalization) and to make one change that addresses it.</p>
    </div>
    <div class="evo-arrow" aria-hidden="true">→</div>
    <div class="evo-stage">
      <span class="evo-step">2</span>
      <h3>Evaluate it</h3>
      <p data-stage="evaluate">Your script trains the design and reports its validation score.</p>
    </div>
    <div class="evo-arrow" aria-hidden="true">→</div>
    <div class="evo-stage">
      <span class="evo-step">3</span>
      <h3>Choose what to try next</h3>
      <p data-stage="choose">Several families of designs are kept. The best ones get more edits, and new families keep being started.</p>
    </div>
  </div>
  <div class="evo-loop-back" aria-hidden="true"></div>
  <p class="evo-loop-note">The loop repeats until the budget is spent. <a class="evo-loop-link" data-base="which-search/" href="which-search/">Preview a search with this skill</a></p>
</div>

## Skills

A skill is a text file for one kind of optimization. It holds instructions for the agents, the settings
that suit the task, and a list of what your scoring script has to report. evoloop ships with thirteen.
You can edit any of them, combine two, or write your own.

<div class="grid cards" markdown>

-   **Models**

    ---

    [Improve a model's score](guides/model-performance.md) ·
    [Train a fixed architecture better](guides/model-training-recipe.md) ·
    [Tune hyperparameters](guides/settings-tuning.md) ·
    [Adapt a pretrained model](guides/model-finetuning.md)

-   **Smaller and faster models**

    ---

    [Shrink a model by distillation](guides/model-efficiency.md) ·
    [Distil an ensemble or a larger model](guides/model-distillation.md) ·
    [Best model at several sizes](guides/model-size-frontier.md)

-   **Algorithms and pipelines**

    ---

    [Faster algorithm](guides/algorithm-runtime.md) ·
    [Cheaper data pipeline](guides/data-pipeline.md) ·
    [Bioinformatics method](guides/bioinformatics-algorithm.md)

-   **Other**

    ---

    [Ensemble members](guides/model-ensemble-members.md) ·
    [Interpretable models](guides/model-mechanistic.md) ·
    [Bayesian tuning without agents](guides/settings-tuning-bayesian.md) ·
    [Write your own](skills.md)

</div>

## Run types

The skill says what to optimize. The run type says how to spend the evaluations: explore many ideas,
refine a model that already works, or explore first and refine later. Any skill can be used with any
run type. [Choose a skill and a run type](which-search.md) shows the search each combination produces.

## Try it

A small search ships with the package. It runs on a laptop in half a minute and needs no API key.
[Worked example](quickstart.md).

## Status

Version 0.2 passes its tests on two built-in examples in which a script stands in for the LLM. It has
not been run with a real LLM on a real training task, and its search settings have not been compared
with each other. [Status and limits](status.md).

[How a search works](how-it-works.md) · [Comparison with FunSearch and AlphaEvolve](compared.md) ·
[Reference](reference.md)
