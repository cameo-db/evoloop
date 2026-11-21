"""The agent side of the established methods: several models writing, find-and-replace edits, approaches that are
kept or dropped by their record, and a child starting from its parent's weights."""
import os
import random

from evoloop import approaches, estimate, form
from evoloop.agents import Agents, _BackendConfig
from evoloop.controller import Controller
from evoloop.design import Designer
from evoloop.store import Store

from helpers import search
from test_loop import scored
from test_parts import make_view, settings

QUIET = dict(evaluation__allowance=150, audit__reviews="none", harness__level="standard")


# --- several models write -------------------------------------------------------------------------
class Recorder:
    """A backend that notes which model and effort each call would have been sent to."""

    def __init__(self):
        self.seen, self.cfg = [], None

    def call(self, role, system, user, schema, context):
        self.seen.append((role, self.cfg.model_for(role), self.cfg.effort_for(role)))
        reply = {"reasoning": "r", "note": "n", "proposals": []} if role == "writer" else \
            {"reasoning": "r", "note": "n", "lessons": [], "questions": []}
        return reply, {"cost_usd": 0.0, "model": self.cfg.model_for(role)}


def test_writer_calls_are_shared_between_models_by_counting(tmp_path):
    mix = [{"model": "big", "share": 0.75}, {"model": "small", "share": 0.25, "effort": "low"}]
    assert form.check_value("agents.writer_mix", mix) is None and form.check_change("agents.writer_mix", mix) is None
    assert form.check_value("agents.writer_mix", [{"model": "big"}]) is not None
    assert form.check_value("agents.writer_mix", [{"model": "big", "share": 1, "temperature": 2}]) is not None
    s = settings(agents__writer_mix=mix, agents__backend="stub", agents__default_model="usual")
    store = Store(str(tmp_path))
    backend = Recorder()
    agents = Agents(s, str(tmp_path), store, backend=backend)
    backend.cfg = _BackendConfig(agents.holder, str(tmp_path))
    for _ in range(12):
        agents.call("writer", {})
    agents.call("analyst", {})
    writers = [(model, effort) for role, model, effort in backend.seen if role == "writer"]
    assert [m for m, _ in writers].count("big") == 9 and [m for m, _ in writers].count("small") == 3
    assert set(writers) == {("big", "high"), ("small", "low")}        # the entry's effort, else the writer's own
    assert backend.seen[-1][1] == "usual"                               # other roles are untouched
    assert backend.cfg.model_for("writer") == "usual"                   # and nothing is left behind after a call
    assert [c.get("drawn_model") for c in store.read("calls")].count("small") == 3
    # A controller that starts again goes on counting from the record.
    again = Agents(s, str(tmp_path), store, backend=backend)
    assert again.mixed == {"big": 9, "small": 3}
    # The estimate prices an average writer call by the shares.
    priced = settings(agents__writer_mix=[{"model": "a", "share": 1}, {"model": "b", "share": 3}],
                      agents__prices={"a": {"input": 4.0, "output": 40.0}, "b": {"input": 0.0, "output": 0.0}})
    assert estimate.price_of(priced, "writer") == {"input": 1.0, "output": 10.0}


def test_a_search_with_two_writer_models_reports_them_side_by_side(tmp_path):
    folder = search(tmp_path, budget__evaluations=10, agents__writer_mix=[{"model": "m-one", "share": 0.5},
                                                                         {"model": "m-two", "share": 0.5}], **QUIET)
    controller = Controller(folder, "t", poll=0.1)
    assert controller.run(max_seconds=300)
    with open(os.path.join(folder, "runs", "t", "report.md"), encoding="utf-8") as handle:
        text = handle.read()
    assert "## Writers by model" in text and "m-one" in text and "m-two" in text
    assert len(scored(controller.view())) >= 6


