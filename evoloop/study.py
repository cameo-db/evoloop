"""The run as a study file, in the CAMEO entry format (version 0.4).

Four parts: `experiment`, `models`, `training`, `runs`. The run's own stores are already in that shape (a
model is the open model blocks, a recipe the open recipe blocks, a run names one of each with its
settings and seed), so this is an export, not a translation. What the run does not know is written as
"not_reported"; nothing is filled in. Steering, modes and agent spend have no field in the format: they
stay in the ledger beside the file and are summarised under `experiment.search.method`."""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from . import space
from .agents import spend
from .store import ENDED, View, write_json

NOT = "not_reported"
FORMAT_VERSION = "0.4"
MOVES = {"new_approach": "new_approach", "structural_change": "structural_change", "settings_move": "settings_move",
         "baseline": "baseline"}   # the others (ablation, block_swap, graft, hybrid, recheck, reference) are this loop's own words


def or_not(value: Any) -> Any:
    return NOT if value in (None, "", [], {}) else value


def build(controller: Any, view: View) -> Dict[str, Any]:
    s, designer, store = controller.settings, controller.designer, controller.store
    base = os.path.join(controller.folder, "base")
    best = view.best()
    lineages = view.lineages()
    captured = next((r["captured"] for r in view.runs.values() if isinstance(r.get("captured"), dict)), {})
    ledger = store.merged_list("ledger")
    steered = [e for e in ledger if e.get("kind") in ("set", "note") and e.get("status") in ("applied", "active")
               and e.get("at_evaluations", 0) > 0]
    method = "evoloop: %s strategy%s, %s harness, run type %s, search space %s. %d steering entries during the run%s." % (
        s["strategy"]["mechanism"], " on %d islands" % s["strategy"]["islands"] if int(s["strategy"]["islands"]) > 1 else "",
        s["harness"]["level"], s["run"]["type"], s["space"]["preset"], len(steered),
        " (a steered run: see ledger.jsonl)" if steered else "")
    data = s["data"]
    experiment = {
        "id": "%s-%s" % (os.path.basename(controller.folder), controller.name), "title": or_not(s["objective"]["goal"]),
        "summary": or_not(s["objective"]["goal"]), "license": s["license"], "created": time.strftime("%Y-%m-%d"),
        "depositor": {k: or_not(v) for k, v in s["depositor"].items()},
        "run_by": {"kind": "agent", "tool": "evoloop", "model": or_not(s["agents"].get("default_model") or s["agents"]["backend"])},
        "objective": {"goal": or_not(s["objective"]["goal"]),
                      "optimize": {"metric": s["objective"]["metric"], "split": "valid", "direction": s["objective"]["direction"]}},
        "data": {"name": or_not(data["name"]), "accession": or_not(data["accession"]), "input": or_not(data["input"]),
                 "output": or_not(data["output"]), "examples": or_not(data["examples"]),
                 "preprocessing": or_not(data["preprocessing"]), "splits": or_not(data["splits"])},
        "evaluation": {"primary_metric": s["objective"]["metric"], "direction": s["objective"]["direction"],
                       "selection_split": "valid", "test_policy": "held out; never shown to an agent or used to choose"
                       if s["evaluation"]["test_set"] == "held_out" else NOT, "noise_floor": or_not(s["evaluation"]["noise"]),
                       "metrics": dict(s["evaluation"].get("metrics") or {}) or NOT},
        "environment": captured.get("environment") or NOT,
        "search": {"method": method, "budget": {"evaluations": s["budget"]["evaluations"], "spent": controller.spent(view),
                                                 "agent_dollars": round(sum(r["dollars"] for r in spend(store).values()), 4)},
                   "lineages": [{"id": l["id"], "name": l["id"], "family": or_not(l["family"]), "parents": l["parents"]}
                                for l in lineages.values()]},
        "conclusions": {"best_run": view.run_of(best["id"])["id"] if best else NOT,
                        "findings": [l["statement"] for l in store.read("knowledge") if l.get("status") == "supported"],
                        "open_questions": [q["question"] for q in store.read("questions") if q.get("status") == "open"]},
    }
    models = []
    for model in view.models.values():
        blocks = designer.blocks(model.get("candidate")) if model.get("candidate") else {}
        speed = next(((r["performance"].get("inference_speed")) for r in view.runs.values()
                      if r.get("model") == model["id"] and r["performance"].get("inference_speed")), None)
        models.append({"id": model["id"], "name": model.get("name") or model["id"], "family": or_not(model.get("family")),
                       "parent": model.get("parent"), "inputs": NOT, "outputs": NOT,
                       "code": space.spliced_text(base, designer.table, blocks, "model", s) if blocks else NOT,
                       "inference_speed": speed if isinstance(speed, dict) else ({"examples_per_s": speed} if speed else NOT)})
    training = {}
    for recipe in view.recipes.values():
        blocks = designer.blocks(recipe.get("candidate")) if recipe.get("candidate") else {}
        resolved = next((r["captured"].get("training") for r in view.runs.values()
                         if r.get("recipe") == recipe["id"] and isinstance(r.get("captured"), dict)
                         and r["captured"].get("training")), None) or {}
        training[recipe["id"]] = {
            "settings": space.all_params(designer.table, blocks), "loss": resolved.get("loss", NOT),
            "schedules": resolved.get("schedules", NOT), "early_stopping": resolved.get("early_stopping", NOT),
            "checkpoint": resolved.get("checkpoint", NOT), "shuffle": resolved.get("shuffle", NOT),
            "augmentation": resolved.get("augmentation", NOT), "init": resolved.get("init", "random"),
            "code": {"entry_point": NOT, "command": s["run_command"],
                     "script": space.spliced_text(base, designer.table, blocks, "recipe", s) or NOT if blocks else NOT,
                     "files": adapter_files(controller.folder)}}
    runs = []
    for run in sorted(view.runs.values(), key=lambda r: int(r["id"][1:])):
        perf, h = run["performance"], run["history"]
        status = perf.get("status") if perf.get("status") in ENDED else "not_run"
        recipe_settings = training.get(run.get("recipe"), {}).get("settings") or {}
        entry: Dict[str, Any] = {
            "id": run["id"], "model": run.get("model") or NOT, "training": run.get("recipe") or NOT, "seed": run.get("seed"),
            "kind": "finetune" if run.get("continue_from") else "train",
            "settings": {k: v for k, v in (run.get("settings") or {}).items() if recipe_settings.get(k) != v},
            "history": {"lineage": h.get("lineage"), "parent": h.get("parent"), "move": MOVES.get(h.get("move"), h.get("move")),
                        "hypothesis": or_not(h.get("hypothesis")), "predicted_effect": or_not(h.get("predicted_effect"))},
            "performance": {"status": status}}
        if h.get("second_parent"):
            entry["history"]["second_parent"] = h["second_parent"]
        if run.get("allowance") is not None:
            entry["settings"]["allowance"] = run["allowance"]
        p = entry["performance"]
        if status in ("done", "stopped_early"):
            p.update(score=perf.get("score"), valid=perf.get("valid") or NOT, test=perf.get("test") or NOT,
                     parameters=or_not(perf.get("parameters")), training_minutes=or_not(perf.get("training_minutes")),
                     best_epoch=or_not(perf.get("best_epoch")), epochs_run=or_not(perf.get("epochs_run")))
        elif perf.get("reason"):
            p["reason"] = str(perf["reason"])[:400]
        if run.get("period"):
            p["period"] = run["period"]   # this loop's own field: which setting of the run length it was fitted under
        runs.append(entry)
    return {"format_version": FORMAT_VERSION, "experiment": experiment, "models": models, "training": training, "runs": runs}


