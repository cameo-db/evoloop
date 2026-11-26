"""The brief: one form that sets up a search, and the settings derived from it.

The person fills in `brief.yaml` by hand, or leaves fields empty and is asked. A setting's value comes
from the first of these that gives one:

    1. the steering ledger (a change made while the run is going)
    2. the brief (what the person wrote or answered)
    3. the run type the person chose (a named bundle of settings)
    4. the guidance for the size of the budget (about 30, 100, 300 or 1,000 evaluations)
    5. the default

and `resolve` returns, beside the settings, where each value came from, so that the plan can show it.
Nothing is filled in by guessing: a required field that is empty stops the run and becomes a question."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import yaml

EMPTY = (None, "", "TODO")
MODES = ("new", "novel", "cross", "local")
MECHANISMS = ("lineage", "archive", "tournament", "pareto", "greedy")
CROSS_KINDS = ("block_swap", "graft", "hybrid")
LOCAL_MOVES = ("edit", "settings", "ablation")
HARNESS = ("minimal", "standard", "full")
SPACES = ("settings_only", "module", "template", "open_architecture", "architecture_and_recipe", "custom")
STRATEGIST_ACTIONS = ("stay", "shares", "novelty", "local_mix", "crossover_kinds", "force", "retire", "revive", "direction",
                      "strategy", "question")
REVIEW_PRESETS = {"none": [], "end": [1.0], "halfway": [0.5, 1.0], "thirds": [0.33, 0.67, 1.0],
                  "quarterly": [0.25, 0.5, 0.75, 1.0], "on_demand": []}

DEFAULTS: Dict[str, Any] = {
    "objective": {"goal": None, "metric": "score", "direction": None, "constraints": [], "success_threshold": None},
    "run": {"type": None, "description": "", "skill": None},
    "space": {"preset": "open_architecture", "modules": [], "roles": {}, "settings": "open",
              "recipe_roles": ["loss", "optimizer", "schedule", "augmentation", "training", "recipe"],
              "forbidden": [], "must_keep": [], "forbidden_terms": [],
              # Bounds for the settings sampler (variation.settings_by: tpe): {"block.key": [low, high]}.
              "ranges": {}},
    "strategy": {"mechanism": "lineage", "islands": 1, "migrate_every": 12,
                 "tournament_size": 3, "window": 24, "descriptors": ["family", "size"],
                 # FunSearch-style resets: every so many scored runs the weaker half of the islands start again from the
                 # best of a surviving one. 0: never.
                 "reset_every": 0,
                 # A second thing to do well on beside the score (`pareto`): a metric the runs report, `parameters`,
                 # `examples_per_s` or `training_minutes`.
                 "second_metric": None, "second_direction": "minimize", "behaviour_similarity": 0.9},
    "schedule": {"phases": [{"until": 0.6, "new": 0.65, "cross": 0.10, "local": 0.25},
                            {"until": 1.0, "new": 0.15, "cross": 0.25, "local": 0.60}],
                 "novel_share": 0.33, "novelty": 0.3, "novelty_measure": "auto", "adaptive": 0.0, "floor": 0.05, "founder_credit": 0.5,
                 "local_mix": {"edit": 0.5, "settings": 0.35, "ablation": 0.15}},
    "population": {"lineages": 8, "quota": 0.4, "trial_runs": 2, "retire_after": 6, "tie_margin": 1.0,
                   "specialist_rate": 0.15},
    "crossover": {"kinds": ["block_swap", "graft", "hybrid"]},
    "variation": {"proposals_per_slot": 2, "step_adaptation": True, "settings_by": "agent",
                  # full: a writer returns the whole of each block it changes. diff: for a change to part of a block it
                  # may return find-and-replace edits, which cost fewer tokens on large blocks.
                  "edit_format": "full",
                  # Ways of working handed to the writers, one per slot, kept or dropped by how their designs did:
                  # off, fixed (yours only, from approach_seeds) or evolve (the analyst adds to them).
                  "approaches": "off", "approach_pool": 6, "approach_seeds": []},
    "harness": {"autonomy": None, "level": "full", "coordinator": "code", "analyst_every": 8, "conductor": "code"},
    "strategist": {"mode": "off", "every": 15, "plateau": 12, "horizon": 15, "min_new_share": 0.10,
                   "max_share_shift": 0.15, "force_max": 5, "ask_first": ["strategy"]},
    "evaluation": {"allowance": None, "allowance_unit": "steps", "seed": 0, "noise": None, "screen_fraction": 0.5,
                   "screen_keep": 0.5, "screen_min_pool": 4, "recheck_every": 0, "speciality_metrics": {},
                   # The metrics to track, each with how it is computed: {name: definition}. Recorded in the study file.
                   "metrics": {},
                   # Held-out evaluations to run on every design, in the same form. Never shown to an agent.
                   "test_metrics": {},
                   # A promotion ladder (successive halving inside one job): at each share `at` of a run, only the best
                   # `keep` of the designs that got there go on, e.g. [{at: 0.1, keep: 0.5}, {at: 0.3, keep: 0.5}].
                   # Empty: the single screen above, for new designs only.
                   "ladder": [], "ladder_applies": "all",
                   "schedule_depends_on_length": True, "keep_checkpoints": False, "on_length_change": "auto",
                   "leaders_refit": 4, "test_set": "held_out", "quick_check": None,
                   # A child is handed its parent's checkpoint folder (EVO_PARENT_CHECKPOINT_DIR) to start from.
                   "inherit_weights": False,
                   # Passed to every job as environment variables, e.g. {PATIENCE: 5, MIN_GAIN: 0.001}: what the adapter reads
                   # beside the run length. A change begins a new period, like a change of the run length.
                   "variables": {}},
    "budget": {"evaluations": None, "model_dollars": None, "model_calls": None, "wall_clock_hours": None,
               "max_uncounted_failures": 10, "max_uncounted_rejections": 50, "spend_policy": "pace", "reserve_share": 0.15},
    "baseline": {"mode": None, "import_from": None},
    "compute": {"gpus": None, "scheduler": "local", "allocation": "per_design", "partition": None, "qos": None, "gpu_type": None, "larger_gpu_type": None,
                "gpus_per_job": 1, "cpus_per_job": 4, "mem_gb": 32, "time_limit": "2-00:00:00", "setup": [],
                "extra_sbatch": [], "infrastructure_retries": 3, "max_running": None, "max_waiting": 1},
    "run_command": "python adapter/run.py",
    "audit": {"reviews": "halfway", "review_roles": "all"},
    "agents": {"backend": None, "stub_module": None, "default_model": "claude-opus-5-5", "models": {}, "effort": "medium",
               # Several models for the writers, by share of the calls: [{model: a, share: 0.8}, {model: b, share: 0.2}].
               "writer_mix": [],
               "efforts": {"writer": "high"}, "fallbacks": "default", "max_tokens": 64000,
               "call_timeout_seconds": 900, "max_concurrent_calls": 4, "max_retries": 2, "prices": {}},
    "data": {"name": None, "accession": None, "input": None, "output": None, "examples": None,
             "preprocessing": None, "splits": None, "fraction": 1.0},
    "depositor": {"name": None, "orcid": None, "lab": None, "institution": None},
    "license": "MIT",
    "report": {"columns": [], "top": 15},
    # Enforced by code on every result and on progress lines: {metric: {max: x}} or {metric: {min: x}}. A design
    # outside a limit is rejected: it has no score, is not charged, and is shown to the writers with the reason.
    "limits": {},
}

# Asked whenever empty. Everything else takes its value from the run type, the budget guidance or the default,
# and the plan says which.
REQUIRED: Dict[str, Tuple[str, str]] = {
    "objective.goal": ("What is being improved, and why?", "Every agent reads this on every call."),
    "objective.direction": ("Is a higher score better (maximize) or a lower one (minimize)?", "Selection turns on it."),
    "run.type": ("What kind of search do you want: explore_then_exploit, refine, survey, discovery, settings_only, "
                 "or custom (then describe it in run.description)?",
                 "It sets the strategy, the schedule, the harness and the search space unless you set them yourself."),
    "budget.evaluations": ("How many models may be trained in all?", "The schedule and the guidance for a small or "
                           "large search are worked out from it."),
    "evaluation.allowance": ("How long is one training run, in the project's own unit?", "Passed to every job."),
    "evaluation.noise": ("How much does the score differ between two fits of the same model (a number)?",
                         "A difference smaller than this is treated as no difference."),
    "baseline.mode": ("Should the baseline be trained inside the search (train), imported from a finished fit "
                      "(import), or skipped (skip)?", "It is the reference every gain is measured against."),
    "compute.gpus": ("How many models may train at once?", "The number of jobs kept running."),
    "agents.backend": ("Which agent backend: anthropic_api, claude_code, or stub (no cost, for a dry run)?",
                       "Decides who writes the designs and what it costs."),
    "budget.model_dollars": ("What is the most the agents may cost, in dollars (0 for a stub run)?",
                             "The run stops asking agents when it is reached."),
}

CHOICES = {"objective.direction": ("maximize", "minimize"), "strategy.mechanism": MECHANISMS, "harness.level": HARNESS,
           "harness.coordinator": ("code", "agent"), "space.preset": SPACES, "baseline.mode": ("train", "import", "skip"),
           "compute.scheduler": ("local", "slurm"), "compute.allocation": ("per_design", "block"), "agents.backend": ("stub", "anthropic_api", "claude_code"),
           "evaluation.on_length_change": ("auto", "continue", "rerun", "compare_anyway"),
           "variation.settings_by": ("agent", "sampler", "tpe"), "strategist.mode": ("off", "advise", "act"),
           "variation.edit_format": ("full", "diff"), "variation.approaches": ("off", "fixed", "evolve"),
           "evaluation.ladder_applies": ("new", "all"), "schedule.novelty_measure": ("auto", "code", "behaviour"),
           "strategy.second_direction": ("maximize", "minimize"),
           "budget.spend_policy": ("none", "pace"), "harness.autonomy": ("harnessed", "guided", "agentic"), "harness.conductor": ("code", "agent"),
           "agents.effort": ("low", "medium", "high", "xhigh", "max", "model_default"), "agents.fallbacks": ("default", "off")}

# What may change while a run is going. A change applies to the next design; jobs already started are untouched.
LIVE = ("schedule.", "limits", "strategist.", "population.", "crossover.", "variation.", "harness.", "strategy.", "space.", "audit.", "budget.",
        "compute.max_running", "compute.time_limit", "compute.qos", "compute.partition", "compute.gpus", "compute.max_waiting",
        "compute.gpu_type", "compute.larger_gpu_type",
        "evaluation.screen_", "evaluation.ladder", "evaluation.recheck_every", "evaluation.speciality_metrics", "evaluation.metrics", "evaluation.test_metrics", "evaluation.on_length_change",
        "evaluation.leaders_refit", "agents.models", "agents.writer_mix", "agents.default_model", "agents.effort", "agents.efforts", "agents.fallbacks", "agents.prices",
        "report.", "run.")
# These change what a score means. They may change too, and then a new period begins: the leaders are fitted again
# (or continued) under the new setting and earlier scores stop deciding selection.
NEW_PERIOD = ("evaluation.allowance", "evaluation.seed", "data.fraction", "evaluation.variables", "evaluation.inherit_weights")
FROZEN_WHY = "it defines the problem (the objective, the data, the scoring); start a new run to change it"

RUN_TYPES: Dict[str, Dict[str, Any]] = {
    "explore_then_exploit": {"strategy": {"mechanism": "lineage"}, "harness": {"level": "full"},
                             "strategist": {"mode": "act"}},
    "refine": {
        "strategy": {"mechanism": "lineage"}, "harness": {"level": "full"}, "strategist": {"mode": "act"},
        "schedule": {"phases": [{"until": 1.0, "new": 0.10, "cross": 0.20, "local": 0.70}], "novel_share": 0.0},
        "population": {"lineages": 3}, "space": {"preset": "template"}},
    "survey": {
        "strategy": {"mechanism": "archive"}, "harness": {"level": "standard"}, "strategist": {"mode": "act"},
        "schedule": {"phases": [{"until": 1.0, "new": 0.75, "cross": 0.10, "local": 0.15}]}},
    "discovery": {
        "strategy": {"mechanism": "archive"}, "harness": {"level": "minimal"},
        "space": {"preset": "architecture_and_recipe"},
        "schedule": {"phases": [{"until": 1.0, "new": 0.60, "cross": 0.15, "local": 0.25}], "novel_share": 0.5,
                     "novelty": 0.7}},
    "settings_only": {
        "space": {"preset": "settings_only"}, "harness": {"level": "minimal"}, "strategy": {"mechanism": "greedy"},
        "schedule": {"phases": [{"until": 1.0, "new": 0.0, "cross": 0.0, "local": 1.0}], "novel_share": 0.0,
                     "local_mix": {"edit": 0.0, "settings": 1.0, "ablation": 0.0}},
        "crossover": {"kinds": []}},
    "custom": {},
}
# How much of the search the agents decide. An overlay like a run type, laid over it: what you set yourself in the
# brief still wins. Left empty, the run type's own choices stand.
AUTONOMY: Dict[str, Dict[str, Any]] = {
    "harnessed": {   # code decides where the search goes; agents write designs and lessons
        "harness": {"level": "full", "coordinator": "code"}, "strategist": {"mode": "off"},
        "variation": {"proposals_per_slot": 1, "settings_by": "sampler"}, "audit": {"reviews": "end"}},
    "guided": {      # code runs the schedule; a strategist may change its course within bounds
        "harness": {"level": "full", "coordinator": "code"}, "strategist": {"mode": "act"},
        "variation": {"settings_by": "agent"}},
    "agentic": {     # agents choose each slot and steer the search; code keeps the floors and the records
        "harness": {"level": "full", "coordinator": "agent", "analyst_every": 5},
        "strategist": {"mode": "act", "every": 10, "plateau": 8, "max_share_shift": 0.30, "force_max": 8, "ask_first": []},
        "variation": {"proposals_per_slot": 3, "settings_by": "agent"}, "audit": {"reviews": "thirds"}},
}


GUIDANCE: List[Tuple[int, str, Dict[str, Any]]] = [
    (45, "about 30", {
        "strategy": {"mechanism": "greedy"}, "population": {"lineages": 3, "trial_runs": 1},
        "crossover": {"kinds": ["graft"]}, "schedule": {"novel_share": 0.0, "adaptive": 0.0},
        "variation": {"proposals_per_slot": 4}, "audit": {"reviews": "end"}}),
    (180, "about 100", {
        "population": {"lineages": 6, "trial_runs": 2}, "crossover": {"kinds": ["graft", "hybrid"]},
        "schedule": {"novel_share": 0.15}, "variation": {"proposals_per_slot": 3}, "audit": {"reviews": "halfway"}}),
    (600, "about 300", {
        "population": {"lineages": 10, "trial_runs": 2}, "schedule": {"novel_share": 0.33},
        "variation": {"proposals_per_slot": 2}, "audit": {"reviews": "quarterly"}}),
    (10 ** 9, "1,000 or more", {
        "strategy": {"mechanism": "archive"}, "harness": {"level": "minimal"}, "schedule": {"adaptive": 0.5},
        "variation": {"proposals_per_slot": 1}, "audit": {"reviews": "on_demand"}}),
]


class BriefError(Exception):
    pass


def flatten(tree: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in tree.items():
        path = prefix + str(key)
        if isinstance(value, dict) and value and path not in ATOMIC:
            out.update(flatten(value, path + "."))
        else:
            out[path] = value
    return out


# Mappings that are one value, not a group of fields.
ATOMIC = ("space.ranges", "space.roles", "schedule.local_mix", "evaluation.speciality_metrics", "evaluation.metrics", "evaluation.test_metrics", "agents.models", "agents.prices", "agents.efforts", "evaluation.variables", "limits",
          "data.examples", "data.splits")


def get(tree: Dict[str, Any], path: str, default: Any = None) -> Any:
    node: Any = tree
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def put(tree: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    node = tree
    for part in parts[:-1]:
        node = node.setdefault(part, {})
        if not isinstance(node, dict):
            raise BriefError("%s is not a group of settings" % path)
    node[parts[-1]] = value


def known(path: str) -> bool:
    return path in flatten(DEFAULTS) or any(path.startswith(p + ".") for p in ATOMIC)


def guidance_for(evaluations: Any) -> Tuple[str, Dict[str, Any]]:
    if not isinstance(evaluations, (int, float)) or evaluations <= 0:
        return "", {}
    for limit, label, overlay in GUIDANCE:
        if evaluations < limit:
            return label, overlay
    return GUIDANCE[-1][1], GUIDANCE[-1][2]


def load_brief(folder: str) -> Dict[str, Any]:
    path = os.path.join(folder, "brief.yaml")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            brief = yaml.safe_load(handle) or {}
    except OSError:
        raise BriefError("no brief.yaml in %s (make one with `evoloop init`)" % folder)
    if not isinstance(brief, dict):
        raise BriefError("brief.yaml must be a mapping")
    return brief


def save_brief(folder: str, brief: Dict[str, Any]) -> None:
    path = os.path.join(folder, "brief.yaml")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write("# The brief: the scope of one search. Fill in what you know; `evoloop setup` asks for the rest.\n"
                     "# An empty field takes its value from the skill, the level of autonomy, the run type, the budget\n"
                     "# guidance or the default (the first that gives one), and\n"
                     "# `evoloop plan` shows which. Never fill a field by guessing.\n")
        yaml.safe_dump(brief, handle, sort_keys=False, default_flow_style=False, width=110)
    os.replace(tmp, path)


def given(brief: Dict[str, Any]) -> Dict[str, Any]:
    """The values the person gave, by path: everything in the brief that is not empty."""
    out = {}
    for path, value in flatten({k: v for k, v in brief.items() if k != "status"}).items():
        if value is False and "off" in (CHOICES.get(path) or ()):
            value = "off"   # YAML reads a bare `off` as false
        if value not in EMPTY and known(path):
            out[path] = value
    return out


def unknown_fields(brief: Dict[str, Any]) -> List[str]:
    return sorted(path for path in flatten({k: v for k, v in brief.items() if k != "status"}) if not known(path))


def resolve(brief: Dict[str, Any], ledger: Optional[List[Dict[str, Any]]] = None,
            folder: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """The settings in force, and for each the layer it came from."""
    settings = copy.deepcopy(DEFAULTS)
    sources = {path: "default" for path in flatten(DEFAULTS)}

    overrides: List[Dict[str, Any]] = []

    def place(path: str, value: Any, source: str) -> None:
        """Set one value, keeping a note when it replaces a different one from another layer."""
        before, was = sources.get(path, "default"), get(settings, path)
        if before != "default" and before != source and was != value:
            overrides.append({"setting": path, "was": was, "from": before, "now": value, "by": source})
        put(settings, path, copy.deepcopy(value))
        sources[path] = source

    def lay(overlay: Dict[str, Any], source: str) -> None:
        for path, value in flatten(overlay).items():
            place(path, value, source)

    # What is particular to this machine (its scheduler, partitions, QoS, how an environment is activated) comes
    # from the site file, right after the defaults: a brief that sets something itself still wins.
    from . import site as sites
    the_site, site_fault = sites.load(folder)
    if the_site and the_site["compute"]:
        lay({"compute": the_site["compute"]}, "site %s" % the_site["name"])
    stated = given(brief)
    changes = [e for e in (ledger or []) if e.get("kind") == "set" and e.get("status", "applied") == "applied"]
    budget = stated.get("budget.evaluations")
    for entry in changes:
        if entry["key"] == "budget.evaluations":
            budget = entry["value"]
    label, overlay = guidance_for(budget)
    if overlay:
        lay(overlay, "guidance for %s evaluations" % label)
    run_type = stated.get("run.type")
    for entry in changes:
        if entry["key"] == "run.type":
            run_type = entry["value"]
    if run_type in RUN_TYPES and RUN_TYPES[run_type]:
        lay(RUN_TYPES[run_type], "run type %s" % run_type)
    autonomy = stated.get("harness.autonomy")
    for entry in changes:
        if entry["key"] == "harness.autonomy":
            autonomy = entry["value"]
    if autonomy in AUTONOMY:
        lay(AUTONOMY[autonomy], "autonomy %s" % autonomy)
    # The skill (what kind of optimization this is) is laid over the run type and the level of autonomy (how to
    # search, and how much the agents decide): where they set the same thing, the skill knows the problem, so a
    # skill that searches without agents stays without agents. A skill of the person's own is found under `folder`.
    from . import skill as skills
    skill_name = stated.get("run.skill")
    for entry in changes:
        if entry["key"] == "run.skill":
            skill_name = entry["value"]
    the_skill, skill_fault = skills.combine(skill_name, folder)
    if the_skill:
        lay(the_skill["settings"], "skill %s" % the_skill["name"])
    for path, value in stated.items():
        place(path, value, "brief")
    for entry in changes:
        place(entry["key"], entry["value"], "changed by %s (%s)" % (entry.get("by") or "?", entry.get("id") or "ledger"))
    settings["_overrides"] = overrides
    # A period begins with any applied entry that changes what a score means: a setting (the run length, the
    # job variables) or a change to the frozen code that the person said moves scores.
    period = sum(1 for e in (ledger or []) if e.get("new_period") and e.get("status", "applied") == "applied")
    settings["_period"] = period
    # With an agent running the search, it has to be able to act: its meetings are on unless the brief says how.
    if settings["harness"]["conductor"] == "agent" and settings["strategist"]["mode"] == "off":
        settings["strategist"]["mode"] = "act"
        sources["strategist.mode"] = "an agent runs the search (harness.conductor)"
    settings["_guidance"] = label
    settings["_skill"], settings["_skill_fault"] = the_skill, skill_fault
    settings["_site"], settings["_site_fault"] = the_site, site_fault or sites.fault(the_site, settings)
    settings["notes"] = [e for e in (ledger or []) if e.get("kind") == "note" and e.get("status", "active") == "active"]
    # Lineages the strategist (or the person) retired or revived: the last word on each stands.
    settings["_lineages"] = {e["lineage"]: {"to": e["to"], "t": e.get("t", 0)} for e in (ledger or [])
                             if e.get("kind") == "lineage" and e.get("status", "applied") == "applied"}
    return settings, sources


def questions(brief: Dict[str, Any], everything: bool = False) -> List[Dict[str, Any]]:
    """What there is still to ask the person. Required fields first; with `everything`, every field."""
    stated = given(brief)
    out = []
    for path, (question, why) in REQUIRED.items():
        if path == "budget.model_dollars" and stated.get("agents.backend") == "stub":
            continue   # the stub makes no model call: there is nothing to cap
        if path not in stated:
            out.append({"field": path, "question": question, "why": why, "required": True,
                        "choices": list(CHOICES.get(path) or (RUN_TYPES if path == "run.type" else []))})
    if stated.get("run.type") == "custom" and "run.description" not in stated:
        out.append({"field": "run.description", "question": "Describe the search you want, in your own words.",
                    "why": "With the custom run type the settings are set from this description.", "required": True,
                    "choices": []})
    if everything:
        settings, sources = resolve(brief)
        for path, value in flatten({k: v for k, v in settings.items() if not k.startswith("_") and k != "notes"}).items():
            if path not in stated and path not in REQUIRED:
                from .menu import FIELDS   # the one place the explanations live
                out.append({"field": path, "question": "Set %s? It is now %r (%s)." % (path, value, sources.get(path)),
                            "why": FIELDS.get(path, ""), "required": False, "choices": list(CHOICES.get(path) or [])})
    return out


def check_value(path: str, value: Any) -> Optional[str]:
    if not known(path):
        return "%s is not a field of the brief" % path
    if path in CHOICES and value not in CHOICES[path] and value not in EMPTY:
        return "%s must be one of: %s" % (path, ", ".join(CHOICES[path]))
    if path == "run.type" and value not in RUN_TYPES:
        return "run.type must be one of: %s" % ", ".join(RUN_TYPES)
    if path == "schedule.phases":
        return check_phases(value)
    if path in ("evaluation.metrics", "evaluation.test_metrics") and value not in EMPTY:
        if not isinstance(value, dict) or not all(isinstance(k, str) and k.strip() for k in value):
            return "%s must map each metric's name to how it is computed" % path
        for name, about in value.items():
            if isinstance(about, dict):
                if not isinstance(about.get("definition"), str) or set(about) - {"definition", "direction", "split", "dataset"}:
                    return ("%s.%s must be text, or {definition: text, direction: maximize or minimize, split: valid or "
                            "test, dataset: the name of the data it is measured on}" % (path, name))
                if about.get("direction") not in (None, "maximize", "minimize"):
                    return "%s.%s.direction must be maximize or minimize" % (path, name)
            elif not isinstance(about, str) or not about.strip():
                return "%s.%s must say how the metric is computed" % (path, name)
    # A value of the wrong kind is refused here, not found out when the loop first uses it.
    default = flatten(DEFAULTS).get(path)
    number = isinstance(value, (int, float)) and not isinstance(value, bool)
    if value not in EMPTY:
        if isinstance(default, bool) and not isinstance(value, bool):
            return "%s must be true or false" % path
        if isinstance(default, (int, float)) and not isinstance(default, bool) and not number:
            return "%s must be a number" % path
        if isinstance(default, list) and path != "compute.qos" and not isinstance(value, list):
            return "%s must be a list" % path
        if isinstance(default, str) and path not in ("audit.reviews", "audit.review_roles", "space.settings") \
                and not isinstance(value, str):
            return "%s must be text" % path
    if path in ("evaluation.seed", "compute.max_waiting", "compute.infrastructure_retries", "evaluation.leaders_refit",
                "evaluation.screen_min_pool", "strategy.islands", "strategy.reset_every", "budget.max_uncounted_failures") \
            and value not in EMPTY and not (number and float(value).is_integer() and value >= 0):
        return "%s must be a whole number, 0 or more" % path
    if path == "space.ranges" and value not in EMPTY and (not isinstance(value, dict) or not all(
            isinstance(k, str) and isinstance(v, (list, tuple)) and len(v) == 2
            and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v) and v[0] < v[1] for k, v in value.items())):
        return "space.ranges must map a setting (block.key) to [low, high], low below high"
    if path == "run.skill" and value not in EMPTY and not (isinstance(value, str) or (
            isinstance(value, list) and all(isinstance(v, str) for v in value))):
        return "run.skill must be the name of a skill, the path of a skill folder, or a list of them"
    if path == "evaluation.ladder" and value not in EMPTY:
        ok = isinstance(value, list) and all(
            isinstance(r, dict) and set(r) == {"at", "keep"} and all(isinstance(x, (int, float)) and not isinstance(x, bool)
                                                                    for x in r.values())
            and 0 < r["at"] < 1 and 0 < r["keep"] <= 1 for r in value)
        if not ok or [r["at"] for r in value] != sorted({r["at"] for r in value}):
            return ("evaluation.ladder must be a list of rungs in rising order, each {at: share of the run, above 0 and "
                    "below 1, keep: share that goes on, above 0 and at most 1}")
    if path == "strategy.descriptors" and (not isinstance(value, list) or not value or not all(isinstance(d, str) and d for d in value)):
        return "strategy.descriptors must be a list of: family, size, behaviour, or the name of a metric the runs report"
    if path == "evaluation.screen_keep" and not (number and 0 < value <= 1):
        return "evaluation.screen_keep must be above 0 and at most 1"
    if path == "evaluation.variables" and value not in EMPTY:
        import re as _re
        if not isinstance(value, dict) or not all(isinstance(k, str) and _re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k)
                                                  and not k.startswith("EVO_") and isinstance(v, (int, float, str, bool))
                                                  for k, v in value.items()):
            return ("evaluation.variables must map names (letters, digits, underscores; not starting EVO_) to numbers, "
                    "text or true/false")
    if path == "limits" and value not in EMPTY:
        ok = isinstance(value, dict) and all(
            isinstance(m, str) and isinstance(b, dict) and b and set(b) <= {"max", "min"}
            and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in b.values()) for m, b in value.items())
        if not ok:
            return ("limits must map a metric to {max: x}, {min: x} or both, e.g. {parameters: {max: 20000000}}; typed as an "
                    "answer, `parameters <= 20000000; training_minutes <= 30`, or `none`")
    if path == "agents.efforts" and value not in EMPTY and (not isinstance(value, dict) or not all(
            isinstance(r, str) and v in CHOICES["agents.effort"] for r, v in value.items())):
        return "agents.efforts must map a role to one of: %s" % ", ".join(CHOICES["agents.effort"])
    if path == "agents.writer_mix" and value not in EMPTY and (not isinstance(value, list) or not all(
            isinstance(m, dict) and isinstance(m.get("model"), str) and m["model"] and set(m) <= {"model", "share", "effort"}
            and isinstance(m.get("share"), (int, float)) and not isinstance(m.get("share"), bool) and m["share"] > 0
            and m.get("effort", "medium") in CHOICES["agents.effort"] for m in value)):
        return "agents.writer_mix must be a list of {model: id, share: a number above 0} (and, if wanted, effort)"
    if path == "variation.approach_seeds" and (not isinstance(value, list) or not all(isinstance(t, str) and t.strip() for t in value)):
        return "variation.approach_seeds must be a list of short instructions, each a line of text"
    if path == "variation.approach_pool" and not (number and float(value).is_integer() and value >= 1):
        return "variation.approach_pool must be a whole number, 1 or more"
    if path == "agents.models" and value not in EMPTY and (not isinstance(value, dict) or not all(
            isinstance(r, str) and isinstance(m, str) and m for r, m in value.items())):
        return "agents.models must map a role to a model id"
    if path == "strategist.ask_first" and (not isinstance(value, list) or not all(isinstance(a, str) for a in value)
                                           or set(value) - set(STRATEGIST_ACTIONS)):
        return "strategist.ask_first must be a list from: %s" % ", ".join(STRATEGIST_ACTIONS)
    if path in ("strategist.min_new_share", "strategist.max_share_shift", "budget.reserve_share") \
            and not (number and 0 <= value <= 1):
        return "%s must be a number from 0 to 1" % path
    if path in ("strategist.every", "strategist.plateau", "strategist.horizon", "strategist.force_max") \
            and not (number and float(value).is_integer() and value >= 1):
        return "%s must be a whole number, 1 or more" % path
    if path in ("schedule.novel_share", "schedule.novelty", "schedule.adaptive", "schedule.founder_credit", "population.quota",
                "population.specialist_rate", "evaluation.screen_fraction", "evaluation.screen_keep", "strategy.behaviour_similarity"):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
            return "%s must be a number from 0 to 1" % path
    if path in ("budget.evaluations", "compute.gpus", "population.lineages", "population.trial_runs",
                "variation.proposals_per_slot", "evaluation.allowance"):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            return "%s must be a positive number" % path
    if path == "crossover.kinds" and (not isinstance(value, list) or not all(isinstance(k, str) and k in CROSS_KINDS for k in value)):
        return "crossover.kinds must be a list from: %s" % ", ".join(CROSS_KINDS)
    if path == "schedule.local_mix":
        shares = list(value.values()) if isinstance(value, dict) else [None]
        if set(value if isinstance(value, dict) else ["?"]) - set(LOCAL_MOVES) or not all(
                isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0 for v in shares) or sum(shares) <= 0:
            return "schedule.local_mix must give non-negative shares, not all zero, for: %s" % ", ".join(LOCAL_MOVES)
    if path == "audit.reviews" and not (value in REVIEW_PRESETS or (isinstance(value, list) and all(
            isinstance(v, (int, float)) and 0 < v <= 1 for v in value))):
        return "audit.reviews must be one of %s, or a list of shares of the budget" % ", ".join(REVIEW_PRESETS)
    return None


def check_phases(value: Any) -> Optional[str]:
    if not isinstance(value, list) or not value:
        return "schedule.phases must be a list of phases"
    last = 0.0
    for phase in value:
        if not isinstance(phase, dict) or set(phase) - {"until", "new", "cross", "local"}:
            return "a phase has `until` and the shares `new`, `cross`, `local`"
        shares = [float(phase.get(k, 0.0)) for k in ("new", "cross", "local")]
        if min(shares) < 0 or abs(sum(shares) - 1.0) > 0.011:
            return "the shares of a phase must be non-negative and sum to 1 (got %s)" % shares
        if not last < float(phase.get("until", 0)) <= 1.0:
            return "each phase's `until` must be above the one before it and at most 1"
        last = float(phase["until"])
    if abs(last - 1.0) > 1e-9:
        return "the last phase must have `until: 1.0`"
    return None


def problems(brief: Dict[str, Any]) -> List[str]:
    out = ["%s is not a field of the brief" % path for path in unknown_fields(brief)]
    for path, value in given(brief).items():
        fault = check_value(path, value)
        if fault:
            out.append(fault)
    return out


def warnings(settings: Dict[str, Any]) -> List[str]:
    """Combinations that work against each other. A warning never stops a run."""
    out = [settings["_skill_fault"]] if settings.get("_skill_fault") else []
    out += [settings["_site_fault"]] if settings.get("_site_fault") else []
    the_skill = settings.get("_skill") or {}
    clashes = the_skill.get("clashes") or []
    notes = the_skill.get("warnings") or []
    out += notes[:len(notes) - len(clashes)]
    mine = {o["setting"]: o for o in settings.get("_overrides") or [] if o["by"] == "brief"}
    for clash, note in zip(clashes, notes[len(notes) - len(clashes):]):
        if clash["setting"] in mine:      # the person's own choice settles it: say that, not which skill would have
            out.append("%s is %r because you set it in the brief. The skills disagree about it (%s: %r, %s: %r), and "
                       "neither value is used" % (clash["setting"], mine[clash["setting"]]["now"], clash["from"],
                                                  clash["value"], clash["stands"], clash["to"]))
        else:
            out.append(note)
    for need in ((settings.get("_skill") or {}).get("needs") or {}).get("adapter") or []:
        out.append("the skill needs: %s" % need)
    n = settings["budget"]["evaluations"] or 0
    mech, level = settings["strategy"]["mechanism"], settings["harness"]["level"]
    label, overlay = guidance_for(n)
    suggested = (overlay.get("strategy") or {}).get("mechanism")
    if suggested and suggested != mech:
        out.append("for %s evaluations the guidance suggests the %s strategy; this run uses %s" % (label, suggested, mech))
    agents = settings["agents"]
    if agents["backend"] not in (None, "stub"):
        from .model import catalog
        roles = ("writer", "analyst", "coordinator", "strategist", "assessor", "translator")
        models = {role: (agents.get("models") or {}).get(role) or agents.get("default_model") for role in roles}
        for model in sorted({m for m in models.values() if m}):
            if catalog.rates(model, agents.get("prices"))[0] is None and agents["backend"] == "anthropic_api":
                out.append("no price is known for %s: give agents.prices ({%s: {input: x, output: y}}, dollars per million "
                           "tokens), or the spend cap cannot count its calls and the run pauses after three of them" % (model, model))
        seen = set()
        for role, model in models.items():
            effort = (agents.get("efforts") or {}).get(role) or agents.get("effort")
            fault = catalog.fault(model, effort)
            if fault and fault not in seen:
                seen.add(fault)
                out.append(fault)
        if not agents.get("default_model") and not all(models.values()):
            out.append("no model is set for some roles: give agents.default_model")
    if settings["evaluation"].get("inherit_weights") and not settings["evaluation"].get("keep_checkpoints"):
        out.append("evaluation.inherit_weights needs the adapter to keep checkpoints: set evaluation.keep_checkpoints, "
                   "or a child finds nothing to start from")
    if settings["variation"].get("approaches") == "fixed" and not settings["variation"].get("approach_seeds"):
        out.append("variation.approaches is fixed but variation.approach_seeds is empty: there is nothing to hand out")
    if settings["variation"].get("approaches") == "evolve" and settings["harness"]["level"] == "minimal":
        out.append("variation.approaches: evolve needs the analyst, which the minimal harness does not run: no "
                   "approach will be added")
    if mech == "pareto" and not settings["strategy"].get("second_metric"):
        out.append("the pareto strategy needs strategy.second_metric (the second thing to do well on); without it, it "
                   "builds on the best design only")
    if int(settings["strategy"].get("reset_every") or 0) > 0 and int(settings["strategy"].get("islands") or 1) < 2:
        out.append("strategy.reset_every has no effect without islands (strategy.islands above 1)")
    if "behaviour" in (settings["strategy"].get("descriptors") or []) or settings["schedule"].get("novelty_measure") == "behaviour":
        out.append("behaviour is measured from `signature` in result.json: an adapter that does not report it gets "
                   "no behaviour grouping")
    if n and n < 60 and mech == "archive":
        out.append("an archive needs many designs to fill; with %d evaluations most cells will hold one model" % n)
    if n and n < 60 and settings["space"]["preset"] in ("architecture_and_recipe", "everything"):
        out.append("the search space is wide (architecture and recipe) for %d evaluations" % n)
    if n and n < 200 and settings["strategy"]["islands"] > 1:
        out.append("%d islands split %d evaluations into about %d each" % (
            settings["strategy"]["islands"], n, n // settings["strategy"]["islands"]))
    if n and n >= 1000 and level == "full":
        out.append("the full harness makes agent calls at every step; over %d evaluations that cost adds up" % n)
    if settings["harness"]["coordinator"] == "agent" and level == "minimal":
        out.append("an agent coordinator is a call per design, which the minimal harness is meant to avoid")
    if "block_swap" in settings["crossover"]["kinds"] and settings["space"]["preset"] in ("settings_only", "module"):
        out.append("block swap needs at least two open structure blocks; this search space may have one")
    if settings["evaluation"]["test_set"] != "held_out":
        out.append("no held-out test set is declared: every reported score has been selected on")
    return out


def digest(brief: Dict[str, Any]) -> str:
    body = {k: v for k, v in brief.items() if k != "status"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:16]


def confirm(folder: str, name: str) -> Dict[str, Any]:
    brief = load_brief(folder)
    open_questions = [q["field"] for q in questions(brief)]
    if open_questions:
        raise BriefError("the brief still has open questions: %s" % ", ".join(open_questions))
    faults = problems(brief)
    if faults:
        raise BriefError("; ".join(faults))
    settings = resolve(brief, folder=folder)[0]
    if settings.get("_skill_fault"):       # the files this search would read, checked now and not at the first run
        raise BriefError("%s. Correct run.skill or the skill file, read `evoloop plan`, then confirm." % settings["_skill_fault"])
    brief.setdefault("status", {}).update(confirmed_by=name, confirmed_on=time.strftime("%Y-%m-%d %H:%M"),
                                          confirmed_digest=digest(brief),
                                          confirmed_skills=dict((settings.get("_skill") or {}).get("digests") or {}))
    save_brief(folder, brief)
    return brief


def skills_changed(brief: Dict[str, Any], folder: Optional[str] = None) -> List[str]:
    """The skills whose files are not as they were when the brief was confirmed (edited, or no longer usable)."""
    then = (brief.get("status") or {}).get("confirmed_skills")
    if not isinstance(then, dict) or not (brief.get("status") or {}).get("confirmed_by"):
        return []
    now = (resolve(brief, folder=folder)[0].get("_skill") or {}).get("digests") or {}
    return sorted(n for n in set(then) | set(now) if then.get(n) != now.get(n))


def confirmed(brief: Dict[str, Any]) -> bool:
    status = brief.get("status") or {}
    return bool(status.get("confirmed_by")) and status.get("confirmed_digest") == digest(brief)


def tracked_columns(settings: Dict[str, Any]) -> List[str]:
    """The leaderboard's further columns: those asked for (`report.columns`), or else every metric the brief tracks,
    validation first and then the test evaluations. The leaderboard is for the person; agents are never shown it."""
    asked = list(settings["report"].get("columns") or [])
    if asked:
        return asked
    ev, named = settings["evaluation"], settings["objective"].get("metric")
    out = []
    for name, about in (ev.get("metrics") or {}).items():
        if name != named:
            out.append(("test.%s" if isinstance(about, dict) and about.get("split") == "test" else "valid.%s") % name)
    return out + ["test.%s" % name for name in (ev.get("test_metrics") or {})]


def at_a_glance(settings: Dict[str, Any]) -> List[str]:
    """What this search will actually do, in a few lines: what is optimized, who writes the designs, which agent
    roles run, how designs are selected and stopped, and what a later choice changed in an earlier one."""
    from . import estimate
    from . import site as sites
    out = []
    skill = settings.get("_skill")
    out.append("  Optimizing:      %s%s" % (settings["run"]["type"] or "no run type yet",
                                          ", skill %s" % skill["name"] if skill else ", no skill"))
    metric, tracked = settings["objective"].get("metric") or "score", sorted(settings["evaluation"].get("metrics") or {})
    held = sorted(settings["evaluation"].get("test_metrics") or {})
    way = {"maximize": "higher is better", "minimize": "lower is better"}.get(settings["objective"]["direction"], "direction not set")
    others = [m for m in tracked if m != metric]
    out.append("  Score:           %s, %s%s" % (
        metric if metric != "score" else "not named (set objective.metric; the study file will call it \"score\")", way,
        "; also tracked: %s" % ", ".join(others) if others else ""))
    if held:
        out.append("  Test evals:      %s (run on every design, kept from the agents)" % ", ".join(held))
    calls = estimate.calls(settings) if settings["budget"]["evaluations"] else {}
    by = settings["variation"]["settings_by"]
    moves = {"agent": "an agent", "sampler": "a sampler in code (no agent call)",
             "tpe": "a Bayesian estimator in code (tpe; no agent call)"}[by]
    writes = calls.get("writer", (0, 0, 0))[1] > 0
    if settings["space"]["preset"] == "settings_only":
        out.append("  Designs:         settings only; every move is made by %s" % moves)
    else:
        out.append("  Designs:         written by %s; settings moves by %s" % ("an agent" if writes else "code", moves))
    backend = settings["agents"]["backend"]
    active = ["%s (about %d calls)" % (role, round(n[1])) for role, n in calls.items() if n[1] >= 0.5]
    if backend == "stub":
        out.append("  Agents:          the stub backend (scripted, no cost)%s" % (
            "; roles: " + ", ".join(active) if active else "; no role is called"))
    else:
        out.append("  Agents:          %s" % (", ".join(active) if active else "none: this search calls no agent"))
        if active:
            out.append("  Model:           %s, effort %s" % (settings["agents"]["default_model"], settings["agents"]["effort"]))
    strat = settings["strategy"]
    select = strat["mechanism"] + (" on %d islands" % int(strat["islands"]) if int(strat.get("islands") or 1) > 1 else "")
    if strat["mechanism"] == "pareto":
        select += " (score and %s)" % (strat.get("second_metric") or "no second figure set")
    out.append("  Selection:       %s" % select)
    data = settings["data"]
    if data.get("name") or data.get("splits") or float(data.get("fraction") or 1) != 1:
        share = float(data.get("fraction") or 1)
        out.append("  Data:            %s%s%s" % (
            data.get("name") or "not named", "; split: %s" % data["splits"] if data.get("splits") else "",
            "; each run uses %g%% of the training data" % (100 * share) if share != 1 else ""))
    place = settings.get("_site")
    compute = settings["compute"]
    block = compute["scheduler"] == "slurm" and compute.get("allocation") == "block"
    where = "this machine, %s at once" % (compute["gpus"] or "?") if compute["scheduler"] == "local" else "Slurm, %s%s%s, %s at once" % (
        "one job that holds every GPU" if block else "one job per design, submitted as GPUs come free",
        ", partition %s" % compute["partition"] if compute.get("partition") else "",
        ", qos %s" % ", ".join(sites.names_of(compute["qos"])) if compute.get("qos") else "", compute["gpus"] or "?")
    if compute["scheduler"] == "slurm":
        where += ", %s per job" % compute["time_limit"]
    out.append("  Runs on:         %s%s" % (where, " (site file: %s)" % place["name"] if place else ""))
    for rule in (place or {}).get("rules") or []:
        out.append("  Site rule:       %s" % rule)
    steps, everyone = rungs(settings)
    if everyone:
        out.append("  Early stopping:  a ladder over every design: %s" % ", ".join(
            "at %d%% keep %d%%" % (round(100 * r["at"]), round(100 * r["keep"])) for r in steps))
    elif steps[0]["keep"] < 1:
        out.append("  Early stopping:  new designs screened at %d%%, the best %d%% go on" % (
            round(100 * steps[0]["at"]), round(100 * steps[0]["keep"])))
    else:
        out.append("  Early stopping:  none")
    money = settings["budget"]["model_dollars"]
    out.append("  Budget:          %s evaluations of %s %s%s" % (
        settings["budget"]["evaluations"], settings["evaluation"]["allowance"], settings["evaluation"]["allowance_unit"],
        "; agents capped at $%s" % money if money not in (None, "") else "; no cap on agent spend"))
    if settings.get("limits"):
        out.append("  Limits:          %s (a result that does not report one of these is rejected and the run pauses)" % ", ".join(
            "%s %s" % (m, " and ".join("%s %g" % (k, v) for k, v in sorted(b.items()))) for m, b in settings["limits"].items()))
    # A later choice that changed what the skill set, or that the skill changed: the ones worth knowing before a run.
    told = [o for o in settings.get("_overrides") or [] if o["from"].startswith("skill") or (
        o["by"].startswith("skill") and o["from"].startswith("autonomy"))]
    for o in told:
        if o["from"].startswith("skill"):
            out.append("  Changed:         %s is %r (%s), not the %r of the %s" % (
                o["setting"], o["now"], "you set it" if o["by"] == "brief" else o["by"], o["was"], o["from"]))
        else:
            out.append("  Kept:            %s stays %r as the %s sets it; the %s asks for %r" % (
                o["setting"], o["now"], o["by"], o["from"], o["was"]))
    return out


def plan_lines(brief: Dict[str, Any], star: Optional[str] = None, folder: Optional[str] = None,
               cost: Optional[List[str]] = None) -> List[str]:
    """The plan: what the search will do at a glance, the warnings, what the agents will cost, and then every
    setting with the layer its value came from."""
    settings, sources = resolve(brief, folder=folder)
    flat = flatten({k: v for k, v in settings.items() if not k.startswith("_") and k != "notes"})
    out = ["Plan for: %s" % (settings["objective"]["goal"] or "(no goal yet)"), "", "At a glance"]
    out += at_a_glance(settings)
    if settings.get("_skill"):
        from . import skill as skills
        out += ["", "Skill: %s. %s" % (settings["_skill"]["name"], settings["_skill"]["summary"])]
        out += ["  file: %s   (%s)" % (row["file"], skills.KINDS[row["kind"]])
                for row in skills.state(settings["run"].get("skill") or settings["_skill"].get("parts") or [], folder) if row["file"]]
        out.append("  Edit a file to change what the skill sets or tells the agents; this plan then shows the effect.")
    notes = warnings(settings)
    moved = skills_changed(brief, folder)
    if moved:
        notes.insert(0, "the skill file of %s changed after this brief was confirmed by %s: read this plan and confirm "
                        "again before the first run (`evoloop skills NAME --diff --dir DIR` shows edits against the library)"
                     % (", ".join(moved), brief["status"]["confirmed_by"]))
    if notes:
        out += ["", "Warnings:"] + ["  - " + note for note in notes]
    if cost:
        out += [line for line in cost]
    if settings.get("_skill"):
        from . import skill as skills
        said = skills.told(settings["_skill"])
        if said:
            out += ["", "What the skill adds to the agent calls (the text of the skill file; edit the file to change it)"] + said
    out += ["", "Every setting, by where its value came from"]
    if settings["_guidance"]:
        out.append("(budget guidance used: %s evaluations)" % settings["_guidance"])
    groups: Dict[str, List[str]] = {}
    for path in sorted(flat):
        groups.setdefault(sources.get(path, "default"), []).append("  %s = %s" % (path, json.dumps(flat[path], default=str)))
    for source in sorted(groups, key=lambda s: (s == "default", s)):
        out.append("")
        out.append("From the %s:" % source if source != "brief" else "From the brief (what you set):")
        out.extend(groups[source])
    if star:
        out.append("")
        out.append(star)
    return out


def is_live(key: str) -> bool:
    return any(key == p or key.startswith(p) for p in LIVE)


def starts_period(key: str) -> bool:
    return any(key == p or key.startswith(p) for p in NEW_PERIOD)


def check_change(key: str, value: Any) -> Optional[str]:
    """Why a setting cannot be changed during a run, or None when it can."""
    if not known(key):
        return "%s is not a setting" % key
    if not (is_live(key) or starts_period(key)):
        return "%s cannot change during a run: %s" % (key, FROZEN_WHY)
    if value in EMPTY and flatten(DEFAULTS).get(key) is not None:
        return "%s cannot be emptied during a run; give a value" % key
    return check_value(key, value)


def review_points(settings: Dict[str, Any]) -> List[float]:
    reviews = settings["audit"]["reviews"]
    return list(REVIEW_PRESETS.get(reviews, [])) if isinstance(reviews, str) else sorted(float(v) for v in reviews)


BLANK = {
    "objective": {"goal": None, "metric": None, "direction": None, "constraints": []},
    "run": {"type": None, "description": ""},
    "budget": {"evaluations": None, "model_dollars": None, "wall_clock_hours": None},
    "evaluation": {"allowance": None, "allowance_unit": "steps", "noise": None, "quick_check": None},
    "baseline": {"mode": None},
    "compute": {"gpus": None},
    "agents": {"backend": None},
    "space": {"forbidden": [], "must_keep": []},
    "data": {"name": None, "accession": None, "preprocessing": None, "splits": None},
    "depositor": {"name": None, "orcid": None, "lab": None, "institution": None},
    "status": {"confirmed_by": None, "confirmed_on": None, "confirmed_digest": None, "asked": []},
}


def rungs(settings: Dict[str, Any]) -> Tuple[List[Dict[str, float]], bool]:
    """The points of a run at which designs are compared and the weaker stopped, and whether every design is
    subject to them (a ladder) or only the first run of a new design (the single screen)."""
    ev = settings["evaluation"]
    ladder = [r for r in ev.get("ladder") or [] if isinstance(r, dict)]
    if ladder:
        return ([{"at": float(r["at"]), "keep": float(r["keep"])} for r in sorted(ladder, key=lambda r: r["at"])],
                ev.get("ladder_applies") != "new")
    return [{"at": float(ev["screen_fraction"]), "keep": float(ev["screen_keep"])}], False


def mean_charge(settings: Dict[str, Any]) -> float:
    """The share of a full run that a design costs on average under the ladder, when the pool is full: with
    [{at: 0.1, keep: 0.5}, {at: 0.3, keep: 0.5}] half the designs cost 0.1, a quarter 0.3 and a quarter 1."""
    steps, everyone = rungs(settings)
    if not everyone:
        return 1.0
    alive, cost = 1.0, 0.0
    for rung in steps:
        cost += alive * (1 - rung["keep"]) * rung["at"]
        alive *= rung["keep"]
    return cost + alive
