"""What an outside review of version 0.2 found: a limit that could go unmeasured, a plan that hid what would
actually run, and part-way scores ranked beside full-length ones."""
import os

from evoloop import form, report
from evoloop.controller import Controller

from helpers import ask, search
from test_loop import scored
from test_parts import make_view

SMALL = dict(evaluation__allowance=150, audit__reviews="none", harness__level="minimal")


# --- a limit on a figure the adapter does not report --------------------------------------------------
def test_a_limit_that_cannot_be_checked_stops_the_run_instead_of_being_skipped(tmp_path):
    folder = search(tmp_path, budget__evaluations=8, limits={"examples_per_s": {"min": 100}}, **SMALL)
    controller = Controller(folder, "t", poll=0.1)
    reason = controller.run(max_seconds=200)
    assert reason.startswith("paused: limits name examples_per_s"), reason
    assert "result.json" in reason and "remove the limit" in reason              # it says what to do
    runs = list(controller.view().runs.values())
    assert not scored(controller.view())                                         # nothing unverified got a score
    ended = [r for r in runs if r["performance"].get("status") == "invalid"]
    assert ended and all(r["performance"].get("rejected") and "cannot be checked" in r["performance"]["reason"] for r in ended)
    assert len(runs) <= 4                                                        # it stopped at once, not after the budget
    # Taking the limit away (or reporting the figure) lets the run go on.
    ask(folder, "t", {"kind": "set", "changes": {"limits": {}}, "by": "Ada"})
    again = Controller(folder, "t", poll=0.1)
    assert not again.run(max_seconds=200).startswith("paused")
    assert len(scored(again.view())) >= 6
    assert any("is rejected and the run pauses" in line for line in form.at_a_glance(controller.settings))


def test_a_limit_on_a_reported_figure_still_works(tmp_path):
    folder = search(tmp_path, budget__evaluations=8, limits={"parameters": {"max": 1000}}, **SMALL)
    controller = Controller(folder, "t", poll=0.1)
    assert not controller.run(max_seconds=200).startswith("paused")
    assert len(scored(controller.view())) >= 6


# --- the plan says what will actually run -------------------------------------------------------------
BRIEF = {"objective": {"goal": "better", "direction": "maximize"}, "budget": {"evaluations": 60, "model_dollars": 20},
         "evaluation": {"allowance": 10, "noise": 0.01}, "agents": {"backend": "anthropic_api"}}


def plan(**answers):
    brief = {k: dict(v) for k, v in BRIEF.items()}
    for key, value in answers.items():
        form.put(brief, key.replace("__", "."), value)
    return form.resolve(brief)[0], form.plan_lines(brief, cost=["", "What the agents will cost: (estimate)"])


def test_a_skill_that_searches_without_agents_stays_without_agents_under_any_autonomy():
    for level in (None, "harnessed", "guided", "agentic"):
        settings, lines = plan(run__type="settings_only", run__skill="settings-tuning", harness__autonomy=level)
        assert settings["variation"]["settings_by"] == "tpe", level
        text = "\n".join(lines)
        assert "every move is made by a Bayesian estimator in code (tpe; no agent call)" in text, level
        assert "none: this search calls no agent" in text, level
    _, lines = plan(run__type="settings_only", run__skill="settings-tuning", harness__autonomy="guided")
    assert any(line.startswith("  Kept:") and "variation.settings_by stays 'tpe'" in line and "autonomy guided asks for 'agent'" in line
               for line in lines)
    # Setting it yourself still wins, and the plan says that the skill's own choice was changed.
    settings, lines = plan(run__type="settings_only", run__skill="settings-tuning", variation__settings_by="agent")
    assert settings["variation"]["settings_by"] == "agent"
    assert any(line.startswith("  Changed:") and "variation.settings_by is 'agent' (you set it)" in line for line in lines)
    assert any("every move is made by an agent" in line for line in lines)


