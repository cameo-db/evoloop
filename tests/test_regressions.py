"""One test for each defect an independent review of the code reproduced (2026-11-20)."""
import os
import threading
import time

import pytest

from evoloop import form
from evoloop.agents import AgentError, Agents
from evoloop.controller import Controller
from evoloop.model.base import ModelError, StubBackend
from evoloop.store import SCORED, Store

from helpers import ask, run, search
from test_loop import drive, scored


class Wrapped:
    """The example's stub, with the writer's reply altered by `change(reply)`."""

    def __init__(self, folder, change=None, delay=0.0):
        self.inner, self.change, self.delay = StubBackend(os.path.join(folder, "stub_agents.py")), change, delay

    def call(self, role, system, user, schema, context):
        reply, usage = self.inner.call(role, system, user, schema, context)
        if self.delay and role == "writer":
            time.sleep(self.delay)
        if self.change and role == "writer":
            reply = self.change(reply)
        return reply, usage


def test_one_slot_and_a_trained_baseline(tmp_path):
    # A run recorded but not yet submitted was counted as holding a slot, so with one slot it never started.
    folder = search(tmp_path, budget__evaluations=5, evaluation__allowance=150, compute__gpus=1, audit__reviews="none")
    controller, reason = run(folder, seconds=120)
    assert reason == "the budget of 5 evaluations is spent"


def test_a_restart_with_every_slot_in_flight(tmp_path):
    folder = search(tmp_path, budget__evaluations=8, evaluation__allowance=2500, compute__gpus=2, audit__reviews="none")
    first = Controller(folder, "t", poll=0.1)
    drive(first, lambda v: sum(1 for r in v.in_flight() if r.get("job")) == 2 and not first.designing)
    first.backend.shutdown()
    first.pool.shutdown(wait=False)
    second = Controller(folder, "t", poll=0.2)
    assert second.run(max_seconds=200) == "the budget of 8 evaluations is spent"


def test_references_for_a_new_period_fit_in_two_slots(tmp_path):
    folder = search(tmp_path, budget__evaluations=14, evaluation__allowance=150, compute__gpus=2, audit__reviews="none")
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(v.lineages()) >= 5 and len(scored(v)) >= 7)
    ask(folder, "t", {"kind": "set", "changes": {"evaluation.allowance": 300, "evaluation.seed": 7}, "by": "Ada"})
    assert controller.run(max_seconds=200).startswith("the budget")
    references = [r for r in controller.view().runs.values() if r["purpose"] == "reference"]
    assert len(references) == 4 and all(r["performance"]["status"] in SCORED and r["seed"] == 7 for r in references)


def test_a_reply_of_an_unexpected_shape_does_not_end_the_run(tmp_path):
    folder = search(tmp_path, budget__evaluations=6, evaluation__allowance=150, audit__reviews="none")

    def spoil(reply):
        for proposal in reply["proposals"]:
            proposal.update(expected_gain=1.5, family=["a", "list"], name={"not": "text"}, hypothesis=7)
        return reply
    controller = Controller(folder, "t", poll=0.2, agent_backend=Wrapped(folder, spoil))
    assert controller.run(max_seconds=120).startswith("the budget")
    view = controller.view()
    assert all(isinstance(m["family"], str) for m in view.models.values())
    assert all(r["history"]["forecast"] is None for r in view.search_runs() if r["history"].get("call"))


def test_designs_that_all_fail_the_quick_check_come_to_an_end(tmp_path):
    folder = search(tmp_path, budget__evaluations=30, evaluation__allowance=150, evaluation__quick_check="false",
                    baseline__mode="skip", audit__reviews="none")
    controller, reason = run(folder, seconds=120)
    assert reason.startswith("stalled: the last") and "all failed or failed the quick check" in reason, reason
    view = controller.view()
    assert 8 <= sum(1 for r in view.runs.values() if r["performance"]["status"] == "invalid") <= 8 + controller.capacity()
    assert len(controller.store.read("calls")) <= 8 + controller.capacity() + 1


