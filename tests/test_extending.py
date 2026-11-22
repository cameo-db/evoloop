"""The extension points that docs/extending.md shows: settings of your own, and a strategy written as a class."""
import random

import yaml

from evoloop import form, strategies
from evoloop.controller import Controller

from helpers import search
from test_loop import drive, scored


class Uniform:
    """The example strategy of docs/extending.md: every parent is drawn at random from the scored designs."""
    name = "uniform"

    def population(self, view, settings):
        return [{"candidate": c["id"], "score": view.display(c["value"]), "family": c["family"]}
                for c in view.scored()[:5]]

    def choose(self, view, mode, settings, rng):
        scored_ = [c["id"] for c in view.scored()]
        if mode == "local" and scored_:
            parent = rng.choice(scored_)
            return {"mode": "local", "lineage": view.cands[parent]["lineage"], "parents": [parent],
                    "step": "normal", "why": "a design drawn at random"}
        if mode == "cross" and len(scored_) >= 2:
            first, second = rng.sample(scored_, 2)
            return {"mode": "cross", "lineage": view.cands[first]["lineage"], "parents": [first, second],
                    "why": "two designs drawn at random"}
        return {"mode": "new", "lineage": None, "parents": [], "why": "a new design"}


def test_a_strategy_written_as_a_class_runs_a_search(tmp_path, monkeypatch):
    monkeypatch.setattr(strategies, "make", lambda settings: Uniform())
    folder = search(tmp_path, budget__evaluations=10, evaluation__allowance=150, audit__reviews="none", strategist__mode="off")
    controller = Controller(folder, "t", poll=0.1)
    drive(controller, lambda v: len(scored(v)) >= 6)
    view = controller.view()
    moves = {r["history"].get("mode") for r in view.runs.values()}
    assert len(scored(view)) >= 6 and "local" in moves                      # parents came from the class, and were built on


def test_the_settings_shown_for_a_schedule_and_metrics_of_your_own_are_accepted():
    shown = yaml.safe_load("""
run: {type: custom, description: "Explore briefly, cross the leaders, then refine."}
schedule:
  phases:
    - {until: 0.2, new: 0.80, cross: 0.00, local: 0.20}
    - {until: 0.5, new: 0.20, cross: 0.50, local: 0.30}
    - {until: 1.0, new: 0.05, cross: 0.15, local: 0.80}
strategy: {mechanism: pareto, second_metric: energy_joules, second_direction: minimize}
""")
    for path, value in form.flatten(shown).items() if hasattr(form, "flatten") else []:
        pass
    assert form.check_value("schedule.phases", shown["schedule"]["phases"]) is None
    assert form.check_value("strategy.second_metric", "energy_joules") is None
    assert form.check_value("strategy.descriptors", ["receptive_field"]) is None
    brief = {"objective": {"goal": "better", "direction": "maximize"}, "budget": {"evaluations": 100}}
    brief.update(shown)
    settings, _ = form.resolve(brief)
    assert settings["run"]["type"] == "custom" and len(settings["schedule"]["phases"]) == 3
    assert settings["strategy"]["mechanism"] == "pareto" and settings["strategy"]["second_metric"] == "energy_joules"
