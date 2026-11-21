"""What a person reads about a run: `status.json` while it goes, `report.md` when asked or at the end."""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from . import approaches, audit, form, schedule, skill, strategies, strategist
from .store import ENDED, Store, View, write_json


def leaderboard(view: View, limit: int = 15, columns: Optional[List[str]] = None,
                references: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """The best designs by validation score, with the baseline always shown, and the reference rows the person
    added (other models to compare with: never part of the search, and marked as such). `columns` names further
    figures: valid.<metric>, test.<metric>, speed, best_epoch, epochs_run."""
    rows = []
    ranked = view.scored()
    shown = ranked[:limit] + [c for c in ranked[limit:] if view.run_of(c["id"]).get("purpose") == "baseline"]
    for cand in shown:
        run = view.run_of(cand["id"])
        perf = run["performance"]
        row = {"kind": "baseline" if run.get("purpose") == "baseline" else "design", "model": cand["id"], "lineage": cand["lineage"],
               "family": cand["family"], "score": view.display(cand["value"]), "fits": len(cand["values"])}
        for column in columns or []:
            part, _, name = column.partition(".")
            if part in ("valid", "test"):
                row[column] = (perf.get(part) or {}).get(name)
            elif column == "speed":
                row[column] = (perf.get("inference_speed") or {}).get("examples_per_s") if isinstance(perf.get("inference_speed"), dict) else None
            else:
                row[column] = perf.get(column)
        row.update(parameters=perf.get("parameters"), minutes=perf.get("training_minutes"))
        rows.append(row)
    for ref in references or []:
        row = {"kind": "reference", "model": ref.get("label"), "lineage": None, "family": ref.get("note"), "score": ref.get("score"), "fits": None}
        for column in columns or []:
            part, _, name = column.partition(".")
            row[column] = (ref.get(part) or {}).get(name) if part in ("valid", "test") else None
        row.update(parameters=ref.get("parameters"), minutes=None)
        rows.append(row)
    return sorted(rows, key=lambda r: -view.sign * float(r["score"]) if isinstance(r.get("score"), (int, float)) else float("inf"))


def snapshot(controller: Any, view: View, reason: Optional[str] = None) -> Dict[str, Any]:
    settings = controller.settings
    best = view.best()
    counts: Dict[str, int] = {}
    for run in view.runs.values():
        status = run["performance"].get("status")
        counts[status] = counts.get(status, 0) + 1
    return {
        "run": controller.name, "updated": time.strftime("%Y-%m-%d %H:%M:%S"), "ended": reason,
        "budget": {"evaluations": settings["budget"]["evaluations"], "spent": round(controller.spent(view), 2),
                   "fraction": round(schedule.fraction_used(view, settings), 3)},
        "best": {"candidate": best["id"], "score": view.display(best["value"]), "family": best["family"]} if best else None,
        "runs": counts, "designing": len(controller.designing), "period": view.period,
        "strategy": {"mechanism": settings["strategy"]["mechanism"], "islands": settings["strategy"]["islands"],
                     "harness": settings["harness"]["level"], "coordinator": settings["harness"]["coordinator"],
                     "run_type": settings["run"]["type"], "space": settings["space"]["preset"]},
        "shares_now": {k: round(v, 3) for k, v in schedule.shares(view, settings).items()},
        "returns_by_mode": {m: {k: round(v, 2) for k, v in row.items()} for m, row in schedule.credit(view).items()},
        "agents": {"dollars": round(controller.agents.dollars, 4), "calls": controller.agents.count,
                   "cap_dollars": settings["budget"]["model_dollars"], "blocked": controller.blocked or controller.agents.available() or controller.agent_block,
                   "calls_without_a_cost": controller.agents.unpriced},
        "spend": strategist.spending(controller.store, controller.agents, view, settings),
        "decisions_waiting": [e["id"] for e in controller.store.merged_list("ledger")
                              if e.get("kind") == "decision" and e.get("status") == "proposed"],
        "forced_slots": controller.state.get("forced") or [],
        "open_questions": [q for q in controller.store.read("questions") if q.get("status") == "open"][-5:],
        "notes_in_force": [{"id": n["id"], "text": n["text"]} for n in settings.get("notes") or []],
    }


def status(controller: Any, view: View, reason: Optional[str] = None) -> None:
    write_json(os.path.join(controller.run_dir, "status.json"), snapshot(controller, view, reason))


def table(rows: List[Dict[str, Any]]) -> List[str]:
    if not rows:
        return ["(none)"]
    heads = list(rows[0])

    def cell(value: Any) -> str:
        if isinstance(value, float):
            return "%.5g" % value
        return "" if value is None else str(value)
    out = ["| " + " | ".join(heads) + " |", "|" + "|".join("---" for _ in heads) + "|"]
    out.extend("| " + " | ".join(cell(row.get(h)) for h in heads) + " |" for row in rows)
    return out


def lines(controller: Any, view: View, reason: Optional[str] = None) -> List[str]:
    settings, store = controller.settings, controller.store
    snap = snapshot(controller, view, reason)
    out = ["# Run %s" % controller.name, "", "Goal: %s" % settings["objective"]["goal"], ""]
    out.append("State: %s. Evaluations spent: %s of %s. Agent spend: $%.2f over %d calls." % (
        reason or "running", snap["budget"]["spent"], snap["budget"]["evaluations"], controller.agents.dollars,
        controller.agents.count))
    if snap["best"]:
        out.append("Best: %s (%s), score %.6g." % (snap["best"]["candidate"], snap["best"]["family"], snap["best"]["score"]))
    out += ["", "## Leaderboard (validation)", ""] + table(leaderboard(view, int(settings["report"]["top"]), settings["report"]["columns"],
                                                                         store.read("references")))
    out += ["", "## Population (%s)" % settings["strategy"]["mechanism"], ""]
    population = strategies.make(settings).population(view, settings)
    out += table([{k: v for k, v in row.items() if not isinstance(v, (list, dict)) or k in ("parents", "cell")}
                  for row in population][:30])
    out += ["", "## What each mode returned", "",
            "Gain is the rise in the best score, in noise floors; half of each rise is credited to the slot that "
            "founded the lineage.", ""]
    out += table([dict(mode=m, **row) for m, row in snap["returns_by_mode"].items()])
    card = audit.scorecard(store, view)
    out += ["", "## By kind of move", ""] + table([dict(move=m, **row) for m, row in card["by_move"].items()])
    out += ["", "## Agents", ""] + table([dict(role=r, calls=row["calls"], dollars=round(row["dollars"], 4),
                                               seconds=round(row["seconds"], 1), failed=row["failed"])
                                          for r, row in card["spend"].items()])
    if card.get("writer"):
        out += ["", "Writer forecasts against outcomes: " + "; ".join("%s %s" % (k.replace("_", " "), v)
                                                                      for k, v in card["writer"].items()) + "."]
    if card.get("coordinator"):
        out += ["", "Coordinator: %d choices, %d of them a departure from what the schedule alone would have chosen." % (
            card["coordinator"]["choices"], card["coordinator"]["departed_from_the_schedule"])]
    if controller.agents.unpriced:
        out += ["", "WARNING: %d agent calls came back with no cost; the spend figure above leaves them out." %
                controller.agents.unpriced]
    ledger = [e for e in store.merged_list("ledger") if e.get("kind") in ("init", "set", "note", "stop", "period", "withdraw", "review", "skill",
                                                                           "lineage", "approve", "decline", "rehash", "force", "import", "reference")]
    decisions = [e for e in store.merged_list("ledger") if e.get("kind") == "decision"]
    if decisions:
        out += ["", "## The strategist", "",
                "Each decision with what it expected and what followed over the next designs (the rise in the best "
                "score, in noise floors). What followed is not proof of what the decision caused.", ""]
        out += table([{"id": e["id"], "at": e.get("at_evaluations"), "action": e.get("action"),
                       "args": json.dumps(e.get("args"), default=str)[:70], "status": e.get("status"),
                       "expected gain": (e.get("expects") or {}).get("gain"),
                       "gain that followed": (e.get("outcome") or {}).get("gain"),
                       "why": (e.get("why") or e.get("reason") or "")[:90]} for e in decisions])
        waiting = [e for e in decisions if e.get("status") == "proposed"]
        if waiting:
            out += ["", "### Waiting for your yes or no", "",
                    "Answer with `evoloop approve` or `evoloop decline` and `--id`. A yes is checked against the run as it "
                    "is then; a decision left unanswered lapses.", ""]
            for e in waiting:
                out += ["- **%s** `%s` %s" % (e["id"], e.get("action"), json.dumps(e.get("args"), default=str)),
                        "  - its reason: %s" % (e.get("reason") or "(none given)"),
                        "  - it expects: %s" % json.dumps(e.get("expects"), default=str),
                        "  - it waits because: %s" % e.get("why")]
    if approaches.on(settings) or store.read("approaches"):
        out += ["", "## Approaches handed to the writers", "",
                "Beat reference: the share of finished designs that beat their parent (or, with no parent, the middle "
                "of all designs) by more than the noise. `none` is no approach.", ""] + table(approaches.table(store, view))
    by_model = writers_by_model(store, view)
    if len(by_model) > 1:
        out += ["", "## Writers by model", ""] + table(by_model)
    money = snap["spend"]
    if money.get("projected") is not None:
        out += ["", "## Agent spend", "", "$%.2f so far, $%.3f per design; at that rate the run ends at about $%.2f%s." % (
            money["dollars"], money["per_design"], money["projected"],
            " against a cap of $%.2f" % float(money["cap"]) if money.get("cap") is not None else "")]
    out += ["", "## Steering ledger", ""]
    for e in ledger:
        what = {"init": "started as %s, %s strategy, %s harness" % (e.get("run_type"), e.get("strategy"), e.get("harness")),
                "set": "%s: %r -> %r" % (e.get("key"), e.get("old"), e.get("value")),
                "note": "note to %s: %s%s" % (", ".join(e.get("roles") or []) or "all roles", e.get("text"),
                                              " [withdrawn]" if e.get("status") == "withdrawn" else ""),
                "stop": "stop %s" % (e.get("run") or "(drain)"), "withdraw": "withdrew %s" % e.get("target"),
                "period": "period %s began; leaders %s %s" % (e.get("period"), e.get("leaders"), e.get("how")),
                "review": "review asked for",
                "rehash": "the frozen code was changed on purpose%s" % ("; scores before and after are not compared" if e.get("new_period") else ""),
                "force": "ordered the next %s slot(s): %s%s%s" % (e.get("count"), e.get("mode"), " (%s)" % e["move"] if e.get("move") else "",
                                                                 "; instruction: %s" % e["instruction"] if e.get("instruction") else ""),
                "import": "imported %s from %s" % (", ".join(e.get("imported") or []) or "nothing", e.get("source")),
                "reference": "reference row %s (score %s)" % (e.get("label"), e.get("score")),
                "lineage": "lineage %s %s" % (e.get("lineage"), e.get("to")),
                "skill": "the skill file(s) %s changed (%s -> %s)" % (", ".join(e.get("skills") or []), e.get("before"), e.get("after")),
                "approve": "approved %s" % e.get("target"), "decline": "declined %s" % e.get("target")}[e["kind"]]
        if e.get("decision"):
            what += " [decision %s]" % e["decision"]
        if e.get("status") == "refused":
            what += " (REFUSED: %s)" % e.get("why")
        if e.get("also_changed"):   # a change of the budget or the run type moves the settings that follow from it
            what += "; with it changed: " + ", ".join("%s %r -> %r" % (k, v[0], v[1]) for k, v in sorted(e["also_changed"].items()))
        out.append("- %s, at %s evaluations, by %s: %s%s" % (e.get("id"), e.get("at_evaluations"), e.get("by") or "the loop",
                                                           what, " (%s)" % e["reason"] if e.get("reason") else ""))
    if card["notes"]:
        out += ["", "Notes as read by the agents: " + "; ".join(
            "%s shown to %d calls, cited by %d" % (n, row["shown_to_calls"], row["said_followed"])
            for n, row in card["notes"].items()) + "."]
    lessons = store.read("knowledge")
    if lessons:
        out += ["", "## Lessons", ""] + ["- %s (%s; %s)" % (l["statement"], l["status"], ", ".join(l.get("evidence") or []))
                                         for l in lessons[-20:]]
    reviews = store.read("reviews")
    if reviews:
        out += ["", "## Reviews of the agents", ""]
        for r in reviews:
            out += ["### %s, %s (%s)" % (r["role"], r["why"], r["id"]), "", str(r.get("assessment") or ""), ""]
            out += ["- suggestion: %s (figure: %s)" % (s.get("change"), s.get("figure")) for s in r.get("suggestions") or []
                    if isinstance(s, dict)]
    questions = [q for q in store.read("questions") if q.get("status") == "open"]
    if questions:
        out += ["", "## Questions for you", ""] + ["- %s: %s (default: %s)" % (q["id"], q["question"], q.get("default"))
                                                   for q in questions]
    failed = [r for r in view.runs.values() if r["performance"].get("status") in ("failed", "invalid", "not_run")]
    if failed:
        out += ["", "## Runs without a score", ""] + ["- %s (%s): %s" % (r["id"], r["performance"]["status"],
                                                                         str(r["performance"].get("reason"))[:200])
                                                      for r in failed[-20:]]
    notes = form.warnings(settings) + skill.missing(settings.get("_skill"), view, store.read("references"))
    if notes:
        out += ["", "## Warnings", ""] + ["- " + n for n in notes]
    return out


def write(controller: Any, view: View, reason: Optional[str] = None) -> str:
    path = os.path.join(controller.run_dir, "report.md")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines(controller, view, reason)) + "\n")
    return path


def writers_by_model(store: Store, view: View) -> List[Dict[str, Any]]:
    """With several models writing (`agents.writer_mix`): what the designs of each came to."""
    drawn = {c["id"]: c["drawn_model"] for c in store.read("calls") if c.get("role") == "writer" and c.get("drawn_model")}
    rows: Dict[str, Dict[str, Any]] = {}
    for call, model in drawn.items():
        rows.setdefault(model, {"model": model, "calls": 0, "designs": 0, "scored": 0, "beat reference": 0, "best": None})["calls"] += 1
    for run in view.runs.values():
        model = drawn.get(run["history"].get("call"))
        if model is None or run.get("purpose", "search") not in ("search", "trial"):
            continue
        row = rows[model]
        row["designs"] += 1
        own = view.own_value(run)
        if own is not None:
            row["scored"] += 1
            row["best"] = view.display(own) if row["best"] is None else view.display(max(view.sign * row["best"], own))
        row["beat reference"] += int(approaches.reward(view, run) or 0)
    return sorted(rows.values(), key=lambda r: r["model"])
