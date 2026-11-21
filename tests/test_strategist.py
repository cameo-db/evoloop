"""The strategist (an agent that may change the course of a search, within bounds) and the spend governor."""
import copy
import os

import pytest

from evoloop import form, strategist
from evoloop.controller import Controller
from evoloop.model.base import StubBackend
from evoloop.strategies import lineage as lineage_rules

from helpers import ask, run, search
from test_loop import drive, scored
from test_parts import make_view, settings

ROWS = [("R1", "L1", "new", None, 0.50, "a"), ("R2", "L1", "local", "R1", 0.52, "a"),
        ("R3", "L2", "new", None, 0.40, "b"), ("R4", "L2", "local", "R3", 0.41, "b")]


def decide(action, args, ledger=(), **changes):
    s = settings(**dict({"strategist__mode": "act"}, **changes))
    return strategist.work_out({"action": action, "args": args}, make_view(ROWS), s, list(ledger))


def test_a_small_shift_of_the_shares_is_applied_and_a_large_one_waits():
    fault, effects, wait = decide("shares", {"new": 0.55, "cross": 0.15, "local": 0.30})
    assert fault is None and wait is None
    phases = effects["sets"]["schedule.phases"]
    assert (phases[0]["new"], phases[0]["cross"], phases[0]["local"]) == (0.55, 0.15, 0.30)
    assert phases[1] == form.DEFAULTS["schedule"]["phases"][1]               # only the phase in force moves
    fault, _, wait = decide("shares", {"new": 0.2, "cross": 0.2, "local": 0.6})
    assert fault is None and "more than strategist.max_share_shift" in wait


def test_exploration_cannot_be_taken_below_its_floor():
    fault, _, _ = decide("shares", {"new": 0.05, "cross": 0.25, "local": 0.70})
    assert "may not fall below strategist.min_new_share" in fault
    assert decide("shares", {"new": 0.5, "cross": 0.5, "local": 0.5})[0] is not None      # must sum to 1


def test_what_waits_for_the_person():
    assert "ask_first" in decide("strategy", {"mechanism": "archive"})[2]
    assert decide("novelty", {"novelty": 0.8})[2] is None
    assert "advise" in decide("novelty", {"novelty": 0.8}, strategist__mode="advise")[2]
    assert decide("stay", {}, strategist__mode="advise")[2] is None
    mine = [{"kind": "set", "key": "schedule.novelty", "value": 0.2, "by": "Ada", "status": "applied"}]
    assert "changed by you" in decide("novelty", {"novelty": 0.8}, ledger=mine)[2]
    theirs = [{"kind": "set", "key": "schedule.novelty", "value": 0.2, "by": strategist.BY, "status": "applied"}]
    assert decide("novelty", {"novelty": 0.8}, ledger=theirs)[2] is None
    assert "ask_first" in decide("force", {"mode": "cross", "count": 2}, strategist__ask_first=["force"])[2]


def test_decisions_off_the_menu_or_out_of_bounds_are_refused():
    assert "not an action on the menu" in decide("rewrite_everything", {})[0]
    assert decide("strategy", {"mechanism": "magic"})[0] is not None
    assert decide("crossover_kinds", {"kinds": ["splice"]})[0] is not None
    assert decide("novelty", {"novelty": 3})[0] is not None
    assert decide("force", {"mode": "cross", "kind": "edit", "count": 1})[0] is not None
    assert decide("force", {"mode": "local", "kind": "ablation", "count": 99})[1]["force"]["left"] == 5    # clipped
    assert "holds the best design is not retired" in decide("retire", {"lineage": "L1"})[0]
    assert decide("retire", {"lineage": "L2"})[1]["lineage"] == {"lineage": "L2", "to": "retired"}
    assert decide("retire", {"lineage": "L9"})[0] is not None


