"""The strategist, and the spend governor.

**The strategist** is the one role that looks at the search as a whole. Code detects and reports; the
agent decides, from a bounded menu; code checks the decision and either applies it or holds it for the
person. It meets every `strategist.every` scored designs, and at once when `strategist.plateau` designs
have passed with no rise in the best score.

    stay              change nothing
    shares            the shares of new designs, crossover and local moves, for the rest of this phase
    novelty           the novelty dial (and the novel share of new designs)
    local_mix         the shares of the local moves
    crossover_kinds   which kinds of crossover are used
    force             the next few slots go to one mode, and to one kind of crossover or local move
    retire, revive    take a lineage out of the active set, or bring one back
    direction         a standing note to the writers (at most three of the strategist's stand at once)
    strategy          change the evolution strategy
    question          ask the person

With `strategist.mode: act`, a decision is applied at once unless its action is listed in
`strategist.ask_first`, it moves a share by more than `strategist.max_share_shift`, or it changes a
setting the person changed during the run; those wait for the person's yes (`evoloop approve`). With
`advise`, every decision waits. New designs never fall below `strategist.min_new_share`. Every
decision is a ledger entry with what it expects, and is scored `strategist.horizon` designs later.

**The spend governor** is code. It watches what the agents cost per design against
`budget.model_dollars`, and when the run is on course to pass the cap it makes the run cheaper, one
step at a time, each step a ledger entry."""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from . import form, schedule, strategies
from .agents import AgentError, Agents, spend
from .store import SCORED, Store, View

BY = "strategist"
GOVERNOR = "spend governor"
MENU = {
    "stay": "args: {}. Change nothing.",
    "shares": "args: {new, cross, local}, summing to 1: the shares for the rest of this phase. `new` at least "
              "min_new_share. A shift of any share by more than max_share_shift waits for the person.",
    "novelty": "args: {novelty: 0 to 1, novel_share: 0 to 1 (optional)}.",
    "local_mix": "args: {edit, settings, ablation}: the shares of the local moves.",
    "crossover_kinds": "args: {kinds: [...]} from block_swap, graft, hybrid.",
    "force": "args: {mode: new|novel|cross|local, kind: optional (a crossover kind or edit|settings|ablation), "
             "count: 1 to force_max}. The next `count` slots go there.",
    "retire": "args: {lineage: id}. Take a lineage out of the active set (lineage strategy).",
    "revive": "args: {lineage: id}. Bring a retired or benched lineage back, its record of no gain wiped.",
    "direction": "args: {text}. A standing note to the writers, e.g. where new designs should look.",
    "strategy": "args: {mechanism: lineage|archive|tournament|greedy}.",
    "question": "args: {question, default}. Ask the person; the run does not wait.",
}


def designs(view: View) -> List[Dict[str, Any]]:
    """Scored designs of the search in the current period, in the order they ended."""
    return sorted((r for r in view.search_runs() if view.own_value(r) is not None), key=lambda r: r.get("ended", 0))


def designs_ever(view: View) -> int:
    """Scored designs of the search over every period. The cadence of meetings and of the governor is counted
    in these, so that a change of the run's length, which begins a new period, does not silence them."""
    return sum(1 for r in view.search_runs() if (r.get("performance") or {}).get("status") in SCORED
               and isinstance(r["performance"].get("score"), (int, float)))


def since_gain(view: View) -> int:
    """Designs scored since the best score last rose by more than the noise. The baseline and the
    references of a period set the best to beat; only designs of the search count toward the stretch."""
    best, since = None, 0
    scored = [r for r in view.runs.values() if view.own_value(r) is not None]
    for run in sorted(scored, key=lambda r: r.get("ended", 0)):
        value = view.own_value(run)
        if best is None or value > best + view.noise:
            best, since = value if best is None else max(best, value), 0
        elif run.get("purpose", "search") in ("search", "trial"):
            since += 1
    return since


