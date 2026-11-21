"""The loop end to end on the built-in example, with stub agents: no model call, no GPU."""
import json
import os
import time

import pytest

from evoloop import audit, form, space, study
from evoloop.controller import Controller
from evoloop.store import SCORED, read_json

from helpers import ask, run, search


def drive(controller, until, limit=900):
    controller.begin()
    for _ in range(limit):
        reason = controller.turn()
        if reason or until(controller.view()):
            return reason
        time.sleep(0.1)
    raise AssertionError("the run did not reach the point the test waits for")


def scored(view):
    return [r for r in view.runs.values() if r["performance"].get("status") in SCORED]


def test_end_to_end(tmp_path):
    folder = search(tmp_path, budget__evaluations=22, evaluation__allowance=300, audit__reviews="halfway",
                    crossover__kinds=["block_swap", "graft", "hybrid"])
    controller, reason = run(folder)
    assert reason == "the budget of 22 evaluations is spent"
    view = controller.view()
    assert controller.spent(view) >= 22
    baseline = [r for r in view.runs.values() if r["purpose"] == "baseline"][0]
    best = view.best()
    assert best["value"] > view.own_value(baseline)                      # the search found something better
    moves = {r["history"]["move"] for r in view.runs.values()}
    assert {"baseline", "new_approach"} <= moves and moves & {"structural_change", "settings_move", "ablation"}
    assert moves & {"block_swap", "graft", "hybrid"}, moves                # a crossover of some kind ran
    for r in view.search_runs():
        assert r["history"]["mode"] in form.MODES and r["history"]["lineage"]
    crosses = [r for r in view.runs.values() if r["history"]["move"] in ("block_swap", "hybrid") and r.get("candidate")]
    assert all(r["history"]["second_parent"] and len(r["history"]["lineage_parents"]) >= 1 for r in crosses)
    # The stub's list holds a form that does not parse. Among several proposals it is passed over, and the
    # run that was chosen instead keeps the reason: nothing is dropped without a record.
    assert any("does not parse" in str(r["history"].get("not_chosen")) for r in view.runs.values() if r.get("candidate"))
    weighed = [r["history"]["proposals_weighed"] for r in view.search_runs() if r["history"].get("call")]
    assert weighed and max(weighed) == controller.settings["variation"]["proposals_per_slot"] == 4
    report = open(os.path.join(controller.run_dir, "report.md")).read()
    for heading in ("## Leaderboard", "## Population", "## What each mode returned", "## Steering ledger", "## Agents"):
        assert heading in report
    assert controller.store.read("reviews"), "the halfway and end reviews were written"
    status = read_json(os.path.join(controller.run_dir, "status.json"))
    assert status["ended"] == reason and status["agents"]["dollars"] == 0


def test_study_file_is_in_the_cameo_shape(tmp_path):
    folder = search(tmp_path, budget__evaluations=8, evaluation__allowance=200, data__accession="10.5555/example")
    controller, _ = run(folder)
    s = read_json(os.path.join(controller.run_dir, "study.json"))
    assert s["format_version"] == "0.4" and set(s) == {"format_version", "experiment", "models", "training", "runs"}
    models, recipes = {m["id"] for m in s["models"]}, set(s["training"])
    done = [r for r in s["runs"] if r["performance"]["status"] in ("done", "stopped_early")]
    assert done and all(r["model"] in models and r["training"] in recipes and r["seed"] is not None for r in done)
    assert all("def predict" in m["code"] for m in s["models"])
    assert all("PARAMS" in t["code"]["script"] for t in s["training"].values())
    assert all(isinstance(r["performance"]["score"], float) and r["performance"]["test"]["test_mse"] > 0 for r in done)
    assert s["experiment"]["search"]["lineages"] and s["experiment"]["conclusions"]["best_run"] in {r["id"] for r in s["runs"]}
    assert "not_reported" == s["experiment"]["environment"]               # never filled in by guessing
    assert study.star(s).startswith("On course for Silver")
    text = json.dumps(s)
    assert "Infinity" not in text and "NaN" not in text


class Recorder:
    """A backend that keeps what every role was shown, and answers with the example's stub."""

    def __init__(self, folder):
        from evoloop.model.base import StubBackend
        self.inner = StubBackend(os.path.join(folder, "stub_agents.py"))
        self.seen = []

    def call(self, role, system, user, schema, context):
        self.seen.append((role, user))
        return self.inner.call(role, system, user, schema, context)


