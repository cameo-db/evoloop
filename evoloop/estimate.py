"""What the agents will cost: an estimate before a run, and a projection during one.

The more of the search the agents decide, the more calls they make. This module counts the calls a
set of settings leads to, sizes them from the search folder itself (the task text and the open blocks),
and prices them with `agents.prices`. It is used by `evoloop plan` and `evoloop estimate`, which show
the three autonomy levels side by side so that the choice can be made with the cost in view.

It is an estimate, and a rough one. The number of calls follows from the settings and is fairly sure.
The size of a call is a guess from the size of the code (about four characters to a token); how long a
model's replies are, how often a design fails, and how often the strategist meets on a plateau are not
known beforehand. So every figure comes as a range, and once a run has made calls its own measured
cost per call replaces the guess."""
from __future__ import annotations

import copy
import os
from typing import Any, Dict, List, Optional, Tuple

from . import form, space
from .agents import CORE, ROLES
from .store import Store

CHARS_PER_TOKEN = 4.0
LEVELS = ("harnessed", "guided", "agentic")
ASSUMPTIONS = [
    "about four characters to a token",
    "one design in ten fails or is refused and is written again (range: none to three in ten)",
    "the strategist meets half again as often as its schedule because of plateaus (range: as scheduled to twice)",
    "a writer's reply is the blocks it changes plus about 400 tokens of reasoning, per proposal (range: half to one and a half times)",
    "prices are yours (agents.prices) where you give them, else the built-in list, which is dated",
]


def sizes(folder: Optional[str], settings: Dict[str, Any]) -> Dict[str, float]:
    """Characters of what a writer is shown and returns, measured from the search folder when there is one."""
    out = {"task": 2000.0, "structure": 6000.0, "params": 300.0, "blocks": 2.0, "measured": 0.0}
    if not folder:
        return out
    try:
        table = space.table(os.path.join(folder, "base"))
    except (space.SpaceError, OSError):
        return out
    opened = space.open_blocks(table, settings)
    structure = [len(table[n]["content"]) for n, k in opened.items() if k == "structure"]
    params = [len(table[n]["content"]) for n, k in opened.items() if k == "params"]
    try:
        task = float(len(space.read(os.path.join(folder, "task.md"))))
    except OSError:
        task = out["task"]
    return {"task": task, "structure": float(sum(structure)), "params": float(sum(params)),
            "blocks": float(max(1, len(structure))), "measured": 1.0}


def mix(settings: Dict[str, Any]) -> Dict[str, float]:
    """The share of the budget each kind of design gets, over the whole schedule."""
    out = {"new": 0.0, "novel": 0.0, "cross": 0.0, "local": 0.0}
    last = 0.0
    novel = float(settings["schedule"]["novel_share"])
    for phase in settings["schedule"]["phases"]:
        span = float(phase["until"]) - last
        last = float(phase["until"])
        out["new"] += span * float(phase.get("new", 0)) * (1 - novel)
        out["novel"] += span * float(phase.get("new", 0)) * novel
        out["cross"] += span * float(phase.get("cross", 0))
        out["local"] += span * float(phase.get("local", 0))
    return out


