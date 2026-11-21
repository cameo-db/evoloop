"""Approaches: ways of working handed to the writers, kept or dropped by how their designs did.

An approach is a short instruction on how to go about designing ("change the receptive field before the
width", "start from the design that fails differently"). With `variation.approaches` on, each slot an
agent writes is given one approach, or none, and code keeps the record: how often a design written
under it beat its reference by more than the noise. The draw favours what has paid and still tries what
has been tried little (an upper confidence bound), and "no approach" is always one of the arms, so the
record shows whether approaches help at all.

    fixed    only the approaches the person gave (`variation.approach_seeds`)
    evolve   the analyst may add approaches from what the results show; when the pool
             (`variation.approach_pool`) is full the worst proven one is retired

This is the part of AlphaEvolve that evolves the instructions together with the designs."""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional

from .store import SCORED, ENDED, Store, View

NONE = "none"
PROVEN = 3       # finished designs before an approach can be retired for its record


def on(settings: Dict[str, Any]) -> bool:
    return settings["variation"].get("approaches", "off") != "off"


def sync(store: Store, settings: Dict[str, Any]) -> None:
    """The person's approaches, entered once each."""
    if not on(settings):
        return
    known = {a.get("text") for a in store.merged_list("approaches")}
    for text in settings["variation"].get("approach_seeds") or []:
        if isinstance(text, str) and text.strip() and text.strip() not in known:
            number = len(store.merged_list("approaches")) + 1
            store.append("approaches", {"id": "P%d" % number, "text": text.strip()[:600], "by": "person", "status": "active"})
            known.add(text.strip())


def active(store: Store) -> List[Dict[str, Any]]:
    return [a for a in store.merged_list("approaches") if a.get("status", "active") == "active"]


def reward(view: View, run: Dict[str, Any]) -> Optional[float]:
    """1 when the design beat its reference by more than the noise, 0 when it did not or broke, None while
    it trains. The reference is its parent, or for a design with no parent the middle of all scored designs."""
    status = (run.get("performance") or {}).get("status")
    if status not in ENDED:
        return None
    if status not in SCORED or view.own_value(run) is None:
        return None if status == "not_run" else 0.0
    parent = view.runs.get(run["history"].get("parent"))
    reference = view.own_value(parent) if parent else None
    if reference is None:
        others = sorted(c["value"] for c in view.scored() if c["id"] != run.get("candidate"))
        if not others:
            return None
        reference = others[len(others) // 2]
    return 1.0 if view.own_value(run) - reference > view.noise else 0.0


def record(store: Store, view: View) -> Dict[str, Dict[str, Any]]:
    """By approach (and `none`): designs written under it, those finished, and the share that beat their reference."""
    out: Dict[str, Dict[str, Any]] = {NONE: {"id": NONE, "text": None, "by": None, "status": "active"}}
    for approach in store.merged_list("approaches"):
        out[approach["id"]] = {k: approach.get(k) for k in ("id", "text", "by", "status")}
    for row in out.values():
        row.update(designs=0, finished=0, wins=0.0)
    for run in view.runs.values():
        key = run["history"].get("approach")
        if key not in out or run.get("purpose", "search") not in ("search", "trial"):
            continue
        out[key]["designs"] += 1
        gained = reward(view, run)
        if gained is not None:
            out[key]["finished"] += 1
            out[key]["wins"] += gained
    for row in out.values():
        row["win_rate"] = round(row["wins"] / row["finished"], 3) if row["finished"] else None
    return out


def pick(store: Store, view: View, settings: Dict[str, Any], rng: random.Random) -> Optional[Dict[str, Any]]:
    """The approach for one slot, or None for no approach."""
    rows = [r for r in record(store, view).values() if r["status"] == "active"]
    fresh = [r for r in rows if r["designs"] == 0]
    if fresh:
        chosen = rng.choice(fresh)
    else:
        total = sum(r["designs"] for r in rows)

        def bound(row: Dict[str, Any]) -> float:
            mean = row["wins"] / row["finished"] if row["finished"] else 0.5
            return mean + math.sqrt(2.0 * math.log(total + 1) / row["designs"])
        top = max(bound(r) for r in rows)
        chosen = rng.choice([r for r in rows if bound(r) >= top - 1e-9])
    return None if chosen["id"] == NONE else chosen


def add(store: Store, view: View, settings: Dict[str, Any], texts: List[Any], call: Any = None) -> List[str]:
    """Approaches the analyst proposes. With a full pool, the worst approach that has had its chance makes way;
    the person's own are never retired, and with nothing to retire the new one is not taken."""
    added: List[str] = []
    if settings["variation"].get("approaches") != "evolve":
        return added
    cap = int(settings["variation"].get("approach_pool") or 0)
    for item in texts[:1]:      # one at a time: each has to earn its record
        text = item.get("text") if isinstance(item, dict) else item
        if not isinstance(text, str) or not text.strip():
            continue
        text = text.strip()[:600]
        everything = store.merged_list("approaches")
        if text in {a.get("text") for a in everything}:
            continue
        if len(active(store)) >= cap:
            rows = record(store, view)
            proven = [r for r in rows.values() if r["id"] != NONE and r["status"] == "active" and r["by"] != "person"
                      and r["finished"] >= PROVEN]
            if not proven:
                continue
            worst = min(proven, key=lambda r: (r["win_rate"], r["id"]))
            store.append("approaches", {"id": worst["id"], "status": "retired",
                                        "retired_with": {"designs": worst["finished"], "win_rate": worst["win_rate"]}})
        number = len(everything) + 1
        store.append("approaches", {"id": "P%d" % number, "text": text, "by": "analyst", "status": "active", "call": call})
        added.append("P%d" % number)
    return added


def table(store: Store, view: View) -> List[Dict[str, Any]]:
    rows = record(store, view)
    return [{"approach": r["id"], "by": r["by"] or "", "status": r["status"], "designs": r["designs"],
             "finished": r["finished"], "beat reference": r["win_rate"], "text": (r["text"] or "no approach given")[:90]}
            for r in sorted(rows.values(), key=lambda r: (r["status"] != "active", -(r["win_rate"] or 0), r["id"]))
            if r["designs"] or r["status"] == "active"]