def test_a_paid_reply_that_cannot_be_used_is_still_charged(tmp_path):
    class Costly:
        def call(self, role, system, user, schema, context):
            return {"reasoning": "x", "note": "y"}, {"cost_usd": 2.5, "model": "m"}       # no `proposals`: unusable
    settings = form.resolve({"agents": {"backend": "anthropic_api"}, "budget": {"model_dollars": 4}})[0]
    agents = Agents(settings, str(tmp_path), Store(str(tmp_path / "r")), backend=Costly())
    for _ in range(2):
        with pytest.raises(AgentError):
            agents.call("writer", {"request": {}})
    assert agents.dollars == 5.0 and "spend cap" in agents.available()
    assert [c["cost_usd"] for c in agents.store.read("calls")] == [2.5, 2.5]


def test_calls_without_a_cost_stop_a_capped_run(tmp_path):
    class Free:
        def call(self, role, system, user, schema, context):
            return {"reasoning": "x", "note": "y", "lessons": []}, {"cost_usd": None, "model": "unpriced"}
    settings = form.resolve({"agents": {"backend": "anthropic_api"}, "budget": {"model_dollars": 10}})[0]
    agents = Agents(settings, str(tmp_path), Store(str(tmp_path / "r")), backend=Free())
    for _ in range(3):
        agents.call("analyst", {})
    assert "cannot be kept" in agents.available()


def test_the_success_threshold_stops_the_run_when_it_is_passed(tmp_path):
    folder = search(tmp_path, budget__evaluations=20, evaluation__allowance=150, objective__success_threshold=100.0,
                    audit__reviews="none")
    controller, reason = run(folder, seconds=120)
    assert reason == "the success threshold was passed"
    assert controller.spent(controller.view()) <= 1 + controller.capacity()      # not the whole budget


def test_rechecks_stay_inside_the_budget(tmp_path):
    folder = search(tmp_path, budget__evaluations=8, evaluation__allowance=150, evaluation__recheck_every=1,
                    audit__reviews="none")
    controller, reason = run(folder, seconds=120)
    assert reason.startswith("the budget")
    view = controller.view()
    assert len(scored(view)) <= 8 + controller.capacity()
    rechecks = [r for r in view.runs.values() if r["purpose"] == "recheck"]
    assert rechecks and all(r["history"]["mode"] is None for r in rechecks)       # a re-check is not a local move
    twice = [c for c in view.cands.values() if len(c["values"]) > 1]
    assert twice and all(abs(c["value"] - sum(c["values"]) / len(c["values"])) < 1e-12 for c in twice)


def test_slots_opened_together_do_not_all_go_to_one_trial(tmp_path):
    folder = search(tmp_path, budget__evaluations=24, evaluation__allowance=150, compute__gpus=4, audit__reviews="none",
                    population__trial_runs=2)
    controller = Controller(folder, "t", poll=0.1, agent_backend=Wrapped(folder, delay=0.6))
    controller.run(max_seconds=240)
    view = controller.view()
    trials = {}
    for r in view.runs.values():
        if r.get("purpose") == "trial":
            trials[r["history"]["lineage"]] = trials.get(r["history"]["lineage"], 0) + 1
    assert trials and max(trials.values()) == 1, trials        # one trial run completes a trial of two
    copies = [r for r in view.runs.values() if "an exact copy" in str(r["performance"].get("reason"))]
    assert len(copies) <= 2, [r["performance"]["reason"] for r in copies]


def test_stopping_a_run_does_not_restart_it(tmp_path):
    folder = search(tmp_path, budget__evaluations=6, evaluation__allowance=400000, compute__gpus=2, audit__reviews="none",
                    baseline__mode="skip")
    controller = Controller(folder, "t", poll=0.1)
    drive(controller, lambda v: any(r["performance"]["status"] == "running" for r in v.runs.values()))
    target = [r for r in controller.view().runs.values() if r["performance"]["status"] == "running"][0]
    ask(folder, "t", {"kind": "stop", "run": target["id"], "by": "Ada", "reason": "too slow"})
    ask(folder, "t", {"kind": "stop", "run": "R999", "by": "Ada"})
    drive(controller, lambda v: v.runs[target["id"]]["performance"]["status"] not in ("running", "queued", "designed"))
    stopped = controller.view().runs[target["id"]]
    assert not stopped.get("restarts") and stopped["performance"]["status"] in ("stopped_early", "not_run", "failed")
    entries = [e for e in controller.store.read("ledger") if e.get("kind") == "stop"]
    assert [e["status"] for e in entries] == ["applied", "refused"]
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    for r in controller.view().in_flight():
        ask(folder, "t", {"kind": "stop", "run": r["id"], "by": "Ada"})
    assert controller.run(max_seconds=60) == "stopped by the person"