def spending(store: Store, agents: Agents, view: View, settings: Dict[str, Any]) -> Dict[str, Any]:
    """What the agents have cost, and where the run is heading.

    The rate is dollars per design *written* (scored, failed, refused or still training alike), over the
    last twenty designs once there are that many, so that it follows a step that made the run cheaper.
    The projection adds that rate for the designs still to be written."""
    budget = settings["budget"]
    cap = budget.get("model_dollars")
    written = sorted((r for r in view.runs.values() if r.get("purpose", "search") in ("search", "trial", "not_run")),
                     key=lambda r: r.get("t", 0))
    out: Dict[str, Any] = {"dollars": round(agents.dollars, 4), "cap": cap, "calls": agents.count,
                           "designs_written": len(written), "designs_scored": designs_ever(view),
                           "by_role": {r: round(row["dollars"], 4) for r, row in spend(store).items()}}
    if len(written) >= 5 and agents.dollars > 0:
        rate = agents.dollars / len(written)
        if len(written) >= 20:
            start = written[-20].get("t", 0)
            recent = sum(float(c.get("cost_usd") or 0.0) for c in store.read("calls") if c.get("t", 0) >= start)
            rate = recent / 20.0
        flying = sum(1 for r in view.in_flight() if r.get("purpose", "search") in ("search", "trial"))
        left = max(0.0, float(budget["evaluations"] or 0) - view.charged() - flying)
        out.update(per_design=round(rate, 4), designs_still_to_write=int(left),
                   projected=round(agents.dollars + rate * left, 2))
        if cap is not None and rate > 0:
            out["designs_the_cap_still_pays_for"] = int(max(0.0, float(cap) - agents.dollars) / rate)
    if cap is not None and budget["spend_policy"] != "none":
        out["reserved_for_writers_from"] = round(float(cap) * (1 - float(budget["reserve_share"])), 2)
    return out


def reserve_reached(agents: Agents, settings: Dict[str, Any]) -> bool:
    """The last part of the agent budget is kept for writing designs: analysis, strategy, reviews and the
    coordinator stop when it is reached."""
    cap = settings["budget"].get("model_dollars")
    if cap is None or settings["agents"]["backend"] == "stub" or settings["budget"]["spend_policy"] == "none":
        return False
    return agents.dollars >= float(cap) * (1 - float(settings["budget"]["reserve_share"]))


def facts(store: Store, agents: Agents, view: View, settings: Dict[str, Any], why: str) -> Dict[str, Any]:
    from . import audit
    phase = schedule.phase_at(settings, schedule.fraction_used(view, settings))
    recent = designs(view)[-20:]
    families = [(view.models.get(r.get("model")) or {}).get("family") for r in recent]
    distances = [r["history"].get("distance") for r in recent[-10:] if isinstance(r["history"].get("distance"), (int, float))]
    best = view.best()
    card = audit.scorecard(store, view)
    cross = {k: v for k, v in card["by_move"].items() if k in form.CROSS_KINDS}
    population = strategies.make(settings).population(view, settings)
    earlier = [{"id": e["id"], "action": e.get("action"), "args": e.get("args"), "status": e.get("status"),
                "expected": e.get("expects"), "outcome": e.get("outcome")}
               for e in store.merged_list("ledger") if e.get("kind") == "decision"][-8:]
    return {
        "why_now": why,
        "budget": {"evaluations": settings["budget"]["evaluations"], "spent": round(view.charged(), 1),
                   "fraction": round(schedule.fraction_used(view, settings), 3)},
        "agent_spend": spending(store, agents, view, settings),
        "best": {"candidate": best["id"], "score": view.display(best["value"]), "family": best["family"]} if best else None,
        "noise_floor": view.noise,
        "designs_since_the_best_rose": since_gain(view),
        "returns_by_mode": {m: {k: round(v, 2) for k, v in row.items()} for m, row in schedule.credit(view).items()},
        "returns_by_move": card["by_move"], "crossover_by_kind": cross,
        "writer_forecasts": card.get("writer"),
        "population": [{k: v for k, v in row.items() if k != "population"} for row in population[:12]],
        "variety": {"families_in_the_last_%d_designs" % len(recent): len(set(families)),
                    "most_common_family": max(set(families), key=families.count) if families else None,
                    "mean_distance_of_the_last_designs": round(sum(distances) / len(distances), 3) if distances else None},
        "schedule": {"phase": phase["index"], "until": phase["until"],
                     "shares_of_this_phase": {k: phase.get(k, 0.0) for k in ("new", "cross", "local")},
                     "novel_share": settings["schedule"]["novel_share"], "novelty": settings["schedule"]["novelty"],
                     "local_mix": settings["schedule"]["local_mix"]},
        "strategy": settings["strategy"]["mechanism"], "crossover_kinds": settings["crossover"]["kinds"],
        "lineages_set_aside_or_brought_back": {k: v["to"] for k, v in (settings.get("_lineages") or {}).items()},
        "your_earlier_decisions": earlier,
    }