def test_test_scores_never_reach_an_agent(tmp_path):
    folder = search(tmp_path, budget__evaluations=10, evaluation__allowance=200, harness__coordinator="agent")
    recorder = Recorder(folder)
    controller = Controller(folder, "t", poll=0.2, agent_backend=recorder)
    controller.run(max_seconds=240)
    assert {"writer", "coordinator", "assessor"} <= {role for role, _ in recorder.seen}
    assert all("test_mse" not in user and "hidden" not in user for _, user in recorder.seen)
    chosen = [r for r in controller.view().runs.values() if r["history"].get("coordinator")]
    assert chosen and all("code_would_choose" in r["history"]["coordinator"] for r in chosen)
    assert audit.scorecard(controller.store, controller.view())["coordinator"]["choices"] == len(chosen)


def test_steering_during_a_run(tmp_path):
    folder = search(tmp_path, budget__evaluations=18, evaluation__allowance=200)
    controller = Controller(folder, "t", poll=0.2)
    assert drive(controller, lambda v: len(scored(v)) >= 5) is None
    ask(folder, "t", {"kind": "set", "changes": {"schedule.novelty": 0.9, "population.lineages": 3}, "by": "Ada", "reason": "try"})
    ask(folder, "t", {"kind": "set", "changes": {"objective.direction": "maximize"}, "by": "Ada"})
    ask(folder, "t", {"kind": "note", "text": "No forms with more than seven constants.", "roles": ["writer"], "by": "Ada"})
    calls_before = len(controller.store.read("calls"))
    controller.turn()
    assert controller.settings["schedule"]["novelty"] == 0.9 and controller.settings["population"]["lineages"] == 3
    assert "Ada" in controller.sources["schedule.novelty"]
    ledger = controller.store.read("ledger")
    applied = [e for e in ledger if e["kind"] == "set" and e["status"] == "applied"]
    refused = [e for e in ledger if e["kind"] == "set" and e["status"] == "refused"]
    assert {e["key"] for e in applied} == {"schedule.novelty", "population.lineages"}
    assert all(e["by"] == "Ada" and e["old"] is not None and e["at_evaluations"] >= 5 for e in applied)
    assert [e["key"] for e in refused] == ["objective.direction"] and "defines the problem" in refused[0]["why"]
    assert controller.settings["objective"]["direction"] == "minimize"     # the refused change changed nothing
    note = [e for e in ledger if e["kind"] == "note"][0]
    reason = controller.run(max_seconds=240)
    assert reason.startswith("the budget")
    later = [c for c in controller.store.read("calls")[calls_before:] if c["role"] == "writer"]
    assert later and all(note["id"] in c["notes_shown"] for c in later)     # every later writer call read the note
    assert all(note["id"] in c["output"]["followed_notes"] for c in later if "output" in c)
    card = audit.scorecard(controller.store, controller.view())
    assert card["notes"][note["id"]]["shown_to_calls"] >= len(later)
    assert "No forms with more than seven constants." in open(os.path.join(controller.run_dir, "report.md")).read()


def test_a_note_can_be_withdrawn(tmp_path):
    folder = search(tmp_path, budget__evaluations=12, evaluation__allowance=200)
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 2)
    ask(folder, "t", {"kind": "note", "text": "Prefer trigonometric forms.", "by": "Ada"})
    controller.turn()
    note = [e for e in controller.store.read("ledger") if e["kind"] == "note"][0]
    assert [n["id"] for n in controller.settings["notes"]] == [note["id"]]
    ask(folder, "t", {"kind": "withdraw", "id": note["id"], "by": "Ada"})
    controller.turn()
    assert controller.settings["notes"] == []
    assert any(e.get("kind") == "note" for e in controller.store.read("ledger"))     # the record is kept
    controller.run(max_seconds=240)


@pytest.mark.parametrize("mechanism,islands", [("lineage", 1), ("archive", 1), ("tournament", 1), ("greedy", 1), ("lineage", 2)])
def test_every_strategy_runs(tmp_path, mechanism, islands):
    folder = search(tmp_path, budget__evaluations=12, evaluation__allowance=200, strategy__mechanism=mechanism,
                    strategy__islands=islands, strategy__migrate_every=3, audit__reviews="none")
    controller, reason = run(folder)
    assert reason.startswith("the budget"), reason
    view = controller.view()
    assert len(scored(view)) >= 12
    assert {r["history"]["mode"] for r in view.search_runs()} >= {"new", "local"}
    if islands > 1:
        assert {r["history"]["island"] for r in view.search_runs() if r["purpose"] == "search"} == {0, 1}
        assert any(r["history"]["migrant"] for r in view.runs.values())


