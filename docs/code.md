# Code map

evoloop is used through its [commands](commands.md); it has no separate programming interface to learn. This page is for reading or changing the code: every module, what it is for, and its public classes and functions, each linked to its line in the repository. It is written from the source by `tools/code_map.py`.

| Module | What it is for |
|---|---|
| [`cli.py`](#m-cli-py) | The commands. |
| [`controller.py`](#m-controller-py) | The loop. |
| [`schedule.py`](#m-schedule-py) | The schedule: what kind of slot comes next. |
| [`strategies/__init__.py`](#m-strategies---init---py) | Evolution strategies: how parents are chosen and what stays in the population. |
| [`strategies/archive.py`](#m-strategies-archive-py) | A quality-diversity archive: the best of each kind of design. |
| [`strategies/greedy.py`](#m-strategies-greedy-py) | Greedy best-first: always build on the current best. |
| [`strategies/islands.py`](#m-strategies-islands-py) | Islands: several populations of any strategy, evolving apart. |
| [`strategies/lineage.py`](#m-strategies-lineage-py) | Lineages kept alive side by side. |
| [`strategies/pareto.py`](#m-strategies-pareto-py) | A trade-off front: the designs that are best on the score and on a second figure at once. |
| [`strategies/tournament.py`](#m-strategies-tournament-py) | Tournament selection with aging (regularized evolution). |
| [`design.py`](#m-design-py) | From a request to a design that can be run. |
| [`agents.py`](#m-agents-py) | The agent roles, and the one way they are called. |
| [`space.py`](#m-space-py) | The search space: the marked blocks of the project's code, and which of them a run may change. |
| [`jobs.py`](#m-jobs-py) | Running a design: one job per training run, on this machine or through Slurm. |
| [`store.py`](#m-store-py) | The shared stores of a run, and the view computed from them. |
| [`form.py`](#m-form-py) | The brief: one form that sets up a search, and the settings derived from it. |
| [`skill.py`](#m-skill-py) | Skills: what kind of optimization a search is. |
| [`interview.py`](#m-interview-py) | Setting up a search by question and answer: one list of questions, three ways to answer it. |
| [`formpage.py`](#m-formpage-py) | The brief as a form in a browser: one self-contained HTML file, no server. |
| [`estimate.py`](#m-estimate-py) | What the agents will cost: an estimate before a run, and a projection during one. |
| [`strategist.py`](#m-strategist-py) | The strategist, and the spend governor. |
| [`approaches.py`](#m-approaches-py) | Approaches: ways of working handed to the writers, kept or dropped by how their designs did. |
| [`tpe.py`](#m-tpe-py) | A tree-structured Parzen estimator for settings moves: Bayesian optimization with no agent call. |
| [`audit.py`](#m-audit-py) | Auditing the agents, like reviewing a consulting group. |
| [`report.py`](#m-report-py) | What a person reads about a run: `status.json` while it goes, `report.md` when asked or at the end. |
| [`study.py`](#m-study-py) | The run as a study file, in the CAMEO entry format (version 0.4). |
| [`site.py`](#m-site-py) | The site file: what is particular to the machine a search runs on. |
| [`menu.py`](#m-menu-py) | The menu: every choice a run can make, the presets, and every field of the brief, each with a line of explanation. |
| [`model/anthropic_api.py`](#m-model-anthropic-api-py) | Backend: the Anthropic Python SDK. |
| [`model/base.py`](#m-model-base-py) | The model client: one interface over interchangeable backends (spec section 10). |
| [`model/catalog.py`](#m-model-catalog-py) | The Claude models this version knows: their ids, prices, and the effort levels each accepts. |
| [`model/claude_code.py`](#m-model-claude-code-py) | Backend: Claude Code run non-interactively as a subprocess, with no tools. |
| [`model/quota.py`](#m-model-quota-py) | Recognising a refusal by the account's spend or usage limit, and reading when the limit resets. |
| [`__init__.py`](#m-init---py) | evoloop. |
| [`__main__.py`](#m-main---py) |  |
| [`evojob.py`](#m-evojob-py) | Helpers for an evaluator (adapter/run.py). |
| [`stub.py`](#m-stub-py) | The built-in stub: stands in for every agent role so that a search can be dry-run with no model call. |

## `cli.py` { #m-cli-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py)

The commands.

| Name | What it does |
|---|---|
| [`out(text)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L87) |  |
| [`run_dir(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L91) |  |
| [`request(args, body)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L98) |  |
| [`parse_pairs(pairs)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L106) |  |
| [`cmd_init(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L126) |  |
| [`cmd_example(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L158) |  |
| [`skill_files(folder, brief)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L170) | The skill files a search in `folder` reads, for each skill its brief names. |
| [`skill_copies(folder, brief, tell)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L176) | Give the search its own copy of each skill its brief names, as soon as one is named, so that the copy can be edited before the plan is read and confirmed. |
| [`open_editor(path)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L194) | Open a file in the person's editor ($VISUAL, then $EDITOR). |
| [`cmd_brief(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L206) |  |
| [`cmd_setup(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L325) | The questions one at a time in the terminal. |
| [`cmd_form(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L339) | The questions as a self-contained HTML form. |
| [`cmd_plan(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L356) |  |
| [`cmd_estimate(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L368) | What the agents will cost: before a run from the brief; during one, from its own calls so far. |
| [`cmd_guide(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L399) |  |
| [`menu_topics()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L410) |  |
| [`cmd_menu(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L415) |  |
| [`cmd_skills(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L427) | The skill library: the list, a search of it, one skill in full, or one written out as a folder to edit. |
| [`cmd_site(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L523) | The site file: what is particular to this machine. |
| [`cmd_run(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L557) |  |
| [`offline(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L569) | A controller object for reading a run, with nothing started. |
| [`cmd_status(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L576) |  |
| [`cmd_show(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L614) | One run: where it came from, what its design changed against its parent, how it ended. |
| [`cmd_report(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L653) |  |
| [`cmd_study(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L664) |  |
| [`cmd_set(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L676) |  |
| [`cmd_note(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L692) |  |
| [`cmd_withdraw(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L698) |  |
| [`cmd_stop(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L704) |  |
| [`cmd_chat(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L710) | Talk with the agent that runs the search. |
| [`cmd_rerun(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L781) |  |
| [`cmd_reply(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L788) |  |
| [`cmd_rehash(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L794) |  |
| [`cmd_force(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L801) |  |
| [`cmd_import(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L808) |  |
| [`import_study(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L821) | Designs from a study file: a path, or a link to one (a study.json downloaded from CAMEO, or another search's). |
| [`cmd_reference(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L850) | A row on the leaderboard for a model that is not part of the search: a published baseline, an earlier run's best. |
| [`cmd_leaderboard(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L877) |  |
| [`cmd_controller(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L917) | A Slurm job script that runs the search and requeues itself at its time limit. |
| [`cmd_lineage(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L958) |  |
| [`cmd_answer(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L966) |  |
| [`cmd_review(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L972) |  |
| [`cmd_steer(args)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L978) | The person's words, turned into ledger entries by the translator, shown back, applied only with --yes. |
| [`build_parser()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L1032) |  |
| [`main(argv)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/cli.py#L1169) |  |

## `controller.py` { #m-controller-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py)

The loop.

| Name | What it does |
|---|---|
| [`class Controller`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L34) |  |
| &nbsp;&nbsp;[`.begin()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L77) | Start a new run: freeze the brief and the base, record the person's own words, queue the baseline. |
| &nbsp;&nbsp;[`.frozen_fault()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L120) | Why nothing new may start: the frozen code (everything outside the marked blocks, and the adapter) is not what this run started with. |
| &nbsp;&nbsp;[`.rehash()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L131) | The person's word that a change to the frozen code is meant: recorded with what changed, and the run goes on. |
| &nbsp;&nbsp;[`.queue()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L157) | A run the loop makes itself (the baseline, a re-check, a reference for a new period): recorded at once under the next free id, so that no design written meanwhile can take the same id, then started when a slot is free. |
| &nbsp;&nbsp;[`.read_inbox()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L165) | The person's requests, written by `evoloop set`, `note`, `stop`, `review`. |
| &nbsp;&nbsp;[`.note_skill()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L256) | A skill's file is the person's to edit, during a run too. |
| &nbsp;&nbsp;[`.rerun()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L322) | Train again a design whose run ended without a score, for instance after the evaluator was repaired. |
| &nbsp;&nbsp;[`.reply()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L347) | The person's answer to a question an agent asked. |
| &nbsp;&nbsp;[`.superseded()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L364) | Why a design that has not started is no longer the one the search would write, or None. |
| &nbsp;&nbsp;[`.rejudge()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L383) | A design waiting for its first start is replaced when newer results have overtaken it. |
| &nbsp;&nbsp;[`.tidy_seats()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L398) | Jobs without a design: one that has ended is forgotten, and all are cancelled when no design will come. |
| &nbsp;&nbsp;[`.stop_grace()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L407) | Seconds a run told to stop is given before its job is cancelled. |
| &nbsp;&nbsp;[`.screen()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L545) | A run is compared, part way, with the runs before it at the same point, and one clearly in the lower part is stopped there and charged for what it ran. |
| &nbsp;&nbsp;[`.spent()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L586) | Evaluations charged: every scored run; runs that failed or failed the quick check beyond the allowance of uncounted ones; and designs rejected for a limit beyond theirs. |
| &nbsp;&nbsp;[`.unscored_streak()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L598) | How many of the most recent designs in a row ended without a score because they broke. |
| &nbsp;&nbsp;[`.measures()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L612) | The figures of a result that a limit can name: its visible diagnostics, `parameters`, and `examples_per_s` from its inference speed. |
| &nbsp;&nbsp;[`.watch_limits()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L637) | A run whose progress lines already show it outside a limit is stopped there, not trained to the end. |
| &nbsp;&nbsp;[`.order()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L648) | The person's order for the next slots: a mode, optionally a kind of crossover or local move, and optionally an instruction the writers of those slots must follow. |
| &nbsp;&nbsp;[`.import_designs()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L661) | Designs from an earlier run, fitted here as designs of this run. |
| &nbsp;&nbsp;[`.import_study()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L700) | Designs from a study file (the CAMEO format this loop also writes). |
| &nbsp;&nbsp;[`.one_new_at_a_time()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L827) | Whether designs from new families are written one after another. |
| &nbsp;&nbsp;[`.write()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L840) | In a worker: the coordinator's choice when there is one, then the design. |
| &nbsp;&nbsp;[`.take_decisions()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L1034) | The decisions of one meeting, each refused, applied, or held for the person. |
| &nbsp;&nbsp;[`.anchor()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L1050) | The settings without what the strategist changed by itself: where the person last left them. |
| &nbsp;&nbsp;[`.answer()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L1102) | The person's yes or no to a decision that was held for them. |
| &nbsp;&nbsp;[`.set_lineage()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L1133) | The person retires a lineage or brings one back: the same entry the strategist writes, in their name. |
| &nbsp;&nbsp;[`.review()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py#L1141) | A review of the agents. |

## `schedule.py` { #m-schedule-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/schedule.py)

The schedule: what kind of slot comes next.

| Name | What it does |
|---|---|
| [`fraction_used(view, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/schedule.py#L23) |  |
| [`phase_at(settings, fraction)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/schedule.py#L28) |  |
| [`credit(view, founder_share)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/schedule.py#L36) | What each mode has returned: runs, and the gain in the best score it is credited with, in noise floors. |
| [`shares(view, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/schedule.py#L64) |  |
| [`available(view, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/schedule.py#L85) |  |
| [`next_mode(view, settings, planned)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/schedule.py#L95) | The mode furthest behind its share, counted over this phase's runs and those being designed. |

## `strategies/__init__.py` { #m-strategies---init---py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/__init__.py)

Evolution strategies: how parents are chosen and what stays in the population.

| Name | What it does |
|---|---|
| [`rank_draw(items, rng, weights)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/__init__.py#L25) | A draw that favours the front of a ranked list without always taking it. |
| [`tied(view, candidates, margin, rng)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/__init__.py#L33) | One of the candidates within `margin` noise floors of the best of them: on one fit the order among near-equal candidates is mostly chance. |
| [`signature(view, candidate)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/__init__.py#L41) |  |
| [`measure(view, candidate, name)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/__init__.py#L46) | A figure of a design beside its score: `parameters`, `examples_per_s`, `training_minutes`, or a metric the runs report. |
| [`behaviour_groups(view, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/__init__.py#L61) | Designs grouped by what the trained model does: two fall in one group when the places their errors fall (`signature` in result.json) correlate at `strategy.behaviour_similarity` or above. |
| [`complement(view, first, pool, rng)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/__init__.py#L88) | The partner for a crossover: the candidate whose errors fall least like the first one's. |
| [`specialist(view, pool, settings, rng)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/__init__.py#L104) | Now and then, the candidate that is best at one thing rather than best overall. |
| [`inspirations(view, exclude, count, rng, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/__init__.py#L117) | Designs that have rarely been built on, from anywhere in the ranking: what a novel slot is shown. |
| [`step_size(view, lineage, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/__init__.py#L142) | The one-in-five rule: when a lineage's recent local moves gain often, ask for bolder ones; when they rarely do, for smaller ones. |
| [`make(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/__init__.py#L163) |  |

## `strategies/archive.py` { #m-strategies-archive-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/archive.py)

A quality-diversity archive: the best of each kind of design.

| Name | What it does |
|---|---|
| [`size_bin(view, candidate)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/archive.py#L18) |  |
| [`cell_of(view, candidate, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/archive.py#L27) |  |
| [`cells(view, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/archive.py#L48) |  |
| [`class Archive`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/archive.py#L58) |  |

## `strategies/greedy.py` { #m-strategies-greedy-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/greedy.py)

Greedy best-first: always build on the current best.

| Name | What it does |
|---|---|
| [`class Greedy`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/greedy.py#L12) |  |

## `strategies/islands.py` { #m-strategies-islands-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/islands.py)

Islands: several populations of any strategy, evolving apart.

| Name | What it does |
|---|---|
| [`class Islands`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/islands.py#L24) |  |
| &nbsp;&nbsp;[`.began()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/islands.py#L33) | For each island, when its present population began (NEVER: it was not reset). |

## `strategies/lineage.py` { #m-strategies-lineage-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/lineage.py)

Lineages kept alive side by side.

| Name | What it does |
|---|---|
| [`state(view, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/lineage.py#L25) |  |
| [`class Lineage`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/lineage.py#L84) |  |

## `strategies/pareto.py` { #m-strategies-pareto-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/pareto.py)

A trade-off front: the designs that are best on the score and on a second figure at once.

| Name | What it does |
|---|---|
| [`points(view, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/pareto.py#L21) | (candidate, score, second figure), both turned so that higher is better. |
| [`fronts(view, settings, margin)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/pareto.py#L32) | The designs in layers: the front, then the front of what is left, and so on. |
| [`spacing(front)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/pareto.py#L49) | How alone each design stands on the front, 0 to 1: the gap to its neighbours on both figures, each scaled to the front's range. |
| [`class Pareto`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/pareto.py#L68) |  |

## `strategies/tournament.py` { #m-strategies-tournament-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/tournament.py)

Tournament selection with aging (regularized evolution).

| Name | What it does |
|---|---|
| [`class Tournament`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/tournament.py#L15) |  |

## `design.py` { #m-design-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py)

From a request to a design that can be run.

| Name | What it does |
|---|---|
| [`spelled(label)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L39) | A family label as it is kept: lower case, words joined by hyphens. |
| [`family_key(label)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L44) | What makes two labels the same family whatever their spelling: -ise read as -ize, plurals as singulars, words in any order. |
| [`same_family(label, known, merged)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L51) | The label a design's family is recorded under: an existing label when the writer's is that label in another spelling, the label the analyst or the person merged it into, else the writer's own. |
| [`class Designer`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L61) |  |
| &nbsp;&nbsp;[`.distance()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L101) | How far a design's model is from the nearest model already tried: 0 the same code, 1 nothing shared. |
| &nbsp;&nbsp;[`.gene()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L187) | The change that gained most in the donor's lineage: a recorded, measured difference. |
| &nbsp;&nbsp;[`.propose()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L302) | Runs in a worker. |
| &nbsp;&nbsp;[`.estimated()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L358) | A settings move drawn by the estimator (`variation.settings_by: tpe`): every open setting at once. |
| &nbsp;&nbsp;[`.changed()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L382) | The blocks a proposal changes: those it gives in full, and those it edits by find-and-replace. |
| &nbsp;&nbsp;[`.commit()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L401) | The run record of the chosen proposal, or (None, why nothing can be run). |
| &nbsp;&nbsp;[`.baseline()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L488) | The base code as it stands, as the first design. |
| &nbsp;&nbsp;[`.again()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py#L501) | A further run of an existing design: another seed for a re-check, or the same design under a new setting of the run length (a reference for the new period). |

## `agents.py` { #m-agents-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/agents.py)

The agent roles, and the one way they are called.

| Name | What it does |
|---|---|
| [`class AgentError`](https://github.com/cameo-db/evoloop/blob/main/evoloop/agents.py#L210) |  |
| [`class AgentsUnavailable`](https://github.com/cameo-db/evoloop/blob/main/evoloop/agents.py#L214) | No call can be made now: the spend cap is reached, or the account's limit refused a call. |
| [`class Agents`](https://github.com/cameo-db/evoloop/blob/main/evoloop/agents.py#L245) |  |
| &nbsp;&nbsp;[`.available()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/agents.py#L282) | Why no call can be made now, or None. |
| &nbsp;&nbsp;[`.draw_writer()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/agents.py#L297) | The model for one writer call when several write (`agents.writer_mix`): by counting, so the realised shares follow the shares set, whatever the order the calls come in. |
| [`spend(store)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/agents.py#L390) | Agent cost by role: calls, dollars, seconds, failures. |

## `space.py` { #m-space-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py)

The search space: the marked blocks of the project's code, and which of them a run may change.

| Name | What it does |
|---|---|
| [`class SpaceError`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L36) |  |
| [`parse(text, filename)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L40) | A file as segments: frozen text, and blocks with their attributes. |
| [`render(segments, blocks)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L78) |  |
| [`files(base)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L89) |  |
| [`read(path)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L99) |  |
| [`table(base)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L104) | Every block of the base: name -> {file, kind, role, content}. |
| [`frozen_hash(base, extra)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L126) | A hash of everything a run may not change: the base with its blocks blanked, and the adapter. |
| [`part_of(block, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L146) | `settings`, `recipe` or `model`: which part of a design a block belongs to. |
| [`open_blocks(blocks, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L153) | The blocks this run may change: name -> kind. |
| [`parse_params(content)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L179) |  |
| [`render_params(name, values)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L197) |  |
| [`all_params(table_, blocks)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L201) | The resolved settings of a design: block.key -> value over every params block. |
| [`full(table_, blocks)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L214) | Every block's content: the given ones, and the base's for the rest. |
| [`check(table_, changed, allowed, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L219) | Why a proposal's blocks cannot be run, or None. |
| [`materialize(base, adapter, blocks, workdir)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L251) | A working copy for one run: the base with the blocks spliced in, and the adapter beside it. |
| [`spliced_text(base, table_, blocks, part, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L277) | The files that hold a design's model (or recipe), as run: what a study file records as its code. |
| [`key_of(blocks, names)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L289) |  |
| [`shingles(text, width)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L301) |  |
| [`similarity(a, b)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L308) | How much two pieces of code share: the overlap of their runs of three tokens (1 the same, 0 nothing shared). |
| [`diff(old, new, limit)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py#L318) |  |

## `jobs.py` { #m-jobs-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py)

Running a design: one job per training run, on this machine or through Slurm.

| Name | What it does |
|---|---|
| [`environment(run, out_dir, checkpoint_dir, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L42) |  |
| [`gpu_type_for(run, compute)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L56) | The GPU type this run asks for: the larger type once it was moved there, else the search's own (empty: any). |
| [`larger_available(run, compute)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L61) | Whether a design too large for its GPU can still be moved to a larger one. |
| [`seconds(limit)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L67) | A Slurm time limit in seconds: minutes, minutes:seconds, hours:minutes:seconds, days-hours, days-hours:minutes or days-hours:minutes:seconds. |
| [`ended_by_machine(code)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L88) |  |
| [`local_gpus()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L96) | The GPUs local jobs may use: those this process was given (CUDA_VISIBLE_DEVICES, as inside a Slurm job that holds several), else every GPU nvidia-smi lists. |
| [`command(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L110) | The quick check, when there is one, then the run command. |
| [`clean_env(extra)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L117) | Designs are model-written code: credentials do not go into their environment. |
| [`class Local`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L124) | Jobs as processes on this machine. |
| &nbsp;&nbsp;[`.take_gpus()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L135) | The GPUs a job is given: the least used ones, so that jobs share a GPU only when there are more jobs at once than GPUs. |
| &nbsp;&nbsp;[`.end()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L145) | Stop the job and everything it started: the job is the leader of its own process group. |
| &nbsp;&nbsp;[`.withdraw()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L184) | A local job starts at once: there is never a waiting design to take back. |
| [`class Slurm`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L202) | Each run its own Slurm job, followed by its job id. |
| &nbsp;&nbsp;[`.pick_qos()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L218) | The first QoS with room: `qos` may be one name or a list in order of preference, [{name: a, max_jobs: 8}, {name: b}]; the last takes the rest. |
| &nbsp;&nbsp;[`.assign()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L234) | Give a job the design it will train: what it does once it starts, written where the job looks for it. |
| &nbsp;&nbsp;[`.withdraw()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L256) | Take back the design of a job that has not started, so that another can be given to it. |
| &nbsp;&nbsp;[`.shutdown()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L348) | Nothing: the jobs go on, and the controller reattaches to them when it starts again. |
| [`in_block(compute)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L352) | Whether the designs run inside one Slurm job that holds every GPU, as processes of that job. |
| [`make(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L357) |  |
| [`reached(out_dir)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L364) | The furthest step a run has reported, over every start of it. |
| [`read_progress(out_dir, every)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L370) | The progress lines of a run. |
| [`tell(out_dir, action, allowance)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L387) |  |
| [`tail(out_dir, lines)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py#L395) |  |

## `store.py` { #m-store-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py)

The shared stores of a run, and the view computed from them.

| Name | What it does |
|---|---|
| [`class Store`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L32) |  |
| &nbsp;&nbsp;[`.merged()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L66) | Records by id, a later record laid over an earlier one with the same id. |
| &nbsp;&nbsp;[`.merged_list()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L79) | The merged records in the order they were first written. |
| [`merge(into, update)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L84) |  |
| [`read_json(path, default)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L93) |  |
| [`write_json(path, value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L101) |  |
| [`class View`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L108) | The results as every strategy sees them. |
| &nbsp;&nbsp;[`.value()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L154) | The score of the candidate a run belongs to, higher better, or None. |
| &nbsp;&nbsp;[`.scored()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L168) | Candidates with a score in this period, best first. |
| &nbsp;&nbsp;[`.charged()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L183) | Evaluations spent: every run that ended with a score, and failures past the uncounted allowance are added by the controller. |
| &nbsp;&nbsp;[`.run_of()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L220) | The first run of a candidate: where its blocks and history are kept. |
| [`order(run)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L230) |  |
| [`pearson(a, b)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py#L236) |  |

## `form.py` { #m-form-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py)

The brief: one form that sets up a search, and the settings derived from it.

| Name | What it does |
|---|---|
| [`class BriefError`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L210) |  |
| [`flatten(tree, prefix)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L214) |  |
| [`get(tree, path, default)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L230) |  |
| [`put(tree, path, value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L239) |  |
| [`known(path)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L249) |  |
| [`guidance_for(evaluations)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L253) |  |
| [`load_brief(folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L262) |  |
| [`save_brief(folder, brief)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L274) |  |
| [`given(brief)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L286) | The values the person gave, by path: everything in the brief that is not empty. |
| [`unknown_fields(brief)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L297) |  |
| [`resolve(brief, ledger, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L301) | The settings in force, and for each the layer it came from. |
| [`questions(brief, everything)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L382) | What there is still to ask the person. |
| [`check_value(path, value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L406) |  |
| [`check_phases(value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L522) |  |
| [`problems(brief)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L540) |  |
| [`warnings(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L549) | Combinations that work against each other. |
| [`digest(brief)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L625) |  |
| [`confirm(folder, name)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L630) |  |
| [`skills_changed(brief, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L648) | The skills whose files are not as they were when the brief was confirmed (edited, or no longer usable). |
| [`confirmed(brief)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L657) |  |
| [`tracked_columns(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L662) | The leaderboard's further columns: those asked for (`report.columns`), or else every metric the brief tracks, validation first and then the test evaluations. |
| [`at_a_glance(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L676) | What this search will actually do, in a few lines: what is optimized, who writes the designs, which agent roles run, how designs are selected and stopped, and what a later choice changed in an earlier one. |
| [`plan_lines(brief, star, folder, cost)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L764) | The plan: what the search will do at a glance, the warnings, what the agents will cost, and then every setting with the layer its value came from. |
| [`is_live(key)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L809) |  |
| [`starts_period(key)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L813) |  |
| [`check_change(key, value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L817) | Why a setting cannot be changed during a run, or None when it can. |
| [`review_points(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L828) |  |
| [`rungs(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L848) | The points of a run at which designs are compared and the weaker stopped, and whether every design is subject to them (a ladder) or only the first run of a new design (the single screen). |
| [`mean_charge(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py#L859) | The share of a full run that a design costs on average under the ladder, when the pool is full: with [{at: 0.1, keep: 0.5}, {at: 0.3, keep: 0.5}] half the designs cost 0.1, a quarter 0.3 and a quarter 1. |

## `skill.py` { #m-skill-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py)

Skills: what kind of optimization a search is.

| Name | What it does |
|---|---|
| [`names()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L64) | The skills of the library in this package, by domain and then by name. |
| [`wanted(value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L73) | The skill names in `run.skill`: one name, a list, or names separated by commas or plus signs. |
| [`find(name, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L88) | The folder of a skill. |
| [`check(raw)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L108) | Why a skill file cannot be used, or None. |
| [`load(name, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L155) | One skill: (the skill, None) or (None, why it cannot be used). |
| [`combine(value, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L200) | The skill a search runs with: the one named in `run.skill`, or several merged in the order given. |
| [`guidance(skill, role, used)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L252) | What a role is shown of the skill: its name, the guidance for every role and for this one, the diagnoses (writer and analyst), and for a writer the advice for this stage of the budget. |
| [`checkout(value, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L271) | Copy the library skills a search names into its own `skills/` folder, where the run reads them and the person edits them. |
| [`index(folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L288) | Every skill of the library (and of a search's own folder), as records a listing or a website can use. |
| [`search(words, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L310) | The skills whose name, title, domain, objective, summary or tags hold every word, best match first. |
| [`summaries()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L322) |  |
| [`missing(skill, view, references)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L326) | What the skill needs and the run does not have yet: figures no result carries, rows the leaderboard lacks. |
| [`library_markdown()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L345) | The library as a page of the documentation (`evoloop skills --markdown`). |
| [`guide_markdown(name)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L422) | One skill as a page: how to use it, exactly what it sets, what it tells each agent, what the scoring script must report, and the file itself. |
| [`write_guides(folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L500) |  |
| [`file_links(name)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L514) | Where a library skill's file is: in the repository, and as a plain file to download. |
| [`table_markdown()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L520) | Every library skill with what it sets, read from the files: the table on the documentation's front page. |
| [`file_of(name, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L552) |  |
| [`state(value, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L565) | For each skill named: the file a search in `folder` reads, and whether it is the library's, the search's own unchanged copy of it, an edited copy, or a skill that is not in the library at all. |
| [`differs(name, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L591) | The lines by which the search's copy of a skill differs from the library's: None when the library has no skill of that name, an empty list when the two are the same. |
| [`sets(value, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L603) | `setting = value` for everything the named skills set, as one search would have them. |
| [`merged_yaml(value, name, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L610) | Several skills written out as one skill file: (the text, None) or (None, why not). |
| [`merge(value, name, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L641) | Write the named skills as one skill, `skills/NAME/skill.yaml` in the search folder: (the file, None) or (None, why not). |
| [`write_edited(name, text, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L661) | Save an edited skill file (from the set-up form) as the search's copy. |
| [`texts(folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L680) | The file of every skill a search in `folder` could name (its own copies first), for the set-up form. |
| [`told(skill)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L690) | What a skill adds to the agent calls, role by role, as lines of a plan. |
| [`new(name, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py#L747) | Write an empty skill of the person's own, `skills/NAME/skill.yaml` in the search folder: (the file, None) or (None, why not). |

## `interview.py` { #m-interview-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py)

Setting up a search by question and answer: one list of questions, three ways to answer it.

| Name | What it does |
|---|---|
| [`applies(question, values)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L190) |  |
| [`state(brief, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L200) | Every question that applies now, with its answer or default, and where the person is in the list. |
| [`parse(question, text)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L228) | An answer as typed, turned into a value. |
| [`metrics_from_text(text)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L253) | `name: how it is computed; name: ...` (or one to a line) as a mapping. |
| [`limits_from_text(text)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L265) | `parameters <= 2000000; training_minutes <= 30` as {metric: {max: x}}; `none` as no limits. |
| [`record(brief, field, value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L285) | Put an answer in the brief (or, with KEEP, note that its default was seen and left). |
| [`merge(brief, answers)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L313) | Answers from a file (the HTML form's, or any nested mapping of fields) into the brief: (set, refused). |
| [`shown(value, empty)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L327) | A value as the person would type it: metrics as `name: how`, limits as `metric <= x`, nothing as words. |
| [`card(q)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L338) | One question as text, the same way every time: where you are, the question, why, the choices. |
| [`skill_step(folder, brief, ask, say, edit)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L360) | After the skill is chosen: give the search its own copies, show what they set, and let the person edit them, or merge several into one file, before going on. |
| [`run(folder, ask, say, edit)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L406) | The terminal walk-through. |
| [`payload(brief, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L453) | What the HTML form needs: every question (the form itself decides which apply as answers change), the current answers, the defaults, and the schedule each kind of search runs. |
| [`as_json(value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L475) |  |
| [`suggest(brief, field, value, why, by)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L479) | Propose an answer for the person to accept or change. |
| [`infer(folder, brief)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/interview.py#L491) | Best guesses from the machine, the search folder and the answers so far, as suggestions. |

## `formpage.py` { #m-formpage-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/formpage.py)

The brief as a form in a browser: one self-contained HTML file, no server.

| Name | What it does |
|---|---|
| [`fragment(brief, download, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/formpage.py#L295) | The page without its outer document tags (a host that wraps pages supplies those). |
| [`document(brief, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/formpage.py#L301) | The form as a complete file to open in a browser. |

## `estimate.py` { #m-estimate-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py)

What the agents will cost: an estimate before a run, and a projection during one.

| Name | What it does |
|---|---|
| [`sizes(folder, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L34) | Characters of what a writer is shown and returns, measured from the search folder when there is one. |
| [`mix(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L54) | The share of the budget each kind of design gets, over the whole schedule. |
| [`calls(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L69) | Agent calls by role over the whole budget: (low, expected, high). |
| [`tokens(settings, size)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L102) | Tokens of one call by role: (in, out), expected. |
| [`price_of(settings, role)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L128) | A role's prices: the brief's `agents.prices`, else the built-in list of models. |
| [`chosen(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L143) | The model and the effort each role runs at. |
| [`estimate(settings, folder, measured)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L151) | Calls, tokens and dollars by role, each as (low, expected, high). |
| [`measured(store)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L192) | What each role's calls have cost and weighed so far in a run. |
| [`by_level(brief, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L211) | The estimate under each autonomy level, everything else in the brief as it is. |
| [`other_models(brief, folder, now)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L221) | The same search with each of the current models for every role: what the choice of model does to the cost. |
| [`span(values, unit, digits)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L239) |  |
| [`lines(brief, folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/estimate.py#L247) | The estimate as the plan prints it. |

## `strategist.py` { #m-strategist-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py)

The strategist, and the spend governor.

| Name | What it does |
|---|---|
| [`designs(view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L56) | Scored designs of the search in the current period, in the order they ended. |
| [`designs_ever(view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L61) | Scored designs of the search over every period. |
| [`since_gain(view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L68) | Designs scored since the best score last rose by more than the noise. |
| [`spending(store, agents, view, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L82) | What the agents have cost, and where the run is heading. |
| [`reserve_reached(agents, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L112) | The last part of the agent budget is kept for writing designs: analysis, strategy, reviews and the coordinator stop when it is reached. |
| [`facts(store, agents, view, settings, why)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L121) |  |
| [`menu(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L160) |  |
| [`meet(store, agents, view, settings, why)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L168) | One meeting: the decisions as the agent gave them. |
| [`person_set(ledger, key)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L182) | Whether the person had the last word on a setting during the run: they changed it, a part of it (`schedule.local_mix.edit` for `schedule.local_mix`), or something it followed from (a change of the run type or of the budget that moved it). |
| [`number(value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L196) |  |
| [`work_out(decision, view, settings, ledger, anchor, approving)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L200) | A decision turned into what it would do: (why it is refused, its effects, why it must wait). |
| [`score(view, entry, horizon)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L317) | What followed a decision, once `horizon` designs have been scored since it: the rise in the best score in noise floors, beside what the strategist expected. |
| [`govern(agents, view, settings, store)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategist.py#L337) | The next step that makes the run cheaper, when it is on course to pass the spend cap, or None. |

## `approaches.py` { #m-approaches-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/approaches.py)

Approaches: ways of working handed to the writers, kept or dropped by how their designs did.

| Name | What it does |
|---|---|
| [`on(settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/approaches.py#L27) |  |
| [`sync(store, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/approaches.py#L31) | The person's approaches, entered once each. |
| [`active(store)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/approaches.py#L43) |  |
| [`reward(view, run)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/approaches.py#L47) | 1 when the design beat its reference by more than the noise, 0 when it did not or broke, None while it trains. |
| [`record(store, view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/approaches.py#L65) | By approach (and `none`): designs written under it, those finished, and the share that beat their reference. |
| [`pick(store, view, settings, rng)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/approaches.py#L86) | The approach for one slot, or None for no approach. |
| [`add(store, view, settings, texts, call)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/approaches.py#L103) | Approaches the analyst proposes. |
| [`table(store, view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/approaches.py#L133) |  |

## `tpe.py` { #m-tpe-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/tpe.py)

A tree-structured Parzen estimator for settings moves: Bayesian optimization with no agent call.

| Name | What it does |
|---|---|
| [`numeric(value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/tpe.py#L30) |  |
| [`scale(values)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/tpe.py#L34) |  |
| [`to(value, how)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/tpe.py#L38) |  |
| [`back(value, how)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/tpe.py#L42) |  |
| [`ranged(key, how, ranges)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/tpe.py#L46) |  |
| [`bounds(key, start, seen, how, ranges)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/tpe.py#L54) |  |
| [`density(points, prior, low, high)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/tpe.py#L63) | A mixture of bells, as (centre, spread) pairs: a wide one on the prior, and one on each point as wide as the gap to its farther neighbour, so that the density is broad where few designs have been and narrow where many have. |
| [`weight(x, mixture)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/tpe.py#L80) |  |
| [`draw(mixture, low, high, rng)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/tpe.py#L87) |  |
| [`suggest(start, history, rng, ranges)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/tpe.py#L96) | New values for the settings in `start` (key -> present value), given what was tried: a list of (settings, score) with higher scores better. |

## `audit.py` { #m-audit-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/audit.py)

Auditing the agents, like reviewing a consulting group.

| Name | What it does |
|---|---|
| [`spearman(pairs)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/audit.py#L24) |  |
| [`forecasts(view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/audit.py#L41) | Each writer forecast beside what came about, in noise floors against the same reference. |
| [`scorecard(store, view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/audit.py#L63) |  |
| [`family_counts(view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/audit.py#L108) |  |
| [`merge_families(store, view, labels, keep, by, call)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/audit.py#L116) | Count several family labels as one. |
| [`analyse(store, agents, designer, view, settings, since)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/audit.py#L138) | The analyst's turn: lessons from the results since its last call, and questions for the person. |
| [`review(store, agents, view, settings, why, only)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/audit.py#L183) | The assessor's review of each role, written for the person. |

## `report.py` { #m-report-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/report.py)

What a person reads about a run: `status.json` while it goes, `report.md` when asked or at the end.

| Name | What it does |
|---|---|
| [`untracked(settings, view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/report.py#L13) | Metrics the brief says to track, and test evaluations it says to run, that no result has reported. |
| [`leaderboard(view, limit, columns, references, allowance)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/report.py#L32) | The best designs by validation score, with the baseline always shown, and the reference rows the person added (other models to compare with: never part of the search, and marked as such). |
| [`snapshot(controller, view, reason)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/report.py#L84) |  |
| [`status(controller, view, reason)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/report.py#L114) |  |
| [`headings(columns)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/report.py#L118) | How a tracked metric is headed in a table: a validation metric by its name, a test evaluation by its name when the name already says test and as `test.<name>` when it does not. |
| [`table(rows, names)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/report.py#L132) |  |
| [`lines(controller, view, reason)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/report.py#L147) |  |
| [`write(controller, view, reason)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/report.py#L275) |  |
| [`writers_by_model(store, view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/report.py#L282) | With several models writing (`agents.writer_mix`): what the designs of each came to. |

## `study.py` { #m-study-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py)

The run as a study file, in the CAMEO entry format (version 0.4).

| Name | What it does |
|---|---|
| [`or_not(value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L25) |  |
| [`tracked(s)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L29) | Every metric the brief tracks, with how it is computed: the validation metrics, and the test evaluations marked as test. |
| [`other_data(s)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L38) | Test evaluations measured on data other than the search's own: {metric: the name of that data}. |
| [`build(controller, view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L44) |  |
| [`adapter_files(folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L143) |  |
| [`star(study)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L156) | The star this file is on course for, by the format's own rules, and what stands in the way of the next. |
| [`write(controller, view)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L180) |  |
| [`load(path)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L188) | A study file (CAMEO format), from a path. |
| [`ranked(study)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L197) | The models of a study that have a finished run, best first by the study's own metric and direction. |
| [`about(study)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L224) | Where a study's designs come from: its id, data, metric and what it concluded. |
| [`blocks_in(texts, table)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L234) | The marked blocks of this project found by name in a study's code. |
| [`score_there(score, metric, data)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/study.py#L251) | An imported design's earlier score, with what it measured. |

## `site.py` { #m-site-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/site.py)

The site file: what is particular to the machine a search runs on.

| Name | What it does |
|---|---|
| [`find(folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/site.py#L40) |  |
| [`check(raw)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/site.py#L54) |  |
| [`load(folder)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/site.py#L79) | (the site, None), (None, why its file cannot be used), or (None, None) when there is no site file. |
| [`names_of(value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/site.py#L104) | The QoS or partition names in a setting: one name, or a list of names or of {name: ...}. |
| [`forbidden(site, key, value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/site.py#L113) | Why this machine does not allow a compute setting to take this value, or None. |
| [`fault(site, settings)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/site.py#L125) |  |
| [`detect(run, which)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/site.py#L141) | What this machine reports about itself: the scheduler, its partitions, QoS names and GPU types. |
| [`draft(found)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/site.py#L180) | A site file drafted from what was detected, with what could not be known left for the person. |

## `menu.py` { #m-menu-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py)

The menu: every choice a run can make, the presets, and every field of the brief, each with a line of explanation.

| Name | What it does |
|---|---|
| [`show(value)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py#L334) |  |
| [`when(path)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py#L338) | Whether a setting can change during a run. |
| [`preset_lines(overlay, indent)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py#L345) |  |
| [`text(topic)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py#L349) |  |
| [`cell(words)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py#L376) |  |
| [`menu_markdown()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py#L380) |  |
| [`anchor(path)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py#L413) | The id of a field on the fields page: `schedule.novelty` is `fields.md#schedule-novelty`. |
| [`fields_markdown()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py#L418) |  |
| [`missing()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py#L446) | Options and fields with no explanation here: must be empty. |
| [`plans()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py#L472) | What a search comes to for every combination of run type, skill, level of autonomy and size of budget: the data behind the documentation's plan explorer. |
| [`plans_json()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/menu.py#L533) |  |

## `model/anthropic_api.py` { #m-model-anthropic-api-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/anthropic_api.py)

Backend: the Anthropic Python SDK.

| Name | What it does |
|---|---|
| [`class AnthropicBackend`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/anthropic_api.py#L10) |  |
| [`request(model, effort, fallbacks, max_tokens, system, user)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/anthropic_api.py#L60) | The arguments of one Messages request, and whether it goes to the beta endpoint. |
| [`price(rates, usage)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/anthropic_api.py#L79) | Cost in dollars from `model.prices` (dollars per million tokens), or None when no price is set. |
| [`parse_message(response)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/anthropic_api.py#L86) | Text and token counts of a Messages API response. |

## `model/base.py` { #m-model-base-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py)

The model client: one interface over interchangeable backends (spec section 10).

| Name | What it does |
|---|---|
| [`class ModelError`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L19) | The call failed in a way that retrying the same request will not fix. |
| [`class TransientError`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L23) | Rate limit, overload or network trouble; retried with backoff. |
| [`class BudgetExceeded`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L27) | `budget.model_calls` has been reached. |
| [`class QuotaExhausted`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L31) | The account's spend or usage limit refused the call. |
| [`class AgentsPaused`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L40) | Raised to a caller that cannot go on without an agent's answer while calls are paused. |
| [`validate(value, schema, path)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L48) | Check `value` against the subset of JSON Schema that the agent schemas use. |
| [`extract_json(text)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L91) | Find the single JSON object in a model reply, tolerating code fences and surrounding prose. |
| [`class ModelClient`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L110) |  |
| &nbsp;&nbsp;[`.paused()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L126) | Seconds left of a pause set by a spend/usage-limit refusal; 0 when calls may be made. |
| &nbsp;&nbsp;[`.pause()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L130) | Hold every call back until the limit resets: until the time the refusal names, else for `QUOTA_RETRY_SECONDS`, after which one call is let through to see whether the limit still holds. |
| &nbsp;&nbsp;[`.complete_with_usage()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L147) | One model call turned into a JSON object. |
| [`class StubBackend`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L193) | Loads a Python module exposing `respond(role, context) -> dict`; deterministic and offline. |
| [`make_client(cfg, calls_used)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/base.py#L220) |  |

## `model/catalog.py` { #m-model-catalog-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/catalog.py)

The Claude models this version knows: their ids, prices, and the effort levels each accepts.

| Name | What it does |
|---|---|
| [`rates(model, given)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/catalog.py#L50) | A model's prices and where they come from: the brief's `agents.prices`, else this list, else none. |
| [`effort_to_send(model, effort)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/catalog.py#L61) | The effort to put in a request, or None to leave it to the model: when none is set, when the setting is `model_default`, or when the model is known not to accept that level (the plan warns of it). |
| [`fault(model, effort)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/catalog.py#L72) | Why this effort does not suit this model, when the model is known; None otherwise. |

## `model/claude_code.py` { #m-model-claude-code-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/claude_code.py)

Backend: Claude Code run non-interactively as a subprocess, with no tools.

| Name | What it does |
|---|---|
| [`build_argv(binary, system, model, effort)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/claude_code.py#L17) |  |
| [`parse_output(stdout)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/claude_code.py#L29) | The reply text and token counts from `claude --print --output-format json`. |
| [`class ClaudeCodeBackend`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/claude_code.py#L57) |  |

## `model/quota.py` { #m-model-quota-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/quota.py)

Recognising a refusal by the account's spend or usage limit, and reading when the limit resets.

| Name | What it does |
|---|---|
| [`quota_reset_time(message, now)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/model/quota.py#L30) | The reset time a limit message names, as a Unix time a minute past it; None when it names none or it cannot be read. |

## `__init__.py` { #m-init---py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/__init__.py)

evoloop.


## `__main__.py` { #m-main---py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/__main__.py)


## `evojob.py` { #m-evojob-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/evojob.py)

Helpers for an evaluator (adapter/run.py).

| Name | What it does |
|---|---|
| [`class Job`](https://github.com/cameo-db/evoloop/blob/main/evoloop/evojob.py#L39) |  |
| &nbsp;&nbsp;[`.path()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/evojob.py#L74) | A file in the folder kept for this run across starts: put weights and optimizer state there. |
| &nbsp;&nbsp;[`.load_state()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/evojob.py#L78) | What `save_state` last wrote, or None when this run has not saved anything yet. |
| &nbsp;&nbsp;[`.save_state()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/evojob.py#L87) | Small facts to continue from (the epoch reached, the best score so far), written in one step so that a job killed while saving leaves the earlier state whole. |
| &nbsp;&nbsp;[`.report()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/evojob.py#L96) | One line of progress. |
| &nbsp;&nbsp;[`.should_stop()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/evojob.py#L106) | True when the search asked this run to end early. |
| &nbsp;&nbsp;[`.out_of_time()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/evojob.py#L117) | True when the job was told to end, or when its time limit would pass before another step like the longest so far could finish. |
| &nbsp;&nbsp;[`.pause()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/evojob.py#L127) | Leave now. |
| &nbsp;&nbsp;[`.finish()`](https://github.com/cameo-db/evoloop/blob/main/evoloop/evojob.py#L132) | Write the result. |

## `stub.py` { #m-stub-py }

[Source](https://github.com/cameo-db/evoloop/blob/main/evoloop/stub.py)

The built-in stub: stands in for every agent role so that a search can be dry-run with no model call.

| Name | What it does |
|---|---|
| [`nudge(text, which, factor)`](https://github.com/cameo-db/evoloop/blob/main/evoloop/stub.py#L14) |  |
| [`class GenericStub`](https://github.com/cameo-db/evoloop/blob/main/evoloop/stub.py#L24) |  |
