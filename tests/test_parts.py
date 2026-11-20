"""The parts on their own: the schedule, the strategies' rules, the search space."""
import copy
import random

import pytest

from evoloop import form, schedule, space, strategies
from evoloop.store import View
from evoloop.strategies import lineage as lineage_rules


def settings(**changes):
    s = copy.deepcopy(form.DEFAULTS)
    s["objective"]["direction"] = "maximize"
    s["evaluation"]["noise"] = 0.01
    s["budget"]["evaluations"] = 100
    s["_period"] = 0
    for key, value in changes.items():
        form.put(s, key.replace("__", "."), value)
    return s


def make_view(rows, noise=0.01):
    """rows: (id, lineage, mode, parent, score, family). One candidate per run."""
    runs, models = {}, {}
    for index, (rid, lin, mode, parent, score, family) in enumerate(rows):
        models["M" + rid] = {"id": "M" + rid, "family": family}
        runs[rid] = {"id": rid, "candidate": "C" + rid[1:], "model": "M" + rid, "recipe": "T1", "purpose": "search",
                     "period": 0, "seed": 0, "t": index, "ended": index,
                     "history": {"lineage": lin, "mode": mode, "move": "x", "parent": parent, "phase": 0},
                     "performance": {"status": "done", "score": score} if score is not None else {"status": "running"}}
    return View(runs, models, {}, "maximize", noise, 0)


def test_the_realised_mix_follows_the_shares_by_counting():
    s = settings(schedule__phases=[{"until": 1.0, "new": 0.5, "cross": 0.2, "local": 0.3}], schedule__novel_share=0.0)
    rows = [("R1", "L1", "new", None, 0.5, "a"), ("R2", "L2", "new", None, 0.6, "b"), ("R3", "L3", "new", None, 0.4, "c")]
    counts = {m: 0 for m in form.MODES}
    for i in range(40):
        view = make_view(rows)
        mode = schedule.next_mode(view, s)
        counts[mode] += 1
        rows.append(("R%d" % (len(rows) + 1), "L%d" % (i % 3 + 1), mode, None, 0.5, "a"))
    assert counts["novel"] == 0
    assert abs(counts["new"] - 20) <= 3 and abs(counts["cross"] - 8) <= 2 and abs(counts["local"] - 12) <= 3, counts


def test_phases_switch_at_the_share_of_the_budget():
    s = settings()
    early = schedule.shares(make_view([("R%d" % i, "L1", "new", None, 0.5, "a") for i in range(1, 30)]), s)
    late = schedule.shares(make_view([("R%d" % i, "L1", "new", None, 0.5, "a") for i in range(1, 80)]), s)
    assert round(early["new"] + early["novel"], 2) == 0.65 and early["cross"] == 0.10 and early["local"] == 0.25
    assert round(late["new"] + late["novel"], 2) == 0.15 and late["cross"] == 0.25 and late["local"] == 0.60


def test_a_mode_with_nothing_to_do_passes_its_share_on():
    s = settings()
    assert schedule.next_mode(make_view([]), s) == "new"                      # nothing scored: only new designs
    one = make_view([("R1", "L1", "new", None, 0.5, "a")])
    assert not schedule.available(one, s)["cross"] and not schedule.available(one, s)["novel"]


def test_credit_goes_back_to_the_slot_that_founded_the_lineage():
    view = make_view([("R1", "L1", "new", None, 0.50, "a"), ("R2", "L2", "novel", None, 0.48, "b"),
                      ("R3", "L2", "local", "R2", 0.60, "b")])
    got = schedule.credit(view)
    assert got["local"]["gain"] == got["novel"]["gain"] == pytest.approx(5.0)   # ten noise floors, shared
    assert got["new"]["gain"] == 0


def test_adaptive_shares_keep_a_floor():
    rows = [("R1", "L1", "new", None, 0.5, "a")]
    for i in range(2, 30):
        rows.append(("R%d" % i, "L1", "local", "R%d" % (i - 1), 0.5 + 0.02 * i, "a"))
    s = settings(schedule__adaptive=1.0, schedule__floor=0.05, schedule__founder_credit=0.0)
    shares = schedule.shares(make_view(rows), s)
    assert abs(sum(shares.values()) - 1.0) < 1e-6 and min(shares.values()) >= 0.05
    assert shares["local"] == max(shares.values())          # with no credit to the founder, what gained gets more
    # With the founder credited, the one new design that everything was built on is worth more than a local move.
    s = settings(schedule__adaptive=1.0, schedule__floor=0.05, schedule__founder_credit=0.5)
    shares = schedule.shares(make_view(rows), s)
    assert shares["new"] == max(shares.values()) and min(shares.values()) >= 0.05
    # At adaptive 0 the schedule is exactly the brief's.
    assert schedule.shares(make_view(rows), settings())["local"] == 0.25