def test_strategy_harness_and_space_can_change_midway(tmp_path):
    folder = search(tmp_path, budget__evaluations=20, evaluation__allowance=200, audit__reviews="none")
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 6)
    ask(folder, "t", {"kind": "set", "changes": {"strategy.mechanism": "archive", "harness.level": "minimal"}, "by": "Ada"})
    drive(controller, lambda v: len(scored(v)) >= 11)
    assert controller.settings["strategy"]["mechanism"] == "archive"
    ask(folder, "t", {"kind": "set", "changes": {"strategy.mechanism": "tournament", "space.preset": "settings_only"}, "by": "Ada"})
    controller.turn()
    switched = len(controller.view().runs)
    reason = controller.run(max_seconds=240)
    assert reason.startswith("the budget")
    view = controller.view()
    after = [r for r in view.search_runs() if int(r["id"][1:]) > switched + 3]
    assert after and all(r["history"]["move"] == "settings_move" for r in after)    # only settings are open now
    assert len(view.models) == len({r["model"] for r in view.runs.values() if r.get("model")})


def test_changing_the_run_length_begins_a_new_period(tmp_path):
    folder = search(tmp_path, budget__evaluations=18, evaluation__allowance=150, evaluation__leaders_refit=2, audit__reviews="none")
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 7)
    ask(folder, "t", {"kind": "set", "changes": {"evaluation.allowance": 400}, "by": "Ada", "reason": "longer fits"})
    def refitted(v):
        refs = [r for r in v.runs.values() if r["purpose"] == "reference"]
        return v.period == 1 and len(refs) == 2 and all(v.counts(r) for r in refs)
    drive(controller, refitted)
    view = controller.view()
    references = [r for r in view.runs.values() if r["purpose"] == "reference"]
    assert len(references) == 2 and all(r["period"] == 1 and r["allowance"] == 400 for r in references)
    assert all(view.counts(r) for r in references)
    old = [r for r in view.runs.values() if r.get("period", 0) == 0 and r["performance"].get("status") in SCORED]
    assert old and not any(view.counts(r) for r in old)        # earlier scores no longer decide selection
    assert any(e["kind"] == "period" and e["how"] == "fitted again" for e in controller.store.read("ledger"))
    reason = controller.run(max_seconds=240)
    assert reason.startswith("the budget")
    new = [r for r in controller.view().runs.values() if r.get("period") == 1 and r["purpose"] == "search"]
    assert new and all(r["allowance"] == 400 for r in new)


def test_a_stopped_run_continues(tmp_path):
    folder = search(tmp_path, budget__evaluations=12, evaluation__allowance=200, audit__reviews="none")
    first = Controller(folder, "t", poll=0.2)
    drive(first, lambda v: len(scored(v)) >= 4)
    first.backend.shutdown()               # the controller dies with jobs in flight
    first.pool.shutdown(wait=False)
    second = Controller(folder, "t", poll=0.2)
    reason = second.run(max_seconds=240)
    assert reason.startswith("the budget")
    view = second.view()
    assert len(scored(view)) >= 12 and not view.in_flight()
    ids = [r["id"] for r in view.runs.values()]
    assert len(ids) == len(set(ids))


def test_drain_and_budget_change(tmp_path):
    folder = search(tmp_path, budget__evaluations=30, evaluation__allowance=200, audit__reviews="none")
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 4)
    ask(folder, "t", {"kind": "stop", "by": "Ada", "reason": "enough"})
    reason = controller.run(max_seconds=120)
    assert reason == "stopped by the person" and len(scored(controller.view())) < 30
    # More runs are added to the ended run, and it goes on from where it stopped.
    ask(folder, "t", {"kind": "set", "changes": {"budget.evaluations": 9}, "by": "Ada"})
    before = len(scored(controller.view()))
    again = Controller(folder, "t", poll=0.2)
    reason = again.run(max_seconds=240)
    assert reason == "the budget of 9 evaluations is spent"
    assert len(scored(again.view())) >= max(9, before)
    assert any(e["kind"] == "set" and e["key"] == "budget.evaluations" and e["old"] == 30 for e in again.store.read("ledger"))


def test_the_space_is_enforced_by_code(tmp_path):
    folder = search(tmp_path, budget__evaluations=10, evaluation__allowance=200, audit__reviews="none",
                    space__forbidden_terms=["np.tanh", "np.abs"], variation__proposals_per_slot=1)
    controller, _ = run(folder)
    view = controller.view()
    refused = [r for r in view.runs.values() if r["performance"]["status"] == "not_run"]
    assert any("which this search forbids" in r["performance"]["reason"] for r in refused)
    for r in view.runs.values():
        if r.get("candidate"):
            assert "np.tanh" not in controller.designer.blocks(r["candidate"])["model"]
    assert space.frozen_hash(os.path.join(folder, "base"), os.path.join(folder, "adapter")) == controller.info["frozen"]


def test_an_unconfirmed_brief_does_not_run(tmp_path):
    folder = search(tmp_path)
    brief = form.load_brief(folder)
    form.put(brief, "budget.evaluations", 500)     # changed after it was agreed
    form.save_brief(folder, brief)
    with pytest.raises(form.BriefError):
        Controller(folder, "t").run(max_seconds=5)