def test_a_lineage_set_aside_or_brought_back():
    rows = ROWS + [("R5", "L3", "new", None, 0.45, "c"), ("R6", "L3", "local", "R5", 0.451, "c"),
                   ("R7", "L3", "local", "R6", 0.452, "c"), ("R8", "L3", "local", "R7", 0.449, "c")]
    s = settings(population__trial_runs=2, population__retire_after=3, population__lineages=2)
    plain = lineage_rules.state(make_view(rows), s)
    assert plain["L3"]["state"] == "retired" and plain["L2"]["state"] == "active"
    s["_lineages"] = {"L3": {"to": "revived", "t": 100}, "L2": {"to": "retired", "t": 100}}
    told = lineage_rules.state(make_view(rows), s)
    assert told["L3"]["state"] == "active" and told["L2"]["state"] == "retired" and told["L1"]["state"] == "active"


def test_the_strategist_changes_course_on_a_plateau(tmp_path):
    folder = search(tmp_path, budget__evaluations=34, evaluation__allowance=150, audit__reviews="none",
                    strategist__mode="act", strategist__every=6, strategist__plateau=6, strategist__horizon=5,
                    crossover__kinds=["block_swap", "graft", "hybrid"], harness__level="standard")
    controller, reason = run(folder)
    assert reason.startswith("the budget"), reason
    ledger = controller.store.merged_list("ledger")
    decisions = [e for e in ledger if e["kind"] == "decision"]
    assert len(decisions) >= 3 and {e["status"] for e in decisions} <= {"applied", "refused", "proposed", "expired"}
    assert all(e["by"] == strategist.BY and e["reason"] and e["expects"] for e in decisions)
    moved = [e for e in ledger if e["kind"] == "set" and e["by"] == strategist.BY]
    assert moved and all(e["key"] == "schedule.phases" and e["decision"] in {d["id"] for d in decisions} for e in moved)
    for e in moved:      # every shift it made by itself was small, and exploration kept its floor
        phase = max(abs(a[k] - b[k]) for a, b in zip(e["old"], e["value"]) for k in ("new", "cross", "local"))
        assert phase <= 0.15 + 1e-9 and min(p["new"] for p in e["value"]) >= 0.10 - 1e-9
    view = controller.view()
    forced = [r for r in view.runs.values() if r["history"].get("forced_by")]
    assert forced and all(r["history"]["mode"] == "cross" for r in forced)
    assert any(e.get("outcome") and "gain" in e["outcome"] for e in decisions)       # scored against what followed
    assert any(c["role"] == "strategist" for c in controller.store.read("calls"))
    report = open(os.path.join(controller.run_dir, "report.md")).read()
    assert "## The strategist" in report and "gain that followed" in report


def test_in_advise_mode_every_decision_waits_for_a_yes(tmp_path):
    folder = search(tmp_path, budget__evaluations=40, evaluation__allowance=150, audit__reviews="none",
                    strategist__mode="advise", strategist__every=5, strategist__plateau=5, harness__level="standard")
    controller = Controller(folder, "t", poll=0.2)

    def waiting(_):
        return [e for e in controller.store.merged_list("ledger") if e["kind"] == "decision" and e["status"] == "proposed"]
    drive(controller, lambda v: len(waiting(v)) >= 2)
    first, second = waiting(None)[:2]
    before = copy.deepcopy(controller.settings["schedule"]["phases"])
    assert not [e for e in controller.store.merged_list("ledger") if e["kind"] == "set" and e["by"] == strategist.BY]
    assert not controller.state["forced"]                                         # nothing was changed yet
    ask(folder, "t", {"kind": "approve", "id": first["id"], "by": "Ada"})
    ask(folder, "t", {"kind": "decline", "id": second["id"], "by": "Ada", "reason": "not now"})
    ask(folder, "t", {"kind": "approve", "id": "S999", "by": "Ada"})
    controller.turn()
    ledger = {e["id"]: e for e in controller.store.merged_list("ledger")}
    assert ledger[first["id"]]["status"] == "approved" and ledger[first["id"]]["answered_by"] == "Ada"
    assert ledger[second["id"]]["status"] == "declined"
    changed = controller.settings["schedule"]["phases"] != before or bool(controller.state["forced"]) \
        or any(r["history"].get("forced_by") == first["id"] for r in controller.view().runs.values())
    assert changed
    answers = [e for e in ledger.values() if e["kind"] in ("approve", "decline")]
    assert [e["status"] for e in answers] == ["applied", "applied", "refused"]
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    controller.run(max_seconds=120)
    snap = __import__("json").load(open(os.path.join(controller.run_dir, "status.json")))
    assert "decisions_waiting" in snap and "spend" in snap


