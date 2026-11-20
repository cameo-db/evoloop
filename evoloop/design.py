"""From a request to a design that can be run.

Three steps, so that agent calls can run side by side while the records stay in one hand:

    prepare   (controller)  picks the move, gathers what the writer is shown
    propose   (worker)      an agent writes the blocks, or code does (block swap, sampled settings)
    commit    (controller)  checks the space and duplicates, picks among several proposals, records the design

Moves. `new_approach` (modes new and novel); under mode local: `structural_change`, `settings_move`,
`ablation`; under mode cross: `block_swap` (code takes whole blocks from each parent), `graft` (the one
change that gained most in the donor's history, applied to the recipient), `hybrid` (an agent writes one
design from two parents)."""
from __future__ import annotations

import json
import os
import random
from typing import Any, Dict, List, Optional, Tuple

from . import space
from .agents import AgentError, Agents
from .schedule import phase_at, fraction_used
from .store import Store, View, read_json, write_json

LOCAL_NAMES = {"edit": "structural_change", "settings": "settings_move", "ablation": "ablation"}
INSTRUCTIONS = {
    "new_approach": "Write a design from a family the search has not covered.",
    "novel": "Write a design unlike anything in the leaderboard. Build from or against the inspirations.",
    "structural_change": "Make ONE attributable change to the parent's structure. Step: %s.",
    "settings_move": "Change only values in the params blocks of the parent. Step: %s.",
    "ablation": "Remove one component from the parent and change nothing else.",
    "graft": "Apply the one change shown in `gene` to the first parent, adapted to fit, and change nothing else.",
    "hybrid": "Write one design from the two parents; say in `parts_from` which parts came from each.",
}