def calls(settings: Dict[str, Any]) -> Dict[str, Tuple[float, float, float]]:
    """Agent calls by role over the whole budget: (low, expected, high)."""
    n = float(settings["budget"]["evaluations"] or 0)
    share = mix(settings)
    local = settings["schedule"]["local_mix"]
    whole = sum(float(v) for v in local.values()) or 1.0
    by_agent = share["new"] + share["novel"]
    by_agent += share["local"] * (float(local.get("edit", 0)) + float(local.get("ablation", 0))) / whole
    if settings["variation"]["settings_by"] == "agent":
        by_agent += share["local"] * float(local.get("settings", 0)) / whole
    kinds = settings["crossover"]["kinds"]
    if kinds:
        by_agent += share["cross"] * sum(1 for k in kinds if k != "block_swap") / float(len(kinds))
    else:
        by_agent += share["cross"]      # no crossover is possible: those slots become local moves
    out: Dict[str, Tuple[float, float, float]] = {"writer": (n * by_agent, n * by_agent * 1.1, n * by_agent * 1.3)}
    if settings["harness"]["coordinator"] == "agent":
        out["coordinator"] = (n, n * 1.1, n * 1.3)
    every = float(settings["harness"]["analyst_every"] or 0)
    if settings["harness"]["level"] != "minimal" and every > 0:
        out["analyst"] = (n / every, n / every, n / every * 1.2)
    if settings["strategist"]["mode"] != "off":
        meet = n / float(settings["strategist"]["every"])
        out["strategist"] = (meet, meet * 1.5, meet * 2.0)
    reviews = len(form.review_points(settings))
    if reviews:
        wanted = settings["audit"]["review_roles"]
        roles = len(wanted) if isinstance(wanted, list) else len(out)
        out["assessor"] = (reviews * roles, reviews * roles, reviews * roles)
    return out


def tokens(settings: Dict[str, Any], size: Dict[str, float]) -> Dict[str, Tuple[float, float]]:
    """Tokens of one call by role: (in, out), expected."""
    share = mix(settings)
    minimal = settings["harness"]["level"] == "minimal"
    one = size["structure"] + size["params"]                       # the open blocks of one design
    board = (5 if minimal else 12) * 250.0 + 40 * 80.0 + (4 if minimal else 10) * 250.0 + (0 if minimal else 20 * 200.0)
    weight = sum(share.values()) or 1.0
    # Designs shown: one for a new design or a local move, four for a novel one (three inspirations), two for a crossover.
    shown = (share["new"] * 1 + share["local"] * 1 + share["novel"] * 4 + share["cross"] * 2) / weight
    # Blocks returned: every structure block for a new or novel design and a hybrid, one block for a local move.
    back = ((share["new"] + share["novel"] + share["cross"]) * size["structure"]
            + share["local"] * size["structure"] / size["blocks"]) / weight
    proposals = float(settings["variation"]["proposals_per_slot"])
    system = lambda role: float(len(CORE) + len(ROLES[role]))   # noqa: E731
    chars = {
        "writer": (system("writer") + size["task"] + shown * one + board, 1200.0 + proposals * (back + 1600.0)),
        "coordinator": (system("coordinator") + 4 * 300.0 + 8 * 250.0 + 800.0, 600.0),
        "analyst": (system("analyst") + float(settings["harness"]["analyst_every"] or 8) * 500.0 + 10 * 250.0 + 30 * 200.0, 2000.0),
        "strategist": (system("strategist") + 9000.0, 1500.0),
        "assessor": (system("assessor") + 60 * 400.0 + 2000.0, 2500.0),
    }
    return {role: (i / CHARS_PER_TOKEN, o / CHARS_PER_TOKEN) for role, (i, o) in chars.items()}


def price_of(settings: Dict[str, Any], role: str) -> Optional[Dict[str, float]]:
    """A role's prices: the brief's `agents.prices`, else the built-in list of models."""
    from .model import catalog
    agents = settings["agents"]
    model = (agents.get("models") or {}).get(role) or agents.get("default_model")
    return catalog.rates(model, agents.get("prices"))[0]


def chosen(settings: Dict[str, Any]) -> Dict[str, Tuple[Any, Any]]:
    """The model and the effort each role runs at."""
    agents = settings["agents"]
    return {role: ((agents.get("models") or {}).get(role) or agents.get("default_model"),
                   (agents.get("efforts") or {}).get(role) or agents.get("effort"))
            for role in ("writer", "analyst", "coordinator", "strategist", "assessor")}


