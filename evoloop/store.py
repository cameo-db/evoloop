"""The shared stores of a run, and the view computed from them.

Every part of the loop communicates through these files and through nothing else: no role talks to
another role, and no evolution strategy keeps state of its own. A run directory holds one append-only
JSON-lines file per stream:

    models     each architecture (the open model blocks), in the shape of a CAMEO `models[]` entry
    recipes    each training recipe (the open recipe blocks), a CAMEO `training{}` entry
    runs       each training run; a later record with the same id updates the earlier one
    ledger     the steering ledger: the person's notes and every change of a setting, never deleted
    calls      every agent call: what it was shown, what it said, what it cost
    knowledge  lessons the analyst wrote, with their evidence
    questions  things a role wants the person to decide
    reviews    the assessor's reviews of each role

Because the strategies read only the view, a run can change strategy midway: the new one computes its
population from the same results."""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Callable, Dict, Iterable, List, Optional

STREAMS = ("models", "recipes", "runs", "ledger", "calls", "knowledge", "questions", "reviews")
SCORED = ("done", "stopped_early")
ENDED = ("done", "stopped_early", "failed", "invalid", "not_run")
SEARCH_PURPOSES = ("search", "trial")   # runs that take part in selection as designs of their own


class Store:
    def __init__(self, run_dir: str):
        self.dir = run_dir
        os.makedirs(run_dir, exist_ok=True)
        self._lock = threading.Lock()

    def path(self, stream: str) -> str:
        return os.path.join(self.dir, stream + ".jsonl")

    def append(self, stream: str, record: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(record)
        record.setdefault("t", round(time.time(), 3))
        line = json.dumps(record, sort_keys=True, default=str) + "\n"
        with self._lock:
            with open(self.path(stream), "a", encoding="utf-8") as handle:
                handle.write(line)
        return record

    def read(self, stream: str) -> List[Dict[str, Any]]:
        try:
            with open(self.path(stream), "r", encoding="utf-8") as handle:
                lines = handle.readlines()
        except OSError:
            return []
        out = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue   # a line cut short by a crash; the record before it stands
        return out

    def merged(self, stream: str) -> Dict[str, Dict[str, Any]]:
        """Records by id, a later record laid over an earlier one with the same id."""
        out: Dict[str, Dict[str, Any]] = {}
        for record in self.read(stream):
            rid = record.get("id")
            if rid is None:
                continue
            if rid in out:
                merge(out[rid], record)
            else:
                out[rid] = record
        return out

    def merged_list(self, stream: str) -> List[Dict[str, Any]]:
        """The merged records in the order they were first written."""
        return list(self.merged(stream).values())


def merge(into: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(into.get(key), dict):
            merge(into[key], value)
        else:
            into[key] = value
    return into


def read_json(path: str, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


def write_json(path: str, value: Any) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=1, sort_keys=True, default=str)
    os.replace(tmp, path)


class View:
    """The results as every strategy sees them. Scores are turned so that higher is better.

    A *candidate* is one design: a model, a recipe and its settings. It may have several runs (seeds).
    Its score is the mean over its scored runs of the current period. A *period* begins whenever the
    person changes something that alters what a score means (the length of a run, the early-stopping
    rule): runs of earlier periods stay in the record and feed the agents' lessons, and take no part
    in selection."""

    def __init__(self, runs: Dict[str, Dict[str, Any]], models: Dict[str, Dict[str, Any]],
                 recipes: Dict[str, Dict[str, Any]], direction: str = "maximize", noise: float = 0.0,
                 period: int = 0):
        self.runs, self.models, self.recipes = runs, models, recipes
        self.sign = -1.0 if direction == "minimize" else 1.0
        self.noise = max(float(noise or 0.0), 1e-12)
        self.period = period
        self.cands: Dict[str, Dict[str, Any]] = {}
        for run in sorted(runs.values(), key=order):
            key = run.get("candidate") or run["id"]
            cand = self.cands.setdefault(key, {"id": key, "runs": [], "values": [], "first": run})
            cand["runs"].append(run["id"])
            if self.counts(run):
                cand["values"].append(self.sign * float(run["performance"]["score"]))
        for cand in self.cands.values():
            cand["value"] = sum(cand["values"]) / len(cand["values"]) if cand["values"] else None
            first = cand["first"]
            cand.update(lineage=first["history"].get("lineage"), model=first.get("model"), recipe=first.get("recipe"),
                        family=(models.get(first.get("model")) or {}).get("family"),
                        island=first["history"].get("island"), order=order(first))

    @classmethod
    def load(cls, store: Store, settings: Dict[str, Any]) -> "View":
        return cls(store.merged("runs"), store.merged("models"), store.merged("recipes"),
                   direction=settings["objective"]["direction"], noise=settings["evaluation"]["noise"] or 0.0,
                   period=int(settings.get("_period", 0)))

    # --- single runs -----------------------------------------------------------------------------
    def counts(self, run: Dict[str, Any]) -> bool:
        perf = run.get("performance") or {}
        return perf.get("status") in SCORED and isinstance(perf.get("score"), (int, float)) \
            and int(run.get("period", 0)) == self.period

    def value(self, run_id: str) -> Optional[float]:
        """The score of the candidate a run belongs to, higher better, or None."""
        run = self.runs.get(run_id)
        if run is None:
            return None
        return self.cands[run.get("candidate") or run_id]["value"]

    def own_value(self, run: Dict[str, Any]) -> Optional[float]:
        return self.sign * float(run["performance"]["score"]) if self.counts(run) else None

    def display(self, value: Optional[float]) -> Optional[float]:
        return None if value is None else self.sign * value

    # --- collections -----------------------------------------------------------------------------
    def scored(self) -> List[Dict[str, Any]]:
        """Candidates with a score in this period, best first."""
        return sorted((c for c in self.cands.values() if c["value"] is not None),
                      key=lambda c: (-c["value"], c["order"]))

    def best(self) -> Optional[Dict[str, Any]]:
        ranked = self.scored()
        return ranked[0] if ranked else None

    def ended(self) -> List[Dict[str, Any]]:
        return [r for r in self.runs.values() if (r.get("performance") or {}).get("status") in ENDED]

    def in_flight(self) -> List[Dict[str, Any]]:
        return [r for r in self.runs.values() if (r.get("performance") or {}).get("status") not in ENDED]

    def charged(self) -> float:
        """Evaluations spent: every run that ended with a score, and failures past the uncounted allowance
        are added by the controller."""
        return float(sum(float(r.get("charge", 1.0)) for r in self.runs.values()
                         if (r.get("performance") or {}).get("status") in SCORED))

    def search_runs(self) -> List[Dict[str, Any]]:
        return [r for r in sorted(self.runs.values(), key=order) if r.get("purpose", "search") in SEARCH_PURPOSES]

    def lineages(self) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for run in sorted(self.runs.values(), key=order):
            lid = run["history"].get("lineage")
            if lid is None:
                continue
            lin = out.setdefault(lid, {"id": lid, "runs": [], "founder": run["id"], "founded_by": run["history"].get("mode"),
                                       "family": (self.models.get(run.get("model")) or {}).get("family"),
                                       "parents": run["history"].get("lineage_parents") or [],
                                       "island": run["history"].get("island")})
            lin["runs"].append(run["id"])
        for lin in out.values():
            keys = []
            for rid in lin["runs"]:
                key = self.runs[rid].get("candidate") or rid
                if key not in keys:
                    keys.append(key)
            cands = [self.cands[k] for k in keys]
            scored = sorted((c for c in cands if c["value"] is not None), key=lambda c: (-c["value"], c["order"]))
            lin.update(candidates=keys, scored=[c["id"] for c in scored], best=scored[0]["value"] if scored else None,
                       best_candidate=scored[0]["id"] if scored else None,
                       flying=sum(1 for rid in lin["runs"] if self.runs[rid]["performance"].get("status") not in ENDED))
        return out

    def subset(self, keep: Callable[[Dict[str, Any]], bool]) -> "View":
        runs = {rid: run for rid, run in self.runs.items() if keep(run)}
        return View(runs, self.models, self.recipes, "maximize" if self.sign > 0 else "minimize", self.noise, self.period)

    def run_of(self, candidate_id: str) -> Dict[str, Any]:
        """The first run of a candidate: where its blocks and history are kept."""
        return self.cands[candidate_id]["first"]

    def descendants(self, candidate_id: str) -> int:
        runs = set(self.cands[candidate_id]["runs"])
        return sum(1 for r in self.runs.values()
                   if r["history"].get("parent") in runs or (r["history"].get("second_parent") or {}).get("run") in runs)


def order(run: Dict[str, Any]) -> Any:
    rid = run.get("id", "")
    digits = "".join(ch for ch in rid if ch.isdigit())
    return (int(digits) if digits else 0, rid)


def pearson(a: Iterable[float], b: Iterable[float]) -> Optional[float]:
    a, b = list(a), list(b)
    n = min(len(a), len(b))
    if n < 3:
        return None
    a, b = a[:n], b[:n]
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va <= 0 or vb <= 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (va * vb) ** 0.5
