# Skill library

Every skill that comes with evoloop. This page is written from the skill files themselves (`evoloop skills --markdown`). Each is a template: a search copies the ones it names into its own `skills/` folder, and that copy is yours to edit. [Skills](skills.md) explains how they work and how to write one.

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
| Diagnoses | 5 |
| Needs from the adapter | nothing special |
| Goes well with | `model-training-recipe` |
| Not with | `settings-tuning` |

| If the results show | Then |
|---|---|
| training and validation scores are both poor and still improving at the end of the run | the run is too short or the optimisation is slow: fix the schedule or normalisation before judging the architecture |
| training score is good, validation score is clearly worse | regularize, augment, or reduce capacity; do not add capacity |
| both scores stop improving early and stay poor | the model lacks capacity or a mechanism: widen, deepen, or add the missing range or interaction |
| the same design gives very different scores on a re-check | the gain is within the noise: treat it as no gain, and prefer changes that reduce variance |
| many designs fail the quick check or crash | the changes are too large for the frozen code around them: make smaller edits and keep shapes compatible |

### model-distillation

**Distil a student from a teacher.** Train a smaller or faster student to match a teacher. The student's architecture and its training recipe (loss, optimizer, learning rate, regularization, augmentation) are both open.

*When to choose it.* You have a strong model or ensemble that is too large or slow to use, and want a student that keeps its accuracy. Not for shrinking a model with no teacher (model-efficiency).

| | |
|---|---|
| Tags | distillation, student, teacher, compression, ensemble, augmentation |
| Sets | `report.columns`, `space.preset`, `variation.approach_seeds`, `variation.approaches` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5 |
| Needs from the adapter | the training script must produce the teacher's outputs (or read stored ones) and train the student against them; the loss and augmentation blocks should be marked as open recipe blocks; to rank on speed or size, report `parameters` and `inference_speed.examples_per_s` in result.json; then `strategy.mechanism: pareto` or `limits` can use them; if the teacher is an ensemble, add a reference row for the ensemble and one for its best single member |
| Goes well with | `model-size-frontier`, `model-efficiency` |
| Not with | `settings-tuning` |

| If the results show | Then |
|---|---|
| the student does not fit the teacher's outputs even on training inputs | the student is too small or trains too briefly: train longer first, then widen or deepen |
| the student fits the teacher on training inputs but not on held-out ones | add teacher-labelled augmented or synthetic inputs, or regularize; do not enlarge the student |
| the student matches the same student trained from scratch on measured targets | the teacher is adding nothing: raise the weight of the teacher's targets, or check that the teacher's outputs are used at all |
| the student beats the teacher on validation data | check for leakage between the teacher's training data and the validation set before believing it |
| stronger augmentation lowers the score | check that the augmented inputs are labelled by the teacher and not paired with the measured targets |

### model-efficiency

**Make one model smaller or faster.** Make the model smaller or faster while holding its score. Designs are selected on the trade-off between the score and size (or speed), and removal is the commonest move.

*When to choose it.* You have a model that scores well enough and costs too much. The aim is one cheaper model at about the same score. For a whole family across sizes use model-size-frontier; with a teacher available, model-distillation.

| | |
|---|---|
| Tags | efficiency, compression, pruning, size, speed, pareto, ablation |
| Sets | `report.columns`, `schedule.local_mix`, `strategy.mechanism`, `strategy.second_direction`, `strategy.second_metric` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 4 |
| Needs from the adapter | report `parameters` in result.json (and `inference_speed.examples_per_s` to rank on speed: then set strategy.second_metric to examples_per_s and strategy.second_direction to maximize); set `limits` for the largest size or lowest speed you accept, and put those figures in the first progress line so that a design outside them costs seconds; add a reference row for the model you are trying to shrink |
| Goes well with | `model-distillation` |
| Not with | `settings-tuning`, `model-size-frontier` |

| If the results show | Then |
|---|---|
| an ablation costs less than the noise floor | the component is dead weight: keep it out, and try removing its neighbours |
| parameter count fell but speed did not | the time is not where the parameters are: cut resolution, sequence length or depth instead of width |
| every reduction costs score, however small | the model is already tight: change the kind of layer (separable, bottleneck, shared weights) instead of shrinking the same ones |
| a much smaller design scores the same as the reference | the reference was over-sized for the data: keep going down until the score moves |

### model-ensemble-members

**Find models that fail differently, for an ensemble.** Find models that are each good and that make different errors from one another, so that averaging them gains more than averaging copies of the best one.

*When to choose it.* You will average several models (as a final predictor, or as the teacher for model-distillation) and want members that add to each other. Not for a single best model.

