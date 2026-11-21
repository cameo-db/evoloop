"""One test for each defect a second independent review reproduced in the strategist and the spend governor
(2026-11-20): bounds that could be got round, decisions that could end a run, figures that were wrong."""
import copy
import os

import pytest

from evoloop import form, strategist
from evoloop.cli import main
from evoloop.controller import Controller
from evoloop.store import View
from evoloop.strategies import lineage as lineage_rules

from helpers import ask, search
from test_loop import drive, scored
from test_parts import make_view, settings
from test_strategist import ROWS, Priced, decide


@pytest.mark.parametrize("action,args", [
    ("local_mix", {"edit": 0.7, "settings": 0.3, "ablation": None}), ("local_mix", {"edit": "most"}),
    ("retire", {"lineage": ["L1"]}), ("revive", {"lineage": {"id": "L2"}}), ("crossover_kinds", {"kinds": [["graft"]]}),
    ("crossover_kinds", {"kinds": []}), ("crossover_kinds", {"kinds": "graft"}), ("force", {"mode": "local", "count": float("nan")}),
    ("force", {"mode": ["local"], "count": 1}), ("strategy", {}), ("strategy", {"mechanism": None}),
    ("shares", {"new": "0.5", "cross": 0.2, "local": 0.3}), ("novelty", {"novelty": None}), ("direction", {"text": 5}),
    (None, {}), (["shares"], {}), ("shares", "not a mapping")])
def test_a_malformed_decision_is_refused_not_raised(action, args):
    fault, _, wait = decide(action, args)
    assert isinstance(fault, str) and wait is None


def running(tmp_path, **answers):
    """A run with a few designs scored, the strategist on but not meeting by itself."""
    base = dict(budget__evaluations=60, evaluation__allowance=150, audit__reviews="none", strategist__mode="act",
                strategist__every=999, strategist__plateau=999, harness__level="standard", population__trial_runs=1)
    base.update(answers)
    folder = search(tmp_path, **base)
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 8)
    return folder, controller


def decisions(controller):
    return [e for e in controller.store.merged_list("ledger") if e["kind"] == "decision"]


def finish(folder, controller):
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    for r in controller.view().in_flight():
        ask(folder, "t", {"kind": "stop", "run": r["id"], "by": "Ada"})
    return controller.run(max_seconds=120)


def test_garbage_from_a_meeting_never_ends_the_run(tmp_path):
    folder, controller = running(tmp_path)
    controller.take_decisions([{"action": "local_mix", "args": {"edit": None}}, {"action": "retire", "args": {"lineage": [1]}},
                               {"action": {"x": 1}, "args": 7}, {"action": "strategy", "args": {}}])
    got = decisions(controller)
    assert len(got) == 4 and all(e["status"] == "refused" and e["why"] for e in got)
    assert controller.settings["strategy"]["mechanism"] == "lineage"
    assert finish(folder, controller) == "stopped by the person"
    assert "## The strategist" in open(os.path.join(controller.run_dir, "report.md")).read()