def menu(settings: Dict[str, Any]) -> Dict[str, Any]:
    s = settings["strategist"]
    return {"actions": MENU,
            "bounds": {"min_new_share": s["min_new_share"], "max_share_shift": s["max_share_shift"], "force_max": s["force_max"]},
            "wait_for_the_person": "everything" if s["mode"] == "advise" else list(s["ask_first"]) + [
                "a share moved by more than max_share_shift", "a setting the person changed during this run"]}


def meet(store: Store, agents: Agents, view: View, settings: Dict[str, Any], why: str) -> List[Dict[str, Any]]:
    """One meeting: the decisions as the agent gave them. Checked and applied by the controller."""
    try:
        reply = agents.call("strategist", {"objective": settings["objective"], "facts": facts(store, agents, view, settings, why),
                                           "menu": menu(settings)}, about=why)
    except AgentError:
        return []
    out = []
    for decision in (reply.get("decisions") or [])[:2]:
        if isinstance(decision, dict) and isinstance(decision.get("action"), str):
            out.append(dict(decision, call=reply.get("_call")))
    return out


def person_set(ledger: List[Dict[str, Any]], key: str) -> bool:
    """Whether the person had the last word on a setting during the run: they changed it, a part of it
    (`schedule.local_mix.edit` for `schedule.local_mix`), or something it followed from (a change of the
    run type or of the budget that moved it)."""
    last = None
    for e in ledger:
        if e.get("kind") != "set" or e.get("status") != "applied":
            continue
        other = str(e.get("key"))
        if other == key or other.startswith(key + ".") or key.startswith(other + ".") or key in (e.get("also_changed") or {}):
            last = e
    return last is not None and last.get("by") not in (BY, GOVERNOR)


def number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == value and abs(value) != float("inf")


