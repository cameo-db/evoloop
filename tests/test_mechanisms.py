"""The mechanisms taken from established methods: a promotion ladder, a trade-off front, behaviour groups, island resets."""
import random

from evoloop import estimate, form, strategies
from evoloop.controller import Controller
from evoloop.strategies import archive, pareto
from evoloop.strategies.islands import Islands
from evoloop.strategies.lineage import Lineage

from helpers import ask, search
from test_loop import drive, scored
from test_parts import make_view, settings


def with_figures(view, **by_run):
    """Set figures of the runs of a made-up view: parameters=..., signature=..., ended=..., designed=..., island=..."""
    for rid, figures in by_run.items():
        for key, value in figures.items():
            if key in ("island",):
                view.runs[rid]["history"][key] = value
            elif key in ("ended", "designed"):
                view.runs[rid][key] = value
            else:
                view.runs[rid]["performance"][key] = value
    return type(view)(view.runs, view.models, view.recipes, "maximize", view.noise, view.period)


# --- the promotion ladder -------------------------------------------------------------------------
def test_the_ladder_is_checked_and_its_average_cost_worked_out():
    assert form.check_value("evaluation.ladder", [{"at": 0.1, "keep": 0.5}, {"at": 0.3, "keep": 0.5}]) is None
    assert form.check_value("evaluation.ladder", [{"at": 0.3, "keep": 0.5}, {"at": 0.1, "keep": 0.5}]) is not None   # rising
    assert form.check_value("evaluation.ladder", [{"at": 1.5, "keep": 0.5}]) is not None
    assert form.check_value("evaluation.ladder", [{"at": 0.2}]) is not None
    assert form.check_change("evaluation.ladder", [{"at": 0.2, "keep": 0.5}]) is None                                # mid-run
    s = settings()
    assert form.rungs(s) == ([{"at": 0.5, "keep": 0.5}], False) and form.mean_charge(s) == 1.0
    s = settings(evaluation__ladder=[{"at": 0.1, "keep": 0.5}, {"at": 0.3, "keep": 0.5}])
    assert form.rungs(s)[1] is True
    assert abs(form.mean_charge(s) - (0.5 * 0.1 + 0.25 * 0.3 + 0.25)) < 1e-9
    plain, laddered = estimate.calls(settings()), estimate.calls(s)
    assert laddered["writer"][1] > 2.5 * plain["writer"][1]                 # more designs fit the budget, so more calls


def test_a_ladder_stops_the_weaker_designs_early_and_charges_them_a_share(tmp_path):
    folder = search(tmp_path, budget__evaluations=14, evaluation__allowance=400, audit__reviews="none",
                    harness__level="minimal", evaluation__screen_min_pool=3,
                    evaluation__ladder=[{"at": 0.1, "keep": 0.5}, {"at": 0.4, "keep": 0.5}])
    controller = Controller(folder, "t", poll=0.1)
    reason = controller.run(max_seconds=400)
    assert reason
    runs = [r for r in controller.view().runs.values() if r.get("purpose", "search") in ("search", "trial")]
    stopped = [r for r in runs if r.get("screened")]
    assert stopped, "the ladder stopped nothing"
    assert {r["screened"]["share"] for r in stopped} <= {0.1, 0.4}
    assert all(abs(r["charge"] - r["screened"]["share"]) < 1e-9 for r in stopped)
    ended = [r for r in runs if r["performance"].get("status") in ("done", "stopped_early")]
    assert len(ended) > 14                                    # the budget of 14 full runs covered more designs
    assert set(controller.state["screen"]) <= {"0.1", "0.4"}


# --- the trade-off front --------------------------------------------------------------------------
FRONT = [("R1", "L1", "new", None, 0.60, "a"), ("R2", "L2", "new", None, 0.55, "b"), ("R3", "L3", "new", None, 0.50, "c"),
         ("R4", "L4", "new", None, 0.52, "d"), ("R5", "L5", "new", None, 0.40, "e"), ("R6", "L6", "new", None, 0.58, "f")]
SIZES = {"R1": 900, "R2": 400, "R3": 100, "R4": 500, "R5": 300, "R6": None}


def front_view():
    return with_figures(make_view(FRONT), **{rid: {"parameters": size} for rid, size in SIZES.items()})