def test_ordered_slots_are_capped_in_all_and_respect_your_word(tmp_path):
    folder, controller = running(tmp_path)
    controller.take_decisions([{"action": "force", "args": {"mode": "local", "count": 4}},
                               {"action": "force", "args": {"mode": "cross", "count": 4}}])       # one of a kind per meeting
    controller.take_decisions([{"action": "force", "args": {"mode": "local", "count": 4}}])       # only one slot is left
    controller.take_decisions([{"action": "force", "args": {"mode": "local", "count": 1}}])       # none is left
    statuses = [(e["status"], (e["effects"].get("force") or {}).get("left")) for e in decisions(controller)]
    assert statuses == [("applied", 4), ("refused", None), ("applied", 1), ("refused", None)]
    assert sum(o["left"] for o in controller.state["forced"]) <= 5 == controller.settings["strategist"]["force_max"]
    assert "already ordered" in decisions(controller)[-1]["why"]
    # After the person sets the shares, an order for slots waits for them.
    controller.state["forced"] = []
    ask(folder, "t", {"kind": "set", "changes": {"schedule.local_mix": {"edit": 1.0, "settings": 0.0, "ablation": 0.0}}, "by": "Ada"})
    controller.turn()
    controller.take_decisions([{"action": "force", "args": {"mode": "local", "kind": "ablation", "count": 1}}])
    assert decisions(controller)[-1]["status"] == "refused" and "no share" in decisions(controller)[-1]["why"]
    controller.take_decisions([{"action": "force", "args": {"mode": "local", "kind": "edit", "count": 1}}])
    assert decisions(controller)[-1]["status"] == "proposed" and "changed by you" in decisions(controller)[-1]["why"]
    # Switched off: what it had ordered is given up.
    controller.state["forced"] = [{"mode": "local", "kind": None, "left": 3, "decision": decisions(controller)[0]["id"]}]
    ask(folder, "t", {"kind": "set", "changes": {"strategist.mode": "off"}, "by": "Ada"})
    controller.turn()
    assert controller.state["forced"] == [] and decisions(controller)[0].get("force_given_up")
    finish(folder, controller)


def test_ordered_slots_do_not_starve_new_designs(tmp_path):
    folder = search(tmp_path, budget__evaluations=40, evaluation__allowance=150, audit__reviews="none", strategist__mode="act",
                    strategist__every=999, strategist__plateau=999, strategist__min_new_share=0.3, strategist__force_max=5,
                    harness__level="standard", schedule__phases=[{"until": 1.0, "new": 0.34, "cross": 0.0, "local": 0.66}])
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 10)
    for _ in range(6):                           # it keeps ordering local slots, meeting after meeting
        controller.take_decisions([{"action": "force", "args": {"mode": "local", "count": 5}}])
        # Wait for the order to be used up (however slow the machine), or for the run to end.
        if drive(controller, lambda v: not controller.state["forced"]):
            break
    view = controller.view()
    modes = [r["history"]["mode"] for r in view.search_runs() if r["purpose"] == "search"][10:]
    fresh = sum(1 for m in modes if m in ("new", "novel")) / float(len(modes))
    assert len(modes) >= 8 and fresh >= 0.2, (fresh, modes)        # held near the floor of 0.3, not driven to 0
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    controller.run(max_seconds=120)


def test_a_yes_is_checked_against_the_run_as_it_is_now(tmp_path):
    folder, controller = running(tmp_path, strategist__mode="advise")
    controller.take_decisions([{"action": "shares", "args": {"new": 0.3, "cross": 0.1, "local": 0.6}}])
    held = decisions(controller)[0]
    assert held["status"] == "proposed"
    # The person changes the later phase and raises the floor on exploration before answering.
    phases = copy.deepcopy(controller.settings["schedule"]["phases"])
    phases[1].update(new=0.4, cross=0.2, local=0.4)
    ask(folder, "t", {"kind": "set", "changes": {"schedule.phases": phases, "strategist.min_new_share": 0.5}, "by": "Ada"})
    ask(folder, "t", {"kind": "approve", "id": held["id"], "by": "Ada"})
    controller.turn()
    after = decisions(controller)[0]
    assert after["status"] == "refused" and "can no longer be done" in after["why"] and "min_new_share" in after["why"]
    assert controller.settings["schedule"]["phases"] == phases                  # the person's phases stand
    # A yes that can still be done is applied with the effects worked out now: the later phase is not put back.
    ask(folder, "t", {"kind": "set", "changes": {"strategist.min_new_share": 0.1}, "by": "Ada"})
    controller.turn()
    controller.take_decisions([{"action": "shares", "args": {"new": 0.5, "cross": 0.2, "local": 0.3}}])
    second = decisions(controller)[-1]
    phases[1].update(new=0.45, local=0.35)
    ask(folder, "t", {"kind": "set", "changes": {"schedule.phases": phases}, "by": "Ada"})
    ask(folder, "t", {"kind": "approve", "id": second["id"], "by": "Ada"})
    controller.turn()
    now = controller.settings["schedule"]["phases"]
    assert decisions(controller)[-1]["status"] == "approved"
    assert (now[0]["new"], now[0]["local"]) == (0.5, 0.3) and (now[1]["new"], now[1]["local"]) == (0.45, 0.35)
    finish(folder, controller)