| | |
|---|---|
| Tags | ensemble, diversity, behaviour, errors, averaging, teacher |
| Sets | `schedule.novelty`, `schedule.novelty_measure`, `schedule.phases`, `strategy.descriptors`, `strategy.mechanism` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 4 |
| Needs from the adapter | report `signature` in result.json: a list of numbers saying where the model's errors fall (per class, per range of the target, or per held-out example); the groups are made from it; after the search, score the average of the best design of each group yourself; evoloop does not train or score ensembles |
| Goes well with | `model-distillation` |
| Not with | `settings-tuning`, `model-efficiency` |

| If the results show | Then |
|---|---|
| new designs keep falling in the same behaviour group as the leader | the changes are too small to change behaviour: change the inductive bias or the view of the data |
| a design is in a group of its own but scores far below the others | improve it within its lineage before discarding it; a member too weak drags an average down |
| all designs fail on the same examples | those examples may be mislabelled or outside what the data can teach: no member will fix them |
| there are many groups with one design each | the similarity threshold is too strict for this task's noise: lower strategy.behaviour_similarity |

### model-finetuning

**Adapt a pretrained model to a task.** Start from a pretrained model and search over how to adapt it (what to freeze, what to add, the learning rates by layer, how long to train).

*When to choose it.* A pretrained model exists and the task has far less data than the model was trained on. Not for training from scratch.

| | |
|---|---|
| Tags | finetuning, pretrained, transfer, adapters, foundation model, freezing |
| Sets | `schedule.local_mix`, `schedule.novelty` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 4 |
| Needs from the adapter | load the pretrained weights from a fixed path outside base/ (weights are not copied per design); mark as open the head, the choice of what is frozen, and the optimizer settings; leave the backbone's definition closed; add a reference row for the frozen backbone with a linear head |
| Goes well with | `model-training-recipe` |
| Not with | none |

| If the results show | Then |
|---|---|
| the score falls below the frozen-backbone baseline when layers are unfrozen | the pretrained weights are being destroyed: lower the backbone's learning rate, add warm-up, or unfreeze fewer layers |
| the training score climbs and the validation score peaks in the first epochs | it is overfitting: train fewer parameters (adapters, last layers), regularize, or stop earlier |
| nothing beats the linear head on the frozen backbone | read from an earlier layer or change the pooling before unfreezing anything |
| results differ widely between seeds | the dataset is small for the number of trained parameters: train fewer, and average seeds before comparing |

### model-mechanistic

**Improve an interpretable or biophysical model.** Improve a model that is interpretable by design, where the parameters stand for something (motifs in filters, a graph of interactions, rates and affinities in a biophysical model). The structure that carries the meaning is kept.

*When to choose it.* The model is meant to be read, not only to predict: its parts stand for things. Not for making a black-box model explainable after the fact.

| | |
|---|---|
| Tags | interpretable, mechanistic, biophysical, motifs, interactions, constraints |
| Sets | `schedule.local_mix`, `schedule.novelty`, `space.must_keep`, `space.preset` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5 |
| Needs from the adapter | optional, and worth doing: report a figure of how well the parts match what is known (the share of filters matching known motifs, recovered interactions, parameters within physical ranges) under diagnostics; it can then be a leaderboard column, a speciality metric, or the second figure of the pareto strategy; report `signature` (where the errors fall) so that designs with the same failure are told apart from ones that fail differently; mark as open only the blocks that define the interpretable parts and their combination; leave the data handling and the evaluation frozen |
| Goes well with | any |
| Not with | `settings-tuning` |

| If the results show | Then |
|---|---|
| two parts have learned the same thing | remove one, or add a term that makes them compete or differ |
| a part has learned nothing (its parameters stay near their start, or removing it costs nothing) | remove it, or change its initialisation if the mechanism is known to matter |
| the score depends strongly on the seed | the fit has poor local optima: improve the initialisation or fit in stages before changing the model |
| errors of every design fall on the same examples | a mechanism is missing: add the term those examples call for, with a stated meaning |
| a design gains by loosening a constraint (sign, non-negativity, a fixed scale) | do not keep it: the parameters are no longer identifiable, so the gain is not a readable one |

### model-size-frontier

**A family of models across sizes.** Find the best model at each size (or speed), from very small to large, so that the result is a whole trade-off curve to choose from and not one winner.

*When to choose it.* You need models for several budgets (a phone, a server, a screen of millions of inputs), or want to know what accuracy each size buys before choosing. For one cheaper model at a fixed score use model-efficiency.

| | |
|---|---|
| Tags | pareto, frontier, trade-off, size, speed, family, scaling, coverage |
| Sets | `report.columns`, `schedule.novelty`, `schedule.phases`, `strategy.descriptors`, `strategy.mechanism` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 4 |
| Needs from the adapter | report `parameters` in result.json for every design; the bands are made from it; to band by speed instead, report `inference_speed.examples_per_s` and set strategy.descriptors to the name of that metric under diagnostics; set `limits` for the smallest and largest size worth having, so that designs outside the range are not trained |
| Goes well with | `model-distillation` |
| Not with | `settings-tuning`, `model-efficiency` |