def test_lineage_rules_trial_active_bench_retired():
    rows = [("R1", "L1", "new", None, 0.50, "a"), ("R2", "L1", "local", "R1", 0.52, "a"),
            ("R3", "L2", "new", None, 0.40, "b"),                                 # one run: still in trial
            ("R4", "L3", "new", None, 0.45, "c"), ("R5", "L3", "local", "R4", 0.451, "c"),
            ("R6", "L3", "local", "R5", 0.452, "c"), ("R7", "L3", "local", "R6", 0.449, "c"),
            ("R8", "L4", "new", None, 0.30, "d"), ("R9", "L4", "local", "R8", 0.33, "d")]
    s = settings(population__trial_runs=2, population__retire_after=3, population__lineages=1)
    state = lineage_rules.state(make_view(rows), s)
    assert state["L1"]["state"] == "active" and state["L2"]["state"] == "trial"
    assert state["L3"]["state"] == "retired" and state["L4"]["state"] == "bench"
    request = lineage_rules.Lineage().choose(make_view(rows), "local", s, random.Random(0))
    assert request["purpose"] == "trial" and request["lineage"] == "L2"           # the trial is served first


def test_no_lineage_takes_more_than_its_quota():
    rows = [("R1", "L1", "new", None, 0.60, "a"), ("R2", "L1", "local", "R1", 0.62, "a"),
            ("R3", "L2", "new", None, 0.50, "b"), ("R4", "L2", "local", "R3", 0.52, "b")]
    s = settings(population__trial_runs=2, population__quota=0.5, population__retire_after=99)
    strategy, rng = lineage_rules.Lineage(), random.Random(1)
    for i in range(30):
        request = strategy.choose(make_view(rows), "local", s, rng)
        rows.append(("R%d" % (len(rows) + 1), request["lineage"], "local", "R1", 0.5, "a"))
    local = [r for r in rows if r[2] == "local"]
    share = sum(1 for r in local if r[1] == "L1") / len(local)
    assert 0.35 <= share <= 0.65, share


@pytest.mark.parametrize("mechanism", form.MECHANISMS)
def test_every_strategy_answers_every_mode(mechanism):
    rows = [("R%d" % i, "L%d" % (i % 4 + 1), "new" if i < 5 else "local", None, 0.4 + 0.01 * i, "f%d" % (i % 3))
            for i in range(1, 13)]
    s = settings(strategy__mechanism=mechanism)
    strategy = strategies.make(s)
    view = make_view(rows)
    for mode in form.MODES:
        request = strategy.choose(view, mode, s, random.Random(3))
        assert request["mode"] in form.MODES and request["why"]
        if request["mode"] == "cross":
            assert len(set(request["parents"])) == 2
        if request["mode"] == "local":
            assert request["parents"][0] in view.cands
    assert strategy.population(view, s)


def test_the_space_presets_decide_which_blocks_are_open():
    blocks = {"stem": {"kind": "structure", "role": "stem", "content": ""},
              "trunk": {"kind": "structure", "role": "trunk", "content": ""},
              "loss": {"kind": "structure", "role": "loss", "content": ""},
              "fit": {"kind": "params", "role": "optimizer", "content": ""}}

    def opened(**changes):
        return set(space.open_blocks(blocks, settings(**changes)))
    assert opened(space__preset="settings_only") == {"fit"}
    assert opened(space__preset="module", space__modules=["trunk"]) == {"trunk", "fit"}
    assert opened(space__preset="open_architecture") == {"stem", "trunk", "fit"}
    assert opened(space__preset="architecture_and_recipe") == {"stem", "trunk", "loss", "fit"}
    assert opened(space__preset="custom", space__roles={"loss": "open"}) == {"loss", "fit"}
    assert opened(space__preset="open_architecture", space__roles={"stem": "fixed"}, space__settings="fixed") == {"trunk"}


def test_markers_parse_and_the_frozen_part_is_hashed(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    text = ("import x\n# EVOLVE-BLOCK-START name=net kind=structure role=trunk\nA = 1\n# EVOLVE-BLOCK-END\n"
            "# EVOLVE-BLOCK-START name=p kind=params\nP = {'lr': 0.1}\n# EVOLVE-BLOCK-END\nfrozen = 1\n")
    (base / "m.py").write_text(text)
    table = space.table(str(base))
    assert table["net"]["role"] == "trunk" and table["p"]["role"] == "settings" and table["net"]["content"] == "A = 1\n"
    before = space.frozen_hash(str(base))
    out = tmp_path / "work"
    space.materialize(str(base), None, {"net": "A = 2\n"}, str(out))
    assert "A = 2" in (out / "m.py").read_text() and "frozen = 1" in (out / "m.py").read_text()
    (base / "m.py").write_text(text.replace("A = 1", "A = 5"))
    assert space.frozen_hash(str(base)) == before          # a block's content is not part of the frozen hash
    (base / "m.py").write_text(text.replace("frozen = 1", "frozen = 2"))
    assert space.frozen_hash(str(base)) != before          # the frozen code is
    s = settings()
    assert space.check(table, {"net": "A = (\n"}, {"net": "structure"}, s) is not None
    assert space.check(table, {"p": "P = {'lr': [1]}\n"}, {"p": "params"}, s) is not None
    assert space.check(table, {"net": "A = 3\n"}, {}, s) == "block net is not open in this search"