def test_a_decision_left_unanswered_lapses(tmp_path):
    folder, controller = running(tmp_path, strategist__mode="advise", strategist__horizon=3, budget__evaluations=40)
    controller.take_decisions([{"action": "novelty", "args": {"novelty": 0.9}}])
    held = decisions(controller)[0]
    drive(controller, lambda v: len(scored(v)) >= held["at_designs"] + 8)
    assert decisions(controller)[0]["status"] == "expired"
    ask(folder, "t", {"kind": "approve", "id": held["id"], "by": "Ada"})
    controller.turn()
    answers = [e for e in controller.store.merged_list("ledger") if e["kind"] == "approve"]
    assert answers[-1]["status"] == "refused" and "expired" in answers[-1]["why"]
    assert controller.settings["schedule"]["novelty"] != 0.9
    finish(folder, controller)


def test_the_cadence_and_the_spend_rate_survive_a_new_period():
    runs = {}
    for i in range(1, 21):
        runs["R%d" % i] = {"id": "R%d" % i, "candidate": "C%d" % i, "model": "M1", "purpose": "search", "period": 0, "t": i,
                           "ended": i, "history": {"lineage": "L1", "mode": "local"},
                           "performance": {"status": "done", "score": 0.5}}
    view = View(runs, {"M1": {"id": "M1", "family": "a"}}, {}, "maximize", 0.01, period=1)
    assert strategist.designs(view) == [] and strategist.designs_ever(view) == 20      # the count does not fall to 0

    class Spent:
        dollars, count = 10.0, 40

    class Calls:
        def read(self, stream):
            return [{"role": "writer", "cost_usd": 0.5, "t": i} for i in range(1, 21)]
    s = settings(budget__evaluations=60, budget__model_dollars=100)
    s["agents"]["backend"] = "claude_code"
    facts = strategist.spending(Calls(), Spent(), view, s)
    assert facts["per_design"] == 0.5 and facts["projected"] == 10.0 + 0.5 * 40      # not $10 a design


def test_the_projection_counts_designs_written_not_only_scored():
    runs = {}
    for i in range(1, 13):
        done = i <= 6          # six scored, six still training
        runs["R%d" % i] = {"id": "R%d" % i, "candidate": "C%d" % i, "model": "M1", "purpose": "search", "period": 0, "t": i,
                           "ended": i, "history": {"lineage": "L1", "mode": "new"},
                           "performance": {"status": "done", "score": 0.5} if done else {"status": "running"}}
    view = View(runs, {"M1": {"id": "M1", "family": "a"}}, {}, "maximize", 0.01, 0)

    class Spent:
        dollars, count = 6.0, 12

    class Calls:
        def read(self, stream):
            return []
    s = settings(budget__evaluations=20, budget__model_dollars=12)
    s["agents"]["backend"] = "claude_code"
    facts = strategist.spending(Calls(), Spent(), view, s)
    assert facts["per_design"] == 0.5                 # $6 over twelve designs written, not over six scored
    assert facts["designs_still_to_write"] == 8 and facts["projected"] == 10.0
    assert strategist.govern(Spent(), view, s, Calls()) is None        # on course: no step


