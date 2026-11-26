"""What a writer is shown of the designs tried, and how family labels are kept to one per family (2026-11-26).

In real searches the opening designs were written at the same moment and came out alike; writers called families
"uncovered" that had only failed or were still training; and one family went under three spellings."""
import os

from evoloop import audit
from evoloop.controller import Controller
from evoloop.design import family_key, same_family, spelled
from evoloop.store import SCORED

from helpers import run, search

QUIET = dict(evaluation__allowance=150, audit__reviews="none", harness__level="standard", baseline__mode="skip")


class Recorder:
    """A backend that keeps what each role was shown, and answers with the example's stub."""

    def __init__(self, folder):
        from evoloop.model.base import StubBackend
        self.inner = StubBackend(os.path.join(folder, "stub_agents.py"))
        self.seen = []

    def call(self, role, system, user, schema, context):
        self.seen.append((role, context))
        return self.inner.call(role, system, user, schema, context)


def test_one_family_has_one_label_whatever_its_spelling():
    assert spelled("Factorised Output_Head") == "factorised-output-head" and spelled("") == "unlabelled"
    assert family_key("factorised output heads") == family_key("output-head-factorized") == family_key("Factorized_Output_Head")
    known = ["factorised-output-head", "dilated-conv", "stub-family-3"]
    assert same_family("Factorized output head", known, {}) == "factorised-output-head"     # the label already in use stays
    assert same_family("dilated convs", known, {}) == "dilated-conv"
    assert same_family("factorized-head", known, {}) == "factorized-head"                   # a word less: code does not guess
    assert same_family("stub_family_4", known, {}) == "stub-family-4"                       # a different number is a different family
    assert same_family("denoise", known, {}) == "denoise"
    # What was merged stays merged for designs written later, in any spelling.
    merged = {"factorized-head": "factorised-output-head"}
    assert same_family("Factorised head", known, merged) == "factorised-output-head"


def test_the_writer_is_shown_every_design_tried_and_the_ones_in_training(tmp_path):
    folder = search(tmp_path, budget__evaluations=8, compute__gpus=3, **QUIET)
    recorder = Recorder(folder)
    controller = Controller(folder, "t", poll=0.2, agent_backend=recorder)
    assert controller.run(max_seconds=240).startswith("the budget")
    shown = [context for role, context in recorder.seen if role == "writer"]
    # The opening designs are written one after another: each is shown the ones before it, still in training.
    assert [len(c["in_training"]) for c in shown[:3]] == [0, 1, 2]
    assert all(c["request"]["mode"] == "new" for c in shown[:3])
    first = shown[2]["in_training"][0]
    assert first["candidate"] == "C1" and first["family"] and first["change"] and first["name"]
    assert sum(f["in_training"] for f in shown[2]["families"]) == 2 and not any(f["scored"] for f in shown[2]["families"])
    last = shown[-1]["families"]
    assert all(set(f) == {"family", "designs", "scored", "failed", "in_training", "best"} for f in last)
    assert all(f["designs"] >= f["scored"] + f["failed"] + f["in_training"] for f in last)
    assert sum(f["scored"] for f in last) >= 3


def test_a_family_whose_designs_all_failed_is_still_a_family_tried(tmp_path):
    folder = search(tmp_path, budget__evaluations=3, budget__max_uncounted_failures=0, compute__gpus=1,
                    run_command="exit 3", **QUIET)
    recorder = Recorder(folder)
    Controller(folder, "t", poll=0.2, agent_backend=recorder).run(max_seconds=120)
    shown = [context for role, context in recorder.seen if role == "writer"]
    assert len(shown) >= 2
    assert sum(f["failed"] for f in shown[-1]["families"]) == len(shown) - 1 and not shown[-1]["in_training"]


def test_new_families_are_written_in_turn_only_while_training_is_slow_next_to_writing(tmp_path):
    folder = search(tmp_path, budget__evaluations=3, compute__gpus=1, **QUIET)
    controller, _ = run(folder)
    view = controller.view()
    took = sorted(r["ended"] - r["running_since"] for r in view.runs.values() if r["performance"].get("status") in SCORED)
    assert took and controller.state["write_seconds"]
    controller.state["write_seconds"] = [took[len(took) // 2] / 100.0]          # a run takes a hundred writer calls
    assert controller.one_new_at_a_time(view)
    controller.state["write_seconds"] = [took[len(took) // 2]]                  # a run takes as long as one writer call
    assert not controller.one_new_at_a_time(view)
    controller.state["write_seconds"] = []                                      # nothing measured yet: in turn
    assert controller.one_new_at_a_time(view)


def test_labels_for_one_family_can_be_merged(tmp_path):
    folder = search(tmp_path, budget__evaluations=8, compute__gpus=2, **QUIET)
    controller, _ = run(folder)
    view = controller.view()
    used = sorted({m["family"] for m in view.models.values()})
    assert len(used) >= 2 and all(f == spelled(f) for f in used)
    first, second = used[0], used[1]
    before = sum(1 for m in view.models.values() if m["family"] in (first, second))
    assert audit.merge_families(controller.store, view, ["no such family", first], None, "Ada") == "name at least two family labels in use"

    class Analyst:      # an analyst who says the two labels are one family
        def call(self, role, context, about=None):
            assert {"family": first, "designs": sum(1 for m in view.models.values() if m["family"] == first)} in context["families"]
            return {"lessons": [], "questions": [], "same_family": [{"labels": [first, second], "keep": first}], "_call": "c9"}
    assert audit.analyse(controller.store, Analyst(), controller.designer, view, controller.settings, 0)
    again = Controller(folder, "t", poll=0.2).view()
    assert second not in {m["family"] for m in again.models.values()}
    assert sum(1 for m in again.models.values() if m["family"] == first) == before
    assert {c["family"] for c in again.cands.values() if c["family"]} == {m["family"] for m in again.models.values()}
    merged = {old: row["as"] for old, row in controller.store.merged("families").items()}
    assert merged == {second: first}
    assert same_family(second.replace("-", " ").title(), sorted({m["family"] for m in again.models.values()}), merged) == first