class Priced:
    """The example's stub, each call costing a fixed sum."""

    def __init__(self, folder, dollars):
        self.inner, self.dollars = StubBackend(os.path.join(folder, "stub_agents.py")), dollars

    def call(self, role, system, user, schema, context):
        reply, usage = self.inner.call(role, system, user, schema, context)
        return reply, dict(usage, cost_usd=self.dollars, model="priced")


def test_the_governor_makes_a_run_cheaper_when_it_heads_past_the_cap(tmp_path):
    folder = search(tmp_path, budget__evaluations=60, evaluation__allowance=150, audit__reviews="quarterly",
                    agents__backend="claude_code", budget__model_dollars=30, strategist__mode="off",
                    variation__proposals_per_slot=3, harness__level="standard", harness__coordinator="agent")
    controller = Controller(folder, "t", poll=0.2, agent_backend=Priced(folder, 0.5))
    reason = controller.run(max_seconds=240)
    steps = [e for e in controller.store.merged_list("ledger") if e["kind"] == "set" and e["by"] == strategist.GOVERNOR]
    keys = [e["key"] for e in steps]
    assert keys[:2] == ["variation.proposals_per_slot", "variation.proposals_per_slot"] and keys[2:3] in ([], ["harness.coordinator"])
    assert all("heading for $" in e["reason"] and "against a cap of $30.00" in e["reason"] for e in steps)
    assert controller.agents.dollars <= 30 + 0.5 * controller.capacity() + 1e-9      # the cap held
    assert reason.startswith("paused: the agent spend cap") or reason.startswith("the budget")
    # Past the reserve (the last 15% of the cap) only writers were called.
    late = [c for c in controller.store.read("calls") if c.get("role") != "writer"]
    spent, last_other = 0.0, 0.0
    for call in controller.store.read("calls"):
        spent += float(call.get("cost_usd") or 0.0)
        if call.get("role") != "writer":
            last_other = spent
    assert late and last_other <= 30 * 0.85 + 0.5 * 4 + 1e-9
    facts = strategist.spending(controller.store, controller.agents, controller.view(), controller.settings)
    assert facts["per_design"] > 0 and facts["projected"] >= facts["dollars"] and facts["cap"] == 30


def test_no_governing_without_a_cap_or_with_the_policy_off(tmp_path):
    folder = search(tmp_path, budget__evaluations=14, evaluation__allowance=150, audit__reviews="none",
                    agents__backend="claude_code", budget__model_dollars=5, budget__spend_policy="none",
                    variation__proposals_per_slot=3, harness__level="minimal")
    controller = Controller(folder, "t", poll=0.2, agent_backend=Priced(folder, 0.5))
    reason = controller.run(max_seconds=120)
    assert not [e for e in controller.store.merged_list("ledger") if e.get("by") == strategist.GOVERNOR]
    assert reason.startswith("paused: the agent spend cap of $5.00")              # the cap still stops the calls


def test_the_strategist_is_off_unless_the_run_type_or_the_brief_turns_it_on():
    base = {"objective": {"goal": "g", "direction": "maximize"}, "budget": {"evaluations": 100}}
    assert form.resolve(dict(base, run={"type": "explore_then_exploit"}))[0]["strategist"]["mode"] == "act"
    assert form.resolve(dict(base, run={"type": "survey"}))[0]["strategist"]["mode"] == "act"
    assert form.resolve(dict(base, run={"type": "discovery"}))[0]["strategist"]["mode"] == "off"
    assert form.resolve(dict(base, run={"type": "custom"}))[0]["strategist"]["mode"] == "off"
    assert form.check_change("strategist.mode", "advise") is None and form.check_change("strategist.mode", "wild") is not None
    assert form.check_change("strategist.ask_first", ["shares", "strategy"]) is None
    assert form.check_change("strategist.ask_first", ["everything"]) is not None
    assert form.check_change("budget.spend_policy", "none") is None
