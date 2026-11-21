"""Auditing the agents, like reviewing a consulting group.

Three levels, each switchable while a run is going:

    records     every call is kept (always)
    scorecard   figures per role, computed by code from the records at no cost (`audit.scorecard`)
    review      an assessor reads each role's record and writes a review for the person, at the points
                `audit.reviews` gives (none, end, halfway, thirds, quarterly, a list of shares, on_demand)

A review goes to the person, not to the agents. Its suggestions take effect only if the person adopts
them, as notes in the steering ledger; the next review can then check whether they did what they were for.

The scorecard judges what a role stated against what happened. It does not show what the search would
have been without the role; that takes a stretch of the run with the role switched off."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .agents import AgentError, Agents, spend
from .schedule import credit
from .store import Store, View


def spearman(pairs: List[Any]) -> Optional[float]:
    if len(pairs) < 5:
        return None

    def ranks(values: List[float]) -> List[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        for rank, index in enumerate(order):
            out[index] = float(rank)
        return out
    a, b = ranks([p[0] for p in pairs]), ranks([p[1] for p in pairs])
    n = len(pairs)
    ma, mb = sum(a) / n, sum(b) / n
    va, vb = sum((x - ma) ** 2 for x in a), sum((y - mb) ** 2 for y in b)
    return None if va <= 0 or vb <= 0 else round(sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (va * vb) ** 0.5, 3)


def forecasts(view: View) -> List[Dict[str, Any]]:
    """Each writer forecast beside what came about, in noise floors against the same reference."""
    rows = []
    for run in view.search_runs():
        forecast = run["history"].get("forecast")
        value = view.own_value(run)
        if not forecast or value is None:
            continue
        parent = run["history"].get("parent")
        reference = view.own_value(view.runs[parent]) if parent in view.runs else None
        if reference is None:
            earlier = [view.own_value(r) for r in view.search_runs() if r["id"] != run["id"] and view.own_value(r) is not None
                       and r.get("ended", 0) <= run.get("t", 0)]
            reference = max(earlier) if earlier else None
        if reference is None:
            continue
        rows.append({"run": run["id"], "move": run["history"].get("move"), "stated_gain": forecast["gain"],
                     "stated_probability": forecast["probability_better"],
                     "gain": round((value - reference) / view.noise, 2), "call": run["history"].get("call")})
    return rows


def scorecard(store: Store, view: View) -> Dict[str, Any]:
    card: Dict[str, Any] = {"spend": spend(store)}
    rows = forecasts(view)
    if rows:
        right = sum(1 for r in rows if (r["gain"] > 0) == (r["stated_gain"] > 0))
        better = [r for r in rows if r["gain"] > 1.0]
        card["writer"] = {
            "forecasts": len(rows),
            "sign_right": "%d of %d" % (right, len(rows)),
            "mean_stated_gain": round(sum(r["stated_gain"] for r in rows) / len(rows), 2),
            "mean_gain": round(sum(r["gain"] for r in rows) / len(rows), 2),
            "rank_correlation": spearman([(r["stated_gain"] * r["stated_probability"], r["gain"]) for r in rows]),
            "beat_reference_by_a_noise_floor": "%d of %d" % (len(better), len(rows)),
            "mean_stated_probability": round(sum(r["stated_probability"] for r in rows) / len(rows), 2)}
    by_move: Dict[str, Dict[str, Any]] = {}
    best = None
    for run in view.search_runs():
        move = run["history"].get("move") or "?"
        row = by_move.setdefault(move, {"runs": 0, "scored": 0, "failed": 0, "raised_the_best": 0})
        row["runs"] += 1
        value = view.own_value(run)
        status = run["performance"].get("status")
        row["failed"] += 1 if status in ("failed", "invalid") else 0
        if value is None:
            continue
        row["scored"] += 1
        if best is not None and value > best + view.noise:
            row["raised_the_best"] += 1
        best = value if best is None else max(best, value)
    card["by_move"] = by_move
    card["by_mode"] = {mode: {k: round(v, 2) for k, v in row.items()} for mode, row in credit(view).items()}
    chosen = [r["history"]["coordinator"] for r in view.runs.values() if r["history"].get("coordinator")]
    if chosen:
        card["coordinator"] = {"choices": len(chosen),
                               "departed_from_the_schedule": sum(1 for c in chosen if c["chose"] != c["code_would_choose"])}
    notes = {}
    for call in store.read("calls"):
        for note in call.get("notes_shown") or []:
            row = notes.setdefault(note, {"shown_to_calls": 0, "said_followed": 0})
            row["shown_to_calls"] += 1
            row["said_followed"] += 1 if note in ((call.get("output") or {}).get("followed_notes") or []) else 0
    card["notes"] = notes
    return card


def analyse(store: Store, agents: Agents, designer: Any, view: View, settings: Dict[str, Any], since: int) -> bool:
    """The analyst's turn: lessons from the results since its last call, and questions for the person."""
    seen = [r for r in view.ended() if r["performance"].get("status") != "not_run"]
    runs = sorted(seen, key=lambda r: r.get("ended", 0))[since:]
    context = {
        "objective": settings["objective"], "noise_floor": view.noise,
        "results": [{"run": r["id"], "candidate": r.get("candidate"), "lineage": r["history"].get("lineage"),
                     "family": (view.models.get(r.get("model")) or {}).get("family"), "move": r["history"].get("move"),
                     "change": r["history"].get("change_summary"), "hypothesis": r["history"].get("hypothesis"),
                     "status": r["performance"].get("status"), "score": r["performance"].get("score"),
                     "valid": r["performance"].get("valid"), "reason": r["performance"].get("reason"),
                     "parent": r["history"].get("parent")} for r in runs],
        "leaderboard": [designer.summary(view, c["id"]) for c in view.scored()[:10]],
        "lessons_so_far": [{"id": l["id"], "statement": l["statement"], "status": l["status"]}
                           for l in store.read("knowledge")][-30:]}
    if settings["variation"].get("approaches") == "evolve":
        from . import approaches
        context["approaches"] = [{k: row[k] for k in ("id", "text", "by", "status", "designs", "finished", "win_rate")}
                                 for row in approaches.record(store, view).values()]
    try:
        output = agents.call("analyst", context, about="results %d to %d" % (since, since + len(runs)))
    except AgentError:
        return False
    for lesson in output.get("lessons") or []:
        if isinstance(lesson, dict) and lesson.get("statement"):
            evidence = [e for e in lesson.get("evidence") or [] if e in view.runs]
            lineages = {view.runs[e]["history"].get("lineage") for e in evidence}
            # Code keeps the gate: a lesson counts as supported only with evidence from two lineages.
            status = "supported" if lesson.get("status") == "supported" and len(lineages) >= 2 else "tentative"
            store.append("knowledge", {"id": "K%d" % (len(store.read("knowledge")) + 1), "statement": str(lesson["statement"])[:600],
                                       "status": status, "evidence": evidence, "call": output.get("_call")})
    if output.get("new_approach"):
        from . import approaches
        approaches.add(store, view, settings, [output["new_approach"]], output.get("_call"))
    for question in output.get("questions") or []:
        if isinstance(question, dict) and question.get("question"):
            store.append("questions", {"id": "Q%d" % (len(store.read("questions")) + 1), "question": str(question["question"])[:600],
                                       "default": question.get("default"), "from": "analyst", "status": "open"})
    return True