| If the results show | Then |
|---|---|
| a band holds no design, or only one | aim new designs at it: scale the nearest good design up or down as a whole |
| a larger band's best design scores no better than the band below it | the larger designs are wasting capacity: move the smaller band's best design up by scaling it, and compare |
| the smallest band's designs all fail or score near chance | that size is below what this approach can do: change the kind of layer, or accept the band above as the floor |
| the curve is flat across the top bands | the data or the recipe is the limit, not size: stop adding large designs and spend the budget lower down |

### model-training-recipe

**Improve how a fixed model is trained.** The architecture is fixed; the training recipe is open (the loss, the optimizer, the learning-rate schedule, regularization, augmentation). Between tuning numbers and changing the model.

*When to choose it.* The architecture is settled (it is published, deployed, or the point of comparison) and the question is how well it can be trained. If only numbers change, settings-tuning is cheaper; if the model may change too, use model-performance with the recipe opened.

| | |
|---|---|
| Tags | recipe, training, loss, optimizer, schedule, regularization, augmentation |
| Sets | `schedule.local_mix`, `space.preset`, `space.roles` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5 |
| Needs from the adapter | mark the loss, optimizer, schedule and augmentation as blocks with those roles; the model blocks stay closed; report the training score beside the validation score under diagnostics, so that fitting and generalising can be told apart; report `best_epoch` and `epochs_run` in result.json |
| Goes well with | `model-performance`, `model-finetuning` |
| Not with | `settings-tuning` |

| If the results show | Then |
|---|---|
| training is unstable or diverges after a recipe change | lower the peak learning rate or lengthen warm-up for that design before rejecting the change |
| the training score rose and the validation score did not | the change helped fitting, not generalisation: pair it with regularization or augmentation |
| a new augmentation lowers both training and validation scores | the answer is not invariant to it: weaken or drop it |
| the best epoch is the last one | the run is too short for this recipe: the comparison favours fast recipes, so say so and ask for a longer run |
| the best epoch is very early and later epochs are worse | the rate is too high late, or regularization too weak: change the decay or add regularization |

## Algorithm

### algorithm-runtime

**Make an algorithm faster at the same output.** Speed up a piece of code (or cut its memory) while its output stays correct. The score is a measured time; a design whose output is wrong is rejected, not scored.

*When to choose it.* The code is correct and too slow or too hungry. The search needs a benchmark that checks the output and times the run. Not for improving what the algorithm computes (see bioinformatics-algorithm for accuracy against a truth set).

| | |
|---|---|
| Tags | speed, runtime, performance, optimisation, complexity, memory, benchmark |
| Sets | `evaluation.screen_keep`, `schedule.local_mix`, `schedule.novelty` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5 |
| Needs from the adapter | compare every design's output with a stored reference output and write `valid: false` with `rejected: "output differs"` when it does not match (exactly, or within a stated tolerance); time the run several times on a quiet machine with a fixed number of threads, and report the median as the score with objective.direction minimize; set evaluation.noise from the spread of repeats; keep a second set of inputs the search never sees, and report its timing under diagnostics.hidden; report peak memory under diagnostics if it matters, and bound it with `limits` |
| Goes well with | `data-pipeline`, `bioinformatics-algorithm` |
| Not with | `settings-tuning` |

| If the results show | Then |
|---|---|
| a design is rejected because its output differs from the reference | find which case differs and keep that case's behaviour; do not relax the check |
| a design is faster on small inputs and slower on large ones (or the reverse) | the complexity changed: decide which size matters from the task, and say which the benchmark weighs |
| timings of one design differ between repeats by as much as the gains | the measurement is the problem: gains below the noise floor are not gains |
| time fell and memory rose sharply | a cache or a table is paying for the speed: check it against the memory limit and say so |
| many small edits each gain a little, then nothing | the current algorithm is at its floor: change the algorithm or the data structure |

## Bioinformatics

### bioinformatics-algorithm

**Improve a bioinformatics algorithm.** Improve a method that analyses biological data (an aligner, a caller, a peak finder, a quantifier, a scoring function) against a truth set, without breaking the conventions of the formats and coordinates it works in.

*When to choose it.* The method has a measurable right answer on some data (simulated, curated, or orthogonally validated) and the aim is to do better on it. If the method is right and only slow, use algorithm-runtime.

