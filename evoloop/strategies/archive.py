"""A quality-diversity archive: the best of each kind of design.

Every scored candidate falls in a cell given by its descriptors (`strategy.descriptors`: the family
label, and a size bin from its parameter count or, failing that, the length of its code). A cell keeps
its best candidate. Parents are drawn across the cells, the less visited ones favoured in proportion
to `schedule.novelty`, so a design that is different but behind stays in play and can be built on."""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Tuple

from ..store import View
from . import Request, complement, inspirations, rank_draw, specialist


def size_bin(view: View, candidate: str) -> int:
    run = view.run_of(candidate)
    params = (run.get("performance") or {}).get("parameters")
    if isinstance(params, (int, float)) and params > 0:
        return int(math.log(params, 4))
    count = len(run.get("settings") or {})   # no parameter count reported: a coarse stand-in
    return -1 - count


def cell_of(view: View, candidate: str, settings: Dict[str, Any]) -> Tuple[Any, ...]:
    out: List[Any] = []
    for name in settings["strategy"]["descriptors"]:
        if name == "family":
            out.append(view.cands[candidate]["family"])
        elif name == "size":
            out.append(size_bin(view, candidate))
        else:   # a metric the runs report, in thirds of its range
            values = sorted(v for c in view.scored() for v in [_metric(view, c["id"], name)] if v is not None)
            mine = _metric(view, candidate, name)
            out.append(None if mine is None or not values else min(2, int(3 * values.index(mine) / max(1, len(values)))))
    return tuple(out)


def _metric(view: View, candidate: str, name: str) -> Any:
    value = ((view.run_of(candidate).get("performance") or {}).get("valid") or {}).get(name)
    return value if isinstance(value, (int, float)) else None


def cells(view: View, settings: Dict[str, Any]) -> Dict[Tuple[Any, ...], Dict[str, Any]]:
    out: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
    for cand in view.scored():   # best first, so the first in a cell is its elite
        cell = out.setdefault(cell_of(view, cand["id"], settings), {"elite": cand["id"], "members": []})
        cell["members"].append(cand["id"])
    for cell in out.values():
        cell["visits"] = sum(view.descendants(m) for m in cell["members"])
    return out


class Archive:
    name = "archive"

    def population(self, view: View, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        grid = cells(view, settings)
        return [{"cell": list(key), "elite": cell["elite"], "best": view.display(view.cands[cell["elite"]]["value"]),
                 "members": len(cell["members"]), "visits": cell["visits"]}
                for key, cell in sorted(grid.items(), key=lambda kv: -view.cands[kv[1]["elite"]]["value"])]

    def draw(self, view: View, settings: Dict[str, Any], rng: random.Random, exclude: Any = None) -> str:
        grid = [c for c in cells(view, settings).values() if c["elite"] != exclude]
        novelty = float(settings["schedule"]["novelty"])
        elites = sorted(grid, key=lambda c: -view.cands[c["elite"]]["value"])
        # At novelty 0 the draw follows the ranking; at 1 it is by how rarely a cell has been built on.
        weights = [((len(elites) - i) / len(elites)) ** (1 - novelty) * (1.0 / (1 + c["visits"])) ** novelty
                   for i, c in enumerate(elites)]
        return rng.choices(elites, weights=weights)[0]["elite"]

    def choose(self, view: View, mode: str, settings: Dict[str, Any], rng: random.Random) -> Request:
        scored = [c["id"] for c in view.scored()]
        if mode == "local" and scored:
            parent = specialist(view, scored, settings, rng) or self.draw(view, settings, rng)
            return {"mode": "local", "lineage": view.cands[parent]["lineage"], "parents": [parent], "step": "normal",
                    "why": "the elite of cell %s" % (cell_of(view, parent, settings),)}
        if mode == "cross" and len(cells(view, settings)) >= 2:
            first = self.draw(view, settings, rng)
            others = [c["elite"] for c in cells(view, settings).values() if c["elite"] != first]
            second = complement(view, first, others, rng)
            return {"mode": "cross", "lineage": view.cands[first]["lineage"], "parents": [first, second],
                    "why": "the elites of two different cells"}
        if mode == "novel":
            return {"mode": "novel", "lineage": None, "parents": [], "inspirations": inspirations(view, scored[:1], 3, rng),
                    "why": "designs that have rarely been built on"}
        thin = sorted(cells(view, settings).items(), key=lambda kv: len(kv[1]["members"]))[:5]
        return {"mode": "new", "lineage": None, "parents": [], "thin_cells": [list(k) for k, _ in thin],
                "why": "a kind of design the archive lacks"}
