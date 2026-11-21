# What do you want to optimize?

Each goal below is a different search, with its own page: a starting configuration, why it fits, what your evaluator must report, when to choose another, and how to read the result.

## A model

| I want to | Guide | In one line |
|---|---|---|
| Improve a model's score | [`model-performance`](model-performance.md) | the best score, nothing else weighed |
| Distil a smaller student from a teacher | [`model-distillation`](model-distillation.md) | a smaller or faster model that matches a larger model or an ensemble |
| Find a smaller or faster model | [`model-efficiency`](model-efficiency.md) | the same score at a lower cost in parameters or time |
| Find models that fail differently, for an ensemble | [`model-ensemble-members`](model-ensemble-members.md) | a set of strong models whose errors do not coincide |
| Adapt a pretrained model to a task | [`model-finetuning`](model-finetuning.md) | the best score on a task starting from a pretrained model |
| Improve an interpretable or biophysical model | [`model-mechanistic`](model-mechanistic.md) | a better fit without losing what the parameters mean |
| Find the best model at several sizes | [`model-size-frontier`](model-size-frontier.md) | the best model at every size or speed across a broad range |
| Train a fixed architecture better | [`model-training-recipe`](model-training-recipe.md) | a better score from the same architecture, by training it better |

## An algorithm

| I want to | Guide | In one line |
|---|---|---|
| Make an algorithm faster | [`algorithm-runtime`](algorithm-runtime.md) | the same results in less time or memory |

## A bioinformatics method

| I want to | Guide | In one line |
|---|---|---|
| Improve a bioinformatics method | [`bioinformatics-algorithm`](bioinformatics-algorithm.md) | better accuracy against a truth set, at an acceptable run time |

## A data pipeline

| I want to | Guide | In one line |
|---|---|---|
| Make a data pipeline faster or cheaper | [`data-pipeline`](data-pipeline.md) | the same output from a pipeline in less time, memory or cost |

## Numbers only

| I want to | Guide | In one line |
|---|---|---|
| Tune hyperparameters | [`settings-tuning`](settings-tuning.md) | the best values for the settings of fixed code |

## Telling similar goals apart

| You have | You want | Use |
|---|---|---|
| a good model | its learning rate, weight decay or widths set better | [`settings-tuning`](settings-tuning.md) |
| a good model | to change how it trains: the loss, the optimizer, augmentation | [`model-training-recipe`](model-training-recipe.md) |
| a good model | one smaller or faster replacement | [`model-efficiency`](model-efficiency.md) |
| a good model | the best model at each of several sizes | [`model-size-frontier`](model-size-frontier.md) |
| a strong model or ensemble | a small model that keeps its accuracy | [`model-distillation`](model-distillation.md) |
| a task and a baseline | the best score you can get | [`model-performance`](model-performance.md) |
| correct code that is slow | the same output, sooner | [`algorithm-runtime`](algorithm-runtime.md) or [`data-pipeline`](data-pipeline.md) |

Goals can be combined ([Skills](../skills.md#combining-skills)), and none of these starting points has been measured against the others yet ([Status and limits](../status.md)).