def adapter_files(folder: str) -> Dict[str, str]:
    out = {}
    adapter = os.path.join(folder, "adapter")
    if os.path.isdir(adapter):
        for rel in space.files(adapter):
            if rel.endswith(space.TEXT):
                try:
                    out["adapter/" + rel] = space.read(os.path.join(adapter, rel))
                except (OSError, UnicodeDecodeError):
                    continue
    return out or NOT


def star(study: Dict[str, Any]) -> str:
    """The star this file is on course for, by the format's own rules, and what stands in the way of the next."""
    exp = study["experiment"]
    has_data = exp["data"]["accession"] != NOT
    has_code = bool(study["models"]) and all(m["code"] != NOT for m in study["models"])
    done = [r for r in study["runs"] if r["performance"]["status"] in ("done", "stopped_early")]
    if not has_data or not has_code:
        return "No star: " + ("data.accession is empty" if not has_data else "a model has no code")
    gaps: List[str] = []
    if exp["environment"] == NOT:
        gaps.append("the environment (package versions, devices) is not captured by the adapter")
    if any(m["inference_speed"] == NOT for m in study["models"]):
        gaps.append("inference speed is not measured")
    if any(t["loss"] == NOT for t in study["training"].values()):
        gaps.append("the recipe's loss, schedule and stopping rule are not captured from the objects the script built")
    if any(r["performance"].get("parameters") == NOT for r in done):
        gaps.append("parameter counts are missing")
    if exp["data"]["splits"] == NOT or exp["data"]["preprocessing"] == NOT:
        gaps.append("data.splits or data.preprocessing is empty")
    if not gaps:
        return "On course for Gold."
    return "On course for Silver. For Gold: " + "; ".join(gaps) + "."