class Designer:
    def __init__(self, folder: str, run_dir: str, store: Store, agents: Optional[Agents], seed: int = 0):
        self.folder, self.run_dir, self.store, self.agents = folder, run_dir, store, agents
        self.base, self.adapter = os.path.join(folder, "base"), os.path.join(folder, "adapter")
        self.table = space.table(self.base)
        self.rng = random.Random(seed)
        self._text: Dict[str, str] = {}

    # --- stored designs --------------------------------------------------------------------------
    def blocks(self, candidate: str) -> Dict[str, str]:
        return read_json(os.path.join(self.run_dir, "candidates", candidate, "blocks.json")) or {}

    def task(self) -> str:
        try:
            return space.read(os.path.join(self.folder, "task.md")).strip()
        except OSError:
            return ""

    def names(self, part: str, settings: Dict[str, Any]) -> List[str]:
        return [n for n, b in self.table.items() if space.part_of(b, settings) == part]

    def keys(self, blocks: Dict[str, str], settings: Dict[str, Any]) -> Dict[str, str]:
        norm = dict(blocks)
        for name, block in self.table.items():   # settings are compared by value, not by how they are written
            if block["kind"] == "params":
                try:
                    norm[name] = repr(sorted(space.parse_params(blocks[name])[1].items()))
                except space.SpaceError:
                    pass
        return {"model": space.key_of(norm, self.names("model", settings)),
                "recipe": space.key_of(norm, self.names("recipe", settings)),
                "candidate": space.key_of(norm, list(self.table))}

    def model_text(self, view: View, model_id: str, settings: Dict[str, Any]) -> str:
        if model_id not in self._text:
            cand = (view.models.get(model_id) or {}).get("candidate")
            blocks = self.blocks(cand) if cand else {}
            self._text[model_id] = space.shingles("\n".join(blocks.get(n, "") for n in sorted(self.names("model", settings))))
        return self._text[model_id]

    def distance(self, view: View, blocks: Dict[str, str], settings: Dict[str, Any]) -> float:
        """How far a design's model is from the nearest model already tried: 0 the same code, 1 nothing shared."""
        mine = space.shingles("\n".join(blocks.get(n, "") for n in sorted(self.names("model", settings))))
        recent = sorted(view.models, key=lambda m: int(m[1:]) if m[1:].isdigit() else 0)[-150:]
        nearest = max((space.similarity(mine, self.model_text(view, m, settings)) for m in recent), default=0.0)
        return round(1.0 - nearest, 4)

    # --- prepare ---------------------------------------------------------------------------------
    def prepare(self, request: Dict[str, Any], view: View, settings: Dict[str, Any]) -> Dict[str, Any]:
        allowed = space.open_blocks(self.table, settings)
        structure = [n for n, k in allowed.items() if k == "structure"]
        params = [n for n, k in allowed.items() if k == "params"]
        request = dict(request)
        mode = request["mode"]
        parents = [p for p in request.get("parents") or [] if p]
        leader = view.best()
        source = self.blocks(parents[0]) if parents else (self.blocks(leader["id"]) if leader else {})
        source = space.full(self.table, source)
        request.update(allowed=allowed, source=source, phase=phase_at(settings, fraction_used(view, settings))["index"])
        if mode in ("new", "novel", "cross") and not structure:
            # No structure is open (a search over settings alone, or the space was narrowed during the run):
            # every slot is a settings move, on the first parent or else on the leader.
            mode = request["mode"] = "local"
            if not parents and leader:
                parents = [leader["id"]]
            parents = parents[:1]
            request.update(parents=parents, lineage=view.cands[parents[0]]["lineage"] if parents else None,
                           inspirations=None, step=request.get("step") or "normal")
        cross = self.cross_kind(request, view, settings, parents) if mode == "cross" else None
        if mode == "cross" and cross is None:
            # None of the crossover kinds the person listed is possible for this pair: the slot becomes a local
            # move on the first parent, and the run's record says why.
            mode = request["mode"] = "local"
            parents = parents[:1]
            request.update(parents=parents, lineage=view.cands[parents[0]]["lineage"], step="normal",
                           why="%s; no listed kind of crossover was possible, so a local move" % request.get("why"))
        if mode == "local":
            mix = dict(settings["schedule"]["local_mix"])
            feasible = {"edit": bool(structure), "ablation": bool(structure), "settings": bool(params)}
            counts = {m: 0 for m in mix}
            for run in view.search_runs():
                key = {v: k for k, v in LOCAL_NAMES.items()}.get(run["history"].get("move"))
                if key in counts:
                    counts[key] += 1
            options = [m for m in mix if feasible.get(m) and float(mix[m]) > 0] or [m for m in feasible if feasible[m]]
            if not options:
                return dict(request, move=None, refuse="no block is open in this search")
            done = sum(counts.values())
            pick = max(options, key=lambda m: float(mix.get(m, 0)) * (done + 1) - counts[m])
            feasible_all = [m for m in feasible if feasible[m]]
            if request.get("force_kind") in feasible_all:
                pick = request["force_kind"]   # the strategist ordered this kind of move
            request["move"] = LOCAL_NAMES[pick]
        elif mode == "cross":
            request["move"] = cross
            if request["move"] == "graft":
                request["gene"] = self.gene(view, parents[1])
        else:
            request["move"] = "new_approach"
        by_code = request["move"] == "block_swap" or (
            request["move"] == "settings_move" and settings["variation"]["settings_by"] == "sampler")
        request["by_code"] = by_code
        if not by_code:
            request["context"] = self.context(request, view, settings, parents)
        return request

    def cross_kind(self, request: Dict[str, Any], view: View, settings: Dict[str, Any], parents: List[str]) -> Optional[str]:
        kinds = [k for k in settings["crossover"]["kinds"]]
        a, b = (space.full(self.table, self.blocks(p)) for p in parents[:2])
        differing = [n for n in request["allowed"] if a.get(n) != b.get(n)]
        feasible = {"block_swap": len(differing) >= 2, "graft": self.gene(view, parents[1]) is not None, "hybrid": True}
        options = [k for k in kinds if feasible[k]]
        if not options:
            return None   # only the kinds the person listed are used
        if request.get("force_kind") in options:
            return request["force_kind"]   # the strategist ordered this kind
        counts = {k: sum(1 for r in view.search_runs() if r["history"].get("move") == k) for k in options}
        return min(options, key=lambda k: (counts[k], options.index(k)))

    def gene(self, view: View, donor: str) -> Optional[Dict[str, Any]]:
        """The change that gained most in the donor's lineage: a recorded, measured difference."""
        lineage = view.cands[donor]["lineage"]
        best: Optional[Tuple[float, str, str]] = None
        for run in view.runs.values():
            parent = run["history"].get("parent")
            if run["history"].get("lineage") != lineage or parent not in view.runs \
                    or run.get("purpose", "search") not in ("search", "trial"):   # a re-check is not a change
                continue
            after, before = view.own_value(run), view.own_value(view.runs[parent])
            if after is None or before is None or after - before <= view.noise:
                continue
            if best is None or after - before > best[0]:
                best = (after - before, view.runs[parent].get("candidate"), run.get("candidate"))
        if best is None:
            return None
        return {"from_candidate": best[2], "gain_in_noise_floors": round(best[0] / view.noise, 2),
                "diff": space.diff(self.blocks(best[1]), self.blocks(best[2]))}

    def summary(self, view: View, candidate: str) -> Dict[str, Any]:
        run = view.run_of(candidate)
        perf = run.get("performance") or {}
        return {"candidate": candidate, "lineage": run["history"].get("lineage"), "family": view.cands[candidate]["family"],
                "score": view.display(view.cands[candidate]["value"]), "move": run["history"].get("move"),
                "change": run["history"].get("change_summary"), "valid": perf.get("valid")}

    def context(self, request: Dict[str, Any], view: View, settings: Dict[str, Any], parents: List[str]) -> Dict[str, Any]:
        level = settings["harness"]["level"]
        allowed, move = request["allowed"], request["move"]
        shown = lambda blocks: {n: blocks.get(n, self.table[n]["content"]) for n in allowed}   # noqa: E731
        instruction = INSTRUCTIONS["novel" if request["mode"] == "novel" else move]
        if "%s" in instruction:
            instruction = instruction % request.get("step", "normal")
        ranked = view.scored()
        families: Dict[str, Dict[str, Any]] = {}
        for cand in ranked:
            row = families.setdefault(str(cand["family"]), {"family": cand["family"], "designs": 0,
                                                            "best": view.display(cand["value"])})
            row["designs"] += 1
        recent = []
        for run in sorted(view.ended(), key=lambda r: r["t"] if "t" in r else 0)[-(4 if level == "minimal" else 10):]:
            perf = run["performance"]
            recent.append({"run": run["id"], "candidate": run.get("candidate"), "move": run["history"].get("move"),
                           "change": run["history"].get("change_summary"), "status": perf.get("status"),
                           "score": perf.get("score") if view.counts(run) else None, "reason": perf.get("reason")})
        context: Dict[str, Any] = {
            "task": self.task(),
            "objective": {"goal": settings["objective"]["goal"], "metric": settings["objective"]["metric"],
                          "direction": settings["objective"]["direction"], "noise_floor": view.noise,
                          "constraints": settings["objective"]["constraints"]},
            "request": {"mode": request["mode"], "move": move, "instruction": instruction,
                        "step": request.get("step"), "why_this_slot": request.get("why"),
                        "number_of_proposals": int(settings["variation"]["proposals_per_slot"])
                        if request.get("purpose") != "trial" else 1},
            "blocks_you_may_change": {n: {"kind": k, "role": self.table[n]["role"]} for n, k in allowed.items()},
            "must_keep": list(settings["space"]["must_keep"]) + (
                ["Keep the overall shape of the model as in the baseline: change parts within it, do not replace it "
                 "with a different kind of model."] if settings["space"]["preset"] == "template" else []),
            "forbidden": settings["space"]["forbidden"],
            "being_written_now": [{"mode": d.get("mode"), "lineage": d.get("lineage"), "parents": d.get("parents")}
                                  for d in settings.get("_designing") or []],
            "parents": [dict(self.summary(view, p), blocks=shown(self.blocks(p))) for p in parents],
            "starting_blocks": shown(request["source"]) if not parents else None,
            "leaderboard": [self.summary(view, c["id"]) for c in ranked[:(5 if level == "minimal" else 12)]],
            "families": sorted(families.values(), key=lambda f: -f["designs"])[:40],
            "recent": recent,
        }
        if request.get("inspirations"):
            context["inspirations"] = [dict(self.summary(view, c), blocks=shown(self.blocks(c)))
                                       for c in request["inspirations"]]
        if request.get("thin_cells"):
            context["thin_cells"] = request["thin_cells"]
        if request.get("gene"):
            context["gene"] = request["gene"]
        if level != "minimal":
            context["lessons"] = [{"id": l["id"], "statement": l["statement"], "status": l["status"]}
                                  for l in self.store.read("knowledge")][-20:]
        return context

    # --- propose ---------------------------------------------------------------------------------
    def propose(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Runs in a worker. Returns the request with `proposals`, or with `refuse`."""
        if request.get("refuse"):
            return request
        try:
            if request["move"] == "block_swap":
                request["proposals"] = [self.block_swap(request)]
            elif request["by_code"]:
                request["proposals"] = [self.sampled(request)]
            else:
                output = self.agents.call("writer", request["context"], about=request.get("move"))
                request["call"] = output.get("_call")
                request["proposals"] = [p for p in output.get("proposals") or [] if isinstance(p, dict)]
        except AgentError as exc:
            request["refuse"] = str(exc)
            request["agents_unavailable"] = type(exc).__name__ == "AgentsUnavailable"
        request.pop("context", None)
        return request

    def block_swap(self, request: Dict[str, Any]) -> Dict[str, Any]:
        first, second = (space.full(self.table, self.blocks(p)) for p in request["parents"][:2])
        differing = [n for n in request["allowed"] if first.get(n) != second.get(n)]
        by_role: Dict[str, List[str]] = {}
        for name in differing:
            by_role.setdefault(self.table[name]["role"], []).append(name)
        roles = sorted(by_role)
        if len(roles) >= 2:    # whole roles change hands: the trunk of one with the heads of the other
            taken = self.rng.sample(roles, max(1, len(roles) // 2))
            names = [n for r in taken for n in by_role[r]]
        else:
            names = self.rng.sample(differing, max(1, len(differing) // 2))
        return {"name": "swap_%s_%s" % tuple(request["parents"][:2]), "family": None,
                "hypothesis": "Blocks %s of %s work with the rest of %s." % (", ".join(names), request["parents"][1],
                                                                             request["parents"][0]),
                "predicted_effect": "not stated (written by code)", "change_summary": "blocks %s taken from %s" % (
                    ", ".join(names), request["parents"][1]),
                "parts_from": {request["parents"][1]: names}, "blocks": {n: second[n] for n in names}}

    def sampled(self, request: Dict[str, Any]) -> Dict[str, Any]:
        spread = {"small": 1.25, "normal": 1.6, "bold": 2.5}.get(request.get("step") or "normal", 1.6)
        blocks, moved = {}, []
        names = [n for n, k in request["allowed"].items() if k == "params"]
        for name in self.rng.sample(names, min(len(names), 1)):
            var, values = space.parse_params(request["source"][name])
            numeric = [k for k, v in values.items() if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0]
            for key in self.rng.sample(numeric, min(len(numeric), 1 + (self.rng.random() < 0.4))):
                factor = spread ** self.rng.uniform(-1, 1)
                values[key] = max(1, int(round(values[key] * factor))) if isinstance(values[key], int) \
                    else float("%.4g" % (values[key] * factor))
                moved.append("%s.%s=%s" % (name, key, values[key]))
            blocks[name] = space.render_params(var, values)
        return {"name": "sampled", "family": None, "hypothesis": "A nearby setting scores better.",
                "predicted_effect": "not stated (drawn by code)", "change_summary": "; ".join(moved), "blocks": blocks}

    # --- commit ----------------------------------------------------------------------------------
    def commit(self, request: Dict[str, Any], view: View, settings: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        """The run record of the chosen proposal, or (None, why nothing can be run)."""
        if request.get("refuse"):
            return None, request["refuse"]
        existing = {run.get("key"): run.get("candidate") for run in view.runs.values()}
        novelty = float(settings["schedule"]["novelty"])
        judged, reasons = [], []
        for proposal in request.get("proposals") or []:
            changed = {k: v for k, v in (proposal.get("blocks") or {}).items() if isinstance(v, str)}
            fault = space.check(self.table, changed, request["allowed"], settings)
            blocks = dict(request["source"], **changed)
            if fault is None and request.get("purpose") != "recheck" and self.keys(blocks, settings)["candidate"] in existing:
                fault = "an exact copy of %s" % existing[self.keys(blocks, settings)["candidate"]]
            if fault is None and not changed:
                fault = "no block was returned"
            if fault:
                reasons.append("%s: %s" % (proposal.get("name") or "proposal", fault))
                continue
            gain = proposal.get("expected_gain") if isinstance(proposal.get("expected_gain"), dict) else {}
            forecast = None
            if isinstance(gain.get("gain"), (int, float)) and isinstance(gain.get("probability_better"), (int, float)):
                forecast = {"gain": float(gain["gain"]), "probability_better": min(1.0, max(0.0, float(gain["probability_better"])))}
            distance = self.distance(view, blocks, settings)
            # The choice among several proposals: the forecast, plus up to three noise floors for a design
            # far from everything tried, scaled by the novelty dial (doubled in a novel slot).
            weight = novelty * (2.0 if request["mode"] == "novel" else 1.0)
            worth = (forecast["gain"] * forecast["probability_better"] if forecast else 0.0) + 3.0 * weight * distance
            judged.append((worth, proposal, blocks, forecast, distance))
        if not judged:
            return None, "; ".join(reasons) or "the writer returned no proposal"
        judged.sort(key=lambda item: -item[0])
        worth, proposal, blocks, forecast, distance = judged[0]
        keys = self.keys(blocks, settings)
        parents = [p for p in request.get("parents") or [] if p]
        mode, move = request["mode"], request["move"]
        models = {m.get("key"): m["id"] for m in view.models.values()}
        recipes = {r.get("key"): r["id"] for r in view.recipes.values()}
        candidate = "C%d" % (len({r.get("candidate") for r in view.runs.values()}) + 1)
        parent_model = view.cands[parents[0]]["model"] if parents else None
        family = proposal.get("family") if isinstance(proposal.get("family"), str) and proposal.get("family") else (
            view.cands[parents[0]]["family"] if parents else "unlabelled")
        for field in ("name", "hypothesis", "predicted_effect", "change_summary"):   # free text, whatever the writer sent
            if proposal.get(field) is not None and not isinstance(proposal[field], str):
                proposal[field] = str(proposal[field])[:400]
        if keys["model"] not in models:
            model = "M%d" % (len(view.models) + 1)
            record = self.store.append("models", {"id": model, "key": keys["model"], "name": proposal.get("name") or model,
                                                  "family": family, "parent": parent_model, "candidate": candidate})
            view.models[model] = record
        else:
            model = models[keys["model"]]
        if keys["recipe"] not in recipes:
            recipe = "T%d" % (len(view.recipes) + 1)
            view.recipes[recipe] = self.store.append("recipes", {"id": recipe, "key": keys["recipe"], "candidate": candidate})
        else:
            recipe = recipes[keys["recipe"]]
        lineages = view.lineages()
        lineage_parents: List[str] = []
        founds = mode in ("new", "novel") or move in ("block_swap", "hybrid") or not request.get("lineage")
        if founds:
            lineage = "L%d" % (len(lineages) + 1)
            lineage_parents = sorted({view.cands[p]["lineage"] for p in parents if view.cands[p]["lineage"]})
        else:
            lineage = request["lineage"]
        os.makedirs(os.path.join(self.run_dir, "candidates", candidate), exist_ok=True)
        write_json(os.path.join(self.run_dir, "candidates", candidate, "blocks.json"), blocks)
        history = {"lineage": lineage, "lineage_parents": lineage_parents, "mode": mode, "move": move,
                   "phase": request.get("phase"), "island": request.get("island"), "migrant": bool(request.get("migrant")),
                   "parent": view.run_of(parents[0])["id"] if parents else None,
                   "second_parent": {"run": view.run_of(parents[1])["id"]} if len(parents) > 1 else None,
                   "hypothesis": proposal.get("hypothesis"), "predicted_effect": proposal.get("predicted_effect"),
                   "change_summary": proposal.get("change_summary"), "parts_from": proposal.get("parts_from"),
                   "forecast": forecast, "why_this_slot": request.get("why"), "step": request.get("step"),
                   "forced_by": request.get("forced_by"),
                   "call": request.get("call"), "distance": distance, "proposals_weighed": len(request.get("proposals") or []),
                   "not_chosen": [{"name": p.get("name"), "worth": round(w, 3)} for w, p, _, _, _ in judged[1:]] + reasons}
        run = {"id": "R%d" % (len(view.runs) + 1), "candidate": candidate, "key": keys["candidate"], "model": model,
               "recipe": recipe, "settings": space.all_params(self.table, blocks), "seed": int(settings["evaluation"]["seed"]),
               "purpose": request.get("purpose") or "search", "period": view.period, "charge": 1.0, "history": history,
               "performance": {"status": "designed"}}
        return run, ""

    def baseline(self, view: View, settings: Dict[str, Any]) -> Dict[str, Any]:
        """The base code as it stands, as the first design."""
        blocks = space.full(self.table, {})
        request = {"mode": "new", "move": "baseline", "parents": [], "allowed": space.open_blocks(self.table, settings),
                   "source": blocks, "purpose": "baseline", "why": "the baseline",
                   "proposals": [{"name": "baseline", "family": "baseline", "hypothesis": "The starting point.",
                                  "change_summary": "the base code unchanged", "blocks": dict(blocks)}]}
        run, why = self.commit(dict(request, allowed={n: b["kind"] for n, b in self.table.items()}), view, settings)
        if run is None:
            raise RuntimeError("the baseline cannot be recorded: %s" % why)
        run["history"]["move"] = "baseline"
        return run

    def again(self, view: View, candidate: str, purpose: str, seed: int, settings: Dict[str, Any],
              period: Optional[int] = None) -> Dict[str, Any]:
        """A further run of an existing design: another seed for a re-check, or the same design under a new
        setting of the run length (a reference for the new period)."""
        first = view.run_of(candidate)
        run = {k: first[k] for k in ("candidate", "key", "model", "recipe", "settings")}
        run.update(id="R%d" % (len(view.runs) + 1), seed=seed, purpose=purpose, charge=1.0,
                   period=view.period if period is None else period,
                   # Not a move of the search: it has no mode, so it counts toward no share, no retirement, no step size.
                   history=dict(first["history"], parent=first["id"], second_parent=None, move=purpose, mode=None,
                                forecast=None, why_this_slot=purpose, call=None, not_chosen=[], coordinator=None),
                   performance={"status": "designed"})
        return run