def test_the_front_holds_the_designs_nothing_else_beats_on_both_counts():
    view = front_view()
    s = settings(strategy__mechanism="pareto", strategy__second_metric="parameters")
    layers = pareto.fronts(view, s)
    name = lambda layer: sorted(view.run_of(p[0])["id"] for p in layer)    # noqa: E731
    assert name(layers[0]) == ["R1", "R2", "R3"]            # best score, the middle, and the smallest
    assert "R4" in name(layers[1]) and "R5" in name(layers[1])   # R2 is better and smaller than R4; R3 than R5
    assert "R6" in name(layers[1])                           # no size reported: worst on size, and R1 scores higher
    chooser = strategies.make(s)
    assert chooser.name == "pareto"
    rng = random.Random(0)
    drawn = {view.run_of(chooser.choose(view, "local", s, rng)["parents"][0])["id"] for _ in range(60)}
    assert drawn == {"R1", "R2", "R3"}                       # parents come from the front only
    pair = chooser.choose(view, "cross", s, rng)
    a, b = (view.run_of(p)["id"] for p in pair["parents"])
    assert {a, b} <= {"R1", "R2", "R3"} and a != b and (a == "R2" or {a, b} == {"R1", "R3"})   # the far end of the front
    rows = chooser.population(view, s)
    assert [r["front"] for r in rows][:3] == [1, 1, 1] and "parameters" in rows[0]
    more = settings(strategy__mechanism="pareto", strategy__second_metric="parameters", strategy__second_direction="maximize")
    assert sorted(view.run_of(p[0])["id"] for p in pareto.fronts(view, more)[0]) == ["R1"]   # the largest also scores best


def test_without_a_second_figure_the_front_is_the_best_design_and_the_plan_says_so():
    view = front_view()
    s = settings(strategy__mechanism="pareto")
    assert [view.run_of(p[0])["id"] for p in pareto.fronts(view, s)[0]] == ["R1"]
    assert any("second_metric" in w for w in form.warnings(s))
    assert strategies.make(s).choose(view, "local", s, random.Random(1))["parents"]


def test_a_search_runs_on_the_trade_off_front(tmp_path):
    folder = search(tmp_path, budget__evaluations=12, evaluation__allowance=150, audit__reviews="none",
                    harness__level="minimal", strategy__mechanism="pareto", strategy__second_metric="parameters")
    controller = Controller(folder, "t", poll=0.1)
    assert controller.run(max_seconds=300)
    assert len(scored(controller.view())) >= 8
    assert any("trade-off front" in str(r["history"].get("why_this_slot")) for r in controller.view().runs.values())


# --- behaviour ------------------------------------------------------------------------------------
ROWS = [("R1", "L1", "new", None, 0.60, "a"), ("R2", "L2", "new", None, 0.55, "a"), ("R3", "L3", "new", None, 0.50, "a"),
        ("R4", "L4", "new", None, 0.45, "a")]
SIGS = {"R1": [1.0, 2.0, 3.0, 4.0], "R2": [1.1, 2.0, 3.1, 4.2], "R3": [4.0, 3.0, 2.0, 1.0], "R4": None}


def test_designs_are_grouped_by_what_the_trained_model_does():
    view = with_figures(make_view(ROWS), **{rid: {"signature": sig} for rid, sig in SIGS.items()})
    s = settings(strategy__mechanism="archive", strategy__descriptors=["behaviour"])
    groups = {view.run_of(c)["id"]: g for c, g in strategies.behaviour_groups(view, s).items()}
    assert groups["R1"] == groups["R2"] and groups["R3"] != groups["R1"] and groups["R4"] is None
    cells = archive.cells(view, s)
    assert len(cells) == 3                                  # same family and code size or not, behaviour splits them
    elites = {view.run_of(c["elite"])["id"] for c in cells.values()}
    assert elites == {"R1", "R3", "R4"}                     # R2 behaves like R1 and scores lower
    assert any("signature" in w for w in form.warnings(s))


def test_a_novel_slot_is_shown_designs_that_behave_unlike_the_leader():
    view = with_figures(make_view(ROWS), **{rid: {"signature": sig} for rid, sig in SIGS.items()})
    leader = view.best()["id"]
    count = {"auto": {}, "code": {}}
    for measure in count:
        s = settings(schedule__novelty_measure=measure)
        rng = random.Random(3)
        for _ in range(400):
            pick = view.run_of(strategies.inspirations(view, [leader], 1, rng, s)[0])["id"]
            count[measure][pick] = count[measure].get(pick, 0) + 1
    assert count["auto"]["R3"] > 4 * count["auto"]["R2"]        # the opposite behaviour far more often than the same
    assert count["code"]["R3"] < 2 * count["code"]["R2"]        # by code alone they are as likely


