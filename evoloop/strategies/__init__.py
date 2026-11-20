"""Evolution strategies: how parents are chosen and what stays in the population.

A strategy answers one question, `choose(view, mode, settings, rng)`: for a slot of this mode, which
candidates are the parents, which lineage does the child belong to, and what is the writer shown.
It keeps no state: its population is computed from the view of the results each time, which is why a
run can change strategy midway.

    lineage      species kept alive side by side, with quotas, protected trials and retirement
    archive      the best of each kind of design on a grid; parents drawn across the grid
    tournament   draw a few of the most recent designs, build on the best of them (aging)
    greedy       always build on the current best

`strategy.islands` above 1 wraps any of them: separate populations that exchange designs at intervals."""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from ..store import View, pearson

Request = Dict[str, Any]


def rank_draw(items: List[Any], rng: random.Random, weights: Optional[List[float]] = None) -> Any:
    """A draw that favours the front of a ranked list without always taking it."""
    base = [len(items) - i for i in range(len(items))]
    if weights:
        base = [b * w for b, w in zip(base, weights)]
    return rng.choices(items, weights=base)[0]


def tied(view: View, candidates: List[str], margin: float, rng: random.Random) -> str:
    """One of the candidates within `margin` noise floors of the best of them: on one fit the order
    among near-equal candidates is mostly chance."""
    top = view.cands[candidates[0]]["value"]
    pool = [c for c in candidates if top - view.cands[c]["value"] <= margin * view.noise]
    return rng.choice(pool)


def signature(view: View, candidate: str) -> Optional[List[float]]:
    sig = (view.run_of(candidate).get("performance") or {}).get("signature")
    return sig if isinstance(sig, list) and len(sig) >= 3 else None


def complement(view: View, first: str, pool: List[str], rng: random.Random) -> Optional[str]:
    """The partner for a crossover: the candidate whose errors fall least like the first one's.
    Without error signatures, one of another family; without that, a rank-weighted draw."""
    pool = [c for c in pool if c != first]
    if not pool:
        return None
    mine = signature(view, first)
    if mine is not None:
        scored = [(pearson(mine, signature(view, c) or []), c) for c in pool]
        scored = [(r, c) for r, c in scored if r is not None]
        if scored:
            return min(scored, key=lambda item: (item[0], view.cands[item[1]]["order"]))[1]
    other = [c for c in pool if view.cands[c]["family"] != view.cands[first]["family"]]
    return rank_draw(other or pool, rng)


def specialist(view: View, pool: List[str], settings: Dict[str, Any], rng: random.Random) -> Optional[str]:
    """Now and then, the candidate that is best at one thing rather than best overall."""
    metrics = settings["evaluation"].get("speciality_metrics") or {}
    if not metrics or rng.random() >= float(settings["population"]["specialist_rate"]):
        return None
    name = rng.choice(sorted(metrics))
    sign = -1.0 if metrics[name] == "minimize" else 1.0
    have = [(sign * float(v), c) for c in pool
            for v in [((view.run_of(c).get("performance") or {}).get("valid") or {}).get(name)]
            if isinstance(v, (int, float))]
    return max(have)[1] if have else None


def inspirations(view: View, exclude: List[str], count: int, rng: random.Random) -> List[str]:
    """Designs that have rarely been built on, from anywhere in the ranking: what a novel slot is shown."""
    pool = [c["id"] for c in view.scored() if c["id"] not in exclude]
    out: List[str] = []
    while pool and len(out) < count:
        weights = [1.0 / (1 + view.descendants(c)) for c in pool]
        pick = rng.choices(pool, weights=weights)[0]
        out.append(pick)
        pool.remove(pick)
    return out


def step_size(view: View, lineage: Dict[str, Any], settings: Dict[str, Any]) -> str:
    """The one-in-five rule: when a lineage's recent local moves gain often, ask for bolder ones; when
    they rarely do, for smaller ones."""
    if not settings["variation"]["step_adaptation"]:
        return "normal"
    recent = []
    for rid in lineage["runs"]:
        run = view.runs[rid]
        if run["history"].get("mode") != "local" or view.own_value(run) is None:
            continue
        parent = run["history"].get("parent")
        before = view.own_value(view.runs[parent]) if parent in view.runs else None
        if before is not None:
            recent.append(view.own_value(run) - before > view.noise)
    recent = recent[-5:]
    if len(recent) < 4:
        return "normal"
    rate = sum(recent) / len(recent)
    return "bold" if rate > 0.3 else ("small" if rate < 0.15 else "normal")


def make(settings: Dict[str, Any]) -> Any:
    from . import archive, greedy, islands, lineage, tournament
    kinds = {"lineage": lineage.Lineage, "archive": archive.Archive, "tournament": tournament.Tournament,
             "greedy": greedy.Greedy}
    strat = settings["strategy"]
    inner = kinds[strat["mechanism"]]()
    return islands.Islands(inner, int(strat["islands"])) if int(strat.get("islands") or 1) > 1 else inner