def estimate(settings: Dict[str, Any], folder: Optional[str] = None, measured: Optional[Dict[str, Dict[str, float]]] = None
             ) -> Dict[str, Any]:
    """Calls, tokens and dollars by role, each as (low, expected, high). Where a run has made calls of a
    role, its own mean cost and size per call are used in place of the guess."""
    size = sizes(folder, settings)
    per_call = tokens(settings, size)
    roles: Dict[str, Dict[str, Any]] = {}
    total = {"calls": [0.0, 0.0, 0.0], "tokens": [0.0, 0.0, 0.0], "dollars": [0.0, 0.0, 0.0]}
    priced = True
    for role, count in calls(settings).items():
        tin, tout = per_call[role]
        seen = (measured or {}).get(role)
        spread = (0.5, 1.0, 1.5) if role == "writer" else (0.8, 1.0, 1.3)
        row: Dict[str, Any] = {"calls": [round(c, 1) for c in count], "tokens_in_per_call": round(tin),
                               "tokens_out_per_call": round(tout), "from": "sizes of the folder" if size["measured"] else "typical sizes"}
        if seen and seen.get("calls", 0) >= 3:
            if seen.get("tokens_in"):
                tin, tout, spread = seen["tokens_in"], seen["tokens_out"], (0.9, 1.0, 1.1)
                row.update(tokens_in_per_call=round(tin), tokens_out_per_call=round(tout))
            row["from"] = "this run's %d calls so far" % seen["calls"]
        toks = [count[i] * (tin + tout * spread[i]) for i in range(3)]
        row["tokens"] = [round(t) for t in toks]
        rates = price_of(settings, role)
        if seen and seen.get("calls", 0) >= 3 and seen.get("dollars_per_call"):
            row["dollars"] = [round(count[i] * seen["dollars_per_call"] * (0.9, 1.0, 1.1)[i], 2) for i in range(3)]
        elif rates:
            row["dollars"] = [round(count[i] * (tin * rates["input"] + tout * spread[i] * rates["output"]) / 1e6, 2) for i in range(3)]
        else:
            row["dollars"] = None
            priced = False
        roles[role] = row
        for i in range(3):
            total["calls"][i] += count[i]
            total["tokens"][i] += toks[i]
            if row["dollars"]:
                total["dollars"][i] += row["dollars"][i]
    return {"roles": roles, "calls": [round(c) for c in total["calls"]], "tokens": [round(t) for t in total["tokens"]],
            "dollars": [round(d, 2) for d in total["dollars"]] if priced and roles else None,
            "priced": priced, "evaluations": settings["budget"]["evaluations"], "assumptions": ASSUMPTIONS}


def measured(store: Store) -> Dict[str, Dict[str, float]]:
    """What each role's calls have cost and weighed so far in a run."""
    out: Dict[str, Dict[str, float]] = {}
    for call in store.read("calls"):
        row = out.setdefault(call.get("role") or "?", {"calls": 0, "dollars": 0.0, "in": 0.0, "out": 0.0, "sized": 0})
        row["calls"] += 1
        row["dollars"] += float(call.get("cost_usd") or 0.0)
        toks = call.get("tokens") or {}
        if isinstance(toks.get("in"), (int, float)) and isinstance(toks.get("out"), (int, float)):
            row["in"] += toks["in"]
            row["out"] += toks["out"]
            row["sized"] += 1
    for row in out.values():
        row["dollars_per_call"] = row["dollars"] / row["calls"] if row["dollars"] > 0 else 0.0
        row["tokens_in"] = row["in"] / row["sized"] if row["sized"] and row["in"] > 0 else 0.0
        row["tokens_out"] = row["out"] / row["sized"] if row["sized"] else 0.0
    return out