def test_the_shift_of_a_share_is_measured_from_where_the_person_left_it(tmp_path):
    folder, controller = running(tmp_path)
    start = controller.settings["schedule"]["phases"][0]["new"]
    controller.take_decisions([{"action": "shares", "args": {"new": round(start - 0.15, 2), "cross": 0.10, "local": round(0.40 - (0.65 - start), 2)}}])
    controller.take_decisions([{"action": "shares", "args": {"new": round(start - 0.30, 2), "cross": 0.10, "local": round(0.55 - (0.65 - start), 2)}}])
    first, second = decisions(controller)
    assert first["status"] == "applied" and second["status"] == "proposed" and "from where you last left it" in second["why"]
    assert controller.settings["schedule"]["phases"][0]["new"] == round(start - 0.15, 2)
    # An approved move becomes the place the next one is measured from.
    ask(folder, "t", {"kind": "approve", "id": second["id"], "by": "Ada"})
    controller.turn()
    assert controller.settings["schedule"]["phases"][0]["new"] == round(start - 0.30, 2)
    controller.take_decisions([{"action": "shares", "args": {"new": round(start - 0.40, 2), "cross": 0.10, "local": round(0.65 - (0.65 - start), 2)}}])
    assert decisions(controller)[-1]["status"] == "applied"
    finish(folder, controller)


def test_a_lineage_brought_back_gets_a_second_chance_not_a_permanent_place():
    rows = [("R1", "L1", "new", None, 0.90, "a"), ("R2", "L1", "local", "R1", 0.91, "a"),
            ("R3", "L2", "new", None, 0.50, "b"), ("R4", "L2", "local", "R3", 0.51, "b"),
            ("R5", "L3", "new", None, 0.40, "c"), ("R6", "L3", "local", "R5", 0.40, "c")]
    s = settings(population__trial_runs=2, population__retire_after=3, population__lineages=1)
    s["_lineages"] = {"L2": {"to": "revived", "t": 100}, "L3": {"to": "revived", "t": 100}}
    state = lineage_rules.state(make_view(rows), s)
    assert state["L1"]["state"] == "active"                 # the leader keeps its place whoever is brought back
    assert state["L2"]["state"] == "active" and state["L3"]["state"] == "active"
    # Three more local moves without a gain after it was brought back: it retires again.
    s["_lineages"] = {"L2": {"to": "revived", "t": 3.5}}
    later = rows + [("R7", "L2", "local", "R4", 0.51, "b"), ("R8", "L2", "local", "R4", 0.505, "b"), ("R9", "L2", "local", "R4", 0.50, "b")]
    assert lineage_rules.state(make_view(later), s)["L2"]["state"] == "retired"
    # Bringing back one that is active, or under another strategy, is refused.
    assert "only a retired or benched lineage" in decide("revive", {"lineage": "L1"})[0]
    assert "only under the lineage strategy" in decide("retire", {"lineage": "L2"}, strategy__mechanism="archive")[0]


def test_off_means_off(tmp_path, capsys):
    folder, controller = running(tmp_path)
    assert main(["set", folder, "--name", "t", "strategist.mode=off", "--by", "Ada"]) == 0       # a bare `off`
    with pytest.raises(SystemExit):
        main(["set", folder, "--name", "t", "strategist.mode=", "--by", "Ada"])                   # not emptied
    with pytest.raises(SystemExit):
        main(["set", folder, "--name", "t", "strategist.ask_first=", "--by", "Ada"])
    controller.turn()
    assert controller.settings["strategist"]["mode"] == "off"
    # A meeting that was under way when it was switched off changes nothing.
    controller.take_decisions([{"action": "novelty", "args": {"novelty": 0.9}}, {"action": "force", "args": {"mode": "local", "count": 2}}])
    assert [e["status"] for e in decisions(controller)] == ["refused", "refused"] and not controller.state["forced"]
    assert controller.settings["schedule"]["novelty"] != 0.9
    finish(folder, controller)
    import yaml
    brief = yaml.safe_load("strategist: {mode: off}\nrun: {type: explore_then_exploit}\nbudget: {evaluations: 100}")
    assert brief["strategist"]["mode"] is False and form.resolve(brief)[0]["strategist"]["mode"] == "off"
    assert form.problems(brief) == []