def test_a_request_that_cannot_be_carried_out_is_refused_on_the_record(tmp_path):
    folder = search(tmp_path, budget__evaluations=4, evaluation__allowance=150, audit__reviews="none")
    controller = Controller(folder, "t", poll=0.2)
    controller.begin()
    ask(folder, "t", {"kind": "stop", "run": "R1", "by": "Ada"})        # recorded, never submitted: withdrawn
    ask(folder, "t", {"kind": "set", "changes": {"evaluation.seed": "abc", "evaluation.screen_keep": 0}, "by": "Ada"})
    ask(folder, "t", {"kind": "withdraw", "id": "S99", "by": "Ada"})
    ask(folder, "t", {"kind": "dance", "by": "Ada"})
    controller.turn()
    ledger = controller.store.merged_list("ledger")
    assert [e["status"] for e in ledger if e["kind"] == "set"] == ["refused", "refused"]
    assert [e["status"] for e in ledger if e["kind"] in ("withdraw", "dance")] == ["refused", "refused"]
    assert controller.view().runs["R1"]["performance"]["status"] == "not_run"
    assert not os.listdir(os.path.join(folder, "runs", "t", "requests")) or \
        os.listdir(os.path.join(folder, "runs", "t", "requests")) == ["done"]
    assert controller.run(max_seconds=120).startswith("the budget")


def test_calls_made_side_by_side_get_one_id_each(tmp_path):
    class Slow:
        def call(self, role, system, user, schema, context):
            time.sleep(0.01)
            return {"reasoning": "x", "note": "y", "lessons": []}, {"cost_usd": 0.01, "model": "m"}
    settings = form.resolve({"agents": {"backend": "anthropic_api", "max_concurrent_calls": 8}})[0]
    agents = Agents(settings, str(tmp_path), Store(str(tmp_path / "r")), backend=Slow())
    threads = [threading.Thread(target=agents.call, args=("analyst", {"n": i})) for i in range(24)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    ids = [c["id"] for c in agents.store.read("calls")]
    assert len(ids) == len(set(ids)) == 24 and abs(agents.dollars - 0.24) < 1e-9


def test_a_budget_change_records_what_else_it_moved(tmp_path):
    folder = search(tmp_path, budget__evaluations=12, evaluation__allowance=150, audit__reviews="none")
    controller = Controller(folder, "t", poll=0.2)
    controller.begin()
    ask(folder, "t", {"kind": "set", "changes": {"budget.evaluations": 100}, "by": "Ada"})
    controller.turn()
    entry = [e for e in controller.store.merged_list("ledger") if e["kind"] == "set"][0]
    assert entry["also_changed"]["variation.proposals_per_slot"] == [4, 3]      # the guidance for about 100
    assert "strategy.mechanism" not in entry["also_changed"]                    # the run type holds its strategy
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    controller.run(max_seconds=120)
    assert "with it changed:" in open(os.path.join(controller.run_dir, "report.md")).read()


def test_indentation_makes_a_different_design_and_distance_follows_the_code():
    from evoloop import space
    a = {"m": "for i in x:\n    y += i\n    z = 1\n"}
    b = {"m": "for i in x:\n    y += i\nz = 1\n"}
    assert space.key_of(a, ["m"]) != space.key_of(b, ["m"])
    assert space.key_of(a, ["m"]) == space.key_of({"m": "for i in x:\n    y += i   \n\n    z = 1\n"}, ["m"])
    conv = "class Net:\n    def forward(self, x):\n        return self.conv(self.pool(x)) + x\n"
    attn = "def score(q, k, v):\n    w = softmax(q @ k.T / sqrt(d))\n    return w @ v\n"
    assert space.similarity(conv, attn) < 0.1 and space.similarity(conv, conv) == 1.0
    assert space.similarity(conv, conv.replace("pool", "norm")) > 0.6


def test_only_the_listed_crossover_kinds_are_used(tmp_path):
    folder = search(tmp_path, budget__evaluations=14, evaluation__allowance=150, audit__reviews="none",
                    crossover__kinds=["graft"], schedule__phases=[{"until": 1.0, "new": 0.4, "cross": 0.4, "local": 0.2}])
    controller, _ = run(folder, seconds=120)
    moves = {r["history"]["move"] for r in controller.view().runs.values()}
    assert "hybrid" not in moves and "block_swap" not in moves