def work_out(decision: Dict[str, Any], view: View, settings: Dict[str, Any], ledger: List[Dict[str, Any]],
             anchor: Optional[Dict[str, Any]] = None, approving: bool = False
             ) -> Tuple[Optional[str], Dict[str, Any], Optional[str]]:
    """A decision turned into what it would do: (why it is refused, its effects, why it must wait).

    The effects: `sets` (settings to change), and at most one of `force`, `lineage`, `note`, `question`.
    `anchor` is the settings as they would be without the changes the strategist made by itself since the
    person last had a say: a share may move `max_share_shift` from *there* without a yes, however many
    decisions it takes. With `approving`, the person has said yes: the decision is checked against the
    run as it is now, and nothing makes it wait."""
    s = settings["strategist"]
    action, args = decision.get("action"), decision.get("args")
    args = args if isinstance(args, dict) else {}
    effects: Dict[str, Any] = {"sets": {}}
    wait: Optional[str] = None
    if action not in form.STRATEGIST_ACTIONS:
        return "not an action on the menu: %r" % (action,), effects, None
    guarded: List[str] = []     # settings whose change by the person makes this decision wait
    if action == "shares":
        new = {k: args.get(k) for k in ("new", "cross", "local")}
        if not all(number(v) and v >= 0 for v in new.values()) or abs(sum(new.values()) - 1.0) > 0.011:
            return "shares must be three non-negative numbers summing to 1", effects, None
        if new["new"] < float(s["min_new_share"]) - 1e-9:
            return "new designs may not fall below strategist.min_new_share (%s)" % s["min_new_share"], effects, None
        phases = copy.deepcopy(settings["schedule"]["phases"])
        index = schedule.phase_at(settings, schedule.fraction_used(view, settings))["index"]
        base = (anchor or settings)["schedule"]["phases"]
        base = base[index] if index < len(base) else phases[index]
        shift = max(abs(float(new[k]) - float(base.get(k, 0.0))) for k in new)
        phases[index].update({k: round(float(v), 4) for k, v in new.items()})
        effects["sets"]["schedule.phases"] = phases
        effects["phase"] = index
        if shift > float(s["max_share_shift"]) + 1e-9:
            wait = "a share would stand %.2f from where you last left it, more than strategist.max_share_shift (%s)" % (
                shift, s["max_share_shift"])
    elif action == "novelty":
        for key in ("novelty", "novel_share"):
            if key in args:
                if not number(args[key]) or not 0 <= args[key] <= 1:
                    return "%s must be a number from 0 to 1" % key, effects, None
                effects["sets"]["schedule." + key] = float(args[key])
        if not effects["sets"]:
            return "novelty needs `novelty` or `novel_share`", effects, None
    elif action == "local_mix":
        mix = {k: args.get(k, 0.0) for k in form.LOCAL_MOVES}
        if not all(number(v) and v >= 0 for v in mix.values()) or sum(mix.values()) <= 0:
            return "local_mix needs non-negative numbers for edit, settings and ablation, not all zero", effects, None
        effects["sets"]["schedule.local_mix"] = {k: float(v) for k, v in mix.items()}
    elif action == "crossover_kinds":
        kinds = args.get("kinds")
        if not isinstance(kinds, list) or not kinds or not all(isinstance(k, str) and k in form.CROSS_KINDS for k in kinds):
            return ("crossover_kinds needs a list of at least one of: %s (to stop crossover, move its share with `shares`)"
                    % ", ".join(form.CROSS_KINDS)), effects, None
        effects["sets"]["crossover.kinds"] = [k for k in form.CROSS_KINDS if k in kinds]
    elif action == "strategy":
        if args.get("mechanism") not in form.MECHANISMS:
            return "strategy needs a mechanism: %s" % ", ".join(form.MECHANISMS), effects, None
        effects["sets"]["strategy.mechanism"] = args["mechanism"]
    elif action == "force":
        mode, kind, count = args.get("mode"), args.get("kind"), args.get("count", 1)
        if not isinstance(mode, str) or mode not in form.MODES or not number(count) or count < 1:
            return "force needs a mode (%s) and a count of 1 or more" % ", ".join(form.MODES), effects, None
        allowed = {"cross": form.CROSS_KINDS, "local": form.LOCAL_MOVES}.get(mode, ())
        if kind is not None and (not isinstance(kind, str) or kind not in allowed):
            return "kind %r does not go with mode %s" % (kind, mode), effects, None
        if mode == "cross" and kind is not None and kind not in settings["crossover"]["kinds"]:
            return "crossover of kind %s is not among crossover.kinds" % kind, effects, None
        if mode == "local" and kind is not None and float(settings["schedule"]["local_mix"].get(kind, 0.0)) <= 0:
            return "local moves of kind %s have no share in schedule.local_mix" % kind, effects, None
        room = int(s["force_max"]) - int(settings.get("_forced_queued") or 0)
        if room <= 0:
            return "strategist.force_max slots (%s) are already ordered" % s["force_max"], effects, None
        effects["force"] = {"mode": mode, "kind": kind, "left": int(min(count, room))}
        guarded = ["schedule.phases"] + ({"cross": ["crossover.kinds"], "local": ["schedule.local_mix"]}.get(mode, [])
                                         if kind is not None else [])
    elif action in ("retire", "revive"):
        lineage = args.get("lineage")
        if settings["strategy"]["mechanism"] != "lineage" or int(settings["strategy"]["islands"]) > 1:
            return "%s has an effect only under the lineage strategy without islands" % action, effects, None
        if not isinstance(lineage, str) or lineage not in view.lineages():
            return "no lineage %r" % (lineage,), effects, None
        from .strategies.lineage import state as lineage_state
        now = lineage_state(view, settings)[lineage]["state"]
        leader = view.best()
        if action == "retire" and leader and leader["lineage"] == lineage:
            return "the lineage that holds the best design is not retired", effects, None
        if action == "retire" and now == "retired":
            return "lineage %s is already retired" % lineage, effects, None
        if action == "revive" and now not in ("retired", "bench"):
            return "lineage %s is %s; only a retired or benched lineage is brought back" % (lineage, now), effects, None
        effects["lineage"] = {"lineage": lineage, "to": "retired" if action == "retire" else "revived"}
    elif action == "direction":
        if not isinstance(args.get("text"), str) or not args["text"].strip():
            return "direction needs a text", effects, None
        effects["note"] = args["text"].strip()[:600]
    elif action == "question":
        if not isinstance(args.get("question"), str) or not args["question"].strip():
            return "question needs a question", effects, None
        effects["question"] = {"question": args["question"].strip()[:600], "default": args.get("default")}
    for key, value in effects["sets"].items():
        fault = form.check_change(key, value)
        if fault:
            return fault, effects, None
    if approving:
        return None, effects, None
    for key in list(effects["sets"]) + guarded:
        if wait is None and person_set(ledger, key):
            wait = "%s was changed by you during this run" % key
    if wait is None and s["mode"] == "advise" and action != "stay":
        wait = "strategist.mode is advise: every decision waits"
    if wait is None and action in s["ask_first"]:
        wait = "%s is listed in strategist.ask_first" % action
    return None, effects, wait