def test_your_word_covers_parts_of_a_setting_and_what_followed_from_it():
    part = [{"kind": "set", "key": "schedule.local_mix.edit", "value": 0.9, "by": "Ada", "status": "applied"}]
    assert "changed by you" in decide("local_mix", {"edit": 0.2, "settings": 0.6, "ablation": 0.2}, ledger=part)[2]
    followed = [{"kind": "set", "key": "run.type", "value": "refine", "by": "Ada", "status": "applied",
                 "also_changed": {"schedule.novel_share": [0.33, 0.0]}}]
    assert "changed by you" in decide("novelty", {"novel_share": 0.9}, ledger=followed)[2]
    assert decide("novelty", {"novelty": 0.9}, ledger=followed)[2] is None
    governed = [{"kind": "set", "key": "schedule.novelty", "value": 0.1, "by": strategist.GOVERNOR, "status": "applied"}]
    assert decide("novelty", {"novelty": 0.9}, ledger=governed)[2] is None


def test_the_plateau_is_measured_against_the_baseline_too():
    rows = [("R1", "L1", "new", None, 0.90, "a")] + [("R%d" % i, "L2", "local", None, 0.2 + 0.04 * i, "b") for i in range(2, 14)]
    view = make_view(rows)
    view.runs["R1"]["purpose"] = "baseline"
    assert strategist.since_gain(view) == 12        # twelve designs, none above the baseline
    climbing = make_view([("R%d" % i, "L1", "local", None, 0.2 + 0.04 * i, "b") for i in range(1, 8)])
    assert strategist.since_gain(climbing) == 0


def test_the_strategists_direction_is_shown_apart_from_your_notes(tmp_path):
    from evoloop.agents import Agents
    from evoloop.store import Store
    seen = []

    class Echo:
        def call(self, role, system, user, schema, context):
            seen.append(context)
            return {"reasoning": "x", "note": "y", "lessons": []}, {"cost_usd": 0.0, "model": "m"}
    s = form.resolve({"agents": {"backend": "claude_code"}}, [
        {"kind": "note", "id": "S1", "text": "No attention.", "by": "Ada", "status": "active"},
        {"kind": "note", "id": "S2", "text": "Look at wider kernels.", "by": strategist.BY, "status": "active"}])[0]
    agents = Agents(s, str(tmp_path), Store(str(tmp_path / "r")), backend=Echo())
    agents.call("analyst", {})
    assert seen[0]["notes_from_the_person"] == [{"id": "S1", "text": "No attention."}]
    assert seen[0]["direction_from_the_strategist"] == [{"id": "S2", "text": "Look at wider kernels."}]
    assert agents.store.read("calls")[0]["notes_shown"] == ["S1", "S2"]


def test_the_person_can_set_a_lineage_aside_and_bring_it_back(tmp_path):
    folder, controller = running(tmp_path)
    lineages = lineage_rules.state(controller.view(), controller.settings)
    target = sorted(l for l, lin in lineages.items() if lin["state"] in ("active", "bench") and l != controller.view().best()["lineage"])[0]
    assert main(["lineage", folder, "--name", "t", "--retire", target, "--by", "Ada"]) == 0
    controller.turn()
    assert lineage_rules.state(controller.view(), controller.settings)[target]["state"] == "retired"
    assert main(["lineage", folder, "--name", "t", "--revive", target, "--by", "Ada"]) == 0
    assert main(["lineage", folder, "--name", "t", "--retire", "L999", "--by", "Ada"]) == 0
    controller.turn()
    assert lineage_rules.state(controller.view(), controller.settings)[target]["state"] == "active"
    entries = [e for e in controller.store.merged_list("ledger") if e["kind"] == "lineage"]
    assert [e["status"] for e in entries] == ["applied", "applied", "refused"] and all(e["by"] == "Ada" for e in entries)
    finish(folder, controller)
