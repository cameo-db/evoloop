"""What a person reads about a run: `status.json` while it goes, `report.md` when asked or at the end."""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from . import audit, form, schedule, strategies, strategist
from .store import ENDED, View, write_json


def leaderboard(view: View, limit: int = 15, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    rows = []
    for cand in view.scored()[:limit]:
        run = view.run_of(cand["id"])
        perf = run["performance"]
        row = {"candidate": cand["id"], "lineage": cand["lineage"], "family": cand["family"],
               "score": view.display(cand["value"]), "runs": len(cand["values"]), "move": run["history"].get("move"),
               "parameters": perf.get("parameters"), "minutes": perf.get("training_minutes")}
        for column in columns or []:   # the brief's own columns: valid.<metric> or test.<metric>
            part, _, name = column.partition(".")
            row[column] = (perf.get(part) or {}).get(name) if part in ("valid", "test") else perf.get(column)
        rows.append(row)
    return rows


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
    out += ["", "## Leaderboard (validation)", ""] + table(leaderboard(view, 15, settings["report"]["columns"]))
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
    ledger = [e for e in store.merged_list("ledger") if e.get("kind") in ("init", "set", "note", "stop", "period", "withdraw", "review",
                                                                           "lineage", "approve", "decline")]
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
                "lineage": "lineage %s %s" % (e.get("lineage"), e.get("to")),
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
    notes = form.warnings(settings)
    if notes:
        out += ["", "## Warnings", ""] + ["- " + n for n in notes]
    return out


def write(controller: Any, view: View, reason: Optional[str] = None) -> str:
    path = os.path.join(controller.run_dir, "report.md")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines(controller, view, reason)) + "\n")
    return path