def by_level(brief: Dict[str, Any], folder: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """The estimate under each autonomy level, everything else in the brief as it is. What the brief sets
    itself is kept at every level, so the levels differ only in what was left to them."""
    out = {}
    for level in LEVELS:
        variant = copy.deepcopy(brief)
        form.put(variant, "harness.autonomy", level)
        out[level] = estimate(form.resolve(variant)[0], folder)
    return out

def other_models(brief: Dict[str, Any], folder: Optional[str], now: Dict[str, Any]) -> List[str]:
    """The same search with each of the current models for every role: what the choice of model does to the cost."""
    from .model import catalog
    settings = form.resolve(brief)[0]
    if (settings["agents"].get("models") or {}):
        return []      # roles are on different models already: a one-model comparison would mislead
    out = ["", "The same search with another model for every role (agents.default_model; yours is %s):" % settings["agents"]["default_model"]]
    for model in catalog.OFFERED:
        variant = copy.deepcopy(brief)
        form.put(variant, "agents.default_model", model)
        est = estimate(form.resolve(variant)[0], folder)
        info = catalog.MODELS[model]
        out.append("  %-20s %s   ($%g in, $%g out per million tokens%s)" % (
            model, span(est["dollars"], "$", 2), info["input"], info["output"], "; " + info["note"] if info["note"] else ""))
    return out



def span(values: Any, unit: str = "", digits: int = 0) -> str:
    if values is None:
        return "no price given"
    low, mid, high = values
    show = (lambda v: "%s%.*f" % (unit, digits, v)) if digits else (lambda v: "%s%s" % (unit, format(int(round(v)), ",")))
    return "about %s (%s to %s)" % (show(mid), show(low), show(high))


def lines(brief: Dict[str, Any], folder: Optional[str] = None) -> List[str]:
    """The estimate as the plan prints it."""
    settings = form.resolve(brief)[0]
    if not settings["budget"]["evaluations"]:
        return []
    if settings["agents"]["backend"] == "stub":
        return ["", "What the agents will cost: nothing. The backend is the stub, which makes no model call."]
    now = estimate(settings, folder)
    out = ["", "What the agents will cost (an estimate, for %s designs):" % settings["budget"]["evaluations"]]
    picks = chosen(settings)
    for role, row in now["roles"].items():
        model, effort = picks.get(role, (None, None))
        out.append("  %-12s %s calls, %s tokens, %s   [%s, effort %s]" % (
            role, span(row["calls"]), span(row["tokens"]), span(row["dollars"], "$", 2), model, effort or "model default"))
    out.append("  %-12s %s calls, %s tokens, %s" % ("in all", span(now["calls"]), span(now["tokens"]), span(now["dollars"], "$", 2)))
    cap = settings["budget"]["model_dollars"]
    if now["dollars"] and cap is not None and now["dollars"][1] > float(cap):
        out.append("  The expected cost is above your cap of $%.2f: the run would be made cheaper as it goes (see "
                   "budget.spend_policy), or pause when the cap is reached." % float(cap))
    out += ["", "The same search at each level of autonomy (harness.autonomy; yours is %s):" % (
        settings["harness"]["autonomy"] or "not set, so the run type decides")]
    for level, est in by_level(brief, folder).items():
        out.append("  %-10s %s calls, %s" % (level, span(est["calls"]), span(est["dollars"], "$", 2)
                                             if est["dollars"] else span(est["tokens"]) + " tokens"))
    from .model import catalog
    agents = settings["agents"]
    models = sorted({m for m, _ in chosen(settings).values() if m})
    sources = {m: catalog.rates(m, agents.get("prices"))[1] for m in models}
    if not now["priced"]:
        out.append("  No price is known for: %s. Give agents.prices ({model: {input: x, output: y}}, dollars per million "
                   "tokens) to see dollars." % ", ".join(m for m in models if sources[m] == "no price"))
    listed = [m for m in models if sources[m].startswith("the built-in")]
    if listed:
        out.append("  Prices for %s are from %s; check them, and give agents.prices where they differ." % (
            ", ".join(listed), sources[listed[0]]))
    out.append("  Not counted: the model's own reasoning, which is billed as output and grows with effort. A run's own calls "
               "replace these guesses after a few calls (`evoloop estimate --name RUN`).")
    out.append("  A rough guide: " + "; ".join(ASSUMPTIONS[1:4]) + ".")
    for alt in other_models(brief, folder, now):
        out.append(alt)
    return out
