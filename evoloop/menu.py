"""The menu: every choice a run can make, the presets, and every field of the brief, each with a line
of explanation.

This is the one place the explanations live. `evoloop menu` prints them, and the reference pages of the
documentation (`docs/menu.md`, `docs/fields.md`) are written from them, so neither can drift from what
the brief accepts: a test fails when an option or a field has no entry here, or when a page is stale."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from . import form

STRATEGIES = {
    "lineage": "Species kept alive side by side. A new lineage gets a protected trial, the best few are active, none "
               "takes more than its quota of the local slots, and one that stops gaining retires to the bench.",
    "archive": "The best of each kind of design on a grid (by family and size). Parents are drawn across the grid, "
               "the less visited cells favoured in proportion to `schedule.novelty`.",
    "tournament": "Draw a few of the most recent designs and build on the best of them. Older designs leave the "
                  "population however good they were, so one lucky score cannot dominate for long.",
    "greedy": "Always build on the current best (or one tied with it within the noise). The right choice when the "
              "budget is too small for a population.",
}
ISLANDS = ("Set `strategy.islands` above 1 to run that many separate populations of the chosen strategy. Each sees its "
           "own results only; every `strategy.migrate_every` scored runs the best design of another island is "
           "brought in as a parent.")
CROSSOVER = {
    "block_swap": "Code takes whole marked blocks from each parent: the trunk of one with the heads of the other, or "
                  "the model of one with the recipe of the other. No agent call. Needs two open blocks that differ.",
    "graft": "The one change that gained most in the donor's history, a recorded and measured difference, is applied "
             "to the recipient by an agent. The child stays in the recipient's lineage.",
    "hybrid": "An agent writes one design from the two parents and says which parts came from each. The child "
              "founds a new lineage with both parents on record.",
}
PARTNER = ("For every kind, the second parent is the candidate whose errors fall least like the first one's, when the "
           "adapter reports where a model's errors fall (`signature` in result.json); otherwise one of another family.")
LOCAL_MOVES = {
    "edit": "One attributable change to the parent's structure, so that the result has one cause. Recorded as "
            "`structural_change`.",
    "settings": "Only values in the params blocks change. Recorded as `settings_move`.",
    "ablation": "One component is removed and nothing else changes: shows what is dead weight.",
}
MODES = {
    "new": "A new family from the known design space (broad exploration). Founds a lineage.",
    "novel": "A design built from or against designs that were rarely built on. Founds a lineage.",
    "cross": "A crossover of two lineages, of one of the kinds in `crossover.kinds`.",
    "local": "A local move on an existing lineage (exploitation), of one of the kinds in `schedule.local_mix`.",
}
RUN_TYPES = {
    "explore_then_exploit": "Most searches. Mostly new designs for the first 60% of the budget, then mostly local "
                            "work and crossover on what was found.",
    "refine": "A known good model. Few lineages, mostly local moves, the overall shape of the model kept.",
    "survey": "A new problem. Mostly new designs throughout, kept on an archive so each kind stays in play.",
    "discovery": "Long runs with cheap evaluations, aiming for something unusual. Architecture and recipe both open, "
                 "novelty high, the lightest harness.",
    "settings_only": "A hyperparameter search. No structure changes; every slot is a settings move.",
    "custom": "Your own choices. Describe the search in `run.description`; where you set nothing, the guidance for "
              "the size of the budget and then the defaults apply.",
}
SPACES = {
    "settings_only": "Only params blocks are open.",
    "module": "Only the structure blocks whose role or name is listed in `space.modules`, and the params blocks.",
    "template": "Every model block is open, and writers are told to keep the overall shape of the baseline.",
    "open_architecture": "Every model block is open; the training recipe is fixed.",
    "architecture_and_recipe": "Every marked block is open: the model and the recipe (the roles in `space.recipe_roles`).",
    "custom": "Only what `space.roles` opens, role by role: {role: open | settings | fixed}.",
}
HARNESS = {
    "minimal": "A writer only: no analyst, a short context. For cheap evaluations and long runs.",
    "standard": "Adds the analyst, which writes lessons from the results every `harness.analyst_every` runs.",
    "full": "Adds a re-check of the leader on a new seed every 20 designs (or `evaluation.recheck_every`).",
}
AUTONOMY = {
    "harnessed": "Code decides where the search goes: the schedule picks each slot, there is no strategist, settings "
                 "moves are drawn by code, one proposal per slot. Agents write the designs and the lessons. The fewest "
                 "agent calls of the three.",
    "guided": "Code runs the schedule and a strategist may change its course within the bounds you set. The middle.",
    "agentic": "Agents choose each slot and steer the search: an agent coordinator, a strategist that meets more often "
               "with wider bounds and asks first for nothing, three proposals per slot. Code still keeps the budget, the "
               "floor on new designs, the frozen problem and the records. The most agent calls of the three.",
}
AUTONOMY_NOTE = ("Left empty, the run type decides. What you set yourself in the brief is kept at every level. `evoloop plan` "
                 "and `evoloop estimate` show what the agents are likely to cost at each of the three.")
COORDINATOR = {
    "code": "The schedule picks the kind of slot and the strategy picks the parents.",
    "agent": "An agent picks each slot from options code prepares; what the schedule alone would have picked is "
             "recorded beside every choice.",
}
STRATEGIST_MODES = {
    "off": "No strategist. The schedule runs as set unless you change it.",
    "advise": "The strategist meets and decides, and every decision waits for your yes or no.",
    "act": "Small decisions are applied at once and recorded; large ones wait for your yes or no.",
}
STRATEGIST_ACTIONS = {
    "stay": "Change nothing. Often the right decision.",
    "shares": "The shares of new designs, crossover and local moves for the phase in force. New designs never "
              "below `strategist.min_new_share`; a share more than `strategist.max_share_shift` from where you left it waits.",
    "novelty": "The novelty dial, and the novel share of new designs.",
    "local_mix": "The shares of the local moves: edit, settings, ablation.",
    "crossover_kinds": "Which kinds of crossover are used; at least one.",
    "force": "The next few slots (at most `strategist.force_max` on order in all) go to one mode, and if named to one kind of "
             "crossover or local move.",
    "retire": "Take a lineage out of the active set. Never the one that holds the best design.",
    "revive": "Give a retired or benched lineage a second chance: active again until it has gone as long without a gain.",
    "direction": "A standing note to the writers, such as where new designs should look. At most three stand at once.",
    "strategy": "Change the evolution strategy. Waits for you by default (`strategist.ask_first`).",
    "question": "Ask you something. The run does not wait for the answer.",
}
SPEND_POLICIES = {
    "pace": "When the agents' cost per design puts the run on course to pass `budget.model_dollars`, the run is made "
            "cheaper one step at a time: one proposal fewer per slot; slots chosen by code; the analyst half as often; "
            "the strategist half as often; reviews at the end only; settings moves drawn by code.",
    "none": "Nothing is adjusted. The cap still stops agent calls when it is reached.",
}
REVIEWS = {
    "none": "No reviews; the scorecard only.", "end": "One review, when the run ends.",
    "halfway": "At 50% of the budget and at the end.", "thirds": "At 33%, 67% and the end.",
    "quarterly": "At 25%, 50%, 75% and the end.", "on_demand": "Only when asked for with `evoloop review`.",
}

FIELDS: Dict[str, str] = {
    "objective.goal": "What is being improved and why. Every agent reads it on every call.",
    "objective.metric": "The name of the score, for the records.",
    "objective.direction": "maximize or minimize.",
    "objective.constraints": "Limits on a solution, as text. Shown to the writers; not enforced by code.",
    "objective.success_threshold": "A score at which the search stops designing and ends.",
    "run.type": "The named bundle of settings to start from. See the run types.",
    "run.description": "Your own description of the search. Kept as the first note the agents read.",
    "space.preset": "Which marked blocks are open. See the search spaces.",
    "space.modules": "With preset `module`: the roles or block names that are open.",
    "space.roles": "Per role (or block name): open, settings or fixed. Overrides the preset for that role.",
    "space.settings": "The params blocks: open, fixed, or a list of block names that may move.",
    "space.recipe_roles": "The roles that make up the training recipe; other structure blocks make up the model.",
    "space.forbidden": "What must not be done, as text. Shown to the writers; not checked by code.",
    "space.must_keep": "What must be kept, as text. Shown to the writers; not checked by code.",
    "space.forbidden_terms": "Strings a block may not contain. Enforced by code: a design that has one is not run.",
    "strategy.mechanism": "How parents are chosen and what stays in the population. See the strategies.",
    "strategy.islands": "Separate populations of the strategy; 1 for none.",
    "strategy.migrate_every": "With islands: scored runs of an island between migrations into it.",
    "strategy.tournament_size": "With `tournament`: how many are drawn for each parent.",
    "strategy.window": "With `tournament`: how many of the most recent designs make up the population.",
    "strategy.descriptors": "With `archive`: what makes a cell: `family`, `size`, or the name of a metric the runs report.",
    "schedule.phases": "The shares of new designs, crossover and local moves, by phase: each phase holds until that "
                       "share of the budget is spent.",
    "schedule.novel_share": "The part of the `new` share that goes to `novel` slots.",
    "schedule.novelty": "0 to 1. How much a design far from everything tried is favoured: in the choice among several "
                        "proposals, and in the archive's draw of a parent.",
    "schedule.adaptive": "0 to 1. 0 follows the phases exactly; above 0 blends in what each mode has returned.",
    "schedule.floor": "With an adaptive schedule: the least share any mode keeps.",
    "schedule.founder_credit": "With an adaptive schedule: the part of each gain credited to the slot that founded the "
                               "lineage, rather than to the move that made the gain.",
    "schedule.local_mix": "The shares of the local moves: edit, settings, ablation.",
    "population.lineages": "With `lineage`: how many lineages are active at once.",
    "population.quota": "With `lineage`: the largest share of the local slots one lineage may take.",
    "population.trial_runs": "With `lineage`: runs a new lineage gets before it is compared with others.",
    "population.retire_after": "With `lineage`: local moves in a row without a gain after which a lineage retires.",
    "population.tie_margin": "Candidates within this many noise floors of a lineage's best count as tied for parent.",
    "population.specialist_rate": "How often the parent is the candidate best on one of `evaluation.speciality_metrics`.",
    "crossover.kinds": "The kinds of crossover that may be used. Only these are used.",
    "variation.proposals_per_slot": "How many proposals the writer returns for a slot; one is chosen and trained.",
    "variation.step_adaptation": "Ask for bolder local edits when a lineage's recent ones gain often, smaller when rarely.",
    "variation.settings_by": "Who makes a settings move: an agent, or a sampler in code (no call).",
    "harness.autonomy": "How much of the search the agents decide: harnessed, guided or agentic. Sets the fields below it.",
    "harness.level": "How much oversight runs beside the writer. See the harness levels.",
    "harness.coordinator": "Who picks each slot: code or an agent.",
    "harness.analyst_every": "Finished runs between two analyses.",
    "strategist.mode": "Whether an agent reviews the search as a whole and may change its course. See the strategist.",
    "strategist.every": "Scored designs between two meetings of the strategist.",
    "strategist.plateau": "Designs with no rise in the best score after which the strategist meets at once.",
    "strategist.horizon": "Designs after a decision at which what followed it is scored.",
    "strategist.min_new_share": "The least share of new designs the strategist may set: exploration is protected.",
    "strategist.max_share_shift": "How far a share may stand from where you last left it without your yes.",
    "strategist.force_max": "The most slots the strategist may have on order at once.",
    "strategist.ask_first": "The actions that always wait for your yes, whatever the mode.",
    "evaluation.allowance": "The length of one training run, in the project's own unit. Passed to every job.",
    "evaluation.allowance_unit": "The name of that unit (steps, epochs, seconds), for the records.",
    "evaluation.seed": "The seed of every design's first fit.",
    "evaluation.noise": "How much the score differs between two fits of one model. A smaller difference is no difference.",
    "evaluation.screen_fraction": "The point of a new design's first run at which it is compared with earlier new designs.",
    "evaluation.screen_keep": "The share of new designs that goes on past that point; 1 switches screening off.",
    "evaluation.screen_min_pool": "Earlier new designs needed before any is stopped at the screen.",
    "evaluation.recheck_every": "Designs between two fits of the leader on a new seed; 0 leaves it to the harness level.",
    "evaluation.speciality_metrics": "Metrics a run reports, with their direction, by which a specialist parent is chosen.",
    "evaluation.schedule_depends_on_length": "Whether the learning-rate schedule depends on the run's length. If not, "
                                             "a longer run can continue a checkpoint.",
    "evaluation.keep_checkpoints": "Whether the adapter keeps checkpoints that a later run can continue.",
    "evaluation.on_length_change": "When the run length changes: auto, continue, rerun, or compare_anyway.",
    "evaluation.leaders_refit": "When a new period begins: how many lineages' leaders are fitted again.",
    "evaluation.test_set": "`held_out` when test scores are kept from the search. Recorded in the study file.",
    "evaluation.quick_check": "A command that tests a design in seconds. A design that fails it is not trained.",
    "budget.evaluations": "How many models may be trained in all.",
    "budget.model_dollars": "The most the agents may cost. No call is made once it is reached.",
    "budget.model_calls": "The most agent calls, as a second cap.",
    "budget.wall_clock_hours": "After this long the search starts nothing more and ends when its jobs do.",
    "budget.max_uncounted_failures": "Failed or invalid designs that are not charged; beyond it each is charged.",
    "budget.spend_policy": "pace (make the run cheaper when it is heading past the spend cap) or none.",
    "budget.reserve_share": "The last part of the spend cap, kept for writing designs.",
    "baseline.mode": "train (fitted inside the search), import (a finished fit) or skip.",
    "baseline.import_from": "With import: the folder holding the fit's result.json.",
    "compute.gpus": "How many training jobs run at once.",
    "compute.scheduler": "local (processes on this machine) or slurm (each run its own job).",
    "compute.partition": "Slurm partition.",
    "compute.qos": "Slurm QoS: one name, or a list in order of preference, [{name: a, max_jobs: 8}, {name: b}].",
    "compute.gpu_type": "Slurm gres type, e.g. a100; empty for any.",
    "compute.gpus_per_job": "GPUs each job asks for; 0 for a CPU job.",
    "compute.cpus_per_job": "Processors each job asks for.",
    "compute.mem_gb": "Memory each job asks for.",
    "compute.time_limit": "Slurm time limit, per start of a job.",
    "compute.setup": "Shell lines run first in each job, e.g. activating an environment.",
    "compute.extra_sbatch": "Further sbatch options.",
    "compute.infrastructure_retries": "How often a run ended by the machine is started again, uncharged.",
    "compute.max_running": "A cap on jobs at once, below `compute.gpus`, that can be moved during a run.",
    "compute.max_waiting": "On Slurm: no new design is written while this many jobs await their first start.",
    "run_command": "The command that trains one design, started in its working copy.",
    "audit.reviews": "When the assessor reviews the agents. See the review schedules, or give a list of shares.",
    "audit.review_roles": "`all`, or the list of roles to review.",
    "agents.backend": "stub (no cost), anthropic_api, or claude_code.",
    "agents.stub_module": "With stub: a Python file with respond(role, context); empty for the built-in stub.",
    "agents.default_model": "The model every role uses unless `agents.models` names another.",
    "agents.models": "A model per role: {writer: ..., analyst: ...}.",
    "agents.max_tokens": "The longest reply (anthropic_api only).",
    "agents.call_timeout_seconds": "How long one call may take.",
    "agents.max_concurrent_calls": "How many calls run side by side.",
    "agents.max_retries": "Retries of a call that failed for a passing reason; a refusal for the account's limit is never retried.",
    "agents.prices": "Dollars per million tokens, {model: {input: x, output: y}} (anthropic_api only). Without it "
                     "the spend cap cannot count the calls.",
    "data.name": "The dataset's name.",
    "data.accession": "The dataset's DOI, accession or link. The study file earns no star without it.",
    "data.input": "What an input is.",
    "data.output": "What an output is.",
    "data.examples": "Counts: {train: n, valid: n, test: n}.",
    "data.preprocessing": "How the data was prepared.",
    "data.splits": "How the split was made, with its code or files.",
    "data.fraction": "The share of the training data a run uses. Passed to jobs as EVO_DATA_FRACTION.",
    "depositor.name": "Who deposits the study.", "depositor.orcid": "Their ORCID.",
    "depositor.lab": "Their lab.", "depositor.institution": "Their institution.",
    "license": "The licence of the study file.",
    "report.columns": "Further leaderboard columns: valid.<metric> or test.<metric>.",
}

SECTIONS: List[Tuple[str, str, str, Dict[str, str], str]] = [
    ("run-types", "Run types", "run.type", RUN_TYPES, ""),
    ("autonomy", "Autonomy: agentic first, or strongly harnessed", "harness.autonomy", AUTONOMY, AUTONOMY_NOTE),
    ("strategies", "Evolution strategies", "strategy.mechanism", STRATEGIES, ISLANDS),
    ("modes", "Slot modes", "schedule.phases", MODES, ""),
    ("crossover", "Crossover kinds", "crossover.kinds", CROSSOVER, PARTNER),
    ("moves", "Local moves", "schedule.local_mix", LOCAL_MOVES, ""),
    ("spaces", "Search spaces", "space.preset", SPACES, ""),
    ("harness", "Harness levels", "harness.level", HARNESS, ""),
    ("coordinator", "Coordinator", "harness.coordinator", COORDINATOR, ""),
    ("strategist", "The strategist", "strategist.mode", STRATEGIST_MODES, ""),
    ("strategist-actions", "What the strategist may do", "strategist.ask_first", STRATEGIST_ACTIONS,
     "Every decision is a ledger entry with the gain it expects, scored `strategist.horizon` designs later."),
    ("spend", "Spend policies", "budget.spend_policy", SPEND_POLICIES,
     "The last `budget.reserve_share` of the cap is kept for writing designs: the analyst, the strategist, the "
     "reviews and the coordinator agent stop when it is reached."),
    ("reviews", "Review schedules", "audit.reviews", REVIEWS, "Or a list of shares of the budget, such as [0.1, 0.4, 0.8]."),
]
PRESETS = {"run-types": form.RUN_TYPES, "autonomy": form.AUTONOMY}
TOPICS = [s[0] for s in SECTIONS] + ["guidance", "defaults", "fields", "all"]


def show(value: Any) -> str:
    return json.dumps(value, default=str)


def when(path: str) -> str:
    """Whether a setting can change during a run."""
    if form.starts_period(path):
        return "yes, and a new period begins"
    return "yes" if form.is_live(path) else "no"


def preset_lines(overlay: Dict[str, Any], indent: str) -> List[str]:
    return ["%s%s = %s" % (indent, key, show(value)) for key, value in sorted(form.flatten(overlay).items())]


def text(topic: str = "all") -> str:
    out: List[str] = []
    for key, title, field, entries, note in SECTIONS:
        if topic not in ("all", key):
            continue
        out += ["", "%s  (%s)" % (title.upper(), field)]
        for name, words in entries.items():
            out.append("  %-22s %s" % (name, words))
            if key in PRESETS:
                out += preset_lines(PRESETS[key][name], "      ") or ["      (sets nothing itself)"]
        if note:
            out.append("  " + note)
    if topic in ("all", "guidance"):
        out += ["", "BUDGET GUIDANCE  (budget.evaluations)",
                "  Applied below the run type and the brief: what you or the run type set wins."]
        for _, label, overlay in form.GUIDANCE:
            out.append("  %s evaluations" % label)
            out += preset_lines(overlay, "      ")
    if topic in ("all", "defaults", "fields"):
        out += ["", "FIELDS OF THE BRIEF  (field = default; changeable during a run?)"]
        for path, default in form.flatten(form.DEFAULTS).items():
            out.append("  %s = %s   [%s]" % (path, show(default), when(path)))
            if topic != "defaults":
                out.append("      " + FIELDS.get(path, ""))
    return "\n".join(out).strip() + "\n"


def cell(words: str) -> str:
    return words.replace("|", "\\|").replace("\n", " ")


def menu_markdown() -> str:
    out = ["# Menu", "",
           "Every choice a run can make. This page is written from the code (`evoloop menu --markdown`), so it "
           "lists exactly what the brief accepts.", ""]
    for key, title, field, entries, note in SECTIONS:
        out += ["## %s" % title, "", "Set with `%s`." % field, "", "| Option | What it does |", "|---|---|"]
        out += ["| `%s` | %s |" % (name, cell(words)) for name, words in entries.items()]
        out.append("")
        if note:
            out += [note, ""]
        if key in PRESETS:
            out += ["### What each %s sets" % {"run-types": "run type", "autonomy": "level of autonomy"}[key], "",
                    "It is a bundle of settings. Anything you set yourself in the brief wins over it.", ""]
            for name in entries:
                lines = preset_lines(PRESETS[key][name], "")
                out += ["**`%s`**" % name, ""] + (["```", *lines, "```"] if lines else ["Sets nothing itself."]) + [""]
    out += ["## Budget guidance", "",
            "Applied below the run type and the brief, from `budget.evaluations`: under 45 is \"about 30\", under 180 "
            "\"about 100\", under 600 \"about 300\", otherwise \"1,000 or more\". When the guidance suggests a "
            "different strategy from the run type's, `evoloop plan` says so and the run type's stands.", ""]
    for _, label, overlay in form.GUIDANCE:
        out += ["**%s evaluations**" % label, "", "```", *preset_lines(overlay, ""), "```", ""]
    return "\n".join(out).rstrip() + "\n"


def fields_markdown() -> str:
    out = ["# Fields of the brief", "",
           "Every field of `brief.yaml`, its default, and whether it can change while a run is going. This page is "
           "written from the code (`evoloop menu fields --markdown`).", "",
           "A value comes from the first of: a change made during the run, the brief, the run type, the guidance "
           "for the size of the budget, the default. `evoloop plan` shows which, for every field.", "",
           "Fields marked **asked** are asked whenever they are empty; the others are never asked unless you run "
           "`evoloop brief --all`.", ""]
    group = None
    for path, default in form.flatten(form.DEFAULTS).items():
        head = path.split(".")[0]
        if head != group:
            group = head
            out += ["", "## %s" % head, "", "| Field | Default | Changes in a run | What it is |", "|---|---|---|---|"]
        asked = " **asked**" if path in form.REQUIRED else ""
        out.append("| `%s`%s | `%s` | %s | %s |" % (path, asked, cell(show(default)), when(path), cell(FIELDS.get(path, ""))))
    return "\n".join(out).rstrip() + "\n"


def missing() -> List[str]:
    """Options and fields with no explanation here: must be empty."""
    out = []
    for name, known, entries in (("strategy", form.MECHANISMS, STRATEGIES), ("crossover", form.CROSS_KINDS, CROSSOVER),
                                 ("local move", form.LOCAL_MOVES, LOCAL_MOVES), ("mode", form.MODES, MODES),
                                 ("run type", tuple(form.RUN_TYPES), RUN_TYPES), ("space", form.SPACES, SPACES),
                                 ("harness", form.HARNESS, HARNESS), ("review", tuple(form.REVIEW_PRESETS), REVIEWS),
                                 ("coordinator", form.CHOICES["harness.coordinator"], COORDINATOR),
                                 ("autonomy", form.CHOICES["harness.autonomy"], AUTONOMY),
                                 ("strategist mode", form.CHOICES["strategist.mode"], STRATEGIST_MODES),
                                 ("strategist action", form.STRATEGIST_ACTIONS, STRATEGIST_ACTIONS),
                                 ("spend policy", form.CHOICES["budget.spend_policy"], SPEND_POLICIES)):
        out += ["%s %s" % (name, option) for option in known if option not in entries]
        out += ["%s %s (not an option)" % (name, option) for option in entries if option not in known]
    paths = form.flatten(form.DEFAULTS)
    out += ["field %s" % path for path in paths if not FIELDS.get(path)]
    out += ["field %s (not a field)" % path for path in FIELDS if path not in paths]
    return out
