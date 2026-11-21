# Skill library

Every skill that comes with evoloop. This page is written from the skill files themselves (`evoloop skills --markdown`). Each is a template: a search copies the ones it names into its own `skills/` folder, and that copy is yours to edit. [Edit or write a skill](skills.md) explains how, and [Skill file format](skill-format.md) is the reference for the file.

| Skill | Domain | For |
|---|---|---|
| [`model-performance`](#model-performance) | model | the best score, nothing else weighed |
| [`model-distillation`](#model-distillation) | model | a smaller or faster model that matches a larger model or an ensemble |
| [`model-efficiency`](#model-efficiency) | model | the same score at a lower cost in parameters or time |
| [`model-ensemble-members`](#model-ensemble-members) | model | a set of strong models whose errors do not coincide |
| [`model-finetuning`](#model-finetuning) | model | the best score on a task starting from a pretrained model |
| [`model-mechanistic`](#model-mechanistic) | model | a better fit without losing what the parameters mean |
| [`model-size-frontier`](#model-size-frontier) | model | the best model at every size or speed across a broad range |
| [`model-training-recipe`](#model-training-recipe) | model | a better score from the same architecture, by training it better |
| [`algorithm-runtime`](#algorithm-runtime) | algorithm | the same results in less time or memory |
| [`bioinformatics-algorithm`](#bioinformatics-algorithm) | bioinformatics | better accuracy against a truth set, at an acceptable run time |
| [`data-pipeline`](#data-pipeline) | pipeline | the same output from a pipeline in less time, memory or cost |
| [`settings-tuning`](#settings-tuning) | settings | the best values for the settings of fixed code |

## Model

### model-performance

**Raise a model's score.** Raise the validation score by whatever the open blocks allow. Size and speed are not weighed unless you set limits.

*When to choose it.* The default for model development. Choose something more specific when the goal is a smaller model (model-efficiency), a family across sizes (model-size-frontier), a student of a teacher (model-distillation), or when only the training recipe or the settings may change.

| | |
|---|---|
| Tags | accuracy, performance, architecture, general |
| Sets | nothing: guidance only |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5, in the guide |
| Needs from the evaluator | nothing special |
| Goes well with | `model-training-recipe` |
| Not with | `settings-tuning` |

[The guide for this goal](guides/model-performance.md) has the starting brief, the advice the agents are given and the diagnoses in full.

### model-distillation

**Distil a student from a teacher.** Train a smaller or faster student to match a teacher. The student's architecture and its training recipe (loss, optimizer, learning rate, regularization, augmentation) are both open.

*When to choose it.* You have a strong model or ensemble that is too large or slow to use, and want a student that keeps its accuracy. Not for shrinking a model with no teacher (model-efficiency).

| | |
|---|---|
| Tags | distillation, student, teacher, compression, ensemble, augmentation |
| Sets | `report.columns`, `space.preset`, `variation.approach_seeds`, `variation.approaches` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5, in the guide |
| Needs from the evaluator | the training script must produce the teacher's outputs (or read stored ones) and train the student against them; the loss and augmentation blocks should be marked as open recipe blocks; to rank on speed or size, report `parameters` and `inference_speed.examples_per_s` in result.json; then `strategy.mechanism: pareto` or `limits` can use them; if the teacher is an ensemble, add a reference row for the ensemble and one for its best single member |
| Goes well with | `model-size-frontier`, `model-efficiency` |
| Not with | `settings-tuning` |

[The guide for this goal](guides/model-distillation.md) has the starting brief, the advice the agents are given and the diagnoses in full.

### model-efficiency

**Make one model smaller or faster.** Make the model smaller or faster while holding its score. Designs are selected on the trade-off between the score and size (or speed), and removal is the commonest move.

*When to choose it.* You have a model that scores well enough and costs too much. The aim is one cheaper model at about the same score. For a whole family across sizes use model-size-frontier; with a teacher available, model-distillation.

| | |
|---|---|
| Tags | efficiency, compression, pruning, size, speed, pareto, ablation |
| Sets | `report.columns`, `schedule.local_mix`, `strategy.mechanism`, `strategy.second_direction`, `strategy.second_metric` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 4, in the guide |
| Needs from the evaluator | report `parameters` in result.json (and `inference_speed.examples_per_s` to rank on speed: then set strategy.second_metric to examples_per_s and strategy.second_direction to maximize); set `limits` for the largest size or lowest speed you accept, and put those figures in the first progress line so that a design outside them costs seconds; add a reference row for the model you are trying to shrink |
| Goes well with | `model-distillation` |
| Not with | `settings-tuning`, `model-size-frontier` |

[The guide for this goal](guides/model-efficiency.md) has the starting brief, the advice the agents are given and the diagnoses in full.

### model-ensemble-members

**Find models that fail differently, for an ensemble.** Find models that are each good and that make different errors from one another, so that averaging them gains more than averaging copies of the best one.

*When to choose it.* You will average several models (as a final predictor, or as the teacher for model-distillation) and want members that add to each other. Not for a single best model.

| | |
|---|---|
| Tags | ensemble, diversity, behaviour, errors, averaging, teacher |
| Sets | `schedule.novelty`, `schedule.novelty_measure`, `schedule.phases`, `strategy.descriptors`, `strategy.mechanism` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 4, in the guide |
| Needs from the evaluator | report `signature` in result.json: a list of numbers saying where the model's errors fall (per class, per range of the target, or per held-out example); the groups are made from it; after the search, score the average of the best design of each group yourself; evoloop does not train or score ensembles |
| Goes well with | `model-distillation` |
| Not with | `settings-tuning`, `model-efficiency` |

[The guide for this goal](guides/model-ensemble-members.md) has the starting brief, the advice the agents are given and the diagnoses in full.

### model-finetuning

**Adapt a pretrained model to a task.** Start from a pretrained model and search over how to adapt it (what to freeze, what to add, the learning rates by layer, how long to train).

*When to choose it.* A pretrained model exists and the task has far less data than the model was trained on. Not for training from scratch.

| | |
|---|---|
| Tags | finetuning, pretrained, transfer, adapters, foundation model, freezing |
| Sets | `schedule.local_mix`, `schedule.novelty` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 4, in the guide |
| Needs from the evaluator | load the pretrained weights from a fixed path outside base/ (weights are not copied per design); mark as open the head, the choice of what is frozen, and the optimizer settings; leave the backbone's definition closed; add a reference row for the frozen backbone with a linear head |
| Goes well with | `model-training-recipe` |
| Not with | `settings-tuning` |

[The guide for this goal](guides/model-finetuning.md) has the starting brief, the advice the agents are given and the diagnoses in full.

### model-mechanistic

**Improve an interpretable or biophysical model.** Improve a model that is interpretable by design, where the parameters stand for something (motifs in filters, a graph of interactions, rates and affinities in a biophysical model). The structure that carries the meaning is kept.

*When to choose it.* The model is meant to be read, not only to predict: its parts stand for things. Not for making a black-box model explainable after the fact.

| | |
|---|---|
| Tags | interpretable, mechanistic, biophysical, motifs, interactions, constraints |
| Sets | `schedule.local_mix`, `schedule.novelty`, `space.must_keep`, `space.preset` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5, in the guide |
| Needs from the evaluator | optional, and worth doing: report a figure of how well the parts match what is known (the share of filters matching known motifs, recovered interactions, parameters within physical ranges) under diagnostics; it can then be a leaderboard column, a speciality metric, or the second figure of the pareto strategy; report `signature` (where the errors fall) so that designs with the same failure are told apart from ones that fail differently; mark as open only the blocks that define the interpretable parts and their combination; leave the data handling and the evaluation frozen |
| Goes well with | any |
| Not with | `settings-tuning` |

[The guide for this goal](guides/model-mechanistic.md) has the starting brief, the advice the agents are given and the diagnoses in full.

### model-size-frontier

**A family of models across sizes.** Find the best model at each size (or speed), from very small to large, so that the result is a whole trade-off curve to choose from and not one winner.

*When to choose it.* You need models for several budgets (a phone, a server, a screen of millions of inputs), or want to know what accuracy each size buys before choosing. For one cheaper model at a fixed score use model-efficiency.

| | |
|---|---|
| Tags | pareto, frontier, trade-off, size, speed, family, scaling, coverage |
| Sets | `report.columns`, `schedule.novelty`, `schedule.phases`, `strategy.descriptors`, `strategy.mechanism` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 4, in the guide |
| Needs from the evaluator | report `parameters` in result.json for every design; the bands are made from it; to band by speed instead, report `inference_speed.examples_per_s` and set strategy.descriptors to the name of that metric under diagnostics; set `limits` for the smallest and largest size worth having, so that designs outside the range are not trained |
| Goes well with | `model-distillation` |
| Not with | `settings-tuning`, `model-efficiency` |

[The guide for this goal](guides/model-size-frontier.md) has the starting brief, the advice the agents are given and the diagnoses in full.

### model-training-recipe

**Improve how a fixed model is trained.** The architecture is fixed; the training recipe is open (the loss, the optimizer, the learning-rate schedule, regularization, augmentation). Between tuning numbers and changing the model.

*When to choose it.* The architecture is settled (it is published, deployed, or the point of comparison) and the question is how well it can be trained. If only numbers change, settings-tuning is cheaper; if the model may change too, use model-performance with the recipe opened.

| | |
|---|---|
| Tags | recipe, training, loss, optimizer, schedule, regularization, augmentation |
| Sets | `schedule.local_mix`, `space.preset`, `space.roles` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5, in the guide |
| Needs from the evaluator | mark the loss, optimizer, schedule and augmentation as blocks with those roles; the model blocks stay closed; report the training score beside the validation score under diagnostics, so that fitting and generalising can be told apart; report `best_epoch` and `epochs_run` in result.json |
| Goes well with | `model-performance`, `model-finetuning` |
| Not with | `settings-tuning` |

[The guide for this goal](guides/model-training-recipe.md) has the starting brief, the advice the agents are given and the diagnoses in full.

## Algorithm

### algorithm-runtime

**Make an algorithm faster at the same output.** Speed up a piece of code (or cut its memory) while its output stays correct. The score is a measured time; a design whose output is wrong is rejected, not scored.

*When to choose it.* The code is correct and too slow or too hungry. The search needs a benchmark that checks the output and times the run. Not for improving what the algorithm computes (see bioinformatics-algorithm for accuracy against a truth set).

| | |
|---|---|
| Tags | speed, runtime, performance, optimization, complexity, memory, benchmark |
| Sets | `evaluation.screen_keep`, `schedule.local_mix`, `schedule.novelty` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5, in the guide |
| Needs from the evaluator | compare every design's output with a stored reference output and write `valid: false` with `rejected: "output differs"` when it does not match (exactly, or within a stated tolerance); time the run several times on a quiet machine with a fixed number of threads, and report the median as the score with objective.direction minimize; set evaluation.noise from the spread of repeats; keep a second set of inputs the search never sees, and report its timing under diagnostics.hidden; report peak memory under diagnostics if it matters, and bound it with `limits` |
| Goes well with | `data-pipeline`, `bioinformatics-algorithm` |
| Not with | `settings-tuning` |

[The guide for this goal](guides/algorithm-runtime.md) has the starting brief, the advice the agents are given and the diagnoses in full.

## Bioinformatics

### bioinformatics-algorithm

**Improve a bioinformatics algorithm.** Improve a method that analyses biological data (an aligner, a caller, a peak finder, a quantifier, a scoring function) against a truth set, without breaking the conventions of the formats and coordinates it works in.

*When to choose it.* The method has a measurable right answer on some data (simulated, curated, or orthogonally validated) and the aim is to do better on it. If the method is right and only slow, use algorithm-runtime.

| | |
|---|---|
| Tags | bioinformatics, genomics, sequence, alignment, variant calling, peak calling, benchmark, truth set |
| Sets | `schedule.local_mix`, `schedule.novelty` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5, in the guide |
| Needs from the evaluator | score against a truth set with a standard comparison for the task, and report precision, recall and their combination under diagnostics; the score should be one number that does not reward trading one for the other at a single threshold; use more than one dataset (another sample, depth or organism), and keep one the search never sees under diagnostics.hidden; check the output's format and coordinates before scoring, and write `valid: false` with the reason when they are wrong; report run time and peak memory under diagnostics, and bound them with `limits` if they matter |
| Goes well with | `algorithm-runtime` |
| Not with | `settings-tuning` |

[The guide for this goal](guides/bioinformatics-algorithm.md) has the starting brief, the advice the agents are given and the diagnoses in full.

## Pipeline

### data-pipeline

**Make a data processing pipeline faster or cheaper.** Speed up a multi-step data pipeline (reading, transforming, joining, writing) or cut its memory and cost, with its output unchanged.

*When to choose it.* A pipeline of several steps produces the right output too slowly or at too high a cost. For a single hot function use algorithm-runtime.

| | |
|---|---|
| Tags | pipeline, data processing, throughput, io, memory, etl, preprocessing, parallel |
| Sets | `evaluation.screen_keep`, `schedule.local_mix`, `schedule.novelty` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5, in the guide |
| Needs from the evaluator | run the pipeline on fixed sample data and compare its output with a stored reference (a checksum of sorted records, or row counts with value checks); write `valid: false` with the reason when it differs; report the cost as the score with objective.direction minimize: wall time as a median of repeats, or a figure that combines time and memory if both matter; report time per step and peak memory under diagnostics, so that the agents can see where the cost is; use sample data large enough that input and output costs resemble the real run, and keep a second sample the search never sees under diagnostics.hidden |
| Goes well with | `algorithm-runtime` |
| Not with | `settings-tuning` |

[The guide for this goal](guides/data-pipeline.md) has the starting brief, the advice the agents are given and the diagnoses in full.

## Settings

### settings-tuning

**Tune settings with a Bayesian estimator.** Tune the settings of fixed code (a model's learning rate, regularization, widths, schedule; or the parameters of any algorithm) with a Bayesian estimator in code. No structure changes and no agent calls.

*When to choose it.* The code is right and only its numbers are in question. It costs no model credits. Not for a search that should change structure; use it after such a search, on the winner.

| | |
|---|---|
| Tags | hyperparameters, tuning, bayesian, tpe, learning rate, no agents |
| Sets | `audit.reviews`, `harness.conductor`, `harness.coordinator`, `harness.level`, `schedule.local_mix`, `schedule.novel_share`, `schedule.phases`, `space.preset`, `strategist.mode`, `strategy.mechanism`, `variation.proposals_per_slot`, `variation.settings_by`, `variation.step_adaptation` |
| Guidance for | all, analyst, writer |
| Diagnoses | 4, in the guide |
| Needs from the evaluator | every setting to tune must sit in a marked params block (one dict of numbers, true/false or text); give bounds for settings that must stay in a range with `space.ranges`, e.g. {"fit.lr": [0.00001, 0.1]}; without one a setting may move a hundredfold either way; to stop poor settings early, report progress and set `evaluation.ladder` |
| Goes well with | any |
| Not with | `model-performance`, `model-distillation`, `model-efficiency`, `model-size-frontier`, `model-mechanistic`, `model-training-recipe`, `model-ensemble-members`, `model-finetuning`, `algorithm-runtime`, `bioinformatics-algorithm`, `data-pipeline` |

[The guide for this goal](guides/settings-tuning.md) has the starting brief, the advice the agents are given and the diagnoses in full.