# --- island resets --------------------------------------------------------------------------------
def island_view():
    rows = [("R%d" % i, "L%d" % i, "new", None, score, "f%d" % i) for i, score in
            enumerate([0.50, 0.30, 0.52, 0.31, 0.54, 0.32], start=1)]
    figures = {"R%d" % i: {"island": (i - 1) % 2, "designed": float(i), "ended": float(i) + 0.5} for i in range(1, 7)}
    return with_figures(make_view(rows), **figures)


def test_the_weaker_islands_start_again_from_the_best_of_one_that_was_kept():
    view = island_view()                       # island 0 holds R1, R3, R5 (the better ones); island 1 holds R2, R4, R6
    isles = Islands(Lineage(), 2)
    off = settings(strategy__islands=2)
    assert all(when == float("-inf") for when in isles.began(view, off).values())
    assert len(isles.sub(view, 1, isles.began(view, off)).runs) == 3
    on = settings(strategy__islands=2, strategy__reset_every=6)
    began = isles.began(view, on)
    assert began[0] == float("-inf") and began[1] == 6.5        # the sixth scored run ended at 6.5: island 1 is reset
    assert not isles.sub(view, 1, began).runs and len(isles.sub(view, 0, began).runs) == 3
    assert [row.get("reset") for row in isles.population(view, on)] == [None, True]
    # Island 1 has the fewest runs counted to it? Both have three, so the tie goes to island 0; add one to it.
    more = with_figures(make_view([(r["id"], r["history"]["lineage"], "new", None, r["performance"]["score"], "x")
                                   for r in view.runs.values()] + [("R7", "L7", "new", None, 0.2, "g")]),
                        **dict({rid: {"island": r["history"]["island"], "designed": r["designed"], "ended": r["ended"]}
                                for rid, r in view.runs.items()}, R7={"island": 0, "designed": 7.0, "ended": 7.5}))
    request = isles.choose(more, "local", on, random.Random(0))
    assert request["island"] == 1 and request["migrant"] and "was reset" in request["why"]
    assert more.run_of(request["parents"][0])["id"] == "R5"     # the best of the island that was kept
    assert isles.choose(more, "new", on, random.Random(0))["migrant"]           # whatever the slot, the island is founded first
    # A design made on island 1 after the reset belongs to its new population.
    later = with_figures(more, R7={"island": 1, "designed": 7.0, "ended": 7.5})
    assert [r["id"] for r in isles.sub(later, 1, isles.began(later, on)).runs.values()] == ["R7"]
    assert any("reset_every" in w for w in form.warnings(settings(strategy__reset_every=10)))


def test_a_search_with_island_resets_runs_to_its_end(tmp_path):
    folder = search(tmp_path, budget__evaluations=16, evaluation__allowance=150, audit__reviews="none",
                    harness__level="minimal", strategy__islands=2, strategy__reset_every=5)
    controller = Controller(folder, "t", poll=0.1)
    assert controller.run(max_seconds=300)
    runs = controller.view().runs.values()
    assert len(scored(controller.view())) >= 10
    assert any("was reset" in str(r["history"].get("why_this_slot")) for r in runs)
    assert all(r.get("designed") for r in runs)


def test_an_island_is_founded_once_after_a_reset():
    view = island_view()
    isles = Islands(Lineage(), 2)
    on = settings(strategy__islands=2, strategy__reset_every=6)
    rows = [(r["id"], r["history"]["lineage"], "new", None, r["performance"]["score"], "x") for r in view.runs.values()]
    figures = {rid: {"island": r["history"]["island"], "designed": r["designed"], "ended": r["ended"]}
               for rid, r in view.runs.items()}
    seeded = with_figures(make_view(rows + [("R7", "L7", "local", "R5", None, "g")]),
                          **dict(figures, R7={"island": 1, "designed": 7.0}))
    seeded.runs["R7"]["history"]["migrant"] = True          # the founding design is still training
    busy = dict(on, _designing=[{"mode": "new", "island": 0}] * 2)            # so the next slot goes to island 1
    request = isles.choose(seeded, "new", busy, random.Random(0))
    assert request["island"] == 1 and not request.get("migrant") and request["mode"] == "new"