| | |
|---|---|
| Tags | bioinformatics, genomics, sequence, alignment, variant calling, peak calling, benchmark, truth set |
| Sets | `schedule.local_mix`, `schedule.novelty` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5 |
| Needs from the adapter | score against a truth set with a standard comparison for the task, and report precision, recall and their combination under diagnostics; the score should be one number that does not reward trading one for the other at a single threshold; use more than one dataset (another sample, depth or organism), and keep one the search never sees under diagnostics.hidden; check the output's format and coordinates before scoring, and write `valid: false` with the reason when they are wrong; report run time and peak memory under diagnostics, and bound them with `limits` if they matter |
| Goes well with | `algorithm-runtime` |
| Not with | `settings-tuning` |

| If the results show | Then |
|---|---|
| precision rose and recall fell by about as much (or the reverse) | a threshold moved, not the method: look for a change that separates true from false cases better |
| the gain is on one dataset of the benchmark and not the others | it is fitted to that dataset: keep only changes that hold across them |
| results are off by one position, or wrong on one strand only | a coordinate or strand convention was broken: restore it before judging anything else |
| errors concentrate in repeats, low-complexity sequence or low coverage | treat those cases explicitly (a separate model, a mask, a penalty) and say how |
| the output changes between two runs on the same input | the method is not deterministic: fix seeds, ordering and tie-breaks first |

## Pipeline

### data-pipeline

**Make a data processing pipeline faster or cheaper.** Speed up a multi-step data pipeline (reading, transforming, joining, writing) or cut its memory and cost, with its output unchanged.

*When to choose it.* A pipeline of several steps produces the right output too slowly or at too high a cost. For a single hot function use algorithm-runtime.

| | |
|---|---|
| Tags | pipeline, data processing, throughput, io, memory, etl, preprocessing, parallel |
| Sets | `evaluation.screen_keep`, `schedule.local_mix`, `schedule.novelty` |
| Guidance for | all, analyst, strategist, writer |
| Diagnoses | 5 |
| Needs from the adapter | run the pipeline on fixed sample data and compare its output with a stored reference (a checksum of sorted records, or row counts with value checks); write `valid: false` with the reason when it differs; report the cost as the score with objective.direction minimize: wall time as a median of repeats, or a figure that combines time and memory if both matter; report time per step and peak memory under diagnostics, so that the agents can see where the cost is; use sample data large enough that input and output costs resemble the real run, and keep a second sample the search never sees under diagnostics.hidden |
| Goes well with | `algorithm-runtime` |
| Not with | `settings-tuning` |

| If the results show | Then |
|---|---|
| a design is rejected because its output differs | find the step that changed it (order, missing values, precision, duplicates) and keep that behaviour |
| run time is dominated by reading or writing | read less and fewer times, or change the format; faster computation will not show |
| adding parallel workers gives no gain, or a loss | the steps contend for disk or memory: reduce what is read first, then parallelise fewer, larger pieces |
| memory peaks at one step | process that step in chunks or streams, or reduce the data before it |
| a design is faster on the sample and its gain depends on the sample's size | say how the cost grows with input size; a gain that vanishes at full size is not one |

## Settings

### settings-tuning

**Tune settings with a Bayesian estimator.** Tune the settings of fixed code (a model's learning rate, regularization, widths, schedule; or the parameters of any algorithm) with a Bayesian estimator in code. No structure changes and no agent calls.

*When to choose it.* The code is right and only its numbers are in question. It costs no model credits. Not for a search that should change structure; use it after such a search, on the winner.

| | |
|---|---|
| Tags | hyperparameters, tuning, bayesian, tpe, learning rate, no agents |
| Sets | `audit.reviews`, `harness.level`, `schedule.local_mix`, `schedule.novel_share`, `schedule.phases`, `space.preset`, `strategist.mode`, `strategy.mechanism`, `variation.proposals_per_slot`, `variation.settings_by`, `variation.step_adaptation` |
| Guidance for | all, analyst, writer |
| Diagnoses | 4 |
| Needs from the adapter | every setting to tune must sit in a marked params block (one dict of numbers, true/false or text); give bounds for settings that must stay in a range with `space.ranges`, e.g. {"fit.lr": [0.00001, 0.1]}; without one a setting may move a hundredfold either way; to stop poor settings early, report progress and set `evaluation.ladder` |
| Goes well with | any |
| Not with | `model-performance`, `model-distillation`, `model-efficiency`, `model-size-frontier`, `model-mechanistic`, `model-training-recipe`, `model-ensemble-members`, `algorithm-runtime`, `bioinformatics-algorithm`, `data-pipeline` |

| If the results show | Then |
|---|---|
| the best designs have a setting at the edge of its range | widen that range in space.ranges; the optimum is probably outside it |
| the score barely changes across a setting's whole range | the setting does not matter here: fix it and spend the budget on the others |
| scores differ as much between repeats as between settings | the noise floor is too high to tune on: lengthen the run or average seeds before continuing |
| good values of one setting depend on another | the estimator models each setting alone: tune the pair in a second, narrower search around the best design |