def score(view: View, entry: Dict[str, Any], horizon: int) -> Optional[Dict[str, Any]]:
    """What followed a decision, once `horizon` designs have been scored since it: the rise in the best
    score in noise floors, beside what the strategist expected. It shows what followed, not what the
    decision caused: there is no run without the decision to compare with."""
    after = [r for r in designs(view) if r.get("ended", 0) > entry.get("t", 0)]
    if len(after) < horizon:
        return None
    before = entry.get("best_before")
    values = [view.own_value(r) for r in after[:horizon]]
    top = max(values)
    gain = 0.0 if before is None else max(0.0, top - view.sign * float(before)) / view.noise
    expected = (entry.get("expects") or {}).get("gain")
    return {"designs": horizon, "gain": round(gain, 2), "expected": expected,
            "raised_the_best": bool(before is not None and top > view.sign * float(before) + view.noise)}


STEPS = ("variation.proposals_per_slot", "harness.coordinator", "harness.analyst_every", "strategist.every",
         "audit.reviews", "variation.settings_by")


def govern(agents: Agents, view: View, settings: Dict[str, Any], store: Store) -> Optional[Dict[str, Any]]:
    """The next step that makes the run cheaper, when it is on course to pass the spend cap, or None.

    Steps, in order: one proposal fewer per slot; slots chosen by code, not an agent; the analyst half as
    often; the strategist half as often; reviews at the end only; settings moves drawn by code."""
    budget = settings["budget"]
    cap = budget.get("model_dollars")
    if cap is None or budget["spend_policy"] != "pace" or settings["agents"]["backend"] == "stub":
        return None
    facts_ = spending(store, agents, view, settings)
    if facts_.get("projected") is None or facts_["projected"] <= float(cap):
        return None
    reason = "at $%.3f per design the run is heading for $%.2f against a cap of $%.2f" % (
        facts_["per_design"], facts_["projected"], float(cap))
    v, h, st = settings["variation"], settings["harness"], settings["strategist"]
    if int(v["proposals_per_slot"]) > 1:
        return {"key": "variation.proposals_per_slot", "value": int(v["proposals_per_slot"]) - 1, "reason": reason}
    if h["coordinator"] == "agent":
        return {"key": "harness.coordinator", "value": "code", "reason": reason}
    if h["level"] != "minimal" and 0 < int(h["analyst_every"]) < 32:
        return {"key": "harness.analyst_every", "value": int(h["analyst_every"]) * 2, "reason": reason}
    if st["mode"] != "off" and int(st["every"]) < 60:
        return {"key": "strategist.every", "value": int(st["every"]) * 2, "reason": reason}
    if settings["audit"]["reviews"] not in ("none", "end", "on_demand"):
        return {"key": "audit.reviews", "value": "end", "reason": reason}
    if v["settings_by"] == "agent":
        return {"key": "variation.settings_by", "value": "sampler", "reason": reason}
    return None