def review(store: Store, agents: Agents, view: View, settings: Dict[str, Any], why: str, only: Any = None) -> None:
    """The assessor's review of each role, written for the person. `only` names the roles the person asked for."""
    card = scorecard(store, view)
    calls = store.read("calls")
    wanted = only if isinstance(only, list) and only else settings["audit"]["review_roles"]
    roles = sorted({c["role"] for c in calls if c.get("role") not in ("assessor", "translator")})
    if isinstance(wanted, list):
        roles = [r for r in roles if r in wanted]
    outcomes = {r["history"].get("call"): r for r in view.runs.values() if r["history"].get("call")}
    adopted = [e for e in store.merged_list("ledger") if e.get("kind") == "note" and e.get("from_review")
               and e.get("status") == "active"]
    for role in roles:
        log = []
        for call in [c for c in calls if c.get("role") == role][-60:]:
            run = outcomes.get(call["id"])
            log.append({"call": call["id"], "about": call.get("about"), "note": (call.get("output") or {}).get("note"),
                        "error": call.get("error"), "shown": call.get("shown"), "notes_shown": call.get("notes_shown"),
                        "stated": (run or {}).get("history", {}).get("forecast") if run else None,
                        "outcome": {"run": run["id"], "status": run["performance"].get("status"),
                                    "score": run["performance"].get("score")} if run else None})
        context = {"role": role, "why_now": why, "noise_floor": view.noise, "scorecard": card.get(role),
                   "spend": card["spend"].get(role), "by_move": card["by_move"] if role == "writer" else None,
                   "calls": log, "changes_adopted_from_earlier_reviews": [
                       {"id": e["id"], "text": e["text"]} for e in adopted if role in (e.get("roles") or [role])]}
        try:
            output = agents.call("assessor", context, about=role)
        except AgentError:
            continue
        store.append("reviews", {"id": "V%d" % (len(store.read("reviews")) + 1), "role": role, "why": why,
                                 "assessment": output.get("assessment"), "strengths": output.get("strengths") or [],
                                 "weaknesses": output.get("weaknesses") or [], "suggestions": output.get("suggestions") or [],
                                 "call": output.get("_call"), "status": "for the person"})
