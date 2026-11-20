"""The schedule: what kind of slot comes next.

Four modes share the evaluations:

    new     a new family from the known design space (broad exploration)
    novel   a design built from unusual parents, far from what has been tried
    cross   a crossover of two lineages
    local   one change, a settings move or an ablation on an existing lineage (exploitation)

The brief gives the shares by phase (`schedule.phases`, with `new` split into broad and novel by
`schedule.novel_share`). The realized mix follows the shares by counting, not by drawing, so that a
short run gets the mix it was promised. With `schedule.adaptive` above 0, the shares are blended with
what each mode has returned so far, each mode keeping at least `schedule.floor`."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .form import MODES
from .store import View


def fraction_used(view: View, settings: Dict[str, Any]) -> float:
    total = float(settings["budget"]["evaluations"] or 0)
    return min(1.0, view.charged() / total) if total > 0 else 0.0


def phase_at(settings: Dict[str, Any], fraction: float) -> Dict[str, Any]:
    phases = settings["schedule"]["phases"]
    for index, phase in enumerate(phases):
        if fraction < float(phase["until"]) or index == len(phases) - 1:
            return dict(phase, index=index)
    return dict(phases[-1], index=len(phases) - 1)


def credit(view: View, founder_share: float = 0.5) -> Dict[str, Dict[str, float]]:
    """What each mode has returned: runs, and the gain in the best score it is credited with, in noise
    floors. When a run raises the best, half the gain goes to the run's own mode and half to the mode
    of the slot that founded its lineage. Without that, a new design is never credited for what was
    later built on it, and the figures always say "do more local"."""
    out = {mode: {"runs": 0.0, "gain": 0.0, "raised": 0.0} for mode in MODES}
    founders = {lid: lin["founded_by"] for lid, lin in view.lineages().items()}
    best: Optional[float] = None
    for run in view.search_runs():
        mode = run["history"].get("mode")
        value = view.own_value(run)
        if mode not in out or value is None:
            continue
        out[mode]["runs"] += 1
        if best is None:
            best = value
            continue
        gain = (value - best) / view.noise
        if gain > 1.0:
            founder = founders.get(run["history"].get("lineage"))
            founder = founder if founder in out else mode
            out[mode]["gain"] += gain * (1 - founder_share)
            out[founder]["gain"] += gain * founder_share
            out[mode]["raised"] += 1
            best = value
    return out


def shares(view: View, settings: Dict[str, Any]) -> Dict[str, float]:
    sched = settings["schedule"]
    phase = phase_at(settings, fraction_used(view, settings))
    novel = float(sched["novel_share"])
    base = {"new": float(phase.get("new", 0)) * (1 - novel), "novel": float(phase.get("new", 0)) * novel,
            "cross": float(phase.get("cross", 0)), "local": float(phase.get("local", 0))}
    blend = float(sched.get("adaptive") or 0.0)
    if blend <= 0:
        return base
    got = credit(view, float(sched.get("founder_credit", 0.5)))
    total = sum(g["runs"] for g in got.values())
    if total < 8:
        return base
    value = {m: got[m]["gain"] / max(1.0, got[m]["runs"]) + math.sqrt(2 * math.log(total + 1) / max(1.0, got[m]["runs"])) * 0.25
             for m in MODES}
    whole = sum(value.values()) or 1.0
    floor = float(sched.get("floor") or 0.0)
    learned = {m: floor + (1 - floor * len(MODES)) * value[m] / whole for m in MODES}
    return {m: (1 - blend) * base[m] + blend * learned[m] for m in MODES}


def available(view: View, settings: Dict[str, Any]) -> Dict[str, bool]:
    scored = view.scored()
    lineages = [l for l in view.lineages().values() if l["best"] is not None]
    return {"new": True, "novel": len(scored) >= 3, "cross": len(lineages) >= 2 and bool(settings["crossover"]["kinds"]),
            "local": len(scored) >= 1}


PASS_ON = {"novel": "new", "cross": "local", "local": "new", "new": "local"}


def next_mode(view: View, settings: Dict[str, Any], planned: Optional[List[str]] = None) -> str:
    """The mode furthest behind its share, counted over this phase's runs and those being designed."""
    want = shares(view, settings)
    can = available(view, settings)
    for mode in MODES:   # a mode with nothing to do passes its share on
        if not can[mode] and want[mode] > 0:
            target = PASS_ON[mode] if can[PASS_ON[mode]] else "new"
            want[target] += want[mode]
            want[mode] = 0.0
    phase = phase_at(settings, fraction_used(view, settings))["index"]
    counts = {mode: 0 for mode in MODES}
    for run in view.search_runs():
        if run["history"].get("phase") == phase and run["history"].get("mode") in counts \
                and run.get("purpose", "search") == "search":
            counts[run["history"]["mode"]] += 1
    for mode in planned or []:
        if mode in counts:
            counts[mode] += 1
    done = sum(counts.values())
    if sum(want.values()) <= 0:
        return "new"
    return max(MODES, key=lambda m: (want[m] * (done + 1) - counts[m], want[m]))