# --- find-and-replace edits -----------------------------------------------------------------------
def test_an_edit_applies_only_where_its_text_occurs_exactly_once():
    source = {"model": "a = 1\nb = 2\nc = 1\n", "fit": "X = {'lr': 0.1}\n"}
    change = lambda *edits, **blocks: Designer.changed({"edits": list(edits), "blocks": blocks or None}, source)   # noqa: E731
    out, fault = change({"block": "model", "find": "b = 2", "replace": "b = 3"})
    assert fault is None and out == {"model": "a = 1\nb = 3\nc = 1\n"}
    out, fault = change({"block": "model", "find": "b = 2", "replace": "b = 3"}, {"block": "model", "find": "b = 3", "replace": "b = 4"})
    assert fault is None and out["model"].count("b = 4") == 1                   # edits to one block apply in order
    assert "occurs 2 times" in change({"block": "model", "find": " = 1", "replace": " = 5"})[1]
    assert "occurs 0 times" in change({"block": "model", "find": "zzz", "replace": "y"})[1]
    assert "occurs 0 times" in change({"block": "model", "find": "", "replace": "y"})[1]
    assert "does not exist" in change({"block": "nope", "find": "a", "replace": "b"})[1]
    assert "must give" in change({"block": "model", "find": 3})[1]
    assert "must give" in change("not an edit")[1]
    out, fault = change({"block": "fit", "find": "0.1", "replace": "0.2"}, model="whole new model\n")
    assert fault is None and out == {"model": "whole new model\n", "fit": "X = {'lr': 0.2}\n"}   # blocks and edits together
    assert Designer.changed({"blocks": ["not", "a", "dict"], "edits": "nor this"}, source) == ({}, None)


def test_a_search_whose_writers_return_edits(tmp_path):
    folder = search(tmp_path, budget__evaluations=14, variation__edit_format="diff", **QUIET)
    controller = Controller(folder, "t", poll=0.1)
    assert controller.run(max_seconds=300)
    runs = list(controller.view().runs.values())
    edited = [r for r in runs if r["history"].get("edits")]
    assert edited and all(r["history"]["mode"] == "local" for r in edited)       # a new design has nothing to edit
    assert any(r["performance"].get("status") == "done" for r in edited)         # and the edited designs train
    full, diff = settings(), settings(variation__edit_format="diff")
    size = {"structure": 4000.0, "params": 400.0, "blocks": 1.0, "task": 2000.0}
    assert estimate.tokens(diff, size)["writer"][1] < estimate.tokens(full, size)["writer"][1]


# --- approaches -----------------------------------------------------------------------------------
ROWS = [("R1", "L1", "new", None, 0.50, "a"), ("R2", "L1", "local", "R1", 0.60, "a"), ("R3", "L1", "local", "R1", 0.50, "a"),
        ("R4", "L1", "local", "R1", 0.62, "a"), ("R5", "L1", "local", "R1", 0.49, "a"), ("R6", "L1", "local", "R1", None, "a"),
        ("R7", "L1", "local", "R1", 0.48, "a"), ("R8", "L1", "local", "R1", 0.47, "a")]
UNDER = {"R2": "P1", "R3": "none", "R4": "P1", "R5": "P2", "R6": "P2", "R7": "P2", "R8": "P2"}


def approach_view():
    view = make_view(ROWS)
    for rid, key in UNDER.items():
        view.runs[rid]["history"]["approach"] = key
    return view