def write(controller: Any, view: View) -> str:
    path = os.path.join(controller.run_dir, "study.json")
    write_json(path, build(controller, view))
    return path


# --- reading a study file: designs from another search, on this data or on other data -----------------------------

def load(path: str) -> Dict[str, Any]:
    """A study file (CAMEO format), from a path. Raises ValueError when it is not one."""
    with open(path, "r", encoding="utf-8") as handle:
        study = json.load(handle)
    if not isinstance(study, dict) or not isinstance(study.get("models"), list) or not isinstance(study.get("runs"), list):
        raise ValueError("%s is not a study file: it needs `models` and `runs`" % path)
    return study


def ranked(study: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The models of a study that have a finished run, best first by the study's own metric and direction."""
    experiment = study.get("experiment") or {}
    evaluation = experiment.get("evaluation") or {}
    lower = str(evaluation.get("direction") or "maximize").startswith("min")
    training = study.get("training") or {}
    best: Dict[str, Dict[str, Any]] = {}
    for run in study["runs"]:
        perf = run.get("performance") or {}
        score = perf.get("score")
        if perf.get("status") != "done" or not isinstance(score, (int, float)):
            continue
        held = best.get(run.get("model"))
        if held is None or (score < held["score"] if lower else score > held["score"]):
            best[run.get("model")] = {"score": score, "run": run.get("id"), "training": run.get("training"),
                                      "parameters": perf.get("parameters")}
    out = []
    for model in study["models"]:
        if model.get("id") in best and isinstance(model.get("code"), str):
            mine = best[model["id"]]
            script = ((training.get(mine["training"]) or {}).get("code") or {}).get("script")
            out.append({"model": model["id"], "name": model.get("name") or model["id"], "family": model.get("family"),
                        "code": model["code"], "script": script if isinstance(script, str) else None,
                        "score": mine["score"], "run": mine["run"], "parameters": mine["parameters"]})
    return sorted(out, key=lambda m: m["score"], reverse=not lower)


def about(study: Dict[str, Any]) -> Dict[str, Any]:
    """Where a study's designs come from: its id, data, metric and what it concluded."""
    experiment = study.get("experiment") or {}
    evaluation = experiment.get("evaluation") or {}
    data = experiment.get("data") or {}
    return {"study": experiment.get("id"), "title": experiment.get("title"), "data": data.get("name"),
            "metric": evaluation.get("primary_metric"), "direction": evaluation.get("direction"),
            "findings": [f for f in ((experiment.get("conclusions") or {}).get("findings") or []) if isinstance(f, str)][:12]}


def blocks_in(texts: List[Optional[str]], table: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    """The marked blocks of this project found by name in a study's code. A study of the same project (the same
    markers) yields them all; code from another project yields none."""
    found: Dict[str, str] = {}
    for text in texts:
        if not text:
            continue
        try:
            segments = space.parse(text)
        except space.SpaceError:
            continue
        for seg in segments:
            if "name" in seg and seg["name"] in table and seg["kind"] == table[seg["name"]]["kind"]:
                found.setdefault(seg["name"], seg["content"])
    return found
