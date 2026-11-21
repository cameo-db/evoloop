"""Lineages kept alive side by side.

Rules, all computed from the results:

- Founding. A lineage starts from a new design (a `new` or `novel` slot, a block swap or a hybrid).
- Protected trial. Until it has `population.trial_runs` finished runs it is in trial: it is owed local
  moves ahead of everything else and is not compared with other lineages.
- Population. The `population.lineages` best lineages that have finished their trial are active; the
  rest sit on the bench, where they can still be a crossover partner.
- Quota. No lineage takes more than `population.quota` of the local slots of a phase while another
  active lineage has had fewer.
- Parent. The lineage is drawn by rank, with a bonus for those built on least; within it, the parent is
  drawn among the candidates tied with its best.
- Retirement. After `population.retire_after` finished local moves in a row without a gain above the
  noise, a lineage retires to the bench."""
from __future__ import annotations

import random
from typing import Any, Dict, List

from ..store import ENDED, View
from . import Request, complement, inspirations, rank_draw, specialist, step_size, tied


def state(view: View, settings: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    pop = settings["population"]
    lineages = view.lineages()
    for lin in lineages.values():
        finished = [view.runs[r] for r in lin["runs"] if view.runs[r]["performance"].get("status") in ENDED]
        flat, best = 0, None
        for run in finished:
            value = view.own_value(run)
            if value is None:
                continue
            if best is None or value > best + view.noise:
                best, flat = (value if best is None else max(best, value)), 0
            elif run["history"].get("mode") == "local":
                flat += 1
        # A trial is a number of attempts, whatever came of them: a lineage whose children keep failing leaves
        # its trial like any other and does not hold the local slots for ever.
        attempts = [r for r in finished if r.get("purpose", "search") in ("search", "trial", "baseline")]
        lin["finished"], lin["flat"] = len(attempts), flat
        lin["failed_only"] = bool(finished) and lin["best"] is None
        if lin["best"] is None:
            lin["state"] = "failed" if lin["failed_only"] and not lin["flying"] else "starting"
        elif lin["finished"] < int(pop["trial_runs"]):
            lin["state"] = "trial"
        elif flat >= int(pop["retire_after"]):
            lin["state"] = "retired"
        else:
            lin["state"] = "contender"
    # What the strategist or the person said about a lineage stands over the rules. One set aside is retired
    # whatever its record. One brought back gets a second chance, not a permanent place: its moves without a
    # gain are counted afresh from that moment, it is active beside the best lineages (it takes no place from
    # them) until it has used that chance up, and then it retires like any other.
    for lid, word in (settings.get("_lineages") or {}).items():
        word = word if isinstance(word, dict) else {"to": word, "t": 0}
        lin = lineages.get(lid)
        if lin is None or lin["best"] is None:
            continue
        if word["to"] == "retired":
            lin["state"] = "retired"
        elif word["to"] == "revived":
            ended = [view.runs[r] for r in lin["runs"] if view.own_value(view.runs[r]) is not None]
            before = [view.own_value(r) for r in ended if r.get("ended", 0) <= word["t"]]
            best, flat = (max(before) if before else None), 0
            for run in sorted((r for r in ended if r.get("ended", 0) > word["t"]), key=lambda r: r.get("ended", 0)):
                value = view.own_value(run)
                if best is None or value > best + view.noise:
                    best, flat = (value if best is None else max(best, value)), 0
                elif run["history"].get("mode") == "local":
                    flat += 1
            lin["flat"] = flat
            if flat >= int(pop["retire_after"]):
                lin["state"] = "retired"
            elif lin["state"] != "trial":
                lin["state"], lin["revived"] = "contender", True
    contenders = sorted((l for l in lineages.values() if l["state"] == "contender"), key=lambda l: -l["best"])
    for index, lin in enumerate(contenders):
        lin["state"] = "active" if index < int(pop["lineages"]) or lin.get("revived") else "bench"
    return lineages


class Lineage:
    name = "lineage"

    def population(self, view: View, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        lins = state(view, settings)
        return [{"id": l["id"], "family": l["family"], "state": l["state"], "best": view.display(l["best"]),
                 "runs": len(l["runs"]), "parents": l["parents"]}
                for l in sorted(lins.values(), key=lambda l: (l["best"] is None, -(l["best"] or 0)))]

    def choose(self, view: View, mode: str, settings: Dict[str, Any], rng: random.Random) -> Request:
        lins = state(view, settings)
        pop = settings["population"]
        active = sorted((l for l in lins.values() if l["state"] == "active"), key=lambda l: -l["best"])
        scored = sorted((l for l in lins.values() if l["best"] is not None), key=lambda l: -l["best"])
        making = settings.get("_designing") or []      # designs being written now, not yet in the results
        busy = {d.get("lineage") for d in making}
        trials = [l for l in scored if l["state"] == "trial" and not l["flying"] and l["id"] not in busy]
        if mode in ("local", "cross") and trials and not settings.get("_forced"):
            # A lineage in trial is owed its runs before anything else is compared with it.
            lin = max(trials, key=lambda l: l["best"])
            return {"mode": "local", "purpose": "trial", "lineage": lin["id"], "parents": [lin["best_candidate"]],
                    "step": "normal", "why": "lineage %s is in its protected trial (%d of %d runs)" % (
                        lin["id"], lin["finished"], int(pop["trial_runs"]))}
        pool = active or scored
        if mode == "local" and pool:
            phase_local = [r for r in view.search_runs() if r["history"].get("mode") == "local"]
            written = [d.get("lineage") for d in making if d.get("mode") == "local"]
            total = max(1, len(phase_local) + len(written))
            counts = {l["id"]: sum(1 for r in phase_local if r["history"].get("lineage") == l["id"]) + written.count(l["id"])
                      for l in pool}
            under = [l for l in pool if counts[l["id"]] / total < float(pop["quota"]) or len(pool) == 1]
            least = min(counts.values())
            allowed = under or [l for l in pool if counts[l["id"]] == least]
            lin = rank_draw(allowed, rng, [1.0 / (1 + counts[l["id"]]) ** 0.5 for l in allowed])
            parent = specialist(view, lin["scored"], settings, rng) or tied(view, lin["scored"], float(pop["tie_margin"]), rng)
            return {"mode": "local", "lineage": lin["id"], "parents": [parent], "step": step_size(view, lin, settings),
                    "why": "lineage %s (%s), %d of %d local slots so far" % (lin["id"], lin["state"], counts[lin["id"]], total)}
        if mode == "cross" and len(scored) >= 2:
            first_lin = rank_draw(pool, rng)
            first = first_lin["best_candidate"]
            others = [l["best_candidate"] for l in scored if l["id"] != first_lin["id"]]
            second = specialist(view, others, settings, rng) or complement(view, first, others, rng)
            return {"mode": "cross", "lineage": first_lin["id"], "parents": [first, second],
                    "why": "the best of lineage %s with the candidate whose errors fall least like its own" % first_lin["id"]}
        if mode == "novel":
            return {"mode": "novel", "lineage": None, "parents": [],
                    "inspirations": inspirations(view, [l["best_candidate"] for l in active[:1]], 3, rng),
                    "why": "designs that have rarely been built on"}
        return {"mode": "new", "lineage": None, "parents": [], "why": "a family the search has not covered"}