def test_the_record_of_an_approach_is_the_share_of_its_designs_that_beat_their_parent(tmp_path):
    store, view = Store(str(tmp_path)), approach_view()
    s = settings(variation__approaches="evolve", variation__approach_pool=2,
                 variation__approach_seeds=["Change the widest layer first.", "Change the widest layer first."])
    approaches.sync(store, s)
    approaches.sync(store, s)
    assert [a["id"] for a in approaches.active(store)] == ["P1"]              # entered once, however often it is read
    store.append("approaches", {"id": "P2", "text": "Add depth.", "by": "analyst", "status": "active"})
    rows = approaches.record(store, view)
    assert (rows["P1"]["designs"], rows["P1"]["finished"], rows["P1"]["win_rate"]) == (2, 2, 1.0)
    assert (rows["P2"]["designs"], rows["P2"]["finished"], rows["P2"]["win_rate"]) == (4, 3, 0.0)   # one still trains
    assert (rows["none"]["designs"], rows["none"]["win_rate"]) == (1, 0.0)
    picks = [(approaches.pick(store, view, s, random.Random(i)) or {"id": "none"})["id"] for i in range(40)]
    assert set(picks) == {"P1"}                           # what has paid, at equal trying, is drawn
    # A full pool: the analyst's worst proven approach makes way for a new one; the person's own never does.
    assert approaches.add(store, view, s, [{"text": "Try residual connections."}], "A9") == ["P3"]
    state = {a["id"]: a["status"] for a in store.merged_list("approaches")}
    assert state == {"P1": "active", "P2": "retired", "P3": "active"}
    assert (approaches.pick(store, view, s, random.Random(0)) or {})["id"] == "P3"       # an untried approach goes first
    assert approaches.add(store, view, s, ["Try residual connections."]) == []           # nothing twice
    assert approaches.add(store, view, s, ["Yet another way."]) == []                    # nothing proven is left to retire
    assert approaches.add(store, view, settings(variation__approaches="fixed"), ["A way."]) == []   # fixed: yours only
    assert any(r["approach"] == "P2" and r["status"] == "retired" for r in approaches.table(store, view))
    assert any("approach_seeds" in w for w in form.warnings(settings(variation__approaches="fixed")))


def test_a_search_hands_out_approaches_and_the_analyst_adds_one(tmp_path):
    folder = search(tmp_path, budget__evaluations=24, variation__approaches="evolve", harness__analyst_every=4,
                    variation__approach_seeds=["Prefer forms with few constants."], **QUIET)
    controller = Controller(folder, "t", poll=0.1)
    assert controller.run(max_seconds=400)
    known = {a["id"]: a for a in controller.store.merged_list("approaches")}
    assert known["P1"]["by"] == "person" and any(a["by"] == "analyst" for a in known.values())
    used = {r["history"].get("approach") for r in controller.view().runs.values()} - {None}
    assert "none" in used and "P1" in used and len(used) >= 3                 # with and without, and the analyst's too
    with open(os.path.join(folder, "runs", "t", "report.md"), encoding="utf-8") as handle:
        assert "## Approaches handed to the writers" in handle.read()
    assert len(scored(controller.view())) >= 12


# --- a child starts from its parent's weights ---------------------------------------------------------
def test_a_child_is_handed_its_parents_checkpoints_when_asked(tmp_path, monkeypatch):
    assert form.starts_period("evaluation.inherit_weights")            # it changes what a score means
    assert any("keep_checkpoints" in w for w in form.warnings(settings(evaluation__inherit_weights=True)))
    folder = search(tmp_path, budget__evaluations=10, evaluation__inherit_weights=True, evaluation__keep_checkpoints=True, **QUIET)
    controller = Controller(folder, "t", poll=0.1)
    handed = {}
    submit = controller.backend.submit

    def watch(run, work, env, settings):
        handed[run["id"]] = env.get("EVO_PARENT_CHECKPOINT_DIR")
        return submit(run, work, env, settings)
    monkeypatch.setattr(controller.backend, "submit", watch)
    assert controller.run(max_seconds=300)
    runs = controller.view().runs
    children = [r for r in runs.values() if r["history"].get("parent") and r.get("purpose", "search") in ("search", "trial")]
    assert children
    for child in children:
        parent = runs[child["history"]["parent"]]
        assert handed[child["id"]] == controller.checkpoint_dir(parent) and os.path.isdir(handed[child["id"]])
    assert all(handed[r["id"]] is None for r in runs.values() if not r["history"].get("parent"))