def test_the_plan_leads_with_what_the_search_will_do_then_warnings_then_cost_then_every_setting():
    settings, lines = plan(run__type="explore_then_exploit", run__skill="model-efficiency", strategy__islands=2)
    text = "\n".join(lines)
    order = [text.index(part) for part in ("At a glance", "Warnings:", "What the agents will cost", "Every setting, by where")]
    assert order == sorted(order) and lines.index("At a glance") <= 3
    glance = "\n".join(form.at_a_glance(settings))
    assert "explore_then_exploit, skill model-efficiency" in glance
    assert "written by an agent" in glance and "writer (about" in glance and "strategist (about" in glance
    assert "Model:" in glance and settings["agents"]["default_model"] in glance
    assert "pareto on 2 islands (score and parameters)" in glance
    assert "new designs screened at 50%, the best 50% go on" in glance
    assert "60 evaluations of 10 steps; agents capped at $20" in glance
    laddered, _ = plan(evaluation__ladder=[{"at": 0.1, "keep": 0.5}], agents__backend="stub")
    glance = "\n".join(form.at_a_glance(laddered))
    assert "a ladder over every design: at 10% keep 50%" in glance and "the stub backend (scripted, no cost)" in glance


def test_six_evaluations_of_tuning_under_guided_autonomy_call_no_agent(tmp_path):
    folder = search(tmp_path, budget__evaluations=6, evaluation__allowance=150, run__type="settings_only",
                    run__skill="settings-tuning", harness__autonomy="guided", space__preset=None)
    controller = Controller(folder, "t", poll=0.1)
    assert controller.run(max_seconds=200)
    assert controller.store.read("calls") == [] and len(scored(controller.view())) >= 5


# --- part-way scores --------------------------------------------------------------------------------
def test_a_design_stopped_part_way_is_not_ranked_with_full_length_fits():
    rows = [("R1", "L1", "new", None, 0.50, "a"), ("R2", "L2", "new", None, 0.90, "b"), ("R3", "L3", "new", None, 0.40, "c")]
    view = make_view(rows)
    view.runs["R2"]["performance"]["status"] = "stopped_early"             # a high score, but only for a tenth of a run
    view.runs["R2"]["screened"] = {"at": 15, "share": 0.1, "metric": 0.9, "cutoff": 0.95}
    view = type(view)(view.runs, view.models, {}, "maximize", 0.01, 0)
    assert [view.run_of(c["id"])["id"] for c in view.scored()] == ["R1", "R3"]      # it is no parent, and not the best
    assert view.run_of(view.best()["id"])["id"] == "R1"
    stopped = view.cands[view.runs["R2"]["candidate"]]
    assert stopped["value"] is None and stopped["provisional"] == 0.90
    assert view.own_value(view.runs["R2"]) == 0.90                                   # the run keeps its own figure
    board = report.leaderboard(view, allowance=150)
    assert [(r["kind"], r["state"], r["length"]) for r in board] == [
        ("design", "full", 150), ("design", "full", 150), ("provisional", "stopped at 10%", 15)]
    assert board[-1]["score"] == 0.90 and board[0]["score"] == 0.50                 # listed last, whatever its score
    # A design with one full fit and one stopped one is ranked by the full fit alone.
    view.runs["R4"] = dict(view.runs["R2"], id="R4", candidate=view.runs["R1"]["candidate"])
    mixed = type(view)(view.runs, view.models, {}, "maximize", 0.01, 0)
    assert mixed.cands[view.runs["R1"]["candidate"]]["value"] == 0.50
    assert mixed.cands[view.runs["R1"]["candidate"]]["provisional"] is None


def test_the_report_of_a_laddered_search_marks_what_was_stopped(tmp_path):
    folder = search(tmp_path, budget__evaluations=14, evaluation__allowance=400, audit__reviews="none",
                    harness__level="minimal", evaluation__screen_min_pool=3,
                    evaluation__ladder=[{"at": 0.1, "keep": 0.5}, {"at": 0.4, "keep": 0.5}])
    controller = Controller(folder, "t", poll=0.1)
    assert controller.run(max_seconds=400)
    view = controller.view()
    stopped = [c for c in view.cands.values() if c.get("provisional") is not None]
    assert stopped and all(c["id"] not in [s["id"] for s in view.scored()] for c in stopped)
    with open(os.path.join(folder, "runs", "t", "report.md"), encoding="utf-8") as handle:
        text = handle.read()
    assert "| state" in text.replace("  ", " ") or "state" in text
    assert "stopped at 10%" in text or "stopped at 40%" in text
    assert "provisional" in text and "full" in text
